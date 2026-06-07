# Agent Role Contracts

TCS-Cosheaf role contracts define bounded prompt, context, tool, output, and
safety expectations for future worker integrations. They are machine-readable
policy data under `cosheaf.agent.roles`.

They do not enable hosted LLM execution, do not call model providers, do not
run workers, do not write accepted knowledge, and do not replace validation,
gates, verifier adapters, or human review.

## Contract Shape

Each `RoleContract` records:

- `role`
- `display_name`
- `purpose`
- `system_prompt`
- `allowed_inputs`
- `forbidden_actions`
- `required_output_schema`
- `context_budget`
- `tool_policy`
- `stop_conditions`
- `risk_flags`
- `provider`
- `hosted_llm_enabled`

All current contracts use `provider: fake`, `hosted_llm_enabled: false`, and
`network_policy: disabled`.

## Roles

| Role | Purpose | Tool Policy | Boundary |
| --- | --- | --- | --- |
| `librarian` | Retrieve and rank existing repository context. | `read_only` | May surface context, not create claims or rewrite artifacts. |
| `reasoner` | Draft candidate reasoning for review. | `none` | May propose arguments, not accepted knowledge or source review. |
| `verifier` | Check explicit evidence, validation, gates, and verifier results. | `verifier_tools` | Must preserve pass/fail/error/skipped distinctions. |
| `formalizer` | Propose formal-link metadata and alignment questions. | `read_only` | Formal links remain metadata unless a checker actually runs. |
| `explorer` | Identify bounded search directions and related context. | `read_only` | Exploration is not mass import or accepted-artifact creation. |
| `counterexampleer` | Search for failures, counterexamples, and edge cases. | `local_tools` | Local checks are adversarial evidence, not proof by themselves. |
| `collector` | Collect source candidates, locators, and provenance notes. | `read_only` | Source collection is not human review or accepted promotion. |

## Common Forbidden Actions

Every role contract forbids:

- `write_accepted_knowledge`
- `promote_artifacts`
- `mark_human_reviewed`
- `claim_machine_verification_without_checker`
- `modify_public_kb`
- `hide_gate_or_verifier_failures`

Individual roles add further role-specific forbidden actions, such as refusing
fabricated source locators, hidden skipped verifier results, or claimed
informal/formal equivalence without alignment review.

## Usage

Use `list_role_contracts()` to inspect all role contracts in deterministic
order and `get_role_contract(<role>)` to load one contract by role name.

Role contracts are input to future worker/runtime work. They do not dispatch
workers or grant permission to write artifacts. Accepted knowledge still enters
only through source metadata where required, validation, gates, human review,
and explicit promotion.
