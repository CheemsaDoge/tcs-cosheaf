# ADR 0035: Application Boundary Before Server And Website Surfaces

Status: proposed

Date: 2026-06-19

## Context

The v1.0.0 framework baseline is CLI-first. It already has a service layer for
workspace inspection, validation, gates, context packs, memory search, task
records, bundle submission, controlled draft writes, provider-send previews,
and provider calls. It does not yet have a stable `cosheaf.app` namespace that
future CLI, MCP, local dashboard, server, website, or forge code can share.

`cosheaf/cli.py` still owns too much orchestration and policy-sensitive helper
logic, especially artifact lifecycle moves, accepted promotion, provider
real-run preparation, terminal rendering, and error conversion.

## Decision

Introduce `cosheaf.app` as the stable Python application-usecase boundary
before adding server or website-backed actions.

The first implementation should be a thin facade over existing services and
domain modules. It should not mass-rename `cosheaf.services`, change CLI
commands, change schemas, or change JSON output. It should make future
non-CLI callers import app use cases instead of Typer command functions.

Initial app use cases should include:

- workspace info;
- repository and artifact validation;
- gate run;
- context build and show;
- memory cards and search;
- controlled draft writes;
- controlled review-request writes;
- bundle submit and reduce; and
- read-only promotion readiness where already supported.

Promotion writes, local command execution, MCP serving, provider real-run, and
Git/GitHub mutation should stay out of the first facade or remain explicitly
dry-run/read-only until their app request/result and negative-test coverage
exists.

## Authority Boundary

The app boundary is not a new authority source. It must not create proof,
source metadata, human review, verifier pass, gate pass, accepted status,
accepted theorem/refutation status, or promotion authority.

Skipped, unavailable, unsupported, and inconclusive results remain non-pass
states. AI, operator, workflow, campaign, benchmark, comparison, memory, and
static-report outputs remain review context or sidecar guidance unless they
enter accepted knowledge through existing review, gate, verifier, and
promotion rules.

## Consequences

- Future server and website work can call Python app functions instead of
  shelling out to CLI.
- CLI entrypoints can be slimmed one group at a time without changing command
  names or behavior.
- `cosheaf.services` remains compatible while the app facade becomes the
  higher-level usecase boundary.
- App facade tests must compare against existing service behavior and protect
  authority boundaries.
- Promotion and write-heavy surfaces require extra care and should move after
  the read/check facade is stable.

## Rejected Options

- Let future server code call `cosheaf.cli` directly.
- Rewrite `cosheaf.services` in one large rename.
- Move accepted-promotion writes before the read/check app facade exists.
- Add web/server/GitHub behavior before the shared app boundary is stable.
- Treat app output as accepted knowledge authority.
