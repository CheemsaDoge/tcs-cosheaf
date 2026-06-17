"""Deterministic bounded research-loop eval harness."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PureWindowsPath

import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError, field_validator

from cosheaf.memory.models import MemoryModel
from cosheaf.research.loop import (
    RESEARCH_LOOP_AUTHORITY_NOTICE,
    AttemptEvidenceSummary,
    AttemptFailureRecord,
    ResearchLoopAttempt,
    ResearchLoopAttemptStatus,
    ResearchLoopBudget,
    ResearchLoopError,
    ResearchLoopFailureTag,
    ResearchLoopOperatorResult,
    append_attempt,
    import_operator_result,
    next_loop_action,
    research_loop_events_path,
    run_loop,
    scan_research_loop,
    start_loop,
)
from cosheaf.storage.repo import RepoContext

DEFAULT_RESEARCH_LOOP_EVAL_CASES = Path("evals") / "research_loop" / "cases.yaml"

ISSUE_ID = "issue.eval.research-loop"
PUBLIC_ARTIFACT_ID = "definition.eval.graph"
PRIVATE_DRAFT_ARTIFACT_ID = "claim.eval.private"


class ResearchLoopEvalError(ValueError):
    """Raised for expected research-loop eval loading failures."""


class ResearchLoopEvalKind(StrEnum):
    """Supported bounded research-loop eval scenarios."""

    LOOP_VALIDITY = "loop_validity"
    ATTEMPT_SCHEMA_VALIDITY = "attempt_schema_validity"
    REPEAT_FAILURE_DETECTION = "repeat_failure_detection"
    UNJUSTIFIED_RETRY_BLOCK = "unjustified_retry_block"
    PUBLIC_PRIVATE_LEAK_PREVENTION = "public_private_leak_prevention"
    SCANNER_BLOCKER_ACCURACY = "scanner_blocker_accuracy"
    HANDOFF_REVIEW_CONTEXT_VALIDITY = "handoff_review_context_validity"
    POLICY_OVERCLAIM_REJECTION = "policy_overclaim_rejection"
    BUDGET_STOP_ACCURACY = "budget_stop_accuracy"
    SKIPPED_NOT_PASS = "skipped_not_pass"


class ResearchLoopEvalCase(MemoryModel):
    """One deterministic research-loop eval case."""

    id: str | None = None
    kind: ResearchLoopEvalKind

    @field_validator("id")
    @classmethod
    def _id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("case id must be non-empty")
        return normalized


class ResearchLoopEvalCaseResult(MemoryModel):
    """One research-loop eval case result."""

    id: str
    kind: ResearchLoopEvalKind
    passed: bool
    loop_valid: bool = False
    attempt_schema_valid: bool = False
    repeat_failure_detected: bool = False
    unjustified_retry_blocked: bool = False
    private_leak_count: int = 0
    scanner_blocker_accuracy: bool = False
    handoff_review_context_valid: bool = False
    policy_overclaim_rejected: bool = False
    budget_stop_accurate: bool = False
    skipped_not_pass: bool = False
    accepted_write_performed: bool = False
    failures: list[str]


class ResearchLoopEvalMetrics(MemoryModel):
    """Aggregate research-loop eval metrics."""

    loop_validity_rate: float
    attempt_schema_validity_rate: float
    repeat_failure_detection_rate: float
    unjustified_retry_block_rate: float
    public_private_leak_count: int
    scanner_blocker_accuracy: float
    handoff_review_context_validity_rate: float
    policy_overclaim_rejection_rate: float
    budget_stop_accuracy: float
    skipped_not_pass_count: int
    accepted_write_violation_count: int


class ResearchLoopEvalReport(MemoryModel):
    """Research-loop eval report."""

    schema_version: int = 1
    kind: str = "research_loop_eval"
    case_count: int
    passed: bool
    fixture_issue_id: str = ISSUE_ID
    fixture_public_artifact_id: str = PUBLIC_ARTIFACT_ID
    fixture_private_draft_artifact_id: str = PRIVATE_DRAFT_ARTIFACT_ID
    metrics: ResearchLoopEvalMetrics
    cases: list[ResearchLoopEvalCaseResult]
    authority_notice: str = RESEARCH_LOOP_AUTHORITY_NOTICE

    def to_json(self) -> str:
        return json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
        ) + "\n"


@dataclass(frozen=True)
class ResearchLoopEvalSuite:
    """Loaded research-loop eval cases."""

    cases: list[ResearchLoopEvalCase]


def resolve_research_loop_eval_case_path(
    context: RepoContext,
    cases_path: Path,
) -> Path:
    """Resolve explicit or default research-loop eval case path."""
    repo_root = context.repo_root
    path = cases_path if cases_path.is_absolute() else repo_root / cases_path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ResearchLoopEvalError(
            "research-loop eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(
        cases_path
    ).is_absolute():
        raise ResearchLoopEvalError(
            "research-loop eval case file must be repository-local"
        )
    return resolved


def load_research_loop_eval_suite(path: Path) -> ResearchLoopEvalSuite:
    """Load research-loop eval cases from YAML."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise ResearchLoopEvalError(f"could not read eval cases: {path}") from exc
    if not isinstance(raw, dict):
        raise ResearchLoopEvalError("research-loop eval cases must be a mapping")
    cases_raw = raw.get("cases")
    if not isinstance(cases_raw, list):
        raise ResearchLoopEvalError("research-loop eval cases require a cases list")
    cases = [ResearchLoopEvalCase.model_validate(item) for item in cases_raw]
    return ResearchLoopEvalSuite(cases=cases)


