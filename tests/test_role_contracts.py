from __future__ import annotations

import pytest
from pydantic import ValidationError

from cosheaf.agent.model_provider import NetworkPolicy, ProviderName, ToolPolicy
from cosheaf.agent.roles import (
    REQUIRED_ROLE_NAMES,
    RoleContract,
    RoleName,
    get_role_contract,
    list_role_contracts,
)


def test_required_role_contracts_are_present() -> None:
    contracts = list_role_contracts()

    assert [contract.role.value for contract in contracts] == list(REQUIRED_ROLE_NAMES)
    assert {contract.role for contract in contracts} == {
        RoleName.REASONER,
        RoleName.VERIFIER,
        RoleName.COUNTEREXAMPLER,
        RoleName.EXPLORER,
        RoleName.FORMALIZER,
        RoleName.LIBRARIAN_SUMMARIZER,
    }


def test_role_contracts_define_required_boundaries() -> None:
    for contract in list_role_contracts():
        assert contract.allowed_inputs
        assert contract.forbidden_actions
        assert contract.required_output_schema.required_fields
        assert contract.context_budget.max_cards > 0
        assert contract.context_budget.max_full_artifacts >= 0
        assert contract.context_budget.max_prompt_chars > 0
        assert contract.stop_conditions
        assert contract.risk_flags

        assert "write_accepted_knowledge" in contract.forbidden_actions
        assert "promote_artifacts" in contract.forbidden_actions
        assert "mark_human_reviewed" in contract.forbidden_actions
        assert "claim_machine_verification_without_checker" in (
            contract.forbidden_actions
        )
        assert contract.context_policy
        assert contract.provider_capability_requirements


def test_role_contracts_encode_structured_failure_output_fields() -> None:
    fields = {
        contract.role: set(
            contract.required_output_schema.required_fields
        ).union(contract.required_output_schema.optional_fields)
        for contract in list_role_contracts()
    }

    assert {
        "conjectures",
        "proof_ideas",
        "assumptions",
        "uncertainty",
        "verification_requests",
    }.issubset(fields[RoleName.REASONER])
    assert {
        "natural_language_concerns",
        "tool_results",
        "verification_requests",
        "failed_attempts",
    }.issubset(fields[RoleName.VERIFIER])
    assert {
        "counterexample_candidates",
        "verified_counterexamples",
        "failed_attempts",
        "assumptions_tested",
        "uncertainty",
    }.issubset(fields[RoleName.COUNTEREXAMPLER])
    assert {"uncertainty", "dependency_questions"}.issubset(
        fields[RoleName.EXPLORER]
    )
    assert {
        "symbol_resolution",
        "semantic_alignment_questions",
        "alignment_limitations",
    }.issubset(fields[RoleName.FORMALIZER])
    assert {"selected_artifacts", "retrieval_audit", "uncertainty"}.issubset(
        fields[RoleName.LIBRARIAN_SUMMARIZER]
    )


def test_role_contracts_reject_missing_role_specific_output_fields() -> None:
    data = get_role_contract(RoleName.REASONER).to_dict()
    data["required_output_schema"]["required_fields"].remove("assumptions")

    with pytest.raises(ValidationError, match="missing role-specific output fields"):
        RoleContract.model_validate(data)


def test_role_contracts_reject_missing_forbidden_authority() -> None:
    data = get_role_contract(RoleName.LIBRARIAN_SUMMARIZER).to_dict()
    data["forbidden_actions"].remove("invent_claims")

    with pytest.raises(ValidationError, match="missing forbidden authority"):
        RoleContract.model_validate(data)


def test_role_contracts_do_not_enable_hosted_llm_or_network() -> None:
    for contract in list_role_contracts():
        assert contract.provider is ProviderName.FAKE
        assert contract.hosted_llm_enabled is False
        assert contract.tool_policy.network_policy is NetworkPolicy.DISABLED
        assert contract.tool_policy.tool_policy in {
            ToolPolicy.NONE,
            ToolPolicy.READ_ONLY,
            ToolPolicy.LOCAL_TOOLS,
            ToolPolicy.VERIFIER_TOOLS,
        }


def test_role_prompts_are_role_specific_not_one_generic_prompt() -> None:
    prompts = [contract.system_prompt for contract in list_role_contracts()]

    assert len(set(prompts)) == len(prompts)
    for contract in list_role_contracts():
        assert contract.role.value.replace("_", " ") in contract.system_prompt


def test_required_hosted_worker_role_names_match_p4_plan() -> None:
    assert list(REQUIRED_ROLE_NAMES) == [
        "reasoner",
        "verifier",
        "counterexampleer",
        "explorer",
        "formalizer",
        "librarian_summarizer",
    ]


def test_role_contract_lookup_and_serialization_are_deterministic() -> None:
    librarian = get_role_contract("librarian_summarizer")
    verifier = get_role_contract(RoleName.VERIFIER)

    assert librarian.role is RoleName.LIBRARIAN_SUMMARIZER
    assert verifier.role is RoleName.VERIFIER
    assert librarian.to_json() == librarian.to_json()
    assert list(librarian.to_dict()) == [
        "role",
        "display_name",
        "purpose",
        "system_prompt",
        "allowed_inputs",
        "forbidden_actions",
        "required_output_schema",
        "context_budget",
        "context_policy",
        "provider_capability_requirements",
        "tool_policy",
        "stop_conditions",
        "risk_flags",
        "provider",
        "hosted_llm_enabled",
    ]
