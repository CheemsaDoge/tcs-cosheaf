# Public And Private Policy

This is the v1.0 short entry point for public/private boundaries. The detailed
policy remains [Public And Private KB Policy](PUBLIC_PRIVATE_KB.md).

## Three-Repository Model

- `tcs-cosheaf`: framework package, CLI, schemas, gates, reports, and tests.
- `tcs-kb-public`: reusable public TCS knowledge, maintained through reviewed
  public KB PRs.
- `tcs-cosheaf-workspace-template`: user-facing workspace with readonly public
  KB plus writable private overlay.

Do not manually merge the framework repository, public KB repository, and a
private workspace into one mixed tree.

## Public KB

Public KB accepted artifacts require source metadata, valid dependencies,
passing validation/gates, and human review where policy requires it. Public KB
must not contain private conjectures, unpublished private research, or
LLM-generated accepted content without review.

Downstream workspaces should treat public KB roots as readonly.

## Private KB

Private research belongs under `kb/private` in a user workspace. Private
artifacts may contain conjectures, proof attempts, failures, local experiments,
operator notes, and draft claims.

Private artifacts may depend on public artifacts. Public artifacts must not
depend on private artifacts. Accepted artifacts must not depend on draft
artifacts across any KB root.

## Review-Context Output

Workflow, campaign, checker, memory, benchmark, comparison, static-report,
provider, MCP, and operator-session outputs are not public KB source metadata,
human review, verifier pass, gate pass, accepted status, accepted theorem or
refutation status, or promotion authority.

Keep those outputs under ignored runtime paths or explicit review-context
directories. Do not copy them into `kb/public/accepted/`.
