# Evaluation

## Scope

Cosheaf evaluation commands are deterministic local regression checks for
retrieval and future context/orchestrator surfaces. They are not hosted
benchmarks, do not call LLMs, do not use network access, and do not change
artifact, review, gate, or promotion state.

The Phase 7 retrieval eval harness measures whether the existing local
artifact-card retrieval surface still returns expected records for small,
reviewable cases. The context-pack regression eval checks whether bounded
context packs stay within configured card, full-artifact, token, and policy
budgets. The agent workflow eval harness checks CLI-agent and provider-worker
workflow boundaries by invoking existing CLI commands through a Python test
harness. The provider workflow eval harness checks provider success, expected
policy denials, validation rejections, context-scope boundaries, and provider
log leakage by calling local services with fake or mocked transports. The
failure/counterexample eval harness checks that WorkerBundle v2 reducer
boundaries preserve failed attempts, uncertainty, candidate counterexamples,
and verification requests as review context. The verifier evidence eval harness
checks verifier-result, promotion-readiness, candidate-counterexample, and Lean
`#check` boundaries with deterministic fake evidence records. The artifact
failure-memory eval harness checks artifact-level failure-log retrieval and
governance boundaries. The checked-evidence run-loop eval harness checks the
candidate-vs-checked counterexample boundary, supporting evidence requirements,
skipped-not-pass behavior, and non-authority constraints for durable checked
counterexample evidence. The research-run loop eval harness checks command
coverage, skipped-not-pass behavior, evidence separation, private-leak
prevention, and authority escalation for external-operator run records. These
harnesses reuse existing runtime surfaces; they do not introduce new
retrieval, context-pack, provider, MCP, verifier, or orchestration algorithms.

## Retrieval Eval Cases

Retrieval eval cases are YAML records under `evals/retrieval/`. The default
case file is:

```text
evals/retrieval/cases.yaml
```

Case file format:

```yaml
schema_version: 1
cases:
  - id: case.retrieval.example
    query: graph separator
    issue_id: issue.example.optional
    expected_relevant_artifacts:
      - definition.example.graph
    forbidden_artifacts:
      - claim.example.private-draft
    allowed_scope:
      - public
```

Fields:

- `query`: local retrieval query text.
- `issue_id`: optional issue ID used as issue-conditioned retrieval context.
- `expected_relevant_artifacts`: artifact IDs that should appear in the top-k
  hits.
- `forbidden_artifacts`: artifact IDs that must not appear in the top-k hits.
- `allowed_scope`: allowed card scopes such as `public`, `workspace`, or
  `framework`.

Private scope is supported by the underlying memory model, but public eval
cases should use it only when the task is explicitly testing private-overlay
behavior. Private leakage is measured separately.

## Metrics

`cosheaf eval retrieval` reports:

- `hit@k`: fraction of cases with at least one expected artifact in the top-k
  retrieval result.
- `forbidden_hit_count`: total forbidden artifact hits across all cases.
- `accepted_priority_score`: average fraction of expected hits that are
  accepted artifacts.
- `private_leakage_count`: total private-scope hits returned when `private` is
  not listed in `allowed_scope`.

These metrics are regression signals only. Retrieval scores, graph scores, and
eval metrics are not proof, human review, source review, verifier evidence, or
accepted-promotion authority.

## Context Eval Cases

Context eval cases are YAML records under `evals/context/`. The default case
file is:

```text
evals/context/cases.yaml
```

Case file format:

```yaml
schema_version: 1
cases:
  - id: case.context.example
    issue_id: issue.example.context
    required_artifacts:
      - definition.example.graph
    role: orchestrator
    public_only: true
    max_cards: 5
    max_full_artifacts: 0
    max_allowed_cards: 5
    max_allowed_full_artifacts: 0
    max_token_estimate: 4000
    min_accepted_ratio: 0.5
    max_draft_ratio: 0.5
    allow_private_cards: false
    allow_known_failures: false
    require_all_required_artifacts: true
```

Fields:

- `issue_id`: issue used to build the context pack.
- `required_artifacts`: artifact IDs that should appear in the context pack's
  retrieved cards.
- `role`: retrieval role passed to `build_context_pack`; the default is
  `orchestrator`.
- `public_only`: when true, the context pack excludes private cards and private
  artifact IDs.
- `max_cards`: card search bound passed to the context-pack builder.
- `max_full_artifacts`: explicit full-artifact pull budget passed to the
  context-pack builder. The orchestrator-safe default is `0`.
