# ADR 0038: Website Backend Authenticated Action Design

Status: accepted

Date: 2026-06-19

## Context

ADR 0037 defines the website as a human interface and forbids frontend GitHub
credential ownership. W4 added localhost preview-only action plans. The next
website phase needs a clear authenticated backend path before any GitHub write
endpoint is implemented.

The current repository already has `cosheaf.forge`, including
`ForgeCredentialProvider` as the future credential lookup boundary, and
confirmed CLI GitHub issue/PR actions that rely on credentials outside the
repository. The server still exposes only localhost read-only and dry-run
preview endpoints.

## Decision

Authenticated website actions must be backend-only. The browser sends an action
intent and an explicit confirmation for a previously shown preview plan. The
backend resolves credentials, calls `cosheaf.app` / `cosheaf.forge`
in-process, writes an audit record, and returns only redacted action metadata.

No W5.1 change implements write endpoints. W5.1 is a design checkpoint for the
future W5.2 endpoints.

## Credential Paths

### GitHub App Installation Token

The GitHub App path is the preferred service-to-repository path for shared or
hosted deployments.

- App ID, private key, webhook secret, and installation metadata live in a
  server secret store or environment, never in the repository.
- The backend maps a requested repository to a known installation ID or learns
  it from a verified installation webhook.
- The backend mints a short-lived installation token server-side only.
- The token is scoped to the target repository and the minimum permissions
  needed for the requested action, such as issues write and pull-requests write.
- The token value is never serialized into frontend responses, repository
  files, audit logs, error payloads, or test fixtures.

### GitHub User Token

The user-token path supports local or user-owned repositories where the action
must run as the operator.

- The backend obtains the token from an explicit server-side credential source:
  environment variable, OS keyring, OAuth session store, or an equivalent
  deployment secret store.
- The frontend never stores or forwards the token. It only holds a normal web
  session or localhost session nonce.
- Audit records include the resolved actor identity when available, but never
  include token material.
- User-token capabilities must be checked before confirmed writes. Missing
  credentials return an authentication error before forge execution.

## Forge Integration

Future server code should extend the forge boundary without making previews
credential-aware:

- preview endpoints remain dry-run and must not call a credential provider;
- create endpoints require both authenticated backend credentials and explicit
  confirmation;
- the app/server layer passes a backend-only `ForgeCredentialProvider` into the
  forge action path at confirmation time;
- forge action results may include redacted metadata such as
  `credential_provider`, `credential_kind`, `actor`, and `installation_id`, but
  must never include token values;
- if the initial implementation still shells out to `gh`, the provider may
  supply a bounded environment such as `GH_TOKEN` only to that subprocess with
  `shell=False`, and the environment must be redacted from logs.

`ForgeCredentialProvider` should evolve from capability probing toward an
opaque credential lease interface. The lease boundary should expose only what
the action runner needs and should close over token cleanup/expiry.

## Repository Checkout And Cache Model

Authenticated actions operate on an explicit repository lease:

- Localhost mode may use the active repository root supplied to
  `cosheaf server serve`.
- Hosted mode must use a server-controlled checkout/cache root outside any
  source repository and outside public KB roots.
- Checkout/cache directories are runtime state, not project memory, and must
  be ignored or stored outside the repository.
- The backend locks per repository/action target before write actions so two
  confirmed actions cannot race on the same checkout.
- Before any write action, the backend verifies the target repository identity,
  branch/ref inputs, and dirty state relevant to that action.
- Cache state never grants authority. Repository YAML/JSON, validation, gate,
  human review, and explicit promotion remain the knowledge authority path.

W5.2 should start with GitHub issue/PR actions and should not add branch push,
accepted writes, promotion, verifier mutation, gate mutation, or human-review
creation.

## Webhook Model

Webhook handling is a future synchronization input, not an authority source.

- Webhook endpoints must validate GitHub signatures with a server-side webhook
  secret.
- Delivery IDs provide idempotency keys.
- Installation events may update server-side installation metadata.
- Issue, PR, and check events may update read-only sync status or enqueue
  reconciliation work.
- Webhook events must not mark artifacts accepted, create human review, change
  verifier results, or treat GitHub checks as gate truth.
- Raw webhook payloads must be bounded and redacted before any audit or debug
  storage.

No webhook endpoint is implemented by this ADR.

## Audit Log Model

Every future authenticated action writes an append-only runtime audit record.
The initial durable shape should include:

- `schema_version`
- `event_id`
- `timestamp`
- `request_id`
- `actor`
- `action`
- `repo`
- `credential_provider`
- `credential_kind`
- `preview_plan_hash`
- `explicit_confirm`
- `planned_files`
- `planned_github_objects`
- `result_status`
- `result_url`
- `git_writes_performed`
- `github_writes_performed`
- `repo_writes_performed`
- `authority_notice`

Audit records are runtime evidence only. They are not human review, verifier
pass, gate pass, accepted status, or promotion authority. They must not include
tokens, private keys, authorization headers, cookies, or unredacted environment
data.

Local development may store audit JSONL under ignored `.cosheaf/audit/`.
Hosted deployments should use a deployment log sink or database with the same
redaction policy.

## Confirmed Request Lifecycle

Future create endpoints should follow this lifecycle:

1. Build or receive a preview request.
2. Return a dry-run preview with planned files/actions and authority warning.
3. Confirm request includes `confirm: true` and a preview hash or plan ID.
4. Backend recomputes the plan and rejects drift.
5. Backend resolves credentials through the configured provider.
6. Backend obtains a repository lease and lock.
7. Backend calls `cosheaf.app` / `cosheaf.forge` in-process.
8. Backend writes a redacted audit event.
9. Backend returns redacted action result flags and URLs only.

## Non-Goals

- No credentials in repository files.
- No frontend GitHub token access.
- No write endpoint implementation in W5.1.
- No production readiness claim.
- No accepted artifact writes, promotion, human review creation, verifier
  mutation, gate mutation, hosted provider call, or branch push.

## Required Future Tests

Before W5.2 can claim implementation, tests must prove:

- preview endpoints do not invoke credential providers;
- create endpoints reject missing auth;
- create endpoints reject missing explicit confirm;
- frontend-visible payloads never contain token-like values;
- audit records redact credentials and record action flags;
- GitHub App and user-token providers can be faked without network access;
- webhook signature rejection is fail-closed if webhooks are implemented;
- forge/app paths are shared by CLI and server code.

## Consequences

- Future W5.2 work has a concrete safe path for authenticated GitHub issue and
  PR creation.
- The website remains credential-free.
- Forge remains the workflow boundary, and previews stay dry-run.
- Audit records become the reviewable runtime trail for authenticated actions
  without becoming accepted-knowledge authority.

## Rejected Options

- Let frontend code call GitHub APIs with user tokens.
- Store GitHub tokens, app private keys, webhook secrets, or installation
  tokens in the repository.
- Add create endpoints before credential provider, confirmation, checkout, and
  audit boundaries are documented.
- Treat webhooks, GitHub checks, GitHub issue state, or audit logs as human
  review, gate pass, verifier pass, accepted status, or promotion authority.
