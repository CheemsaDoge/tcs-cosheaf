# Post-v0.5.0 State Audit

Status: completed for issue #378.

Date: 2026-06-16.

This audit records the actual repository state at the start of the
`v0.6.0 Operator Session + Review Handoff` line. It verifies the completed
`v0.5.0 Operator MCP + Codex Application Layer` release before adding any
operator-session runtime, schema, or handoff behavior.

This audit is documentation only. It does not implement operator sessions,
add dependencies, add schemas, change runtime behavior, bump package version,
write KB artifacts, create human review, promote artifacts, or change verifier
or gate semantics.

## Verification Snapshot

The audit used the current `main` branches of:

- `CheemsaDoge/tcs-cosheaf`
- `CheemsaDoge/tcs-cosheaf-workspace-template`
- `CheemsaDoge/tcs-kb-public`

Observed state:

- `tcs-cosheaf` local `main` matched `origin/main` at
  `c1835b9fb19819399ff551be942e6674b1247d6a` before this audit branch.
- `tcs-cosheaf-workspace-template` local `main` matched `origin/main`.
- `tcs-kb-public` local `main` matched `origin/main`.
- GitHub showed no open PRs in any of the three repositories.
- Before creating this audit issue, GitHub showed no open issues in any of
  the three repositories. During this task, issue #378 is the active tracking
  issue for the audit itself.

## Package Version

The framework version is consistently `0.5.0`.

Observed checks:

```text
python -m cosheaf.cli version --json
```

reported:

```json
{
  "schema_version": 1,
  "package": "tcs-cosheaf",
  "version": "0.5.0"
}
```

Additional direct checks reported:

- `cosheaf.__version__ == "0.5.0"`
- `pyproject.toml` project version is `0.5.0`

## v0.5.0 Tag, Release, And Release Smoke

The public `v0.5.0` release is complete.

Observed release state:

- GitHub release URL:
  `https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.5.0`
- Release name: `v0.5.0 Operator MCP + Codex Application Layer`
- Release state: non-draft, non-prerelease
- Published at: `2026-06-16T13:00:17Z`
- Annotated tag object:
  `49ea4c9de153ccc9c41b39ec2fc705b3735c8795`
- Peeled commit:
  `25913148da5e512aa888ec76198146825509e071`

`docs/releases/v0.5.0.md` and `context/PROJECT_STATE.md` record that release
smoke from
`git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.5.0` passed, installed
`tcs-cosheaf==0.5.0`, and covered help, version, validation, gate, index
rebuild, and context build checks.

## Downstream Pin State

The downstream repositories are aligned to `@v0.5.0`.

`tcs-cosheaf-workspace-template` active README, quickstart, demos, Makefile,
provider-preview, fake-provider, verifier-evidence, failure-memory,
checked-evidence, research-run, strategy, and operator docs/scripts reference
or install `v0.5.0`.

`tcs-kb-public` CI installs:

```text
git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.5.0
```

The public KB README records that repository CI installs from the published
`v0.5.0` framework tag.

No artifact, review-record, formalization-metadata, schema, or promotion-policy
changes are part of this audit.

## Current MCP Tool Surface

`python -m cosheaf.cli mcp list-tools` reported these tools:

```text
workspace_info
validate
gate
gate_pr_checklist
gate_run
memory_cards
memory_search
context_build
context_show
strategy_plan
strategy_show
strategy_graph
strategy_next
run_show
run_evidence_report
eval_strategy_planner
eval_research_run_loop
draft_artifact_create_or_update
source_note_draft_create
worker_bundle_validate
worker_bundle_stage
review_request_from_bundle
checked_counterexample_evidence_validate
checked_counterexample_evidence_stage
failure_log_add_draft
research_run_start
research_run_append_command
research_run_append_artifact
research_run_append_output
research_run_finalize
research_run_export_review_dry_run
research_run_export_review
strategy_update_from_run
strategy_export_review_dry_run
strategy_export_review
orchestrator_plan
```

Read-only or runtime-output-oriented tools include workspace inspection,
validation, gate, PR checklist gate, memory, context, strategy inspection,
research-run inspection, eval smoke, and the compatibility `orchestrator_plan`
surface.