- `max_allowed_cards`, `max_allowed_full_artifacts`, and `max_token_estimate`:
  regression thresholds for boundedness. If omitted, the allowed card and
  full-artifact thresholds default to the requested builder budgets.
- `min_accepted_ratio` and `max_draft_ratio`: policy thresholds for the
  returned card mix.
- `allow_private_cards`: permits private cards in non-public-only cases when a
  private-overlay task is intentionally being tested.
- `allow_known_failures`: permits refuted, obsolete, or superseded cards when a
  task intentionally asks for known failures.
- `require_all_required_artifacts`: fails the case when any required artifact is
  absent.

`cosheaf eval context` reuses `build_context_pack`, then scores the generated
`RETRIEVAL_AUDIT.json`. Like `cosheaf context build`, it may refresh
`context/TASKS/<issue-id>/` runtime context-pack files. Do not commit those
runtime outputs unless a task explicitly asks for persisted handoff material.

## Context Metrics

`cosheaf eval context` reports:

- `max_cards`: largest returned card count across cases.
- `max_full_artifacts`: largest full-artifact pull count across cases.
- `token_estimate`: largest approximate token count across generated context
  pack files, using a deterministic character-count estimate.
- `accepted_ratio`: average fraction of returned cards with accepted status.
- `draft_ratio`: average fraction of returned cards with pre-accepted status.
- `private_leakage_count`: total private cards returned when private cards are
  not allowed.
- `required_artifact_hit`: average fraction of required artifacts returned.

Case output also lists returned artifacts, full-artifact pulls, private cards,
known-failure cards, missing required artifacts, and policy failures. A failed
case exits nonzero in text mode and records the failures in JSON mode.

## Agent Workflow Eval Cases

Agent workflow eval cases are YAML records under `evals/agent_workflow/`. The
default case file is:

```text
evals/agent_workflow/cases.yaml
```

The harness is a Python API in `cosheaf.evals.agent_workflow`; there is no
dedicated `cosheaf eval agent-workflow` CLI command in this phase. Tests load
the suite and invoke the existing Typer CLI through `CliRunner`.

Case file format:

```yaml
schema_version: 1
cases:
  - id: case.agent.cli-agent-workflow
    kind: cli_agent_workflow
    surface: cli
    command:
      - context
      - build
      - issue.agent-dry-run.demo
      - --public-only
      - --json
    expect_exit_code: 0
    expect_json: true
    required_artifacts:
      - claim.agent-dry-run.demo
    forbidden_substrings:
      - kb/private
      - private-secret
```

Required case kinds for the default suite are:

- `cli_agent_workflow`: CLI context workflow smoke.
- `provider_worker_fake`: deterministic fake-provider worker boundary.
- `context_privacy`: provider context-preview privacy regression.
- `bundle_validity`: malformed WorkerBundle rejection.
- `gate_regression`: accepted-write rejection through the controlled draft
  write surface.
- `optional_mcp_readonly`: existing read-only MCP whitelist smoke, when that
  surface is present. This does not make MCP mandatory and does not add MCP
  write behavior.

`surface` records which access path the case exercises: `cli`, `provider`, or
`optional_mcp`. The command list is passed to the existing `cosheaf` CLI app.
The `{repo_root}` token expands to the active repository root and is used only
for repository-local paths.

## Agent Workflow Metrics

The agent workflow eval report records:

- `command_success_rate`: fraction of cases whose exit code matched
  `expect_exit_code`.
- `json_parse_success_rate`: fraction of cases with parseable JSON when
  `expect_json` is true; text-only cases opt out explicitly.
- `required_artifact_hit`: average fraction of required artifact IDs observed
  in command output or generated context retrieval audit files.
- `private_leakage_count`: forbidden substring hits across case stdout.
- `accepted_write_rejection_count`: expected accepted-write policy rejections.
- `malformed_bundle_rejection_count`: expected malformed bundle rejections.
- `provider_redaction_pass_count`: fake-provider cases whose redacted log
  evidence confirms secret redaction.
- `surface_counts`: deterministic counts for `cli`, `provider`, and
  `optional_mcp` cases.

Expected safety rejections are successful eval outcomes only when the command
exits with the expected code and returns the expected structured error code.
Skipped or unavailable external tools are not treated as passes.

## Provider Workflow Eval Cases

Provider workflow eval cases are YAML records under `evals/provider_workflow/`.
The default case file is:

```text
evals/provider_workflow/cases.yaml
```

