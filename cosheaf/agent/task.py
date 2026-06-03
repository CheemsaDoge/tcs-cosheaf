"""Agent task public interface.

The concrete task record models live in ``cosheaf.core.task`` so lower storage
layers can validate task examples without importing the higher agent layer.
This module preserves the public agent-harness import path.
"""

from __future__ import annotations

from cosheaf.core.task import (
    DEFAULT_EXPECTED_OUTPUTS,
    AgentTask,
    BudgetValue,
    TaskStatus,
    WorkerType,
    create_task_id,
)

__all__ = [
    "DEFAULT_EXPECTED_OUTPUTS",
    "AgentTask",
    "BudgetValue",
    "TaskStatus",
    "WorkerType",
    "create_task_id",
]
