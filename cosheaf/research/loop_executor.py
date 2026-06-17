"""Research-loop local execution engine using the deterministic action registry.

Integrates the v0.8.0 LocalActionRegistry with the v0.7.0 bounded research loop.
Allows bounded non-dry-run execution of whitelisted local actions only.
"""

from __future__ import annotations

from datetime import UTC, datetime

from cosheaf.actions.builtins import build_default_registry
from cosheaf.actions.registry import (
    LocalActionPolicy,
    LocalActionRunRequest,
    LocalActionStatus,
)
from cosheaf.research.loop import (
    ResearchLoop,
    ResearchLoopRunResult,
    ResearchLoopStopCondition,
    next_loop_action,
)
from cosheaf.storage.repo import RepoContext

_EXECUTABLE_ACTION_IDS = frozenset(
    {
        "memory.search",
        "context.build",
        "strategy.next",
        "validate.run",
        "gate.run",
        "research_loop.scan",
        "eval.research_loop",
        "operator_handoff.preview",
    }
)


def run_local_actions_step(
    context: RepoContext,
    loop: ResearchLoop,
    *,
    dry_run: bool = False,
) -> ResearchLoopRunResult:
    """Execute one step of allowed local actions for a research loop.

    Runs a sequence of whitelisted local actions as one execution step.
    Scanner blockers or failures stop the step.
    """
    registry = build_default_registry()
    policy = LocalActionPolicy(mode="private_research")
    repo_root = context.repo_root
    issue_id = loop.issue_id or ""

    actions_to_run = [
        ("memory.search", {"issue_id": issue_id}),
        ("context.build", {"issue_id": issue_id}),
        ("strategy.next", {"issue_id": issue_id}),
    ]

    for action_id, input_refs in actions_to_run:
        req = LocalActionRunRequest(
            action_id=action_id,
            input_refs=input_refs,
            dry_run=dry_run,
        )
        result = registry.run(req, policy, repo_root)
        if result.status in (
            LocalActionStatus.FAILED,
            LocalActionStatus.ERROR,
            LocalActionStatus.BLOCKED,
        ):
            message = result.error.message if result.error else str(result.status)
            return ResearchLoopRunResult(
                loop_id=loop.loop_id,
                mode="local",
                dry_run=dry_run,
                planned_actions=(),
                writes_performed=False,
                stop_conditions=(
                    ResearchLoopStopCondition(
                        condition_id=f"stop.{loop.loop_id}.local-action-failure",
                        kind="action_failure",
                        description=message,
                        triggered=True,
                        triggered_at=datetime.now(UTC).replace(microsecond=0),
                    ),
                ),
            )

    planned = next_loop_action(context, loop.loop_id)
    return ResearchLoopRunResult(
        loop_id=loop.loop_id,
        mode="local",
        dry_run=dry_run,
        planned_actions=(planned,),
        writes_performed=False,
    )