def run_research_loop_eval_suite(
    context: RepoContext,
    suite: ResearchLoopEvalSuite,
) -> ResearchLoopEvalReport:
    """Run deterministic bounded research-loop eval cases."""
    _ = context
    results = [_run_case(case) for case in suite.cases]
    metrics = ResearchLoopEvalMetrics(
        loop_validity_rate=_rate(
            results,
            ResearchLoopEvalKind.LOOP_VALIDITY,
            "loop_valid",
        ),
        attempt_schema_validity_rate=_rate(
            results,
            ResearchLoopEvalKind.ATTEMPT_SCHEMA_VALIDITY,
            "attempt_schema_valid",
        ),
        repeat_failure_detection_rate=_rate(
            results,
            ResearchLoopEvalKind.REPEAT_FAILURE_DETECTION,
            "repeat_failure_detected",
        ),
        unjustified_retry_block_rate=_rate(
            results,
            ResearchLoopEvalKind.UNJUSTIFIED_RETRY_BLOCK,
            "unjustified_retry_blocked",
        ),
        public_private_leak_count=sum(result.private_leak_count for result in results),
        scanner_blocker_accuracy=_rate(
            results,
            ResearchLoopEvalKind.SCANNER_BLOCKER_ACCURACY,
            "scanner_blocker_accuracy",
        ),
        handoff_review_context_validity_rate=_rate(
            results,
            ResearchLoopEvalKind.HANDOFF_REVIEW_CONTEXT_VALIDITY,
            "handoff_review_context_valid",
        ),
        policy_overclaim_rejection_rate=_rate(
            results,
            ResearchLoopEvalKind.POLICY_OVERCLAIM_REJECTION,
            "policy_overclaim_rejected",
        ),
        budget_stop_accuracy=_rate(
            results,
            ResearchLoopEvalKind.BUDGET_STOP_ACCURACY,
            "budget_stop_accurate",
        ),
        skipped_not_pass_count=sum(1 for result in results if result.skipped_not_pass),
        accepted_write_violation_count=sum(
            1 for result in results if result.accepted_write_performed
        ),
    )
    return ResearchLoopEvalReport(
        case_count=len(results),
        passed=all(result.passed for result in results),
        metrics=metrics,
        cases=results,
    )


def _run_case(case: ResearchLoopEvalCase) -> ResearchLoopEvalCaseResult:
    with tempfile.TemporaryDirectory(prefix="cosheaf-research-loop-eval-") as temp_dir:
        context = RepoContext(Path(temp_dir))
        _write_eval_fixture(context.repo_root)
        result = _evaluate_case(context, case)
    return result


