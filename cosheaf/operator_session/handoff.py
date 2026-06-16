"""Review handoff bundles for finalized operator sessions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path, repo_relative_posix
from cosheaf.operator_session.models import (
    OPERATOR_SESSION_AUTHORITY_NOTICE,
    OperatorArtifactRefKind,
    OperatorCheckKind,
    OperatorCheckResult,
    OperatorCheckStatus,
    OperatorSessionError,
    OperatorSessionEvent,
    OperatorSessionStatus,
)
from cosheaf.operator_session.security import (
    OperatorSessionScanFinding,
    OperatorSessionScanResult,
    scan_operator_session,
)
from cosheaf.operator_session.storage import (
    load_operator_session,
    load_operator_session_events,
)
from cosheaf.storage.repo import RepoContext
from cosheaf.storage.writer import write_yaml_deterministic

OPERATOR_HANDOFF_KIND = "operator_handoff_bundle"
OPERATOR_HANDOFF_REQUIRED_CHECKS: tuple[OperatorCheckKind, ...] = (
    OperatorCheckKind.VALIDATE,
    OperatorCheckKind.GATE,
    OperatorCheckKind.TEST,
    OperatorCheckKind.EVAL,
)
OPERATOR_HANDOFF_REVIEW_CHECKLIST: tuple[str, ...] = (
    "Confirm source metadata separately from this handoff.",
    "Confirm human review separately from this handoff.",
    "Run or inspect validation, gate, tests, and evals independently.",
    "Confirm skipped checks are not treated as pass evidence.",
    "Confirm no accepted write, promotion, or verifier mutation occurred.",
)


class OperatorHandoffModel(BaseModel):
    """Strict deterministic base model for operator handoff DTOs."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-serializable data."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON text."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class OperatorHandoffKbRoot(OperatorHandoffModel):
    """One configured KB root summarized in a handoff bundle."""

    name: str
    path: str
    readonly: bool
    priority: int


class OperatorHandoffCheckSummary(OperatorHandoffModel):
    """Compact check-status accounting for one handoff."""

    passed: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()
    errored: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    all_required_recorded: bool


class OperatorHandoffToolStatusCounts(OperatorHandoffModel):
    """Bounded per-tool status counts."""

    completed: int = 0
    denied: int = 0
    error: int = 0
    failed: int = 0


class OperatorHandoffScannerSummary(OperatorHandoffModel):
    """Scanner status embedded in a handoff bundle."""

    report_path: str
    finding_count: int
    blocking_finding_count: int
    handoff_blocked: bool
    findings: tuple[dict[str, Any], ...] = ()


class OperatorHandoffBundle(OperatorHandoffModel):
    """One compact review handoff bundle for a finalized operator session."""

    schema_version: Literal[1] = 1
    kind: Literal["operator_handoff_bundle"] = "operator_handoff_bundle"
    handoff_id: str
    session_id: str
    issue_id: str
    policy_mode: str
    session_status: str
    operator_label: str
    started_at: datetime
    finalized_at: datetime
    kb_roots: tuple[OperatorHandoffKbRoot, ...]
    referenced_files: tuple[str, ...] = ()
    draft_artifacts: tuple[str, ...] = ()
    source_notes: tuple[str, ...] = ()
    review_context_records: tuple[str, ...] = ()
    checks: tuple[OperatorCheckResult, ...] = ()
    check_summary: OperatorHandoffCheckSummary
    tool_summary: dict[str, OperatorHandoffToolStatusCounts] = Field(
        default_factory=dict
    )
    scanner: OperatorHandoffScannerSummary
    skipped_checks_are_pass: Literal[False] = False
    human_review_checklist: tuple[str, ...] = OPERATOR_HANDOFF_REVIEW_CHECKLIST
    known_limitations: tuple[str, ...]
    follow_up_recommendations: tuple[str, ...]
    authority_notice: str = OPERATOR_SESSION_AUTHORITY_NOTICE
    accepted_write_performed: Literal[False] = False
    human_review_created: Literal[False] = False
    promotion_performed: Literal[False] = False
    verifier_result_mutated: Literal[False] = False

    @field_validator("handoff_id", "session_id", "issue_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator(
        "referenced_files",
        "source_notes",
        "review_context_records",
        mode="before",
    )
    @classmethod
    def _paths(cls, value: Any) -> tuple[str, ...]:
        return tuple(_validate_repo_local_nonaccepted_path(item) for item in value)

    @field_validator("authority_notice")
    @classmethod
    def _authority_notice(cls, value: str) -> str:
        if value != OPERATOR_SESSION_AUTHORITY_NOTICE:
            raise ValueError("authority_notice must preserve handoff boundary")
        return value


