"""Review handoff packets for reviewable workflow output."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path
from cosheaf.security.provider_logs import scan_provider_log_text
from cosheaf.storage.repo import RepoContext
from cosheaf.storage.writer import write_yaml_deterministic
from cosheaf.workflow.engine import (
    WorkflowError,
    WorkflowRecord,
    load_workflow,
    workflow_events_path,
    workflow_fsm_path,
    workflow_librarian_path,
    workflow_loop_path,
    workflow_path,
    workflow_readiness_path,
    workflow_root,
)
from cosheaf.workflow.proposal import build_draft_proposal

WORKFLOW_HANDOFF_KIND = "workflow_handoff_bundle"
WORKFLOW_HANDOFF_SCAN_KIND = "workflow_handoff_scan"
WORKFLOW_HANDOFF_AUTHORITY_NOTICE = (
    "Workflow handoff packets are review context only; they are not proof, "
    "source metadata, human review, verifier pass, gate pass, accepted status, "
    "accepted theorem/refutation, or promotion authority."
)
WORKFLOW_HANDOFF_REVIEW_CHECKLIST: tuple[str, ...] = (
    "Confirm candidate claims against durable public sources.",
    "Add source metadata separately before any accepted promotion.",
    "Run validation and gates independently before review.",
    "Confirm skipped workflow or verifier results are not treated as pass evidence.",
    "Record explicit human review outside this workflow handoff.",
    "Confirm no accepted write, promotion, or verifier mutation occurred.",
)

FINDING_MESSAGES = {
    "api_key": "workflow handoff contains an API-key-shaped value",
    "bearer_token": "workflow handoff contains an unredacted bearer token",
    "environment_dump": "workflow handoff contains an environment-like dump",
    "secret_env_value": "workflow handoff contains a secret-looking key with a value",
    "hidden_reasoning": "workflow handoff contains hidden-reasoning marker text",
    "absolute_private_path": (
        "workflow handoff contains an absolute user or private filesystem path"
    ),
    "accepted_write_attempt": "workflow handoff references an accepted KB write target",
    "provider_payload": "workflow handoff stores raw provider request/response data",
    "private_path_reference": "workflow handoff references private KB path material",
    "human_review_overclaim": "workflow handoff claims or creates human review",
    "verifier_gate_overclaim": (
        "workflow handoff claims verifier or gate pass authority"
    ),
    "source_metadata_fabrication": (
        "workflow handoff claims or embeds source metadata authority"
    ),
    "accepted_theorem_or_refutation": (
        "workflow handoff claims accepted theorem/refutation status without promotion"
    ),
    "handoff_json_invalid": "workflow handoff JSON could not be parsed",
    "workflow_json_invalid": "workflow runtime JSON could not be parsed",
    "events_json_invalid": "workflow event JSON could not be parsed",
    "skipped_not_pass": "skipped workflow results are preserved as non-pass evidence",
}

PRIVATE_PATH_PATTERN = re.compile(
    r"(?i)(?:^|[/\\])kb[/\\]private[/\\]|(?:^|[/\\])private[/\\]"
)
ACCEPTED_PATH_PATTERN = re.compile(r"(?i)(?:^|[/\\])kb[/\\][^\"'\s,}]*accepted[/\\]")
PROVIDER_PAYLOAD_KEYS = frozenset(
    {
        "provider_payload",
        "provider_request",
        "provider_response",
        "raw_provider_payload",
        "raw_provider_request",
        "raw_provider_response",
        "raw_request",
        "raw_response",
    }
)
ENVIRONMENT_DUMP_KEYS = frozenset({"env", "environ", "environment", "env_dump"})
HUMAN_REVIEW_KEYS = frozenset(
    {
        "human_review",
        "human_review_created",
        "human_reviewed",
        "review_state",
    }
)
VERIFIER_GATE_KEYS = frozenset(
    {
        "gate_pass",
        "gate_result",
        "gate_result_mutated",
        "verifier_pass",
        "verifier_result",
        "verifier_result_mutated",
    }
)
SOURCE_METADATA_KEYS = frozenset(
    {
        "source_metadata",
        "source_metadata_created",
        "source_metadata_verified",
        "source_locator",
        "source_locators",
        "sources",
    }
)
HUMAN_REVIEW_TEXT_PATTERN = re.compile(
    r"(?i)(mark\s+human[_ -]?reviewed|review_state\s*[:=]\s*human_reviewed|"
    r"human_reviewed\s*[:=]\s*true|human review completed)"
)
VERIFIER_GATE_TEXT_PATTERN = re.compile(
    r"(?i)(verifier_pass\s*[:=]\s*true|gate_pass\s*[:=]\s*true|"
    r"verifier pass\s*[:=]\s*true|gate pass\s*[:=]\s*true)"
)
SOURCE_METADATA_TEXT_PATTERN = re.compile(
    r"(?i)(source metadata (?:created|verified|complete|confirmed)|"
    r"fabricated source|fake source locator)"
)
ACCEPTED_THEOREM_TEXT_PATTERN = re.compile(
    r"(?i)(?:^|[^a-z])(?:is\s+an\s+)?accepted\s+(?:theorem|refutation)\b|"
    r"\b(?:theorem|refutation)_status\s*[:=]\s*accepted"
)


def _json_text(payload: Any) -> str:
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json")
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


class WorkflowHandoffModel(BaseModel):
    """Strict deterministic base model for workflow handoff DTOs."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        return _json_text(self)


