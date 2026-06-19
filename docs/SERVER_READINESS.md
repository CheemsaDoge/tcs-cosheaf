# Server Readiness

This document records the in-process entry points local server code should call.
The first implemented server surface is the read-only localhost website API in
[Local Read-Only Server API](SERVER_API.md). It does not implement a web UI,
hosted provider, public network service, or GitHub mutation path.

The authenticated website action design is recorded in
[ADR 0038](ADR/0038-website-backend-auth-actions.md). That design is not an
implemented server endpoint yet.

## Server Entry Points

Server code should open the repository through `open_app` and then call the app
facade directly:

- `CosheafApp.workspace_info`
- `CosheafApp.validate_repository`
- `CosheafApp.validate_artifact_file`
- `CosheafApp.run_gate`
- `CosheafApp.build_context`
- `CosheafApp.show_context`
- `CosheafApp.create_issue`
- `CosheafApp.preview_issue`
- `CosheafApp.forge_status`
- `CosheafApp.forge_issue_preview`
- `CosheafApp.forge_pr_preview`

Server-facing error responses should serialize `ErrorResult` instead of
returning raw Python exceptions or terminal-only CLI text.

## Boundary Rules

Server code should call `cosheaf.app` and shared service/forge objects
in-process. It must not shell out to `cosheaf` CLI commands for workspace info,
validation, gatekeeper runs, context packs, local issue creation, forge
previews, or website payloads.

Forge and website previews are read-only planning output. They do not call
`git`, `gh`, the network, create GitHub issues, create GitHub PRs, push, store
credentials, or change accepted/promotion state.

Local issue creation through `CosheafApp.create_issue` writes only
repository-local issue YAML under `issues/open/`. It does not create a GitHub
issue and does not accept, refute, review, verify, gate, or promote artifacts.
Local issue preview through `CosheafApp.preview_issue` validates and returns the
planned issue path and record without writing the YAML file.

Validation and gatekeeper calls remain the same authority boundaries as the
CLI: skipped is not pass, gate output is not human review, and neither a
passing gate nor a GitHub workflow state creates accepted knowledge.

## Planned Authenticated Boundary

Future authenticated GitHub issue/PR actions must keep credentials in the
backend and pass them to forge through a server-side credential provider only
after explicit confirmation. Frontend code must not store, forward, or inspect
GitHub tokens.

The planned backend model has six parts:

- GitHub App installation tokens minted server-side from deployment secrets.
- GitHub user tokens resolved from server-side environment, keyring, OAuth
  session, or equivalent secret storage.
- `ForgeCredentialProvider` integration at confirmed action time, never during
  previews.
- A repository checkout/cache lease outside public KB roots and outside source
  control for hosted deployments.
- Verified webhooks for installation and sync events only, never authority.
- Redacted append-only audit records for every confirmed action.

These planned surfaces do not create accepted knowledge, human review, verifier
pass, gate pass, promotion authority, or a production-readiness claim.

## Regression Coverage

`tests/test_server_readiness.py` proves the listed app and forge entry points
can be called without CLI subprocesses. `tests/test_readonly_server.py` proves
the website API routes app-layer payloads without CLI subprocesses, serves
preview-only action plans without repository or GitHub writes, and supports
localhost browser preflight.
