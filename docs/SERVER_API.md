# Local Read-Only Server API

Cosheaf includes an optional localhost API for dynamic website preview and
dry-run action previews:

```bash
cosheaf server serve --readonly --port 8765
```

The server binds to `127.0.0.1` and refuses to start unless `--readonly` is
provided. It has no authentication because it is loopback-only and read-only.
Do not expose it on a public interface. Browser CORS responses are limited to
localhost origins such as `http://localhost:<port>` and
`http://127.0.0.1:<port>`.

## Boundary

The server calls `cosheaf.app.open_app` and the application facade in-process.
It does not shell out to the `cosheaf` CLI, run hosted providers, call GitHub,
write accepted artifacts, promote artifacts, create human review, or run gates
as a side effect.

Read-only payloads are generated through the existing website export path into
a temporary directory outside the repository, then returned as JSON. Preview
actions return dry-run plans only. Repository YAML/JSON records remain the
source of truth. Server responses are display context only.

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
POST /api/forge/prs/preview
POST /api/forge/review-packets/preview
```

Non-preview `POST` requests and unsupported methods return
`405 method_not_allowed`. `OPTIONS` is supported for localhost browser
preflight.

`/api/context/<issue_id>` returns the exported context-pack summary for that
issue. It does not run `cosheaf context build` and does not write
`context/TASKS/`.

Preview endpoints return `dry_run_only: true`, planned actions, planned files,
and the forge authority warning. They do not write repository files, call
GitHub, run `git` or `gh`, store credentials, run providers, create human
review, or change accepted/promotion state.

## Future Authenticated Actions

Authenticated create endpoints are not implemented by the local read-only
server. The required backend-only design is recorded in
[ADR 0038](ADR/0038-website-backend-auth-actions.md). Future create endpoints
must keep GitHub credentials server-side, call `cosheaf.app` / `cosheaf.forge`
in-process, require explicit confirmation, write redacted audit records, and
return only redacted action metadata. The frontend must never receive GitHub
tokens or call GitHub APIs directly.

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