class OperatorHandoffExportResult(OperatorHandoffModel):
    """One explicit review-context export result for a handoff bundle."""

    schema_version: Literal[1] = 1
    kind: Literal["operator_handoff_export"] = "operator_handoff_export"
    handoff_id: str
    source_runtime_path: str
    target_path: str
    dry_run: bool
    written_paths: tuple[str, ...] = ()
    review_context_only: Literal[True] = True
    handoff: OperatorHandoffBundle
    authority_notice: str = OPERATOR_SESSION_AUTHORITY_NOTICE
    accepted_write_performed: Literal[False] = False
    human_review_created: Literal[False] = False
    promotion_performed: Literal[False] = False
    verifier_result_mutated: Literal[False] = False

    @field_validator("handoff_id")
    @classmethod
    def _handoff_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("source_runtime_path", "target_path")
    @classmethod
    def _paths(cls, value: str) -> str:
        return _validate_repo_local_nonaccepted_path(value)

    @field_validator("written_paths", mode="before")
    @classmethod
    def _written_paths(cls, value: Any) -> tuple[str, ...]:
        return tuple(_validate_repo_local_nonaccepted_path(item) for item in value)

    @field_validator("authority_notice")
    @classmethod
    def _authority_notice(cls, value: str) -> str:
        if value != OPERATOR_SESSION_AUTHORITY_NOTICE:
            raise ValueError("authority_notice must preserve handoff boundary")
        return value


@dataclass(frozen=True)
class OperatorHandoffWriteResult:
    """One loaded or written operator handoff bundle."""

    handoff: OperatorHandoffBundle
    relative_path: Path
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        payload = self.handoff.to_dict()
        payload["path"] = self.relative_path.as_posix()
        payload["accepted_write_performed"] = self.accepted_write_performed
        return payload


def build_operator_handoff(
    context: RepoContext,
    *,
    session_id: str,
) -> OperatorHandoffWriteResult:
    """Build and persist one runtime review handoff bundle."""
    loaded = load_operator_session(context, session_id)
    session = loaded.session
    if session.status is not OperatorSessionStatus.FINALIZED:
        raise OperatorSessionError(
            f"operator session must be finalized before handoff: {session.session_id}",
            code="operator_handoff_session_not_finalized",
            remediation="Run `cosheaf operator session finalize <session-id>` first.",
            details={"session_id": session.session_id, "status": session.status.value},
        )
    if session.finalized_at is None:
        raise OperatorSessionError(
            f"operator session has no finalized_at timestamp: {session.session_id}",
            code="operator_handoff_session_not_finalized",
            remediation="Finalize the session again after repairing runtime metadata.",
            details={"session_id": session.session_id},
        )

    scan = scan_operator_session(context, session.session_id)
    if scan.handoff_blocked:
        raise OperatorSessionError(
            "operator handoff blocked by blocking leak scanner findings",
            code="operator_handoff_blocked_by_scan",
            remediation=(
                "Inspect the session scan report, remove or redact blockers, "
                "then rebuild the handoff."
            ),
            details={
                "session_id": session.session_id,
                "report_path": scan.report_path.as_posix(),
            },
        )

    events = load_operator_session_events(context, session.session_id)
    handoff = OperatorHandoffBundle(
        handoff_id=operator_handoff_id(session.session_id),
        session_id=session.session_id,
        issue_id=session.issue_id,
        policy_mode=session.policy_mode.value,
        session_status=session.status.value,
        operator_label=session.operator_label,
        started_at=session.started_at,
        finalized_at=session.finalized_at,
        kb_roots=_kb_roots(context),
        referenced_files=_referenced_files(session),
        draft_artifacts=_draft_artifacts(session),
        source_notes=_source_notes(session),
        review_context_records=_review_context_records(session),
        checks=session.check_results,
        check_summary=_check_summary(session.check_results),
        tool_summary=_tool_summary(events),
        scanner=_scanner_summary(scan),
        known_limitations=_known_limitations(session.check_results),
        follow_up_recommendations=_follow_up_recommendations(
            checks=session.check_results,
            scan=scan,
        ),
    )
    return write_operator_handoff(context, handoff)


