---
name: cosheaf-operator
description: Use when operating TCS-Cosheaf repositories through CLI or optional MCP for issue-driven framework, workspace-template, or public-KB work. Covers required repo memory reads, safe context building, validation/gate checks, strategy/run provenance, controlled draft/review/runtime writes, PR summaries, and forbidden actions such as accepted writes, promotion, human-review spoofing, verifier-pass spoofing, private leakage, hosted-provider defaults, or agent-specific branch/PR prefixes.
---

# Cosheaf Operator

Use this skill as an operator runbook. It is documentation only: it does not
grant authority, change repository policy, or replace `AGENTS.md`, validation,
gates, human review, verifier evidence, or accepted promotion.

## Read First

Before changing files, read:

- `AGENTS.md`
- `README.md`
- `context/CURRENT_MILESTONE.md`
- `context/PROJECT_STATE.md`
- `docs/CODEX_WORKFLOW.md`
- `docs/EXTERNAL_OPERATOR_RUN_LOOP.md`
- `docs/OPERATOR_WORKSPACE_DEMO.md`
- `docs/MCP_SERVER.md` when using MCP

For public KB work, also read the public KB `AGENTS.md`, `docs/KB_POLICY.md`,
`docs/REVIEW_POLICY.md`, and `docs/OPERATOR_POLICY.md` if present.

## Operating Loop

1. Use one issue, one branch, one PR, and no `codex` or agent-specific prefix.
2. Inspect current state with `cosheaf workspace info --json`.
3. Establish baseline with `cosheaf validate --json` and
   `cosheaf gate run --json`.
4. Build bounded context with `cosheaf memory search ... --json`,
   `cosheaf context build <issue-id> --json`, and strategy commands when
   relevant.
5. Start a research run when auditable provenance is expected, then append
   command, artifact, and output records.
6. Write only explicitly scoped draft, proposal, review-context, or runtime
   records through controlled commands or whitelisted MCP tools.
7. Rerun required checks: usually `make lint`, `make typecheck`, `make test`,
   `make validate`, `make gate`, and `git diff --check`.
8. Open one PR with exact commands, outcomes, runtime-output paths, skipped
   rows, limitations, and authority-boundary confirmations.

## Tool Preference

Prefer CLI with `--json` for coding agents. Use MCP only when an MCP-capable
client needs whitelisted tool/resource calls. MCP remains an adapter over the
same service-layer policy; it is not a replacement for CLI/CI review.

## Allowed Output Areas

Use only task-scoped and policy-scoped paths, such as:

- `.cosheaf/` for ignored runtime output;
- `context/TASKS/<issue-id>/` for context packs;
- draft/private KB paths when the issue explicitly permits draft work;
- `sources/notes/` for draft source-note records;
- `reviews/requests/`, `reviews/runs/`, or `reviews/strategy/` for
  non-authoritative review-context exports.

## Forbidden Actions

Do not:

- write directly to `kb/accepted/` or `kb/public/accepted/`;
- promote artifacts through MCP or agent output;
- mark AI, MCP, provider, or operator output as `human_reviewed`;
- treat validation, gate, verifier, Lean, SAT, SMT, provider, MCP, strategy,
  memory, context, or run output as human review;
- treat skipped, unavailable, failed, or inconclusive results as passes;
- mutate verifier results outside real verifier workflows;
- expose arbitrary shell or unrestricted filesystem access through MCP;
- send private KB context to hosted providers without explicit policy,
  preview, configuration, network permission, credentials, and operator
  consent;
- store secrets, hidden reasoning, `.env` content, API keys, or private KB
  text in public PRs or public KB artifacts.

## PR Summary Shape

Include:

- issue and branch;
- summary and changed files;
- commands run and exact results;
- generated runtime paths and whether they are ignored;
- known limitations and skipped rows;
- interface, schema, artifact, and docs changes;
- gate result;
- confirmation that no accepted write, promotion bypass, human-review spoofing,
  verifier-pass spoofing, private leakage, hosted-provider default, or
  automatic theorem-proving claim was added.
