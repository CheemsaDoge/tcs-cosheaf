# Authentication And Authorization

Cosheaf has two Workbench identity modes:

- `local`: the default localhost Workbench mode. `--local-actor <name>` is an
  audit label for the person using the local process. It is not authentication,
  authorization, or cryptographic identity.
- `hosted`: a design stub for future hosted deployments. It can enforce
  server-side action guards when `ReadOnlySiteApi` is constructed with
  `web_action_mode=WebActionMode.HOSTED` and a `HostedAuthProvider`.

Hosted auth is not production-ready in this release. The repository does not
implement OAuth, GitHub App login, sessions, cookies, token parsing, account
linking, webhook sync, hosted checkout caching, or repository/server settings
management. A hosted deployment must provide those pieces outside this stub
before exposing the Workbench to real users.

## Provider Interface

The hosted provider contract lives in `cosheaf.server.auth`:

```python
class HostedAuthProvider(Protocol):
    def current_identity(self) -> HostedIdentity | None:
        ...
```

`HostedIdentity` contains a non-empty `subject` and a frozen set of
`HostedRole` values. A provider returning `None` means the request is
unauthenticated and write-class hosted actions are refused before repository,
Git, GitHub, review, or promotion writes.

Current roles are:

- `reader`
- `contributor`
- `reviewer`
- `maintainer`
- `admin`

`admin` is allowed to perform every guarded hosted action. Other roles are not
treated as a hierarchy; assign multiple roles to one identity when a hosted
deployment needs combined capabilities.

## Action Guards

Hosted route guards are enforced inside `ReadOnlySiteApi` before POST route
execution. They are guard stubs for existing Workbench actions, not a complete
hosted product.

| Role | Guarded actions |
| --- | --- |
| `reader` | read-only GET surfaces; no write-class POST authority |
| `contributor` | issue create/update/close, draft artifact create/update, source/evidence attach, review packet create, context build, validate/gate run, GitHub issue publish |
| `reviewer` | human review decision preview/create |
| `maintainer` | promotion preview/confirm, forge branch/commit/push/PR actions |
| `admin` | all guarded hosted actions |

Unauthorized hosted actions return:

- `403 hosted_auth_required` when no hosted identity is available.
- `403 hosted_action_denied` when the identity lacks the required role.

Denied actions write redacted web-action audit entries with
`mode: "hosted"` and no repository write flags.

## Authority Boundaries

Hosted authorization only decides who may ask the server to run an action. It
does not replace Cosheaf policy:

- Promotion still runs validation, gatekeeper, review-state, dependency,
  source-metadata, readonly-root, and path/status checks.
- GitHub PR approval is not a Cosheaf human-review record unless a human
  imports an explicit review record.
- Gate output, verifier output, AI output, operator output, and hosted auth
  are not accepted-knowledge authority.
- Skipped verifier or gate rows are still not pass rows.

In local mode, promotion and human-review decisions continue to require a
configured local actor. In hosted mode, those actions use the authenticated
hosted identity subject as the audit actor and do not rely on `--local-actor`.
