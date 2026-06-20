# Website Server API

Cosheaf includes an optional localhost API for dynamic website preview,
forge-backed action previews, local issue workbench actions, and a narrow
backend-only GitHub create slice:

```bash
cosheaf server serve --readonly --port 8765 --local-actor "Ada Reviewer"
```

The CLI server binds to `127.0.0.1` and refuses to start unless `--readonly`
is provided. Read and preview endpoints need no authentication because they
are loopback-only and non-mutating. Confirmed local issue actions are
loopback-only local repository writes and require `confirm: true`.
Confirmed context-build actions are loopback-only runtime writes under
`context/TASKS/` and require `confirm: true`.
Validate and gate run actions are loopback-only check actions; gate runs may
write ignored runtime reports under `.cosheaf/reports/`.
Authenticated GitHub create endpoints exist for backend integrations that
instantiate `ReadOnlySiteApi` with a server-side `ForgeCredentialProvider`;
the default CLI server does not configure one, so confirmed GitHub create
requests return `401 auth_required`.

In local mode, `--local-actor <name>` records the local person operating the
Workbench. It is not authentication, authorization, or cryptographic identity.
Confirmed human review decisions and promotion actions are refused with
`400 local_actor_required` when the server has no configured local actor.

Hosted auth design is recorded in [Authentication And Authorization](AUTH.md).
Hosted mode is available only as a backend guard stub when `ReadOnlySiteApi`
is constructed with `web_action_mode=WebActionMode.HOSTED` and a
server-provided `HostedAuthProvider`; the CLI localhost server still starts in
local mode. Hosted mode refuses unauthenticated write-class POST actions with
`403 hosted_auth_required` and refuses insufficient-role actions with
`403 hosted_action_denied`. It does not implement OAuth, GitHub App login,
sessions, browser credentials, hosted checkout caching, webhook handling, or
production SaaS.

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
side effect. The local issue workbench slice may write repository-local issue
YAML after explicit confirmation, through `cosheaf.app`, with audit logging.
The context workbench slice may build deterministic issue context packs under
`context/TASKS/` after explicit confirmation, through `cosheaf.app`, with
audit logging.
The validate/gate workbench slice may run repository validation and gatekeeper
checks through `cosheaf.app`, with audit logging and no accepted-state changes.
The artifact draft editor slice may create or update draft/pre-accepted
lifecycle artifacts after explicit confirmation, through `cosheaf.app`, with
validation and audit logging. It refuses direct accepted, refuted, obsolete, or
superseded writes.

