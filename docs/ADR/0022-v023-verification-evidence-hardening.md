# ADR 0022: v0.2.3 Verification Evidence Hardening

Status: Accepted

Date: 2026-06-14

## Context

`v0.2.2` published the Provider Transport + Agent Workflow Hardening release.
It made provider real-run behavior explicit and default-off, added provider
context-send policy checks, preserved worker failure/counterexample material,
expanded deterministic evals, and added three-repository smoke coverage.

The next project risk is not lack of provider access. It is ambiguity in
verification evidence:

- verifier requests can be confused with verifier results;
- candidate counterexamples can be confused with checked refutations;
- skipped optional-tool results can be overread as passes;
- Lean `#check` symbol/import resolution can be overread as informal/formal
  semantic alignment;
- promotion/readiness decisions can be hard to audit when evidence is spread
  across artifacts, sidecars, gate reports, and logs.

The project needs a conservative `v0.2.3` direction that deepens verification
evidence without claiming automatic theorem proving or expanding provider/MCP
authority.

## Decision

The next target is `v0.2.3 Verification Evidence Hardening`.

The milestone will focus on:

- auditing existing verifier adapters, result records, gate integration, and
  promotion evidence paths before changing schemas;
- defining a normalized evidence vocabulary that distinguishes
  `verifier_request`, `verifier_result`, `candidate_counterexample`, and
  `checked_counterexample`;
- keeping verifier result states explicit, including `pass`, `fail`, `error`,
  `skipped`, `unknown`, and not-applicable cases where relevant;
- improving SAT, SMT, plain Lean, and external Lean library reference checker
  ergonomics while keeping all external tools optional;
- preserving command, cwd, timeout, exit code, stdout/stderr log references,
  and tool-version metadata where available;
- improving failure/counterexample evidence workflows and review visibility;
- improving promotion-readiness reporting without changing promotion authority;
- maintaining three-repository smoke and policy coverage.

The first implementation task after this ADR is a verifier evidence status
audit. Runtime and schema changes must wait until that audit establishes the
current compatibility surface.

## Required Boundaries

- A `verifier_request` is not a verifier result.
- A skipped verifier result is not a pass.
- A candidate counterexample is not a checked counterexample.
- A Lean `#check` pass only means import and symbol resolution succeeded.
- Lean `#check` does not prove informal/formal semantic alignment.
- SAT/SMT/Lean backend absence must remain skipped or unavailable, not pass.
- Provider output remains untrusted review material.
- AI/provider review is not human review.
- Accepted knowledge still requires validation, gates, review where policy
  requires it, verifier evidence where applicable, and explicit promotion.
- Public KB accepted artifacts still require complete source metadata and
  human review.

## Non-Goals

This decision does not authorize:

- automatic theorem proving;
- automatic Lean/mathlib/CSLib proof checking of informal statements;
- automatic informal/formal semantic alignment;
- automatic accepted promotion;
- default-on real provider calls;
- real provider calls in CI or default tests;
- provider/MCP authority expansion;
- provider MCP tools;
- controlled-write MCP;
- direct accepted writes;
- replacing human review with AI/provider review;
- public KB mass imports;
- private conjectures or unreviewed LLM output in accepted public KB paths.

## Consequences

`v0.2.3` work should be split into small PRs:

1. Audit existing verifier evidence and formal-link surfaces.
2. Define the evidence taxonomy and compatibility plan.
3. Implement narrow evidence-record or reporting improvements.
4. Deepen optional SAT/SMT/Lean ergonomics with fake/mocked/tool-absence tests.
5. Improve failure/counterexample review workflows.
6. Improve promotion-readiness reporting.
7. Run three-repository readiness checks before a release candidate.

Documentation must stay conservative. Release notes may claim only implemented
and tested behavior. If external tools are missing, results must remain
skipped or unavailable rather than successful.
