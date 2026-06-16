# Post-v0.4.0 State Audit

Date: 2026-06-16

Issue: #364

Scope: kickoff audit for the `v0.5.0 Operator MCP + Codex Application Layer`
line. This audit records current evidence before implementing V9 behavior.
It does not change runtime behavior, schemas, version metadata, MCP behavior,
provider behavior, promotion semantics, review state, or KB artifacts.

## Summary

`v0.4.0` is closed and published. The next line can start from a clean
`v0.4.0` baseline:

- package metadata and `cosheaf.__version__` are `0.4.0`;
- the annotated `v0.4.0` tag exists and points to the reviewed release
  candidate commit;
- the GitHub release exists and is not draft or prerelease;
- release smoke from `@v0.4.0` was rerun during this audit and passed;
- workspace-template active pins use `@v0.4.0`;
- public KB CI installs `@v0.4.0`;
- no open PRs or issues block the next line in the three repositories, other
  than this kickoff issue after it was created; and
- strategy plans, research-run records, checked evidence, validation, and
  gates remain non-authoritative review/workflow context.

## Required Audit Answers

### 1. Is package metadata `0.4.0`?

Yes.

Evidence:

- `python -m cosheaf.cli version --json` reported `version: 0.4.0`.
- `pyproject.toml` records `version = "0.4.0"`.
- `cosheaf/__init__.py` records `__version__ = "0.4.0"`.

### 2. Are `v0.4.0` tag, release, and release smoke complete?

Yes.

Evidence:

- `git rev-parse v0.4.0` returned annotated tag object
  `4c58cf94499d6b18ffec1c98157b608b90a9ad63`.
- `git rev-parse "v0.4.0^{}"` returned release-candidate commit
  `9f2e51eddeca6bc09d1915e706493ca4b4d5f99a`.
- `gh release view v0.4.0` reported
  `v0.4.0 Strategy Planner + Research Task Graph`, `isDraft: false`, and
  `isPrerelease: false`.
- `python scripts/release_smoke.py --source git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.4.0`
  installed `tcs-cosheaf==0.4.0` and passed help, version, validate, gate,
  index rebuild, and context build checks.

### 3. Are workspace-template and public KB pinned to `@v0.4.0`?

Yes.

Evidence:

- `tcs-cosheaf-workspace-template` `Makefile`, demos, README, and docs use
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.4.0` or
  `COSHEAF_FRAMEWORK_REF` defaulting to `v0.4.0`.
- `tcs-kb-public/.github/workflows/ci.yml` installs
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.4.0`.
- `tcs-kb-public/RELEASE_CHECKLIST.md` records the immutable `v0.4.0` CI pin.

### 4. Are open PRs/issues empty or intentionally deferred?

No blockers were found.

Evidence:

- Before creating issue #364, `gh pr list --state open` and
  `gh issue list --state open` returned no rows in `tcs-cosheaf`,
  `tcs-cosheaf-workspace-template`, and `tcs-kb-public`.
- After creating issue #364, the only expected open framework issue for this
  branch is `Post-v0.4.0 to v0.5.0 kickoff audit`.

### 5. Which strategy commands exist?

Current strategy commands:

- `cosheaf strategy plan`
- `cosheaf strategy update-from-run`
- `cosheaf strategy export-review`
- `cosheaf strategy show`
- `cosheaf strategy graph`
- `cosheaf strategy next`

Boundary:

Strategy plans are guidance only. They are not proof, evidence, verifier pass,
gate pass, human review, accepted status, accepted refutation, or promotion
authority.

### 6. Which research-run commands exist?

Current research-run commands:

- `cosheaf run start`
- `cosheaf run append-command`
- `cosheaf run append-artifact`
- `cosheaf run append-output`
- `cosheaf run finalize`
- `cosheaf run show`
- `cosheaf run evidence-report`
- `cosheaf run export-review`
- `cosheaf run replay-plan`

Boundary:

Research-run records are provenance only. They are not proof, verifier pass,
gate pass, human review, accepted status, or promotion authority.