def _evaluate_case(
    context: RepoContext,
    case: ResearchLoopEvalCase,
) -> ResearchLoopEvalCaseResult:
    failures: list[str] = []
    loop_valid = False
    attempt_schema_valid = False
    repeat_failure_detected = False
    unjustified_retry_blocked = False
    private_leak_count = 0
    scanner_blocker_accuracy = False
    handoff_review_context_valid = False
    policy_overclaim_rejected = False
    budget_stop_accurate = False
    skipped_not_pass = False
    accepted_write_performed = False

    if case.kind is ResearchLoopEvalKind.LOOP_VALIDITY:
        start = start_loop(context, issue_id=ISSUE_ID, loop_id="loop.eval.valid")
        loop_valid = (
            start.loop.issue_id == ISSUE_ID
            and start.relative_path.as_posix().startswith(".cosheaf/research-loops/")
            and not (context.repo_root / "kb" / "accepted").exists()
        )
        if not loop_valid:
            failures.append("expected loop runtime record to stay valid and ignored")
    elif case.kind is ResearchLoopEvalKind.ATTEMPT_SCHEMA_VALIDITY:
        start_loop(context, issue_id=ISSUE_ID, loop_id="loop.eval.attempt")
        attempt = _failed_attempt("loop.eval.attempt", 1)
        written = append_attempt(context, "loop.eval.attempt", attempt)
        reloaded = ResearchLoopAttempt.model_validate(written.attempt.to_dict())
        attempt_schema_valid = reloaded.attempt_id == attempt.attempt_id
        if not attempt_schema_valid:
            failures.append("expected attempt schema round-trip to validate")
    elif case.kind is ResearchLoopEvalKind.REPEAT_FAILURE_DETECTION:
        _seed_prior_failure(context, "loop.eval.previous")
        start_loop(context, issue_id=ISSUE_ID, loop_id="loop.eval.current")
        next_result = next_loop_action(context, "loop.eval.current")
        repeat_failure_detected = (
            bool(next_result.previous_failures_to_avoid)
            and next_result.next_action.retry_requires_justification
        )
        if not repeat_failure_detected:
            failures.append("expected next action to surface prior failed direction")
    elif case.kind is ResearchLoopEvalKind.UNJUSTIFIED_RETRY_BLOCK:
        _seed_prior_failure(context, "loop.eval.previous")
        start_loop(context, issue_id=ISSUE_ID, loop_id="loop.eval.retry")
        try:
            import_operator_result(context, "loop.eval.retry", _operator_result())
        except ResearchLoopError as exc:
            unjustified_retry_blocked = (
                exc.code == "repeat_retry_requires_justification"
            )
        if not unjustified_retry_blocked:
            failures.append(
                "expected repeated failed direction to require justification"
            )
    elif case.kind is ResearchLoopEvalKind.PUBLIC_PRIVATE_LEAK_PREVENTION:
        _seed_public_only_leak_loop(context, "loop.eval.public-leak")
        report = scan_research_loop(context, "loop.eval.public-leak")
        expected = {"private_path_reference", "accepted_write_attempt"}
        codes = {finding.code for finding in report.findings}
        private_leak_count = 0 if expected <= codes and report.handoff_blocked else 1
        if private_leak_count:
            failures.append("expected scanner to block public/private leak fixture")
    elif case.kind is ResearchLoopEvalKind.SCANNER_BLOCKER_ACCURACY:
        _seed_public_only_leak_loop(context, "loop.eval.scanner")
        report = scan_research_loop(context, "loop.eval.scanner")
        codes = {finding.code for finding in report.findings}
        scanner_blocker_accuracy = report.handoff_blocked and {
            "private_path_reference",
            "accepted_write_attempt",
            "provider_payload",
            "authority_claim",
        } <= codes
        if not scanner_blocker_accuracy:
            failures.append("expected scanner blockers to match unsafe fixture")
    elif case.kind is ResearchLoopEvalKind.HANDOFF_REVIEW_CONTEXT_VALIDITY:
        start_loop(context, issue_id=ISSUE_ID, loop_id="loop.eval.handoff")
        append_attempt(
            context,
            "loop.eval.handoff",
            _failed_attempt("loop.eval.handoff", 1),
        )
        report = scan_research_loop(context, "loop.eval.handoff")
        handoff_review_context_valid = (
            report.accepted_write_performed is False
            and report.report_path.startswith(".cosheaf/research-loops/")
            and report.handoff_blocked is False
        )
        if not handoff_review_context_valid:
            failures.append("expected scan report to remain review context only")
    elif case.kind is ResearchLoopEvalKind.POLICY_OVERCLAIM_REJECTION:
        start_loop(context, issue_id=ISSUE_ID, loop_id="loop.eval.overclaim")
        try:
            import_operator_result(
                context,
                "loop.eval.overclaim",
                _operator_result(claimed_authority=True),
            )
        except (ResearchLoopError, ValidationError, ValueError):
            policy_overclaim_rejected = True
        if not policy_overclaim_rejected:
            failures.append("expected authority overclaim to be rejected")
    elif case.kind is ResearchLoopEvalKind.BUDGET_STOP_ACCURACY:
        start_loop(
            context,
            issue_id=ISSUE_ID,
            loop_id="loop.eval.budget",
            budget=ResearchLoopBudget(max_attempts=1),
        )
        append_attempt(
            context,
            "loop.eval.budget",
            _failed_attempt("loop.eval.budget", 1),
        )
        dry_run = run_loop(
            context,
            "loop.eval.budget",
            max_attempts=1,
            wallclock_minutes=1,
            dry_run=True,
        )
        budget_stop_accurate = any(
            condition.kind == "max_attempts"
            and condition.triggered
            for action in dry_run.planned_actions
            for condition in action.stop_conditions
        )
        if not budget_stop_accurate:
            failures.append("expected max-attempt budget stop to be triggered")
    elif case.kind is ResearchLoopEvalKind.SKIPPED_NOT_PASS:
        skipped_status = "skipped"
        skipped_not_pass = skipped_status != "pass"
        if not skipped_not_pass:
            failures.append("expected skipped to remain distinct from pass")
    else:  # pragma: no cover - StrEnum exhaustiveness guard
        failures.append(f"unsupported research-loop eval case: {case.kind}")

    return ResearchLoopEvalCaseResult(
        id=case.id or f"case.research-loop.{case.kind.value}",
        kind=case.kind,
        passed=not failures,
        loop_valid=loop_valid,
        attempt_schema_valid=attempt_schema_valid,
        repeat_failure_detected=repeat_failure_detected,
        unjustified_retry_blocked=unjustified_retry_blocked,
        private_leak_count=private_leak_count,
        scanner_blocker_accuracy=scanner_blocker_accuracy,
        handoff_review_context_valid=handoff_review_context_valid,
        policy_overclaim_rejected=policy_overclaim_rejected,
        budget_stop_accurate=budget_stop_accurate,
        skipped_not_pass=skipped_not_pass,
        accepted_write_performed=accepted_write_performed,
        failures=failures,
    )


