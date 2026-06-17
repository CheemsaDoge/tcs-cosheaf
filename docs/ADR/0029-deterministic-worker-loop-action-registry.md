# ADR 0029: Deterministic Worker Loop And Local Action Registry

## Status

Accepted for the v0.8.0 implementation line. This ADR describes the design
direction; actual implementation is scoped by the V12 plan and the repository
state at the time each phase starts.

## Context

v0.7.0 Bounded Research Loop + Attempt Memory provides dry-run planning,
external operator task/result protocol, runtime attempt memory, and loop
scanner/eval. The loop still refuses non-dry-run execution.

Without any execution capability, the loop is a planning and audit harness. The
next useful capability is local deterministic execution of safe repository
operations: memory search, context build, strategy next, validate, gate, eval,
scan, and handoff preview. These operations already exist as Cosheaf service
calls with deterministic JSON output. There is no need for hosted LLM,
arbitrary shell, or network access.

## Decision

v0.8.0 will add a deterministic local action registry and enable bounded
non-dry-run loop execution for whitelisted local actions only:

1. Typed `LocalActionRegistry` with static allowlist.
2. `cosheaf action list/describe/run` CLI.
3. `cosheaf research-loop run --execute-local-actions` for bounded local execution.
4. Worker profiles that bundle allowed actions without hosted models.
5. Deterministic eval and ecosystem smoke.

All actions remain non-authoritative review context. No action can write
accepted KB, create human review, mutate verifier results, call hosted
providers, execute arbitrary shell, or authorize promotion.

## Authority boundaries (unchanged)

- Local action success is not proof.
- Validate/gate/eval success is not human review.
- Loop success is not accepted status.
- Handoff export remains review context only.
- Failure memory remains research memory, not refutation authority.
- Public KB accepted artifacts still require source metadata and human review.
- No arbitrary shell, network, hosted provider, or promotion authority.

## Consequences

- The research loop becomes a usable local execution harness.
- External operators (Codex, human) can use the loop to run safe repository
  workflows deterministically.
- The system stays safely outside accepted-knowledge authority.
- Future v0.9.0+ may add bounded connector interfaces to external tools, but only
  after v0.8.0 local execution is stable and the allowlist model is proven.
