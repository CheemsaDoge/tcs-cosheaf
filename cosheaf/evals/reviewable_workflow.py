"""Deterministic reviewable-workflow eval harness."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import field_validator

from cosheaf.memory.models import MemoryModel
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.engine import (
    WORKFLOW_AUTHORITY_NOTICE,
    ReadinessClass,
    WorkflowEvidenceRef,
    WorkflowFailureSummary,
    WorkflowStep,
    append_step,
    append_workflow_event,
    assess_readiness,
    load_workflow,
    start_workflow,
    step_workflow,
    workflow_events_path,
    workflow_fsm_path,
    workflow_librarian_path,
    workflow_loop_path,
    workflow_path,
    write_workflow,
)
from cosheaf.workflow.handoff import (
    WorkflowHandoffScanResult,
    build_workflow_handoff,
    scan_workflow_handoff,
    workflow_handoff_id,
)
from cosheaf.workflow.proposal import (
    DraftResearchArtifactProposal,
    build_draft_proposal,
)

DEFAULT_REVIEWABLE_WORKFLOW_EVAL_CASES = (
    Path("evals") / "reviewable_workflow" / "cases.yaml"
)

ISSUE_ID = "issue.eval.reviewable-workflow"
PUBLIC_ARTIFACT_ID = "definition.eval.reviewable-public"
PRIVATE_DRAFT_ARTIFACT_ID = "claim.eval.reviewable-private"


class ReviewableWorkflowEvalError(ValueError):
    """Raised for expected reviewable-workflow eval loading failures."""


class ReviewableWorkflowEvalKind(StrEnum):
    """Supported issue-to-reviewable-packet eval scenarios."""

    ACCEPTED_DEPENDENCY_DRAFT_TARGET = "accepted_dependency_draft_target"
    REPEATED_FAILURE_MEMORY = "repeated_failure_memory"
    UNCHECKED_COUNTEREXAMPLE = "unchecked_counterexample"
    PRIVATE_LEAKAGE_RISK = "private_leakage_risk"
    GATE_SCANNER_BLOCKER = "gate_scanner_blocker"
    DRAFT_PROPOSAL_READY = "draft_proposal_ready"


class ReviewableWorkflowEvalCase(MemoryModel):
    """One deterministic reviewable-workflow eval case."""

    id: str | None = None
    kind: ReviewableWorkflowEvalKind

    @field_validator("id")
    @classmethod
    def _id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("case id must be non-empty")
        return normalized


class ReviewableWorkflowEvalCaseResult(MemoryModel):
    """One reviewable-workflow eval case result."""

    id: str
    kind: ReviewableWorkflowEvalKind
    passed: bool
    workflow_valid: bool = False
    librarian_trace_complete: bool = False
    fsm_replay_valid: bool = False
    local_action_whitelist_valid: bool = False
    draft_proposal_valid: bool = False
    handoff_scanner_blocked: bool = False
    authority_overclaim_rejected: bool = False
    private_leak_rejected: bool = False
    review_readiness_classified: bool = False
    skipped_not_pass: bool = False
    accepted_write_performed: bool = False
    failures: list[str]


class ReviewableWorkflowEvalMetrics(MemoryModel):
    """Aggregate reviewable-workflow eval metrics."""

    workflow_validity_rate: float
    librarian_trace_completeness_rate: float
    fsm_replay_validity_rate: float
    local_action_whitelist_rate: float
    draft_proposal_validity_rate: float
    handoff_scanner_block_rate: float
    authority_overclaim_rejection_rate: float
    private_leak_rejection_rate: float
    review_readiness_classification_rate: float
    skipped_not_pass_count: int
    accepted_write_violation_count: int


class ReviewableWorkflowEvalReport(MemoryModel):
    """Reviewable-workflow eval report."""

    schema_version: int = 1
    kind: str = "reviewable_workflow_eval"
    case_count: int
    passed: bool
    fixture_issue_id: str = ISSUE_ID
    fixture_public_artifact_id: str = PUBLIC_ARTIFACT_ID
    fixture_private_draft_artifact_id: str = PRIVATE_DRAFT_ARTIFACT_ID
    metrics: ReviewableWorkflowEvalMetrics
    cases: list[ReviewableWorkflowEvalCaseResult]
    authority_notice: str = WORKFLOW_AUTHORITY_NOTICE

    def to_json(self) -> str:
        return json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
        ) + "\n"


@dataclass(frozen=True)
class ReviewableWorkflowEvalSuite:
    """Loaded reviewable-workflow eval cases."""

    cases: list[ReviewableWorkflowEvalCase]


def resolve_reviewable_workflow_eval_case_path(
    context: RepoContext,
    cases_path: Path,
) -> Path:
    """Resolve explicit or default reviewable-workflow eval case path."""
    repo_root = context.repo_root
    path = cases_path if cases_path.is_absolute() else repo_root / cases_path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ReviewableWorkflowEvalError(
            "reviewable-workflow eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(
        cases_path
    ).is_absolute():
        raise ReviewableWorkflowEvalError(
            "reviewable-workflow eval case file must be repository-local"
        )
    return resolved


def load_reviewable_workflow_eval_suite(
    path: Path,
) -> ReviewableWorkflowEvalSuite:
    """Load reviewable-workflow eval cases from YAML."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise ReviewableWorkflowEvalError(f"could not read eval cases: {path}") from exc
    if not isinstance(raw, dict):
        raise ReviewableWorkflowEvalError(
            "reviewable-workflow eval cases must be a mapping"
        )
    cases_raw = raw.get("cases")
    if not isinstance(cases_raw, list):
        raise ReviewableWorkflowEvalError(
            "reviewable-workflow eval cases require a cases list"
        )
    cases = [ReviewableWorkflowEvalCase.model_validate(item) for item in cases_raw]
    return ReviewableWorkflowEvalSuite(cases=cases)


