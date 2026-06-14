# Post-v0.2.4 V6 Completion Audit

Audit date: 2026-06-15

Source plan: `H:\ai4tcs\longplan_v6_post_v023_artifact_failure_memory.md`

This audit checks the completed V6 Artifact Failure Memory + Attempt
Traceability line against the current repository state after the published
`v0.2.4` release closeout. It is a documentation and code-surface audit. It is
not a production-readiness claim, does not add runtime behavior, and does not
change schema, verifier, provider, MCP, gate, promotion, or KB policy
semantics.

## Summary

V6 is complete as a release line. The framework has artifact-level
`failure_log` model/schema support, read-only and controlled draft-write CLI
surfaces, WorkerBundle bridging, memory/context surfacing, promotion-readiness
warnings, security regression coverage, deterministic eval coverage, release
notes, and published `v0.2.4` package metadata. The workspace template and
public KB are pinned to `v0.2.4` and include the required demo/policy surfaces.

The V6 work remains bounded:

- `failure_log` is research memory only.
- It is not proof, verifier success, checked counterexample evidence, human
  review, source review, gate success, accepted status, accepted refutation, or
  promotion evidence.
- Accepted knowledge still requires validation, gates, human review where
  policy requires it, source metadata for accepted public artifacts, and
  explicit promotion.
- Skipped verifier, provider, SAT, SMT, Lean, lake, optional-tool, or network
  results remain skipped, not pass.
- Provider and MCP authority did not expand in this line.

## Task Evidence

| Plan task | Status | Evidence |
| --- | --- | --- |
| A.1 Post-v0.2.3 state audit | Complete | `docs/POST_V023_STATE_AUDIT.md`; `context/PROJECT_STATE.md` entry for issue 300. |
| A.2 Land V6 plan and ADR | Complete | `docs/CODEX_DEVELOPMENT_PLAN_V6.md`; `docs/ADR/0023-artifact-failure-memory.md`; issue 302. |
| B.1 Failure-log schema ADR/design | Complete | ADR 0023 and `docs/ARTIFACT_SCHEMA.md` describe fields, authority boundaries, WorkerBundle differences, and public-KB review policy. |
| B.2 Model/schema implementation | Complete | `cosheaf/core/artifact.py`, `schemas/artifact.schema.json`, `tests/test_artifact_models.py`, and `tests/test_schema_files_exist.py`. |
| C.1 Read-only failure-log CLI | Complete | `cosheaf/cli.py`, `tests/test_cli_json_readonly.py`, `docs/AGENT_ACCESS.md`, and `context/INTERFACE_REGISTRY.md`. |
| C.2 Controlled draft write CLI | Complete | `cosheaf/cli.py`, `cosheaf/services/__init__.py`, `tests/test_cli_controlled_draft_writes.py`, `docs/AGENT_ACCESS.md`, and `docs/ARTIFACT_SCHEMA.md`. |
| C.3 WorkerBundle failure-log bridge | Complete | `cosheaf/services/__init__.py`, `cosheaf/cli.py`, `tests/test_cli_controlled_draft_writes.py`, `docs/AGENT_ACCESS.md`, and `context/INTERFACE_REGISTRY.md`. |
| D.1 Failure-log memory index | Complete | `cosheaf/memory/cards.py`, `cosheaf/memory/search.py`, `tests/test_memory_cards_cli.py`, `tests/test_memory_search_cli.py`, and `docs/MEMORY_POLICY.md`. |
| D.2 Context-pack failure sections | Complete | `cosheaf/agent/context_pack.py`, `tests/test_context_pack.py`, `docs/AGENT_ACCESS.md`, and `docs/MEMORY_POLICY.md`. |
| D.3 Promotion-readiness failure memory | Complete | `cosheaf/gates/promotion_readiness.py`, `tests/test_promotion_readiness_cli.py`, `docs/ARTIFACT_SCHEMA.md`, and `docs/VERIFIER_EVIDENCE_AUDIT.md`. |
| E.1 Workspace failure-log demo | Complete | `tcs-cosheaf-workspace-template` PR #56 and current `README.md`, `docs/QUICKSTART.md`, `Makefile`, and `scripts/demo_failure_memory.sh` in that repository. |
| E.2 Public KB failure-log policy | Complete | `tcs-kb-public` PR #67 and current `docs/FAILURE_LOG_POLICY.md`, `docs/KB_POLICY.md`, `docs/REVIEW_POLICY.md`, and `.github/pull_request_template.md` in that repository. |
| F.1 Failure-log security regression | Complete | `tests/security/test_failure_log_security_regression.py` and `docs/SECURITY.md`. |
| F.2 Artifact failure-memory eval suite | Complete | `cosheaf/evals/artifact_failure_memory.py`, `evals/artifact_failure_memory/cases.yaml`, `tests/evals/test_artifact_failure_memory_eval.py`, and `docs/EVALUATION.md`. |
| G.1 v0.2.4 readiness audit | Complete | `docs/releases/v0.2.4.md` readiness-audit section and release-readiness PR #325. |
| G.2 v0.2.4 release candidate | Complete | `pyproject.toml`, `cosheaf/__init__.py`, `docs/releases/v0.2.4.md`, and release-candidate PR #327. |
| G.3 publication closeout | Complete | Published annotated `v0.2.4` tag, GitHub release, release smoke record, downstream pin PRs, and publication docs PR #329. |

