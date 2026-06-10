"""Machine-readable role prompt and context contracts."""

from __future__ import annotations

from cosheaf.agent.roles.contracts import (
    REQUIRED_ROLE_NAMES,
    ROLE_CONTRACTS,
    RoleContextBudget,
    RoleContextPolicy,
    RoleContract,
    RoleName,
    RoleOutputSchema,
    RoleProviderCapabilityRequirements,
    RoleToolPolicy,
    get_role_contract,
    list_role_contracts,
)

__all__ = [
    "REQUIRED_ROLE_NAMES",
    "ROLE_CONTRACTS",
    "RoleContextBudget",
    "RoleContextPolicy",
    "RoleContract",
    "RoleName",
    "RoleOutputSchema",
    "RoleProviderCapabilityRequirements",
    "RoleToolPolicy",
    "get_role_contract",
    "list_role_contracts",
]