def _rate(
    results: list[ResearchLoopEvalCaseResult],
    kind: ResearchLoopEvalKind,
    field_name: str,
) -> float:
    selected = [result for result in results if result.kind is kind]
    if not selected:
        return 1.0
    return sum(
        1 for result in selected if bool(getattr(result, field_name))
    ) / len(selected)


def _write_eval_fixture(root: Path) -> None:
    (root / "kb" / "public" / "accepted" / "definitions").mkdir(parents=True)
    (root / "kb" / "private" / "draft" / "claims").mkdir(parents=True)
    (root / "issues" / "open").mkdir(parents=True)
    (root / "cosheaf.toml").write_text(
        "\n".join(
            [
                'name = "research-loop-eval-workspace"',
                "",
                "[[kb_roots]]",
                'name = "public"',
                'path = "kb/public"',
                "readonly = true",
                "priority = 10",
                "",
                "[[kb_roots]]",
                'name = "private"',
                'path = "kb/private"',
                "readonly = false",
                "priority = 20",
                "",
            ]
        ),
        encoding="utf-8",
    )
    public_artifact = (
        root
        / "kb"
        / "public"
        / "accepted"
        / "definitions"
        / "definition.eval.graph.yaml"
    )
    public_artifact.write_text(
        "id: definition.eval.graph\nstatus: accepted\ntype: definition\n",
        encoding="utf-8",
    )
    private_artifact = (
        root
        / "kb"
        / "private"
        / "draft"
        / "claims"
        / "claim.eval.private.yaml"
    )
    private_artifact.write_text(
        "id: claim.eval.private\nstatus: draft\ntype: claim\n",
        encoding="utf-8",
    )
    (root / "issues" / "open" / "issue.eval.research-loop.yaml").write_text(
        "id: issue.eval.research-loop\nstatus: open\n",
        encoding="utf-8",
    )


