# Source Ingestion

Source ingestion is a staging workflow for public source material. It helps
maintainers prepare source notes, explorer tasks, and draft proposals, but it
does not create accepted knowledge.

## Boundary

Source ingestion is not validation, gatekeeping, verification, human review, or
promotion. Converted source material cannot become artifact truth unless a
later artifact PR adds complete source metadata, passes validation and gates,
receives human review where policy requires it, and uses the accepted
promotion workflow.

The accepted-knowledge path remains:

1. Write or update artifact YAML.
2. Record source metadata in the artifact.
3. Run validation and gates.
4. Record required human review.
5. Promote accepted knowledge through the explicit promotion workflow.

An ingestion result may help with steps 1 or 2, but it does not satisfy steps
3, 4, or 5.

## MarkItDown Role

Microsoft MarkItDown is exposed through an optional local-file conversion
adapter. Its role is to convert repository-local source files, such as PDFs or
Office documents, into staged Markdown for review.

The adapter stays optional. The default framework install, CI, validation,
gates, promotion, index rebuilds, context packs, and verifier flows continue to
work when MarkItDown is absent.

## CLI Surface

The MVP command is:

```text
cosheaf ingest convert <path>
cosheaf ingest convert <path> --out <dir>
cosheaf ingest convert <path> --metadata-json
cosheaf ingest convert <path> --repo-root <path>
```

By default, converted Markdown and provenance metadata are written under
`.cosheaf/ingest/`. `--metadata-json` prints the same provenance metadata to
stdout. If MarkItDown is not installed, the command exits nonzero with install
guidance; this unavailable result is not a validation, gate, verifier, or
promotion pass.

This command is for trusted local files already staged in the repository. It
does not provide a sandbox for hostile documents. Processing untrusted source
files still requires a future bounded subprocess or documented sandbox
boundary.

## Allowed Inputs

The default ingestion surface is repository-local files or explicitly allowed
local source directories. Remote URL ingestion, plugins, OCR, LLM vision, and
Azure Document Intelligence are disabled by default and require separate future
capability flags, tests, audit logging, and review.

The MVP local adapter runs through the optional Python package interface and is
not a sandbox. A future sandboxed implementation must record the command,
working directory, timeout, exit code, stdout/stderr logs when applicable, and
tool version metadata when available.

## Allowed Outputs

Converted Markdown and metadata may be written only to staging or runtime
locations such as:

- `sources/raw/` for explicitly staged original source files.
- `sources/markdown/` for converted Markdown plus provenance metadata.
- `sources/notes/` for source-note drafts or review notes.
- `.cosheaf/ingest/` for local runtime output that should not be committed.

Persisted source notes or curated source metadata may be committed only through
the repository policy that owns those files.

## Provenance

Every converted output must keep provenance sufficient for review:

- original repository-local path or approved source path;
- input SHA-256 hash;
- converter package name and version when available;
- conversion timestamp;
- command options and capability flags;
- warnings emitted by the converter;
- output path;
- exit code and log paths when a subprocess is used.

If provenance cannot be recorded, the conversion result must remain runtime
scratch material and must not be used as review evidence.

## Prohibited Behavior

Source ingestion must not:

- write to `kb/accepted/`, `kb/public/accepted/`, or any accepted KB root;
- create, promote, or mark an artifact as accepted;
- mark `review.state` as `human_reviewed` or `accepted`;
- create human review records;
- create verifier `pass` results;
- bypass source metadata requirements;
- copy private material into public KB paths;
- claim Lean, CSLib, mathlib, SAT, SMT, or theorem-proving verification.

Converted Markdown is source material. It may feed source notes, explorer
tasks, or draft proposals only. It is not accepted artifact truth.

## Review And Gate Interaction

Validation and gates may later check staged metadata shape or path safety for a
specific ingest command, but ingestion output itself is never human review.
Validation or gate success is also not a substitute for human review.

Formal links remain metadata unless a real checker verifies them and records
evidence. Planned formal links in artifacts or notes do not mean Lean has
checked anything.

## Rollback Triggers

Disable or revert a source-ingestion adapter if it can:

- write accepted KB paths;
- bypass review, gates, or promotion;
- enable URL, OCR, plugin, LLM vision, or cloud-document inputs by default;
- weaken artifact source metadata policy;
- make core validation, gates, tests, or package install depend on MarkItDown.
