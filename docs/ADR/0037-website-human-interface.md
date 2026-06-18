# ADR 0037: Website Human Interface Boundary

Status: accepted

Date: 2026-06-19

## Context

Cosheaf has a stable CLI, app facade, forge boundary, and server-readiness
contract. The next line of work adds a human-facing website. Without an
explicit boundary, a website could be mistaken for source-of-truth data,
accepted-knowledge authority, or a place to handle GitHub credentials.

## Decision

Define the website as a human interface over sanitized Cosheaf export data.

The first website release is read-only. Repository YAML, JSON sidecars, and
generated reports remain the source of truth. CLI and `cosheaf.app` remain the
machine/oracle interfaces.

The website data contract is a deterministic static export containing:

- `site.json`
- `workspace.json`
- `artifacts.json`
- `issues.json`
- `graph.json`
- `gates.json`
- `context_packs.json`
- `reports.json`
- `authority_boundaries.json`

Public demo exports must not include private source notes, private unpublished
artifacts unless explicitly demo-only, API keys, tokens, raw provider prompts
with private context, or hidden reviewer identity.

Future write actions must call a backend. The backend must call `cosheaf.app`
or `cosheaf.forge`. Frontend code must not own GitHub credentials and must not
call GitHub APIs directly with user tokens.

## Authority Boundary

The website does not grant proof, source metadata, human review, verifier pass,
gate pass, accepted status, accepted theorem/refutation status, or promotion
authority. A website badge, graph edge, rendered context pack, issue display,
or gate summary is display context only.

Accepted knowledge still enters only through repository validation, gates,
source metadata, human review, and explicit promotion.

## Consequences

- The first website can be deployed as static read-only content.
- Public demo data needs an explicit sanitized export step before any frontend
  build consumes it.
- Future authenticated actions have a backend/app/forge path and no frontend
  token handling.
- Website tests and docs must preserve private-data and authority boundaries.

## Rejected Options

- Treat the website as source of truth.
- Let frontend code own GitHub tokens.
- Allow the first website release to write issues, PRs, reviews, gate results,
  verifier results, or accepted artifacts.
- Display private KB material in public exports by default.
