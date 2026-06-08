# External Tool Boundaries

This document records decisions for optional external tools that may support
future TCS-Cosheaf workflows. These tools are not project truth. YAML
artifacts, review records, gate reports, verifier evidence, and explicit
promotion remain the authority for accepted knowledge.

License information below was checked from GitHub repository metadata on
2026-06-07. Re-check license and packaging details before adding any dependency
or implementation.

## Decision Summary

| Tool | Decision | Default State | Allowed Phase | License |
| --- | --- | --- | --- | --- |
| Microsoft MarkItDown | Accepted only as opt-in source ingestion. | Disabled, not installed by default. | Phase 2 source-ingestion adapter. | MIT |
| Headroom | Scaffolded as a default-off compression experiment boundary. | Disabled, not installed by default. | Phase 5 developer experiment. | Apache-2.0 |
| CodeGraph | Accepted as optional developer tooling only. | Not part of runtime or CI requirements. | Developer tooling after boundary docs. | MIT |
| Understand-Anything | Manual isolated onboarding only. | Not installed, not run by default. | Release/showcase docs or dev tooling docs only. | MIT |

## Global Rules

- Do not add any of these tools as default package dependencies in this task.
- Do not make validation, gates, promotion, artifact loading, or accepted KB
  state depend on these tools.
- Do not let tool output write directly to `kb/accepted/`,
  `kb/public/accepted/`, `reviews/human/`, artifact schemas, or gate truth.
- Do not treat generated summaries, compressed text, code graphs, or dashboards
  as source of truth.
- Missing tools must degrade gracefully. They may be reported as unavailable or
  skipped in their own explicit command path, but must not break core
  `validate`, `gate`, or tests.
- Any future command that invokes an external tool must record enough metadata
  to audit what happened: command, working directory, inputs, outputs, timeout,
  exit code, logs, and tool version or revision when available.
- Network, URL, hosted model, OCR, plugin, and cloud-document capabilities are
  disabled by default unless a future PR adds explicit capability flags, tests,
  and audit logging.

## MarkItDown

Repository: `microsoft/markitdown`

Decision: accept as an opt-in local source-ingestion adapter. MarkItDown may
convert local source files such as PDFs, Office documents, HTML, CSV, JSON, XML,
or text into staged Markdown for review.

Implemented surface:

```text
cosheaf ingest convert <path>
cosheaf ingest convert <path> --out <dir>
cosheaf ingest convert <path> --metadata-json
cosheaf ingest convert <path> --repo-root <path>
```

The command defaults to `.cosheaf/ingest/` runtime output and writes a Markdown
file plus deterministic provenance metadata when MarkItDown is installed. If
MarkItDown is absent, it exits nonzero with install guidance. MarkItDown is not
a default dependency.

MarkItDown output is source material, not accepted knowledge. Converted
Markdown may support source notes, private draft proposals, or explorer tasks.
It must not directly create accepted artifacts, human review records, verifier
passes, or promotion evidence.

Allowed outputs for a future adapter:

- `sources/raw/` for copied or staged original source material when explicitly
  requested by a repository policy.
- `sources/markdown/` for converted Markdown and deterministic metadata.
- `sources/notes/` or equivalent source-note staging paths.
- `.cosheaf/ingest/` for runtime conversion output that should not be committed.

Disallowed behavior:

- Write to `kb/accepted/` or `kb/public/accepted/`.
- Mark any statement as accepted, reviewed, verified, or proven.
- Use URL, YouTube, network, plugin, OCR, Azure, or LLM-vision inputs by
  default.
- Copy private material into public KB paths.

Install surface: documented manual install only for the current MVP, for
example `pip install markitdown`. The default framework install must continue to
work without MarkItDown.

Fallback: if MarkItDown is not installed, the explicit ingest command reports
unavailable with install guidance and exits nonzero. Core validation and gates
must continue normally.

Rollback trigger: remove or disable the adapter if it can write accepted KB,
promote artifacts, bypass review, use network/cloud capabilities by default, or
weaken source metadata policy.

## Headroom

Repository: `chopratejas/headroom`

Decision: scaffold as a Phase 5 default-off developer experiment boundary.
Headroom may be useful later for compressing long logs, tool outputs,
temporary RAG chunks, or local developer-agent context, but it must not enter
canonical retrieval or knowledge governance paths.

Implemented surface:

```text
python scripts/dev/headroom_probe.py --source <repo-local-noncanonical-text> --json
python scripts/dev/headroom_probe.py --enable --source <repo-local-noncanonical-text> --json
python scripts/dev/headroom_probe.py --enable --strict --source <repo-local-noncanonical-text> --json
```

The probe is disabled unless `--enable` is provided. When disabled, it records
`status: disabled`, `fallback: use_original_text`, and exits 0 without looking
for Headroom. When enabled, it first checks the source path against the
noncanonical-input allowlist. If the path is refused, it exits nonzero without
checking or invoking Headroom. If the path is allowed but Headroom is absent,
it reports `status: unavailable`, `fallback: use_original_text`, and exits 0
unless `--strict` is provided. When Headroom is present, this scaffold records
availability and version metadata only; it does not run an actual compression
subcommand.

