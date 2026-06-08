# Evaluation

## Scope

Cosheaf evaluation commands are deterministic local regression checks for
retrieval and future context/orchestrator surfaces. They are not hosted
benchmarks, do not call LLMs, do not use network access, and do not change
artifact, review, gate, or promotion state.

The Phase 7 retrieval eval harness measures whether the existing local
artifact-card retrieval surface still returns expected records for small,
reviewable cases. It reuses `cosheaf.memory.search_artifact_cards`; it does
not introduce a new retrieval algorithm.

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

## CLI

Run the default retrieval eval suite:

```bash
cosheaf eval retrieval
```

Use an explicit case file and JSON output:

```bash
cosheaf eval retrieval --cases evals/retrieval/cases.yaml --k 5 --json
```

The command reads repository YAML metadata and produces deterministic output.
It does not write `.cosheaf/memory` sidecars and does not rebuild the SQLite
index implicitly.

## Limitations

- The harness is intentionally small and fixture-oriented.
- It does not use embeddings, hosted model calls, external benchmark data, or
  network access.
- It does not judge mathematical truth or informal/formal alignment.
- It does not replace validation, gatekeeper, verifier adapters, source review,
  human review, or accepted promotion.
