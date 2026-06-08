# ADR 0012: Source Ingestion Boundary

## Status

Accepted

## Context

TCS-Cosheaf needs a controlled way to prepare source material for public KB
work. MarkItDown is a plausible future adapter for converting local source
files into Markdown, but source conversion is not the same as knowledge
acceptance.

The project already treats YAML artifacts, source metadata, review records,
gate reports, verifier evidence, and explicit promotion as the authority for
accepted knowledge. Letting a converter write accepted artifacts, human review
records, verifier passes, or promotion evidence would weaken that boundary.

The public KB also requires complete source metadata and human review for
accepted artifacts. Validation and gates are workflow evidence, not human
review.

## Decision

Create a dedicated source-ingestion policy before implementing a MarkItDown
adapter. The detailed policy lives in `docs/SOURCE_INGESTION.md`.

Source ingestion is staging only:

1. MarkItDown may later convert local source files to Markdown for review.
2. Converted Markdown must preserve provenance: original path, input hash,
   converter version, timestamp, options, warnings, output path, and execution
   metadata where applicable.
3. Converted output may feed source notes, explorer tasks, or draft proposals.
4. Converted output cannot become accepted artifact truth without artifact
   source metadata, validation, gates, human review where required, and
   explicit promotion.
5. URL, OCR, plugins, LLM vision, and Azure Document Intelligence remain
   disabled by default.
6. Untrusted input must run through a bounded subprocess or documented sandbox
   boundary.

No adapter code, dependency, CLI command, schema, gate behavior, verifier
behavior, promotion behavior, or public/private KB behavior changes in this
policy task.

## Consequences

Future MarkItDown implementation work has a narrow review surface. It can add
an optional local-file conversion command without confusing conversion output
with accepted knowledge, verifier evidence, or human review.

The default framework install remains dependency-light. Missing MarkItDown
will be reported only by an explicit future ingest command and must not affect
core validation, gates, tests, context packs, index rebuilds, or promotion.

Public KB source-note and foundation workflows can use staged conversions as
review aids while preserving the existing accepted-knowledge boundary.

## Non-Goals

- Do not implement MarkItDown in this ADR task.
- Do not add MarkItDown or any ingestion extra to package dependencies.
- Do not add `cosheaf ingest` CLI commands in this task.
- Do not add or change schemas, gates, verifiers, promotion semantics, or
  workspace root semantics.
- Do not touch public KB artifacts.
- Do not claim source ingestion performs theorem proving, formal verification,
  or human review.

## Follow-Up Requirements

A future MarkItDown adapter PR must:

- keep MarkItDown optional;
- test unavailable-tool behavior;
- test path-boundary enforcement;
- test that accepted KB paths are not written;
- record provenance metadata;
- disable URL, OCR, plugins, LLM vision, and cloud-document capabilities by
  default;
- update `context/INTERFACE_REGISTRY.md` if it adds CLI commands, Python APIs,
  sidecar formats, or optional dependency extras.
