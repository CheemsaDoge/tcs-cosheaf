"""Workflow cross-check reports and proof-obligation gap taxonomy."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from cosheaf.checkers.models import CheckerRunRecord, CheckerStatus
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.engine import (
    WorkflowError,
    WorkflowRecord,
    WorkflowStep,
    load_workflow,
    workflow_root,
)

CROSSCHECK_AUTHORITY_NOTICE = (
    "Workflow cross-check reports are review context only; checker pass and "
    "workflow success are not proof, source metadata, human review, gate pass, "
    "verifier pass, accepted status, accepted theorem/refutation, or promotion "
    "authority; skipped and inconclusive results are not passes."
)

GAP_AUTHORITY_NOTICE = (
    "Workflow gap reports are review guidance only; a gap is not itself a "
    "defect, proof, source metadata, human review, accepted status, or "
    "promotion authority."
)

_HUMAN_REVIEW_PATTERN = re.compile(
    r"(?i)(creates?\s+human review|created\s+human review|"
    r"human review completed|mark(?:ed)?\s+human[_ -]?reviewed|"
    r"human_reviewed\s*[:=]\s*true|review_state\s*[:=]\s*human_reviewed)"
)
_ACCEPTED_THEOREM_PATTERN = re.compile(
    r"(?i)(?:^|[^a-z])accepted\s+(?:theorem|refutation)\b|"
    r"\b(?:theorem|refutation)_status\s*[:=]\s*accepted"
)
_VERIFIER_GATE_PATTERN = re.compile(
    r"(?i)(verifier_pass\s*[:=]\s*true|gate_pass\s*[:=]\s*true|"
    r"verifier pass completed|gate pass completed|"
    r"claims?\s+(?:a\s+)?(?:verifier|gate)\s+pass)"
)
_SOURCE_METADATA_PATTERN = re.compile(
    r"(?i)(source metadata (?:created|verified|complete|confirmed)|"
    r"fabricated source|fake source locator)"
)


class CrossCheckClassification(StrEnum):
    """Review-context classification for workflow evidence rows."""

    UNCHECKED = "unchecked"
    CHECKED_PASS = "checked-pass"
    CHECKED_FAIL = "checked-fail"
    INCONCLUSIVE = "inconclusive"
    REVIEW_NEEDED = "review-needed"


class GapKind(StrEnum):
    """First-class workflow gap taxonomy."""

    PROOF = "proof_gap"
    SOURCE = "source_gap"
    FORMALIZATION = "formalization_gap"
    COUNTEREXAMPLE = "counterexample_gap"
    SEMANTIC_ALIGNMENT = "semantic_alignment_gap"
    DEPENDENCY = "dependency_gap"
    REVIEW = "review_gap"
    REPRODUCIBILITY = "reproducibility_gap"


class CrossCheckModel(BaseModel):
    """Strict deterministic base model for cross-check DTOs."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        return _json_text(self)


class CrossCheckItem(CrossCheckModel):
    """One row in the workflow cross-check matrix."""

    item_id: str
    item_kind: str
    subject: str
    classification: CrossCheckClassification
    checker_id: str | None = None
    checker_status: str | None = None
    command_surface: str | None = None
    timestamp: str | None = None
    paths: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    accepted_status_created: Literal[False] = False
    authority_notice: str = CROSSCHECK_AUTHORITY_NOTICE


class CrossCheckMatrix(CrossCheckModel):
    """Deterministic summary matrix for workflow evidence."""

    status_counts: dict[str, int]
    checker_status_counts: dict[str, int] = Field(default_factory=dict)
    items: tuple[CrossCheckItem, ...] = ()
    skipped_is_pass: Literal[False] = False
    checked_pass_is_accepted: Literal[False] = False


class UnverifiedClaim(CrossCheckModel):
    """Candidate claim that still needs human review and proof/source work."""

    claim_id: str
    statement: str
    source_path: str
    reason: str = "claim has not been accepted or human-reviewed"

    @field_validator("claim_id")
    @classmethod
    def _claim_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())


class ProofObligation(CrossCheckModel):
    """One proof obligation remaining for a workflow."""

    obligation_id: str
    description: str
    related_item_id: str
    status: Literal["open"] = "open"


