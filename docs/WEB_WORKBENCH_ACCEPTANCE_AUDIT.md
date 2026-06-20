# Web Workbench Acceptance Audit

Date: 2026-06-20

Issue: #588

Branch: `web-workbench-acceptance-audit`

Decision: **ACCEPTED_WITH_LIMITATIONS**

## 1. Scope

This is the final Longplan B2 acceptance audit for the Cosheaf Web Workbench.
It checks whether the web UI and localhost server can now complete most normal
Cosheaf human governance work in local mode while preserving the repository,
review, gate, verifier, and promotion authority boundaries.

The audit covers the framework repository only:

- repository: `tcs-cosheaf`;
- baseline commit inspected before this audit: `a98508d` (`Write Web Workbench
  runbook`);
- current issue: #588; and
- current branch: `web-workbench-acceptance-audit`.

This audit is documentation-only. It does not add frontend behavior, server
endpoints, schemas, KB artifacts, review records, accepted artifacts, or
promotion rules.

## 2. Decision Summary

The Web Workbench is accepted for the B2 local-workbench milestone with
limitations.

The accepted scope is:

1. static showcase mode for public/demo-safe inspection;
2. live local mode backed by the loopback Cosheaf server;
3. write-capable local Workbench actions that route through
   `cosheaf.server -> cosheaf.app -> storage/services/forge`;
4. preview-before-confirm flows for issue, artifact, source/evidence, context,
   validate/gate, review packet, human review, promotion, and forge actions;
5. automated local happy-path and authority-negative coverage; and
6. sanitized Markdown and LaTeX rendering for formula-bearing TCS text surfaces.

The remaining limitations are not B2 acceptance blockers because they are
outside the local-workbench acceptance definition, but they must not be
overclaimed:

- hosted/collaborative mode is a guard stub, not production SaaS;
- the default localhost server has no server-side `ForgeCredentialProvider`, so
  confirmed GitHub issue/PR creation may return `401 auth_required`;
- static showcase mode is display-only and cannot prove live repository state;
- live-local writes require the loopback server, explicit confirmation, and a
  configured local actor for human review and promotion;
- PR creation in the automated happy path is mocked through a fake `gh`
  runner, not a live network GitHub call;
- external frontend/design review remains advisory, but a read-only Claude
  review of this audit found no blocking overclaims, missing limitations, or
  authority-boundary risks; and
- generated runtime outputs such as `.cosheaf/`, `context/TASKS/`,
  `website/dist/`, and `website/.astro/` remain local outputs and are not
  committed.

## 3. Acceptance Matrix

