"""Role prompt and context contracts for local agent workers.

These contracts are machine-readable policy data. They do not call hosted
model providers, run tools, write files, request review, or promote knowledge.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cosheaf.agent.model_provider import NetworkPolicy, ProviderName, ToolPolicy


class RoleName(StrEnum):
    """Role names used by prompt/context contracts."""

    LIBRARIAN = "librarian"
    REASONER = "reasoner"
    VERIFIER = "verifier"
    FORMALIZER = "formalizer"
    EXPLORER = "explorer"
    COUNTEREXAMPLER = "counterexampleer"
    COLLECTOR = "collector"


REQUIRED_ROLE_NAMES = tuple(role.value for role in RoleName)

COMMON_FORBIDDEN_ACTIONS = (
    "write_accepted_knowledge",
    "promote_artifacts",
    "mark_human_reviewed",
    "claim_machine_verification_without_checker",
    "modify_public_kb",
    "hide_gate_or_verifier_failures",
)


class RoleContractModel(BaseModel):
    """Shared strict base for role-contract DTOs."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic machine-readable mapping."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON for this model."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class RoleOutputSchema(RoleContractModel):
    """Expected worker output shape for one role."""

    schema_name: str
    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)

    @field_validator("schema_name")
    @classmethod
    def _validate_schema_name(cls, value: str) -> str:
        return _validate_slug(value, field_name="schema_name")

    @field_validator("required_fields", "optional_fields")
    @classmethod
    def _normalize_fields(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            _validate_slug(value, field_name="output field") for value in values
        )

    @model_validator(mode="after")
    def _reject_overlap(self) -> RoleOutputSchema:
        overlap = set(self.required_fields).intersection(self.optional_fields)
        if overlap:
            raise ValueError(
                "output fields cannot be both required and optional: "
                + ", ".join(sorted(overlap))
            )
        return self


class RoleContextBudget(RoleContractModel):
    """Bounded context budget for one role."""

    max_cards: int
    max_full_artifacts: int
    max_prompt_chars: int
    allow_private_context: bool = True
    notes: str = ""

    @field_validator("max_cards", "max_prompt_chars")
    @classmethod
    def _validate_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("role context budget values must be positive")
        return value

    @field_validator("max_full_artifacts")
    @classmethod
    def _validate_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("max_full_artifacts must be non-negative")
        return value

    @field_validator("notes")
    @classmethod
    def _strip_notes(cls, value: str) -> str:
        return value.strip()


