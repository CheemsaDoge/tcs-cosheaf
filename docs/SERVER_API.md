# Local Read-Only Server API

Cosheaf includes an optional localhost API for dynamic website preview:

```bash
cosheaf server serve --readonly --port 8765
```

The server binds to `127.0.0.1` and refuses to start unless `--readonly` is
provided. It has no authentication because it is loopback-only and read-only.
Do not expose it on a public interface.

## Boundary

The server calls `cosheaf.app.open_app` and the application facade in-process.
It does not shell out to the `cosheaf` CLI, run hosted providers, call GitHub,
write accepted artifacts, promote artifacts, create human review, or run gates
as a side effect.

Payloads are generated through the existing website export path into a temporary
directory outside the repository, then returned as JSON. Repository YAML/JSON
records remain the source of truth. Server responses are display context only.

## Endpoints

```text
GET /api/health
GET /api/workspace
GET /api/artifacts
GET /api/issues
GET /api/graph
GET /api/gates
GET /api/context/<issue_id>
```

All non-`GET` methods return `405 method_not_allowed`.

`/api/context/<issue_id>` returns the exported context-pack summary for that
issue. It does not run `cosheaf context build` and does not write
`context/TASKS/`.

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
```
