"""Runtime storage for generated strategy plans."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from cosheaf.storage.repo import RepoContext
from cosheaf.strategy.models import (
    STRATEGY_AUTHORITY_NOTICE,
    StrategyError,
    StrategyPlan,
)

STRATEGY_RUNTIME_ROOT = Path(".cosheaf") / "strategy"


@dataclass(frozen=True)
class StrategyPlanStorageResult:
    """One loaded or written runtime strategy plan."""

    plan: StrategyPlan
    relative_path: Path
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "strategy_plan",
            "plan_id": self.plan.plan_id,
            "path": self.relative_path.as_posix(),
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": STRATEGY_AUTHORITY_NOTICE,
            "plan": self.plan.to_dict(),
        }


def write_strategy_plan(
    context: RepoContext,
    plan: StrategyPlan,
) -> StrategyPlanStorageResult:
    """Persist a generated strategy plan under runtime storage."""
    relative_path = strategy_plan_path(plan.plan_id)
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(plan.to_json(), encoding="utf-8", newline="\n")
    return StrategyPlanStorageResult(plan=plan, relative_path=relative_path)


def load_strategy_plan(
    context: RepoContext,
    plan_id: str,
) -> StrategyPlanStorageResult:
    """Load one runtime strategy plan."""
    relative_path = strategy_plan_path(plan_id)
    target = context.resolve(relative_path)
    if not target.is_file():
        raise StrategyError(
            f"strategy plan not found: {plan_id}",
            code="strategy_plan_not_found",
            remediation="Run `cosheaf strategy plan --issue <issue-id>` first.",
            details={"path": relative_path.as_posix()},
        )
    try:
        raw = json.loads(target.read_text(encoding="utf-8-sig"))
        plan = StrategyPlan.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValueError, ValidationError) as exc:
        raise StrategyError(
            f"strategy plan failed validation: {exc}",
            code="strategy_plan_validation_failed",
            remediation="Regenerate the strategy plan or repair the runtime JSON.",
            details={"path": relative_path.as_posix()},
        ) from exc
    return StrategyPlanStorageResult(plan=plan, relative_path=relative_path)


def strategy_plan_path(plan_id: str) -> Path:
    """Return runtime path for one strategy plan ID."""
    plan = StrategyPlan.model_validate(
        {
            "schema_version": 1,
            "plan_id": plan_id,
            "issue_id": plan_id.removeprefix("strategy.").removesuffix(".plan"),
            "created_at": "2026-01-01T00:00:00Z",
            "problem": {
                "issue_id": plan_id.removeprefix("strategy.").removesuffix(".plan"),
                "title": "placeholder",
            },
            "graph": {"nodes": [], "edges": []},
            "next_steps": [],
            "authority_notice": STRATEGY_AUTHORITY_NOTICE,
            "accepted_write_performed": False,
        }
    )
    return STRATEGY_RUNTIME_ROOT / plan.plan_id / "strategy.json"


def _ensure_repo_local(context: RepoContext, target: Path) -> None:
    try:
        target.resolve().relative_to(context.repo_root.resolve())
    except ValueError as exc:
        raise StrategyError(
            "strategy plan target must stay repository-local",
            code="invalid_strategy_path",
            remediation="Use the controlled .cosheaf/strategy runtime path.",
        ) from exc


__all__ = [
    "STRATEGY_RUNTIME_ROOT",
    "StrategyPlanStorageResult",
    "load_strategy_plan",
    "strategy_plan_path",
    "write_strategy_plan",
]
