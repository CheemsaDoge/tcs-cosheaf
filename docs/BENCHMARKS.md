# Benchmarks

V17 Phase C adds a deterministic benchmark suite aggregator over existing local
eval harnesses.

Benchmarks are regression evidence only. They are not proof, source metadata,
human review, verifier pass, gate pass, accepted status, accepted
theorem/refutation, or promotion authority.

## Commands

```bash
cosheaf benchmark list --json
cosheaf benchmark run --suite smoke --json
cosheaf benchmark report <run-id> --out reviews/benchmark/smoke.md --json
```

Supported suites:

- `smoke`
- `regression`
- `authority_negative`
- `private_boundary`
- `research_loop`
- `campaign`
- `review_workflow`

Runs are written under ignored runtime storage:

```text
.cosheaf/benchmark-runs/<run-id>/run.json
```

Reports render from existing run sidecars. A `.json` output path writes the run
JSON; any other safe repository-local path writes a short Markdown report.
Accepted KB paths are refused.

## Metrics

The v1 aggregate metrics are:

- `pass_count`
- `fail_count`
- `skipped_count`
- `retrieval_precision_at_k`
- `context_relevance_score`
- `workflow_completion_rate`
- `checker_matrix_accuracy`
- `failure_reuse_rate`
- `budget_stop_accuracy`
- `authority_violation_count`
- `private_leak_count`
- `review_handoff_validity`

`skipped_count` is reported separately. Skipped, unsupported, unavailable, and
inconclusive rows are not passes.

## Boundaries

Benchmark commands do not call hosted providers, use network access, require API
keys, mutate YAML artifacts, write accepted KB content, create human review,
fabricate source metadata, mutate verifier results, mark gates as passing, or
promote artifacts.
