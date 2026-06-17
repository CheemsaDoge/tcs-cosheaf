"""Built-in checker registry entries."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from pydantic import ValidationError

from cosheaf.checkers.models import (
    CheckerCapability,
    CheckerInput,
    CheckerResult,
    CheckerSpec,
    CheckerStatus,
    CheckerType,
)
from cosheaf.checkers.registry import CheckerExecution, CheckerRegistry
from cosheaf.core.artifact import BaseArtifact
from cosheaf.gates.gatekeeper import (
    run_gatekeeper,
    validate_artifact_file,
    validate_repository,
)
from cosheaf.gates.source_metadata_gate import missing_required_source_metadata
from cosheaf.storage.loader import LoadedRecord, load_artifacts, load_yaml_file
from cosheaf.storage.repo import RepoContext

OVERCLAIM_PAYLOAD_FIELDS = frozenset(
    {
        "accepted",
        "accepted_status",
        "accepted_theorem",
        "accepted_refutation",
        "human_review",
        "human_reviewed",
        "promotion_authority",
        "gate_pass",
        "verifier_pass",
        "proof",
        "machine_checked",
        "lean_verified",
        "source_metadata",
        "source_metadata_authority",
    }
)
OVERCLAIM_TEXT_MARKERS = (
    "accepted theorem",
    "accepted refutation",
    "accepted status",
    "human reviewed",
    "human review complete",
    "promoted to accepted",
    "gate passed therefore accepted",
    "verifier passed therefore accepted",
    "lean verified",
    "machine checked proof",
)
PRIVATE_LEAK_MARKERS = (
    "kb/private",
    "private draft",
    "private conjecture",
    "private research",
    "private-only",
)


def default_checker_registry() -> CheckerRegistry:
    """Return the default built-in checker registry."""
    registry = CheckerRegistry()
    for spec, handler in (
        (_spec_schema(), _schema_check),
        (_spec_artifact_path_policy(), _artifact_path_policy_check),
        (_spec_gate(), _gate_check),
        (_spec_python_local(), _python_local_check),
        (_spec_sat_optional(), _sat_optional_check),
        (_spec_smt_optional(), _smt_optional_check),
        (_spec_lean_optional(), _lean_optional_check),
        (_spec_source_metadata(), _source_metadata_check),
        (_spec_private_leak(), _private_leak_check),
        (_spec_authority_overclaim(), _authority_overclaim_check),
    ):
        registry.register(spec, handler)
    return registry


def _spec_schema() -> CheckerSpec:
    return CheckerSpec(
        checker_id=CheckerType.SCHEMA_CHECK.value,
        checker_type=CheckerType.SCHEMA_CHECK,
        title="Schema check",
        description="Validate repository or artifact schema/path invariants.",
        capabilities=(CheckerCapability.SCHEMA,),
    )


def _spec_artifact_path_policy() -> CheckerSpec:
    return CheckerSpec(
        checker_id=CheckerType.ARTIFACT_PATH_POLICY_CHECK.value,
        checker_type=CheckerType.ARTIFACT_PATH_POLICY_CHECK,
        title="Artifact path policy check",
        description="Reject accepted-KB, traversal, or outside-repository paths.",
        capabilities=(CheckerCapability.PATH_POLICY,),
    )


def _spec_gate() -> CheckerSpec:
    return CheckerSpec(
        checker_id=CheckerType.GATE_CHECK.value,
        checker_type=CheckerType.GATE_CHECK,
        title="Gate check",
        description="Run the existing gatekeeper and summarize its verdict.",
        capabilities=(CheckerCapability.GATE,),
    )


def _spec_python_local() -> CheckerSpec:
    return CheckerSpec(
        checker_id=CheckerType.PYTHON_LOCAL_CHECK.value,
        checker_type=CheckerType.PYTHON_LOCAL_CHECK,
        title="Python local check",
        description="Run an explicit repository-local Python script.",
        capabilities=(CheckerCapability.LOCAL_PYTHON,),
        default_timeout_seconds=30.0,
    )


def _spec_sat_optional() -> CheckerSpec:
    return CheckerSpec(
        checker_id=CheckerType.SAT_OPTIONAL_CHECK.value,
        checker_type=CheckerType.SAT_OPTIONAL_CHECK,
        title="SAT optional check",
        description="Check optional SAT backend availability without requiring CI.",
        capabilities=(CheckerCapability.OPTIONAL_TOOL,),
        optional=True,
    )


def _spec_smt_optional() -> CheckerSpec:
    return CheckerSpec(
        checker_id=CheckerType.SMT_OPTIONAL_CHECK.value,
        checker_type=CheckerType.SMT_OPTIONAL_CHECK,
        title="SMT optional check",
        description="Check optional SMT backend availability without requiring CI.",
        capabilities=(CheckerCapability.OPTIONAL_TOOL,),
        optional=True,
    )


def _spec_lean_optional() -> CheckerSpec:
    return CheckerSpec(
        checker_id=CheckerType.LEAN_OPTIONAL_CHECK.value,
        checker_type=CheckerType.LEAN_OPTIONAL_CHECK,
        title="Lean optional check",
        description="Check optional Lean backend availability without requiring CI.",
        capabilities=(CheckerCapability.OPTIONAL_TOOL,),
        optional=True,
    )


def _spec_source_metadata() -> CheckerSpec:
    return CheckerSpec(
        checker_id=CheckerType.SOURCE_METADATA_CHECK.value,
        checker_type=CheckerType.SOURCE_METADATA_CHECK,
        title="Source metadata check",
        description="Inspect required source metadata for one artifact.",
        capabilities=(CheckerCapability.SOURCE_METADATA,),
    )


def _spec_private_leak() -> CheckerSpec:
    return CheckerSpec(
        checker_id=CheckerType.PRIVATE_LEAK_CHECK.value,
        checker_type=CheckerType.PRIVATE_LEAK_CHECK,
        title="Private leak check",
        description="Reject private paths or markers in public-mode packets.",
        capabilities=(CheckerCapability.PRIVACY_POLICY,),
    )


def _spec_authority_overclaim() -> CheckerSpec:
    return CheckerSpec(
        checker_id=CheckerType.AUTHORITY_OVERCLAIM_CHECK.value,
        checker_type=CheckerType.AUTHORITY_OVERCLAIM_CHECK,
        title="Authority overclaim check",
        description=(
            "Reject checker/proposal text that claims review or truth authority."
        ),
        capabilities=(CheckerCapability.AUTHORITY_POLICY,),
    )


def _schema_check(
    context: RepoContext,
    checker_input: CheckerInput,
    spec: CheckerSpec,
) -> CheckerExecution:
    started_at = _now()
    try:
        if checker_input.artifact_path:
            report = validate_artifact_file(
                context,
                context.resolve(checker_input.artifact_path),
            )
        else:
            report = validate_repository(context)
    except Exception as exc:  # noqa: BLE001 - checker errors must be structured.
        return _execution(
            spec,
            CheckerStatus.ERROR,
            started_at,
            f"schema check failed to run: {exc}",
            stderr=str(exc),
        )
    status = CheckerStatus.PASS if report.ok else CheckerStatus.FAIL
    message = (
        f"schema check passed for {report.checked_count} record(s)"
        if report.ok
        else f"schema check found {len(report.failures)} failure(s)"
    )
    diagnostics = tuple(
        failure.source_path for failure in report.failures if failure.source_path
    )
    stdout = json.dumps(
        {
            "ok": report.ok,
            "checked_count": report.checked_count,
            "failures": [
                {
                    "gate": failure.gate,
                    "source_path": failure.source_path,
                    "artifact_id": failure.artifact_id,
                    "message": failure.message,
                }
                for failure in report.failures
            ],
        },
        ensure_ascii=True,
        indent=2,
    )
    return _execution(
        spec,
        status,
        started_at,
        message,
        diagnostic_paths=diagnostics,
        stdout=stdout + "\n",
        input_paths=_input_paths(checker_input),
    )


def _artifact_path_policy_check(
    context: RepoContext,
    checker_input: CheckerInput,
    spec: CheckerSpec,
) -> CheckerExecution:
    started_at = _now()
    paths = _input_paths(checker_input)
    if not paths:
        return _execution(
            spec,
            CheckerStatus.UNSUPPORTED,
            started_at,
            "no paths were provided for artifact path policy checking",
        )
    violations: list[str] = []
    for path in paths:
        violation = _path_policy_violation(context, path)
        if violation:
            violations.append(violation)
    if violations:
        return _execution(
            spec,
            CheckerStatus.BLOCKED_BY_POLICY,
            started_at,
            f"artifact path policy blocked {len(violations)} path(s)",
            stderr="\n".join(violations) + "\n",
            input_paths=paths,
        )
    return _execution(
        spec,
        CheckerStatus.PASS,
        started_at,
        f"artifact path policy passed for {len(paths)} path(s)",
        input_paths=paths,
    )


def _gate_check(
    context: RepoContext,
    checker_input: CheckerInput,
    spec: CheckerSpec,
) -> CheckerExecution:
    started_at = _now()
    try:
        result = run_gatekeeper(context)
    except Exception as exc:  # noqa: BLE001 - checker errors must be structured.
        return _execution(
            spec,
            CheckerStatus.ERROR,
            started_at,
            f"gate check failed to run: {exc}",
            stderr=str(exc),
        )
    status = (
        CheckerStatus.PASS
        if result.report.verdict == "pass"
        else CheckerStatus.FAIL
    )
    output_paths = (
        _relative(context, result.json_path),
        _relative(context, result.markdown_path),
    )
    message = f"gatekeeper verdict: {result.report.verdict}"
    stdout = json.dumps(result.report.to_dict(), ensure_ascii=True, indent=2) + "\n"
    return _execution(
        spec,
        status,
        started_at,
        message,
        diagnostic_paths=output_paths,
        output_paths=output_paths,
        stdout=stdout,
        input_paths=_input_paths(checker_input),
    )


def _python_local_check(
    context: RepoContext,
    checker_input: CheckerInput,
    spec: CheckerSpec,
) -> CheckerExecution:
    started_at = _now()
    script = checker_input.payload.get("script_path")
    if not isinstance(script, str) or not script.strip():
        return _execution(
            spec,
            CheckerStatus.UNSUPPORTED,
            started_at,
            "python_local_check requires payload.script_path",
        )
    violation = _path_policy_violation(context, script)
    if violation:
        return _execution(
            spec,
            CheckerStatus.BLOCKED_BY_POLICY,
            started_at,
            "python local script path is blocked by policy",
            stderr=violation + "\n",
            input_paths=(script,),
        )
    script_path = context.resolve(script)
    if not script_path.is_file():
        return _execution(
            spec,
            CheckerStatus.ERROR,
            started_at,
            f"python local script not found: {script}",
            input_paths=(script,),
        )
    timeout = _timeout(checker_input, spec)
    args = _string_list(checker_input.payload.get("args"))
    command = (sys.executable, script, *args)
    try:
        completed = subprocess.run(
            command,
            cwd=context.repo_root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return _execution(
            spec,
            CheckerStatus.ERROR,
            started_at,
            f"python local check timed out after {timeout:g} second(s)",
            command=command,
            cwd=str(context.repo_root),
            exit_code=None,
            timeout_seconds=timeout,
            stdout=_process_output(exc.stdout),
            stderr=_process_output(exc.stderr),
            input_paths=(script,),
            tool_name="python",
            tool_version=sys.version.split()[0],
        )
    status = CheckerStatus.PASS if completed.returncode == 0 else CheckerStatus.FAIL
    message = (
        "python local check passed"
        if completed.returncode == 0
        else f"python local check failed with exit code {completed.returncode}"
    )
    return _execution(
        spec,
        status,
        started_at,
        message,
        command=command,
        cwd=str(context.repo_root),
        exit_code=completed.returncode,
        timeout_seconds=timeout,
        stdout=completed.stdout,
        stderr=completed.stderr,
        input_paths=(script,),
        tool_name="python",
        tool_version=sys.version.split()[0],
    )


def _sat_optional_check(
    context: RepoContext,
    checker_input: CheckerInput,
    spec: CheckerSpec,
) -> CheckerExecution:
    return _optional_tool_check("kissat", context, checker_input, spec)


def _smt_optional_check(
    context: RepoContext,
    checker_input: CheckerInput,
    spec: CheckerSpec,
) -> CheckerExecution:
    return _optional_tool_check("z3", context, checker_input, spec)


def _lean_optional_check(
    context: RepoContext,
    checker_input: CheckerInput,
    spec: CheckerSpec,
) -> CheckerExecution:
    return _optional_tool_check("lean", context, checker_input, spec)


def _optional_tool_check(
    default_command: str,
    context: RepoContext,
    checker_input: CheckerInput,
    spec: CheckerSpec,
) -> CheckerExecution:
    started_at = _now()
    raw_tool = checker_input.payload.get("tool_command", default_command)
    tool = (
        raw_tool
        if isinstance(raw_tool, str) and raw_tool.strip()
        else default_command
    )
    if shutil.which(tool) is None:
        return _execution(
            spec,
            CheckerStatus.SKIPPED,
            started_at,
            f"optional tool is unavailable: {tool}",
            tool_name=tool,
        )
    return _execution(
        spec,
        CheckerStatus.INCONCLUSIVE,
        started_at,
        (
            f"optional tool is available: {tool}; this registry check only "
            "records availability and does not prove semantic alignment"
        ),
        tool_name=tool,
        cwd=str(context.repo_root),
    )


def _source_metadata_check(
    context: RepoContext,
    checker_input: CheckerInput,
    spec: CheckerSpec,
) -> CheckerExecution:
    started_at = _now()
    try:
        loaded = _load_target_artifact(context, checker_input)
    except (OSError, ValueError, ValidationError) as exc:
        return _execution(
            spec,
            CheckerStatus.ERROR,
            started_at,
            f"source metadata check failed to load artifact: {exc}",
            stderr=str(exc),
        )
    if loaded is None or not isinstance(loaded.record, BaseArtifact):
        return _execution(
            spec,
            CheckerStatus.UNSUPPORTED,
            started_at,
            "source_metadata_check requires artifact_id or artifact_path",
        )
    artifact = loaded.record
    missing = missing_required_source_metadata(artifact)
    if missing:
        return _execution(
            spec,
            CheckerStatus.FAIL,
            started_at,
            "source metadata is incomplete: " + ", ".join(missing),
            diagnostic_paths=(loaded.source_path.as_posix(),),
            input_paths=(loaded.source_path.as_posix(),),
        )
    return _execution(
        spec,
        CheckerStatus.PASS,
        started_at,
        f"source metadata present for {artifact.id}",
        diagnostic_paths=(loaded.source_path.as_posix(),),
        input_paths=(loaded.source_path.as_posix(),),
    )


def _private_leak_check(
    context: RepoContext,
    checker_input: CheckerInput,
    spec: CheckerSpec,
) -> CheckerExecution:
    started_at = _now()
    if checker_input.mode != "public":
        return _execution(
            spec,
            CheckerStatus.INCONCLUSIVE,
            started_at,
            "private leak check only blocks in public mode",
            input_paths=_input_paths(checker_input),
        )
    haystack = _input_haystack(checker_input)
    findings = tuple(marker for marker in PRIVATE_LEAK_MARKERS if marker in haystack)
    if findings:
        return _execution(
            spec,
            CheckerStatus.BLOCKED_BY_POLICY,
            started_at,
            "public-mode checker input contains private markers",
            stderr="\n".join(findings) + "\n",
            input_paths=_input_paths(checker_input),
        )
    return _execution(
        spec,
        CheckerStatus.PASS,
        started_at,
        "no private markers found in public-mode checker input",
        input_paths=_input_paths(checker_input),
    )


def _authority_overclaim_check(
    context: RepoContext,
    checker_input: CheckerInput,
    spec: CheckerSpec,
) -> CheckerExecution:
    started_at = _now()
    findings: list[str] = []
    haystack = _input_haystack(checker_input)
    findings.extend(marker for marker in OVERCLAIM_TEXT_MARKERS if marker in haystack)
    findings.extend(_truthy_overclaim_fields(checker_input.payload))
    if findings:
        return _execution(
            spec,
            CheckerStatus.BLOCKED_BY_POLICY,
            started_at,
            "checker input overclaims review, proof, or accepted-knowledge authority",
            stderr="\n".join(sorted(set(findings))) + "\n",
            input_paths=_input_paths(checker_input),
        )
    return _execution(
        spec,
        CheckerStatus.PASS,
        started_at,
        "no authority overclaim markers found",
        input_paths=_input_paths(checker_input),
    )


def _execution(
    spec: CheckerSpec,
    status: CheckerStatus,
    started_at: datetime,
    message: str,
    *,
    diagnostic_paths: tuple[str, ...] = (),
    command: tuple[str, ...] | None = None,
    cwd: str | None = None,
    exit_code: int | None = None,
    input_paths: tuple[str, ...] = (),
    output_paths: tuple[str, ...] = (),
    timeout_seconds: float | None = None,
    tool_name: str | None = None,
    tool_version: str | None = None,
    stdout: str = "",
    stderr: str = "",
) -> CheckerExecution:
    ended_at = _now()
    result = CheckerResult(
        checker_id=spec.checker_id,
        checker_type=spec.checker_type,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        message=message,
        diagnostic_paths=diagnostic_paths,
        command=command,
        cwd=cwd,
        exit_code=exit_code,
        input_paths=input_paths,
        output_paths=output_paths,
        timeout_seconds=timeout_seconds,
        tool_name=tool_name,
        tool_version=tool_version,
        limitations=(spec.authority_notice.message,),
        authority_notice=spec.authority_notice,
    )
    return CheckerExecution(result=result, stdout=stdout, stderr=stderr)


def _input_paths(checker_input: CheckerInput) -> tuple[str, ...]:
    paths = list(checker_input.paths)
    if checker_input.artifact_path:
        paths.append(checker_input.artifact_path)
    return tuple(sorted(dict.fromkeys(paths)))


def _path_policy_violation(context: RepoContext, path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    if not normalized:
        return "path must not be empty"
    parts = PurePosixPath(normalized).parts
    if ".." in parts:
        return f"path must not traverse parents: {path}"
    candidate = Path(normalized)
    resolved = candidate.resolve() if candidate.is_absolute() else context.resolve(path)
    try:
        relative = resolved.relative_to(context.repo_root).as_posix()
    except ValueError:
        return f"path must stay inside repository: {path}"
    relative_parts = PurePosixPath(relative).parts
    if len(relative_parts) >= 2 and relative_parts[0] == "kb":
        if "accepted" in relative_parts[1:]:
            return f"path must not target accepted KB paths: {relative}"
    return ""


def _load_target_artifact(
    context: RepoContext,
    checker_input: CheckerInput,
) -> LoadedRecord | None:
    if checker_input.artifact_path:
        return load_yaml_file(context, context.resolve(checker_input.artifact_path))
    if checker_input.artifact_id:
        matches = [
            loaded
            for loaded in load_artifacts(context)
            if loaded.id == checker_input.artifact_id
        ]
        if not matches:
            return None
        return sorted(matches, key=lambda loaded: loaded.source_path.as_posix())[0]
    return None


def _input_haystack(checker_input: CheckerInput) -> str:
    payload_text = json.dumps(
        checker_input.payload,
        ensure_ascii=True,
        sort_keys=True,
        default=str,
    )
    return " ".join(
        (
            checker_input.text,
            checker_input.artifact_id or "",
            checker_input.artifact_path or "",
            " ".join(checker_input.paths),
            payload_text,
        )
    ).lower()


def _truthy_overclaim_fields(payload: dict[str, Any]) -> list[str]:
    findings: list[str] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                key_normalized = str(key).strip().lower()
                if key_normalized in OVERCLAIM_PAYLOAD_FIELDS and bool(child):
                    findings.append(child_path)
                visit(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    visit(payload, "")
    return findings


def _timeout(checker_input: CheckerInput, spec: CheckerSpec) -> float:
    value = checker_input.payload.get("timeout_seconds", spec.default_timeout_seconds)
    if value is None:
        return spec.default_timeout_seconds or 30.0
    try:
        timeout = float(value)
    except (TypeError, ValueError):
        timeout = spec.default_timeout_seconds or 30.0
    return timeout if timeout > 0 else spec.default_timeout_seconds or 30.0


def _string_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    try:
        return tuple(str(item) for item in value)
    except TypeError:
        return ()


def _process_output(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def _relative(context: RepoContext, path: Path) -> str:
    return path.resolve().relative_to(context.repo_root).as_posix()


def _now() -> datetime:
    return datetime.now(UTC)
