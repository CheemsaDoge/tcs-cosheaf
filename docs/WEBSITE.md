# Website Scope And Data Contract

Cosheaf's website is a human-facing interface over sanitized repository data.
It is not the source of truth and does not create knowledge authority.

## Scope

The first website release is read-only. It may show:

- workspace metadata and public/demo KB root summaries;
- artifact cards and safe artifact metadata;
- repository-local issues and their public/demo links;
- dependency graph summaries;
- gate report summaries;
- context-pack summaries;
- static report summaries; and
- explicit authority-boundary notices.

The CLI and `cosheaf.app` remain the machine/oracle interfaces. Repository
YAML, JSON sidecars, and generated reports remain the source of truth.

## Authority Boundary

Website output must never mark artifacts accepted, human-reviewed, verifier
pass, gate pass, promoted, refuted, source-reviewed, or semantically aligned.
A rendered page, click, filter, graph edge, or badge is display context only.

The website must not become accepted-knowledge evidence. Accepted artifacts
still enter through validation, gates, source metadata, human review, and the
explicit `cosheaf artifact promote` path.

## Public Demo Privacy

Public demo exports must exclude:

- private source notes;
- private unpublished artifacts unless they are explicitly demo-only fixtures;
- API keys;
- tokens;
- raw provider prompts with private context; and
- hidden reviewer identity.

No private KB content may enter a public export unless it was created
explicitly as demo-only data for that export.

## Data Contract

The planned static export directory contains these JSON files:

- `site.json`: site metadata, schema version, build timestamp, and source
  summary.
- `workspace.json`: sanitized workspace name, mode, KB roots, readonly flags,
  and public/private policy summary.
- `artifacts.json`: artifact cards and safe artifact metadata.
- `issues.json`: repository-local issue summaries and safe links.
- `graph.json`: dependency graph nodes, edges, cycle summaries, and missing
  dependency summaries.
- `gates.json`: gate verdict summaries, skipped rows, blocking issues, and
  report references.
- `context_packs.json`: context-pack summaries, issue links, selected cards,
  public-only flags, and known-failure summaries.
- `reports.json`: static report summaries and review-context report paths.
- `authority_boundaries.json`: explicit non-authority notices for website,
  export, gate, verifier, issue, workflow, report, provider, and forge output.

All files must use deterministic JSON, stable schema versions, and
repository-relative paths. Export output is a rebuildable sidecar, not source
of truth.

## Future Write Actions

The frontend must not own GitHub credentials or tokens. Future authenticated
write actions must call a backend, and the backend must call `cosheaf.app` or
`cosheaf.forge`. Frontend code must never call GitHub APIs directly with user
tokens.

Future write actions remain out of scope for the first deployable website.