def write_operator_handoff(
    context: RepoContext,
    handoff: OperatorHandoffBundle,
) -> OperatorHandoffWriteResult:
    """Persist one runtime handoff bundle."""
    relative_path = operator_handoff_path(handoff.handoff_id)
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(handoff.to_json(), encoding="utf-8", newline="\n")
    return OperatorHandoffWriteResult(handoff=handoff, relative_path=relative_path)


def export_operator_handoff(
    context: RepoContext,
    *,
    handoff_id: str,
    dry_run: bool = False,
    target_path: str | Path | None = None,
) -> OperatorHandoffExportResult:
    """Export one handoff as explicit review context under reviews/operator."""
    loaded = load_operator_handoff(context, handoff_id)
    handoff = loaded.handoff
    if handoff.scanner.handoff_blocked or handoff.scanner.blocking_finding_count > 0:
        raise OperatorSessionError(
            "operator handoff export blocked by scanner findings",
            code="operator_handoff_blocked_by_scan",
            remediation=(
                "Rebuild the handoff from a clean scanned session before export."
            ),
            details={
                "handoff_id": handoff.handoff_id,
                "scanner_report": handoff.scanner.report_path,
            },
        )
    relative_target = (
        operator_handoff_export_path(handoff.handoff_id)
        if target_path is None
        else _normalize_export_target(target_path)
    )
    _ensure_operator_handoff_export_target(context, relative_target)
    result = OperatorHandoffExportResult(
        handoff_id=handoff.handoff_id,
        source_runtime_path=loaded.relative_path.as_posix(),
        target_path=relative_target.as_posix(),
        dry_run=dry_run,
        written_paths=() if dry_run else (relative_target.as_posix(),),
        handoff=handoff,
    )
    if not dry_run:
        target = context.resolve(relative_target)
        _ensure_repo_local(context, target)
        write_yaml_deterministic(target, result.to_dict())
    return result


def load_operator_handoff(
    context: RepoContext,
    handoff_id: str,
) -> OperatorHandoffWriteResult:
    """Load one runtime handoff bundle."""
    resolved = validate_artifact_id(handoff_id.strip())
    relative_path = operator_handoff_path(resolved)
    target = context.resolve(relative_path)
    if not target.is_file():
        raise OperatorSessionError(
            f"operator handoff not found: {resolved}",
            code="operator_handoff_not_found",
            remediation="Build the handoff first or pass an existing handoff ID.",
            details={"path": relative_path.as_posix()},
        )
    try:
        raw = json.loads(target.read_text(encoding="utf-8-sig"))
        handoff = OperatorHandoffBundle.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise OperatorSessionError(
            f"operator handoff failed validation: {exc}",
            code="operator_handoff_validation_failed",
            remediation="Inspect the runtime handoff.json file and repair it.",
            details={"path": relative_path.as_posix()},
        ) from exc
    return OperatorHandoffWriteResult(handoff=handoff, relative_path=relative_path)


def operator_handoff_id(session_id: str) -> str:
    """Return deterministic handoff ID for one session."""
    return validate_artifact_id(f"handoff.{validate_artifact_id(session_id.strip())}")


def operator_handoff_path(handoff_id: str) -> Path:
    """Return runtime handoff.json path for one handoff ID."""
    resolved = validate_artifact_id(handoff_id.strip())
    prefix = "handoff."
    if not resolved.startswith(prefix):
        raise OperatorSessionError(
            f"operator handoff ID must start with {prefix}: {resolved}",
            code="operator_handoff_validation_failed",
            remediation=(
                "Use a handoff ID returned by "
                "`cosheaf operator handoff build`."
            ),
        )
    session_id = validate_artifact_id(resolved.removeprefix(prefix))
    return Path(".cosheaf") / "operator-sessions" / session_id / "handoff.json"


def operator_handoff_export_path(handoff_id: str) -> Path:
    """Return the explicit review-context export path for one handoff ID."""
    resolved = validate_artifact_id(handoff_id.strip())
    return Path("reviews") / "operator" / f"{resolved}.yaml"


def _kb_roots(context: RepoContext) -> tuple[OperatorHandoffKbRoot, ...]:
    return tuple(
        OperatorHandoffKbRoot(
            name=root.name,
            path=root.path,
            readonly=root.readonly,
            priority=root.priority,
        )
        for root in context.workspace_config.ordered_kb
    )


