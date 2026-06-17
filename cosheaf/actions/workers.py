"""Deterministic worker profiles that bundle allowed local actions."""
from __future__ import annotations

from cosheaf.actions.builtins import build_default_registry
from cosheaf.actions.registry import (
    LOCAL_ACTION_AUTHORITY_NOTICE,
    LocalActionPolicy,
    LocalActionRunRequest,
    LocalActionResult,
    LocalActionStatus,
)

_WORKER_PROFILES: dict[str, list[str]] = {
    "librarian_local": ["memory.search", "context.build", "index.rebuild"],
    "planner_local": ["strategy.next", "context.build", "failure_memory.summary"],
    "checker_local": [
        "validate.run",
        "gate.run",
        "checked_evidence.summary",
        "eval.research_loop",
    ],
    "handoff_local": [
        "research_loop.scan",
        "operator_session.scan",
        "operator_handoff.preview",
    ],
}

def list_worker_profiles() -> list[dict]:
    return [
        {"worker_id": pid, "allowed_actions": actions}
        for pid, actions in sorted(_WORKER_PROFILES.items())
    ]

def get_worker_profile(worker_id: str) -> dict | None:
    actions = _WORKER_PROFILES.get(worker_id)
    if actions is None:
        return None
    return {"worker_id": worker_id, "allowed_actions": actions}

def run_worker(
    worker_id: str,
    input_refs: dict[str, str],
    repo_root: str,
    *,
    dry_run: bool = False,
    mode: str = "private_research",
) -> list[LocalActionResult]:
    """Run all actions in a worker profile."""
    profile = _WORKER_PROFILES.get(worker_id)
    if profile is None:
        return [
            LocalActionResult(
                action_id=worker_id,
                status=LocalActionStatus.ERROR,
                error={"error_code": "UNKNOWN_WORKER", "message": f"Worker {worker_id!r} not found"},
            )
        ]

    registry = build_default_registry()
    policy = LocalActionPolicy(mode=mode)  # type: ignore[arg-type]
    from pathlib import Path
    repo = Path(repo_root)

    results: list[LocalActionResult] = []
    for action_id in profile:
        req = LocalActionRunRequest(action_id=action_id, input_refs=input_refs, dry_run=dry_run)
        result = registry.run(req, policy, repo)
        results.append(result)

    return results
