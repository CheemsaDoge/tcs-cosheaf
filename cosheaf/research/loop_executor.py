"""Research-loop local execution engine using the deterministic action registry.

Integrates the v0.8.0 LocalActionRegistry with the v0.7.0 bounded research loop.
Allows bounded non-dry-run execution of whitelisted local actions only.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cosheaf.actions.builtins import build_default_registry
from cosheaf.actions.registry import (
    LocalActionPolicy,
    LocalActionRunRequest,
    LocalActionStatus,
)
from cosheaf.research.loop import (
    RESEARCH_LOOP_AUTHORITY_NOTICE,
    ResearchLoop,
    ResearchLoopAttempt,
    ResearchLoopError,
    ResearchLoopMetrics,
    ResearchLoopRunResult,
    ResearchLoopStopCondition,
    _budget_stop_conditions,
    load_attempt_memory_index,
    load_loop,
    next_loop_action,
)
from cosheaf.storage.repo import RepoContext

_EXECUTABLE_ACTION_IDS = frozenset({
    "memory.search",
    "context.build",
    "strategy.next",
    "validate.run",
    "gate.run",
    "research_loop.scan",
    "eval.research_loop",
    "operator_handoff.preview",
})


def run_local_actions_step(
    context: RepoContext,
    loop: ResearchLoop,
    *,
    dry_run: bool = False,
) -> ResearchLoopRunResult:
    """Execute one step of allowed local actions for a research loop.

    Runs a sequence of whitelisted local actions as one execution step.
    Each action result is recorded; scanner blockers or failures stop the step.
    """
    registry = build_default_registry()
    policy = LocalActionPolicy(mode=loop.mode)
    repo_root = context.repo_root
    issue_id = loop.issue_id or ""

    actions_to_run = [
        ("memory.search", {"issue_id": issue_id}),
        ("context.build", {"issue_id": issue_id}),
        ("strategy.next", {"issue_id": issue_id}),
    ]

    results: list[dict[str, Any]] = []
    for action_id, input_refs in actions_to_run:
        req = LocalActionRunRequest(
            action_id=action_id,
            input_refs=input_refs,
            dry_run=dry_run,
        )
        result = registry.run(req, policy, repo_root)
        results.append(result.model_dump(mode="json"))
        if result.status in (
            LocalActionStatus.FAILED,
            LocalActionStatus.ERROR,
            LocalActionStatus.BLOCKED,
        ):
            return ResearchLoopRunResult(
                loop_id=loop.loop_id,
                status="running",
                max_attempts=1,
                wallclock_minutes=1,
                dry_run=dry_run,
                planned_actions=[],
                writes_performed=False,
                step_results=results,
                stop_conditions=[
                    ResearchLoopStopCondition(
                        reason="action_failure",
                        kind="action_failure",
                        message=result.error.message if result.error else str(result.status),
                    )
                ],
            )

    planned = next_loop_action(loop, memory_index=load_attempt_memory_index(context))
    return ResearchLoopRunResult(
        loop_id=loop.loop_id,
        status="running",
        max_attempts=1,
        wallclock_minutes=1,
        dry_run=dry_run,
        planned_actions=planned.actions if planned else [],
        writes_performed=False,
        step_results=results,
    )
