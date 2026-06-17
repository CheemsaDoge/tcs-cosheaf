# ADR 0032: External Operator Campaign Harness

Status: accepted

Date: 2026-06-18

## Context

V15 added checker registry, checker sidecars, workflow cross-check reports,
evidence reports, proof/source/formalization gap reports, and deterministic
checker/cross-check eval coverage. Those surfaces make weak evidence and
missing obligations more visible to a human reviewer, but they still do not
create proof, source metadata, human review, accepted status, or promotion
authority.

The next useful capability is not autonomous theorem proving or an internal
hosted-agent runtime. It is a bounded way to run multiple external attempts
against one research issue while preserving context, budgets, outputs,
failures, scans, checks, and review handoff.

## Decision

V16 will introduce an external-operator campaign harness.

Cosheaf will act as the deterministic campaign controller:

- create and persist campaign records;
- export narrow task packets for external operators;
- import structured result packets;
- enforce budgets and stop conditions;
- scan outputs for unsafe paths, private leakage, secrets, and authority
  overclaims;
- summarize attempts through deterministic scorecards and handoff packets; and
- expose campaign evals for regression coverage.

External operators remain outside Cosheaf. They may be a human, Codex-like
tool, local script under a future whitelist, or a default-off provider path,
but Cosheaf will not treat any operator output as accepted knowledge.

## Authority Boundary

Campaign records, task packets, result packets, scorecards, scans, reports,
and handoffs are not:

- proof;
- source metadata;
- human review;
- verifier pass unless a real checker result explicitly records pass;
- gate pass;
- accepted status;
- accepted theorem/refutation;
- promotion authority.

Campaign success means only that the campaign satisfied its configured local
criteria. It does not prove the mathematical statement and does not authorize
accepted KB writes.

## Safety Boundary

The default campaign path must not require:

- hosted provider calls;
- API keys;
- network access;
- arbitrary shell execution;
- public KB writes;
- accepted KB writes; or
- private-context leakage in public mode.

Runtime outputs should remain under ignored `.cosheaf/campaigns/` paths unless
the user explicitly exports review-context reports. Exported review context is
still non-authoritative.

## Consequences

- V16 can support many attempts without embedding an autonomous agent runtime.
- Repeated attempts become inspectable and comparable instead of disposable
  chat logs.
- Budget exhaustion, repeated failure, unsafe output, and skipped checks become
  explicit states rather than hidden failures.
- The framework can later support hosted providers or MCP adapters without
  making them the source of truth.
- Public KB policy must reject campaign outputs as source metadata, accepted
  proof, human review, verifier/gate pass, accepted status, accepted
  theorem/refutation, or promotion authority.

## Rejected Options

- Treating a successful campaign as accepted proof.
- Treating external operator output as human review.
- Making hosted providers default-on or required in CI.
- Allowing campaign runtime to write accepted KB artifacts.
- Allowing arbitrary shell execution as the core campaign mechanism.
- Combining V16 campaign runtime with V17 memory learning or V18 v1.0 scope
  freeze before V16 is published.
