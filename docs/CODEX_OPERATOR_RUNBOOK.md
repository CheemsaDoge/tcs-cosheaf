# Codex Operator Runbook

This is the stable entrypoint for Codex-style operator instructions.

Use:

- `docs/EXTERNAL_OPERATOR_RUN_LOOP.md` for the full CLI-first issue loop;
- `docs/OPERATOR_SESSIONS.md` for bounded operator-session metadata records;
- `docs/OPERATOR_HANDOFF.md` for compact runtime handoff bundles;
- `docs/OPERATOR_WORKSPACE_DEMO.md` for a concrete demo command sequence;
- `docs/OPERATOR_SKILL.md` for the portable Skill-like instruction package;
- `docs/CODEX_WORKFLOW.md` for repository workflow and PR expectations.

Operator sessions can now wrap an issue-focused work session without executing
commands themselves:

```bash
cosheaf operator session start --issue <issue-id> --json
cosheaf operator session append-check <session-id> --kind validate --status pass --summary "validation ran outside this recorder" --json
cosheaf operator session append-ref <session-id> --kind runtime --path .cosheaf/reports/example.json --json
cosheaf operator session finalize <session-id> --json
cosheaf operator session scan <session-id> --json
cosheaf operator handoff build --session <session-id> --json
cosheaf operator handoff show handoff.<session-id> --json
cosheaf operator handoff export --handoff handoff.<session-id> --dry-run --json
cosheaf operator handoff export --handoff handoff.<session-id> --json
```

These records are session metadata only. Run `cosheaf validate`,
`cosheaf gate run`, tests, evals, and review workflows separately and record
their outcomes honestly. Skipped checks remain skipped and are not pass
evidence.

Handoff bundles are compact runtime review context under
`.cosheaf/operator-sessions/<session-id>/handoff.json`. The build command
fails closed when the leak scanner reports blockers. Handoff export writes
explicit review-context YAML under `reviews/operator/`; it is not human review,
accepted knowledge, verifier evidence, gate pass, or promotion authority.

The runbook is documentation only. It does not embed an agent runtime, call
hosted providers by default, require MCP, write accepted knowledge, create
human review, mutate verifier results, promote artifacts, or claim automatic
theorem proving.