## Code-Surface Audit

The current code surface matches the V6 boundaries:

- `BaseArtifact.failure_log` is optional and defaults to an empty list, so
  existing artifacts remain compatible.
- `FailureLogEntry` requires a timezone-aware `attempted_at`, stable failure
  ID, origin, attempt kind, nonempty direction, summary, failed reason, status,
  and limitations.
- Repository-local evidence paths are normalized and cannot target accepted KB
  paths.
- Read-only inspection returns deterministic JSON and an explicit
  non-authority notice.
- Controlled write commands reject accepted artifacts, direct accepted-path
  mutation, readonly roots, and authority-spoofing fields.
- WorkerBundle conversion preserves imported-bundle provenance and links typed
  counterexample candidates by reference only.
- Memory search and context packs label failure memory as failed or unresolved
  attempt context and preserve public/private scope.
- Promotion-readiness reports unresolved failure memory as warnings, not as
  automatic blockers and not as verifier failure evidence.
- Security and eval fixtures are deterministic and do not require hosted
  providers, API keys, MCP, SAT, SMT, Lean, lake, or network access.

## Downstream Audit

The user-facing workspace template is pinned to `v0.2.4` for active install,
demo, CLI-agent, provider-preview, fake-provider, verifier-evidence, and
failure-memory paths. Its failure-memory demo uses private/draft template
material and ignored runtime copies; it does not promote artifacts, create
accepted private claims, call a hosted provider, require an API key, or mark
human review complete.

The public KB CI installs `tcs-cosheaf@v0.2.4`. Public KB policy documents say
that failure logs are public research memory only, must not contain private or
unreviewed provider/agent dumps in accepted paths, and do not replace source
metadata, validation/gates, or human review.

## Documentation Closeout

The current canonical documents for this line are:

- `docs/CODEX_DEVELOPMENT_PLAN_V6.md`
- `docs/ADR/0023-artifact-failure-memory.md`
- `docs/releases/v0.2.4.md`
- `docs/ARTIFACT_SCHEMA.md`
- `docs/AGENT_ACCESS.md`
- `docs/MEMORY_POLICY.md`
- `docs/EVALUATION.md`
- `docs/SECURITY.md`
- `docs/ROADMAP.md`
- `context/CURRENT_MILESTONE.md`
- `context/PROJECT_STATE.md`
- `context/INTERFACE_REGISTRY.md`

Historical documents such as `docs/POST_V023_STATE_AUDIT.md` still describe
the pre-V6 gap at the time they were written. They should be read as historical
evidence and must not override the completed `v0.2.4` status recorded in the
current milestone, roadmap, release note, and this audit.

## Residual Non-Blockers

- Checked-counterexample review artifacts beyond WorkerBundle candidate
  records remain future evidence-taxonomy work.
- Optional SAT, SMT, Lean, lake, hosted-provider, MCP, and network paths remain
  optional and default-off; unavailable rows must stay skipped, not pass.
- A future post-v0.2.4 line should start from a fresh issue-scoped plan rather
  than reopening V6 as an active implementation queue.
