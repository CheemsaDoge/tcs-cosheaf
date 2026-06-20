"""Hosted Workbench auth stubs.

This module defines the hosted authorization contract only. It does not
implement OAuth, sessions, token parsing, or production GitHub auth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from cosheaf.web_actions import WebActionKind


class HostedRole(StrEnum):
    """Roles recognized by hosted Workbench authorization guards."""

    READER = "reader"
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    MAINTAINER = "maintainer"
    ADMIN = "admin"


@dataclass(frozen=True)
class HostedIdentity:
    """Authenticated hosted identity returned by a hosted auth provider."""

    subject: str
    roles: frozenset[HostedRole] = field(
        default_factory=lambda: frozenset({HostedRole.READER})
    )

    def __post_init__(self) -> None:
        subject = self.subject.strip()
        if not subject:
            raise ValueError("hosted identity subject must be non-empty")
        roles = frozenset(HostedRole(role) for role in self.roles)
        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "roles", roles)


class HostedAuthProvider(Protocol):
    """Minimal provider interface for future hosted request authentication."""

    def current_identity(self) -> HostedIdentity | None:
        """Return the authenticated identity for the current request."""


_REQUIRED_ROLE_BY_ACTION: dict[WebActionKind, HostedRole] = {
    WebActionKind.READ_WORKSPACE: HostedRole.READER,
    WebActionKind.AUDIT_READ: HostedRole.READER,
    WebActionKind.ISSUE_CREATE: HostedRole.CONTRIBUTOR,
    WebActionKind.ISSUE_UPDATE: HostedRole.CONTRIBUTOR,
    WebActionKind.ISSUE_CLOSE: HostedRole.CONTRIBUTOR,
    WebActionKind.ISSUE_PUBLISH_GITHUB: HostedRole.CONTRIBUTOR,
    WebActionKind.ARTIFACT_CREATE: HostedRole.CONTRIBUTOR,
    WebActionKind.ARTIFACT_UPDATE: HostedRole.CONTRIBUTOR,
    WebActionKind.SOURCE_ATTACH: HostedRole.CONTRIBUTOR,
    WebActionKind.EVIDENCE_ATTACH: HostedRole.CONTRIBUTOR,
    WebActionKind.CONTEXT_BUILD: HostedRole.CONTRIBUTOR,
    WebActionKind.VALIDATE_RUN: HostedRole.CONTRIBUTOR,
    WebActionKind.GATE_RUN: HostedRole.CONTRIBUTOR,
    WebActionKind.REVIEW_PACKET_CREATE: HostedRole.CONTRIBUTOR,
    WebActionKind.REVIEW_DECISION_CREATE: HostedRole.REVIEWER,
    WebActionKind.PROMOTION_PREVIEW: HostedRole.MAINTAINER,
    WebActionKind.PROMOTION_CONFIRM: HostedRole.MAINTAINER,
    WebActionKind.FORGE_BRANCH_CREATE: HostedRole.MAINTAINER,
    WebActionKind.FORGE_COMMIT_CREATE: HostedRole.MAINTAINER,
    WebActionKind.FORGE_PUSH_CREATE: HostedRole.MAINTAINER,
    WebActionKind.FORGE_PR_CREATE: HostedRole.MAINTAINER,
}


def hosted_required_role(action: WebActionKind) -> HostedRole:
    """Return the minimum hosted role required for a web action."""

    return _REQUIRED_ROLE_BY_ACTION[action]


def hosted_action_allowed(
    identity: HostedIdentity | None,
    action: WebActionKind,
) -> bool:
    """Return whether a hosted identity may perform a web action."""

    if identity is None:
        return False
    if HostedRole.ADMIN in identity.roles:
        return True
    required = hosted_required_role(action)
    if required is HostedRole.READER:
        return bool(identity.roles)
    return required in identity.roles


__all__ = [
    "HostedAuthProvider",
    "HostedIdentity",
    "HostedRole",
    "hosted_action_allowed",
    "hosted_required_role",
]
