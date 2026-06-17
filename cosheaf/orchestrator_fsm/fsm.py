"""Deterministic orchestrator FSM for issue-driven research workflow."""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

FSM_AUTHORITY_NOTICE = (
    "Orchestrator FSM records are workflow context only; they are not proof, "
    "verifier pass, gate pass, human review, accepted status, accepted "
    "refutation, or promotion authority."
)

class FSMState(StrEnum):
    CREATED = "created"
    PLANNED = "planned"
    READY = "ready_to_run"
    RUNNING = "running"
    BLOCKED = "blocked"
    FINALIZED = "finalized"
    ABANDONED = "abandoned"
    FAILED = "failed"

FSM_TRANSITIONS: dict[FSMState, list[FSMState]] = {
    FSMState.CREATED: [FSMState.PLANNED, FSMState.ABANDONED],
    FSMState.PLANNED: [FSMState.READY, FSMState.ABANDONED],
    FSMState.READY: [FSMState.RUNNING, FSMState.ABANDONED],
    FSMState.RUNNING: [FSMState.BLOCKED, FSMState.FINALIZED, FSMState.FAILED],
    FSMState.BLOCKED: [FSMState.READY, FSMState.ABANDONED],
    FSMState.FINALIZED: [],
    FSMState.ABANDONED: [],
    FSMState.FAILED: [FSMState.ABANDONED],
}

class OrchestratorRecord(BaseModel):
    orch_id: str
    issue_id: str = ""
    state: FSMState = FSMState.CREATED
    events: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    authority_notice: str = FSM_AUTHORITY_NOTICE


class OrchestratorDecision(BaseModel):
    next_state: FSMState | None = None
    recommendation: str = ""
    blocked_reason: str = ""
    authority_notice: str = FSM_AUTHORITY_NOTICE


def create_orchestrator(issue_id: str) -> OrchestratorRecord:
    now = datetime.now(UTC).isoformat()
    return OrchestratorRecord(
        orch_id=f"orch-{issue_id}",
        issue_id=issue_id,
        created_at=now,
        updated_at=now,
    )


def transition_state(record: OrchestratorRecord, target_state: FSMState) -> OrchestratorRecord:
    if target_state not in FSM_TRANSITIONS.get(record.state, []):
        raise ValueError(
            f"Invalid transition: {record.state.value} -> {target_state.value}. "
            f"Allowed: {[s.value for s in FSM_TRANSITIONS.get(record.state, [])]}"
        )
    now = datetime.now(UTC).isoformat()
    record.events.append({
        "from_state": record.state.value,
        "to_state": target_state.value,
        "timestamp": now,
    })
    return record.model_copy(update={"state": target_state, "updated_at": now})


def next_action(record: OrchestratorRecord) -> OrchestratorDecision:
    current = record.state
    if current == FSMState.CREATED:
        return OrchestratorDecision(next_state=FSMState.PLANNED, recommendation="Plan the task graph")
    if current == FSMState.PLANNED:
        return OrchestratorDecision(next_state=FSMState.READY, recommendation="Mark task graph ready")
    if current == FSMState.READY:
        return OrchestratorDecision(next_state=FSMState.RUNNING, recommendation="Start local execution")
    if current == FSMState.RUNNING:
        return OrchestratorDecision(next_state=FSMState.FINALIZED, recommendation="Finalize the run")
    if current == FSMState.BLOCKED:
        return OrchestratorDecision(next_state=FSMState.READY, recommendation="Unblock and retry")
    if current == FSMState.FINALIZED:
        return OrchestratorDecision(recommendation="Orchestrator is finalized, no further actions")
    if current == FSMState.FAILED:
        return OrchestratorDecision(next_state=FSMState.ABANDONED, recommendation="Orchestrator failed, consider abandoning")
    return OrchestratorDecision(recommendation="No action available")
