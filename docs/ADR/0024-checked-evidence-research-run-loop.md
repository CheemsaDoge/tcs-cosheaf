# ADR 0024: Checked Evidence And Research Run Loop

Status: Accepted for the `v0.3.0` implementation line.

Date: 2026-06-15

## Context

The `v0.2.x` series established the CLI-agent, provider, verifier evidence,
and artifact failure-memory foundation. It also made several boundaries
explicit:

- WorkerBundle counterexample candidates are review-only metadata.
- Verifier evidence records are not human review and do not authorize
  promotion.
- Artifact failure memory is non-authoritative research memory.
- Provider and MCP surfaces do not grant accepted-write or promotion authority.
- CLI remains the primary interface for external coding agents.

The missing next layer is checked evidence that can be reviewed without being
mistaken for accepted knowledge, plus a reproducible research-run ledger that
lets an external operator record what was done.

## Decision

`v0.3.0` will add two non-authoritative surfaces:

1. Checked counterexample evidence.
2. Research run records.

Checked counterexample evidence records will distinguish proposed
counterexample candidates from evidence that a specified method checked a
candidate. A checked evidence record may cite verifier evidence, review record
paths, executable evidence, or other repository-local evidence paths. It will
not mark human review, accepted status, artifact refutation, or promotion by
itself.

Research run records will capture external-operator provenance: issue,
operator kind, start/end state, commits, workspace/context references, command
records, artifacts touched, controlled write outputs, verifier evidence,
checked evidence, failure-log additions, validation/gate reports, PR/issue
references, limitations, and replay plans. Runtime sidecars remain under
`.cosheaf/` by default, with controlled review export as a separate command.

The intended operator model is CLI/Git first. Codex-style agents call CLI
commands, edit files, run verification, open PRs, and record research runs.
Cosheaf will not embed GPT, Claude, or any hosted model as the default runtime
for this line.

## Boundaries

Checked evidence is not:

- proof by itself;
- human review;
- an accepted refutation;
- accepted artifact status;
- promotion evidence by itself;
- automatic artifact rewriting;
- automatic formal/informal semantic alignment.

Research run records are not:

- proof;
- verifier pass;
- gate pass;
- human review;
- accepted status;
- promotion authorization;
- hidden reasoning storage.

Provider and MCP behavior remains unchanged in this line. Hosted provider
calls remain explicit, default-off, policy-scoped, previewed, consented, and
excluded from CI/default tests. MCP remains optional and non-blocking.

Skipped verifier, provider, SAT, SMT, Lean, lake, optional-tool, network, or
operator steps remain skipped, not pass.

## Consequences

Positive consequences:

- Candidate counterexamples and checked evidence become visibly distinct in
  CLI, context, readiness reports, and evals.
- External operators gain a reproducible run ledger without gaining accepted
  write, review, gate, verifier, or promotion authority.
- Downstream workspace demos can show a complete CLI/Git research loop.
- Public KB policy can cite checked evidence records while preserving source
  metadata and human-review requirements for accepted public knowledge.

Costs and risks:

- More repository-controlled metadata surfaces must be kept deterministic and
  redacted.
- CLI and docs must repeatedly state that checked evidence is evidence for
  review, not human review or accepted refutation.
- Public-only context and exported run records need explicit leakage tests.
- The release must avoid production-readiness, automatic theorem proving, and
  semantic-alignment claims.

## Follow-Up Work

- Implement `checked-counterexample-evidence-core`.
- Implement `research-run-record-cli-core`.
- Update external-operator docs and downstream workspace/public KB surfaces.
- Add checked-evidence/run-loop evals and three-repository smoke coverage.
- Prepare the `v0.3.0` release candidate only after implementation and
  downstream alignment pass.
