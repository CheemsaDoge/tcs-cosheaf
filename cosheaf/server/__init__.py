"""Read-only local server surface for website preview."""

from cosheaf.server.api import (
    READONLY_SERVER_HOST,
    READONLY_SERVER_PORT,
    ApiResponse,
    ReadOnlySiteApi,
    make_handler,
    serve_readonly_api,
)
from cosheaf.server.auth import (
    HostedAuthProvider,
    HostedIdentity,
    HostedRole,
    hosted_action_allowed,
    hosted_required_role,
)

__all__ = [
    "READONLY_SERVER_HOST",
    "READONLY_SERVER_PORT",
    "ApiResponse",
    "HostedAuthProvider",
    "HostedIdentity",
    "HostedRole",
    "ReadOnlySiteApi",
    "hosted_action_allowed",
    "hosted_required_role",
    "make_handler",
    "serve_readonly_api",
]
