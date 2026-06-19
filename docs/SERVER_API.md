# Website Server API

Cosheaf includes an optional localhost API for dynamic website preview,
forge-backed action previews, and a narrow backend-only GitHub create slice:

```bash
cosheaf server serve --readonly --port 8765
```

The CLI server binds to `127.0.0.1` and refuses to start unless `--readonly`
is provided. Read and preview endpoints need no authentication because they
are loopback-only and non-mutating. Authenticated create endpoints exist for
backend integrations that instantiate `ReadOnlySiteApi` with a server-side
`ForgeCredentialProvider`; the default CLI server does not configure one, so
confirmed create requests return `401 auth_required`.

Longplan B2 turns this server boundary into the Human Governance Workbench
bridge. The server is the only allowed path from browser actions to policy
checks, repository writes, Git/GitHub actions, audit logs, human review records,
and promotion workflows. This document records that target contract without
claiming that the full write surface exists yet.

Do not expose the localhost server on a public interface. Browser CORS
responses are limited to localhost origins such as
`http://localhost:<port>` and `http://127.0.0.1:<port>`.

## Boundary

The server calls `cosheaf.app.open_app` and the application facade in-process.
It does not shell out to the `cosheaf` CLI, run hosted providers, write
accepted artifacts, promote artifacts, create human review, or run gates as a
side effect in the current read/preview implementation.

Read-only payloads are generated through the existing website export path into
a temporary directory outside the repository, then returned as JSON. Preview
actions return dry-run plans only and never call GitHub. Authenticated create
actions call the same `cosheaf.app` / `cosheaf.forge` GitHub issue/PR logic as
the CLI after backend auth and explicit confirmation. Repository YAML/JSON
records remain the source of truth. Server responses are display context only.

Future Workbench write endpoints may create or update issues, draft artifacts,
source/evidence metadata, review packets, human review decisions, promotion
records, branches, commits, pushes, GitHub issues, and GitHub PRs only through
the backend/app/storage/forge path. Direct browser-to-YAML writes are
forbidden. Browser-side GitHub token storage is forbidden. Server logs,
responses, audit records, and test fixtures must never expose tokens,
authorization headers, private keys, or cookies.

The B2.1.1 action DTO contract lives in `cosheaf.web_actions` and
`schemas/web_action.schema.json`. Future endpoints should use
`WebActionPreviewRequest`, `WebActionConfirmRequest`, `WebActionResult`,
`WebActionAuditEntry`, `WebActionError`, and the write-plan DTOs before adding
new endpoint-specific payloads. The DTOs are a data contract only; B2.1.1 does
not add write endpoints or audit-log persistence.

B2.1.2 adds the shared append-only web-action audit helper at
`cosheaf.web_actions.append_web_action_audit`. Current preview and
authenticated forge create endpoints write redacted machine-readable audit
entries to ignored runtime JSONL at `.cosheaf/audit/web-actions.jsonl`.

Every write-class endpoint must:

- offer a preview request that performs no repository write and no network
  mutation;
- require an explicit confirm request before writing;
- recompute or verify the preview plan before confirmation;
- run the policy checks required for the action class;
- write a redacted machine-readable audit event;
- report planned and written files/actions; and
- preserve skipped, failed, unavailable, and not-run states instead of turning
  them into pass.

Review and promotion endpoints are allowed in the Workbench target because the
website is the human interface. They still cannot invent authority: accepted,
refuted, or obsolete promotion requires explicit human review state and the
ordinary Cosheaf validation, gate, source, dependency, and audit policy.

## Endpoints

```text
GET /api/health
GET /api/workspace
GET /api/artifacts
GET /api/issues
GET /api/graph
GET /api/gates
GET /api/context/<issue_id>
POST /api/forge/local-issues/preview
POST /api/forge/issues/preview
POST /api/forge/issues/create
POST /api/forge/prs/preview
POST /api/forge/prs/create
POST /api/forge/review-packets/preview
```

Unsupported `POST` requests and unsupported methods return
`405 method_not_allowed`. `OPTIONS` is supported for localhost browser
preflight.

`/api/context/<issue_id>` returns the exported context-pack summary for that
issue. It does not run `cosheaf context build` and does not write
`context/TASKS/`.

Preview endpoints return `dry_run_only: true`, planned actions, planned files,
and the forge authority warning. They do not write repository files, call
GitHub, run `git` or `gh`, store credentials, run providers, create human
review, or change accepted/promotion state.

## Target Workbench Action Classes

Future endpoints should keep actions in these classes:

- read actions: live workspace, issue, artifact, context, gate, evidence,
  review, promotion-readiness, forge, and audit reads;
- preview actions: dry-run plans for every write-class action;
- local repo write actions: issue, draft artifact, source/evidence, review
  packet, and human review record writes;
- git/forge actions: branch, commit, push, and PR preparation;
- GitHub actions: GitHub issue and PR creation/update through server-side
  credentials only; and
- review/promotion actions: human review decisions and accepted/refuted/
  obsolete promotion through policy-checked backend workflows.

Local mode may use the active repository root and local credential provider.
Hosted mode must use authenticated server sessions, role checks, server-owned
checkout/cache state, and backend-held GitHub App or OAuth credentials. Hosted
mode must route writes through branches and PRs, not direct main writes.

## Authenticated Create Actions

The backend-only design is recorded in
[ADR 0038](ADR/0038-website-backend-auth-actions.md). The implemented W5.2
create endpoints are limited to:

```text
POST /api/forge/issues/create
POST /api/forge/prs/create
```

Both endpoints require a server-side `ForgeCredentialProvider` with GitHub
credentials available and a request body containing `confirm: true`. Missing
auth returns `401 auth_required`; missing explicit confirmation returns
`400 confirm_required`. The frontend never receives GitHub tokens and must not
call GitHub APIs directly.

Confirmed issue creation calls `CosheafApp.forge_github_issue_create`, which
uses the shared forge service and updates the source issue record's
`external_links` as the CLI forge path does. Confirmed PR creation calls
`CosheafApp.forge_github_pr_create`. Both routes return redacted action flags
and URLs only. Success, auth/confirm refusal, and forge failures are logged to
ignored runtime JSONL at `.cosheaf/audit/web-actions.jsonl`.

These endpoints do not create accepted knowledge, human review, verifier pass,
gate pass, promotion authority, token storage, branch pushes, production
hosting, checkout caching, or webhook handling.

## Authority Rules

- Website and server output are display context only.
- Gate output is workflow context, not accepted status or truth.
- Skipped, unavailable, and not-run checks are not pass.
- AI/provider/operator output is review context only.
- Accepted knowledge still requires repository records, source metadata,
  validation, gate policy, real human review, and explicit promotion.

## Local Smoke

In one terminal:

```bash
cosheaf server serve --readonly --port 8765
```

In another terminal:

```bash
curl http://127.0.0.1:8765/api/health
curl http://127.0.0.1:8765/api/artifacts
curl -X POST http://127.0.0.1:8765/api/forge/prs/preview \
  -H "Content-Type: application/json" \
  -d '{"base":"main","head":"website-preview-actions"}'
```
