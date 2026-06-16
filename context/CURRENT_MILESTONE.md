# Current Milestone

## Milestone

`v0.6.0` Operator Session + Review Handoff.

## Goal

Turn the published `v0.5.0` Operator MCP + Codex Application Layer release
into a replayable, reviewable, privacy-audited operator session workflow.

The v0.6.0 line should help a maintainer inspect what an external operator did:
which issue was worked on, which tools were called, which context and draft or
review-context files were referenced, which checks ran, which checks were
skipped, whether public/private boundaries held, and what needs human review
next.

Operator sessions and handoff bundles are review context only. They are not a
new truth, accepted-knowledge, review, proof, verifier, gate, provider, or
promotion authority.

## Current Baseline

- Framework package metadata and `cosheaf.__version__` record `0.5.0`.
- `python -m cosheaf.cli version --json` reports package version `0.5.0`.
- Remote tag `v0.5.0` exists as an annotated tag and the GitHub release is
  published.
- Release smoke from
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.5.0` passed during
  publication closeout and installed `tcs-cosheaf==0.5.0`.
- `tcs-cosheaf-workspace-template` active demo, Makefile, CLI-agent,
  provider-preview, fake-provider smoke, verifier-evidence, failure-memory,
  checked-evidence, research-run, strategy, and operator docs/scripts pin or
  install `@v0.5.0`.
- `tcs-kb-public` CI installs `tcs-cosheaf` from `@v0.5.0`.
- The optional MCP tool surface includes read-only/operator runtime tools and
  controlled draft/review/runtime write tools.
- Forbidden authority-expanding MCP tools such as `write_accepted`,
  `promote_artifact`, `mark_human_reviewed`,
  `run_hosted_provider_by_default`, and `arbitrary_shell` are absent.
- `docs/POST_V050_STATE_AUDIT.md` records the v0.5.0 completion audit for the
  v0.6.0 kickoff.
- `docs/CODEX_DEVELOPMENT_PLAN_V10.md` is the active accelerated v0.6.0 plan.
- ADR 0027 records the Operator Session + Review Handoff direction.
- Operator session DTOs, runtime storage, and CLI metadata commands are
  implemented. Runtime files stay under ignored `.cosheaf/operator-sessions/`
  paths.

## Active Scope

The active line is:

```text
v0.6.0 Operator Session + Review Handoff
```

Compressed milestones:

1. Post-v0.5.0 kickoff audit, V10 plan, and ADR.
2. Operator session model and runtime storage.
3. Operator session CLI core.
4. Optional MCP session recording.
5. Operator session leak scanner.
6. Review handoff bundle and explicit review-context export.
7. Downstream workspace-template demo and public KB policy integration.
8. Ecosystem smoke rows for the operator-session workflow.
9. v0.6.0 release candidate, publication closeout, and downstream pin
   alignment.

## Current And Next Functional Tasks

Most recently completed task:

```text
operator-session-cli-core
```

This task added `cosheaf operator session` metadata commands to start, show,
append bounded check/reference records to, and finalize operator sessions. The
CLI does not execute arbitrary commands, does not record MCP calls, does not
build handoff bundles, does not write accepted knowledge, does not create
human review, does not mutate verifier results, does not promote artifacts, and
does not change provider defaults or accepted-promotion semantics.

Next project step:

```text
mcp-session-recording
```

## Explicit Boundaries

- CLI remains the human and CI oracle.
- MCP remains optional and local.
- Operator sessions record bounded metadata and safe references; they do not
  execute arbitrary commands.
- Operator-session storage is runtime state under ignored
  `.cosheaf/operator-sessions/` paths.
- Review handoff export is planned as explicit review context under
  `reviews/operator/`.
- No accepted KB writes through sessions, MCP, handoff bundles, or exports.
- No promotion through sessions, MCP, handoff bundles, or exports.
- No human-review creation through sessions, MCP, handoff bundles, or exports.
- No verifier-result mutation through sessions, MCP, handoff bundles, or
  exports.
- No hosted provider default and no API-key requirement.
- No real provider calls run in CI or default tests.
- Session logs must be redacted and bounded.
- Secrets, environment dumps, hidden reasoning markers, provider payloads, and
  private content in public mode must be rejected or redacted.
- Validation/gate/eval pass does not equal human review or accepted status.
- Skipped verifier, provider, SAT, SMT, Lean, lake, optional-tool, network,
  MCP, session, or eval results are not passes.
- Public KB accepted artifacts still require complete source metadata and human
  review.
- Formal links remain metadata unless a checker actually records a result.
- A successful Lean `#check` means only import and symbol resolution; it does
  not prove informal/formal semantic alignment.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show that
prefix.