Controlled-write tools include draft artifact creation/update, source-note
draft staging, WorkerBundle validation/staging, draft review-request creation
from WorkerBundles, checked-counterexample evidence validation/staging,
failure-log appends on writable non-accepted artifacts, research-run
provenance writes, and strategy review-context exports.

The following forbidden authority-expanding tool names were checked and are
absent:

```text
write_accepted
promote_artifact
mark_human_reviewed
edit_public_kb_by_default
run_hosted_provider_by_default
arbitrary_shell
```

## Operator Docs And Skill Surfaces

The v0.5.0 operator documentation surface exists and remains the current
operator guide until v0.6.0 adds session/handoff behavior:

- `docs/CODEX_OPERATOR_RUNBOOK.md`
- `docs/OPERATOR_MCP.md`
- `docs/OPERATOR_WORKSPACE_DEMO.md`
- `docs/OPERATOR_SKILL.md`
- `docs/skills/cosheaf-operator/SKILL.md`
- `docs/EXTERNAL_OPERATOR_RUN_LOOP.md`
- `docs/AGENT_ACCESS.md`

These are runbooks and policy documents. They do not grant runtime authority
outside the underlying CLI, service, MCP, gate, verifier, review, and
promotion policy surfaces.

## Security And Public/Private Coverage

The current test surface includes coverage for the boundaries that the
v0.6.0 line must preserve:

- `tests/test_mcp_server.py`
- `tests/security/test_agent_access_security_regression.py`
- `tests/security/test_checked_counterexample_security.py`
- `tests/security/test_research_run_security.py`
- `tests/security/test_provider_log_scanner.py`
- `tests/security/test_failure_log_security_regression.py`
- `tests/security/test_strategy_planner_security.py`
- `tests/test_workspace_template_smoke.py`
- `tests/test_ecosystem_smoke.py`
- `tests/test_promotion_gate_verifier_regressions.py`
- `tests/evals/test_strategy_planner_eval.py`
- `tests/evals/test_research_run_loop_eval.py`
- `tests/evals/test_provider_workflow_eval.py`
- `tests/evals/test_failure_counterexample_eval.py`
- `tests/evals/test_checked_evidence_run_loop_eval.py`

Covered policy areas include accepted-path rejection, readonly public-root
refusal, public/private filtering, skipped-not-pass accounting, provider
default-off behavior, no-real-network defaults, human-review spoofing
rejection, review-context-only export behavior, and controlled write boundaries
for draft/proposal/runtime records.

## Runtime Outputs And Review-Context Exports

Runtime-only outputs include generated files under ignored `.cosheaf/` paths,
such as reports, indexes, logs, run records, strategy runtime plans, task
runtime records, provider logs, and future operator-session records.

Existing explicit review-context exports may be written only through
controlled commands to approved review-context locations such as
`reviews/strategy/`, `reviews/runs/`, `reviews/evidence/`, or task-specific
review request paths documented by the relevant command. Those exports are
review context only.

For the v0.6.0 line, operator-session storage is planned as runtime state under
`.cosheaf/operator-sessions/`. Handoff export is planned as explicit
review-context YAML under `reviews/operator/`. Neither location is accepted
knowledge, verifier evidence by itself, gate pass, human review, accepted
status, accepted refutation, or promotion authority.

## What Must Not Become Operator-Session Authority

Operator sessions, MCP recordings, leak scans, handoff bundles, and handoff
exports must not become authority for:

- accepted KB writes;
- artifact promotion;
- human-review creation, completion, or spoofing;
- verifier-result mutation;
- verifier pass, gate pass, or skipped-as-pass claims;
- accepted status or accepted refutation;
- public KB source metadata;
- informal/formal semantic alignment;
- automatic theorem proving;
- hosted provider defaults or API-key requirements;
- production hosted multi-agent SaaS claims;
- public KB edits from downstream workspaces by default.

Validation, gates, evals, operator runbooks, MCP tools, session transcripts,
and handoff bundles can help a maintainer review work. They do not replace
source metadata, human review, verifier evidence, or explicit promotion where
those are required.
