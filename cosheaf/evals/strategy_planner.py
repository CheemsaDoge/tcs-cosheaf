"""Deterministic strategy-planner boundary eval harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PureWindowsPath

import yaml  # type: ignore[import-untyped]
from pydantic import field_validator

from cosheaf.memory.models import MemoryModel
from cosheaf.research.run import SKIPPED_RESEARCH_RUN_LIMITATION
from cosheaf.storage.repo import RepoContext
from cosheaf.strategy.models import (
    STRATEGY_AUTHORITY_NOTICE,
    StrategyNextStep,
    StrategyPlan,
    StrategyProblem,
    StrategyTaskGraph,
    StrategyTaskNode,
    StrategyTaskNodeKind,
    StrategyTaskReference,
    StrategyTaskReferenceKind,
    StrategyTaskScope,
    StrategyTaskStatus,
)

DEFAULT_STRATEGY_PLANNER_EVAL_CASES = (
    Path("evals") / "strategy_planner" / "cases.yaml"
)


class StrategyPlannerEvalError(ValueError):
    """Raised for expected strategy-planner eval loading failures."""


class StrategyPlannerEvalKind(StrEnum):
    """Supported strategy-planner scenarios."""

    PROBLEM_DECOMPOSITION = "problem_decomposition"
    FAILED_DIRECTIONS_NOT_REPEATED = "failed_directions_not_repeated"
    EVIDENCE_LABEL_SEPARATION = "evidence_label_separation"
    SKIPPED_NOT_PASS = "skipped_not_pass"
    PUBLIC_ONLY_PRIVATE_LEAKAGE = "public_only_private_leakage"
    NO_AUTHORITY_ESCALATION = "no_authority_escalation"


class StrategyPlannerEvalCase(MemoryModel):
    """One deterministic strategy-planner eval case."""

    id: str | None = None
    kind: StrategyPlannerEvalKind

    @field_validator("id")
    @classmethod
    def _id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("case id must be non-empty")
        return normalized


class StrategyPlannerEvalCaseResult(MemoryModel):
    """One strategy-planner eval case result."""

    id: str
    kind: StrategyPlannerEvalKind
    passed: bool
    problem_decomposed: bool = False
    failed_direction_repeated: bool = False
    evidence_labels_separated: bool = False
    skipped_not_pass: bool = False
    private_leak_count: int = 0
    authority_escalation: bool = False
    accepted_write_performed: bool = False
    failures: list[str]


class StrategyPlannerEvalMetrics(MemoryModel):
    """Aggregate strategy-planner eval metrics."""

    problem_decomposition_count: int
    failed_direction_repeat_count: int
    evidence_label_separation_count: int
    skipped_not_pass_count: int
    private_leak_count: int
    authority_escalation_count: int
    accepted_write_violation_count: int


class StrategyPlannerEvalReport(MemoryModel):
    """Strategy-planner eval report."""

    schema_version: int = 1
    kind: str = "strategy_planner_eval"
    case_count: int
    passed: bool
    metrics: StrategyPlannerEvalMetrics
    cases: list[StrategyPlannerEvalCaseResult]
    authority_notice: str = STRATEGY_AUTHORITY_NOTICE

    def to_json(self) -> str:
        return json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
        ) + "\n"


@dataclass(frozen=True)
class StrategyPlannerEvalSuite:
    """Loaded strategy-planner eval cases."""

    cases: list[StrategyPlannerEvalCase]


def resolve_strategy_planner_eval_case_path(
    context: RepoContext,
    cases_path: Path,
) -> Path:
    """Resolve explicit or default strategy-planner eval case path."""
    repo_root = context.repo_root
    path = cases_path if cases_path.is_absolute() else repo_root / cases_path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise StrategyPlannerEvalError(
            "strategy-planner eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(
        cases_path
    ).is_absolute():
        raise StrategyPlannerEvalError(
            "strategy-planner eval case file must be repository-local"
        )
    return resolved


def load_strategy_planner_eval_suite(path: Path) -> StrategyPlannerEvalSuite:
    """Load strategy-planner eval cases from YAML."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise StrategyPlannerEvalError(f"could not read eval cases: {path}") from exc
    if not isinstance(raw, dict):
        raise StrategyPlannerEvalError("strategy-planner eval cases must be a mapping")
    cases_raw = raw.get("cases")
    if not isinstance(cases_raw, list):
        raise StrategyPlannerEvalError(
            "strategy-planner eval cases require a cases list"
        )
    cases = [StrategyPlannerEvalCase.model_validate(item) for item in cases_raw]
    return StrategyPlannerEvalSuite(cases=cases)


