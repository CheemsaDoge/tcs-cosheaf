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

## Static Export Command

The deterministic static export command is:

```bash
cosheaf site export --out .cosheaf/site-data
cosheaf site export --public-only --out .cosheaf/site-data
cosheaf site export --demo --out .cosheaf/site-data
```

`--demo` forces the public-only sanitizer because demo data is intended for
public builds, with one explicit exception: private records tagged
`workspace-demo`, `site-demo`, or `demo-only` may appear as demo fixtures.
Plain `--public-only` remains strict and excludes private KB records and
private-scope issues. The command writes exactly the data-contract files listed
above, with `schema_version: 1`, deterministic key ordering, and no web
framework, server, network, provider, GitHub, gate, verifier, or context-build
execution.

The export uses compact artifact cards and issue summaries, not full artifact
statements or provider prompts. Public-only output excludes private KB roots,
private-scope issues, private artifact IDs, and private dependency edges. Demo
fixture output marks included demo records with `demo_fixture: true` and does
not export full private artifact statements. The sidecar can be regenerated
from repository YAML and is never accepted knowledge, human review, verifier
evidence, gate evidence, or promotion authority.

## Static Frontend Scaffold

The read-only website app lives under `website/`. It is an Astro static site
that imports the committed demo fixture under `website/src/fixtures/site-data/`
and renders the first Longplan B W2.1 routes:

- Home
- Docs / Concepts
- Demo
- Artifacts
- Issues
- Graph
- Gate Reports
- Authority Boundaries

Build and test it locally with:

```bash
cd website && npm install
cd website && npm test
cd website && npm run build
```

The scaffold has no backend, no repository writes, no GitHub token handling, no
runtime private repository fetch, and no hosted provider call. The rendered
site is a human interface over exported JSON only; repository files remain the
source of truth.

The static output directory is `website/dist`. The separate `Website build`
GitHub Actions workflow runs `npm ci`, `npm test`, and `npm run build` under
`website/`, then uploads `website/dist` as a CI artifact. It does not deploy
the site and does not require secrets. Manual Cloudflare Pages or equivalent
static-host setup is documented in [Static Website Deployment](DEPLOYMENT.md).

Artifact, issue, and context views now include static detail pages generated
from the fixture data. Artifact filters run in the browser over already-exported
metadata only. Status badges include authority explanations; missing verifier
or source data is rendered as not checked or unavailable instead of pass.
Graph and gate pages render dependency, reverse-dependency, neighborhood, gate
summary, warning, skip, and report-reference views from the same static export.
Graph edges are explanatory only, and gate pass never implies accepted status.
The Authority Boundaries route now includes a short new-user guide covering
what Cosheaf is, what it is not, why gates/verifiers/AI output are not truth or
human review, how public/private KB roots are separated, and how accepted
status enters through repository records, source metadata, validation, gates,
real human review, and explicit promotion.

## Future Write Actions

The frontend must not own GitHub credentials or tokens. Future authenticated
write actions must call a backend, and the backend must call `cosheaf.app` or
`cosheaf.forge`. Frontend code must never call GitHub APIs directly with user
tokens.

Future write actions remain out of scope for the first deployable website.