Allowed surfaces:

- Local experiments that compare compressed and uncompressed views.
- CI log summarization only if the original logs remain available.
- Temporary, explicitly labeled noncanonical summaries.
- Developer-only probe metadata for `.cosheaf/logs/`,
  `.cosheaf/tasks/.../stdout.txt`, `.cosheaf/tasks/.../stderr.txt`,
  `.cosheaf/orchestrator/.../stdout.txt`,
  `.cosheaf/orchestrator/.../stderr.txt`, and `.cosheaf/dev/headroom/`.

Disallowed behavior:

- Change ArtifactCard ranking, retrieval scores, PageRank weights, gate inputs,
  YAML artifacts, accepted KB, or review records.
- Replace `RETRIEVAL_AUDIT.json` or any other audit record with compressed
  text.
- Run a learning or write-back mode against `AGENTS.md`, `CODEX_WORKFLOW.md`,
  ADRs, artifact YAML, or project memory files.
- Become a default runtime, CI, or package dependency.
- Compress or rewrite source notes, review records, formalization metadata,
  schemas, gate reports, memory sidecars, index outputs, accepted artifacts, or
  any YAML file.

Install surface: no default install. Any experiment must be explicitly enabled
and tested with the dependency absent.

Fallback: when unavailable, compression experiments skip and the canonical
uncompressed workflow remains unchanged.

Rollback trigger: disable immediately if compressed text affects canonical
retrieval, gates, YAML, accepted knowledge, project memory files, or review
records.

## CodeGraph

Repository: `colbymchenry/codegraph`

Decision: accept as optional developer tooling for code navigation and impact
analysis. CodeGraph may help developers inspect dependencies, choose affected
tests, or understand implementation impact, but it is not product runtime.

Allowed future surfaces:

- `docs/DEV_TOOLING.md` guidance.
- `scripts/dev/codegraph_probe.py`, a developer-only availability probe that
  reports `fallback: run_full_verification` when CodeGraph is unavailable.
- Optional affected-test hints that fall back to full checks.

Disallowed behavior:

- Become a runtime Python dependency.
- Become required for CI, validation, gates, indexing, retrieval, or context
  generation.
- Write generated graphs, indexes, or analysis output into project truth files.
- Replace `make test`, `make validate`, `make gate`, or human review.

Install surface for future work: manual developer install or optional dev-tool
probe only. Generated `.codegraph/` data must be ignored before any helper can
write it.

Fallback: if unavailable or stale, dev helpers print unavailable/skipped status
and preserve the normal full verification path.

Rollback trigger: remove helper integration if CodeGraph absence breaks CI or
if generated code graphs become a source of truth.

## Understand-Anything

Repository: `Lum1104/Understand-Anything`

Decision: allow only isolated manual onboarding and architecture visualization.
It must not be integrated into runtime, default CI, package dependencies,
retrieval, `.cosheaf/memory`, or KB truth paths.

Manual usage guidance is documented in [Developer Tooling](DEV_TOOLING.md).

Allowed future surfaces:

- Manual onboarding notes for sanitized public-only clones.
- Architecture visualization on a scrubbed repository subset.
- Read-only local dashboard use bound to `127.0.0.1`, with authentication if
  the dashboard supports it.

Disallowed behavior:

- Analyze private KB originals or sensitive local paths.
- Commit generated dashboard, graph, cache, or knowledge-graph files.
- Feed generated graphs into `.cosheaf/memory`, artifact YAML, reviews,
  verifier evidence, or accepted KB.
- Run in default CI, package install, validation, gates, or runtime commands.

Install surface for future work: manual-only documentation. No installer script
or dependency should be added to the default workflow.

Fallback: if unavailable, no project workflow is affected.

Rollback trigger: remove documentation or helpers if they encourage use against
private KB originals, expose dashboards beyond localhost, or treat generated
graphs as project memory.

## Gitignore And Cache Policy

Future implementation PRs must add ignore rules before generating tool output.
Expected generated locations include:

- `.cosheaf/ingest/`
- `.codegraph/`
- `.headroom/`
- `.cosheaf/dev/headroom/`
- `.understand-anything/`
- `knowledge-graph.json`
- `headroom*.json`
- tool-specific cache or dashboard directories

Persisted source notes or curated source metadata may be committed only through
the repository policy that owns those files. Runtime conversions, code graphs,
compressed summaries, dashboards, and temporary caches should remain generated
sidecars.

## Review Checklist

Before merging a future tool integration, verify:

- The tool is optional and absent-tool behavior is tested.
- Default installs and CI still pass without the tool.
- Unsafe paths, accepted KB paths, public/private leakage, network defaults,
  cloud defaults, plugin defaults, and hosted model defaults are blocked.
- Tool output cannot become accepted knowledge without source metadata, human
  review, validation, gates, and explicit promotion.
- Documentation and interface registry entries match the implemented surface.
