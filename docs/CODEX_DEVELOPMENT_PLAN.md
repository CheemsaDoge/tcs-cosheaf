# Historical Codex Development Plan

This document is historical project memory. It is superseded by
[`CODEX_DEVELOPMENT_PLAN_V11.md`](CODEX_DEVELOPMENT_PLAN_V11.md), which
records the current post-`v0.6.0` bounded research-loop and attempt-memory
plan. Earlier plans remain available for traceability only.

Do not use this file to select the next task. It remains in the repository for
traceability only because it describes earlier local-MVP planning and fixed
longplan work. If this file conflicts with `CODEX_DEVELOPMENT_PLAN_V11.md`,
the V11 plan controls.

Codex conversations are not project memory. If a decision, workflow
constraint, known limitation, or operator pitfall matters after context
compaction, record it in repository files.

## Historical Summary

The earlier plan moved TCS-Cosheaf from pre-MVP scaffold through:

- workspace-template productization;
- public KB policy/backlog work;
- deterministic librarian and context-pack v2;
- local orchestrator dry-run scaffolding;
- fake provider contracts;
- optional source ingestion and formal-link checking surfaces;
- release-hardening documentation for `v0.2.0`.

Those phases remain historical evidence. They do not override the current
post-`v0.2.0` direction.

## Current Override

The durable CLI-first direction remains:

- CLI is the first agent interface.
- Hosted provider support is planned but controlled, default-off, and tested
  with fake or mocked providers.
- MCP is optional adapter work and not a `v0.2.1` blocker.
- Skill is an operator runbook, not a source of truth.
- Agents, MCP tools, hosted workers, and CLI draft-write commands must not
  write accepted knowledge or bypass validation, gates, human review, and
  promotion.

Use [`CODEX_DEVELOPMENT_PLAN_V11.md`](CODEX_DEVELOPMENT_PLAN_V11.md) for
current task order and PR scope.