Static read-only payloads are generated through the existing website export
path into a temporary directory outside the repository, then returned as JSON.
Live payloads call `cosheaf.app` services and storage loaders
in-process for repository YAML, read existing ignored runtime sidecars directly
when the requested source is `.cosheaf/` or `context/TASKS/`, and do not run
gates, build context packs, call GitHub, or shell out to CLI. Preview actions
return dry-run plans only and never call GitHub.
Authenticated create actions call the same `cosheaf.app` / `cosheaf.forge`
GitHub issue/PR logic as the CLI after backend auth and explicit confirmation.
Repository YAML/JSON records remain the source of truth. Server responses are
display context only.

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
GET /api/workspace/live
GET /api/status
GET /api/artifacts
GET /api/artifacts/live
GET /api/artifacts/<artifact_id>
GET /api/artifacts/<artifact_id>/promotion-readiness
GET /api/issues
GET /api/issues/live
GET /api/issues/<issue_id>
GET /api/graph
GET /api/gates
GET /api/gates/latest
GET /api/context/<issue_id>
GET /api/context/<issue_id>/latest
GET /api/audit/recent
POST /api/validate/run
POST /api/gate/run
POST /api/forge/local-issues/preview
POST /api/issues/preview-create
POST /api/issues/create
POST /api/issues/<issue_id>/preview-update
POST /api/issues/<issue_id>/update
POST /api/issues/<issue_id>/preview-close
POST /api/issues/<issue_id>/close
POST /api/artifacts/preview-create
POST /api/artifacts/create
POST /api/artifacts/<artifact_id>/preview-update
POST /api/artifacts/<artifact_id>/update
POST /api/artifacts/<artifact_id>/preview-source
POST /api/artifacts/<artifact_id>/source
POST /api/artifacts/<artifact_id>/preview-evidence
POST /api/artifacts/<artifact_id>/evidence
POST /api/context/<issue_id>/preview-build
POST /api/context/<issue_id>/build
POST /api/reviews/packets/preview
POST /api/reviews/packets/create
POST /api/reviews/decisions/preview
POST /api/reviews/decisions/create
POST /api/artifacts/<artifact_id>/promotion/preview
POST /api/artifacts/<artifact_id>/promotion/confirm
POST /api/forge/issues/preview
POST /api/forge/issues/create
POST /api/forge/branch/preview
POST /api/forge/branch/create
POST /api/forge/commit/preview
POST /api/forge/commit/create
POST /api/forge/push/preview
POST /api/forge/push/create
POST /api/forge/pr/preview
POST /api/forge/pr/create
POST /api/forge/prs/preview
POST /api/forge/prs/create
POST /api/forge/review-packets/preview
GET /api/forge/pr-status?number=<n>&base=main&head=<branch>
```

`GET /api/health` includes `local_actor`, `local_actor_configured`,
`local_actor_is_auth: false`, `local_actor_notice`, `web_action_mode`,
`hosted_auth_configured`, and `hosted_auth_production_ready: false` so the
frontend can show local actor metadata without presenting it as hosted auth.

Unsupported `POST` requests and unsupported methods return
`405 method_not_allowed`. `OPTIONS` is supported for localhost browser
preflight.

`/api/context/<issue_id>` returns the exported context-pack summary for that
issue. It does not run `cosheaf context build` and does not write
`context/TASKS/`.

Live endpoints return `source_of_truth: "repository"` and an authority notice:

- `/api/workspace/live` returns active workspace and KB-root metadata.
- `/api/status` returns workspace metadata plus validation status. It runs
  repository validation but does not run gates or write reports.
- `/api/issues/live` and `/api/issues/<issue_id>` read repository-local issue
  YAML records.
- `/api/artifacts/live` and `/api/artifacts/<artifact_id>` read lifecycle
  artifact YAML records.
- `/api/artifacts/<artifact_id>/promotion-readiness` returns a live advisory
  promotion-readiness report from `CosheafApp.promotion_readiness`; it runs
  validation and gatekeeper checks and may write ignored gate reports under
  `.cosheaf/reports/`, but it writes no lifecycle artifacts.
- `/api/context/<issue_id>/latest` reads an existing
  `context/TASKS/<issue_id>/` pack when present. It does not build one.
- `/api/gates/latest` reads the latest existing
  `.cosheaf/reports/*-gate-report.json` when present, or returns `not_run`.
- `/api/audit/recent` reads recent existing entries from
  `.cosheaf/audit/web-actions.jsonl`.
- `/api/forge/pr-status` reads GitHub PR collaboration metadata through the
  server-side `gh pr view` path when available. It writes no repository files,
  no review records, and no GitHub state. If `gh` auth or network access is
  unavailable, it returns a degraded `200` payload with `github_auth_available:
  false` instead of leaving the web status panel empty.

Preview endpoints return `dry_run_only: true`, planned actions, planned files,
and the forge authority warning. They do not write repository files, call
GitHub, run `git` or `gh`, store credentials, run providers, create human
review, or change accepted/promotion state.

## Local Issue Workbench Actions

The B2.3.1 local issue workbench endpoints are:

```text
POST /api/issues/preview-create
POST /api/issues/create
POST /api/issues/<issue_id>/preview-update
POST /api/issues/<issue_id>/update
POST /api/issues/<issue_id>/preview-close
POST /api/issues/<issue_id>/close
```

Create and update requests accept `issue_id` for create, `title`, optional
`summary`, `scope` as `private` or `public`, and arrays for `authors`,
`labels`, `related_artifacts`, and `related_sources`. Close requests accept a
non-empty `reason`. Confirmed create, update, and close requests must include
`confirm: true`.

All local issue writes go through `CosheafApp` and `LocalIssueService`.
Preview responses include planned files and a unified diff and write no issue
YAML. Confirmed responses include written files, issue payload, action flags,
diff, and authority warnings. Every preview, confirm refusal, and confirmed
write appends a redacted web-action audit record under
`.cosheaf/audit/web-actions.jsonl`.

Issue closing moves the issue record to `issues/closed/<issue_id>.yaml` and
records `close_reason`. It does not change related artifact status, accepted
state, refuted state, verifier output, gate state, human review, or promotion
state.

## Draft Artifact Workbench Actions

The B2.5.1 draft artifact editor endpoints are:

```text
POST /api/artifacts/preview-create
POST /api/artifacts/create
POST /api/artifacts/<artifact_id>/preview-update
POST /api/artifacts/<artifact_id>/update
```

Create requests accept `artifact_id`, `artifact_type`, `title`, `domain`,
`status`, `statement`, `authors`, `tags`, `depends_on`, and `supersedes`.
Update requests accept the same fields except the path artifact ID comes from
the URL. Confirmed create and update requests must include `confirm: true`.

The web surface is limited to draft/pre-accepted statuses: `raw`, `draft`,
`locally_tested`, `adversarially_tested`, `machine_checked`, and
`human_reviewed`. Direct `accepted`, `refuted`, `obsolete`, or `superseded`
writes are refused and audited. Update keeps the existing artifact type and
edits the current writable artifact file in place; cross-directory lifecycle
moves remain lifecycle/promotion workflow responsibilities.

All artifact writes go through `CosheafApp` and `DraftWriteService`. Preview
responses include planned files, generated YAML, and a unified diff, and write
no artifact YAML. Confirmed responses include written files, artifact payload,
generated YAML, diff, validation summary, and authority warnings. Every preview,
confirm refusal, refusal such as `accepted_write_forbidden`, and confirmed write
appends a redacted web-action audit record under
`.cosheaf/audit/web-actions.jsonl`.

Artifact create/update output is draft workflow context only. It does not
create proof, source metadata, verifier pass, gate pass, human review, accepted
status, or promotion authority.

The B2.5.2 source and evidence metadata endpoints are:

```text
POST /api/artifacts/<artifact_id>/preview-source
POST /api/artifacts/<artifact_id>/source
POST /api/artifacts/<artifact_id>/preview-evidence
POST /api/artifacts/<artifact_id>/evidence
```

Source metadata requests accept `kind`, `title`, `authors`, `year`, `doi`,
`arxiv`, `url`, `theorem_number`, `page`, and `notes`. Evidence metadata
requests accept `kind`, `path`, and `summary`. Confirmed source and evidence
requests must include `confirm: true`.

Preview-source and preview-evidence return generated YAML and a unified diff
without writing artifact YAML. Evidence previews also warn when a non-external
local evidence path is missing or escapes the repository. Confirmed writes
append to the target artifact's `sources` or `evidence` list, validate the
artifact file after the write, and roll back the file on validation failure.
Writes are limited to writable draft/pre-accepted artifacts; accepted,
terminal, readonly-root, and accepted-path targets are refused and audited.
Source writes audit as `source.attach`; evidence writes audit as
`evidence.attach`.

Attached source and evidence metadata are workflow context. They do not create
proof, verifier pass, gate pass, human review, accepted status, or promotion
authority; public accepted promotion still requires policy checks, gates, and
human review.

## Context Build Workbench Actions

The B2.4.1 context build endpoints are:

```text
POST /api/context/<issue_id>/preview-build
POST /api/context/<issue_id>/build
GET /api/context/<issue_id>/latest
```

Preview-build accepts optional `role`, `public_only`, `max_cards`, and
`max_full_artifacts`, returns the planned `context/TASKS/<issue_id>/` files,
and writes only a redacted audit entry. It does not build the context pack.

Confirmed build requests must include `confirm: true`. They call
`CosheafApp.build_context`, write the deterministic context pack under
`context/TASKS/<issue_id>/`, return the written file list and retrieval audit,
and append a redacted web-action audit record under
`.cosheaf/audit/web-actions.jsonl`.

Context packs are retrieval guidance only. They do not create proof, verifier
pass, gate pass, human review, accepted status, or promotion authority.

## Review Packet Workbench Actions

The B2.6.1 review packet endpoints are:

```text
POST /api/reviews/packets/preview
POST /api/reviews/packets/create
```

Requests accept `issue_id` and optional `artifact_id`. Confirmed create
requests must include `confirm: true`.

Preview builds a draft informational review packet from issue/artifact context,
including available artifact statement, dependencies, sources, evidence, known
failures, latest gate state, reviewer questions, and an authority checklist. It
uses the controlled review-request service in dry-run mode, plans a
`reviews/requests/<review-id>.yaml` target, and writes no review YAML.

Confirmed create recomputes the packet and writes one draft informational
review request under `reviews/requests/` through `CosheafApp` and
`DraftWriteService.write_review_request`. It audits as `review.packet_create`.
It does not change artifact review state, mark `human_reviewed`, accept or
reject artifacts, mutate verifier output, pass gates, or promote knowledge.

Review packets are informational context for human reviewers only. They do not
create proof, complete human review, grant accepted status, or authorize
promotion.

## Human Review Decision Workbench Actions

The B2.6.2 human review decision endpoints are:

```text
POST /api/reviews/decisions/preview
POST /api/reviews/decisions/create
```

Requests accept `artifact_id`, `reviewer`, `decision`, `review_notes`, `scope`,
`limitations`, `dependencies_checked`, `sources_checked`, `evidence_checked`,
`gate_state_acknowledged`, and `explicit_human_confirmation`. Confirmed create
requests must include `confirm: true`.

Supported decisions are `accept_for_private_use`,
`accept_for_public_candidate`, `changes_requested`, `keep_draft`,
`refute_candidate`, and `mark_obsolete`.

Preview validates the requested human review decision, plans one
`reviews/decisions/<review-id>.yaml` record, reports whether the artifact
review state would change, and writes no repository files. Confirmed create
recomputes the decision and writes the review record under `reviews/decisions/`.
For accepted-private, accepted-public-candidate, and changes-requested
decisions, the confirmed write may update the target artifact's `review.state`
according to repository policy.

Human review decision endpoints refuse AI, Codex, agent, provider, model, or
verifier identities as reviewers. They audit as `review.decision_create`. They
do not set artifact `status: accepted`, pass gates, mutate verifier evidence,
promote knowledge, or write accepted artifacts. Confirmed creates also require
the server's local mode to be started with `--local-actor <name>`; the audit
actor comes from that server option, while the review record reviewer comes
from the confirmed review payload.

## Promotion Readiness Workbench Actions

The B2.7 promotion readiness/action endpoints are:

```text
GET /api/artifacts/<artifact_id>/promotion-readiness
POST /api/artifacts/<artifact_id>/promotion/preview
POST /api/artifacts/<artifact_id>/promotion/confirm
```

The GET endpoint returns `PromotionReadinessReport.to_dict()` under
`promotion_readiness`, plus `ready`, `accepted_write_performed: false`, and
`promotion_performed: false`. It evaluates current repository records through
the existing promotion-readiness service, including validation, gatekeeper
state, dependency status, review state, source metadata requirements, and
verifier evidence. Skipped verifier output is reported as skipped, never pass.

Promotion preview requests accept `target_state` as `accepted`, `refuted`, or
`obsolete`, plus an optional human `actor`. Preview returns a dry-run
`promotion_plan` with `required_confirmation`, the readiness report,
`promotion_blocked`, `missing_requirements`, `planned_files`, `yaml_diff`,
`review_record_preview`, `validation_summary`, and `gate_summary` when policy
allows the selected target. It writes no lifecycle YAML, does not run `git` or
`gh`, and audits as `promotion.preview`.

Promotion confirm requests require `confirm: true`, a configured server
`--local-actor <name>`, the same `target_state`, an exact
`typed_confirmation` phrase:
`PROMOTE TO ACCEPTED`, `MARK REFUTED`, or `MARK OBSOLETE`, and a non-empty
`promotion_justification`. The server rejects missing justification before any
lifecycle write, then recomputes validation, gate, review, dependency,
source-metadata, readonly-root, and path/status policy checks before writing.
Successful confirm writes the deterministic lifecycle YAML, moves the source
file to the target lifecycle path, returns `written_files` and
`promotion_justification_recorded: true`, and audits as `promotion.confirm`
with the server-local actor and justification stored as `operator_notes`. The
local actor is not auth, and the justification is not written into artifact
YAML. AI/Codex/provider/agent/model/verifier identities are refused as
promotion actors.

Promotion readiness and preview output are advisory workflow context. Confirmed
promotion is a repository write through `cosheaf.app` and service-layer policy;
it does not run `git` or `gh`, mutate verifier evidence, or make website output
accepted authority by itself.

## Validate And Gate Workbench Actions

The B2.4.2 validate/gate endpoints are:

```text
POST /api/validate/run
POST /api/gate/run
GET /api/gates/latest
```

`POST /api/validate/run` calls `CosheafApp.validate_repository`, returns the
validation summary, writes a redacted audit entry, and does not write
repository files or accepted-state records.

`POST /api/gate/run` calls `CosheafApp.run_gate`, writes the normal ignored
gate reports under `.cosheaf/reports/`, returns pass/fail/skipped counts plus
blocking and nonblocking issues, and writes a redacted audit entry.

Validate and gate output are workflow context only. Skipped is not pass, and
gate pass does not create proof, human review, accepted status, or promotion
authority.

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
[ADR 0038](ADR/0038-website-backend-auth-actions.md). The GitHub create
endpoints are:

```text
POST /api/forge/issues/create
POST /api/forge/pr/create
POST /api/forge/prs/create
```

These endpoints require a server-side `ForgeCredentialProvider` with GitHub
credentials available and a request body containing `confirm: true`. Missing
auth returns `401 auth_required`; missing explicit confirmation returns
`400 confirm_required`. The frontend never receives GitHub tokens and must not
call GitHub APIs directly.

Confirmed issue creation calls `CosheafApp.forge_github_issue_create`, which
uses the shared forge service and updates the source issue record's
`external_links` as the CLI forge path does. Confirmed PR creation calls
`CosheafApp.forge_github_pr_create` on the compatibility `/prs/create` route.
The B2.8.1 `/api/forge/pr/create` route calls
`CosheafApp.forge_github_pr_submit`: it runs validation and gatekeeper,
pushes the non-protected head branch, creates a draft PR by default, and
returns the redacted PR URL. Success, auth/confirm refusal, and forge failures
are logged to ignored runtime JSONL at `.cosheaf/audit/web-actions.jsonl`.

The local Forge endpoints `branch/create`, `commit/create`, and `push/create`
require `confirm: true` but do not require a GitHub credential provider.
Branch creation and push refuse `main`/`master`; commit creation also refuses
when the current branch is `main` or `master`, before optional staging or
commit execution. Branch creation refuses dirty state unless the confirmed
request explicitly sets `allow_dirty: true`, in which case current worktree
changes are carried onto the new branch. Commit requires already staged changes
by default, or may stage repository changes itself when the confirmed request
explicitly sets `stage_all: true`; it still runs validation/gate before
committing.

These endpoints do not create accepted knowledge, human review, verifier pass,
gate pass, promotion authority, token storage, production hosting, checkout
caching, or webhook handling.

## Pull Request Status

The B2.8.2 pull-request status endpoint is:

```text
GET /api/forge/pr-status?number=<n>&base=main&head=<branch>
```

The endpoint returns `kind: "github_pr_status"` with a nested `pr_status`
object. The object separates:

- `pr`: PR number, title, state, URL, base/head, merge state, and review
  decision reported by GitHub;
- `linked_issue`: the first closing issue reference when GitHub reports one;
- `checklist`: parsed GitHub markdown checklist counts and items;
- `ci`: status-check rollup summary;
- `gate`: gate check summary when a GitHub check named like `gate` exists;
- `github_reviews` and `review_comments`: GitHub collaboration signals;
- `cosheaf_review`: a separate Cosheaf review placeholder with
  `status: "not_imported"` unless a future explicit human import flow creates
  a repository review record.

GitHub review approval, PR mergeability, CI success, and gate success displayed
by this endpoint remain workflow context only. They do not create Cosheaf human
review, accepted status, verifier pass, source metadata, refutation, or
promotion authority. The endpoint does not expose any API for resolving review
comments.

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
cosheaf server serve --readonly --port 8765 --local-actor "Ada Reviewer"
```

In another terminal:

```bash
curl http://127.0.0.1:8765/api/health
curl http://127.0.0.1:8765/api/artifacts
curl -X POST http://127.0.0.1:8765/api/forge/prs/preview \
  -H "Content-Type: application/json" \
  -d '{"base":"main","head":"website-preview-actions"}'
```
