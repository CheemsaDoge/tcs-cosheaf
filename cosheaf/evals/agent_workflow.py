"""Deterministic CLI-agent and provider-worker workflow eval harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import Field, field_validator
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.core.ids import validate_artifact_id
from cosheaf.memory.models import MemoryModel
from cosheaf.storage.repo import RepoContext

DEFAULT_AGENT_WORKFLOW_EVAL_CASES = Path("evals") / "agent_workflow" / "cases.yaml"


class AgentWorkflowEvalError(ValueError):
    """Raised for expected agent workflow eval loading or execution failures."""


class AgentWorkflowEvalKind(StrEnum):
    """Supported agent-workflow eval case categories."""

    CLI_AGENT_WORKFLOW = "cli_agent_workflow"
    PROVIDER_WORKER_FAKE = "provider_worker_fake"
    CONTEXT_PRIVACY = "context_privacy"
    BUNDLE_VALIDITY = "bundle_validity"
    GATE_REGRESSION = "gate_regression"
    OPTIONAL_MCP_READONLY = "optional_mcp_readonly"


class AgentWorkflowEvalSurface(StrEnum):
    """High-level access surface exercised by an eval case."""

    CLI = "cli"
    PROVIDER = "provider"
    OPTIONAL_MCP = "optional_mcp"


class AgentWorkflowEvalCase(MemoryModel):
    """One deterministic CLI-agent/provider workflow eval case."""

    id: str | None = None
    kind: AgentWorkflowEvalKind
    surface: AgentWorkflowEvalSurface = AgentWorkflowEvalSurface.CLI
    command: list[str]
    expect_exit_code: int = 0
    expect_json: bool = True
    required_artifacts: list[str] = Field(default_factory=list)
    forbidden_substrings: list[str] = Field(default_factory=list)
    expected_error_code: str | None = None
    require_provider_redaction: bool = False

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_artifact_id(value.strip())

    @field_validator("kind", mode="before")
    @classmethod
    def _validate_kind(
        cls,
        value: AgentWorkflowEvalKind | str,
    ) -> AgentWorkflowEvalKind:
        if isinstance(value, AgentWorkflowEvalKind):
            return value
        return AgentWorkflowEvalKind(value)

    @field_validator("surface", mode="before")
    @classmethod
    def _validate_surface(
        cls,
        value: AgentWorkflowEvalSurface | str,
    ) -> AgentWorkflowEvalSurface:
        return (
            value
            if isinstance(value, AgentWorkflowEvalSurface)
            else AgentWorkflowEvalSurface(value)
        )

    @field_validator("command")
    @classmethod
    def _validate_command(cls, values: list[str]) -> list[str]:
        normalized = [_non_empty(value) for value in values]
        if not normalized:
            raise ValueError("command must not be empty")
        return normalized

    @field_validator("expect_exit_code")
    @classmethod
    def _validate_exit_code(cls, value: int) -> int:
        if value < 0:
            raise ValueError("expect_exit_code must be non-negative")
        return value

    @field_validator("required_artifacts")
    @classmethod
    def _validate_required_artifacts(cls, values: list[str]) -> list[str]:
        return [validate_artifact_id(value.strip()) for value in values]

    @field_validator("forbidden_substrings")
    @classmethod
    def _validate_forbidden_substrings(cls, values: list[str]) -> list[str]:
        return [_non_empty(value) for value in values]

    @field_validator("expected_error_code")
    @classmethod
    def _validate_error_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _non_empty(value)


class AgentWorkflowEvalSuite(MemoryModel):
    """Collection of deterministic CLI-agent/provider workflow eval cases."""

    schema_version: Literal[1] = 1
    cases: list[AgentWorkflowEvalCase]

    @field_validator("cases")
    @classmethod
    def _validate_cases(
        cls,
        values: list[AgentWorkflowEvalCase],
    ) -> list[AgentWorkflowEvalCase]:
        if not values:
            raise ValueError("cases must not be empty")
        return values


@dataclass(frozen=True)
class AgentWorkflowEvalMetrics:
    """Aggregate metrics required by the CLI-agent workflow eval."""

    command_success_rate: float
    json_parse_success_rate: float
    required_artifact_hit: float
    private_leakage_count: int
    accepted_write_rejection_count: int
    malformed_bundle_rejection_count: int
    provider_redaction_pass_count: int

    def to_dict(self) -> dict[str, int | float]:
        """Return deterministic machine-readable metrics."""
        return {
            "command_success_rate": self.command_success_rate,
            "json_parse_success_rate": self.json_parse_success_rate,
            "required_artifact_hit": self.required_artifact_hit,
            "private_leakage_count": self.private_leakage_count,
            "accepted_write_rejection_count": self.accepted_write_rejection_count,
            "malformed_bundle_rejection_count": self.malformed_bundle_rejection_count,
            "provider_redaction_pass_count": self.provider_redaction_pass_count,
        }


@dataclass(frozen=True)
class AgentWorkflowEvalCaseResult:
    """One executed workflow eval case."""

    id: str
    kind: AgentWorkflowEvalKind
    surface: AgentWorkflowEvalSurface
    command: tuple[str, ...]
    exit_code: int
    expected_exit_code: int
    json_parse_ok: bool
    required_artifact_hit: float
    private_leakage_count: int
    accepted_write_rejection: bool
    malformed_bundle_rejection: bool
    provider_redaction_pass: bool
    failures: list[str]

    @property
    def command_matched_expectation(self) -> bool:
        """Return whether the command exited with the expected code."""
        return self.exit_code == self.expected_exit_code

    @property
    def passed(self) -> bool:
        """Return whether this eval case satisfied every expectation."""
        return not self.failures

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic machine-readable case output."""
        return {
            "id": self.id,
            "kind": self.kind.value,
            "surface": self.surface.value,
            "command": list(self.command),
            "exit_code": self.exit_code,
            "expected_exit_code": self.expected_exit_code,
            "command_matched_expectation": self.command_matched_expectation,
            "json_parse_ok": self.json_parse_ok,
            "required_artifact_hit": self.required_artifact_hit,
            "private_leakage_count": self.private_leakage_count,
            "accepted_write_rejection": self.accepted_write_rejection,
            "malformed_bundle_rejection": self.malformed_bundle_rejection,
            "provider_redaction_pass": self.provider_redaction_pass,
            "failures": self.failures,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class AgentWorkflowEvalReport:
    """Scored agent workflow eval suite output."""

    schema_version: Literal[1]
    case_count: int
    passed: bool
    metrics: AgentWorkflowEvalMetrics
    surface_counts: dict[str, int]
    cases: list[AgentWorkflowEvalCaseResult]

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic machine-readable report output."""
        return {
            "schema_version": self.schema_version,
            "case_count": self.case_count,
            "passed": self.passed,
            "metrics": self.metrics.to_dict(),
            "surface_counts": dict(sorted(self.surface_counts.items())),
            "cases": [case.to_dict() for case in self.cases],
        }

    def to_json(self) -> str:
        """Return deterministic JSON for the report."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


def load_agent_workflow_eval_suite(path: Path) -> AgentWorkflowEvalSuite:
    """Load an agent workflow eval suite from a YAML file."""
    if not path.exists():
        raise AgentWorkflowEvalError(f"agent workflow eval case file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise AgentWorkflowEvalError(
            f"cannot read agent workflow eval case file: {exc}"
        ) from exc
    if data is None:
        raise AgentWorkflowEvalError("agent workflow eval case file is empty")
    try:
        return AgentWorkflowEvalSuite.model_validate(data)
    except ValueError as exc:
        raise AgentWorkflowEvalError(
            f"invalid agent workflow eval case file: {exc}"
        ) from exc


def resolve_agent_workflow_eval_case_path(
    context: RepoContext,
    cases_path: Path,
) -> Path:
    """Resolve and constrain the case file path to the repository root."""
    repo_root = context.repo_root
    path = cases_path if cases_path.is_absolute() else repo_root / cases_path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise AgentWorkflowEvalError(
            "agent workflow eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(cases_path).is_absolute():
        raise AgentWorkflowEvalError(
            "agent workflow eval case file must be repository-local"
        )
    return resolved


def run_agent_workflow_eval_suite(
    context: RepoContext,
    suite: AgentWorkflowEvalSuite,
) -> AgentWorkflowEvalReport:
    """Run every agent workflow eval case through the existing CLI surface."""
    runner = CliRunner()
    case_results = [
        run_agent_workflow_eval_case(context, case, runner=runner, case_index=index)
        for index, case in enumerate(suite.cases, start=1)
    ]
    metrics = _aggregate_metrics(case_results)
    return AgentWorkflowEvalReport(
        schema_version=1,
        case_count=len(case_results),
        passed=all(case.passed for case in case_results),
        metrics=metrics,
        surface_counts=_surface_counts(case_results),
        cases=case_results,
    )


def run_agent_workflow_eval_case(
    context: RepoContext,
    case: AgentWorkflowEvalCase,
    *,
    runner: CliRunner | None = None,
    case_index: int = 1,
) -> AgentWorkflowEvalCaseResult:
    """Run and score one agent workflow eval case."""
    active_runner = runner or CliRunner()
    command = _resolve_command(context, case.command)
    result = active_runner.invoke(app, command)
    payload: dict[str, Any] | None = None
    json_parse_ok = False
    if case.expect_json:
        try:
            loaded = json.loads(result.output)
        except json.JSONDecodeError:
            loaded = None
        if isinstance(loaded, dict):
            payload = loaded
            json_parse_ok = True
    else:
        json_parse_ok = True

    output_text = result.output
    required_hit = _required_artifact_hit(context, case, payload, output_text)
    private_leakage_count = _private_leakage_count(case, output_text)
    accepted_write_rejection = _expected_error_seen(
        case,
        payload,
        "accepted_write_forbidden",
    )
    malformed_bundle_rejection = _expected_error_seen(
        case,
        payload,
        "bundle_submit_failed",
    )
    provider_redaction_pass = _provider_redaction_pass(case, payload, output_text)
    failures = _case_failures(
        case,
        exit_code=result.exit_code,
        payload=payload,
        json_parse_ok=json_parse_ok,
        required_artifact_hit=required_hit,
        private_leakage_count=private_leakage_count,
        provider_redaction_pass=provider_redaction_pass,
    )

    return AgentWorkflowEvalCaseResult(
        id=_case_id(case, case_index),
        kind=case.kind,
        surface=case.surface,
        command=tuple(command),
        exit_code=result.exit_code,
        expected_exit_code=case.expect_exit_code,
        json_parse_ok=json_parse_ok,
        required_artifact_hit=required_hit,
        private_leakage_count=private_leakage_count,
        accepted_write_rejection=accepted_write_rejection,
        malformed_bundle_rejection=malformed_bundle_rejection,
        provider_redaction_pass=provider_redaction_pass,
        failures=failures,
    )


def _case_failures(
    case: AgentWorkflowEvalCase,
    *,
    exit_code: int,
    payload: dict[str, Any] | None,
    json_parse_ok: bool,
    required_artifact_hit: float,
    private_leakage_count: int,
    provider_redaction_pass: bool,
) -> list[str]:
    failures: list[str] = []
    if exit_code != case.expect_exit_code:
        failures.append(
            f"exit_code {exit_code} did not match expected {case.expect_exit_code}"
        )
    if case.expect_json and not json_parse_ok:
        failures.append("stdout was not parseable JSON")
    if case.expected_error_code is not None:
        actual = payload.get("code") if payload else None
        if actual != case.expected_error_code:
            failures.append(
                f"error_code {actual!r} did not match expected "
                f"{case.expected_error_code!r}"
            )
    if case.required_artifacts and required_artifact_hit < 1.0:
        failures.append(
            f"required_artifact_hit {required_artifact_hit:.6f} below required 1.0"
        )
    if private_leakage_count:
        failures.append(f"private_leakage_count {private_leakage_count} exceeds 0")
    if case.require_provider_redaction and not provider_redaction_pass:
        failures.append("provider redaction expectation was not satisfied")
    return failures


def _aggregate_metrics(
    cases: list[AgentWorkflowEvalCaseResult],
) -> AgentWorkflowEvalMetrics:
    if not cases:
        raise AgentWorkflowEvalError("cannot aggregate empty agent workflow eval")
    return AgentWorkflowEvalMetrics(
        command_success_rate=round(
            sum(1 for case in cases if case.command_matched_expectation) / len(cases),
            6,
        ),
        json_parse_success_rate=round(
            sum(1 for case in cases if case.json_parse_ok) / len(cases),
            6,
        ),
        required_artifact_hit=round(
            sum(case.required_artifact_hit for case in cases) / len(cases),
            6,
        ),
        private_leakage_count=sum(case.private_leakage_count for case in cases),
        accepted_write_rejection_count=sum(
            1 for case in cases if case.accepted_write_rejection
        ),
        malformed_bundle_rejection_count=sum(
            1 for case in cases if case.malformed_bundle_rejection
        ),
        provider_redaction_pass_count=sum(
            1 for case in cases if case.provider_redaction_pass
        ),
    )


def _surface_counts(
    cases: list[AgentWorkflowEvalCaseResult],
) -> dict[str, int]:
    counts = {surface.value: 0 for surface in AgentWorkflowEvalSurface}
    for case in cases:
        counts[case.surface.value] += 1
    return counts


def _required_artifact_hit(
    context: RepoContext,
    case: AgentWorkflowEvalCase,
    payload: dict[str, Any] | None,
    output_text: str,
) -> float:
    if not case.required_artifacts:
        return 1.0
    haystack = output_text
    if payload is not None:
        haystack = json.dumps(payload, sort_keys=True)
        task_dir = payload.get("task_dir")
        if isinstance(task_dir, str):
            audit_path = context.resolve(Path(task_dir) / "RETRIEVAL_AUDIT.json")
            try:
                audit_path.relative_to(context.repo_root)
            except ValueError:
                pass
            else:
                if audit_path.is_file():
                    haystack += audit_path.read_text(encoding="utf-8")
    hits = sum(1 for artifact_id in case.required_artifacts if artifact_id in haystack)
    return round(hits / len(case.required_artifacts), 6)


def _private_leakage_count(
    case: AgentWorkflowEvalCase,
    output_text: str,
) -> int:
    return sum(1 for value in case.forbidden_substrings if value in output_text)


def _expected_error_seen(
    case: AgentWorkflowEvalCase,
    payload: dict[str, Any] | None,
    expected_code: str,
) -> bool:
    return (
        case.expected_error_code == expected_code
        and payload is not None
        and payload.get("code") == expected_code
    )


def _provider_redaction_pass(
    case: AgentWorkflowEvalCase,
    payload: dict[str, Any] | None,
    output_text: str,
) -> bool:
    if not case.require_provider_redaction:
        return False
    return (
        payload is not None
        and "<redacted>" in output_text
        and "provider_log" in payload
        and bool(payload["provider_log"].get("redaction_applied"))
    )


def _case_id(case: AgentWorkflowEvalCase, index: int) -> str:
    if case.id:
        return case.id
    return f"case.agent-workflow.{index:04d}"


def _resolve_command(context: RepoContext, command: list[str]) -> list[str]:
    return [
        value.replace("{repo_root}", str(context.repo_root))
        for value in command
    ]


def _non_empty(value: str) -> str:
    stripped = str(value).strip()
    if not stripped:
        raise ValueError("text value must be non-empty")
    return stripped
