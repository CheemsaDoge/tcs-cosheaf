"""Repository-local research-run provenance records.

Research-run records are provenance only. They do not prove claims, create
human review, authorize gate passes, or grant accepted-promotion authority.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cosheaf.agent.run_logging import SECRET_VALUE_PATTERN, redact_command
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path
from cosheaf.storage.repo import RepoContext
from cosheaf.storage.writer import write_yaml_deterministic

RESEARCH_RUN_AUTHORITY_NOTICE = (
    "Research run records are provenance for review only; they are not proof, "
    "verifier pass, gate pass, human review, accepted status, or promotion "
    "authority."
)
SKIPPED_RESEARCH_RUN_LIMITATION = (
    "Skipped research-run steps are not pass evidence."
)
RESEARCH_RUN_RUNTIME_ROOT = Path(".cosheaf") / "runs"
RESEARCH_RUN_REVIEW_ROOT = Path("reviews") / "runs"
AUTHORITY_CLAIM_FIELDS = frozenset(
    {
        "accepted",
        "accepted_write_performed",
        "artifact_status",
        "gate_pass",
        "human_review",
        "human_reviewed",
        "promote",
        "promotion_authority",
        "review_state",
        "verifier_pass",
    }
)
HIDDEN_REASONING_FIELDS = frozenset(
    {"chain_of_thought", "hidden_reasoning", "reasoning_trace"}
)


class ResearchRunError(ValueError):
    """Expected research-run service failure."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        remediation: str,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.remediation = remediation
        self.details = dict(details or {})


class ResearchRunOperatorKind(StrEnum):
    """Who or what operated a research run."""

    EXTERNAL = "external"
    HUMAN = "human"
    LOCAL = "local"