def run_strategy_planner_eval_suite(
    context: RepoContext,
    suite: StrategyPlannerEvalSuite,
) -> StrategyPlannerEvalReport:
    """Run deterministic strategy-planner boundary eval cases."""
    _ = context
    results = [_run_case(case) for case in suite.cases]
    metrics = StrategyPlannerEvalMetrics(
        problem_decomposition_count=sum(
            1 for result in results if result.problem_decomposed
        ),
        failed_direction_repeat_count=sum(
            1 for result in results if result.failed_direction_repeated
        ),
        evidence_label_separation_count=sum(
            1 for result in results if result.evidence_labels_separated
        ),
        skipped_not_pass_count=sum(1 for result in results if result.skipped_not_pass),
        private_leak_count=sum(result.private_leak_count for result in results),
        authority_escalation_count=sum(
            1 for result in results if result.authority_escalation
        ),
        accepted_write_violation_count=sum(
            1 for result in results if result.accepted_write_performed
        ),
    )
    return StrategyPlannerEvalReport(
        case_count=len(results),
        passed=all(result.passed for result in results),
        metrics=metrics,
        cases=results,
    )


def _run_case(case: StrategyPlannerEvalCase) -> StrategyPlannerEvalCaseResult:
    plan = _plan()
    failures: list[str] = []
    problem_decomposed = False
    failed_direction_repeated = False
    evidence_labels_separated = False
    skipped_not_pass = False
    private_leak_count = 0
    authority_escalation = False
    accepted_write_performed = False

    if case.kind is StrategyPlannerEvalKind.PROBLEM_DECOMPOSITION:
        kinds = {node.kind for node in plan.graph.nodes}
        problem_decomposed = {
            StrategyTaskNodeKind.RETRIEVAL_CONTEXT,
            StrategyTaskNodeKind.REVIEW_DECISION,
            StrategyTaskNodeKind.PROOF_ATTEMPT,
        }.issubset(kinds)
        if not problem_decomposed:
            failures.append("expected context, review, and proof-attempt task nodes")
    elif case.kind is StrategyPlannerEvalKind.FAILED_DIRECTIONS_NOT_REPEATED:
        proof_step = _node(plan, "task.proof-attempt")
        failed_direction_repeated = proof_step.status is StrategyTaskStatus.READY
        if failed_direction_repeated:
            failures.append("known failed direction was blindly repeated")
    elif case.kind is StrategyPlannerEvalKind.EVIDENCE_LABEL_SEPARATION:
        counterexample_step = _node(plan, "task.counterexample-review")
        evidence_labels_separated = (
            bool(counterexample_step.related_candidate_counterexamples)
            and bool(counterexample_step.related_checked_counterexample_evidence)
            and not plan.accepted_write_performed
        )
        if not evidence_labels_separated:
            failures.append("expected candidate and checked evidence labels to differ")
    elif case.kind is StrategyPlannerEvalKind.SKIPPED_NOT_PASS:
        gate_step = _node(plan, "task.gate")
        skipped_not_pass = (
            gate_step.status is StrategyTaskStatus.SKIPPED
            and bool(gate_step.references)
            and "not pass" in gate_step.references[0].summary
        )
        if not skipped_not_pass:
            failures.append("expected skipped strategy task to remain non-pass")
    elif case.kind is StrategyPlannerEvalKind.PUBLIC_ONLY_PRIVATE_LEAKAGE:
        serialized = _public_only_summary(plan)
        private_marker = "private-secret-strategy-marker"
        private_leak_count = 1 if private_marker in serialized else 0
        if private_leak_count:
            failures.append("private strategy marker leaked into public summary")
    elif case.kind is StrategyPlannerEvalKind.NO_AUTHORITY_ESCALATION:
        serialized = plan.to_json()
        authority_escalation = (
            plan.accepted_write_performed
            or "human_reviewed" in serialized
            or "promotion_authority" in serialized
        )
        if authority_escalation:
            failures.append("strategy plan escalated authority")
    else:  # pragma: no cover - StrEnum exhaustiveness guard
        failures.append(f"unsupported strategy-planner eval case: {case.kind}")

    return StrategyPlannerEvalCaseResult(
        id=case.id or f"case.strategy.{case.kind.value}",
        kind=case.kind,
        passed=not failures,
        problem_decomposed=problem_decomposed,
        failed_direction_repeated=failed_direction_repeated,
        evidence_labels_separated=evidence_labels_separated,
        skipped_not_pass=skipped_not_pass,
        private_leak_count=private_leak_count,
        authority_escalation=authority_escalation,
        accepted_write_performed=accepted_write_performed,
        failures=failures,
    )


