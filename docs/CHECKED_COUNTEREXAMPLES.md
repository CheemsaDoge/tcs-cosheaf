# Checked Counterexamples

## Purpose

Checked counterexample evidence separates two things that were previously easy
to confuse:

- a `counterexample_candidate` in a WorkerBundle, failure log, artifact note,
  or manual note; and
- a durable `checked_counterexample_evidence` record saying how a specific
  candidate was checked.

Checked evidence is evidence for review only. It is not human review, accepted
refutation, accepted status, proof, gate success, verifier pass by itself, or
promotion authority.

## Record Shape

The v1 schema is `schemas/counterexample_evidence.schema.json`. The Python
model is `CheckedCounterexampleEvidenceRecord` in
`cosheaf.verification.counterexample_evidence`.

Required fields:

```yaml
schema_version: 1
evidence_id: checked-counterexample.<target>.<candidate>.h<digest>
target_artifact_id: claim.example
candidate_id: candidate.example
candidate_source: worker_bundle | failure_log | artifact | manual_note | verifier
check_method: verifier_result | manual_review_reference | executable_check | proof_sketch_review | other
checked_result: checked_refutes | checked_does_not_refute | inconclusive | error | skipped
created_at: 2026-06-15T00:00:00Z
checker: checker label
limitations:
  - Checked counterexample evidence is evidence for review only; ...
```

`verifier_evidence_ids`, `review_record_paths`, and `evidence_paths` default to
empty lists. A `checked_refutes` record must include at least one of those
supporting references. A `skipped` record must explicitly say skipped is not
pass evidence.

All paths must be repository-local and must not point at accepted KB paths.

## CLI

Validate without writing:

```bash
cosheaf counterexample evidence validate --input-json evidence.json --json
```

Stage review evidence:

```bash
cosheaf counterexample evidence stage --input-json evidence.json --json
cosheaf counterexample evidence stage --input-json evidence.json --dry-run --json
```

Show staged evidence:

```bash
cosheaf counterexample evidence show \
  --evidence checked-counterexample.claim.example.candidate.example.habc123 \
  --json
```

Staging writes only to:

```text
reviews/evidence/checked-counterexamples/<evidence-id>.yaml
```

The command refuses authority-spoofing fields such as `human_reviewed`,
`review_state`, `accepted`, `artifact_status`, and `promote`.

## Context And Readiness

Context packs render visible checked evidence in `CONTEXT.md` and
`KNOWN_FAILURES.md`, and record it in `RETRIEVAL_AUDIT.json` under
`checked_counterexample_evidence`.

`--public-only` context excludes private checked evidence text and private
target artifact IDs.

Promotion readiness reports checked evidence as a warning reason only. The
warning can help reviewers focus on a possible refutation, but it is not a
promotion blocker by itself and does not replace verifier, gate, review, or
promotion policy.

## Eval

The deterministic eval harness is:

```bash
cosheaf eval checked-evidence-run-loop --json
```

Default cases live in:

```text
evals/checked_evidence_run_loop/cases.yaml
```

The eval checks candidate-vs-checked separation, supporting evidence for
`checked_refutes`, skipped-not-pass behavior, non-refuting `inconclusive` and
`error` outcomes, and accepted-write non-authority. It does not call hosted
providers, MCP, SAT, SMT, Lean, lake, or network tools.
