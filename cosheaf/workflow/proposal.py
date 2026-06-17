"""Draft proposal generation from persisted workflow output."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, field_validator

from cosheaf.core.ids import validate_artifact_id
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.engine import (
    WorkflowRecord,
    load_workflow,
    workflow_events_path,
    workflow_fsm_path,
    workflow_librarian_path,
    workflow_loop_path,
    workflow_path,
    workflow_readiness_path,
)

WORKFLOW_DRAFT_PROPOSAL_AUTHORITY_NOTICE = (
    "Draft workflow proposals are review context only; they are not proof, "
    "source metadata, human review, verifier pass, gate pass, accepted status, "
    "accepted refutation, or promotion authority."
)


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _json_text(payload: Any) -> str:
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json")
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def _repo_relative_path(context: RepoContext, path: Path) -> Path:
    if path.is_absolute():
        resolved = path.resolve()
    else:
        resolved = context.resolve(path)
    root = context.repo_root.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError("draft proposal output path must stay inside the repository")
    return resolved.relative_to(root)


def _is_accepted_path(relative_path: Path) -> bool:
    normalized = relative_path.as_posix().lower()
    return normalized.startswith("kb/accepted/") or "/accepted/" in normalized


def _is_public_path(context: RepoContext, relative_path: Path) -> bool:
    normalized = relative_path.as_posix().lower()
    root = context.kb_root_for_path(relative_path)
    if root is not None and (root.readonly or root.name.lower() == "public"):
        return True
    return normalized.startswith("kb/public/") or "/public/" in normalized


def _ensure_review_context_output(context: RepoContext, relative_path: Path) -> None:
    if _is_accepted_path(relative_path):
        raise ValueError("draft proposal output must not target accepted KB paths")
    if _is_public_path(context, relative_path):
        raise ValueError("draft proposal output must not target public KB paths")


def _ensure_private_root(context: RepoContext, private_root: Path) -> Path:
    relative = _repo_relative_path(context, private_root)
    if _is_accepted_path(relative):
        raise ValueError("private draft root must not target accepted KB paths")
    if _is_public_path(context, relative):
        raise ValueError("private draft root must not target public KB paths")
    root = context.kb_root_for_path(relative)
    if root is not None and root.readonly:
        raise ValueError("private draft root must be writable")
    if (
        root is not None
        and context.workspace_config.configured
        and root.name.lower() != "private"
    ):
        raise ValueError("private draft root must be a private KB root")
    if root is None and "private" not in {part.lower() for part in relative.parts}:
        raise ValueError("private draft root path must be explicitly private")
    return relative


class DraftProposalModel(BaseModel):
    """Strict base model for draft proposal review-context records."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        return _json_text(self)


class WorkflowProposalProvenance(DraftProposalModel):
    workflow_id: str
    workflow_path: str
    events_path: str
    librarian_path: str
    fsm_path: str
    loop_path: str
    readiness_path: str
    action_ids: list[str] = Field(default_factory=list)
    authority_notice: str = WORKFLOW_DRAFT_PROPOSAL_AUTHORITY_NOTICE

    @field_validator("workflow_id")
    @classmethod
    def _workflow_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())


class DraftClaimCandidate(DraftProposalModel):
    candidate_id: str
    candidate_kind: str = "candidate_claim"
    status: str = "draft"
    title: str
    statement: str
    depends_on: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    authority_notice: str = WORKFLOW_DRAFT_PROPOSAL_AUTHORITY_NOTICE

    @field_validator("candidate_id")
    @classmethod
    def _candidate_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("status")
    @classmethod
    def _status(cls, value: str) -> str:
        if value != "draft":
            raise ValueError("draft proposal candidates must keep draft status")
        return value

    @field_validator("candidate_kind")
    @classmethod
    def _kind(cls, value: str) -> str:
        if value != "candidate_claim":
            raise ValueError("draft proposal candidates must remain candidate claims")
        return value


class DraftProofSketchCandidate(DraftProposalModel):
    candidate_id: str
    status: str = "draft"
    summary: str
    unchecked_steps: list[str] = Field(default_factory=list)
    authority_notice: str = WORKFLOW_DRAFT_PROPOSAL_AUTHORITY_NOTICE


class DraftCounterexampleCandidate(DraftProposalModel):
    candidate_id: str
    status: str = "draft"
    summary: str
    checked: bool = False
    authority_notice: str = WORKFLOW_DRAFT_PROPOSAL_AUTHORITY_NOTICE


class DraftEvidenceSummary(DraftProposalModel):
    workflow_steps: int = 0
    local_action_statuses: list[str] = Field(default_factory=list)
    unresolved_warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    authority_notice: str = WORKFLOW_DRAFT_PROPOSAL_AUTHORITY_NOTICE


class DraftKnownFailureSummary(DraftProposalModel):
    failure_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    authority_notice: str = WORKFLOW_DRAFT_PROPOSAL_AUTHORITY_NOTICE


