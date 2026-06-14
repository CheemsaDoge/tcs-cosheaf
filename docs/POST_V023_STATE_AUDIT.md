# Post-v0.2.3 State Audit

Issue: [#300](https://github.com/CheemsaDoge/tcs-cosheaf/issues/300)

Date: 2026-06-14

## Summary

The published `v0.2.3` release is aligned across the three repositories:

- `tcs-cosheaf` reports package version `0.2.3`.
- `tcs-cosheaf-workspace-template` active install/demo/provider/verifier
  paths pin or default to `tcs-cosheaf@v0.2.3`.
- `tcs-kb-public` CI installs `tcs-cosheaf@v0.2.3`.
- All three repositories had no open issues or pull requests when this audit
  issue was opened.

The implementation gap for the next release line is real: artifact records do
not yet have an artifact-level `failure_log` field in the Pydantic model or
JSON Schema. Failure and counterexample memory exists in WorkerBundle,
review-request, eval, and report-adjacent surfaces, but it is not yet durable
on long-lived artifact records.

This audit is documentation/status only. It does not change runtime behavior,
schemas, verifier behavior, provider/MCP authority, public/private KB policy,
accepted-promotion semantics, workspace-template behavior, or public KB
content.

## Three-Repository State

### tcs-cosheaf

- Local branch: `main...origin/main` before this audit branch.
- Current main commit when the audit started:
  `9816ec6f0b01de724d12cc7a06947d4749fd295b`.
- Latest commit subject: `Close post-v0.2.3 docs audit`.
- Runtime version command:
  `python -m cosheaf.cli version --json` reported `0.2.3`.
- GitHub issue/PR state before opening this audit issue:
  no open issues and no open pull requests.

### tcs-cosheaf-workspace-template

- Local branch: `main...origin/main`.
- Current main commit when the audit started:
  `359c8cee2478bb9e4d257710ddfb7bc1005c02a9`.
- Latest commit subject: `Pin workspace template to v0.2.3`.
- Active references in `README.md`, `Makefile`, docs, and demo/provider
  scripts pin or default to
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.3`.
- GitHub issue/PR state before opening this audit issue:
  no open issues and no open pull requests.

### tcs-kb-public

- Local branch: `main...origin/main`.
- Current main commit when the audit started:
  `967b343653b8134aa667139a6b7ba3afba4f365b`.
- Latest commit subject: `Pin public KB CI to v0.2.3`.
- `.github/workflows/ci.yml` installs
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.3`.
- GitHub issue/PR state before opening this audit issue:
  no open issues and no open pull requests.

## Artifact-Level Failure Memory Gap

`cosheaf/core/artifact.py` currently defines `BaseArtifact` with:

- `id`
- `type`
- `title`
- `domain`
- `status`
- `created_at`
- `updated_at`
- `authors`
- `depends_on`
- `supersedes`
- `tags`
- `statement`
- `evidence`
- `sources`
- `formalizations`
- `alignment`
- `verification_policy`
- `review`
- `risk`

There is no `failure_log` field on `BaseArtifact`.

`schemas/artifact.schema.json` likewise has no `failure_log` property and does
not define failure-log entry fields. The schema is strict with
`additionalProperties: false`, so artifact YAML files cannot add `failure_log`
until the model and schema are extended together.

Current validation behavior is therefore:

- existing artifacts without `failure_log` validate;
- artifacts with an undeclared `failure_log` would be rejected by the strict
  model/schema path;
- there is no artifact-level place to preserve failed proof, reduction,
  construction, counterexample-search, formalization, verifier, or retrieval
  directions.

## Existing Failure-Memory Surfaces

The project already preserves failure/counterexample material in sidecar or
workflow records:

- `cosheaf/agent/worker_bundle_v2.py`
  - `WorkerBundleV2.failed_attempts`
  - legacy string `counterexamples`
  - typed `counterexample_candidates`
  - `failures_or_counterexamples`
  - `dependency_questions`
  - reducer warnings that label failures and candidates as review-only
- `schemas/worker_bundle_v2.schema.json`
  - schema coverage for optional `failed_attempts` and typed
    `counterexample_candidates`
- `cosheaf/services/__init__.py`
  - `review request-from-bundle` generation preserves WorkerBundle
    `failed_attempts`, `counterexamples`, and typed
    `counterexample_candidates` as draft informational review findings
- `cosheaf/evals/failure_counterexample.py`
  - deterministic eval coverage for preserving failures and candidates without
    authority expansion
- `cosheaf/evals/verifier_evidence.py`
  - deterministic eval coverage that keeps candidate counterexamples
    review-only and Lean `#check` symbol-resolution-only
- `cosheaf/gates/promotion_readiness.py`
  - read-only promotion readiness reporting that distinguishes review,
    verifier, source metadata, dependency, draft status, and gate issues
- `docs/AGENT_ACCESS.md`, `docs/AGENT_ROLES.md`, `docs/EVALUATION.md`,
  `docs/GATES.md`, `docs/VERIFIER_EVIDENCE_AUDIT.md`,
  `docs/releases/v0.2.3.md`, and `context/INTERFACE_REGISTRY.md`
  - documentation and interface registry coverage for WorkerBundle failure and
    counterexample boundaries

These surfaces do not replace an artifact-level `failure_log`. WorkerBundle and
review-request records are task/run/review context; they are not embedded in
the durable artifact record that future retrieval, context-pack, or promotion
readiness surfaces naturally inspect.

## Files Likely To Change In Later Tasks

Schema and model design:

- `docs/ADR/0023-artifact-failure-memory.md`
- `docs/ARTIFACT_SCHEMA.md`
- `docs/AGENT_ACCESS.md`
- `docs/VERIFIER_EVIDENCE_AUDIT.md`
- `context/INTERFACE_REGISTRY.md`

Model/schema implementation:

- `cosheaf/core/artifact.py`
- `schemas/artifact.schema.json`
- `tests/test_artifact_models.py`
- `tests/test_schema_files_exist.py`
- related validation/status tests if path safety helpers are shared

Read CLI and controlled write services:

- `cosheaf/cli.py`
- `cosheaf/services/`
- `tests/test_artifact_lifecycle_cli.py` or focused artifact failure CLI tests
- `docs/ARTIFACT_SCHEMA.md`
- `docs/AGENT_ACCESS.md`
- `context/INTERFACE_REGISTRY.md`

WorkerBundle bridge:

- `cosheaf/agent/worker_bundle_v2.py` if helper methods are needed
- `cosheaf/services/`
- `cosheaf/cli.py`
- `tests/test_worker_bundle_v2.py`
- `tests/test_cli_controlled_draft_writes.py`
- `docs/AGENT_ACCESS.md`
- `docs/AGENT_PROVIDERS.md`
- `context/INTERFACE_REGISTRY.md`

Retrieval, memory, context, and readiness surfacing:

- `cosheaf/memory/`
- `cosheaf/storage/`
- `cosheaf/agent/context_pack.py`
- `cosheaf/gates/promotion_readiness.py`
- `tests/test_context_pack.py`
- `tests/test_memory_search_cli.py`
- `tests/test_promotion_readiness_cli.py`
- `docs/MEMORY_POLICY.md`
- `docs/AGENT_ACCESS.md`
- `docs/ARTIFACT_SCHEMA.md`
- `context/INTERFACE_REGISTRY.md`

Workspace and public KB integration:

- `tcs-cosheaf-workspace-template` docs/scripts/Makefile and private draft
  demo material
- `tcs-kb-public` docs and policy guard if failure-log policy becomes
  checkable

Security and eval coverage:

- `tests/security/`
- `cosheaf/evals/`
- `evals/`
- `tests/evals/`
- `docs/EVALUATION.md`
- `docs/SECURITY.md` if security policy wording changes

## Required Boundaries For Later Work

- `failure_log` must be optional and backward compatible.
- `failure_log` is research memory, not proof, verifier success, human review,
  or promotion evidence.
- A failed attempt does not refute a claim without a separate checked
  counterexample or reviewed refutation path.
- Agent/provider-origin entries must preserve origin and must not claim human
  review.
- Failure memory may inform retrieval, context, and review, but must not bypass
  validation, gates, reviewer judgment, verifier requirements, or promotion.
- Existing public/private policy must remain unchanged.
- Real provider calls must remain default-off and absent from CI/default tests.
- MCP must remain optional/read-only unless a separate maintainer-approved
  issue changes that scope.
- No accepted public KB content should be mass-updated as part of the schema
  introduction.

## Audit Conclusion

The next implementation line should proceed. The immediate next task is to land
the V6 plan and ADR for artifact failure memory before changing the artifact
model or schema.