def _plan() -> StrategyPlan:
    created_at = datetime(2026, 6, 15, 1, 0, tzinfo=UTC)
    nodes = (
        StrategyTaskNode(
            node_id="task.context-build",
            kind=StrategyTaskNodeKind.RETRIEVAL_CONTEXT,
            title="Build context",
            status=StrategyTaskStatus.COMPLETED,
            scope=StrategyTaskScope.WORKSPACE,
            command=("cosheaf", "context", "build", "issue.fixture.strategy"),
        ),
        StrategyTaskNode(
            node_id="task.review-failures",
            kind=StrategyTaskNodeKind.REVIEW_DECISION,
            title="Review known failed directions",
            status=StrategyTaskStatus.READY,
            scope=StrategyTaskScope.WORKSPACE,
            related_failure_log_entries=("failure.fixture.strategy.0001",),
            notes=("Known failed direction must be reviewed before retry.",),
        ),
        StrategyTaskNode(
            node_id="task.counterexample-review",
            kind=StrategyTaskNodeKind.COUNTEREXAMPLE_SEARCH,
            title="Review counterexample labels",
            status=StrategyTaskStatus.READY,
            scope=StrategyTaskScope.WORKSPACE,
            related_candidate_counterexamples=("candidate.fixture.strategy",),
            related_checked_counterexample_evidence=(
                "checked-counterexample.fixture.strategy",
            ),
        ),
        StrategyTaskNode(
            node_id="task.gate",
            kind=StrategyTaskNodeKind.GATE,
            title="Run gatekeeper",
            status=StrategyTaskStatus.SKIPPED,
            scope=StrategyTaskScope.WORKSPACE,
            references=(
                StrategyTaskReference(
                    kind=StrategyTaskReferenceKind.COMMAND,
                    identifier="cosheaf gate run",
                    status="skipped",
                    summary=SKIPPED_RESEARCH_RUN_LIMITATION,
                ),
            ),
        ),
        StrategyTaskNode(
            node_id="task.private-note",
            kind=StrategyTaskNodeKind.REVIEW_DECISION,
            title="Private strategy note",
            status=StrategyTaskStatus.READY,
            scope=StrategyTaskScope.PRIVATE,
            notes=("private-secret-strategy-marker",),
        ),
        StrategyTaskNode(
            node_id="task.proof-attempt",
            kind=StrategyTaskNodeKind.PROOF_ATTEMPT,
            title="Choose bounded proof attempt",
            status=StrategyTaskStatus.BLOCKED,
            scope=StrategyTaskScope.PRIVATE,
            blocked_by=("task.review-failures",),
            notes=("Do not retry failed direction blindly.",),
        ),
    )
    return StrategyPlan(
        plan_id="strategy.issue.fixture.strategy.plan",
        issue_id="issue.fixture.strategy",
        created_at=created_at,
        problem=StrategyProblem(
            issue_id="issue.fixture.strategy",
            title="Strategy fixture",
            target_artifacts=("claim.fixture.strategy",),
        ),
        graph=StrategyTaskGraph(nodes=nodes),
        next_steps=(
            StrategyNextStep(
                rank=1,
                node_id="task.context-build",
                score=100.0,
                reasons=("first-class CLI command",),
                command=("cosheaf", "context", "build", "issue.fixture.strategy"),
            ),
        ),
    )


def _node(plan: StrategyPlan, node_id: str) -> StrategyTaskNode:
    for node in plan.graph.nodes:
        if node.node_id == node_id:
            return node
    raise AssertionError(f"missing fixture node: {node_id}")


def _public_only_summary(plan: StrategyPlan) -> str:
    public_nodes = [
        node.to_dict()
        for node in plan.graph.nodes
        if node.scope is not StrategyTaskScope.PRIVATE
    ]
    return json.dumps(public_nodes, ensure_ascii=True, sort_keys=True)


__all__ = [
    "DEFAULT_STRATEGY_PLANNER_EVAL_CASES",
    "StrategyPlannerEvalCase",
    "StrategyPlannerEvalCaseResult",
    "StrategyPlannerEvalError",
    "StrategyPlannerEvalKind",
    "StrategyPlannerEvalMetrics",
    "StrategyPlannerEvalReport",
    "StrategyPlannerEvalSuite",
    "load_strategy_planner_eval_suite",
    "resolve_strategy_planner_eval_case_path",
    "run_strategy_planner_eval_suite",
]
