# TCS-Cosheaf Development Plan V18

Target: `v1.0.0 AI Math Collaborator MVP`

Status: Phase F release-candidate and publication closeout after Phase A scope
freeze, Phase B CLI/API polish, the workspace-template Phase C demo, Phase D
documentation/operator packaging, and Phase E security/authority/benchmark
audit.

## Goal

Release Cosheaf v1.0.0 as a Git-backed AI math collaborator MVP: safe,
reviewable, benchmarked, and useful for research exploration without
pretending to be an autonomous source of accepted truth.

## What v1.0.0 Means

A human or external AI operator can take a research issue, run Cosheaf, receive
context, plan attempts, execute bounded safe local actions, record failures and
evidence, generate a draft proposal, produce a review handoff, and compare the
outcome against benchmark expectations.

## Non-Goals

- No autonomous AI mathematician.
- No automatic theorem proving.
- No automatic accepted-artifact promotion.
- No AI-as-human-review.
- No default hosted LLM runtime.
- No formal correctness claim for arbitrary mathematics.
- No replacement for Lean, mathlib, CSLib, or human semantic-alignment review.
- No production SaaS or multi-user permission system.

## Frozen v1.0.0 Scope

Included in v1.0.0:

- CLI-first workspace validation, gates, indexing, context packs, and lifecycle
  governance.
- Reviewable workflow, draft proposal, handoff, cross-check, gap, campaign,
  memory, benchmark, comparison, and static-report surfaces.
- Optional verifier adapters and optional provider surfaces only under their
  existing explicit/default-off policies.
- Workspace-template canonical demo proving the safe collaborator loop.
- Public KB policy guards that reject workflow/campaign/checker/operator
  outputs as accepted proof, source metadata, human review, verifier pass, gate
  pass, accepted status, or promotion authority.
- Release audit evidence for authority, privacy, benchmark, stale-doc, and
  stale-issue boundaries.

Deferred to v1.1+:

- Web UI or hosted service.
- New model/provider integrations beyond existing explicit/default-off paths.
- Full Lean/mathlib/CSLib integration or semantic-alignment automation.
- Automatic theorem proving.
- Automatic public KB expansion.
- Multi-user auth/permission system.
- Large schema rewrites or new major subsystems.

Experimental/default-off surfaces:

- Real hosted provider transport and `provider real-run`.
- Optional MCP operator adapter.
- Optional MarkItDown, Headroom, CodeGraph, and other developer tooling.
- Optional SAT/SMT/Lean/lake execution paths.

## Stable v1.0 CLI Surface

The v1.0 stable user-facing surface is:

- `cosheaf interface list --json` for deterministic CLI surface discovery;
- `cosheaf workspace`, `validate`, `gate`, `index`, `context`;
- `cosheaf artifact`, `promotion`;
- `cosheaf workflow`, `checker`, `gap`;
- `cosheaf research-loop`, `research-run`;
- `cosheaf campaign`;
- `cosheaf memory`, `benchmark`, `compare`, `report`;
- `cosheaf operator session`;
- `cosheaf provider` fake/preview/config paths;
- optional `cosheaf mcp` paths as adapter surfaces, not the oracle.

Compatibility aliases remain until the CLI/API polish task documents or
deprecates them. `cosheaf gate run` is the preferred gate spelling; `cosheaf
gate` remains compatibility behavior during the v1.0 line. `cosheaf
research-run` is the preferred research-run provenance spelling; `cosheaf run`
remains compatibility behavior for existing scripts.

## Canonical MVP Demo

The v1.0 MVP demo is a workspace-template command:

```bash
make ai-math-collaborator-demo
```

It must use readonly public KB plus writable private draft overlay, run the
safe workflow/campaign/checker/memory/benchmark/report loop, write only ignored
runtime or draft/review-context outputs, and leave accepted/public KB content
unchanged. It must not require hosted LLMs, secrets, or network access except
for optional framework installation.

## Phase Structure

1. Phase A: post-v0.12.0 audit and v1.0 scope freeze (landed).
2. Phase B: CLI/API polish and deprecation cleanup (landed).
3. Phase C: end-to-end AI math collaborator demo (landed downstream).
4. Phase D: documentation and operator packaging (landed).
5. Phase E: security, authority, and benchmark release audit (landed).
6. Phase F: v1.0.0 release candidate and publication closeout (current).

## Phase A Scope

Phase A is documentation only:

- `docs/POST_V0120_STATE_AUDIT.md`;
- this V18 plan;
- `docs/ADR/0034-v100-ai-math-collaborator-mvp-scope.md`;
- roadmap, milestone, and project-state updates.

It verifies:

- package version is `0.12.0`;
- the `v0.12.0` tag and GitHub release are published;
- memory and benchmark surfaces exist;
- workspace-template active pins use `v0.12.0`;
- public KB CI/docs pins use `v0.12.0`;
- open issue/PR state across the three repositories; and
- accepted-write, human-review, source-metadata, verifier/gate, and promotion
  authority remain unchanged.

## Phase B Outline

Stabilize CLI/API discoverability before v1.0.0. This is polish, not a new
subsystem:

- consistent `--json` behavior;
- clear errors;
- repeated authority notices where users can misread output;
- documented aliases/deprecations;
- interface registry completeness;
- valid examples.

## Phase C Outline

Add the canonical workspace-template `make ai-math-collaborator-demo` path.
Framework changes are allowed only when directly required for demo stability.

## Phase D Outline

Finalize user and operator docs. CLI remains the oracle; skill and MCP docs are
operator guidance only and do not expand authority.

## Phase E Outline

Audit security, authority, benchmark, stale-doc, stale-issue, and release
readiness boundaries across all three repositories.

## Phase F Outline

Prepare and publish the conservative `v1.0.0` release only after Phase B-E
evidence is complete. Downstream pins and demos must be aligned before claiming
publication closeout.

## Required Verification Pattern

For framework PRs:

```bash
make lint
make typecheck
make test
make validate
make gate
git diff --check
```

For release/audit work, also run the relevant benchmark and ecosystem smoke
commands. Skipped rows must be listed as skipped and must not be counted as
passes.