class ResearchRunStatus(StrEnum):
    """Lifecycle state for a research run."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ResearchRunCommandStatus(StrEnum):
    """Normalized command record status."""

    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"
    UNAVAILABLE = "unavailable"


class ResearchRunOutputKind(StrEnum):
    """Reviewable output categories a run can reference."""

    WORKSPACE_INFO = "workspace_info"
    CONTEXT_PACK = "context_pack"
    CONTROLLED_WRITE = "controlled_write"
    WORKER_BUNDLE = "worker_bundle"
    VERIFIER_EVIDENCE = "verifier_evidence"
    CHECKED_COUNTEREXAMPLE_EVIDENCE = "checked_counterexample_evidence"
    FAILURE_LOG = "failure_log"
    VALIDATION_REPORT = "validation_report"
    GATE_REPORT = "gate_report"
    PR_REFERENCE = "pr_reference"
    ISSUE_REFERENCE = "issue_reference"
    OTHER = "other"


class ResearchRunModel(BaseModel):
    """Strict base model for research-run DTOs."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable mapping."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON for this model."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class ResearchRunCommandRecord(ResearchRunModel):
    """One external command observed during a research run."""

    argv: tuple[str, ...]
    cwd: str = "."
    started_at: datetime
    ended_at: datetime | None = None
    exit_code: int | None = None
    status: ResearchRunCommandStatus
    stdout_path: str | None = None
    stdout_sha256: str | None = None
    stderr_path: str | None = None
    stderr_sha256: str | None = None
    skipped_reason: str | None = None
    unavailable_reason: str | None = None
    redaction_applied: bool = False

    @model_validator(mode="before")
    @classmethod
    def _redact_argv(cls, value: Any) -> Any:
        if not isinstance(value, dict) or "argv" not in value:
            return value
        data = dict(value)
        raw_argv = _text_items(data["argv"])
        redacted = tuple(redact_command(list(raw_argv)))
        data["argv"] = redacted
        data["redaction_applied"] = bool(
            data.get("redaction_applied", False) or redacted != raw_argv
        )
        return data

    @field_validator("argv", mode="before")
    @classmethod
    def _argv(cls, value: Any) -> tuple[str, ...]:
        argv = _text_items(value)
        if not argv:
            raise ValueError("argv must contain at least one argument")
        return argv

    @field_validator("cwd")
    @classmethod
    def _cwd(cls, value: str) -> str:
        return _validate_repo_local_path(value, allow_dot=True)

    @field_validator("stdout_path", "stderr_path")
    @classmethod
    def _paths(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_repo_local_path(value)

    @field_validator("stdout_sha256", "stderr_sha256")
    @classmethod
    def _hash(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        if _contains_secret(normalized):
            raise ValueError("hash fields must not contain secret-looking values")
        return normalized

    @field_validator("skipped_reason", "unavailable_reason")
    @classmethod
    def _safe_optional_text(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)

    @field_validator("started_at", "ended_at")
    @classmethod
    def _timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return _normalize_timestamp(value)

    @model_validator(mode="after")
    def _consistency(self) -> Self:
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("ended_at must not be earlier than started_at")
        if self.status is ResearchRunCommandStatus.SKIPPED:
            if not self.skipped_reason:
                raise ValueError("skipped command records require skipped_reason")
            if SKIPPED_RESEARCH_RUN_LIMITATION.lower() not in (
                self.skipped_reason.lower()
            ):
                raise ValueError("skipped command records must say skipped is not pass")
        if self.status is ResearchRunCommandStatus.UNAVAILABLE:
            if not self.unavailable_reason:
                raise ValueError(
                    "unavailable command records require unavailable_reason"
                )
        return self


class ResearchRunOutputRef(ResearchRunModel):
    """One repository-local output or reference attached to a run."""

    kind: ResearchRunOutputKind
    path: str | None = None
    identifier: str | None = None
    sha256: str | None = None
    status: str | None = None
    summary: str | None = None

    @field_validator("path")
    @classmethod
    def _path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_repo_local_path(value)

    @field_validator("identifier", "sha256", "status", "summary")
    @classmethod
    def _safe_optional_text(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)

    @model_validator(mode="after")
    def _has_path_or_identifier(self) -> Self:
        if self.path is None and self.identifier is None:
            raise ValueError("output references require path or identifier")
        if self.status == "skipped" and (
            not self.summary
            or SKIPPED_RESEARCH_RUN_LIMITATION.lower() not in self.summary.lower()
        ):
            raise ValueError("skipped output references must say skipped is not pass")
        return self


class ResearchRunRecord(ResearchRunModel):
    """Durable v1 research-run provenance record."""

    schema_version: Literal[1] = 1
    run_id: str
    issue_id: str
    operator_kind: ResearchRunOperatorKind
    operator_label: str
    status: ResearchRunStatus
    started_at: datetime
    ended_at: datetime | None = None
    stop_reason: str | None = None
    base_commit: str | None = None
    head_commit: str | None = None
    dirty_state_note: str | None = None
    workspace_info_summary: ResearchRunOutputRef | None = None
    context_packs: tuple[ResearchRunOutputRef, ...] = ()
    commands: tuple[ResearchRunCommandRecord, ...] = ()
    artifacts_read: tuple[str, ...] = ()
    artifacts_touched: tuple[str, ...] = ()
    controlled_write_outputs: tuple[ResearchRunOutputRef, ...] = ()
    worker_bundle_paths: tuple[ResearchRunOutputRef, ...] = ()
    verifier_evidence_paths: tuple[ResearchRunOutputRef, ...] = ()
    checked_counterexample_evidence_paths: tuple[ResearchRunOutputRef, ...] = ()
    failure_log_entries_added: tuple[ResearchRunOutputRef, ...] = ()
    validation_reports: tuple[ResearchRunOutputRef, ...] = ()
    gate_reports: tuple[ResearchRunOutputRef, ...] = ()
    pr_references: tuple[str, ...] = ()
    issue_references: tuple[str, ...] = ()
    limitations: tuple[str, ...] = Field(
        default_factory=lambda: (RESEARCH_RUN_AUTHORITY_NOTICE,)
    )
    operator_notes: tuple[str, ...] = ()
    authority_notice: str = RESEARCH_RUN_AUTHORITY_NOTICE
    accepted_write_performed: Literal[False] = False

    @classmethod
    def start(
        cls,
        *,
        run_id: str,
        issue_id: str,
        operator_kind: ResearchRunOperatorKind | str,
        operator_label: str,
        now: datetime | None = None,
        base_commit: str | None = None,
        dirty_state_note: str | None = None,
    ) -> ResearchRunRecord:
        """Create an in-progress research run record."""
        timestamp = _normalize_timestamp(now or _utc_now())
        return cls(
            run_id=run_id,
            issue_id=issue_id,
            operator_kind=ResearchRunOperatorKind(operator_kind),
            operator_label=operator_label,
            status=ResearchRunStatus.IN_PROGRESS,
            started_at=timestamp,
            base_commit=base_commit,
            dirty_state_note=dirty_state_note,
        )

    @field_validator("run_id", "issue_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("operator_label")
    @classmethod
    def _operator_label(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("base_commit", "head_commit", "dirty_state_note", "stop_reason")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)

    @field_validator("started_at", "ended_at")
    @classmethod
    def _timestamps(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return _normalize_timestamp(value)

    @field_validator("artifacts_read", "artifacts_touched", mode="before")
    @classmethod
    def _artifact_ids(cls, value: Any) -> tuple[str, ...]:
        return _dedupe(validate_artifact_id(item) for item in _text_items(value))

    @field_validator("pr_references", "issue_references", mode="before")
    @classmethod
    def _refs(cls, value: Any) -> tuple[str, ...]:
        return _dedupe(_safe_text(item) for item in _text_items(value))

    @field_validator("limitations", "operator_notes", mode="before")
    @classmethod
    def _safe_text_tuple(cls, value: Any) -> tuple[str, ...]:
        return _dedupe(_safe_text(item) for item in _text_items(value))

    @model_validator(mode="after")
    def _consistency(self) -> Self:
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("ended_at must not be earlier than started_at")
        if self.status is ResearchRunStatus.IN_PROGRESS:
            if self.ended_at is not None or self.stop_reason is not None:
                raise ValueError("in-progress runs cannot have ended_at or stop_reason")
        else:
            if self.ended_at is None:
                raise ValueError("terminal runs require ended_at")
            if not self.stop_reason:
                raise ValueError("terminal runs require stop_reason")
        if RESEARCH_RUN_AUTHORITY_NOTICE not in self.limitations:
            raise ValueError("limitations must include research-run authority notice")
        if self.authority_notice != RESEARCH_RUN_AUTHORITY_NOTICE:
            raise ValueError("authority_notice must preserve research-run boundary")
        return self

    def with_command(
        self,
        command: ResearchRunCommandRecord,
    ) -> ResearchRunRecord:
        """Return a copy with one command appended."""
        self._ensure_mutable()
        return self._replace(commands=(*self.commands, command))

    def with_artifact(self, artifact_id: str, *, mode: str) -> ResearchRunRecord:
        """Return a copy with an artifact read/touched marker appended."""
        self._ensure_mutable()
        artifact = validate_artifact_id(artifact_id.strip())
        if mode == "read":
            return self._replace(
                artifacts_read=_dedupe((*self.artifacts_read, artifact))
            )
        if mode == "touched":
            return self._replace(
                artifacts_touched=_dedupe((*self.artifacts_touched, artifact))
            )
        raise ValueError("artifact mode must be 'read' or 'touched'")

    def with_output(self, output: ResearchRunOutputRef) -> ResearchRunRecord:
        """Return a copy with one output reference appended to its category."""
        self._ensure_mutable()
        if output.kind is ResearchRunOutputKind.WORKSPACE_INFO:
            return self._replace(workspace_info_summary=output)
        if output.kind is ResearchRunOutputKind.CONTEXT_PACK:
            return self._replace(context_packs=(*self.context_packs, output))
        if output.kind is ResearchRunOutputKind.CONTROLLED_WRITE:
            return self._replace(
                controlled_write_outputs=(*self.controlled_write_outputs, output)
            )
        if output.kind is ResearchRunOutputKind.WORKER_BUNDLE:
            return self._replace(
                worker_bundle_paths=(*self.worker_bundle_paths, output)
            )
        if output.kind is ResearchRunOutputKind.VERIFIER_EVIDENCE:
            return self._replace(
                verifier_evidence_paths=(*self.verifier_evidence_paths, output)
            )
        if output.kind is ResearchRunOutputKind.CHECKED_COUNTEREXAMPLE_EVIDENCE:
            return self._replace(
                checked_counterexample_evidence_paths=(
                    *self.checked_counterexample_evidence_paths,
                    output,
                )
            )
        if output.kind is ResearchRunOutputKind.FAILURE_LOG:
            return self._replace(
                failure_log_entries_added=(*self.failure_log_entries_added, output)
            )
        if output.kind is ResearchRunOutputKind.VALIDATION_REPORT:
            return self._replace(validation_reports=(*self.validation_reports, output))
        if output.kind is ResearchRunOutputKind.GATE_REPORT:
            return self._replace(gate_reports=(*self.gate_reports, output))
        if output.kind is ResearchRunOutputKind.PR_REFERENCE and output.identifier:
            return self._replace(
                pr_references=_dedupe((*self.pr_references, output.identifier))
            )
        if output.kind is ResearchRunOutputKind.ISSUE_REFERENCE and output.identifier:
            return self._replace(
                issue_references=_dedupe((*self.issue_references, output.identifier))
            )
        note = output.summary or output.identifier or output.path or "other output"
        return self._replace(operator_notes=_dedupe((*self.operator_notes, note)))

    def finalize(
        self,
        *,
        status: ResearchRunStatus | str,
        stop_reason: str,
        now: datetime | None = None,
        head_commit: str | None = None,
    ) -> ResearchRunRecord:
        """Return a terminal research run record."""
        self._ensure_mutable()
        resolved = ResearchRunStatus(status)
        if resolved is ResearchRunStatus.IN_PROGRESS:
            raise ValueError("final status must be terminal")
        return self._replace(
            status=resolved,
            ended_at=_normalize_timestamp(now or _utc_now()),
            stop_reason=_safe_text(stop_reason),
            head_commit=head_commit,
        )

    def _replace(self, **updates: Any) -> ResearchRunRecord:
        data = self.model_dump(mode="python")
        data.update(updates)
        return ResearchRunRecord.model_validate(data)

    def _ensure_mutable(self) -> None:
        if self.status is not ResearchRunStatus.IN_PROGRESS:
            raise ValueError("terminal research runs cannot be modified")


@dataclass(frozen=True)
class ResearchRunWriteResult:
    """Result for writing or updating a runtime research run."""

    record: ResearchRunRecord
    relative_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "research_run",
            "run_id": self.record.run_id,
            "status": self.record.status.value,
            "path": self.relative_path.as_posix(),
            "accepted_write_performed": False,
            "authority_notice": RESEARCH_RUN_AUTHORITY_NOTICE,
            "command_count": len(self.record.commands),
            "run": self.record.to_dict(),
        }


@dataclass(frozen=True)
class ResearchRunReviewExportResult:
    """Result for review export or dry-run export."""

    record: ResearchRunRecord
    relative_path: Path
    written_paths: tuple[Path, ...]
    dry_run: bool
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "research_run_review_export",
            "run_id": self.record.run_id,
            "path": self.relative_path.as_posix(),
            "written_paths": [path.as_posix() for path in self.written_paths],
            "dry_run": self.dry_run,
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": RESEARCH_RUN_AUTHORITY_NOTICE,
            "run": self.record.to_dict(),
        }


def start_research_run(
    context: RepoContext,
    *,
    issue_id: str,
    operator_kind: ResearchRunOperatorKind | str,
    operator_label: str,
    run_id: str | None = None,
    now: datetime | None = None,
) -> ResearchRunWriteResult:
    """Create and persist a new runtime research run."""
    timestamp = _normalize_timestamp(now or _utc_now())
    resolved_issue = validate_artifact_id(issue_id.strip())
    resolved_run_id = validate_artifact_id(
        run_id.strip() if run_id else _default_run_id(resolved_issue, timestamp)
    )
    relative_path = _runtime_relative_path(resolved_run_id)
    target = context.resolve(relative_path)
    if target.exists():
        raise ResearchRunError(
            f"research run already exists: {resolved_run_id}",
            code="research_run_path_exists",
            remediation="Use a new run_id or show the existing run.",
            details={"path": relative_path.as_posix()},
        )
    record = ResearchRunRecord.start(
        run_id=resolved_run_id,
        issue_id=resolved_issue,
        operator_kind=operator_kind,
        operator_label=operator_label,
        now=timestamp,
        base_commit=_git_commit(context.repo_root),
        dirty_state_note=_git_dirty_note(context.repo_root),
    )
    _write_runtime_record(context, record, relative_path)
    return ResearchRunWriteResult(record=record, relative_path=relative_path)


def load_research_run(context: RepoContext, run_id: str) -> ResearchRunWriteResult:
    """Load a runtime research run by ID."""
    resolved = validate_artifact_id(run_id.strip())
    relative_path = _runtime_relative_path(resolved)
    path = context.resolve(relative_path)
    if not path.is_file():
        raise ResearchRunError(
            f"research run not found: {resolved}",
            code="research_run_not_found",
            remediation="Start the run first or pass an existing run_id.",
            details={"path": relative_path.as_posix()},
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        record = ResearchRunRecord.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ResearchRunError(
            f"research run failed validation: {exc}",
            code="research_run_validation_failed",
            remediation="Inspect the runtime run.json file and repair the record.",
            details={"path": relative_path.as_posix()},
        ) from exc
    return ResearchRunWriteResult(record=record, relative_path=relative_path)


def append_command_to_research_run(
    context: RepoContext,
    *,
    run_id: str,
    payload: dict[str, Any],
) -> ResearchRunWriteResult:
    """Append a command record to an in-progress run."""
    reject_forbidden_run_payload(payload)
    loaded = load_research_run(context, run_id)
    try:
        command = ResearchRunCommandRecord.model_validate(payload)
        record = loaded.record.with_command(command)
    except ValueError as exc:
        raise _validation_error(exc) from exc
    _write_runtime_record(context, record, loaded.relative_path)
    return ResearchRunWriteResult(record=record, relative_path=loaded.relative_path)


def append_artifact_to_research_run(
    context: RepoContext,
    *,
    run_id: str,
    artifact_id: str,
    mode: str,
) -> ResearchRunWriteResult:
    """Append an artifact read/touched marker."""
    loaded = load_research_run(context, run_id)
    try:
        record = loaded.record.with_artifact(artifact_id, mode=mode)
    except ValueError as exc:
        raise _validation_error(exc) from exc
    _write_runtime_record(context, record, loaded.relative_path)
    return ResearchRunWriteResult(record=record, relative_path=loaded.relative_path)


def append_output_to_research_run(
    context: RepoContext,
    *,
    run_id: str,
    payload: dict[str, Any],
) -> ResearchRunWriteResult:
    """Append one output/reference payload to an in-progress run."""
    reject_forbidden_run_payload(payload)
    loaded = load_research_run(context, run_id)
    try:
        output = ResearchRunOutputRef.model_validate(payload)
        record = loaded.record.with_output(output)
    except ValueError as exc:
        raise _validation_error(exc) from exc
    _write_runtime_record(context, record, loaded.relative_path)
    return ResearchRunWriteResult(record=record, relative_path=loaded.relative_path)


def finalize_research_run(
    context: RepoContext,
    *,
    run_id: str,
    status: ResearchRunStatus | str,
    stop_reason: str,
    now: datetime | None = None,
) -> ResearchRunWriteResult:
    """Finalize a runtime run with a terminal status."""
    loaded = load_research_run(context, run_id)
    try:
        record = loaded.record.finalize(
            status=status,
            stop_reason=stop_reason,
            now=now,
            head_commit=_git_commit(context.repo_root),
        )
    except ValueError as exc:
        raise _validation_error(exc) from exc
    _write_runtime_record(context, record, loaded.relative_path)
    return ResearchRunWriteResult(record=record, relative_path=loaded.relative_path)


def export_research_run_review(
    context: RepoContext,
    *,
    run_id: str,
    dry_run: bool,
) -> ResearchRunReviewExportResult:
    """Export a runtime run to review-controlled YAML."""
    loaded = load_research_run(context, run_id)
    relative_path = RESEARCH_RUN_REVIEW_ROOT / f"{loaded.record.run_id}.yaml"
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    if target.exists() and not dry_run:
        raise ResearchRunError(
            f"research run review export already exists: {relative_path.as_posix()}",
            code="research_run_path_exists",
            remediation="Inspect the existing review export before replacing it.",
            details={"path": relative_path.as_posix()},
        )
    written: tuple[Path, ...] = ()
    if not dry_run:
        write_yaml_deterministic(target, loaded.record.to_dict())
        written = (relative_path,)
    return ResearchRunReviewExportResult(
        record=loaded.record,
        relative_path=relative_path,
        written_paths=written,
        dry_run=dry_run,
    )


def build_research_run_evidence_report(record: ResearchRunRecord) -> dict[str, Any]:
    """Build a read-only evidence report for one research run."""
    skipped_commands = [
        command for command in record.commands if command.status == "skipped"
    ]
    return {
        "schema_version": 1,
        "kind": "research_run_evidence_report",
        "run_id": record.run_id,
        "issue_id": record.issue_id,
        "status": record.status.value,
        "command_count": len(record.commands),
        "skipped_command_count": len(skipped_commands),
        "artifact_read_count": len(record.artifacts_read),
        "artifact_touched_count": len(record.artifacts_touched),
        "controlled_write_count": len(record.controlled_write_outputs),
        "worker_bundle_count": len(record.worker_bundle_paths),
        "verifier_evidence_count": len(record.verifier_evidence_paths),
        "checked_counterexample_evidence_count": len(
            record.checked_counterexample_evidence_paths
        ),
        "failure_log_count": len(record.failure_log_entries_added),
        "validation_report_count": len(record.validation_reports),
        "gate_report_count": len(record.gate_reports),
        "accepted_write_performed": False,
        "authority_notice": RESEARCH_RUN_AUTHORITY_NOTICE,
        "limitations": list(record.limitations),
    }


def build_replay_plan(record: ResearchRunRecord) -> dict[str, Any]:
    """Build a read-only command replay plan from recorded command metadata."""
    return {
        "schema_version": 1,
        "kind": "research_run_replay_plan",
        "run_id": record.run_id,
        "issue_id": record.issue_id,
        "read_only": True,
        "execution_performed": False,
        "accepted_write_performed": False,
        "authority_notice": RESEARCH_RUN_AUTHORITY_NOTICE,
        "commands": [
            {
                "argv": list(command.argv),
                "cwd": command.cwd,
                "recorded_status": command.status.value,
                "recorded_exit_code": command.exit_code,
                "skipped_reason": command.skipped_reason,
                "unavailable_reason": command.unavailable_reason,
            }
            for command in record.commands
        ],
    }


def reject_forbidden_run_payload(payload: dict[str, Any]) -> None:
    """Reject authority or hidden-reasoning spoofing fields."""
    forbidden = sorted(AUTHORITY_CLAIM_FIELDS.intersection(payload))
    if forbidden:
        raise ResearchRunError(
            "research run payload cannot claim review, accepted, verifier, gate, "
            "or promotion authority",
            code="authority_claim_forbidden",
            remediation="Remove authority fields; run records are provenance only.",
            details={"forbidden_fields": ",".join(forbidden)},
        )
    hidden = sorted(HIDDEN_REASONING_FIELDS.intersection(payload))
    if hidden:
        raise ResearchRunError(
            "research run payload cannot store hidden reasoning fields",
            code="research_run_validation_failed",
            remediation="Store only concise operator notes or output summaries.",
            details={"forbidden_fields": ",".join(hidden)},
        )


def _write_runtime_record(
    context: RepoContext,
    record: ResearchRunRecord,
    relative_path: Path,
) -> None:
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(record.to_json(), encoding="utf-8", newline="\n")


def _runtime_relative_path(run_id: str) -> Path:
    return RESEARCH_RUN_RUNTIME_ROOT / run_id / "run.json"


def _default_run_id(issue_id: str, timestamp: datetime) -> str:
    slug = timestamp.strftime("r%Y%m%d.t%H%M%Sz")
    return validate_artifact_id(f"run.{issue_id}.{slug}")


def _git_commit(repo_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    commit = completed.stdout.strip()
    return commit or None


def _git_dirty_note(repo_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "git status unavailable"
    if completed.returncode != 0:
        return "git status unavailable"
    return "dirty" if completed.stdout.strip() else "clean"


def _validation_error(exc: ValueError) -> ResearchRunError:
    return ResearchRunError(
        _redacted_message(str(exc)),
        code="research_run_validation_failed",
        remediation="Fix the research-run payload and retry.",
    )


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")
    return value.astimezone(UTC).replace(microsecond=0)


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _validate_repo_local_path(value: str, *, allow_dot: bool = False) -> str:
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
        or (normalized == "." and not allow_dot)
        or ".." in parts
    ):
        raise ValueError("path must be repository-local")
    if parts and parts[0] == "kb" and "accepted" in parts:
        raise ValueError("research run records cannot reference accepted KB paths")
    return normalized


def _ensure_repo_local(context: RepoContext, target: Path) -> None:
    try:
        target.resolve().relative_to(context.repo_root.resolve())
    except ValueError as exc:
        raise ResearchRunError(
            "research run target must stay repository-local",
            code="invalid_staging_path",
            remediation="Use the controlled research-run runtime or review path.",
        ) from exc


def _text_items(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    values: tuple[str, ...]
    if isinstance(value, str):
        values = (value,)
    else:
        try:
            values = tuple(str(item) for item in value)
        except TypeError as exc:
            raise ValueError("field must be a sequence of strings") from exc
    return tuple(item.strip() for item in values if item.strip())


def _dedupe(values: Any) -> tuple[Any, ...]:
    seen: set[Any] = set()
    result: list[Any] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return tuple(result)


def _safe_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return _safe_text(normalized)


def _safe_text(value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError("text field must be non-empty")
    if _contains_secret(normalized):
        raise ValueError("text field contains secret-looking value")
    return normalized


def _contains_secret(value: str) -> bool:
    return bool(SECRET_VALUE_PATTERN.search(value))


def _redacted_message(value: str) -> str:
    return SECRET_VALUE_PATTERN.sub("<redacted>", value)


__all__ = [
    "AUTHORITY_CLAIM_FIELDS",
    "RESEARCH_RUN_AUTHORITY_NOTICE",
    "RESEARCH_RUN_RUNTIME_ROOT",
    "RESEARCH_RUN_REVIEW_ROOT",
    "SKIPPED_RESEARCH_RUN_LIMITATION",
    "ResearchRunCommandRecord",
    "ResearchRunCommandStatus",
    "ResearchRunError",
    "ResearchRunOperatorKind",
    "ResearchRunOutputKind",
    "ResearchRunOutputRef",
    "ResearchRunRecord",
    "ResearchRunReviewExportResult",
    "ResearchRunStatus",
    "ResearchRunWriteResult",
    "append_artifact_to_research_run",
    "append_command_to_research_run",
    "append_output_to_research_run",
    "build_replay_plan",
    "build_research_run_evidence_report",
    "export_research_run_review",
    "finalize_research_run",
    "load_research_run",
    "reject_forbidden_run_payload",
    "start_research_run",
]
