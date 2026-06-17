# Longplan Completion Audit

Audit date: 2026-06-08

Source plan: `H:\ai4tcs\longplan_fixed.md`

This audit records the current evidence for the fixed longplan work across the
three-repository TCS-Cosheaf ecosystem. It is a documentation and code-surface
audit, not a release tag and not a claim that the project is production-ready.

Supersession note: this document is a historical audit of the older
`longplan_fixed.md` execution plan. Future task ordering is now governed by
`context/CURRENT_MILESTONE.md` and
`docs/CODEX_DEVELOPMENT_PLAN_V11.md`; V3/V4 remain historical evidence for
the older CLI/provider lines. Hosted provider work remains explicit,
default-off, and fake/mocked in tests. The Phase 5 Task 5.3 gating language
below records the old audit state and must not be used to defer or override
the current bounded research-loop plan.

## Summary

All fixed-plan tasks through Phase 8 have merged evidence except Phase 5 Task
5.3. Under the older `longplan_fixed.md` plan, Task 5.3 was not implemented
because the task itself had an unmet precondition around provider-adapter
approval. That historical gating language is superseded for future task
ordering by the current milestone and V11 plan. Provider and hosted-worker work
that exists after this audit must still preserve explicit configuration,
default-off behavior, fake or mocked tests, and the ban on accepted writes or
review/gate/promotion bypass.

Current ecosystem state at the audit point:

- `tcs-cosheaf` is on `main` with the longplan completion audit merged after
  the Phase 8 Task 8.4 milestone proposal.
- `tcs-kb-public` is on `main` with public-KB policy, source-note, backlog, and
  small foundation-artifact work merged.
- `tcs-cosheaf-workspace-template` is on `main` with workspace demo,
  bootstrap, CI smoke, private draft example, and showcase docs merged.
- No open PRs or open issues were present before this audit issue was created.
- The three repositories' local and remote branch state had been cleaned to
  `main` only before the audit branch was opened.

## Task Evidence

