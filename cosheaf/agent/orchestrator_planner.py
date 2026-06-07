"""Deterministic orchestrator planner stub.

The planner turns one issue record into an auditable task DAG. It does not
build context packs, execute workers, call hosted services, run gates, or write
accepted knowledge.
"""

from __future__ import annotations

from cosheaf.agent.orchestrator_state import Plan, TaskDAG, TaskNode
from cosheaf.agent.task import WorkerType
from cosheaf.storage.loader import IssueRecord, LoadError, load_artifacts
from cosheaf.storage.repo import RepoContext


class OrchestratorPlannerError(ValueError):
    """Raised for expected deterministic planner failures."""


def plan_for_issue(context: RepoContext, issue_id: str) -> Plan:
    """Create a deterministic local-only plan for an existing issue."""
    issue = _find_issue(context, issue_id)
    context_dir = f"context/TASKS/{issue.id}"
    librarian_node = f"node.{issue.id}.librarian-retrieval"
    reasoner_node = f"node.{issue.id}.reasoner-draft"
    verifier_node = f"node.{issue.id}.verifier-check"
    review_node = f"node.{issue.id}.review-request"

    return Plan(
        plan_id=f"plan.{issue.id}",
        issue_id=issue.id,
        objective=f"{issue.title}: {issue.description.strip()}",
        notes=(
            "Deterministic planner stub only. It references the expected "
            "context-pack location but does not build context, execute workers, "
            "call LLMs, run gates, request review, merge outputs, or promote "
            "accepted knowledge."
        ),
        task_dag=TaskDAG(
            nodes=[
                TaskNode(
                    node_id=librarian_node,
                    worker_type=WorkerType.ORCHESTRATOR,
                    description=(
                        "Prepare bounded librarian retrieval context from the "
                        "issue metadata and related artifacts."
                    ),
                    input_artifacts=list(issue.related_artifacts),
                    expected_outputs=[
                        f"{context_dir}/CONTEXT.md",
                        f"{context_dir}/RETRIEVAL_AUDIT.json",
                    ],
                ),
                TaskNode(
                    node_id=reasoner_node,
                    worker_type=WorkerType.REASONER,
                    description=(
                        "Draft a reviewable response or artifact proposal from "
                        "the planned context pack."
                    ),
                    depends_on=[librarian_node],
                    input_artifacts=list(issue.related_artifacts),
                    expected_outputs=[
                        f".cosheaf/orchestrator/{issue.id}/reasoner-draft.yaml",
                    ],
                ),
                TaskNode(
                    node_id=verifier_node,
                    worker_type=WorkerType.VERIFIER,
                    description=(
                        "Check the draft output with applicable local validation "
                        "or verifier commands before review."
                    ),
                    depends_on=[reasoner_node],
                    input_artifacts=list(issue.related_artifacts),
                    expected_outputs=[
                        f".cosheaf/orchestrator/{issue.id}/verifier-check.yaml",
                    ],
                ),
                TaskNode(
                    node_id=review_node,
                    worker_type=WorkerType.ORCHESTRATOR,
                    description=(
                        "Prepare a human review request for any draft outputs "
                        "without changing accepted knowledge."
                    ),
                    depends_on=[verifier_node],
                    input_artifacts=list(issue.related_artifacts),
                    expected_outputs=[
                        f".cosheaf/orchestrator/{issue.id}/review-request.yaml",
                    ],
                ),
            ]
        ),
    )


def _find_issue(context: RepoContext, issue_id: str) -> IssueRecord:
    try:
        records = tuple(load_artifacts(context))
    except LoadError as exc:
        raise OrchestratorPlannerError(
            f"cannot load repository records: {exc}"
        ) from exc

    issues = [
        record.record
        for record in records
        if isinstance(record.record, IssueRecord) and record.record.id == issue_id
    ]
    if not issues:
        raise OrchestratorPlannerError(f"issue not found: {issue_id}")
    return sorted(issues, key=lambda issue: issue.id)[0]
