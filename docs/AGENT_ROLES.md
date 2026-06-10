# Agent Role Contracts

TCS-Cosheaf role contracts define bounded prompt, context, tool, output, and
safety expectations for worker integrations. They are machine-readable policy
data under `cosheaf.agent.roles`.

Role contracts do not grant authority to write accepted knowledge, mark human
review, promote artifacts, bypass gates, or claim machine verification. Hosted
worker execution, when used through `HostedWorkerService`, still routes output
through local validation and review-only result types.

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
- `context_policy`
- `provider_capability_requirements`
- `tool_policy`
- `stop_conditions`
- `risk_flags`
- `provider`
- `hosted_llm_enabled`

All current contracts use `provider: fake`, `hosted_llm_enabled: false`, and
`network_policy: disabled`. Real provider transport remains an explicit
configuration and consent concern outside the static role contract.

## Hosted Worker Roles

`REQUIRED_ROLE_NAMES` is the hosted-worker role set for the current
CLI-first/provider track:

| Role | Output Surface | Tool Policy | Boundary |
| --- | --- | --- | --- |
| `reasoner` | WorkerBundle v2 | `none` | May propose arguments for review, not accepted knowledge or source review. |
| `verifier` | WorkerBundle v2 | `verifier_tools` | Must preserve pass/fail/error/skipped distinctions and cannot mark accepted or human reviewed. |
| `counterexampleer` | WorkerBundle v2 | `local_tools` | May search for failures and edge cases; local checks are not proof by themselves. |
| `explorer` | typed sub-result | `read_only` | Exploration is not mass import or accepted-artifact creation. |
| `formalizer` | WorkerBundle v2 | `read_only` | Formal links remain metadata unless a checker actually records a result. |
| `librarian_summarizer` | typed sub-result | `read_only` | Summarizes bounded retrieval context without creating claims or review authority. |

Legacy local role names `librarian` and `collector` are accepted by
`get_role_contract(...)` as aliases for `librarian_summarizer`; they are not
part of the required hosted-worker role order.

## Hosted Worker Bridge

`cosheaf.agent.hosted_workers.HostedWorkerService` connects these contracts to
the provider gateway. It supports:

- deterministic fake-provider worker runs for tests and local smoke paths;
- mocked OpenAI-compatible provider calls through an injected transport;
- WorkerBundle v2 output for roles that map directly to protocol
  `WorkerType`;
- typed review-only sub-results for roles such as `explorer` and
  `librarian_summarizer`;
- local rejection of invalid provider output or unsafe authority claims.

The bridge does not add a hosted-provider CLI command, built-in HTTP transport,
or orchestrator dispatch. It does not write accepted artifacts, create human
review records, promote artifacts, or treat provider output as truth.

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

Use `list_role_contracts()` to inspect required hosted-worker role contracts in
deterministic order and `get_role_contract(<role>)` to load one contract by
role name or legacy alias.

Accepted knowledge still enters only through source metadata where required,
validation, gates, human review, and explicit promotion.