class WorkflowHandoffActionSummary(WorkflowHandoffModel):
    """Compact summary for one workflow action."""

    step_number: int
    action: str
    status: str
    warning_count: int = 0


class WorkflowHandoffCandidateClaim(WorkflowHandoffModel):
    """Review-only candidate claim summary."""

    candidate_id: str
    status: Literal["draft"] = "draft"
    title: str
    statement: str
    limitations: tuple[str, ...] = ()
    authority_notice: str = WORKFLOW_HANDOFF_AUTHORITY_NOTICE

    @field_validator("candidate_id")
    @classmethod
    def _candidate_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())


class WorkflowHandoffScannerFinding(WorkflowHandoffModel):
    """One deterministic workflow-handoff scanner finding."""

    code: str
    severity: Literal["warning", "blocker"]
    message: str
    source_path: str
    line: int | None = None
    field_path: str | None = None


class WorkflowHandoffScanResult(WorkflowHandoffModel):
    """One workflow-handoff scan report."""

    schema_version: Literal[1] = 1
    kind: Literal["workflow_handoff_scan"] = "workflow_handoff_scan"
    handoff_id: str
    workflow_id: str
    findings: tuple[WorkflowHandoffScannerFinding, ...] = ()
    report_path: str
    accepted_write_performed: Literal[False] = False
    authority_notice: str = WORKFLOW_HANDOFF_AUTHORITY_NOTICE

    @field_validator("handoff_id", "workflow_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def blocking_finding_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "blocker")

    @property
    def handoff_blocked(self) -> bool:
        return self.blocking_finding_count > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "handoff_id": self.handoff_id,
            "workflow_id": self.workflow_id,
            "finding_count": self.finding_count,
            "blocking_finding_count": self.blocking_finding_count,
            "handoff_blocked": self.handoff_blocked,
            "report_path": self.report_path,
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": self.authority_notice,
            "findings": [finding.to_dict() for finding in self.findings],
        }


class WorkflowHandoffScannerSummary(WorkflowHandoffModel):
    """Scanner status embedded in a workflow handoff bundle."""

    report_path: str
    finding_count: int
    blocking_finding_count: int
    handoff_blocked: bool
    findings: tuple[dict[str, Any], ...] = ()


