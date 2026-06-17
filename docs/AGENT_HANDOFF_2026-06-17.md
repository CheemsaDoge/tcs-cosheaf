# Agent Handoff: Phase E Complete → Phase F Start

## Current three-repo state (2026-06-17)

| Repo | Main commit | Branch |
|------|-----------|--------|
| tcs-cosheaf | 92d5360 | main (clean after docs closeout) |
| tcs-cosheaf-workspace-template | 7c30b34 | main (clean) |
| tcs-kb-public | 197eccd | main (clean) |

## Phase E completed

- Framework PR #407: cosheaf eval research-loop --json, ecosystem smoke rows
- Workspace-template PR #77: make research-loop-demo
- Public KB PR #92: docs/RESEARCH_LOOP_POLICY.md, policy guard expansion
- Matrix: 25 rows local no-network: 22 pass, 0 fail, 3 skipped (expected)

## Next task: Phase F.1 release-v070-readiness-and-rc

Branch name: release-v070-readiness-and-rc (no agent prefix)

What to do:
1. Bump package metadata to 0.7.0 (pyproject.toml, cosheaf/__init__.py)
2. Write docs/releases/v0.7.0.md with conservative scope, explicit limitations
3. Update README, README.zh-CN.md, ROADMAP, PROJECT_STATE, CURRENT_MILESTONE
4. Run full verification ladder
5. Run matrix with --framework-tag v0.7.0
6. Create PR, get it merged

Do NOT in Phase F.1:
- Create or push the v0.7.0 tag (that is F.2, maintainer action)
- Update downstream workspace-template or public-KB pins
- Add new runtime features
- Claim v0.7.0 is published

## Key invariants

- No accepted writes without promotion workflow
- No human review creation by agent
- Skipped != pass
- No hosted provider defaults
- No automatic theorem proving or Lean semantic-alignment claims
- Research-loop output is review context only, not source metadata or proof
- Workspace-template published install pin stays on v0.6.0 until F.2
- No agent prefixes in branch/PR/issue titles

## Verification commands (run before every PR)

make lint && make typecheck && make test && make validate && make gate && git diff --check

If make is not on PATH:
python -m ruff check cosheaf tests
python -m mypy cosheaf tests
python -m pytest -q
python -m cosheaf.cli validate
python -m cosheaf.cli gate

## Operator notes

- gh proxy: HTTP_PROXY=127.0.0.1:3067
- cosheaf binary: C:\Users\ywjhn\AppData\Roaming\Python\Python313\Scripts
- Git author: CheemsaDoge <cheemsadoge@gmail.com>
- Three repos at H:\ai4tcs\tcs-cosheaf, H:\ai4tcs\tcs-cosheaf-workspace-template, H:\ai4tcs\tcs-kb-public
- .cosheaf/ and context/TASKS/ are gitignored; do not commit runtime outputs
