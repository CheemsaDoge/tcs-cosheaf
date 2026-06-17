# Codex Operator Runbook

This is the stable entrypoint for Codex-style operator instructions.

Use:

- `docs/WORKFLOWS.md` for the current v0.9.0 reviewable-workflow CLI surface
  and remaining workflow gaps;
- `docs/RESEARCH_LOOPS.md` for bounded multi-attempt research loops;
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

Research loops support bounded multi-attempt exploration of a research issue:

```bash
cosheaf research-loop start --issue <issue-id> --json
cosheaf research-loop show <loop-id> --json
cosheaf research-loop list --json
cosheaf research-loop append-attempt <loop-id> --input-json attempt.json --json
cosheaf research-loop next <loop-id> --json
cosheaf research-loop step <loop-id> --json
cosheaf research-loop run <loop-id> --max-attempts <n> --wallclock-minutes <n> --dry-run --json
cosheaf research-loop export-task <loop-id> --out .cosheaf/research-loops/<loop-id>/operator_task.json --json
cosheaf research-loop import-result <loop-id> --input-json operator_result.json --json
cosheaf research-loop scan <loop-id> --json
cosheaf research-loop finalize <loop-id> --json
```

Loop records are review context only under `.cosheaf/research-loops/`. Each
attempt records planned direction, actions taken, evidence refs, terminal
result or structured failure records, and policy findings. Loop success never
means accepted status. Attempts cannot write `kb/accepted/`, create human
review, mutate verifier results, or claim promotion authority.

The current D.1 research-loop surface remains CLI-first and bounded. `next`
previews the next deterministic action, `step` records one planning event,
`run --dry-run` previews bounded actions without writing source-of-truth files,
`export-task` writes an explicit repository-local operator task packet, and
`import-result` imports a structured external result as runtime loop memory.
Attempt imports rebuild `.cosheaf/research-loops/attempt-memory.json` and
refuse repeated failed directions unless `retry_justification` is present.
`scan` writes a runtime report under `.cosheaf/research-loops/<loop-id>/` and
fails closed on blocking leak or authority findings. The current `run` command
refuses non-dry-run execution. These commands do not call hosted providers,
execute arbitrary shell, run gates, create verifier results, create human
review, write accepted knowledge, or promote artifacts.

The runbook is documentation only. It does not embed an agent runtime, call
hosted providers by default, require MCP, write accepted knowledge, create
human review, mutate verifier results, promote artifacts, or claim automatic
theorem proving.