class WorkflowHandoffBundle(WorkflowHandoffModel):
    """One compact review handoff bundle for a reviewable workflow."""

    schema_version: Literal[1] = 1
    kind: Literal["workflow_handoff_bundle"] = "workflow_handoff_bundle"
    handoff_id: str
    workflow_id: str
    issue_id: str
    issue_summary: str
    query_objective: str
    librarian_context_summary: str
    fsm_trace: tuple[str, ...] = ()
    actions_executed: tuple[WorkflowHandoffActionSummary, ...] = ()
    failures_and_avoided_directions: tuple[str, ...] = ()
    candidate_claims: tuple[WorkflowHandoffCandidateClaim, ...] = ()
    evidence_and_limitations: tuple[str, ...] = ()
    scanner: WorkflowHandoffScannerSummary
    human_review_checklist: tuple[str, ...] = WORKFLOW_HANDOFF_REVIEW_CHECKLIST
    skipped_results_are_pass: Literal[False] = False
    review_context_only: Literal[True] = True
    authority_notice: str = WORKFLOW_HANDOFF_AUTHORITY_NOTICE
    accepted_write_performed: Literal[False] = False
    human_review_created: Literal[False] = False
    source_metadata_created: Literal[False] = False
    promotion_performed: Literal[False] = False
    verifier_result_mutated: Literal[False] = False
    gate_result_mutated: Literal[False] = False

    @field_validator("handoff_id", "workflow_id", "issue_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("authority_notice")
    @classmethod
    def _authority_notice(cls, value: str) -> str:
        if value != WORKFLOW_HANDOFF_AUTHORITY_NOTICE:
            raise ValueError("authority_notice must preserve workflow handoff boundary")
        return value


class WorkflowHandoffExportResult(WorkflowHandoffModel):
    """One explicit review-context export result for a workflow handoff."""

    schema_version: Literal[1] = 1
    kind: Literal["workflow_handoff_export"] = "workflow_handoff_export"
    handoff_id: str
    workflow_id: str
    source_runtime_path: str
    target_path: str
    dry_run: bool
    written_paths: tuple[str, ...] = ()
    review_context_only: Literal[True] = True
    handoff: WorkflowHandoffBundle
    authority_notice: str = WORKFLOW_HANDOFF_AUTHORITY_NOTICE
    accepted_write_performed: Literal[False] = False
    human_review_created: Literal[False] = False
    source_metadata_created: Literal[False] = False
    promotion_performed: Literal[False] = False
    verifier_result_mutated: Literal[False] = False
    gate_result_mutated: Literal[False] = False

    @field_validator("handoff_id", "workflow_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("source_runtime_path", "target_path")
    @classmethod
    def _paths(cls, value: str) -> str:
        return _validate_repo_local_nonaccepted_path(value)

    @field_validator("written_paths", mode="before")
    @classmethod
    def _written_paths(cls, value: Any) -> tuple[str, ...]:
        return tuple(_validate_repo_local_nonaccepted_path(item) for item in value)


@dataclass(frozen=True)
class WorkflowHandoffWriteResult:
    """One loaded or written workflow handoff bundle."""

    handoff: WorkflowHandoffBundle
    relative_path: Path
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        payload = self.handoff.to_dict()
        payload["path"] = self.relative_path.as_posix()
        payload["accepted_write_performed"] = self.accepted_write_performed
        return payload


def workflow_handoff_id(workflow_id: str) -> str:
    """Return deterministic handoff ID for one workflow."""

    return validate_artifact_id(f"handoff.{validate_artifact_id(workflow_id.strip())}")


def workflow_id_from_handoff_id(handoff_id: str) -> str:
    """Return workflow ID encoded in one workflow handoff ID."""

    resolved = validate_artifact_id(handoff_id.strip())
    prefix = "handoff."
    if not resolved.startswith(prefix):
        raise WorkflowError(
            f"workflow handoff ID must start with {prefix}: {resolved}",
            code="WORKFLOW_HANDOFF_VALIDATION_FAILED",
            remediation=(
                "Use a handoff ID returned by "
                "`cosheaf workflow handoff build`."
            ),
        )
    return validate_artifact_id(resolved.removeprefix(prefix))


def workflow_handoff_path(handoff_id: str) -> Path:
    """Return runtime handoff.json path for one workflow handoff ID."""

    workflow_id = workflow_id_from_handoff_id(handoff_id)
    return workflow_root(workflow_id) / "handoff.json"


def workflow_handoff_scan_path(handoff_id: str) -> Path:
    """Return runtime scan report path for one workflow handoff ID."""

    workflow_id = workflow_id_from_handoff_id(handoff_id)
    return workflow_root(workflow_id) / "handoff-scan.json"


def workflow_handoff_export_path(handoff_id: str) -> Path:
    """Return explicit review-context export path for one workflow handoff."""

    resolved = validate_artifact_id(handoff_id.strip())
    return Path("reviews") / "workflow" / f"{resolved}.yaml"


def build_workflow_handoff(
    context: RepoContext,
    workflow_id: str,
) -> WorkflowHandoffWriteResult:
    """Build and persist one review-only workflow handoff bundle."""

    workflow = load_workflow(context, workflow_id)
    handoff_id = workflow_handoff_id(workflow.workflow_id)
    scan = scan_workflow_handoff(context, handoff_id, include_existing_handoff=False)
    if scan.handoff_blocked:
        raise WorkflowError(
            "workflow handoff blocked by scanner findings",
            code="WORKFLOW_HANDOFF_BLOCKED_BY_SCAN",
            remediation=(
                "Inspect the workflow handoff scan report, remove or redact "
                "blockers, then rebuild the handoff."
            ),
            details={
                "workflow_id": workflow.workflow_id,
                "report_path": scan.report_path,
            },
        )
    proposal = build_draft_proposal(context, workflow.workflow_id)
    handoff = WorkflowHandoffBundle(
        handoff_id=handoff_id,
        workflow_id=workflow.workflow_id,
        issue_id=workflow.issue_id,
        issue_summary=_issue_summary(workflow),
        query_objective=workflow.query or workflow.issue_id,
        librarian_context_summary=_librarian_context_summary(workflow),
        fsm_trace=_fsm_trace(workflow),
        actions_executed=_actions_executed(workflow),
        failures_and_avoided_directions=_failures_and_avoided_directions(workflow),
        candidate_claims=tuple(
            WorkflowHandoffCandidateClaim(
                candidate_id=claim.candidate_id,
                title=claim.title,
                statement=claim.statement,
                limitations=tuple(claim.limitations),
            )
            for claim in proposal.claim_candidates
        ),
        evidence_and_limitations=_evidence_and_limitations(workflow),
        scanner=_scanner_summary(scan),
    )
    return write_workflow_handoff(context, handoff)


def write_workflow_handoff(
    context: RepoContext,
    handoff: WorkflowHandoffBundle,
) -> WorkflowHandoffWriteResult:
    """Persist one runtime workflow handoff bundle."""

    relative_path = workflow_handoff_path(handoff.handoff_id)
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(handoff.to_json(), encoding="utf-8", newline="\n")
    return WorkflowHandoffWriteResult(handoff=handoff, relative_path=relative_path)


def load_workflow_handoff(
    context: RepoContext,
    handoff_id: str,
) -> WorkflowHandoffWriteResult:
    """Load one runtime workflow handoff bundle."""

    resolved = validate_artifact_id(handoff_id.strip())
    relative_path = workflow_handoff_path(resolved)
    target = context.resolve(relative_path)
    if not target.is_file():
        raise WorkflowError(
            f"workflow handoff not found: {resolved}",
            code="WORKFLOW_HANDOFF_NOT_FOUND",
            remediation="Build the handoff first or pass an existing handoff ID.",
            details={"path": relative_path.as_posix()},
        )
    try:
        raw = json.loads(target.read_text(encoding="utf-8-sig"))
        handoff = WorkflowHandoffBundle.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise WorkflowError(
            f"workflow handoff failed validation: {exc}",
            code="WORKFLOW_HANDOFF_VALIDATION_FAILED",
            remediation="Inspect the runtime handoff.json file and repair it.",
            details={"path": relative_path.as_posix()},
        ) from exc
    return WorkflowHandoffWriteResult(handoff=handoff, relative_path=relative_path)


def scan_workflow_handoff(
    context: RepoContext,
    handoff_id: str,
    *,
    include_existing_handoff: bool = True,
    write_report: bool = True,
) -> WorkflowHandoffScanResult:
    """Scan workflow runtime and handoff records for review-boundary blockers."""

    resolved_handoff_id = validate_artifact_id(handoff_id.strip())
    workflow_id = workflow_id_from_handoff_id(resolved_handoff_id)
    scanner = _WorkflowHandoffScanner(context=context, handoff_id=resolved_handoff_id)
    for relative_path in _scan_input_paths(
        workflow_id,
        handoff_id=resolved_handoff_id,
        include_existing_handoff=include_existing_handoff,
        context=context,
    ):
        target = context.resolve(relative_path)
        if not target.exists():
            continue
        text = target.read_text(encoding="utf-8-sig")
        if relative_path.suffix.lower() == ".jsonl":
            scanner.scan_events_jsonl(text, source_path=relative_path.as_posix())
        else:
            invalid_code = (
                "handoff_json_invalid"
                if relative_path.name == "handoff.json"
                else "workflow_json_invalid"
            )
            scanner.scan_json_file(
                text,
                source_path=relative_path.as_posix(),
                invalid_code=invalid_code,
            )
    result = WorkflowHandoffScanResult(
        handoff_id=resolved_handoff_id,
        workflow_id=workflow_id,
        findings=tuple(scanner.findings),
        report_path=workflow_handoff_scan_path(resolved_handoff_id).as_posix(),
    )
    if write_report:
        target = context.resolve(Path(result.report_path))
        _ensure_repo_local(context, target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(result.to_json(), encoding="utf-8", newline="\n")
    return result


def export_workflow_handoff(
    context: RepoContext,
    handoff_id: str,
    *,
    dry_run: bool = False,
    target_path: str | Path | None = None,
) -> WorkflowHandoffExportResult:
    """Export one workflow handoff as explicit review context."""

    scan = scan_workflow_handoff(context, handoff_id)
    if scan.handoff_blocked:
        raise WorkflowError(
            "workflow handoff export blocked by scanner findings",
            code="WORKFLOW_HANDOFF_BLOCKED_BY_SCAN",
            remediation=(
                "Repair the runtime handoff and rerun the scanner before export."
            ),
            details={"handoff_id": handoff_id, "scanner_report": scan.report_path},
        )
    loaded = load_workflow_handoff(context, handoff_id)
    handoff = loaded.handoff
    relative_target = (
        workflow_handoff_export_path(handoff.handoff_id)
        if target_path is None
        else _normalize_export_target(target_path)
    )
    _ensure_workflow_handoff_export_target(context, relative_target)
    result = WorkflowHandoffExportResult(
        handoff_id=handoff.handoff_id,
        workflow_id=handoff.workflow_id,
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


class _WorkflowHandoffScanner:
    def __init__(self, *, context: RepoContext, handoff_id: str) -> None:
        self.context = context
        self.handoff_id = handoff_id
        self.findings: list[WorkflowHandoffScannerFinding] = []
        self._seen: set[tuple[str, str, int | None, str | None]] = set()

    def scan_json_file(
        self,
        text: str,
        *,
        source_path: str,
        invalid_code: str,
    ) -> object | None:
        self.scan_text(text, source_path=source_path)
        try:
            parsed = cast(object, json.loads(text))
        except json.JSONDecodeError as exc:
            self._add(
                invalid_code,
                source_path=source_path,
                line=exc.lineno,
                severity="blocker",
            )
            return None
        self.scan_json(parsed, source_path=source_path)
        return parsed

    def scan_events_jsonl(self, text: str, *, source_path: str) -> None:
        self.scan_text(text, source_path=source_path)
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                parsed = cast(object, json.loads(line))
            except json.JSONDecodeError:
                self._add(
                    "events_json_invalid",
                    source_path=source_path,
                    line=line_number,
                    severity="blocker",
                )
                continue
            self.scan_json(parsed, source_path=source_path)

    def scan_text(self, text: str, *, source_path: str) -> None:
        for finding in scan_provider_log_text(text, path=source_path):
            self._add(
                finding.kind,
                source_path=source_path,
                line=finding.line,
                field_path=finding.key,
                severity="blocker",
            )
        if ACCEPTED_PATH_PATTERN.search(text):
            self._add(
                "accepted_write_attempt",
                source_path=source_path,
                severity="blocker",
            )
        if PRIVATE_PATH_PATTERN.search(text):
            self._add(
                "private_path_reference",
                source_path=source_path,
                severity="blocker",
            )

    def scan_json(self, value: object, *, source_path: str) -> None:
        for field_path, scalar in _walk_json(value):
            key = field_path[-1] if field_path else ""
            normalized_key = _normalize_key(key)
            path_text = ".".join(field_path)
            if normalized_key in PROVIDER_PAYLOAD_KEYS:
                self._add(
                    "provider_payload",
                    source_path=source_path,
                    field_path=path_text,
                    severity="blocker",
                )
            if normalized_key in ENVIRONMENT_DUMP_KEYS:
                self._add(
                    "environment_dump",
                    source_path=source_path,
                    field_path=path_text,
                    severity="blocker",
                )
            if normalized_key in HUMAN_REVIEW_KEYS and _truthy_authority(scalar):
                self._add(
                    "human_review_overclaim",
                    source_path=source_path,
                    field_path=path_text,
                    severity="blocker",
                )
            if normalized_key in VERIFIER_GATE_KEYS and _truthy_authority(scalar):
                self._add(
                    "verifier_gate_overclaim",
                    source_path=source_path,
                    field_path=path_text,
                    severity="blocker",
                )
            if normalized_key in SOURCE_METADATA_KEYS and _truthy_source_claim(scalar):
                self._add(
                    "source_metadata_fabrication",
                    source_path=source_path,
                    field_path=path_text,
                    severity="blocker",
                )
            if _is_accepted_path_scalar(scalar):
                self._add(
                    "accepted_write_attempt",
                    source_path=source_path,
                    field_path=path_text,
                    severity="blocker",
                )
            if _is_private_path_scalar(scalar):
                self._add(
                    "private_path_reference",
                    source_path=source_path,
                    field_path=path_text,
                    severity="blocker",
                )
            if isinstance(scalar, str):
                self._scan_string(
                    scalar,
                    source_path=source_path,
                    field_path=path_text,
                )
            if normalized_key == "status" and str(scalar).lower() == "skipped":
                self._add(
                    "skipped_not_pass",
                    source_path=source_path,
                    field_path=path_text,
                    severity="warning",
                )

    def _scan_string(
        self,
        text: str,
        *,
        source_path: str,
        field_path: str,
    ) -> None:
        if field_path.endswith("authority_notice"):
            return
        if HUMAN_REVIEW_TEXT_PATTERN.search(text):
            self._add(
                "human_review_overclaim",
                source_path=source_path,
                field_path=field_path,
                severity="blocker",
            )
        if VERIFIER_GATE_TEXT_PATTERN.search(text):
            self._add(
                "verifier_gate_overclaim",
                source_path=source_path,
                field_path=field_path,
                severity="blocker",
            )
        if SOURCE_METADATA_TEXT_PATTERN.search(text):
            self._add(
                "source_metadata_fabrication",
                source_path=source_path,
                field_path=field_path,
                severity="blocker",
            )
        if _accepted_theorem_claim(text):
            self._add(
                "accepted_theorem_or_refutation",
                source_path=source_path,
                field_path=field_path,
                severity="blocker",
            )

    def _add(
        self,
        code: str,
        *,
        source_path: str,
        severity: Literal["warning", "blocker"],
        line: int | None = None,
        field_path: str | None = None,
    ) -> None:
        marker = (code, source_path, line, field_path)
        if marker in self._seen:
            return
        self._seen.add(marker)
        self.findings.append(
            WorkflowHandoffScannerFinding(
                code=code,
                severity=severity,
                message=FINDING_MESSAGES[code],
                source_path=source_path,
                line=line,
                field_path=field_path,
            )
        )


def _scan_input_paths(
    workflow_id: str,
    *,
    handoff_id: str,
    include_existing_handoff: bool,
    context: RepoContext,
) -> tuple[Path, ...]:
    paths = [
        workflow_path(workflow_id),
        workflow_events_path(workflow_id),
        workflow_librarian_path(workflow_id),
        workflow_fsm_path(workflow_id),
        workflow_loop_path(workflow_id),
        workflow_readiness_path(workflow_id),
    ]
    proposal_path = workflow_root(workflow_id) / "proposal.json"
    if context.resolve(proposal_path).exists():
        paths.append(proposal_path)
    handoff_path = workflow_handoff_path(handoff_id)
    if include_existing_handoff and context.resolve(handoff_path).exists():
        paths.append(handoff_path)
    return tuple(paths)


def _issue_summary(workflow: WorkflowRecord) -> str:
    query = workflow.query.strip() if workflow.query else ""
    if query:
        return f"{workflow.issue_id}: {query}"
    return workflow.issue_id


def _librarian_context_summary(workflow: WorkflowRecord) -> str:
    if workflow.steps:
        action_ids = ", ".join(step.action for step in workflow.steps)
        return (
            f"Workflow context references {len(workflow.steps)} step(s): "
            f"{action_ids}."
        )
    return "No workflow steps have been recorded yet."


def _fsm_trace(workflow: WorkflowRecord) -> tuple[str, ...]:
    return tuple(
        f"{step.step_number}: {step.action} -> {step.status}" for step in workflow.steps
    )


def _actions_executed(
    workflow: WorkflowRecord,
) -> tuple[WorkflowHandoffActionSummary, ...]:
    return tuple(
        WorkflowHandoffActionSummary(
            step_number=step.step_number,
            action=step.action,
            status=step.status,
            warning_count=len(step.warnings),
        )
        for step in workflow.steps
    )


def _failures_and_avoided_directions(workflow: WorkflowRecord) -> tuple[str, ...]:
    failures = list(workflow.failure_summary.blocker_details)
    for step in workflow.steps:
        if step.status in {"blocked", "failed", "error"}:
            failures.append(f"Step {step.step_number} ({step.action}) {step.status}.")
        failures.extend(step.warnings)
    if failures:
        return tuple(failures)
    return ("No workflow failure or avoided-direction record is present.",)


def _evidence_and_limitations(workflow: WorkflowRecord) -> tuple[str, ...]:
    limitations = [
        f"Workflow status: {workflow.status.value}.",
        f"Workflow step count: {len(workflow.steps)}.",
        "Workflow handoff is review context only.",
        "No source metadata is created by this handoff.",
        (
            "No human review, verifier pass, gate pass, accepted status, "
            "or promotion is created."
        ),
    ]
    if workflow.readiness is not None:
        limitations.append(f"Workflow readiness: {workflow.readiness.value}.")
    if any(step.status == "skipped" for step in workflow.steps):
        limitations.append("Skipped workflow steps are not pass evidence.")
    if any(
        step.output_refs.get("scanner_status") == "skipped"
        or step.output_refs.get("action_status") == "skipped"
        for step in workflow.steps
    ):
        limitations.append("Skipped verifier/tool results are not pass evidence.")
    return tuple(limitations)


def _scanner_summary(scan: WorkflowHandoffScanResult) -> WorkflowHandoffScannerSummary:
    return WorkflowHandoffScannerSummary(
        report_path=scan.report_path,
        finding_count=scan.finding_count,
        blocking_finding_count=scan.blocking_finding_count,
        handoff_blocked=scan.handoff_blocked,
        findings=tuple(finding.to_dict() for finding in scan.findings),
    )


def _walk_json(
    value: object,
    path: tuple[str, ...] = (),
) -> Iterator[tuple[tuple[str, ...], object]]:
    yield path, value
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            yield from _walk_json(child, (*path, key))
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_json(child, (*path, str(index)))
        return


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(".", "_")


def _truthy_authority(value: object) -> bool:
    if value is True:
        return True
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    return normalized in {
        "true",
        "accepted",
        "approved",
        "human_reviewed",
        "pass",
        "passed",
        "promote",
        "promotion_performed",
        "verifier_pass",
    }


def _truthy_source_claim(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, list | tuple | dict):
        return len(value) > 0
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    if normalized in {"", "false", "none", "not created", "required"}:
        return False
    return normalized in {"true", "verified", "complete", "created"} or (
        "created" in normalized
        or "verified" in normalized
        or "complete" in normalized
    )


def _is_accepted_path_scalar(value: object) -> bool:
    return isinstance(value, str) and bool(ACCEPTED_PATH_PATTERN.search(value))


def _is_private_path_scalar(value: object) -> bool:
    return isinstance(value, str) and bool(PRIVATE_PATH_PATTERN.search(value))


def _accepted_theorem_claim(text: str) -> bool:
    if not ACCEPTED_THEOREM_TEXT_PATTERN.search(text):
        return False
    normalized = text.lower()
    return "not accepted theorem" not in normalized and (
        "not accepted refutation" not in normalized
    )


def _normalize_export_target(value: str | Path) -> Path:
    normalized = _validate_repo_local_nonaccepted_path(str(value))
    return Path(normalized)


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
        raise ValueError("workflow handoff records cannot reference accepted KB paths")
    return normalized


def _ensure_workflow_handoff_export_target(
    context: RepoContext,
    relative_target: Path,
) -> None:
    normalized = normalize_repo_path(relative_target)
    if normalized.startswith("kb/accepted/") or "/accepted/" in normalized:
        raise WorkflowError(
            "workflow handoff export target must not be an accepted KB path",
            code="ACCEPTED_WRITE_FORBIDDEN",
            remediation=(
                "Export workflow handoff review context under reviews/workflow/."
            ),
            details={"path": normalized},
        )
    if not normalized.startswith("reviews/workflow/"):
        raise WorkflowError(
            "workflow handoff export target must be under reviews/workflow/",
            code="INVALID_WORKFLOW_HANDOFF_EXPORT_PATH",
            remediation=(
                "Use the deterministic reviews/workflow/<handoff-id>.yaml path."
            ),
            details={"path": normalized},
        )
    if Path(normalized).suffix.lower() not in {".yaml", ".yml"}:
        raise WorkflowError(
            "workflow handoff export target must be YAML",
            code="INVALID_WORKFLOW_HANDOFF_EXPORT_PATH",
            remediation=(
                "Use the deterministic reviews/workflow/<handoff-id>.yaml path."
            ),
            details={"path": normalized},
        )
    _ensure_repo_local(context, context.resolve(relative_target))


def _ensure_repo_local(context: RepoContext, target: Path) -> None:
    root = context.repo_root.resolve()
    resolved = target.resolve()
    if resolved != root and root not in resolved.parents:
        raise WorkflowError(
            "workflow handoff target must stay repository-local",
            code="INVALID_WORKFLOW_HANDOFF_PATH",
            remediation="Use the controlled .cosheaf/workflows path.",
        )
    normalized = normalize_repo_path(resolved.relative_to(root))
    if normalized.startswith("kb/accepted/") or "/accepted/" in normalized:
        raise WorkflowError(
            "workflow handoff target must not be an accepted KB path",
            code="ACCEPTED_WRITE_FORBIDDEN",
            remediation="Use runtime storage or review-context export paths only.",
        )


__all__ = [
    "WORKFLOW_HANDOFF_AUTHORITY_NOTICE",
    "WORKFLOW_HANDOFF_KIND",
    "WORKFLOW_HANDOFF_REVIEW_CHECKLIST",
    "WORKFLOW_HANDOFF_SCAN_KIND",
    "WorkflowHandoffActionSummary",
    "WorkflowHandoffBundle",
    "WorkflowHandoffCandidateClaim",
    "WorkflowHandoffExportResult",
    "WorkflowHandoffScanResult",
    "WorkflowHandoffScannerFinding",
    "WorkflowHandoffScannerSummary",
    "WorkflowHandoffWriteResult",
    "build_workflow_handoff",
    "export_workflow_handoff",
    "load_workflow_handoff",
    "scan_workflow_handoff",
    "workflow_handoff_export_path",
    "workflow_handoff_id",
    "workflow_handoff_path",
    "workflow_handoff_scan_path",
    "workflow_id_from_handoff_id",
    "write_workflow_handoff",
]