The harness is a Python API in `cosheaf.evals.provider_workflow`; there is no
dedicated `cosheaf eval provider-workflow` CLI command in this phase. Tests load
the suite and invoke existing service-layer boundaries directly, using fake
provider output, injected mocked OpenAI-compatible transports, and the
provider-send context policy service.

Case file format:

```yaml
schema_version: 1
cases:
  - id: case.provider.missing-consent
    kind: missing_consent
    expected_error_code: provider_confirm_send_required
    expect_policy_denial: true
    forbidden_substrings:
      - sk-provider-workflow-
```

Required case kinds for the default suite are:

- `fake_provider_success`: deterministic fake hosted-worker success.
- `mocked_openai_success`: injected mocked OpenAI-compatible hosted-worker
  success.
- `missing_config`: OpenAI-compatible preflight failure for missing provider
  configuration.
- `missing_consent`: explicit-send consent failure.
- `private_context_denied`: private context denied by provider-send policy.
- `malformed_output`: invalid provider output rejected by WorkerBundle
  validation.
- `policy_violating_verifier_output`: verifier output rejected for unsafe
  authority claims.
- `rate_limit`, `timeout`, and `cancellation`: injected transport failure
  fixtures with stable provider error codes.

Expected safety failures are successful eval outcomes only when the observed
error code exactly matches `expected_error_code`. The harness scans structured
case output and generated `.cosheaf/providers/` logs for provider-log leakage.
It does not call live provider networks, does not require API keys, and does
not write accepted knowledge.

## Provider Workflow Metrics

The provider workflow eval report records:

- `policy_denial_accuracy`: fraction of expected policy-denial cases that
  returned the exact expected structured error code.
- `validation_rejection_accuracy`: fraction of expected validation-rejection
  cases that returned the exact expected structured error code.
- `secret_leak_count`: total provider-log scanner findings plus forbidden
  substring leaks observed in case output/logs.
- `malformed_output_reject_count`: count of malformed-output cases rejected as
  provider output validation failures.
- `bundle_validity_rate`: fraction of expected-valid WorkerBundle outputs that
  completed with a valid bundle.
- `context_scope_violation_count`: count of private-context or scope-denial
  cases observed by the provider-send policy boundary.

These metrics are regression signals only. They are not provider quality
scores, proof evidence, human review, source review, accepted status, or
promotion authority.

## Failure/Counterexample Eval Cases

Failure/counterexample eval cases are YAML records under
`evals/failure_counterexample/`. The default case file is:

```text
evals/failure_counterexample/cases.yaml
```

The harness is a Python API in `cosheaf.evals.failure_counterexample`; there
is no dedicated `cosheaf eval failure-counterexample` CLI command in this
phase. Tests load the suite and invoke the existing WorkerBundle v2 reducer
boundary directly. The harness writes deterministic bundle fixtures under
`.cosheaf/evals/failure_counterexample/` and does not write accepted
knowledge.

Case file format:

```yaml
schema_version: 1
cases:
  - id: case.failure.counterexample-candidate
    kind: counterexample_candidate
    expect_failure_preserved: true
    expect_counterexample_candidate: true
    expect_verifier_request: true
```

Required case kinds for the default suite are:

- `reasoner_uncertainty`: reasoner output preserves an assumption, uncertainty,
  failed attempt, and verifier request.
- `counterexample_candidate`: counterexampleer output preserves candidate
  counterexample evidence without treating it as a checked refutation.
- `verifier_rejects_invalid_proof`: verifier output preserves an invalid proof
  rejection as a failed attempt plus uncertainty and next verifier request.
- `reducer_preserves_failure`: reducer warnings preserve failed attempts and
  legacy failure notes as reviewer context.
- `accepted_write_boundary`: unsafe accepted-path output is rejected by the
  WorkerBundle v2 boundary and no accepted path is created.

Expected safety failures are successful eval outcomes only when the reducer
rejects the unsafe bundle for the expected case. Candidate counterexamples are
review-only evidence until a verifier and human review process checks them.
WorkerBundle v2 may now carry typed `counterexample_candidates` with
candidate IDs, optional target claims, construction summaries, evidence paths,
verifier-request IDs, status, and limitations. The current eval metrics still
score the reducer boundary by looking for candidate-review warnings; typed
candidates remain review context and do not become accepted refutations.

## Failure/Counterexample Metrics

The failure/counterexample eval report records:

- `failure_preservation_rate`: fraction of cases expecting preserved failure
  evidence whose reducer warnings retained it.
