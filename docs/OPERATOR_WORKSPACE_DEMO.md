# Operator Workspace Demo

This demo is the framework-side operator flow for the `v0.5.0` Operator MCP +
Codex Application Layer. It is CLI-first. MCP is optional adapter access for
clients that can call whitelisted tools, not a replacement for the CLI or CI
oracle.

The demo does not require hosted providers, API keys, network access, public KB
write access, Lean, SAT, SMT, or an external MCP client. It must not write
accepted knowledge, promote artifacts, create human review, mutate verifier
results, or commit runtime outputs.

## Runtime Output Policy

The commands below may write deterministic runtime sidecars under ignored
locations such as `.cosheaf/` and `context/TASKS/`. Review exports are shown as
dry-runs unless the issue explicitly asks for a review-context file. Runtime
files are not accepted knowledge.

## CLI Demo Flow

Use an existing issue ID in the active repository or workspace. In the
framework repository, `issue.graph-toy-search.0001` is a small local fixture
that can exercise the flow without public KB writes.

```bash
ISSUE_ID=issue.graph-toy-search.0001
RUN_ID=run.issue.graph-toy-search.0001.operator-demo
```

Inspect the workspace and establish the baseline:

```bash
cosheaf workspace info --json
cosheaf validate --json
cosheaf gate run --json
```

Search memory and build bounded context:

```bash
cosheaf memory search "graph toy" --issue "$ISSUE_ID" --json
cosheaf context build "$ISSUE_ID" --json
```

Create a strategy plan from the context pack:

```bash
cosheaf strategy plan \
  --issue "$ISSUE_ID" \
  --from-context "context/TASKS/$ISSUE_ID" \
  --json
```

Start a provenance run:

```bash
cosheaf run start \
  --issue "$ISSUE_ID" \
  --operator external \
  --operator-label "operator demo" \
  --run-id "$RUN_ID" \
  --json
```

Record command, artifact, and output provenance with JSON payloads kept under
ignored runtime space, for example `.cosheaf/operator-demo/`. Command records
must not contain secrets, hidden reasoning, full environment dumps, or
authority-spoofing fields.

Example command record:

```json
{
  "argv": ["cosheaf", "validate", "--json"],
  "cwd": ".",
  "started_at": "2026-06-16T00:00:00Z",
  "ended_at": "2026-06-16T00:00:01Z",
  "exit_code": 0,
  "status": "completed"
}
```

Append it with:

```bash
cosheaf run append-command \
  --run "$RUN_ID" \
  --input-json .cosheaf/operator-demo/command.validate.json \
  --json
```

Record a relevant artifact as read or touched:

```bash
cosheaf run append-artifact \
  --run "$RUN_ID" \
  --artifact construction.graph-toy.0001 \
  --mode read \
  --json
```

Stage only draft or review-context output. Prefer dry-run first:

Example source-note request:

```json
{
  "source_id": "source.operator.demo",
  "kind": "web",
  "title": "Operator demo source note",
  "authors": ["operator"],
  "year": 2026,
  "url": "https://example.invalid/operator-demo",
  "notes": "Demo-only draft source note. Not accepted public knowledge."
}
```

```bash
cosheaf draft write-source-note \
  --input-json .cosheaf/operator-demo/source-note.json \
  --dry-run \
  --json
```

If a real controlled write is intended, remove `--dry-run` only after checking
the target path and issue scope. Controlled writes still do not create accepted
knowledge or human review.

Append an output reference for reviewable runtime or controlled-write output:

Example output reference:

```json
{
  "kind": "context_pack",
  "path": "context/TASKS/issue.graph-toy-search.0001/CONTEXT.md",
  "identifier": "issue.graph-toy-search.0001",
  "status": "completed",
  "summary": "bounded public context pack generated for the operator demo"
}
```

```bash
cosheaf run append-output \
  --run "$RUN_ID" \
  --input-json .cosheaf/operator-demo/output.context-pack.json \
  --json
```

Rerun repository checks:

```bash
cosheaf validate --json
cosheaf gate run --json
```

Finalize the run and preview review export:

```bash
cosheaf run finalize \
  --run "$RUN_ID" \
  --status completed \
  --stop-reason "operator workspace demo completed" \
  --json

cosheaf run evidence-report --run "$RUN_ID" --json
cosheaf run export-review --run "$RUN_ID" --dry-run --json
```

When a strategy plan was generated, update it from the run and preview the
strategy review export:

```bash
cosheaf strategy update-from-run \
  --plan "strategy.$ISSUE_ID.plan" \
  --run "$RUN_ID" \
  --json

cosheaf strategy export-review \
  --plan "strategy.$ISSUE_ID.plan" \
  --dry-run \
  --json
```

Before opening a PR, run the repository verification ladder:

```bash
make lint
make typecheck
make test
make validate
make gate
git diff --check
```

## Optional MCP Adapter Mapping

Operators that have an MCP client may use the stdio adapter for the same
bounded operations. The CLI remains the oracle, and PR summaries should still
record the CLI verification ladder.

Read-only and runtime-inspection MCP tools include:

- `workspace_info`
- `validate`
- `gate` or `gate_run`
- `gate_pr_checklist`
- `memory_search`
- `context_build`
- `strategy_plan`
- `strategy_show`
- `strategy_next`
- `run_show`
- `run_evidence_report`

Controlled MCP tools include:

- `draft_artifact_create_or_update`
- `source_note_draft_create`
- `worker_bundle_validate`
- `worker_bundle_stage`
- `review_request_from_bundle`
- `checked_counterexample_evidence_validate`
- `checked_counterexample_evidence_stage`
- `failure_log_add_draft`
- `research_run_start`
- `research_run_append_command`
- `research_run_append_artifact`
- `research_run_append_output`
- `research_run_finalize`
- `research_run_export_review_dry_run`
- `research_run_export_review`
- `strategy_update_from_run`
- `strategy_export_review_dry_run`
- `strategy_export_review`

These tools call whitelisted service-layer functions. They do not expose
arbitrary shell, accepted writes, promotion, human-review creation,
verifier-result mutation, hosted providers, environment dumps, or unrestricted
filesystem access.

## Workspace-Template Use

For user-facing demos, start from `tcs-cosheaf-workspace-template`, not the
framework repository. A downstream workspace should use a readonly public KB
root and a writable private KB overlay. The workspace demo should pin a
released framework tag, run the same CLI-first flow, and keep all example
private work draft unless explicit review and gates authorize a later
promotion.

Do not manually merge the framework, public KB, and private workspace
repositories into one mixed tree.