def _referenced_files(session: Any) -> tuple[str, ...]:
    return tuple(ref.path for ref in session.artifact_refs if ref.path is not None)


def _draft_artifacts(session: Any) -> tuple[str, ...]:
    return tuple(
        ref.artifact_id
        for ref in session.artifact_refs
        if ref.kind is OperatorArtifactRefKind.DRAFT and ref.artifact_id is not None
    )


def _source_notes(session: Any) -> tuple[str, ...]:
    return tuple(
        ref.path
        for ref in session.artifact_refs
        if ref.kind is OperatorArtifactRefKind.SOURCE_NOTE and ref.path is not None
    )


def _review_context_records(session: Any) -> tuple[str, ...]:
    return tuple(
        ref.path
        for ref in session.artifact_refs
        if ref.kind is OperatorArtifactRefKind.REVIEW_CONTEXT and ref.path is not None
    )


def _check_summary(
    checks: tuple[OperatorCheckResult, ...],
) -> OperatorHandoffCheckSummary:
    latest: dict[OperatorCheckKind, OperatorCheckStatus] = {
        check.kind: check.status for check in checks
    }
    missing = tuple(
        kind.value for kind in OPERATOR_HANDOFF_REQUIRED_CHECKS if kind not in latest
    )
    return OperatorHandoffCheckSummary(
        passed=_check_kinds_with_status(latest, OperatorCheckStatus.PASS),
        failed=_check_kinds_with_status(latest, OperatorCheckStatus.FAIL),
        errored=_check_kinds_with_status(latest, OperatorCheckStatus.ERROR),
        skipped=_check_kinds_with_status(latest, OperatorCheckStatus.SKIPPED),
        missing=missing,
        all_required_recorded=not missing,
    )


def _check_kinds_with_status(
    statuses: dict[OperatorCheckKind, OperatorCheckStatus],
    wanted: OperatorCheckStatus,
) -> tuple[str, ...]:
    return tuple(
        kind.value
        for kind in OPERATOR_HANDOFF_REQUIRED_CHECKS
        if statuses.get(kind) is wanted
    )


def _tool_summary(
    events: tuple[OperatorSessionEvent, ...],
) -> dict[str, OperatorHandoffToolStatusCounts]:
    counts: dict[str, dict[str, int]] = {}
    for event in events:
        if event.event_kind != "tool_call":
            continue
        tool_name = str(event.event.get("tool_name", "")).strip()
        if not tool_name:
            continue
        status = str(event.event.get("status", "")).strip()
        tool_counts = counts.setdefault(
            tool_name,
            {"completed": 0, "denied": 0, "error": 0, "failed": 0},
        )
        if status in tool_counts:
            tool_counts[status] += 1
    return {
        tool_name: OperatorHandoffToolStatusCounts.model_validate(status_counts)
        for tool_name, status_counts in sorted(counts.items())
    }


def _scanner_summary(scan: OperatorSessionScanResult) -> OperatorHandoffScannerSummary:
    return OperatorHandoffScannerSummary(
        report_path=scan.report_path.as_posix(),
        finding_count=scan.finding_count,
        blocking_finding_count=scan.blocking_finding_count,
        handoff_blocked=scan.handoff_blocked,
        findings=tuple(_finding_payload(finding) for finding in scan.findings),
    )


def _finding_payload(finding: OperatorSessionScanFinding) -> dict[str, Any]:
    return finding.to_dict()


def _known_limitations(
    checks: tuple[OperatorCheckResult, ...],
) -> tuple[str, ...]:
    limitations = [
        "Handoff bundles are review context only.",
        "Handoff bundles do not create human review.",
        "Handoff bundles do not promote artifacts or mark accepted/refuted/proved.",
        "Validation, gate, test, eval, and scan results must be inspected separately.",
    ]
    if any(check.status is OperatorCheckStatus.SKIPPED for check in checks):
        limitations.append("Skipped checks are not pass evidence.")
    return tuple(limitations)