def run_reviewable_workflow_eval_suite(
    context: RepoContext,
    suite: ReviewableWorkflowEvalSuite,
) -> ReviewableWorkflowEvalReport:
    """Run deterministic issue-to-reviewable-packet eval cases."""
    _ = context
    results = [_run_case(case) for case in suite.cases]
    metrics = ReviewableWorkflowEvalMetrics(
        workflow_validity_rate=_rate_all(results, "workflow_valid"),
        librarian_trace_completeness_rate=_rate_all(
            results,
            "librarian_trace_complete",
        ),
        fsm_replay_validity_rate=_rate_all(results, "fsm_replay_valid"),
        local_action_whitelist_rate=_rate_all(
            results,
            "local_action_whitelist_valid",
        ),
        draft_proposal_validity_rate=_rate_all(results, "draft_proposal_valid"),
        handoff_scanner_block_rate=_rate_selected(
            results,
            {
                ReviewableWorkflowEvalKind.PRIVATE_LEAKAGE_RISK,
                ReviewableWorkflowEvalKind.GATE_SCANNER_BLOCKER,
            },
            "handoff_scanner_blocked",
        ),
        authority_overclaim_rejection_rate=_rate_selected(
            results,
            {ReviewableWorkflowEvalKind.GATE_SCANNER_BLOCKER},
            "authority_overclaim_rejected",
        ),
        private_leak_rejection_rate=_rate_selected(
            results,
            {ReviewableWorkflowEvalKind.PRIVATE_LEAKAGE_RISK},
            "private_leak_rejected",
        ),
        review_readiness_classification_rate=_rate_all(
            results,
            "review_readiness_classified",
        ),
        skipped_not_pass_count=sum(1 for result in results if result.skipped_not_pass),
        accepted_write_violation_count=sum(
            1 for result in results if result.accepted_write_performed
        ),
    )
    return ReviewableWorkflowEvalReport(
        case_count=len(results),
        passed=all(result.passed for result in results),
        metrics=metrics,
        cases=results,
    )


def _run_case(
    case: ReviewableWorkflowEvalCase,
) -> ReviewableWorkflowEvalCaseResult:
    with tempfile.TemporaryDirectory(
        prefix="cosheaf-reviewable-workflow-eval-"
    ) as temp_dir:
        context = RepoContext(Path(temp_dir))
        _write_eval_fixture(context.repo_root)
        result = _evaluate_case(context, case)
    return result


