"""Typed DTOs for future web-originated actions."""

from cosheaf.web_actions.audit import WEB_ACTION_AUDIT_PATH, append_web_action_audit
from cosheaf.web_actions.models import (
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
    "WEB_ACTION_AUDIT_PATH",
    "GitHubWritePlan",
    "GitWritePlan",
    "PromotionPlan",
    "RepoWritePlan",
    "ReviewDecisionPlan",
    "WebActionAuditEntry",
    "WebActionConfirmRequest",
    "WebActionDtoBundle",
    "WebActionError",
    "WebActionKind",
    "WebActionMode",
    "WebActionPreviewRequest",
    "WebActionResult",
    "append_web_action_audit",
]