def _follow_up_recommendations(
    *,
    checks: tuple[OperatorCheckResult, ...],
    scan: OperatorSessionScanResult,
) -> tuple[str, ...]:
    summary = _check_summary(checks)
    recommendations = [
        "Review referenced draft, source-note, and review-context files manually.",
        "Confirm source metadata and human review outside this handoff bundle.",
    ]
    if summary.missing:
        recommendations.append(
            "Record missing check results before relying on this handoff: "
            + ", ".join(summary.missing)
            + "."
        )
    if summary.skipped:
        recommendations.append(
            "Inspect skipped checks separately; skipped is not pass evidence: "
            + ", ".join(summary.skipped)
            + "."
        )
    if scan.finding_count == 0:
        recommendations.append(
            "Leak scanner found no blockers, but this is not human review."
        )
    return tuple(recommendations)


def _validate_repo_local_nonaccepted_path(value: str) -> str:
    raw = str(value).strip()
    normalized = normalize_repo_path(raw)
    is_absolute = Path(raw).is_absolute() or PureWindowsPath(raw).is_absolute()
    parts = PurePosixPath(normalized).parts
    if (
        not normalized
        or is_absolute
        or raw.startswith("/")
        or normalized == ".."
        or normalized.startswith("../")
        or normalized == "."
        or ".." in parts
    ):
        raise ValueError("path must be repository-local")
    if parts and parts[0] == "kb" and "accepted" in parts:
        raise ValueError("operator handoff records cannot reference accepted KB paths")
    return normalized


def _normalize_export_target(value: str | Path) -> Path:
    normalized = _validate_repo_local_path(str(value))
    return Path(normalized)


def _validate_repo_local_path(value: str) -> str:
    raw = str(value).strip()
    normalized = normalize_repo_path(raw)
    is_absolute = Path(raw).is_absolute() or PureWindowsPath(raw).is_absolute()
    parts = PurePosixPath(normalized).parts
    if (
        not normalized
        or is_absolute
        or raw.startswith("/")
        or normalized == ".."
        or normalized.startswith("../")
        or normalized == "."
        or ".." in parts
    ):
        raise ValueError("path must be repository-local")
    return normalized


def _ensure_operator_handoff_export_target(
    context: RepoContext,
    relative_target: Path,
) -> None:
    normalized = normalize_repo_path(relative_target)
    if normalized.startswith("kb/accepted/") or "/accepted/" in normalized:
        raise OperatorSessionError(
            "operator handoff export target must not be an accepted KB path",
            code="accepted_write_forbidden",
            remediation="Export handoff review context under reviews/operator/ only.",
            details={"path": normalized},
        )
    if not normalized.startswith("reviews/operator/"):
        raise OperatorSessionError(
            "operator handoff export target must be under reviews/operator/",
            code="invalid_operator_handoff_export_path",
            remediation=(
                "Use the deterministic reviews/operator/<handoff-id>.yaml path."
            ),
            details={"path": normalized},
        )
    if Path(normalized).suffix.lower() not in {".yaml", ".yml"}:
        raise OperatorSessionError(
            "operator handoff export target must be YAML",
            code="invalid_operator_handoff_export_path",
            remediation=(
                "Use the deterministic reviews/operator/<handoff-id>.yaml path."
            ),
            details={"path": normalized},
        )
    _ensure_repo_local(context, context.resolve(relative_target))


def _ensure_repo_local(context: RepoContext, target: Path) -> None:
    try:
        target.resolve().relative_to(context.repo_root.resolve())
    except ValueError as exc:
        raise OperatorSessionError(
            "operator handoff target must stay repository-local",
            code="invalid_operator_handoff_path",
            remediation="Use the controlled .cosheaf/operator-sessions path.",
        ) from exc
    relative = repo_relative_posix(context.repo_root, target)
    if relative.startswith("kb/accepted/") or "/accepted/" in relative:
        raise OperatorSessionError(
            "operator handoff target must not be an accepted KB path",
            code="accepted_write_forbidden",
            remediation="Use runtime storage or review-context export paths only.",
        )


__all__ = [
    "OPERATOR_HANDOFF_KIND",
    "OPERATOR_HANDOFF_REQUIRED_CHECKS",
    "OperatorHandoffBundle",
    "OperatorHandoffCheckSummary",
    "OperatorHandoffExportResult",
    "OperatorHandoffKbRoot",
    "OperatorHandoffScannerSummary",
    "OperatorHandoffToolStatusCounts",
    "OperatorHandoffWriteResult",
    "build_operator_handoff",
    "export_operator_handoff",
    "load_operator_handoff",
    "operator_handoff_export_path",
    "operator_handoff_id",
    "operator_handoff_path",
    "write_operator_handoff",
]