class DraftDependencySummary(DraftProposalModel):
    depends_on: list[str] = Field(default_factory=list)
    unresolved_dependencies: list[str] = Field(default_factory=list)
    authority_notice: str = WORKFLOW_DRAFT_PROPOSAL_AUTHORITY_NOTICE


class DraftReviewChecklist(DraftProposalModel):
    human_review_required: bool = True
    source_metadata_required_before_acceptance: bool = True
    validation_required: bool = True
    gate_required: bool = True
    unchecked_items: list[str] = Field(default_factory=list)
    authority_notice: str = WORKFLOW_DRAFT_PROPOSAL_AUTHORITY_NOTICE


class DraftResearchArtifactProposal(DraftProposalModel):
    proposal_id: str
    workflow_id: str
    issue_id: str
    generated_at: datetime
    provenance: WorkflowProposalProvenance
    claim_candidates: list[DraftClaimCandidate] = Field(default_factory=list)
    proof_sketch_candidates: list[DraftProofSketchCandidate] = Field(
        default_factory=list
    )
    counterexample_candidates: list[DraftCounterexampleCandidate] = Field(
        default_factory=list
    )
    evidence_summary: DraftEvidenceSummary
    known_failure_summary: DraftKnownFailureSummary
    dependency_summary: DraftDependencySummary
    review_checklist: DraftReviewChecklist
    authority_notice: str = WORKFLOW_DRAFT_PROPOSAL_AUTHORITY_NOTICE

    @field_validator("proposal_id", "workflow_id", "issue_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())


class DraftProposalWriteResult(DraftProposalModel):
    proposal: DraftResearchArtifactProposal
    target_path: str | None = None
    written: bool = False
    artifact_written: bool = False
    dry_run: bool = False
    authority_notice: str = WORKFLOW_DRAFT_PROPOSAL_AUTHORITY_NOTICE


def _workflow_from_payload(
    context: RepoContext,
    workflow_id: str,
    workflow_payload: dict[str, Any] | None,
) -> WorkflowRecord:
    if workflow_payload is None:
        return load_workflow(context, workflow_id)
    return WorkflowRecord.model_validate(workflow_payload)


def _candidate_statement(workflow: WorkflowRecord) -> str:
    query = workflow.query or workflow.issue_id
    return (
        f"Candidate research claim derived from workflow {workflow.workflow_id} "
        f"for query: {query}. This requires source review, validation, gates, "
        "and human review before any lifecycle change."
    )


def build_draft_proposal(
    context: RepoContext,
    workflow_id: str,
    *,
    artifact_id: str | None = None,
    workflow_payload: dict[str, Any] | None = None,
    candidate_status: str = "draft",
) -> DraftResearchArtifactProposal:
    """Build a non-authoritative draft proposal from workflow runtime state."""
    if candidate_status != "draft":
        raise ValueError("draft proposal candidates must keep draft status")
    workflow = _workflow_from_payload(context, workflow_id, workflow_payload)
    candidate_id = artifact_id or f"claim.{workflow.workflow_id}.candidate"
    validate_artifact_id(candidate_id)
    action_statuses = [
        step.output_refs.get("action_status", step.status) for step in workflow.steps
    ]
    unresolved_warnings = [
        warning for step in workflow.steps for warning in step.warnings if warning
    ]
    planned_steps = [step.action for step in workflow.steps if step.status == "planned"]
    blockers = list(workflow.failure_summary.blocker_details)
    if planned_steps:
        blockers.extend(
            f"planned step not executed: {action}" for action in planned_steps
        )
    limitations = [
        "Proposal is generated from workflow runtime review context only.",
        "No source metadata has been created or verified by this command.",
        "No verifier, gate, or human-review authority is granted.",
    ]
    if workflow.readiness is not None:
        limitations.append(f"workflow readiness: {workflow.readiness.value}")
    return DraftResearchArtifactProposal(
        proposal_id=f"proposal.{workflow.workflow_id}",
        workflow_id=workflow.workflow_id,
        issue_id=workflow.issue_id,
        generated_at=_utc_now(),
        provenance=WorkflowProposalProvenance(
            workflow_id=workflow.workflow_id,
            workflow_path=workflow_path(workflow.workflow_id).as_posix(),
            events_path=workflow_events_path(workflow.workflow_id).as_posix(),
            librarian_path=workflow_librarian_path(workflow.workflow_id).as_posix(),
            fsm_path=workflow_fsm_path(workflow.workflow_id).as_posix(),
            loop_path=workflow_loop_path(workflow.workflow_id).as_posix(),
            readiness_path=workflow_readiness_path(workflow.workflow_id).as_posix(),
            action_ids=[step.action for step in workflow.steps],
        ),
        claim_candidates=[
            DraftClaimCandidate(
                candidate_id=candidate_id,
                title=f"Draft candidate from {workflow.workflow_id}",
                statement=_candidate_statement(workflow),
                limitations=limitations,
            )
        ],
        evidence_summary=DraftEvidenceSummary(
            workflow_steps=len(workflow.steps),
            local_action_statuses=action_statuses,
            unresolved_warnings=unresolved_warnings,
            limitations=limitations,
        ),
        known_failure_summary=DraftKnownFailureSummary(
            failure_count=len(blockers),
            blockers=blockers,
        ),
        dependency_summary=DraftDependencySummary(depends_on=[]),
        review_checklist=DraftReviewChecklist(
            unchecked_items=[
                "Confirm the candidate statement against durable sources.",
                "Add source metadata before any accepted promotion.",
                "Run validation and gates before review.",
                "Record explicit human review outside this workflow output.",
            ]
        ),
    )


def _write_review_context_json(
    context: RepoContext,
    relative_path: Path,
    proposal: DraftResearchArtifactProposal,
    *,
    dry_run: bool,
) -> DraftProposalWriteResult:
    _ensure_review_context_output(context, relative_path)
    if not dry_run:
        target = context.resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(proposal.to_json(), encoding="utf-8", newline="\n")
    return DraftProposalWriteResult(
        proposal=proposal,
        target_path=relative_path.as_posix(),
        written=not dry_run,
        dry_run=dry_run,
    )


def _draft_artifact_payload(
    proposal: DraftResearchArtifactProposal,
    artifact_id: str,
) -> dict[str, Any]:
    claim = proposal.claim_candidates[0]
    now = proposal.generated_at.isoformat()
    return {
        "id": artifact_id,
        "type": "claim",
        "title": claim.title,
        "domain": ["workflow-proposal"],
        "status": "draft",
        "created_at": now,
        "updated_at": now,
        "authors": ["cosheaf-workflow"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["workflow-proposal", "candidate"],
        "statement": claim.statement,
        "evidence": [
            {
                "kind": "workflow_proposal",
                "path": proposal.provenance.workflow_path,
                "summary": "Runtime workflow provenance for a draft candidate.",
            }
        ],
        "review": {
            "state": "requested",
            "notes": "Requires explicit maintainer review before lifecycle changes.",
        },
        "risk": {
            "level": "medium",
            "notes": "Generated candidate from workflow runtime context only.",
        },
    }


def _write_private_draft_artifact(
    context: RepoContext,
    private_root: Path,
    proposal: DraftResearchArtifactProposal,
    artifact_id: str,
    *,
    dry_run: bool,
) -> DraftProposalWriteResult:
    resolved_artifact_id = validate_artifact_id(artifact_id.strip())
    relative_root = _ensure_private_root(context, private_root)
    target = relative_root / "draft" / "claims" / f"{resolved_artifact_id}.yaml"
    _ensure_review_context_output(context, target)
    payload = _draft_artifact_payload(proposal, resolved_artifact_id)
    if not dry_run:
        resolved = context.resolve(target)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
            newline="\n",
        )
    return DraftProposalWriteResult(
        proposal=proposal,
        target_path=target.as_posix(),
        written=not dry_run,
        artifact_written=not dry_run,
        dry_run=dry_run,
    )


def write_draft_proposal(
    context: RepoContext,
    workflow_id: str,
    *,
    out: Path | None = None,
    private_root: Path | None = None,
    artifact_id: str | None = None,
    dry_run: bool = False,
) -> DraftProposalWriteResult:
    """Write or preview a workflow draft proposal."""
    if out is not None and private_root is not None:
        raise ValueError("choose either --out or --private-root, not both")
    if private_root is not None and artifact_id is None:
        raise ValueError("--private-root requires --artifact-id")
    proposal = build_draft_proposal(
        context,
        workflow_id,
        artifact_id=artifact_id,
    )
    if private_root is not None:
        return _write_private_draft_artifact(
            context,
            private_root,
            proposal,
            artifact_id or proposal.claim_candidates[0].candidate_id,
            dry_run=dry_run,
        )
    if out is not None:
        relative_out = _repo_relative_path(context, out)
        return _write_review_context_json(
            context,
            relative_out,
            proposal,
            dry_run=dry_run,
        )
    return DraftProposalWriteResult(proposal=proposal, dry_run=True)


__all__ = [
    "WORKFLOW_DRAFT_PROPOSAL_AUTHORITY_NOTICE",
    "DraftClaimCandidate",
    "DraftCounterexampleCandidate",
    "DraftDependencySummary",
    "DraftEvidenceSummary",
    "DraftKnownFailureSummary",
    "DraftProofSketchCandidate",
    "DraftProposalWriteResult",
    "DraftResearchArtifactProposal",
    "DraftReviewChecklist",
    "WorkflowProposalProvenance",
    "build_draft_proposal",
    "write_draft_proposal",
]