- `uncertainty_field_presence`: fraction of cases expecting uncertainty whose
  reducer warnings retained it.
- `counterexample_candidate_flag_accuracy`: fraction of cases expecting a
  candidate counterexample whose reducer warnings labeled it as a candidate.
- `verifier_request_presence`: fraction of cases expecting verifier requests
  whose reducer warnings retained them.
- `accepted_write_violation_count`: count of cases that opened or returned an
  accepted write path.

These metrics are regression signals only. They are not proof evidence, human
review, source review, verifier results, accepted status, accepted refutation,
or promotion authority.

## Artifact Failure-Memory Eval Cases

Artifact failure-memory eval cases are YAML records under
`evals/artifact_failure_memory/`. The default case file is:

```text
evals/artifact_failure_memory/cases.yaml
```

The harness is a Python API in `cosheaf.evals.artifact_failure_memory`; there
is no dedicated `cosheaf eval artifact-failure-memory` CLI command in this
phase. Tests load the suite and create deterministic temporary workspaces under
`.cosheaf/evals/artifact_failure_memory/`. Each fixture contains a readonly
public KB root, a writable private KB root, one accepted public artifact with
failure memory, one private draft artifact with private failure memory, and an
issue that references both. The harness searches the existing artifact-card
surface and does not write accepted knowledge in the source repository.

Case file format:

```yaml
schema_version: 1
cases:
  - id: case.failure-memory.retrieval-recall
    kind: failure_retrieval
    query: separator induction dead end
    public_only: true
    expect_failure_retrieved: true
```

Required case kinds for the default suite are:

- `failure_retrieval`: public failure memory is retrievable by relevant query.
- `repeat_failed_direction`: repeated failed directions are surfaced so they
  can be avoided.
- `public_scope_boundary`: public-only retrieval does not leak private
  failure-log text or private artifact IDs.
- `authority_boundary`: failure memory remains non-authoritative review
  context and is not surfaced as proof, human review, verifier pass, accepted
  status, or promotion evidence.
- `candidate_counterexample_boundary`: candidate references in failure logs
  remain candidates and are not mislabeled as checked counterexamples.

## Artifact Failure-Memory Metrics

The artifact failure-memory eval report records:

- `failure_retrieval_recall`: fraction of expected failure-memory retrieval
  cases where the public failure direction was returned.
- `repeat_failed_direction_rate`: fraction of expected repeat-direction cases
  where the repeated failed direction slipped through undetected; lower is
  better.
- `failure_scope_leak_count`: count of cases that leaked private failure-log
  text or private artifact IDs into public-only output.
- `failure_authority_violation_count`: count of cases that surfaced failure
  memory as proof, human review, verifier pass, accepted status, checked
  counterexample evidence, or promotion authority.
- `candidate_counterexample_mislabel_count`: count of cases that mislabeled a
  candidate counterexample reference as checked.

These metrics are regression signals only. Artifact failure memory is not
proof evidence, verifier success, checked counterexample evidence, human
review, source review, gate success, accepted status, accepted refutation, or
promotion authority.

## Checked-Evidence Run-Loop Eval Cases

Checked-evidence run-loop eval cases are YAML records under
`evals/checked_evidence_run_loop/`. The default case file is:

```text
evals/checked_evidence_run_loop/cases.yaml
```

The harness is available both as a Python API in
`cosheaf.evals.checked_evidence_run_loop` and as a CLI command:

```bash
cosheaf eval checked-evidence-run-loop --json
```

Case file format:

```yaml
schema_version: 1
cases:
  - id: case.checked-evidence.checked-refutes-with-support
    kind: checked_refutes_with_support
    expect_checked_result: checked_refutes
    expect_checked_refutation: true
    expect_support_required: true
```

Required case kinds for the default suite are:

- `candidate_remains_candidate`: a candidate remains review-only and is not
  treated as checked evidence.
- `checked_refutes_with_support`: `checked_refutes` has supporting evidence.
- `skipped_not_pass`: skipped checked evidence is not treated as pass.
- `inconclusive_not_refutes`: inconclusive results are not refutations.
- `error_not_pass`: error results are not passes or refutations.

## Checked-Evidence Run-Loop Metrics

The checked-evidence run-loop eval report records:

- `candidate_checked_separation_accuracy`: fraction of cases that preserve the
  expected candidate-vs-checked boundary.
- `checked_refutes_support_count`: count of checked-refutation cases with
  supporting verifier evidence IDs, review paths, or evidence paths.
