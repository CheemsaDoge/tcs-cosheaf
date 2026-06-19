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
from cosheaf.web_actions import (
    GitHubWritePlan,
    GitWritePlan,
    PromotionPlan,
    RepoWritePlan,
    ReviewDecisionPlan,
    WebActionAuditEntry,
    WebActionConfirmRequest,
    WebActionDtoBundle,
    WebActionError,
    WebActionKind,
    WebActionMode,
    WebActionPreviewRequest,
    WebActionResult,
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
    "GitHubWritePlan",
    "GitWritePlan",
    "ReviewRequestWriteRequest",
    "ReviewRequestWriteResult",
    "PromotionPlan",
    "RepoWritePlan",
    "ReviewDecisionPlan",
    "SourceNoteWriteRequest",
    "ValidateRequest",
    "ValidateResult",
    "WebActionAuditEntry",
    "WebActionConfirmRequest",
    "WebActionDtoBundle",
    "WebActionError",
    "WebActionKind",
    "WebActionMode",
    "WebActionPreviewRequest",
    "WebActionResult",
    "WorkspaceInfoRequest",
    "WorkspaceInfoResult",
]
