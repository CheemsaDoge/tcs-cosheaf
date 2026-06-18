# Server Readiness

This document records the in-process entry points a future server should call.
It does not implement a server, web UI, network service, hosted provider, or
GitHub mutation path.

## Server Entry Points

Future server code should open the repository through `open_app` and then call
the app facade directly:

- `CosheafApp.workspace_info`
- `CosheafApp.validate_repository`
- `CosheafApp.validate_artifact_file`
- `CosheafApp.run_gate`
- `CosheafApp.build_context`
- `CosheafApp.show_context`
- `CosheafApp.create_issue`
- `CosheafApp.forge_status`
- `CosheafApp.forge_issue_preview`
- `CosheafApp.forge_pr_preview`

Server-facing error responses should serialize `ErrorResult` instead of
returning raw Python exceptions or terminal-only CLI text.

## Boundary Rules

The future server should call `cosheaf.app` and shared service/forge objects
in-process. It should not shell out to `cosheaf` CLI commands for workspace
info, validation, gatekeeper runs, context packs, local issue creation, or
forge previews.

Forge previews are read-only planning output. They do not call `git`, `gh`, the
network, create GitHub issues, create GitHub PRs, push, store credentials, or
change accepted/promotion state.

Local issue creation through `CosheafApp.create_issue` writes only
repository-local issue YAML under `issues/open/`. It does not create a GitHub
issue and does not accept, refute, review, verify, gate, or promote artifacts.

Validation and gatekeeper calls remain the same authority boundaries as the
CLI: skipped is not pass, gate output is not human review, and neither a
passing gate nor a GitHub workflow state creates accepted knowledge.

## Regression Coverage

`tests/test_server_readiness.py` proves the listed app and forge entry points
can be called without CLI subprocesses. The test monkeypatches
`subprocess.run` to fail, then exercises workspace info, repository validation,
gatekeeper, context build/show, local issue creation, forge issue preview,
forge PR preview, and `ErrorResult` serialization.
