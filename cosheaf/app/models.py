"""App-level request/result DTOs.

This module reuses the existing agent-access DTO base so app, CLI adapters,
MCP adapters, and future server code share one deterministic JSON shape.
"""

from __future__ import annotations

from cosheaf.services.models import (
    AgentAccessModel,
    AgentAccessStatus,
    ContextBuildRequest,
    ContextBuildResult,
    DraftWriteRequest,
    DraftWriteResult,
    ErrorResult,
    GateRunRequest,
    GateRunResult,
    ReviewRequestWriteRequest,
    ReviewRequestWriteResult,
    SourceNoteWriteRequest,
    ValidateRequest,
    ValidateResult,
    WorkspaceInfoRequest,
    WorkspaceInfoResult,
)

__all__ = [
    "AgentAccessModel",
    "AgentAccessStatus",
    "ContextBuildRequest",
    "ContextBuildResult",
    "DraftWriteRequest",
    "DraftWriteResult",
    "ErrorResult",
    "GateRunRequest",
    "GateRunResult",
    "ReviewRequestWriteRequest",
    "ReviewRequestWriteResult",
    "SourceNoteWriteRequest",
    "ValidateRequest",
    "ValidateResult",
    "WorkspaceInfoRequest",
    "WorkspaceInfoResult",
]