class FormalizationGap(CrossCheckModel):
    """Missing or unchecked formalization reference."""

    gap_id: str
    description: str
    related_item_id: str
    checker_id: str | None = None
    status: Literal["open"] = "open"


class SourceGap(CrossCheckModel):
    """Missing or failed source-metadata evidence."""

    gap_id: str
    description: str
    related_item_id: str
    checker_id: str | None = None
    status: Literal["open"] = "open"


class ReviewRequiredItem(CrossCheckModel):
    """Item that requires human review before accepted knowledge use."""

    item_id: str
    description: str
    related_item_id: str
    human_review_created: Literal[False] = False


class WorkflowGap(CrossCheckModel):
    """Generic exported workflow gap."""

    gap_id: str
    kind: GapKind
    description: str
    related_item_id: str
    guidance: str
    gaps_are_defects: Literal[False] = False
    authority_notice: str = GAP_AUTHORITY_NOTICE


class CrossCheckReport(CrossCheckModel):
    """Workflow-level cross-check evidence report."""

    schema_version: Literal[1] = 1
    kind: Literal["workflow_crosscheck_report"] = "workflow_crosscheck_report"
    workflow_id: str
    issue_id: str
    generated_at: datetime
    matrix: CrossCheckMatrix
    unverified_claims: tuple[UnverifiedClaim, ...] = ()
    proof_obligations: tuple[ProofObligation, ...] = ()
    formalization_gaps: tuple[FormalizationGap, ...] = ()
    source_gaps: tuple[SourceGap, ...] = ()
    review_required: tuple[ReviewRequiredItem, ...] = ()
    runtime_json_path: str
    runtime_markdown_path: str
    checked_pass_is_accepted: Literal[False] = False
    human_review_created: Literal[False] = False
    source_metadata_created: Literal[False] = False
    accepted_status_created: Literal[False] = False
    promotion_performed: Literal[False] = False
    authority_notice: str = CROSSCHECK_AUTHORITY_NOTICE

    @field_validator("workflow_id", "issue_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())


class WorkflowEvidenceReport(CrossCheckModel):
    """Compact evidence-report wrapper around cross-check output."""

    schema_version: Literal[1] = 1
    kind: Literal["workflow_evidence_report"] = "workflow_evidence_report"
    workflow_id: str
    crosscheck_report: CrossCheckReport
    status_counts: dict[str, int]
    gap_counts: dict[str, int]
    checked_pass_is_accepted: Literal[False] = False
    human_review_created: Literal[False] = False
    authority_notice: str = CROSSCHECK_AUTHORITY_NOTICE


class CrossCheckExportResult(CrossCheckModel):
    """One explicit cross-check export result."""

    schema_version: Literal[1] = 1
    kind: Literal["workflow_crosscheck_export"] = "workflow_crosscheck_export"
    workflow_id: str
    target_path: str
    written: bool
    report: CrossCheckReport
    authority_notice: str = CROSSCHECK_AUTHORITY_NOTICE
    accepted_status_created: Literal[False] = False
    human_review_created: Literal[False] = False


class WorkflowGapReport(CrossCheckModel):
    """Workflow gap report generated from cross-check evidence."""

    schema_version: Literal[1] = 1
    kind: Literal["workflow_gap_report"] = "workflow_gap_report"
    workflow_id: str
    issue_id: str
    gaps: tuple[WorkflowGap, ...]
    gap_counts: dict[str, int]
    runtime_path: str
    gaps_are_defects: Literal[False] = False
    authority_notice: str = GAP_AUTHORITY_NOTICE


class GapExportResult(CrossCheckModel):
    """One explicit gap export result."""

    schema_version: Literal[1] = 1
    kind: Literal["workflow_gap_export"] = "workflow_gap_export"
    workflow_id: str
    target_path: str
    written: bool
    report: WorkflowGapReport
    authority_notice: str = GAP_AUTHORITY_NOTICE


def workflow_crosscheck_path(workflow_id: str) -> Path:
    """Return runtime crosscheck.json path."""

    return workflow_root(workflow_id) / "crosscheck.json"


def workflow_crosscheck_markdown_path(workflow_id: str) -> Path:
    """Return runtime crosscheck.md path."""

    return workflow_root(workflow_id) / "crosscheck.md"


def workflow_gap_path(workflow_id: str) -> Path:
    """Return runtime gaps.json path."""

    return workflow_root(workflow_id) / "gaps.json"


def build_crosscheck_report(
    context: RepoContext,
    workflow_id: str,
    *,
    write: bool = True,
) -> CrossCheckReport:
    """Build a review-only cross-check report for one workflow."""

    workflow = load_workflow(context, workflow_id)
    checker_runs = _load_relevant_checker_runs(context, workflow)
    items = _workflow_step_items(workflow) + _checker_items(checker_runs)
    unverified_claims = _unverified_claims(context, workflow)
    items += tuple(
        CrossCheckItem(
            item_id=f"claim.{index}",
            item_kind="unverified_claim",
            subject=claim.statement,
            classification=CrossCheckClassification.UNCHECKED,
            paths=(claim.source_path,),
            limitations=(
                "Candidate claim is not source-reviewed, human-reviewed, or accepted.",
            ),
        )
        for index, claim in enumerate(unverified_claims, start=1)
    )
    matrix = _matrix(items, checker_runs)
    proof_obligations = _proof_obligations(items, unverified_claims)
    source_gaps = _source_gaps(checker_runs, unverified_claims)
    formalization_gaps = _formalization_gaps(checker_runs, unverified_claims)
    review_required = _review_required(unverified_claims, items)
    report = CrossCheckReport(
        workflow_id=workflow.workflow_id,
        issue_id=workflow.issue_id,
        generated_at=datetime.now(UTC).replace(microsecond=0),
        matrix=matrix,
        unverified_claims=unverified_claims,
        proof_obligations=proof_obligations,
        formalization_gaps=formalization_gaps,
        source_gaps=source_gaps,
        review_required=review_required,
        runtime_json_path=workflow_crosscheck_path(workflow.workflow_id).as_posix(),
        runtime_markdown_path=workflow_crosscheck_markdown_path(
            workflow.workflow_id
        ).as_posix(),
    )
    findings = scan_crosscheck_report_text(report.to_json())
    if findings:
        raise WorkflowError(
            "workflow cross-check report blocked by authority scanner",
            code="WORKFLOW_CROSSCHECK_BLOCKED_BY_SCAN",
            remediation=(
                "Remove accepted-proof, human-review, verifier/gate, or source "
                "overclaims."
            ),
            details={"finding_count": str(len(findings))},
        )
    if write:
        _write_text(
            context, workflow_crosscheck_path(workflow.workflow_id), report.to_json()
        )
        _write_text(
            context,
            workflow_crosscheck_markdown_path(workflow.workflow_id),
            render_crosscheck_markdown(report),
        )
    return report


def build_workflow_evidence_report(
    context: RepoContext,
    workflow_id: str,
) -> WorkflowEvidenceReport:
    """Build a compact evidence report from cross-check and gap records."""

    crosscheck = build_crosscheck_report(context, workflow_id)
    gaps = build_gap_report(context, workflow_id, crosscheck_report=crosscheck)
    return WorkflowEvidenceReport(
        workflow_id=crosscheck.workflow_id,
        crosscheck_report=crosscheck,
        status_counts=crosscheck.matrix.status_counts,
        gap_counts=gaps.gap_counts,
    )


def export_crosscheck_report(
    context: RepoContext,
    workflow_id: str,
    target_path: str | Path,
) -> CrossCheckExportResult:
    """Export one cross-check report under reviews/workflow."""

    report = build_crosscheck_report(context, workflow_id)
    target = _normalize_export_target(target_path, suffixes={".json", ".md"})
    _ensure_review_target(target)
    text = (
        report.to_json()
        if target.suffix.lower() == ".json"
        else render_crosscheck_markdown(report)
    )
    findings = scan_crosscheck_report_text(text)
    if findings:
        raise WorkflowError(
            "workflow cross-check export blocked by authority scanner",
            code="WORKFLOW_CROSSCHECK_BLOCKED_BY_SCAN",
            remediation="Export only review-context cross-check reports.",
            details={"finding_count": str(len(findings))},
        )
    _write_text(context, target, text)
    return CrossCheckExportResult(
        workflow_id=report.workflow_id,
        target_path=target.as_posix(),
        written=True,
        report=report,
    )


def build_gap_report(
    context: RepoContext,
    workflow_id: str,
    *,
    crosscheck_report: CrossCheckReport | None = None,
    write: bool = True,
) -> WorkflowGapReport:
    """Build a review-guidance gap report for one workflow."""

    report = crosscheck_report or build_crosscheck_report(context, workflow_id)
    gaps = _gaps_from_crosscheck(report)
    gap_counts: dict[str, int] = {}
    for gap in gaps:
        gap_counts[gap.kind.value] = gap_counts.get(gap.kind.value, 0) + 1
    gap_report = WorkflowGapReport(
        workflow_id=report.workflow_id,
        issue_id=report.issue_id,
        gaps=gaps,
        gap_counts=dict(sorted(gap_counts.items())),
        runtime_path=workflow_gap_path(report.workflow_id).as_posix(),
    )
    if write:
        _write_text(
            context, workflow_gap_path(report.workflow_id), gap_report.to_json()
        )
    return gap_report


def export_gap_report(
    context: RepoContext,
    workflow_id: str,
    target_path: str | Path,
) -> GapExportResult:
    """Export one workflow gap report under reviews/workflow."""

    report = build_gap_report(context, workflow_id)
    target = _normalize_export_target(target_path, suffixes={".json"})
    _ensure_review_target(target)
    _write_text(context, target, report.to_json())
    return GapExportResult(
        workflow_id=report.workflow_id,
        target_path=target.as_posix(),
        written=True,
        report=report,
    )


def render_crosscheck_markdown(report: CrossCheckReport) -> str:
    """Render a deterministic human-readable cross-check report."""

    lines = [
        f"# Workflow Cross-Check: {report.workflow_id}",
        "",
        "This report is review context only; checked-pass is not accepted, proof, "
        "source metadata, human review, verifier pass, gate pass, or promotion.",
        "",
        "## Matrix",
    ]
    for key, value in sorted(report.matrix.status_counts.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Items"])
    for item in report.matrix.items:
        checker = f" [{item.checker_id}]" if item.checker_id else ""
        lines.append(
            f"- {item.item_id}{checker}: {item.classification.value} - {item.subject}"
        )
        for limitation in item.limitations:
            lines.append(f"  - limitation: {limitation}")
    lines.extend(["", "## Obligations"])
    for obligation in report.proof_obligations:
        lines.append(f"- {obligation.obligation_id}: {obligation.description}")
    for source_gap in report.source_gaps:
        lines.append(f"- {source_gap.gap_id}: {source_gap.description}")
    for formalization_gap in report.formalization_gaps:
        lines.append(
            f"- {formalization_gap.gap_id}: {formalization_gap.description}"
        )
    for review_item in report.review_required:
        lines.append(f"- {review_item.item_id}: {review_item.description}")
    lines.extend(["", f"Authority: {report.authority_notice}", ""])
    return "\n".join(lines)


def scan_crosscheck_report_text(text: str) -> tuple[dict[str, str], ...]:
    """Return authority-overclaim findings for cross-check report text."""

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        scan_text = _plain_authority_scan_text(text)
    else:
        scan_text = "\n".join(_authority_scan_strings(parsed))
    findings: list[dict[str, str]] = []
    _append_finding(
        findings,
        "human_review_overclaim",
        "cross-check report claims or creates human review",
        _HUMAN_REVIEW_PATTERN.search(scan_text) is not None,
    )
    _append_finding(
        findings,
        "accepted_theorem_or_refutation",
        "cross-check report claims accepted theorem/refutation authority",
        _ACCEPTED_THEOREM_PATTERN.search(scan_text) is not None,
    )
    _append_finding(
        findings,
        "verifier_gate_overclaim",
        "cross-check report claims verifier or gate authority",
        _VERIFIER_GATE_PATTERN.search(scan_text) is not None,
    )
    _append_finding(
        findings,
        "source_metadata_fabrication",
        "cross-check report claims source metadata authority",
        _SOURCE_METADATA_PATTERN.search(scan_text) is not None,
    )
    return tuple(findings)


def _workflow_step_items(workflow: WorkflowRecord) -> tuple[CrossCheckItem, ...]:
    return tuple(_workflow_step_item(step) for step in workflow.steps)


def _workflow_step_item(step: WorkflowStep) -> CrossCheckItem:
    status = step.status.lower()
    classification = CrossCheckClassification.INCONCLUSIVE
    if status == "planned":
        classification = CrossCheckClassification.UNCHECKED
    elif status in {"success", "pass", "passed"}:
        classification = CrossCheckClassification.CHECKED_PASS
    elif status in {"failed", "fail", "error", "blocked"}:
        classification = CrossCheckClassification.CHECKED_FAIL
    elif status == "skipped":
        classification = CrossCheckClassification.INCONCLUSIVE
    paths = tuple(
        sorted(
            str(value)
            for value in [*step.input_refs.values(), *step.output_refs.values()]
            if _looks_like_path(str(value))
        )
    )
    limitations = ["Workflow step status is not proof or accepted status."]
    if classification is CrossCheckClassification.INCONCLUSIVE:
        limitations.append(
            "Skipped or inconclusive workflow output is not pass evidence."
        )
    return CrossCheckItem(
        item_id=f"workflow.step.{step.step_number}",
        item_kind="workflow_step",
        subject=f"{step.action} -> {step.status}",
        classification=classification,
        command_surface=step.action,
        paths=paths,
        limitations=tuple(limitations),
    )


def _checker_items(
    checker_runs: tuple[CheckerRunRecord, ...],
) -> tuple[CrossCheckItem, ...]:
    return tuple(_checker_item(record) for record in checker_runs)


def _checker_item(record: CheckerRunRecord) -> CrossCheckItem:
    status = record.result.status
    classification = CrossCheckClassification.INCONCLUSIVE
    if status is CheckerStatus.PASS:
        classification = CrossCheckClassification.CHECKED_PASS
    elif status in {
        CheckerStatus.FAIL,
        CheckerStatus.ERROR,
        CheckerStatus.BLOCKED_BY_POLICY,
    }:
        classification = CrossCheckClassification.CHECKED_FAIL
    elif status in {
        CheckerStatus.SKIPPED,
        CheckerStatus.INCONCLUSIVE,
        CheckerStatus.UNSUPPORTED,
    }:
        classification = CrossCheckClassification.INCONCLUSIVE
    command_surface = (
        " ".join(record.result.command)
        if record.result.command is not None
        else record.checker.checker_id
    )
    paths = tuple(
        sorted(
            set(record.result.input_paths)
            | set(record.result.output_paths)
            | set(record.result.diagnostic_paths)
            | {record.result_path, record.stdout_path, record.stderr_path}
        )
    )
    limitations = tuple(
        record.result.limitations or ("Checker result is review context only.",)
    )
    return CrossCheckItem(
        item_id=f"checker.{record.run_id}",
        item_kind="checker_run",
        subject=record.result.message,
        classification=classification,
        checker_id=record.checker.checker_id,
        checker_status=record.result.status.value,
        command_surface=command_surface,
        timestamp=record.created_at.isoformat(),
        paths=paths,
        limitations=limitations,
    )


def _matrix(
    items: tuple[CrossCheckItem, ...],
    checker_runs: tuple[CheckerRunRecord, ...],
) -> CrossCheckMatrix:
    status_counts: dict[str, int] = {}
    checker_status_counts: dict[str, int] = {}
    for item in items:
        key = item.classification.value
        status_counts[key] = status_counts.get(key, 0) + 1
    for record in checker_runs:
        key = record.result.status.value
        checker_status_counts[key] = checker_status_counts.get(key, 0) + 1
    for key in CrossCheckClassification:
        status_counts.setdefault(key.value, 0)
    return CrossCheckMatrix(
        status_counts=dict(sorted(status_counts.items())),
        checker_status_counts=dict(sorted(checker_status_counts.items())),
        items=items,
    )


def _unverified_claims(
    context: RepoContext,
    workflow: WorkflowRecord,
) -> tuple[UnverifiedClaim, ...]:
    proposal_path = workflow_root(workflow.workflow_id) / "proposal.json"
    target = context.resolve(proposal_path)
    claims: list[UnverifiedClaim] = []
    if target.is_file():
        try:
            raw = json.loads(target.read_text(encoding="utf-8-sig"))
            for index, item in enumerate(
                raw.get("proposal", {}).get("claim_candidates", []), start=1
            ):
                statement = str(
                    item.get("statement") or item.get("title") or workflow.query
                )
                claims.append(
                    UnverifiedClaim(
                        claim_id=f"claim.{workflow.issue_id}.candidate.{index}",
                        statement=statement,
                        source_path=proposal_path.as_posix(),
                    )
                )
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            pass
    if claims:
        return tuple(claims)
    statement = workflow.query or f"Candidate claim for {workflow.issue_id}"
    return (
        UnverifiedClaim(
            claim_id=f"claim.{workflow.issue_id}.candidate",
            statement=statement,
            source_path=workflow_root(workflow.workflow_id).as_posix(),
        ),
    )


def _proof_obligations(
    items: tuple[CrossCheckItem, ...],
    claims: tuple[UnverifiedClaim, ...],
) -> tuple[ProofObligation, ...]:
    obligations: list[ProofObligation] = []
    for index, claim in enumerate(claims, start=1):
        obligations.append(
            ProofObligation(
                obligation_id=f"proof.obligation.{index}",
                description=(
                    f"Provide source-reviewed proof or refutation for {claim.claim_id}."
                ),
                related_item_id=claim.claim_id,
            )
        )
    for item in items:
        if item.classification in {
            CrossCheckClassification.UNCHECKED,
            CrossCheckClassification.CHECKED_FAIL,
            CrossCheckClassification.INCONCLUSIVE,
            CrossCheckClassification.REVIEW_NEEDED,
        }:
            obligations.append(
                ProofObligation(
                    obligation_id=f"proof.obligation.{len(obligations) + 1}",
                    description=(
                        f"Resolve {item.classification.value} evidence item "
                        f"{item.item_id}."
                    ),
                    related_item_id=item.item_id,
                )
            )
    return tuple(obligations)


def _source_gaps(
    checker_runs: tuple[CheckerRunRecord, ...],
    claims: tuple[UnverifiedClaim, ...],
) -> tuple[SourceGap, ...]:
    source_runs = [
        record
        for record in checker_runs
        if record.checker.checker_id == "source_metadata_check"
    ]
    has_source_pass = any(
        record.result.status is CheckerStatus.PASS for record in source_runs
    )
    if has_source_pass:
        return ()
    reason = "No passing source_metadata_check exists for this workflow."
    if source_runs:
        reason = "Source metadata checker did not pass for this workflow."
    return tuple(
        SourceGap(
            gap_id=f"source.gap.{index}",
            description=(
                f"{reason} Candidate {claim.claim_id} still needs durable "
                "source metadata."
            ),
            related_item_id=claim.claim_id,
            checker_id="source_metadata_check",
        )
        for index, claim in enumerate(claims, start=1)
    )


def _formalization_gaps(
    checker_runs: tuple[CheckerRunRecord, ...],
    claims: tuple[UnverifiedClaim, ...],
) -> tuple[FormalizationGap, ...]:
    formal_runs = [
        record
        for record in checker_runs
        if record.checker.checker_id
        in {"lean_optional_check", "sat_optional_check", "smt_optional_check"}
    ]
    has_formal_pass = any(
        record.result.status is CheckerStatus.PASS for record in formal_runs
    )
    if has_formal_pass:
        return ()
    reason = "No passing optional formal checker exists for this workflow."
    if formal_runs:
        reason = (
            "Optional formal checker output is skipped, failed, unsupported, or "
            "inconclusive."
        )
    return tuple(
        FormalizationGap(
            gap_id=f"formalization.gap.{index}",
            description=f"{reason} Candidate {claim.claim_id} is not formally checked.",
            related_item_id=claim.claim_id,
            checker_id="lean_optional_check",
        )
        for index, claim in enumerate(claims, start=1)
    )


def _review_required(
    claims: tuple[UnverifiedClaim, ...],
    items: tuple[CrossCheckItem, ...],
) -> tuple[ReviewRequiredItem, ...]:
    review_items = [
        ReviewRequiredItem(
            item_id=f"review.required.{index}",
            description=(
                f"Human review is required before using {claim.claim_id} as "
                "accepted knowledge."
            ),
            related_item_id=claim.claim_id,
        )
        for index, claim in enumerate(claims, start=1)
    ]
    for item in items:
        if item.classification is CrossCheckClassification.CHECKED_PASS:
            review_items.append(
                ReviewRequiredItem(
                    item_id=f"review.required.{len(review_items) + 1}",
                    description=(
                        f"Checked item {item.item_id} still requires human "
                        "review for acceptance."
                    ),
                    related_item_id=item.item_id,
                )
            )
    return tuple(review_items)


def _gaps_from_crosscheck(report: CrossCheckReport) -> tuple[WorkflowGap, ...]:
    gaps: list[WorkflowGap] = []
    for obligation in report.proof_obligations:
        gaps.append(
            WorkflowGap(
                gap_id=f"gap.{len(gaps) + 1}",
                kind=GapKind.PROOF,
                description=obligation.description,
                related_item_id=obligation.related_item_id,
                guidance="A reviewer must supply or reject the proof obligation.",
            )
        )
    for source_gap in report.source_gaps:
        gaps.append(
            WorkflowGap(
                gap_id=f"gap.{len(gaps) + 1}",
                kind=GapKind.SOURCE,
                description=source_gap.description,
                related_item_id=source_gap.related_item_id,
                guidance=(
                    "Add durable source metadata through the normal artifact path."
                ),
            )
        )
    for formal_gap in report.formalization_gaps:
        gaps.append(
            WorkflowGap(
                gap_id=f"gap.{len(gaps) + 1}",
                kind=GapKind.FORMALIZATION,
                description=formal_gap.description,
                related_item_id=formal_gap.related_item_id,
                guidance=(
                    "Treat formal links as metadata unless a checker actually "
                    "verifies them."
                ),
            )
        )
        gaps.append(
            WorkflowGap(
                gap_id=f"gap.{len(gaps) + 1}",
                kind=GapKind.SEMANTIC_ALIGNMENT,
                description=(
                    "Human semantic-alignment review remains open for "
                    f"{formal_gap.related_item_id}."
                ),
                related_item_id=formal_gap.related_item_id,
                guidance=(
                    "A successful tool check would still not prove informal/formal "
                    "alignment."
                ),
            )
        )
    for item in report.review_required:
        gaps.append(
            WorkflowGap(
                gap_id=f"gap.{len(gaps) + 1}",
                kind=GapKind.REVIEW,
                description=item.description,
                related_item_id=item.related_item_id,
                guidance=(
                    "Record human review separately; this report cannot create it."
                ),
            )
        )
    if not report.matrix.checker_status_counts:
        gaps.append(
            WorkflowGap(
                gap_id=f"gap.{len(gaps) + 1}",
                kind=GapKind.REPRODUCIBILITY,
                description="No checker-run sidecars are attached to this workflow.",
                related_item_id=report.workflow_id,
                guidance="Run relevant checkers and regenerate the cross-check report.",
            )
        )
    return tuple(gaps)


def _load_relevant_checker_runs(
    context: RepoContext,
    workflow: WorkflowRecord,
) -> tuple[CheckerRunRecord, ...]:
    root = context.resolve(Path(".cosheaf") / "checker-runs")
    if not root.is_dir():
        return ()
    records: list[CheckerRunRecord] = []
    for path in sorted(root.glob("*/result.json")):
        try:
            record = CheckerRunRecord.model_validate_json(
                path.read_text(encoding="utf-8-sig")
            )
        except (OSError, ValueError):
            continue
        if _checker_mentions_workflow(record, workflow):
            records.append(record)
    return tuple(records)


def _checker_mentions_workflow(
    record: CheckerRunRecord,
    workflow: WorkflowRecord,
) -> bool:
    text = json.dumps(record.to_dict(), ensure_ascii=True, sort_keys=True)
    needles = (
        workflow.workflow_id,
        workflow.issue_id,
        workflow_root(workflow.workflow_id).as_posix(),
    )
    return any(needle in text for needle in needles)


def _normalize_export_target(value: str | Path, *, suffixes: set[str]) -> Path:
    raw = str(value).strip()
    normalized = normalize_repo_path(raw)
    is_absolute = Path(raw).is_absolute() or PureWindowsPath(raw).is_absolute()
    parts = PurePosixPath(normalized).parts
    if (
        not normalized
        or is_absolute
        or raw.startswith("/")
        or normalized in {".", ".."}
        or normalized.startswith("../")
        or ".." in parts
    ):
        raise WorkflowError(
            "cross-check export target must be repository-local",
            code="INVALID_CROSSCHECK_EXPORT_PATH",
            remediation="Use a path under reviews/workflow/.",
            details={"path": raw},
        )
    target = Path(normalized)
    if target.suffix.lower() not in suffixes:
        raise WorkflowError(
            "cross-check export target has an unsupported suffix",
            code="INVALID_CROSSCHECK_EXPORT_PATH",
            remediation=f"Use one of: {', '.join(sorted(suffixes))}.",
            details={"path": normalized},
        )
    return target


def _ensure_review_target(target: Path) -> None:
    normalized = target.as_posix()
    if not normalized.startswith("reviews/workflow/"):
        raise WorkflowError(
            "cross-check exports must be under reviews/workflow/",
            code="INVALID_CROSSCHECK_EXPORT_PATH",
            remediation="Use reviews/workflow/<name>.json or .md.",
            details={"path": normalized},
        )
    if normalized.startswith("kb/accepted/") or "/accepted/" in normalized:
        raise WorkflowError(
            "cross-check exports cannot target accepted KB paths",
            code="ACCEPTED_WRITE_FORBIDDEN",
            remediation="Use reviews/workflow/ for review context.",
            details={"path": normalized},
        )


def _write_text(context: RepoContext, relative_path: Path, text: str) -> None:
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def _ensure_repo_local(context: RepoContext, target: Path) -> None:
    root = context.repo_root.resolve()
    resolved = target.resolve()
    if resolved != root and root not in resolved.parents:
        raise WorkflowError(
            "cross-check path must stay repository-local",
            code="INVALID_CROSSCHECK_PATH",
            remediation="Use runtime storage or reviews/workflow export paths.",
        )


def _json_text(payload: Any) -> str:
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json")
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def _looks_like_path(value: str) -> bool:
    return (
        "/" in value
        or "\\" in value
        or value.endswith(".json")
        or value.endswith(".yaml")
    )


def _append_finding(
    findings: list[dict[str, str]],
    code: str,
    message: str,
    condition: bool,
) -> None:
    if condition:
        findings.append({"code": code, "severity": "blocker", "message": message})


def _authority_scan_strings(value: object) -> tuple[str, ...]:
    strings: list[str] = []
    if isinstance(value, dict):
        for raw_key, child in value.items():
            key = str(raw_key).lower()
            if key == "authority_notice":
                continue
            if key in {
                "human_review_created",
                "source_metadata_created",
                "accepted_status_created",
                "promotion_performed",
                "checked_pass_is_accepted",
            }:
                if child is True:
                    strings.append(f"{key}=true")
                continue
            strings.extend(_authority_scan_strings(child))
        return tuple(strings)
    if isinstance(value, list):
        for child in value:
            strings.extend(_authority_scan_strings(child))
        return tuple(strings)
    if isinstance(value, str):
        strings.append(value)
    return tuple(strings)


def _plain_authority_scan_text(text: str) -> str:
    scanned_lines: list[str] = []
    for line in text.splitlines():
        normalized = line.strip().lower()
        if normalized.startswith("authority:"):
            continue
        if "not accepted" in normalized and "not proof" in normalized:
            continue
        scanned_lines.append(line)
    return "\n".join(scanned_lines)


__all__ = [
    "CROSSCHECK_AUTHORITY_NOTICE",
    "GAP_AUTHORITY_NOTICE",
    "CrossCheckItem",
    "CrossCheckMatrix",
    "CrossCheckReport",
    "FormalizationGap",
    "GapExportResult",
    "GapKind",
    "ProofObligation",
    "ReviewRequiredItem",
    "SourceGap",
    "UnverifiedClaim",
    "WorkflowEvidenceReport",
    "WorkflowGap",
    "WorkflowGapReport",
    "build_crosscheck_report",
    "build_gap_report",
    "build_workflow_evidence_report",
    "export_crosscheck_report",
    "export_gap_report",
    "render_crosscheck_markdown",
    "scan_crosscheck_report_text",
    "workflow_crosscheck_markdown_path",
    "workflow_crosscheck_path",
    "workflow_gap_path",
]
