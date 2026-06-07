# ADR 0011: External Tooling Boundaries

## Status

Accepted

## Context

The current roadmap introduces four external repositories that could support
future work:

- Microsoft MarkItDown for document-to-Markdown source ingestion;
- Headroom for compression experiments;
- CodeGraph for code navigation and impact analysis;
- Understand-Anything for manual architecture visualization.

These tools were not part of the original core MVP scaffold. Adding them
without explicit boundaries would risk weakening TCS-Cosheaf's existing
knowledge governance model:

- YAML artifacts remain source of truth.
- Accepted knowledge requires validation, gates, human review, and explicit
  promotion.
- Public KB accepted artifacts require source metadata and human review.
- Worker, librarian, and orchestrator outputs cannot directly write accepted
  knowledge.
- Generated sidecars are rebuildable views, not project facts.
- Missing optional tools must not break core validation, gates, or tests.

The risky alternative is to add each tool opportunistically as a dependency,
runtime surface, or CI shortcut. That would blur the line between source
material, developer assistance, generated summaries, and accepted knowledge.

## Decision

Record external-tool boundaries before implementing any adapters or helpers.
The detailed policy lives in `docs/EXTERNAL_TOOLS.md`.

Tool decisions:

1. MarkItDown is accepted only as an opt-in source-ingestion adapter. It may
   convert local source files into staged Markdown with provenance metadata.
   It must not write accepted artifacts, human review records, verifier passes,
   or promotion evidence.
2. Headroom is deferred to Phase 5 or later as a default-off compression
   experiment. It must not change canonical retrieval scores, ArtifactCard
   ranking, retrieval audits, gate inputs, YAML artifacts, accepted KB, or
   project memory files.
3. CodeGraph is accepted only as optional developer tooling. It may support
   local code navigation or affected-test hints, but absence must not break CI
   and generated graphs must not become project truth.
4. Understand-Anything is allowed only for isolated manual onboarding or
   sanitized architecture visualization. It must not run in default CI,
   package install, runtime commands, retrieval, `.cosheaf/memory`, or KB truth
   paths.

Implementation constraints for future PRs:

- No default dependency is added by this ADR task.
- Any future dependency must be optional and absent-tool behavior must be
  tested.
- Network, URL, plugin, OCR, hosted model, and cloud-document capabilities are
  disabled by default unless a future PR adds explicit capability flags, tests,
  and audit logging.
- Tool outputs must stay in allowed staging, runtime, cache, or dev-only paths.
- Future generated caches must be ignored before any helper writes them.
- Missing tools skip or report unavailable in their explicit command path;
  they do not change core `validate`, `gate`, or test behavior.

## Consequences

The project can gain source-ingestion and developer-tool benefits without
changing the accepted-knowledge path. Future implementation tasks have clear
review boundaries and rollback triggers.

MarkItDown can support source-note and draft workflows, but curation and human
review remain required before any public accepted artifact changes.

Headroom can be evaluated without contaminating canonical retrieval or audit
records. Compressed text remains a view, not a ranking or gate input.

CodeGraph can improve developer navigation without becoming a runtime or CI
requirement. Normal verification remains the fallback.

Understand-Anything can be used only as a manual, isolated visualization aid on
sanitized inputs. It does not define memory, retrieval, artifact truth, or
architecture truth.

## Non-Goals

- Do not implement MarkItDown, Headroom, CodeGraph, or Understand-Anything in
  this ADR task.
- Do not add package dependencies or optional extras in this ADR task.
- Do not add CLI commands, scripts, CI jobs, schemas, gates, or runtime code.
- Do not alter artifact, review, verifier, formal-link, promotion, or
  public/private KB semantics.
- Do not claim that any external tool verifies mathematical correctness.
- Do not treat generated conversion output, compressed text, code graphs, or
  dashboard graphs as accepted knowledge or project memory.

## Follow-Up Requirements

Future tool PRs must remain separate issue/branch/PR units.

The next MarkItDown policy and adapter work must preserve the staging boundary:
converted Markdown is source material only. If a future adapter can write to
accepted KB, bypass human review, enable network/cloud inputs by default, or
weaken validation/gate behavior, it must be rolled back.

Any future public CLI, Python API, sidecar layout, dependency extra, cache
directory, or workflow helper must update the relevant docs, tests, and
`context/INTERFACE_REGISTRY.md` in the same PR.
