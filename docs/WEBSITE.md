# Web Workbench Scope And Data Contract

Cosheaf's website is the Human Governance Workbench: the primary human
research, review, and governance workspace over a Git-backed Cosheaf
repository. It is not only a showcase. Static demo pages remain useful, but
they are one read-only mode of the product rather than the full product.

## Scope

The product contract is:

- Website: main human workspace for research, issue triage, review,
  promotion, forge/PR preparation, and audit inspection.
- CLI: AI/Codex/operator/automation interface and scriptable oracle.
- Server: policy, auth, audit, repo-write, and GitHub bridge.
- Repository: source of truth.

The Web Workbench may execute human review and accepted/refuted/obsolete
promotion workflows when the backend enforces the same policy checks,
confirmation, audit, repository writes, and Git/GitHub review flow as the CLI.
The frontend must never become accepted authority by itself.

Static showcase mode may show:

- workspace metadata and public/demo KB root summaries;
- artifact cards and safe artifact metadata;
- repository-local issues and their public/demo links;
- dependency graph summaries;
- gate report summaries;
- context-pack summaries;
- static report summaries; and
- explicit authority-boundary notices.

Live local and hosted Workbench modes may additionally expose confirmed human
actions through the server. They are not implemented by this documentation
change; this file defines the contract future runtime tasks must preserve.

## Authority Boundary

Website display output must never mark artifacts accepted, human-reviewed,
verifier pass, gate pass, promoted, refuted, source-reviewed, or semantically
aligned. A rendered page, click, filter, graph edge, badge, or readiness panel
is display context only.

Confirmed Workbench actions may write review records or promote artifacts only
through `cosheaf.server -> cosheaf.app -> cosheaf.core/storage/forge` and the
ordinary Cosheaf policy path. Accepted artifacts still require repository
records, source metadata where policy requires it, validation, gate policy,
explicit human review, and explicit promotion. Gate pass, verifier pass,
GitHub PR merge, AI/Codex output, or server audit output is not accepted
authority by itself.

Direct frontend YAML mutation is forbidden. Browser-side GitHub token storage
is forbidden. Frontend code must not call GitHub APIs directly with user
tokens and must not write repository files.

## Operating Modes

### Static Showcase Mode

Static showcase mode is a read-only public or local build from sanitized
export JSON. It has no backend, no repository writes, no GitHub token
handling, no provider call, and no private repository fetch. It is appropriate
for public explanation and inspection, not governance work.

### Local Workbench Mode

Local mode is for a single researcher running the server on loopback with an
explicit write-enabled configuration. The backend may write local repository
files, run validation/gate/context workflows, create local branches/commits,
and call local GitHub/forge credentials only after preview and explicit
confirm. All writes must be audited.

Local mode may record a local actor identity, but that identity is not
cryptographic hosted auth. Human review and promotion actions still require an
explicit human decision and policy checks.

### Hosted Workbench Mode

Hosted mode is a future collaborative deployment. It must use server-side auth,
role checks, server-owned repository checkout/cache state, branch/PR write
flows, and backend-held GitHub App or OAuth credentials. Browser GitHub token
storage remains forbidden. Hosted mode must not write directly to `main` and
must not treat GitHub issue, PR, webhook, or CI state as Cosheaf human review
or accepted authority.

## Action Taxonomy

Workbench actions are classified by authority and side effects:

- Read actions: inspect exported or live repository state without writes.
- Preview actions: compute planned files, Git/GitHub actions, warnings, and
  policy blockers without writes or network mutation.
- Local repo write actions: create or update repository records only through
  backend/app/storage paths after preview and confirm.
- Git/forge actions: create branches, stage selected files, commit, push, and
  prepare PRs through the forge boundary after preview, checks, and confirm.
- GitHub actions: create or update GitHub issues/PRs only through backend-held
  credentials and redacted audit logs.
- Review/promotion actions: record human review decisions and promote to
  accepted, refuted, or obsolete only through policy checks, audit, repository
  writes, and the promotion workflow.

Every write-class action must support preview before confirm, produce a
machine-readable audit entry, show authority warnings, and report skipped,
failed, unavailable, or not-run checks separately from pass.

## Target UX Surfaces

The Workbench target surface includes:

- Dashboard: workspace health, open work, failures, recent actions, and next
  actions.
- Issues: create, edit, close, publish, and link local/GitHub issues.
- Artifacts: inspect, create, and edit draft/pre-accepted artifacts.
- Context: build and inspect issue-scoped context packs.
- Gates: run and inspect validation/gate outcomes with skipped-not-pass
  display.
- Evidence: attach and inspect source notes, evidence paths, checker output,
  and reproducibility metadata.
- Review: generate packets and record explicit human review decisions.
- Promotion: inspect readiness and promote only through policy-confirmed
  accepted/refuted/obsolete workflows.
- Forge/PR: prepare branch, commit, push, GitHub issue, and GitHub PR actions.
- Audit: inspect append-only Workbench, forge, review, and promotion action
  history.

## Language UX

The target Web Workbench should support English and Simplified Chinese for
human-facing navigation, labels, authority warnings, action confirmations,
error messages, and workflow guidance. If a later implementation slice cannot
finish full bilingual UI without risking the authority work, Chinese-first UI
copy is an acceptable temporary fallback and English localization should remain
tracked in a follow-up issue or PR acceptance checklist as deferred Workbench
polish. Any implementation PR that ships Chinese-first fallback must open or
link a follow-up issue titled `Complete Workbench English localization` and
list the localization gap under its known limitations. Repository source files,
schemas, and project-facing docs remain English unless a task explicitly
requires Chinese.

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

For local dynamic preview, `cosheaf server serve --readonly --port 8765`
exposes the same read-only website payloads through localhost JSON endpoints.
The server calls the app facade in-process, does not shell out to CLI commands,
does not write repository records, and does not run gates or context builds as
request side effects. See [Local Read-Only Server API](SERVER_API.md).

The demo page can also call localhost preview-only endpoints for local issue,
GitHub issue, pull request, and review packet plans. These requests are
`POST` dry-runs only. They show planned files/actions and authority warnings,
but they do not write repository files, call GitHub, store tokens, run
providers, create human review, or change accepted/promotion state.

The server API now also has backend-only authenticated create endpoints for
GitHub issue and PR creation. They are not frontend token flows: a backend must
inject a server-side `ForgeCredentialProvider`, the request must include
`confirm: true`, and the server calls `cosheaf.app` / `cosheaf.forge`
in-process. Results and failures are redacted and audited under ignored
`.cosheaf/audit/`. These endpoints write only the shared forge issue/PR
effects; they do not write accepted knowledge, create human review, mutate
verifier/gate state, promote artifacts, store tokens, or claim production
readiness.

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

## Workbench Write Actions

The frontend must not own GitHub credentials or tokens. Authenticated write
actions must call a backend, and the backend must call `cosheaf.app` or
`cosheaf.forge`. Frontend code must never call GitHub APIs directly with user
tokens.

The W5.1 backend-auth design is recorded in
[ADR 0038](ADR/0038-website-backend-auth-actions.md). W5.2 implements the
first GitHub issue/PR create slice with backend credential-provider gating,
explicit confirmation, shared forge execution, and redacted audit records.
Future hosted deployments still need server-side GitHub App/user-token
resolution, repository checkout/cache locking, and webhook synchronization.

Longplan B2 extends this backend-action direction into the full Human
Governance Workbench. Write actions are allowed only when they stay behind the
server/app/forge boundary, preserve preview-before-confirm, emit redacted
machine-readable audit logs, and keep repository files as the source of truth.
They do not make website output a knowledge authority.