| Requirement | Result | Evidence |
| --- | --- | --- |
| Issue create/edit/close | Accepted | `docs/SERVER_API.md` documents `/api/issues/preview-create`, `/create`, `/preview-update`, `/update`, `/preview-close`, and `/close`; `tests/test_web_issue_workbench.py` covers preview, confirmed create/update, and close without artifact status mutation; website routes include `/issues/create/`, `/issues/<id>/`, and `/issues/<id>/edit/`. |
| Artifact draft/edit | Accepted | `docs/SERVER_API.md` documents draft artifact create/update endpoints and direct accepted-write refusal; `tests/test_web_artifact_workbench.py` covers draft create/update, live payloads, and accepted direct-write refusal; website routes include `/artifacts/create/`, `/artifacts/<id>/`, and `/artifacts/<id>/edit/`. |
| Source/evidence attach | Accepted | `docs/SERVER_API.md` documents source/evidence preview and confirm endpoints; `tests/test_web_artifact_workbench.py` covers source append, evidence append, missing local evidence warnings, and validation rollback/refusal. |
| Context build | Accepted | `docs/SERVER_API.md` documents context preview/build/latest endpoints; the local E2E test builds context and records the step as real; `/context/<issueId>/` exists as a Workbench route. |
| Validate/gate | Accepted | `docs/SERVER_API.md` documents `/api/validate/run`, `/api/gate/run`, and `/api/gates/latest`; `website/tests/gateWorkbench.test.ts` checks separate pass/fail/skipped counts; the local E2E test runs validate and gate as real steps. |
| Review packet | Accepted | `docs/SERVER_API.md` documents review packet preview/create; `tests/test_web_review_packet_workbench.py` proves preview writes no files and confirmed packet creation remains informational; issue and artifact review-packet routes exist. |
| Human review decision | Accepted | `docs/SERVER_API.md` documents review decision preview/create and the explicit human-review requirements; `tests/test_web_review_decision_workbench.py` covers confirmation, local actor requirement, missing notes, AI reviewer refusal, and keep-draft behavior. |
| Accepted/refuted/obsolete promotion | Accepted with policy limits | `docs/SERVER_API.md` documents promotion readiness, preview, and confirm for `accepted`, `refuted`, and `obsolete`; `tests/test_web_promotion_readiness_workbench.py` covers accepted promotion, refuted lifecycle movement, missing review blocking, local actor requirement, typed confirmation, justification, skipped-verifier blocking, and AI actor refusal. |
| Branch/commit/push/PR | Accepted with local/GitHub limits | `docs/SERVER_API.md` documents forge branch/commit/push/PR endpoints; `tests/test_web_workbench_e2e_happy_path.py` covers branch, commit, PR preview, and mocked PR creation; `tests/test_web_authority_negative_e2e.py` proves direct `main` commit refusal. Live GitHub creation still requires server-side credentials. |
| GitHub issue/PR linking | Accepted with backend credential limit | `docs/SERVER_API.md` documents backend-only GitHub issue/PR create endpoints and `401 auth_required` when credentials are missing; `docs/WEB_WORKBENCH_RUNBOOK.md` documents the default localhost limitation; forge tests and the E2E fake runner cover the behavior without browser tokens. |
| Audit log | Accepted | `cosheaf.web_actions.append_web_action_audit` writes append-only redacted JSONL; `tests/test_web_action_audit.py` proves append and redaction; Workbench endpoint tests assert audit entries for preview, refused, and confirmed actions. |
| Auth/role guard | Accepted as guard stub | `docs/AUTH.md` documents local actor and hosted roles; `tests/test_hosted_auth.py` covers hosted auth required, denied reviewer role, and maintainer promotion using hosted identity. Hosted auth is not production OAuth/GitHub App auth. |
| Markdown and LaTeX rendering | Accepted | `docs/MARKDOWN_MATH_RENDERING.md` documents the shared Markdown/KaTeX renderer; `website/tests/markdownMathRenderer.test.ts` covers `Triangle graph $K_3$`, literal `K_3`, unsafe HTML, unsafe URLs, KaTeX trust, malformed formulas, and token redaction; `website/tests/markdownSurfaceWiring.test.ts` covers display-surface and editor-hint wiring. |
| Static mode still works | Accepted | Static fixture mode is documented in `docs/WEB_WORKBENCH_RUNBOOK.md`; `website/tests/siteData.test.ts` loads fixture data, checks route/data contracts, pagination, authority text, and static fallback; `website/tests/astroConfig.test.ts` checks direct static HTML styling assumptions. |
| Live local mode works | Accepted | `docs/WEB_WORKBENCH_RUNBOOK.md` documents the server and Astro live-local commands; `website/tests/siteData.test.ts` covers live data loading and full fixture fallback; Python Workbench tests exercise `ReadOnlySiteApi` in process. |
| No secret leakage | Accepted | Browser-side token storage is forbidden in docs; `tests/test_web_action_audit.py`, `tests/test_web_authority_negative_e2e.py`, and `website/tests/markdownMathRenderer.test.ts` cover audit/text redaction and browser-token refusal. |
| No accepted authority bypass | Accepted | `tests/test_web_authority_negative_e2e.py` covers direct accepted write refusal, promotion without review refusal, skipped-verifier blocking, public source-metadata blocking, and direct-main commit refusal. |
| No AI-as-human-review | Accepted | `tests/test_web_review_decision_workbench.py` and `tests/test_web_authority_negative_e2e.py` cover AI/Codex reviewer refusal; `docs/SERVER_API.md` and `docs/WEB_WORKBENCH_RUNBOOK.md` document that AI/operator output cannot be human review. |