def _evaluate_case(
    context: RepoContext,
    case: ReviewableWorkflowEvalCase,
) -> ReviewableWorkflowEvalCaseResult:
    slug = case.kind.value.replace("_", "-")
    workflow_id = f"workflow.eval.{slug}"
    start_workflow(
        context,
        issue_id=ISSUE_ID,
        query=_query_for_case(case.kind),
        workflow_id=workflow_id,
    )
    local_action_whitelist_valid = _unknown_action_is_blocked(context, slug)

    failures: list[str] = []
    draft_proposal_valid = False
    handoff_scanner_blocked = False
    authority_overclaim_rejected = False
    private_leak_rejected = False
    skipped_not_pass = False
    accepted_write_performed = False

    if case.kind is ReviewableWorkflowEvalKind.ACCEPTED_DEPENDENCY_DRAFT_TARGET:
        _append_success_steps(
            context,
            workflow_id,
            ("workspace.info", "context.build"),
            output_refs={
                "accepted_dependency": PUBLIC_ARTIFACT_ID,
                "draft_target": PRIVATE_DRAFT_ARTIFACT_ID,
            },
        )
        proposal = build_draft_proposal(context, workflow_id)
        draft_proposal_valid = _proposal_is_review_only(proposal)
        if not _fixture_depends_on_public(context.repo_root):
            failures.append(
                "expected private draft fixture to depend on public artifact"
            )
        if not draft_proposal_valid:
            failures.append("expected draft proposal to remain review-only")
    elif case.kind is ReviewableWorkflowEvalKind.REPEATED_FAILURE_MEMORY:
        record = load_workflow(context, workflow_id)
        record = record.model_copy(
            update={
                "failure_summary": WorkflowFailureSummary(
                    failure_count=1,
                    blocker_details=[
                        "Prior failure memory: direct induction missed an invariant."
                    ],
                )
            }
        )
        write_workflow(context, record)
        _append_success_steps(context, workflow_id, ("workspace.info", "context.build"))
        proposal = build_draft_proposal(context, workflow_id)
        draft_proposal_valid = (
            _proposal_is_review_only(proposal)
            and proposal.known_failure_summary.failure_count == 1
        )
        if not draft_proposal_valid:
            failures.append("expected prior failure memory in draft proposal")
    elif case.kind is ReviewableWorkflowEvalKind.UNCHECKED_COUNTEREXAMPLE:
        record = load_workflow(context, workflow_id)
        skipped = append_step(
            record,
            WorkflowStep(
                step_number=1,
                action="counterexample.review",
                status="skipped",
                output_refs={
                    "action_status": "skipped",
                    "counterexample_status": "unchecked",
                },
            ),
        )
        skipped = skipped.model_copy(
            update={
                "evidence_refs": [
                    WorkflowEvidenceRef(
                        kind="counterexample_candidate",
                        ref="counterexample.eval.unchecked",
                        checked=False,
                    )
                ],
                "readiness": assess_readiness(skipped).classification,
            }
        )
        write_workflow(context, skipped)
        proposal = build_draft_proposal(context, workflow_id)
        draft_proposal_valid = _proposal_is_review_only(proposal)
        skipped_not_pass = True
        if not draft_proposal_valid:
            failures.append("expected unchecked counterexample proposal boundary")
    elif case.kind is ReviewableWorkflowEvalKind.PRIVATE_LEAKAGE_RISK:
        _append_success_steps(
            context,
            workflow_id,
            ("workspace.info",),
            warnings=[
                "private leakage risk: kb/private/draft/claims/"
                f"{PRIVATE_DRAFT_ARTIFACT_ID}.yaml"
            ],
        )
        scan = scan_workflow_handoff(context, workflow_handoff_id(workflow_id))
        codes = _scan_codes(scan)
        handoff_scanner_blocked = scan.handoff_blocked
        private_leak_rejected = "private_path_reference" in codes
        if not private_leak_rejected:
            failures.append("expected handoff scanner to reject private leakage")
    elif case.kind is ReviewableWorkflowEvalKind.GATE_SCANNER_BLOCKER:
        append_workflow_event(
            context,
            workflow_id=workflow_id,
            event_kind="unsafe_eval_fixture",
            payload={
                "target_path": "kb/accepted/claims/claim.eval.bad.yaml",
                "human_reviewed": True,
                "gate_pass": True,
                "source_metadata": "created",
            },
        )
        scan = scan_workflow_handoff(context, workflow_handoff_id(workflow_id))
        codes = _scan_codes(scan)
        handoff_scanner_blocked = scan.handoff_blocked
        authority_overclaim_rejected = {
            "accepted_write_attempt",
            "human_review_overclaim",
            "verifier_gate_overclaim",
            "source_metadata_fabrication",
        } <= codes
        if not authority_overclaim_rejected:
            failures.append("expected scanner to reject authority overclaims")
    elif case.kind is ReviewableWorkflowEvalKind.DRAFT_PROPOSAL_READY:
        _append_success_steps(context, workflow_id, ("workspace.info", "context.build"))
        record = load_workflow(context, workflow_id)
        readiness = assess_readiness(record)
        proposal = build_draft_proposal(context, workflow_id)
        draft_proposal_valid = _proposal_is_review_only(proposal)
        try:
            handoff = build_workflow_handoff(context, workflow_id)
        except Exception as exc:
            failures.append(f"expected clean workflow handoff: {exc}")
        else:
            draft_proposal_valid = (
                draft_proposal_valid and handoff.handoff.review_context_only
            )
        if readiness.classification is not ReadinessClass.READY:
            failures.append("expected workflow to reach draft-proposal-ready state")
    else:  # pragma: no cover - StrEnum exhaustiveness guard
        failures.append(f"unsupported reviewable-workflow eval case: {case.kind}")

    workflow_valid = _workflow_is_valid(context, workflow_id)
    librarian_trace_complete = _component_trace_complete(context, workflow_id)
    fsm_replay_valid = _fsm_replay_is_valid(context, workflow_id)
    review_readiness_classified = isinstance(
        assess_readiness(load_workflow(context, workflow_id)).classification,
        ReadinessClass,
    )

    if not workflow_valid:
        failures.append("expected persisted workflow record and events")
    if not librarian_trace_complete:
        failures.append("expected workflow component trace files")
    if not fsm_replay_valid:
        failures.append("expected parseable FSM placeholder and event log")
    if not local_action_whitelist_valid:
        failures.append("expected non-whitelisted local action to be blocked")
    if not review_readiness_classified:
        failures.append("expected stable readiness classification")
    if accepted_write_performed:
        failures.append("eval case performed an accepted write")

    return ReviewableWorkflowEvalCaseResult(
        id=case.id or f"case.reviewable-workflow.{case.kind.value}",
        kind=case.kind,
        passed=not failures,
        workflow_valid=workflow_valid,
        librarian_trace_complete=librarian_trace_complete,
        fsm_replay_valid=fsm_replay_valid,
        local_action_whitelist_valid=local_action_whitelist_valid,
        draft_proposal_valid=draft_proposal_valid,
        handoff_scanner_blocked=handoff_scanner_blocked,
        authority_overclaim_rejected=authority_overclaim_rejected,
        private_leak_rejected=private_leak_rejected,
        review_readiness_classified=review_readiness_classified,
        skipped_not_pass=skipped_not_pass,
        accepted_write_performed=accepted_write_performed,
        failures=failures,
    )


