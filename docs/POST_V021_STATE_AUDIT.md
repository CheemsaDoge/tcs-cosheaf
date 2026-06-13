# Post-v0.2.1 Three-Repo State Audit

Date: 2026-06-13
Framework issue: [#227](https://github.com/CheemsaDoge/tcs-cosheaf/issues/227)

This audit records the state of the TCS-Cosheaf framework, workspace template,
and public KB after the `v0.2.1` closeout. It is documentation-only evidence:
it does not change runtime behavior, schemas, CLI behavior, provider behavior,
MCP behavior, promotion policy, or KB artifacts.

## Summary

- `tcs-cosheaf` is at package version `0.2.1`.
- The GitHub `v0.2.1` release is published as a prerelease, not as a
  production-ready release.
- `tcs-cosheaf-workspace-template` installs and demonstrates
  `tcs-cosheaf@v0.2.1`.
- `tcs-kb-public` CI installs `tcs-cosheaf@v0.2.1`.
- At audit time, the only open item across the three repositories was this
  framework audit issue, `CheemsaDoge/tcs-cosheaf#227`; open PRs were empty.
- Controlled-write MCP is not an approved near-term task. The historical
  controlled-write MCP issue is closed as `not planned`.
- MCP remains optional and is not required for ordinary CLI-first agent work.
- Documentation does not present the whole system as permanently local-only;
  `local-only` appears only for explicit local/dry-run/developer-tool modes or
  as a fallback/offline/CI boundary.
- No accepted artifacts were added during the `v0.2.1` closeout window checked
  by this audit.
- No CI/default path runs a real provider call. Provider default and CI paths
  are fake or mocked, and the real OpenAI-compatible HTTP transport is not
  built in.

## Evidence

### Framework Version And Release

Commands:

```bash
python -m cosheaf.cli version --json
gh release view v0.2.1 --repo CheemsaDoge/tcs-cosheaf --json tagName,isPrerelease,isDraft,name,url,publishedAt
git tag --list v0.2.1
git rev-parse v0.2.1
```

Observed:

- `python -m cosheaf.cli version --json` reported package
  `tcs-cosheaf`, version `0.2.1`.
- `cosheaf/__init__.py` records `__version__ = "0.2.1"`.
- `pyproject.toml` records `version = "0.2.1"`.
- GitHub release `v0.2.1` exists, is not a draft, and has
  `isPrerelease: true`.
- The release title is `v0.2.1 - CLI Agent Access + Hosted Provider Gateway
  RC`.

Conclusion: version metadata and release status agree on `v0.2.1` as a
conservative prerelease.

### Downstream Pins

Commands:

```bash
rg -n "v0\.2\.1|@main|tcs-cosheaf.git@" \
  tcs-cosheaf-workspace-template/README.md \
  tcs-cosheaf-workspace-template/docs \
  tcs-cosheaf-workspace-template/Makefile \
  tcs-cosheaf-workspace-template/scripts \
  tcs-cosheaf-workspace-template/.github/workflows

rg -n "v0\.2\.1|@main|tcs-cosheaf.git@" \
  tcs-kb-public/README.md \
  tcs-kb-public/RELEASE_CHECKLIST.md \
  tcs-kb-public/docs \
  tcs-kb-public/.github/workflows
```

Observed:

- Workspace-template `Makefile`, README, quickstart/showcase docs, and demo
  scripts install or default to
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.1`.
- Workspace-template provider smoke scripts default to `COSHEAF_FRAMEWORK_REF`
  of `v0.2.1`.
- Public KB `.github/workflows/ci.yml` installs
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.1`.
- Public KB `RELEASE_CHECKLIST.md` records the same immutable tag pin.
- No downstream `@main` framework install pin was found in the scanned
  downstream docs/scripts/workflows.

Conclusion: downstream release checks are pinned to `v0.2.1`, not `main`.

### Open Issue And PR State

Commands:

```bash
gh issue list --repo CheemsaDoge/tcs-cosheaf --state open --limit 100 --json number,title,state,updatedAt
gh pr list --repo CheemsaDoge/tcs-cosheaf --state open --limit 100 --json number,title,headRefName,isDraft,updatedAt
gh issue list --repo CheemsaDoge/tcs-cosheaf-workspace-template --state open --limit 100 --json number,title,state,updatedAt
gh pr list --repo CheemsaDoge/tcs-cosheaf-workspace-template --state open --limit 100 --json number,title,headRefName,isDraft,updatedAt
gh issue list --repo CheemsaDoge/tcs-kb-public --state open --limit 100 --json number,title,state,updatedAt
gh pr list --repo CheemsaDoge/tcs-kb-public --state open --limit 100 --json number,title,headRefName,isDraft,updatedAt
```

Observed:

- `tcs-cosheaf`: open issue #227 for this audit; no open PRs.
- `tcs-cosheaf-workspace-template`: no open issues and no open PRs.
- `tcs-kb-public`: no open issues and no open PRs.

Conclusion: the only open item at audit time is this documentation audit issue.

### MCP Boundary

Command:

```bash
gh issue view 190 --repo CheemsaDoge/tcs-cosheaf --json number,title,state,stateReason,closedAt,comments
```

Observed:

- `CheemsaDoge/tcs-cosheaf#190` is titled `Add controlled-write MCP tools`.
- It is closed with `stateReason: NOT_PLANNED`.
- The closing comment states that MCP remains optional adapter work and that
  controlled-write MCP must not proceed without a separate explicit approval
  task.
- `docs/AGENT_ACCESS.md`, `docs/CODEX_WORKFLOW.md`, `docs/ROADMAP.md`,
  `context/CURRENT_MILESTONE.md`, and `context/INTERFACE_REGISTRY.md` state
  that MCP is optional and not required for ordinary CLI-first work.

Exception to track:

- Some historical design docs still mention controlled-write MCP as later
  optional work. Those statements are not current approval. They should be
  interpreted through issue #190 and the current milestone: controlled-write
  MCP is not planned unless a separate maintainer-approved issue reopens that
  scope.

Conclusion: MCP is optional, and controlled-write MCP is not an active
approved implementation path.

### Local-Only Language

Command:

```bash
rg -n -i "local-only|local only" tcs-cosheaf/README.md tcs-cosheaf/docs tcs-cosheaf/context
```

Observed:

- `local-only` appears for explicit local/dry-run/developer-tool surfaces such
  as local orchestrator dry-run, local task planning, CodeGraph developer
  tooling, and observability.
- `docs/ROADMAP.md` and `docs/AGENT_PROVIDERS.md` explicitly say local-only
  execution is fallback, offline, and CI/testing mode, not the permanent
  product boundary.
- No scanned current-state document says the whole system is permanently
  local-only.

Conclusion: current docs do not overclaim local-only as the project boundary.

### Accepted Artifact Changes During Closeout

Commands:

```bash
git -C tcs-cosheaf log --since='2026-06-13T00:00:00Z' --name-status --oneline -- kb/accepted kb/draft kb/public
git -C tcs-kb-public log --since='2026-06-13T00:00:00Z' --name-status --oneline -- kb/public/accepted kb/public/draft reviews sources
git -C tcs-cosheaf-workspace-template log --since='2026-06-13T00:00:00Z' --name-status --oneline -- kb/public kb/private issues scripts Makefile README.md docs
```

Observed:

- Framework KB paths had no closeout-window changes in the checked lifecycle
  paths.
- Public KB accepted/draft/review/source paths had no closeout-window changes.
- Workspace-template closeout changed release/demo docs, scripts, and Makefile
  pinning, not KB content or artifact statuses.

Conclusion: the `v0.2.1` closeout did not add accepted artifacts or promote KB
content.

### Provider Defaults And CI

Commands:

```bash
python -m cosheaf.cli provider list --json
python -m cosheaf.cli provider config-check --provider openai --json
python -m cosheaf.cli orchestrator run --issue issue.graph-toy-search.0001 --provider openai-compatible --json
python -m cosheaf.cli orchestrator run --issue issue.graph-toy-search.0001 --provider openai-compatible --confirm-send --json
rg -n -i "requests\.|httpx|urllib\.request|aiohttp|OPENAI_API_KEY|allow-network|real-run|provider real" \
  tcs-cosheaf/cosheaf tcs-cosheaf/tests tcs-cosheaf/.github/workflows
```

Observed:

- Provider list reports `fake` as enabled by default with `network:
  not_used` and `real_run_cli: false`.
- Provider list reports `openai` as `enabled_by_default: false`, `network:
  explicit_config_only`, and `real_run_cli: false`.
- OpenAI config check reports `enabled: false`, `api_key_value: missing`, and
  `real_run_cli: false`.
- OpenAI-compatible orchestrator dispatch without `--confirm-send` fails with
  `provider_confirm_send_required`.
- OpenAI-compatible orchestrator dispatch with `--confirm-send` still fails
  closed when no injected/configured transport exists, recording
  `provider_transport_missing: OpenAI-compatible provider transport is not
  configured`.
- CI only runs package install, lint, typecheck, test, validate, and gate.
  It does not provide provider credentials or invoke a real provider run.
- Tests mention OpenAI-compatible provider paths only through fake or injected
  mocked transport fixtures.

Conclusion: no real provider call is default-enabled or used in CI/default
tests.

## Stale Or Follow-Up Documentation Items

No runtime or policy changes are required for the audit itself. The following
wording should be tightened in a later documentation hardening PR:

1. Historical design text that says controlled-write MCP is "later optional
   work" should be aligned with the current issue state: controlled-write MCP
   is not planned unless a separate approved issue explicitly reopens it.
2. Documents that mention local-only modes should continue to distinguish
   specific local/dry-run/developer-tool modes from the product boundary.

These follow-ups are documentation wording only. They do not imply provider,
MCP, schema, promotion, or KB behavior changes.
