# ADR 0039: Web Governance Workbench

Status: accepted

Date: 2026-06-19

## Context

ADR 0037 defined the first website release as a read-only human interface over
sanitized export data. ADR 0038 defined the backend-only credential and audit
path for authenticated website actions. That boundary was safe, but it framed
the website too narrowly for the next product phase.

Cosheaf now needs a human workspace that can perform ordinary research,
review, promotion, forge, and audit work without making the browser a source
of truth or accepted-knowledge authority.

## Decision

Define the website target as the Cosheaf Human Governance Workbench.

The product roles are:

- Website: main human research, review, governance, promotion, forge/PR, and
  audit workspace.
- CLI: AI/Codex/operator/automation interface and scriptable oracle.
- Server: policy, auth, audit, repo-write, and GitHub bridge.
- Repository: source of truth.

The Workbench may execute human review and accepted/refuted/obsolete promotion
workflows only through backend-enforced policy checks, explicit confirmation,
audited repository writes, and Git/GitHub review flow where relevant.

Static showcase mode remains valid but incomplete. It is a read-only public or
local explanation mode, not the full web product.

## Authority Rules

- Repository files remain the source of truth.
- Frontend state is never source of truth.
- Website display output is never proof, source metadata, human review,
  verifier pass, gate pass, accepted status, refutation status, or promotion
  authority.
- Web actions must call `cosheaf.server -> cosheaf.app -> storage/forge`.
- Direct frontend YAML mutation is forbidden.
- Browser-side GitHub token storage is forbidden.
- Browser code must not call GitHub APIs directly with user tokens.
- Accepted/refuted/obsolete promotion requires explicit human review state and
  ordinary Cosheaf policy checks.
- Gate pass, verifier pass, GitHub PR merge, audit output, and AI/Codex output
  do not create accepted authority by themselves.
- Every write-class action must support preview before confirm and produce a
  redacted machine-readable audit entry.
- Failed, skipped, unavailable, and not-run checks must stay distinct from
  pass.

## Modes

Local Workbench mode is for a single researcher running the server on loopback
with explicit write enablement. It may use the active repository root, local
actor identity, local git state, and local forge credentials after preview and
confirmation. It still must audit writes and enforce review/promotion policy.

Hosted Workbench mode is a future collaborative deployment. It must use
server-side authentication, role checks, server-owned checkout/cache state,
branch/PR write flows, and backend-held GitHub App or OAuth credentials.
Hosted mode must not expose GitHub tokens to the browser and must not write
directly to `main`.

## Action Taxonomy

Workbench actions use this taxonomy:

- Read actions inspect repository or export state without writes.
- Preview actions compute plans, diffs, warnings, and blockers without writes
  or network mutation.
- Local repo write actions create or update repository records through backend
  app/storage paths.
- Git/forge actions create branches, commits, pushes, and PR plans through the
  forge boundary.
- GitHub actions create or update GitHub issues/PRs through backend-held
  credentials only.
- Review/promotion actions record explicit human decisions and promote
  artifacts only through policy-checked workflows.

## Target UX Surfaces

The target Workbench surfaces are dashboard, issues, artifacts, context, gates,
evidence, review, promotion, forge/PR, and audit.

Human-facing Workbench UI should support English and Simplified Chinese. If a
later implementation slice cannot complete full bilingual UI without delaying
authority-critical work, Chinese-first UI copy is an acceptable temporary
fallback and English localization should remain tracked in a follow-up issue or
PR acceptance checklist as deferred polish. Any implementation PR that ships
Chinese-first fallback must open or link a follow-up issue titled `Complete
Workbench English localization` and list the localization gap under its known
limitations.

## Consequences

- Future web work is not a showcase-only effort.
- Runtime tasks must add write endpoints behind typed DTOs, preview/confirm,
  policy checks, audit, and tests.
- Static export and public demo mode remain available for explanation and
  inspection.
- Review and promotion from the web are allowed only as human-interface
  workflows through Cosheaf policy, not as browser authority.
- Frontend implementation must avoid direct YAML writes and token storage.

## Rejected Options

- Keep the website permanently read-only.
- Treat static website output as accepted knowledge evidence.
- Let frontend code mutate YAML or store GitHub tokens.
- Treat gate/verifier/GitHub/AI output as human review or accepted authority.
- Collapse local and hosted modes into one ambiguous security model.