def _rate_all(
    results: list[ReviewableWorkflowEvalCaseResult],
    field_name: str,
) -> float:
    if not results:
        return 1.0
    return sum(1 for result in results if bool(getattr(result, field_name))) / len(
        results
    )


def _rate_selected(
    results: list[ReviewableWorkflowEvalCaseResult],
    kinds: set[ReviewableWorkflowEvalKind],
    field_name: str,
) -> float:
    selected = [result for result in results if result.kind in kinds]
    if not selected:
        return 1.0
    return sum(1 for result in selected if bool(getattr(result, field_name))) / len(
        selected
    )


def _write_eval_fixture(root: Path) -> None:
    (root / "kb" / "public" / "accepted" / "definitions").mkdir(parents=True)
    (root / "kb" / "private" / "draft" / "claims").mkdir(parents=True)
    (root / "issues" / "open").mkdir(parents=True)
    (root / "cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "reviewable-workflow-eval"',
                "",
                "[[kb]]",
                'name = "public"',
                'path = "kb/public"',
                "readonly = true",
                "priority = 10",
                "",
                "[[kb]]",
                'name = "private"',
                'path = "kb/private"',
                "readonly = false",
                "priority = 20",
                "",
                "[policy]",
                "private_can_depend_on_public = true",
                "public_can_depend_on_private = false",
                "accepted_requires_source = true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_yaml(
        root,
        "kb/public/accepted/definitions/definition.eval.reviewable-public.yaml",
        _artifact_data(
            PUBLIC_ARTIFACT_ID,
            artifact_type="definition",
            status="accepted",
            sources=[_source_fixture()],
        ),
    )
    _write_yaml(
        root,
        "kb/private/draft/claims/claim.eval.reviewable-private.yaml",
        _artifact_data(
            PRIVATE_DRAFT_ARTIFACT_ID,
            artifact_type="claim",
            status="draft",
            depends_on=[PUBLIC_ARTIFACT_ID],
        ),
    )
    _write_yaml(
        root,
        "issues/open/issue.eval.reviewable-workflow.yaml",
        {
            "id": ISSUE_ID,
            "type": "issue",
            "title": "Evaluate reviewable workflow packet",
            "status": "open",
            "created_at": "2026-06-18T00:00:00Z",
            "updated_at": "2026-06-18T00:00:00Z",
            "authors": ["eval-fixture"],
            "severity": "low",
            "description": "Reviewable workflow eval fixture.",
            "related_artifacts": [PRIVATE_DRAFT_ARTIFACT_ID],
            "tags": ["reviewable-workflow"],
        },
    )


