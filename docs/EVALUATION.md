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
budgets. Both harnesses reuse existing runtime surfaces; they do not introduce
new retrieval or context-pack algorithms.

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

## Limitations

- The harness is intentionally small and fixture-oriented.
- It does not use embeddings, hosted model calls, external benchmark data, or
  network access.
- It does not judge mathematical truth or informal/formal alignment.
- It does not replace validation, gatekeeper, verifier adapters, source review,
  human review, or accepted promotion.