## 4. Local End-To-End Evidence

`tests/test_web_workbench_e2e_happy_path.py` exercises the B2 local acceptance
workflow through the in-process `ReadOnlySiteApi`:

```text
health/dashboard reads
-> local issue creation
-> pre-accepted artifact creation with source/evidence metadata
-> context build
-> validate
-> gate
-> review packet creation
-> explicit human review decision
-> promotion preview
-> accepted promotion
-> local branch/commit
-> PR preview
-> mocked GitHub PR creation through gh
-> audit and repository-file verification
```

The test records no skipped or deferred step in the scenario report. The PR
creation step is intentionally mocked, while the local repository writes and
policy checks are real fixture-repository operations.

## 5. Authority Boundary Evidence

The negative authority suite verifies fail-closed behavior for the critical
policy boundaries:

- direct accepted artifact creation from the artifact editor is refused and
  audited;
- promotion without human review is refused;
- a required skipped verifier cannot be treated as a promotion pass;
- AI/Codex reviewer identities are refused;
- browser-supplied GitHub tokens are ignored/refused and not logged;
- GitHub PR creation without backend credentials returns `auth_required`;
- public accepted promotion without required source metadata is refused; and
- direct commit attempts on `main` are refused before a commit is made.

These checks preserve the project invariants:

- gate/verifier output is evidence or workflow context, not accepted authority;
- skipped is not pass;
- Lean `#check` style symbol resolution is not semantic alignment;
- local actor is an audit label, not authentication; and
- GitHub issue/PR/CI/review state is collaboration context, not Cosheaf human
  review or promotion authority.

## 6. Verification

Claude read-only review was run after drafting this audit and reported no
blocking findings. It specifically checked for overclaims, missing limitations,
authority-boundary risks, and frontend/user-facing scope drift. Claude review is
advisory only and does not create accepted authority.

The audit branch was verified with the full repository and website command set
as one batch:

```powershell
make lint
make typecheck
make test
make validate
make gate
cd website && npm ci
cd website && npm test
cd website && npm run build
git diff --check
```

Result:

| Command | Result |
| --- | --- |
| `make lint` | passed |
| `make typecheck` | passed, no issues in 275 source files |
| `make test` | passed, 954 tests |
| `make validate` | passed, checked 20 YAML records |
| `make gate` | passed |
| `cd website && npm ci` | passed |
| `cd website && npm test` | passed, 109 tests in 14 files |
| `cd website && npm run build` | passed, 31 pages built |
| `git diff --check` | passed |

Generated runtime outputs from validation, gate, context, and website build were
removed before commit.

## 7. Limitations To Carry Forward

1. Production hosted auth remains future work. The current role model and guard
   tests are sufficient for B2 local acceptance, but not for a hosted product.
2. Default local GitHub issue/PR creation requires a backend credential
   provider that the CLI localhost server does not configure.
3. Static showcase mode remains public/demo display only.
4. The browser never owns GitHub credentials and never writes YAML directly.
5. Review packets, audit logs, rendered Markdown/LaTeX, context packs,
   validation output, gate output, verifier output, and GitHub PR status remain
   workflow context only.

## 8. Decision

ACCEPTED_WITH_LIMITATIONS:

Longplan B2 is accepted for the local Web Workbench milestone. A human can use
the web UI in live-local mode to complete the core Cosheaf workflow:

```text
create issue
-> create/edit draft artifact
-> build context
-> run validate/gate
-> add evidence/source note
-> generate review packet
-> record human review decision
-> promote accepted/refuted/obsolete when policy allows
-> create branch/commit
-> create/publish GitHub PR through backend/forge, with live GitHub writes
   dependent on server-side credentials
-> inspect audit log and final repo state
```

This decision does not accept production hosted mode, browser-side credentials,
AI-as-human-review, gate/verifier-as-authority, skipped-as-pass, direct YAML
promotion, or automatic accepted knowledge creation.
