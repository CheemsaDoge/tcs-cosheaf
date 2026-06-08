# Post-v0.2.0 Rollback Audit

Issue: #170

Task: Phase R / Task R.1 from `longplan_v3.md`

## Scope

This audit compares current `main` with the `v0.2.0` release baseline and
classifies every post-release changed file as `KEEP`, `REVERT`, `REWRITE`, or
`NEEDS_HUMAN_DECISION`.

This audit is documentation only. It does not change runtime behavior, schemas,
tests, gate behavior, verifier adapters, KB artifacts, accepted-promotion
policy, workspace-template behavior, or release tags.

## Baseline

- Baseline tag: `v0.2.0`
- Baseline commit: `9b1c3fa6f52de487e91db0282a5cf991e3e671e6`
- Current audited `main`: `b43ebe9747a435f0de90e6990636370b61e20d3e`
- Tag object observed locally: `6c2cedc19545643a77474c6208d2324e95da20ca`

`v0.2.0` is the local-MVP release baseline. It is not a production-ready claim,
and it is not the older `v0.1.1` Formal Link Layer support baseline.

## Required Git Evidence

Commands used for this audit:

```powershell
git fetch --tags --prune
git log --oneline v0.2.0..main
git diff --name-status v0.2.0..main
git diff --stat v0.2.0..main
git rev-list -n 1 v0.2.0
git rev-parse main
```

Post-`v0.2.0` commits on `main`:

```text
b43ebe9 Expand default context eval cases
bef6c72 Expand default retrieval eval cases
14f9f43 Document git index lock recovery
12d9d6f Harden worker bundle proposed paths
8a036a4 Document stuck Actions check recovery
3e1c455 Harden orchestrator state path validation
f1c4333 Align v0.2.0 state documentation
```

Changed-file summary:

```text
14 files changed, 271 insertions(+), 66 deletions(-)
```

No files under `kb/`, `issues/`, or `reviews/` changed in
`v0.2.0..main`.

## Classification Summary

| File | Classification | Reason |
| --- | --- | --- |
| `README.md` | KEEP | Aligns release wording after the tag and keeps hosted LLM execution listed as not implemented. It does not make local-only policy permanent. |
| `RELEASE_CHECKLIST.md` | KEEP | Converts release-candidate checklist language into post-release smoke/showcase language and preserves non-production boundaries. |
| `context/CURRENT_MILESTONE.md` | REWRITE | Contains local-only roadmap pollution: the current next focus is "state consistency and local orchestrator hardening" and says not to start hosted-provider work. Longplan v3 requires v0.2.1 Agent Access + Hosted API + MCP/Skill direction. |
| `context/PROJECT_STATE.md` | KEEP | Adds accurate ordered release-state history and preserves hosted-provider gating as historical state. It does not claim production readiness or change policy. |
| `cosheaf/agent/orchestrator_state.py` | KEEP | Adds rejection for nested `..` path segments in orchestrator state paths. This is security-compatible hardening and does not introduce local-only policy. |
| `cosheaf/agent/worker_bundle_v2.py` | KEEP | Adds rejection for nested `..` path segments in proposed worker-bundle artifact paths. This protects draft/proposal boundaries and does not affect accepted promotion semantics. |
| `docs/OPERATOR_NOTES.md` | KEEP | Records real operator pitfalls for stuck Actions checks, Git index locks, identity, proxy, and generated outputs. This is durable workflow knowledge and does not change runtime behavior. |
| `docs/ROADMAP.md` | REWRITE | Contains local-only roadmap pollution: the next focus section says implementation work should stay local-only and should not introduce hosted providers. Longplan v3 requires hosted API/provider work to be scheduled, controlled, and default-safe rather than deferred indefinitely. |
| `evals/context/cases.yaml` | KEEP | Adds default context eval coverage for the SAT/SMT pilot. This strengthens local regression evidence and is compatible with future agent access. |
| `evals/retrieval/cases.yaml` | KEEP | Adds default retrieval eval coverage for the SAT/SMT pilot. This strengthens retrieval quality baselines and does not alter KB truth. |
| `tests/test_context_eval.py` | KEEP | Tests the expanded default context eval suite. No runtime behavior or policy semantics changed. |
| `tests/test_orchestrator_state.py` | KEEP | Tests nested parent-directory rejection in orchestrator state paths. This supports security boundaries needed by future MCP/API access. |
| `tests/test_retrieval_eval.py` | KEEP | Tests the expanded default retrieval eval suite. No runtime behavior or policy semantics changed. |
| `tests/test_worker_bundle_v2.py` | KEEP | Tests nested parent-directory rejection in worker-bundle proposal paths. This preserves draft/proposal safety. |

## Local-Only Roadmap Pollution

The audit identifies two files that should be rewritten in Phase R / Task R.2:

- `context/CURRENT_MILESTONE.md`
- `docs/ROADMAP.md`

The problematic direction is not the existence of local orchestrator code or
tests. The problem is the current documentation direction that makes local-only
orchestrator hardening the next mainline focus and tells operators not to start
hosted-provider work.

Longplan v3 changes that direction:

- MCP should be the first-class external-agent interface.
- Skill should be an operator guide.
- Hosted model API/provider work should be scheduled as a controlled,
  default-off capability.
- Local-only execution should remain fallback/testing mode, not the permanent
  product boundary.
- External agents and the internal orchestrator may coexist under the same
  service, reducer, gate, review, and promotion boundaries.

## Files Safe To Keep

The following post-`v0.2.0` changes are safe to keep:

- Release/status wording updates in `README.md`, `RELEASE_CHECKLIST.md`, and
  `context/PROJECT_STATE.md`.
- Operator runbook additions in `docs/OPERATOR_NOTES.md`.
- Nested parent-directory rejection in `cosheaf/agent/orchestrator_state.py`
  and `cosheaf/agent/worker_bundle_v2.py`.
- Regression tests for those path-boundary checks.
- Default retrieval and context eval case expansion for graph and SAT/SMT
  pilots.

These changes either preserve current release facts or strengthen safety and
evaluation boundaries that are also required by future MCP/provider access.

## Revert Scope

No post-`v0.2.0` file currently requires direct revert.

The local-only roadmap issue should be handled by targeted rewrite in R.2, not
by resetting `main` or reverting the code/test safety hardening.

## Human-Decision Scope

No post-`v0.2.0` file in this diff requires a new human decision for ambiguous
provider, security, license, or schema behavior.

R.2 should still be reviewed as a roadmap decision because it will replace the
local-only next-focus language with the v0.2.1 Agent Access + Hosted API +
MCP/Skill direction.

## Invariants Checked

- No runtime behavior changed by this audit document.
- No schema files changed by this audit document.
- No verifier adapter behavior changed by this audit document.
- No gate behavior changed by this audit document.
- No accepted-promotion policy changed by this audit document.
- No KB artifacts changed in `v0.2.0..main`.
- No public/private KB boundaries were weakened.
- No hosted provider implementation was added.
- No automatic theorem proving, Lean alignment, or production-readiness claim
  was added.

## Follow-Up

Recommended next task: Phase R / Task R.2, branch
`roadmap-agent-api-mcp`.

R.2 should rewrite `context/CURRENT_MILESTONE.md` and `docs/ROADMAP.md` toward
the v0.2.1 Agent Access + Hosted API + MCP/Skill milestone while preserving
gate, review, promotion, skipped-not-pass, private-context, and no-accepted
direct-write boundaries.