| Task | Status | Evidence |
| --- | --- | --- |
| 0.1 Three-repo state audit | Complete | `tcs-cosheaf` PR #70, `docs/CODEX_STATE_AUDIT.md`. |
| 0.2 Durable development plan | Complete | `tcs-cosheaf` PR #72, `docs/CODEX_DEVELOPMENT_PLAN.md`, ADR 0008. |
| 0.3 External tooling ADR | Complete | `tcs-cosheaf` PR #92, `docs/EXTERNAL_TOOLS.md`, ADR 0011. |
| 1.1 Workspace Makefile and demo | Complete | `tcs-cosheaf-workspace-template` PR #24. |
| 1.2 Public KB bootstrap script | Complete | `tcs-cosheaf-workspace-template` PR #26. |
| 1.3 Workspace CI smoke | Complete | `tcs-cosheaf-workspace-template` PR #28. |
| 1.4 Demo issue and private draft | Complete | `tcs-cosheaf-workspace-template` PR #30. |
| 2.1 Public KB contribution templates | Complete | `tcs-kb-public` PR #41. |
| 2.2 Foundation backlog | Complete | `tcs-kb-public` PR #35 and follow-up PR #47. |
| 2.3 MarkItDown source-ingestion policy | Complete | `tcs-cosheaf` PR #94, `docs/SOURCE_INGESTION.md`, ADR 0012. |
| 2.4 MarkItDown local source-ingestion adapter | Complete | `tcs-cosheaf` PR #96. |
| 2.5 One public foundation artifact PR | Complete | `tcs-kb-public` PR #49. |
| 2.6 Public KB policy CI guard | Complete | `tcs-kb-public` PR #45. |
| 3.1 Memory policy docs and ADR | Complete | `tcs-cosheaf` PR #74, `docs/MEMORY_POLICY.md`, ADR 0009. |
| 3.2 ArtifactCard model | Complete | `tcs-cosheaf` PR #76. |
| 3.3 Librarian card builder CLI | Complete | `tcs-cosheaf` PR #78. |
| 3.4 SQLite FTS/BM25 retrieval MVP | Complete | `tcs-cosheaf` PR #80. |
| 3.5 Memory graph and global PageRank | Complete | `tcs-cosheaf` PR #82. |
| 3.6 Personalized PageRank retrieval | Complete | `tcs-cosheaf` PR #84. |
| 3.7 Context pack v2 integration | Complete | `tcs-cosheaf` PR #86. |
| 4.1 Orchestrator state model | Complete | `tcs-cosheaf` PR #88, ADR 0010. |
| 4.2 Task DAG planner stub | Complete | `tcs-cosheaf` PR #98. |
| 4.3 Reducer and worker bundle v2 | Complete | `tcs-cosheaf` PR #100. |
| 4.4 Local worker runner integration | Complete | `tcs-cosheaf` PR #102. |
| 4.5 Agent dry-run workflow | Complete | `tcs-cosheaf` PR #104. |
| 4.6 CodeGraph dev-only tooling | Complete | `tcs-cosheaf` PR #106. |
| 5.1 Provider-neutral model interface | Complete | `tcs-cosheaf` PR #108, ADR 0013. |
| 5.2 Role prompt contracts | Complete | `tcs-cosheaf` PR #110, `docs/AGENT_ROLES.md`. |
| 5.3 Hosted provider adapter behind explicit flag | Historical gated state, not implemented in this audit | Under `longplan_fixed.md`, this remained gated by provider-adapter approval. Future scheduling is superseded by the CLI-first plan; current code at this audit point intentionally kept only `FakeModelProvider`, and hosted execution was not enabled. |
| 5.4 Headroom default-off scaffold | Complete | `tcs-cosheaf` PR #112. |
| 6.1 Formal library manifest audit | Complete | `tcs-cosheaf` PR #114. |
| 6.2 Lean external library `#check` adapter | Complete | `tcs-cosheaf` PR #116. |
| 6.3 Formal Link Gate hardening | Complete | `tcs-cosheaf` PR #118. |
| 6.4 Formal link pilot | Complete | `tcs-cosheaf` PR #120. |
| 7.1 Retrieval eval harness | Complete | `tcs-cosheaf` PR #122. |
| 7.2 Context pack regression eval | Complete | `tcs-cosheaf` PR #124. |
| 7.3 Structured run logging | Complete | `tcs-cosheaf` PR #126. |
| 7.4 Optional OpenTelemetry adapter | Complete | `tcs-cosheaf` PR #129. |
| 8.1 Three-repo release checklist | Complete | `tcs-cosheaf` PR #138. |
| 8.2 Showcase demo docs | Complete | `tcs-cosheaf-workspace-template` PR #32. |
| 8.3 Understand-Anything onboarding note | Complete | `tcs-cosheaf` PR #142. |
| 8.4 v0.2.0 milestone proposal | Complete | `tcs-cosheaf` PR #144, ADR 0014. |

## Historical Code-Surface Audit

At the 2026-06-08 audit point, the framework code surface matched the
conservative plan boundaries:

- Hosted model provider execution is not implemented as a runtime path.
- `FakeModelProvider` is the only implemented provider.
- Role contracts require `provider: fake`, `hosted_llm_enabled: false`, and
  `network_policy: disabled`.
- The local orchestrator runner and local worker runner execute explicit local
  commands only and do not call hosted LLMs, use network services, write
  accepted knowledge, request human review, or promote artifacts.
- MarkItDown, Headroom, CodeGraph, and Understand-Anything are optional,
  bounded, and excluded from the source-of-truth path.
- Formal links remain metadata unless a checker actually runs and records a
  result. External Lean `#check` checks import/symbol resolution only.
- Skipped verifier results remain skipped, not pass.
- Public-KB accepted artifacts still require source metadata and human review;
  validation and gate success are not substitutes for review.

## Gated Follow-Up

Future hosted provider work should follow the current milestone and active
development plan, not this historical audit's old task ordering. That work
must stay explicit, opt-in, default-off, fake-transport-tested, network-free in
tests, and unable to write accepted knowledge or bypass review/gate/promotion.

## Verification Expectation

For this audit PR, run the full framework verification ladder:

```bash
make lint
make typecheck
make test
make validate
make gate
git diff --check
```

This audit does not replace a future release audit before a `v0.2.0` tag.