### 7. Which controlled-write CLI commands exist and can be safely wrapped?

Candidate V9 MCP wrappers can be derived from existing controlled CLI/service
surfaces:

- `cosheaf draft write-artifact`
- `cosheaf draft write-source-note`
- `cosheaf review request`
- `cosheaf review request-from-bundle`
- `cosheaf bundle submit`
- `cosheaf counterexample evidence validate`
- `cosheaf counterexample evidence stage`
- `cosheaf artifact failure add`
- `cosheaf artifact failure plan-from-bundle`
- `cosheaf artifact failure add-from-bundle`
- research-run start/append/finalize/export-review commands
- strategy update-from-run/export-review commands

These surfaces already avoid accepted writes in their tests. MCP wrappers must
reuse the same service-layer or CLI-equivalent policy boundaries.

### 8. Which MCP surfaces already exist?

Current MCP surface:

- package path: `cosheaf/mcp/server.py`
- CLI group: `cosheaf mcp`
- commands: `list-tools`, `serve`
- current read-only tool names:
  - `workspace_info`
  - `validate`
  - `gate_run`
  - `memory_search`
  - `context_build`
  - `context_show`
  - `orchestrator_plan`

Gap for V9:

The current MCP surface is a minimal read-only stdio layer. It does not yet
cover the V9 read-only set for PR checklist gate, memory cards, strategy
commands, research-run evidence, or eval smoke. It also does not implement V9
controlled-write MCP tools.

The current `cosheaf mcp list-tools` command emits deterministic text, not
JSON. V9 should provide structured tool responses and stable error codes for
operator clients.

### 9. Which public/private and accepted-write negative tests already exist?

Existing coverage includes:

- `tests/test_mcp_server.py`
  - public MCP resources exclude private artifacts and private text;
  - read-only tool lists exclude promotion tools;
  - private-scoped resources require explicit policy permission.
- `tests/test_cli_controlled_draft_writes.py`
  - draft artifact writes reject accepted status;
  - source-note writes reject accepted paths;
  - failure-log writes reject accepted artifacts and readonly public roots;
  - bundle-derived controlled writes reject accepted paths.
- `tests/test_worker_bundle_v2.py`
  - worker bundles reject accepted evidence paths, parent traversal, accepted
    KB proposals, and human-reviewed artifact creation.
- `tests/security/test_checked_counterexample_security.py`
  - checked evidence rejects accepted evidence paths and authority-spoofing
    fields.
- `tests/security/test_research_run_security.py`
  - research-run records reject accepted-write and authority-spoofing fields.
- `tests/security/test_strategy_planner_security.py`
  - strategy plans reject authority-spoofing fields, hidden reasoning,
    accepted paths, non-repository paths, and provider/API-key-looking text.
- `tests/security/test_agent_access_security_regression.py`
  - provider/orchestrator paths reject private leakage without policy and
    consent, accepted provider outputs, and promotion bypass attempts.
- `tests/test_artifact_promotion_cli.py`
  - accepted promotion remains a dedicated gate/review workflow, refuses
    readonly roots, missing source metadata, missing review, failed verifier
    evidence, non-accepted dependencies, and non-lifecycle records.

### 10. What must not be exposed through MCP?

V9 MCP must not expose:

- arbitrary shell;
- direct writes to `kb/accepted/`;
- `artifact promote` or any promotion wrapper;
- human-review creation or `mark_human_reviewed`;
- default hosted provider calls;
- provider/MCP tools that send private KB to external models by default;
- public KB edits by default from downstream workspaces;
- direct schema/policy weakening;
- private-to-public content copying;
- any tool that treats validation, gates, evals, strategy plans, research-run
  records, checked evidence, worker bundles, provider output, or MCP output as
  proof, human review, accepted status, or promotion authority.

## Verification Run For This Audit

The release-smoke command above was rerun during the audit. The Task A PR must
also run:

- `make lint`
- `make typecheck`
- `make test`
- `make validate`
- `make gate`
- `git diff --check`

Generated runtime outputs must remain ignored under `.cosheaf/` or temporary
directories.