class RoleToolPolicy(RoleContractModel):
    """Tool and network policy for one role contract."""

    tool_policy: ToolPolicy
    network_policy: NetworkPolicy = NetworkPolicy.DISABLED
    allowed_tools: list[str] = Field(default_factory=list)
    notes: str = ""

    @field_validator("allowed_tools")
    @classmethod
    def _normalize_allowed_tools(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            _validate_slug(value, field_name="allowed tool") for value in values
        )

    @field_validator("notes")
    @classmethod
    def _strip_notes(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def _validate_network_disabled(self) -> RoleToolPolicy:
        if self.network_policy is not NetworkPolicy.DISABLED:
            raise ValueError("role contracts must not enable network access")
        return self


class RoleContract(RoleContractModel):
    """Machine-readable prompt, context, output, and boundary contract."""

    role: RoleName
    display_name: str
    purpose: str
    system_prompt: str
    allowed_inputs: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    required_output_schema: RoleOutputSchema
    context_budget: RoleContextBudget
    tool_policy: RoleToolPolicy
    stop_conditions: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    provider: ProviderName = ProviderName.FAKE
    hosted_llm_enabled: bool = False

    @field_validator("display_name", "purpose", "system_prompt")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        return _validate_non_empty_text(value)

    @field_validator(
        "allowed_inputs",
        "forbidden_actions",
        "stop_conditions",
        "risk_flags",
    )
    @classmethod
    def _normalize_text_list(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            _validate_slug(value, field_name="role contract list value")
            for value in values
        )

    @model_validator(mode="after")
    def _validate_safety_boundary(self) -> RoleContract:
        missing_forbidden = set(COMMON_FORBIDDEN_ACTIONS).difference(
            self.forbidden_actions
        )
        if missing_forbidden:
            raise ValueError(
                "role contract missing common forbidden actions: "
                + ", ".join(sorted(missing_forbidden))
            )
        if self.provider is not ProviderName.FAKE:
            raise ValueError("role contracts must use the fake provider by default")
        if self.hosted_llm_enabled:
            raise ValueError("role contracts must not enable hosted LLM execution")
        if self.tool_policy.network_policy is not NetworkPolicy.DISABLED:
            raise ValueError("role contracts must keep network access disabled")
        role_text = self.role.value.replace("_", " ")
        if role_text not in self.system_prompt:
            raise ValueError(f"system_prompt must name role {role_text!r}")
        return self


def list_role_contracts() -> tuple[RoleContract, ...]:
    """Return role contracts in deterministic required-role order."""
    return ROLE_CONTRACTS


def get_role_contract(role: RoleName | str) -> RoleContract:
    """Return one role contract by enum value or string name."""
    role_name = RoleName(role)
    return ROLE_CONTRACT_BY_NAME[role_name]


def _contract(
    *,
    role: RoleName,
    display_name: str,
    purpose: str,
    system_prompt: str,
    allowed_inputs: Iterable[str],
    output_required: Iterable[str],
    output_optional: Iterable[str],
    context_budget: RoleContextBudget,
    tool_policy: RoleToolPolicy,
    stop_conditions: Iterable[str],
    risk_flags: Iterable[str],
    forbidden_actions: Iterable[str] = (),
) -> RoleContract:
    return RoleContract(
        role=role,
        display_name=display_name,
        purpose=purpose,
        system_prompt=system_prompt,
        allowed_inputs=list(allowed_inputs),
        forbidden_actions=[
            *COMMON_FORBIDDEN_ACTIONS,
            *list(forbidden_actions),
        ],
        required_output_schema=RoleOutputSchema(
            schema_name=f"{role.value}_worker_output",
            required_fields=list(output_required),
            optional_fields=list(output_optional),
        ),
        context_budget=context_budget,
        tool_policy=tool_policy,
        stop_conditions=list(stop_conditions),
        risk_flags=list(risk_flags),
    )


def _validate_non_empty_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("text values must be non-empty")
    return normalized


def _validate_slug(value: str, *, field_name: str) -> str:
    normalized = _validate_non_empty_text(value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
    if any(character not in allowed for character in normalized):
        raise ValueError(f"{field_name} must be a lowercase slug")
    return normalized


def _dedupe_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


CARD_ONLY_BUDGET = RoleContextBudget(
    max_cards=20,
    max_full_artifacts=0,
    max_prompt_chars=12000,
    notes="Default cards-only context; full artifacts require explicit budget.",
)
SOURCE_REVIEW_BUDGET = RoleContextBudget(
    max_cards=24,
    max_full_artifacts=2,
    max_prompt_chars=16000,
    notes="Small source-review budget for inspecting cited local context.",
)
VERIFIER_BUDGET = RoleContextBudget(
    max_cards=16,
    max_full_artifacts=1,
    max_prompt_chars=12000,
    notes="Verifier context remains bounded and must not imply a pass result.",
)
EXPLORATION_BUDGET = RoleContextBudget(
    max_cards=28,
    max_full_artifacts=1,
    max_prompt_chars=18000,
    notes="Exploration may inspect more cards but still avoids bulk context.",
)

READ_ONLY_TOOLS = RoleToolPolicy(
    tool_policy=ToolPolicy.READ_ONLY,
    allowed_tools=["context_pack", "artifact_index_query", "memory_search"],
    notes="Read-only repository inspection only.",
)
NO_TOOLS = RoleToolPolicy(
    tool_policy=ToolPolicy.NONE,
    notes="No tools; reason only from supplied context.",
)
LOCAL_ANALYSIS_TOOLS = RoleToolPolicy(
    tool_policy=ToolPolicy.LOCAL_TOOLS,
    allowed_tools=["local_python", "artifact_index_query"],
    notes="Repository-local deterministic analysis only; no accepted writes.",
)
VERIFIER_TOOLS = RoleToolPolicy(
    tool_policy=ToolPolicy.VERIFIER_TOOLS,
    allowed_tools=["validate", "gate", "optional_verifier_adapters"],
    notes="Verifier tools may report pass/fail/error/skipped; skipped is not pass.",
)

ROLE_CONTRACTS = (
    _contract(
        role=RoleName.LIBRARIAN,
        display_name="Librarian",
        purpose="Retrieve and rank existing repository context for an issue.",
        system_prompt=(
            "You are the librarian role. Retrieve bounded existing context, "
            "label draft and private material clearly, and report retrieval "
            "uncertainty without creating new claims."
        ),
        allowed_inputs=["issue_record", "artifact_cards", "retrieval_audit"],
        output_required=[
            "summary",
            "selected_artifacts",
            "retrieval_audit",
            "risk_flags",
        ],
        output_optional=["excluded_artifacts", "next_steps"],
        context_budget=CARD_ONLY_BUDGET,
        tool_policy=READ_ONLY_TOOLS,
        stop_conditions=["missing_issue", "context_budget_exhausted"],
        risk_flags=["draft_context_present", "private_context_present"],
        forbidden_actions=["create_claims", "rewrite_artifacts"],
    ),
    _contract(
        role=RoleName.REASONER,
        display_name="Reasoner",
        purpose="Draft candidate reasoning for human review from supplied context.",
        system_prompt=(
            "You are the reasoner role. Propose candidate arguments from the "
            "provided context only, keep uncertainty visible, and never present "
            "draft reasoning as accepted knowledge."
        ),
        allowed_inputs=["issue_context", "artifact_cards", "draft_notes"],
        output_required=[
            "summary",
            "candidate_claims",
            "assumptions",
            "risk_flags",
        ],
        output_optional=["proof_sketches", "open_questions", "next_steps"],
        context_budget=CARD_ONLY_BUDGET,
        tool_policy=NO_TOOLS,
        stop_conditions=["insufficient_context", "contradiction_found"],
        risk_flags=["unverified_reasoning", "needs_human_review"],
        forbidden_actions=["claim_source_review", "claim_machine_verification"],
    ),
    _contract(
        role=RoleName.VERIFIER,
        display_name="Verifier",
        purpose="Check proposed outputs against explicit local evidence and gates.",
        system_prompt=(
            "You are the verifier role. Check explicit evidence, validation, "
            "gate, and verifier results; distinguish pass, fail, error, and "
            "skipped without upgrading skipped results."
        ),
        allowed_inputs=["proposed_output", "evidence_metadata", "gate_reports"],
        output_required=[
            "summary",
            "verification_requests",
            "failures_or_counterexamples",
            "risk_flags",
        ],
        output_optional=["commands_to_run", "evidence_gaps", "next_steps"],
        context_budget=VERIFIER_BUDGET,
        tool_policy=VERIFIER_TOOLS,
        stop_conditions=[
            "gate_failed",
            "verifier_error",
            "optional_tool_skipped",
        ],
        risk_flags=["skipped_is_not_pass", "not_machine_checked"],
        forbidden_actions=["weaken_tests", "hide_skipped_results"],
    ),
    _contract(
        role=RoleName.FORMALIZER,
        display_name="Formalizer",
        purpose="Map informal statements to formal-link metadata for review.",
        system_prompt=(
            "You are the formalizer role. Propose formal-link metadata and "
            "alignment questions only; do not claim Lean, CSLib, or mathlib "
            "verification unless an actual checker result is present."
        ),
        allowed_inputs=[
            "artifact_statement",
            "formalization_metadata",
            "alignment_notes",
        ],
        output_required=[
            "summary",
            "formalization_mapping",
            "alignment_limitations",
            "risk_flags",
        ],
        output_optional=["candidate_imports", "candidate_symbols", "next_steps"],
        context_budget=SOURCE_REVIEW_BUDGET,
        tool_policy=READ_ONLY_TOOLS,
        stop_conditions=["missing_source_locator", "alignment_unclear"],
        risk_flags=["formal_link_metadata_only", "alignment_not_proven"],
        forbidden_actions=[
            "claim_lean_checked_without_checker",
            "claim_informal_formal_equivalence",
        ],
    ),
    _contract(
        role=RoleName.EXPLORER,
        display_name="Explorer",
        purpose="Identify bounded search directions and related context.",
        system_prompt=(
            "You are the explorer role. Explore adjacent definitions, examples, "
            "sources, and open questions while keeping proposals separate from "
            "accepted knowledge."
        ),
        allowed_inputs=["issue_context", "artifact_cards", "source_notes"],
        output_required=[
            "summary",
            "search_directions",
            "source_candidates",
            "risk_flags",
        ],
        output_optional=["related_artifacts", "next_steps"],
        context_budget=EXPLORATION_BUDGET,
        tool_policy=READ_ONLY_TOOLS,
        stop_conditions=["scope_too_large", "source_boundary_unclear"],
        risk_flags=["exploratory_only", "source_review_needed"],
        forbidden_actions=["mass_import_sources", "create_accepted_artifacts"],
    ),
    _contract(
        role=RoleName.COUNTEREXAMPLER,
        display_name="Counterexampleer",
        purpose="Search for failures, counterexamples, and edge cases.",
        system_prompt=(
            "You are the counterexampleer role. Try to break candidate claims "
            "with explicit assumptions, small examples, and local deterministic "
            "checks when allowed."
        ),
        allowed_inputs=["candidate_claims", "assumptions", "known_failures"],
        output_required=[
            "summary",
            "counterexamples_or_failed_attempts",
            "assumptions_tested",
            "risk_flags",
        ],
        output_optional=["local_checks", "next_steps"],
        context_budget=VERIFIER_BUDGET,
        tool_policy=LOCAL_ANALYSIS_TOOLS,
        stop_conditions=["counterexample_found", "assumptions_incomplete"],
        risk_flags=["adversarial_check_only", "not_a_proof"],
        forbidden_actions=["claim_refutation_without_evidence", "edit_artifacts"],
    ),
    _contract(
        role=RoleName.COLLECTOR,
        display_name="Collector",
        purpose="Collect source candidates and provenance for later review.",
        system_prompt=(
            "You are the collector role. Collect source candidates, locators, "
            "and provenance notes for review without turning them into accepted "
            "artifacts or human review records."
        ),
        allowed_inputs=["source_candidates", "source_notes", "issue_context"],
        output_required=[
            "summary",
            "source_candidates",
            "locator_status",
            "risk_flags",
        ],
        output_optional=["missing_locators", "next_steps"],
        context_budget=SOURCE_REVIEW_BUDGET,
        tool_policy=READ_ONLY_TOOLS,
        stop_conditions=["source_not_citable", "locator_missing"],
        risk_flags=["source_review_required", "locator_may_be_incomplete"],
        forbidden_actions=["fabricate_source_locators", "mark_reviewed"],
    ),
)

ROLE_CONTRACT_BY_NAME = {contract.role: contract for contract in ROLE_CONTRACTS}