def _artifact_data(
    artifact_id: str,
    *,
    artifact_type: str,
    status: str,
    depends_on: list[str] | None = None,
    sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": artifact_type,
        "title": f"Eval fixture {artifact_id}",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-18T00:00:00Z",
        "updated_at": "2026-06-18T00:00:00Z",
        "authors": ["eval-fixture"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": ["reviewable-workflow"],
        "statement": "Reviewable workflow eval fixture statement.",
        "evidence": [
            {
                "kind": "external",
                "path": "external:reviewable-workflow-eval",
                "summary": "Deterministic local eval fixture.",
            }
        ],
        "sources": sources or [],
        "review": {"state": "requested", "notes": "Eval fixture only."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _source_fixture() -> dict[str, Any]:
    return {
        "kind": "book",
        "title": "Reviewable Workflow Fixture Source",
        "authors": ["A. Maintainer"],
        "year": 2026,
        "doi": "",
        "arxiv": "",
        "url": "https://example.invalid/reviewable-workflow-fixture",
        "theorem_number": "Definition 1",
        "page": "1",
        "notes": "Fixture source metadata for temporary eval workspace only.",
    }


def _write_yaml(root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
        newline="\n",
    )


def _query_for_case(kind: ReviewableWorkflowEvalKind) -> str:
    return {
        ReviewableWorkflowEvalKind.ACCEPTED_DEPENDENCY_DRAFT_TARGET: (
            "use accepted public dependency for a private draft target"
        ),
        ReviewableWorkflowEvalKind.REPEATED_FAILURE_MEMORY: (
            "avoid a repeated failed direction"
        ),
        ReviewableWorkflowEvalKind.UNCHECKED_COUNTEREXAMPLE: (
            "preserve unchecked counterexample as non-pass evidence"
        ),
        ReviewableWorkflowEvalKind.PRIVATE_LEAKAGE_RISK: (
            "reject workflow packet private leakage"
        ),
        ReviewableWorkflowEvalKind.GATE_SCANNER_BLOCKER: (
            "reject gate and authority scanner blockers"
        ),
        ReviewableWorkflowEvalKind.DRAFT_PROPOSAL_READY: (
            "reach draft proposal readiness without accepted authority"
        ),
    }[kind]


def _append_success_steps(
    context: RepoContext,
    workflow_id: str,
    actions: tuple[str, ...],
    *,
    output_refs: dict[str, str] | None = None,
    warnings: list[str] | None = None,
) -> None:
    record = load_workflow(context, workflow_id)
    for action in actions:
        record = append_step(
            record,
            WorkflowStep(
                step_number=len(record.steps) + 1,
                action=action,
                status="success",
                output_refs=dict(output_refs or {}),
                warnings=list(warnings or []),
            ),
        )
    readiness = assess_readiness(record)
    record = record.model_copy(update={"readiness": readiness.classification})
    write_workflow(context, record)


def _unknown_action_is_blocked(context: RepoContext, slug: str) -> bool:
    workflow_id = f"workflow.eval.{slug}.whitelist"
    start_workflow(
        context,
        issue_id=ISSUE_ID,
        query="local action whitelist fixture",
        workflow_id=workflow_id,
    )
    result = step_workflow(
        context,
        workflow_id,
        action_id="unsafe.not-registered",
        execute_local_action=True,
    )
    step = result.workflow.steps[-1]
    return step.status == "blocked" and step.output_refs.get("error_code") == (
        "UNKNOWN_ACTION"
    )


def _workflow_is_valid(context: RepoContext, workflow_id: str) -> bool:
    workflow = load_workflow(context, workflow_id)
    return (
        workflow.workflow_id == workflow_id
        and workflow.issue_id == ISSUE_ID
        and workflow.authority_notice == WORKFLOW_AUTHORITY_NOTICE
        and context.resolve(workflow_path(workflow_id)).is_file()
        and context.resolve(workflow_events_path(workflow_id)).is_file()
    )


def _component_trace_complete(context: RepoContext, workflow_id: str) -> bool:
    for path in (
        workflow_librarian_path(workflow_id),
        workflow_fsm_path(workflow_id),
        workflow_loop_path(workflow_id),
    ):
        target = context.resolve(path)
        if not target.is_file():
            return False
        payload = json.loads(target.read_text(encoding="utf-8-sig"))
        if payload.get("workflow_id") != workflow_id:
            return False
    return True


def _fsm_replay_is_valid(context: RepoContext, workflow_id: str) -> bool:
    fsm_payload = json.loads(
        context.resolve(workflow_fsm_path(workflow_id)).read_text(
            encoding="utf-8-sig"
        )
    )
    if fsm_payload.get("status") != "planned":
        return False
    events_path = context.resolve(workflow_events_path(workflow_id))
    for line in events_path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("workflow_id") != workflow_id:
            return False
    return True


def _proposal_is_review_only(proposal: DraftResearchArtifactProposal) -> bool:
    return (
        bool(proposal.claim_candidates)
        and proposal.claim_candidates[0].status == "draft"
        and proposal.review_checklist.human_review_required is True
        and "review context only" in proposal.authority_notice.lower()
    )


def _fixture_depends_on_public(root: Path) -> bool:
    payload = yaml.safe_load(
        (
            root
            / "kb"
            / "private"
            / "draft"
            / "claims"
            / "claim.eval.reviewable-private.yaml"
        ).read_text(encoding="utf-8-sig")
    )
    return isinstance(payload, dict) and PUBLIC_ARTIFACT_ID in payload.get(
        "depends_on",
        [],
    )


def _scan_codes(scan: WorkflowHandoffScanResult) -> set[str]:
    return {finding.code for finding in scan.findings}


__all__ = [
    "DEFAULT_REVIEWABLE_WORKFLOW_EVAL_CASES",
    "PRIVATE_DRAFT_ARTIFACT_ID",
    "PUBLIC_ARTIFACT_ID",
    "ReviewableWorkflowEvalCase",
    "ReviewableWorkflowEvalCaseResult",
    "ReviewableWorkflowEvalError",
    "ReviewableWorkflowEvalKind",
    "ReviewableWorkflowEvalMetrics",
    "ReviewableWorkflowEvalReport",
    "ReviewableWorkflowEvalSuite",
    "load_reviewable_workflow_eval_suite",
    "resolve_reviewable_workflow_eval_case_path",
    "run_reviewable_workflow_eval_suite",
]
