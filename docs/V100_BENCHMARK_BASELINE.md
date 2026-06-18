# V100 Benchmark Baseline

Date: 2026-06-18

Command:

```bash
python -m cosheaf.cli benchmark run --suite regression --json
```

Run ID:

```text
benchmark.regression.r19700101.t000000z
```

Benchmark runs are deterministic regression evidence only. They are not proof,
source metadata, human review, verifier pass, gate pass, accepted status,
accepted theorem/refutation status, or promotion authority.

## Aggregate Metrics

| Metric | Value |
| --- | ---: |
| passed | `true` |
| pass_count | `6` |
| fail_count | `0` |
| skipped_count | `3` |
| retrieval_precision_at_k | `1.0` |
| context_relevance_score | `1.0` |
| workflow_completion_rate | `1.0` |
| checker_matrix_accuracy | `1.0` |
| failure_reuse_rate | `1.0` |
| budget_stop_accuracy | `1.0` |
| authority_violation_count | `0` |
| private_leak_count | `0` |
| review_handoff_validity | `1.0` |

Safety flags:

- skipped_rows_are_passes: `false`
- accepted_write_performed: `false`
- yaml_artifacts_mutated: `false`

## Component Baseline

| Component | Passed | Cases | Skipped | Notes |
| --- | --- | ---: | ---: | --- |
| retrieval | `true` | 2 | 0 | hit@5 `1.0`, forbidden hits `0` |
| context | `true` | 2 | 0 | required artifact hit `1.0`, private leakage `0` |
| checker_crosscheck | `true` | 8 | 1 | skipped/inconclusive rows remain not-pass |
| reviewable_workflow | `true` | 6 | 1 | handoff scanner and overclaim guards active |
| research_loop | `true` | 10 | 1 | retry, scanner, policy, and budget guards active |
| campaign | `true` | 4 | 0 | budget and operator-contract checks active |

## Baseline Interpretation

This baseline is suitable for V18 release-candidate comparison. It does not
mean the framework proves mathematics, replaces human review, or permits
accepted promotion. Phase F must re-run the benchmark and ecosystem smoke
before tagging `v1.0.0`.

