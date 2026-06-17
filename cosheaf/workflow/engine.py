"""Deterministic reviewable research workflow engine.

Wires librarian, FSM, action registry, research-loop, and handoff primitives
into a single workflow record. Every step records inputs, outputs, status,
warnings, and authority notice. Workflow records are review context only.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

WORKFLOW_AUTHORITY_NOTICE = (
    "Research workflow records are review context only; they are not proof, "
    "verifier pass, gate pass, human review, accepted status, accepted "
    "refutation, or promotion authority."
)

class WorkflowStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    READY_FOR_DRAFT = "ready_for_draft"
    BLOCKED = "blocked"
    FINALIZED = "finalized"
    FAILED = "failed"

class ReadinessClass(StrEnum):
    READY = "ready_for_draft_proposal"
    BLOCKED_GATE = "blocked_by_gate"
    BLOCKED_SCANNER = "blocked_by_scanner"
    BLOCKED_EVIDENCE = "blocked_by_missing_evidence"
    BLOCKED_LEAK = "blocked_by_private_leak_risk"
    BLOCKED_COUNTEREXAMPLE = "blocked_by_unchecked_counterexample"
    INCONCLUSIVE = "inconclusive"

class WorkflowStep(BaseModel):
    step_number: int
    action: str
    status: str = "success"
    input_refs: dict[str, str] = Field(default_factory=dict)
    output_refs: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    authority_notice: str = WORKFLOW_AUTHORITY_NOTICE

class WorkflowRecord(BaseModel):
    workflow_id: str
    issue_id: str = ""
    query: str = ""
    status: WorkflowStatus = WorkflowStatus.CREATED
    steps: list[WorkflowStep] = Field(default_factory=list)
    readiness: ReadinessClass | None = None
    created_at: str = ""
    updated_at: str = ""
    authority_notice: str = WORKFLOW_AUTHORITY_NOTICE

class WorkflowReadinessReport(BaseModel):
    workflow_id: str
    classification: ReadinessClass
    blocker_details: list[str] = Field(default_factory=list)
    completed_steps: int = 0
    recommendations: list[str] = Field(default_factory=list)
    authority_notice: str = WORKFLOW_AUTHORITY_NOTICE


def start_workflow(issue_id: str, query: str = "") -> WorkflowRecord:
    now = datetime.now(UTC).isoformat()
    return WorkflowRecord(
        workflow_id=f"wf-{issue_id}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}",
        issue_id=issue_id,
        query=query,
        created_at=now,
        updated_at=now,
    )

def append_step(record: WorkflowRecord, step: WorkflowStep) -> WorkflowRecord:
    steps = list(record.steps)
    steps.append(step.model_copy(update={"step_number": len(steps) + 1}))
    return record.model_copy(
        update={
            "steps": steps,
            "status": WorkflowStatus.RUNNING,
            "updated_at": datetime.now(UTC).isoformat(),
        }
    )

def assess_readiness(record: WorkflowRecord) -> WorkflowReadinessReport:
    completed = len(record.steps)
    blockers: list[str] = []
    classification = ReadinessClass.READY

    for step in record.steps:
        if step.status in ("failed", "blocked"):
            blockers.append(f"Step {step.step_number} ({step.action}) failed")
            classification = ReadinessClass.BLOCKED_EVIDENCE
        if "accepted" in str(step.output_refs).lower():
            blockers.append(f"Step {step.step_number}: accepted-write reference detected")
            classification = ReadinessClass.BLOCKED_SCANNER
        if "private" in str(step.warnings).lower():
            classification = ReadinessClass.BLOCKED_LEAK

    if completed == 0:
        classification = ReadinessClass.INCONCLUSIVE

    return WorkflowReadinessReport(
        workflow_id=record.workflow_id,
        classification=classification,
        blocker_details=blockers,
        completed_steps=completed,
        recommendations=["Run more steps to gather evidence"] if completed < 2 else [],
    )
