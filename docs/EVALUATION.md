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
harness. These harnesses reuse existing runtime surfaces; they do not introduce
new retrieval, context-pack, provider, MCP, or orchestration algorithms.

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

The agent workflow eval currently has no CLI command. Running it from Python
may refresh `context/TASKS/<issue-id>/` context packs and redacted fake-provider
logs under `.cosheaf/providers/`. These are runtime outputs and should not be
committed.

## Limitations

- The harness is intentionally small and fixture-oriented.
- It does not use embeddings, real hosted model calls, external benchmark
  data, API keys, or network access.
- Fake-provider cases are deterministic local regressions, not hosted-provider
  proof that a real API is configured.
- Optional MCP cases only cover the existing read-only whitelist surface; they
  do not make MCP required and do not authorize arbitrary shell or controlled
  writes.
- It does not judge mathematical truth or informal/formal alignment.
- It does not replace validation, gatekeeper, verifier adapters, source review,
  human review, or accepted promotion.