- `skipped_not_pass_count`: count of skipped cases that remain skipped and are
  not treated as pass.
- `non_refuting_result_count`: count of `inconclusive` and `error` cases that
  do not become refutations.
- `accepted_write_violation_count`: count of cases that opened or reported an
  accepted write.

These metrics are regression signals only. Checked counterexample evidence is
not proof evidence, human review, accepted status, accepted refutation, or
promotion authority.

## Research-Run Loop Eval Cases

Research-run loop eval cases are YAML records under `evals/research_run_loop/`.
The default case file is:

```text
evals/research_run_loop/cases.yaml
```

The harness is available both as a Python API in
`cosheaf.evals.research_run_loop` and as a CLI command:

```bash
cosheaf eval research-run-loop --json
```

Required case kinds for the default suite are:

- `complete_command_coverage`: a run records at least one command.
- `skipped_not_pass`: skipped run steps remain non-pass evidence.
- `evidence_separation`: checked evidence remains review evidence and does not
  become accepted authority.
- `private_leakage_prevention`: private markers do not leak into run records.
- `no_authority_escalation`: run records do not claim human review,
  accepted-write, verifier-pass, gate-pass, or promotion authority.

The report records command coverage, skipped-not-pass count,
evidence-separation count, private leak count, authority-escalation count, and
accepted-write violation count. These metrics are regression signals only.
Research runs are provenance, not proof, human review, verifier pass, gate
pass, accepted status, or promotion authority.

## Verifier Evidence Eval Cases

Verifier evidence eval cases are YAML records under `evals/verifier_evidence/`.
The default case file is:

```text
evals/verifier_evidence/cases.yaml
```

The harness is a Python API in `cosheaf.evals.verifier_evidence`. Tests load
the suite and exercise deterministic fake verifier evidence records plus typed
counterexample candidate fixtures. It does not run SAT, SMT, Lean, lake, or any
external checker.

Case file format:

```yaml
schema_version: 1
cases:
  - id: case.verifier.skipped-required
    kind: skipped_checker_required
    expect_ready: false
    expect_evidence_result: skipped
    expected_reason_codes:
      - skipped_verifier
    expect_skipped_not_pass: true
```

Required case kinds for the default suite are:

- `pass_evidence_policy_allowed`: passing verifier evidence supports readiness
  only in a fixture where ordinary policy requirements are satisfied.
- `failed_evidence_blocks_readiness`: failed verifier evidence records a stable
  `failed_verifier` readiness blocker.
- `skipped_checker_required`: skipped checker-required evidence records a
  stable `skipped_verifier` blocker and is not treated as pass.
- `counterexample_remains_candidate`: typed counterexample candidates remain
  review-only evidence rather than checked counterexamples or accepted
  refutations.
- `lean_check_symbol_only`: external Lean `#check` pass evidence is recorded as
  symbol/import resolution only, not semantic alignment.

## Verifier Evidence Metrics

The verifier evidence eval report records:

- `readiness_boundary_accuracy`: fraction of readiness expectations that match
  the reported ready/not-ready boundary.
- `failed_evidence_block_count`: count of failed verifier cases that produce a
  `failed_verifier` blocker.
- `skipped_not_pass_count`: count of skipped verifier cases that remain
  skipped and are not treated as pass.
- `candidate_counterexample_review_only_count`: count of candidate
  counterexample cases that remain review-only evidence.
- `lean_alignment_claim_count`: count of cases that incorrectly claim semantic
  alignment from Lean symbol resolution.
- `accepted_write_violation_count`: count of cases that opened or reported an
  accepted write.

These metrics are regression signals only. They are not proof evidence, human
review, source review, accepted status, accepted refutation, or promotion
authority.

## Research Loop Memory And Scanner Metrics

The D.1 research-loop runtime surfaces report deterministic memory/scanner
metrics in attempt-memory indexes and scan reports:

- `attempt_count`: number of runtime attempts included in the measurement.
- `unique_direction_count`: number of normalized attempted directions.
- `repeat_failure_count`: number of failure clusters with more than one
  failure.
- `blocked_repeat_retry_count`: number of blocking repeat-retry policy
  findings.
- `candidate_counterexample_count`: candidate counterexample references in
  attempt evidence and failure records.
- `checked_counterexample_count`: checked counterexample references in attempt
  evidence and failure records.