def _seed_prior_failure(context: RepoContext, loop_id: str) -> None:
    start_loop(context, issue_id=ISSUE_ID, loop_id=loop_id)
    append_attempt(context, loop_id, _failed_attempt(loop_id, 1))


def _seed_public_only_leak_loop(context: RepoContext, loop_id: str) -> None:
    start_loop(context, issue_id=ISSUE_ID, loop_id=loop_id)
    append_attempt(
        context,
        loop_id,
        _failed_attempt(loop_id, 1).model_copy(update={"policy_mode": "public_only"}),
    )
    events_path = context.repo_root / research_loop_events_path(loop_id)
    events_path.write_text(
        json.dumps(
            {
                "sequence": 999,
                "event_kind": "unsafe_eval_fixture",
                "payload": {
                    "provider_payload": {"messages": [{"content": "raw"}]},
                    "path": "kb/private/draft/claims/claim.eval.private.yaml",
                    "accepted_target": "kb/accepted/claims/claim.bad.yaml",
                    "human_reviewed": True,
                },
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _failed_attempt(loop_id: str, attempt_number: int) -> ResearchLoopAttempt:
    attempt_id = f"{loop_id}.attempt.{attempt_number}"
    started = datetime(2026, 6, 17, 1, attempt_number, tzinfo=UTC)
    return ResearchLoopAttempt(
        attempt_id=attempt_id,
        loop_id=loop_id,
        attempt_number=attempt_number,
        status=ResearchLoopAttemptStatus.FAILED,
        planned_direction="Try direct induction",
        started_at=started,
        completed_at=started,
        result_summary="Direct induction failed on the private draft fixture.",
        actions_taken=("inspect public definition",),
        failures=(
            AttemptFailureRecord(
                failure_id=f"failure.{attempt_id}",
                attempt_id=attempt_id,
                attempted_direction="Try direct induction",
                why_it_failed="The induction step needs a missing invariant.",
                evidence_for_failure=("reviews/runs/research-loop-eval.json",),
                related_artifacts=(PUBLIC_ARTIFACT_ID, PRIVATE_DRAFT_ARTIFACT_ID),
                should_retry=False,
                avoid_in_future="Do not retry direct induction without an invariant.",
                tags=(ResearchLoopFailureTag.INSUFFICIENT_EVIDENCE,),
                signature="direct-induction-missing-invariant",
            ),
        ),
        evidence=AttemptEvidenceSummary(
            related_artifacts=(PUBLIC_ARTIFACT_ID, PRIVATE_DRAFT_ARTIFACT_ID),
            draft_artifact_refs=(PRIVATE_DRAFT_ARTIFACT_ID,),
            summary="Eval fixture references public and private draft artifacts.",
        ),
    )


def _operator_result(*, claimed_authority: bool = False) -> ResearchLoopOperatorResult:
    return ResearchLoopOperatorResult.model_validate(
        {
            "attempted_direction": "Try direct induction",
            "actions_taken": ["inspect public definition"],
            "checks_run": ["cosheaf validate"],
            "result_summary": "Retrying direct induction",
            "evidence_refs": ["reviews/runs/research-loop-eval.json"],
            "artifacts_referenced": [PUBLIC_ARTIFACT_ID, PRIVATE_DRAFT_ARTIFACT_ID],
            "claimed_authority_flags": {
                "accepted": claimed_authority,
                "human_review": False,
                "verifier_pass": False,
                "gate_pass": False,
                "promotion": False,
            },
        }
    )


__all__ = [
    "DEFAULT_RESEARCH_LOOP_EVAL_CASES",
    "PRIVATE_DRAFT_ARTIFACT_ID",
    "PUBLIC_ARTIFACT_ID",
    "ResearchLoopEvalCase",
    "ResearchLoopEvalCaseResult",
    "ResearchLoopEvalError",
    "ResearchLoopEvalKind",
    "ResearchLoopEvalMetrics",
    "ResearchLoopEvalReport",
    "ResearchLoopEvalSuite",
    "load_research_loop_eval_suite",
    "resolve_research_loop_eval_case_path",
    "run_research_loop_eval_suite",
]
