# ADR 0027: Operator Session And Review Handoff

Status: Accepted for the `v0.6.0` implementation line.

Date: 2026-06-16

## Context

The published `v0.5.0` release adds the Operator MCP + Codex Application Layer.
Cosheaf now has a CLI-first operator workflow, optional MCP tools, controlled
draft/review/runtime MCP writes, operator runbooks, a workspace demo, public KB
operator policy smoke, and an optional documentation-only operator Skill
package.

The remaining operational gap is reviewability across a whole operator session.
A maintainer should be able to answer:

- which issue was worked on;
- which CLI or MCP tools were used;
- which context, strategy, run, draft, review-context, and runtime records were
  referenced or written;
- which validate, gate, test, eval, or smoke checks ran;
- whether skipped checks stayed visibly skipped;
- whether private/public and readonly/writable boundaries were preserved; and
- what should be reviewed next.

Raw terminal transcripts or MCP logs are too noisy and can contain secrets,
private content, hidden reasoning markers, provider payloads, or absolute local
paths. A compact, deterministic, redacted handoff layer is needed, but it must
not become a new trust authority.

## Decision

Cosheaf will implement an Operator Session + Review Handoff layer for the
`v0.6.0` line.

The layer will be thin and deterministic:

- strict operator session DTOs and repository-local runtime storage;
- CLI commands to start, inspect, append safe references/checks to, scan, and
  finalize sessions;
- optional MCP session recording for whitelisted tools;
- a deterministic leak scanner for sessions and handoff candidates;
- handoff bundles generated from finalized sessions; and
- explicit review-context exports under `reviews/operator/`.

The CLI remains the human and CI oracle. MCP remains optional. Operator
sessions record metadata, bounded summaries, safe references, and check
statuses; they do not execute arbitrary commands or authorize writes outside
existing Cosheaf policy.

## Authority Boundary

Operator sessions, MCP session recordings, leak scanner reports, handoff
bundles, and handoff exports are review context only.

They must not:

- write accepted KB records;
- promote artifacts;
- mark or create human review;
- mutate verifier results;
- treat skipped as pass;
- mark gate, verifier, SAT, SMT, Lean, provider, MCP, eval, or network results
  as successful unless the corresponding command actually ran and passed;
- make provider calls default-on;
- require API keys in default tests or CI;
- store secrets, environment dumps, hidden reasoning, provider request/response
  payloads, or full private artifact text by default;
- turn public KB source metadata or human review into an operator-generated
  artifact; or
- claim automatic theorem proving or informal/formal semantic alignment.

`reviews/operator/<handoff-id>.yaml` is a review-context export. It is not a
human review record, verifier evidence, gate pass, accepted status, accepted
refutation, or promotion decision.

## Consequences

The `v0.6.0` line should make Codex-style and human operator work easier to
audit without widening accepted-knowledge authority.

Implementation tasks must include negative tests for:

- direct `kb/accepted/` write targets;
- private paths or private artifact IDs in public-only sessions;
- readonly public-root write attempts where relevant;
- skipped checks remaining skipped;
- blocking leak scanner findings preventing handoff export;
- human-review or promotion authority claims; and
- backward-compatible MCP behavior when no session ID is supplied.

Generated session state belongs under ignored `.cosheaf/operator-sessions/`
unless a task explicitly writes a review-context export under
`reviews/operator/`.

## Non-Goals

This ADR does not approve:

- production hosted multi-agent SaaS;
- a web UI;
- multi-user permission systems;
- default hosted provider calls;
- accepted promotion through sessions, MCP, or handoff bundles;
- human-review creation through sessions, MCP, or handoff bundles;
- verifier-result mutation through sessions, MCP, or handoff bundles;
- arbitrary shell tools;
- automatic theorem proving;
- automatic Lean/mathlib/CSLib semantic alignment; or
- replacing GitHub PR review.

## Follow-Ups

- [x] Land `docs/CODEX_DEVELOPMENT_PLAN_V10.md` and
  `docs/POST_V050_STATE_AUDIT.md`.
- [x] Add strict operator session DTOs and runtime storage.
- [x] Add the operator session CLI core.
- [x] Add optional MCP session recording.
- [x] Add the operator session leak scanner.
- [x] Add handoff bundle build/show commands.
- [x] Add handoff export to `reviews/operator/`.
- [x] Add downstream workspace-template and public KB policy integration.
- [x] Add deterministic ecosystem smoke rows.
- [x] Prepare and publish a conservative `v0.6.0` release only after implementation,
  downstream smoke, and release verification pass.