- `draft_artifact_ref_count`: draft artifact references in attempt evidence.
- `handoff_ref_count`: handoff-bundle references in attempt evidence.
- `scanner_blocker_count`: blocking findings emitted by the loop scanner.

These metrics are operational signals for reviewing a bounded research loop.
They are not proof, source metadata, human review, verifier pass, gate pass,
accepted status, accepted refutation, or promotion authority.

The Phase E `cosheaf eval research-loop --json` command and ecosystem matrix
rows remain future work. Until then, D.1 metrics are available through runtime
attempt-memory and scan JSON only.

## Ecosystem Readiness Matrix

The three-repository readiness matrix is exposed through:

```bash
python scripts/ecosystem_smoke.py --matrix --cosheaf "python -m cosheaf.cli" --framework-root . --workspace-template-root ../tcs-cosheaf-workspace-template --public-kb-root ../tcs-kb-public --json
```

The active integration matrix rows cover framework local smoke,
framework verifier-evidence eval smoke, framework checked-evidence run-loop
eval, framework research-run loop eval, framework strategy-planner eval,
framework operator-session CLI smoke, framework operator-handoff dry-run
smoke, optional verifier availability, framework git-tag release smoke,
workspace-template install demo, workspace-template CLI-agent demo,
workspace-template research-run demo, workspace-template strategy demo,
workspace-template operator-session demo, workspace-template fake-provider
smoke, workspace-template verifier-evidence demo, public KB policy guard,
public KB checked-evidence policy docs, public KB strategy-plan policy docs,
public KB operator-handoff policy docs, and public KB verifier-policy
self-test coverage. The default git-tag release-smoke row uses the latest
published release target `v0.5.0`. Release-candidate checks for `v0.6.0` should
pass `--framework-tag v0.6.0` explicitly until publication closeout updates the
published baseline. The git-tag release-smoke row remains an opt-in network row
and is skipped unless `--include-network` is explicitly supplied.

Network rows remain opt-in through `--include-network`. When optional external
SAT/SMT/Lean/lake tools are unavailable, the optional verifier availability
row exits with code `77` and is counted as `skipped`, not `pass`. Matrix
failures identify the repository and command that failed.

These matrix results are release-readiness signals only. They do not create
human review, do not write accepted knowledge, do not promote artifacts, do
not call real hosted providers, and do not prove mathematical truth or
informal/formal semantic alignment.

## CLI

Run the default retrieval eval suite:

```bash
cosheaf eval retrieval
```

Use an explicit case file and JSON output:

```bash
cosheaf eval retrieval --cases evals/retrieval/cases.yaml --k 5 --json
```

Run the default context eval suite:

```bash
cosheaf eval context
```

Use an explicit case file and JSON output:

```bash
cosheaf eval context --cases evals/context/cases.yaml --json
```

The command reads repository YAML metadata and produces deterministic output.
The retrieval eval does not write `.cosheaf/memory` sidecars and does not
rebuild the SQLite index implicitly. The context eval does not rebuild the
SQLite index implicitly, but it does build context packs through the existing
context-pack writer.

The agent workflow, provider workflow, failure/counterexample, artifact
failure-memory, and verifier evidence evals currently have no CLI commands.
The checked-evidence and research-run loop evals have CLI commands:

```bash
cosheaf eval checked-evidence-run-loop --json
cosheaf eval research-run-loop --json
```

The checked-evidence and research-run loop evals use deterministic local
fixtures and do not require hosted providers, API keys, MCP, network, SAT, SMT,
Lean, or lake. Other Python-level evals may refresh `context/TASKS/<issue-id>/`
context packs, redacted provider logs under `.cosheaf/providers/`, or eval
fixtures under `.cosheaf/evals/`. Runtime outputs should not be committed.

## Limitations

- The harness is intentionally small and fixture-oriented.
- It does not use embeddings, real hosted model calls, external benchmark
  data, API keys, or network access.
- Fake-provider cases are deterministic local regressions, not hosted-provider
  proof that a real API is configured.
- Mocked OpenAI-compatible provider workflow cases exercise injected local
  transport fixtures, not live provider behavior.
- Optional MCP cases only cover the existing read-only whitelist surface; they
  do not make MCP required and do not authorize arbitrary shell or controlled
  writes.
- Verifier evidence eval cases use deterministic fake evidence records. They
  do not run external checkers and do not prove mathematical truth.
- It does not judge mathematical truth or informal/formal alignment.
- It does not replace validation, gatekeeper, verifier adapters, source review,
  human review, or accepted promotion.
