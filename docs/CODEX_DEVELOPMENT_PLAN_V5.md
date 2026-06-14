# TCS-Cosheaf Development Plan v5

Status: current post-`v0.2.2` durable plan

This plan follows the published `v0.2.2` Provider Transport + Agent Workflow
Hardening release. It starts from the release closeout recorded in
[`docs/releases/v0.2.2.md`](releases/v0.2.2.md),
[`context/CURRENT_MILESTONE.md`](../context/CURRENT_MILESTONE.md), and
[`context/PROJECT_STATE.md`](../context/PROJECT_STATE.md).

The next target is:

```text
v0.2.3 Verification Evidence Hardening
```

The goal is to make verifier requests, verifier results, failure evidence,
counterexample evidence, optional SAT/SMT/Lean runs, and promotion-readiness
reporting more explicit, reviewable, and auditable without turning Cosheaf into
an automatic theorem prover or a production hosted multi-agent system.

## Baseline

At the start of this plan:

- `tcs-cosheaf` package metadata and `cosheaf.__version__` are `0.2.2`.
- The `v0.2.2` tag and GitHub release are published.
- `tcs-cosheaf-workspace-template` active demo, CLI-agent, provider-preview,
  and fake-provider smoke paths pin or default to `tcs-cosheaf@v0.2.2`.
- `tcs-kb-public` CI installs `tcs-cosheaf@v0.2.2`.
- CLI remains the first agent interface and the human/CI oracle.
- Provider real-run support exists but remains explicit, default-off, and
  excluded from CI/default tests.
- WorkerBundle v2 preserves verification requests, uncertainty, failed
  attempts, and candidate counterexamples as review-only material.
- Minimal optional Python, SAT, SMT, plain Lean, and external Lean library
  reference checker surfaces exist.
- The current formal-link documentation file is
  [`docs/FORMALIZATION_LINKS.md`](FORMALIZATION_LINKS.md). Future work should
  update that file unless a dedicated rename PR intentionally changes the
  filename.

## Non-Negotiable Invariants

Knowledge lifecycle:

- Accepted artifacts require validation, gates, review where policy requires
  it, and explicit promotion.
- Worker/provider/verifier output must not write directly to `kb/accepted/`.
- AI/provider review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier, provider, SAT, SMT, or Lean results are not passes.
- Public KB accepted artifacts require source metadata and human review.
- Public KB artifacts must not depend on private KB artifacts.
- Private KB artifacts may depend on public accepted artifacts.

Verification and formal links:

- A `verifier_request` is a request for a verifier or human to check
  something. It is not evidence that any verifier ran.
- A `verifier_result` is evidence from an executed checker, adapter, or
  documented manual review path. Its state must distinguish `pass`, `fail`,
  `error`, `skipped`, `unknown`, and not-applicable cases where relevant.
- A `candidate_counterexample` is proposed refuting evidence. It is not a
  checked counterexample and must not be treated as an accepted refutation.
- A `checked_counterexample` requires explicit verification evidence or human
  review metadata and must record the checking method.
- Formal links are metadata unless a checker actually records a result.
- Lean `#check` success means import and symbol resolution only. It does not
  prove informal/formal semantic alignment.
- Cosheaf does not claim automatic theorem proving, Lean/mathlib/CSLib proof
  checking of informal statements, or automatic autoformalization.

Provider and MCP boundary:

- Real provider calls remain default-off and require explicit configuration,
  credentials, policy scope, context preview, network permission, and operator
  consent.
- CI and default tests must not make live provider calls or require API keys.
- Provider output may become WorkerBundle, draft proposal, draft artifact
  input, or review context only.
- `v0.2.3` does not expand provider authority, add provider MCP tools, add
  controlled-write MCP, or make MCP the primary agent path.

Public KB boundary:

- Public KB growth remains small and source-reviewed.
- Accepted public artifacts require complete source metadata and human review.
- Proof sketches are explanatory and source-reviewed; they are not
  machine-checked proofs unless a checker actually records that evidence.
- No private conjectures, unpublished research ideas, or unreviewed LLM output
  may enter accepted public KB paths.

## Phase A: v0.2.2 Release Closeout

Status: complete.

The `v0.2.2` tag and GitHub release are published. Release smoke installs the
tag, workspace-template pins active workflows to `v0.2.2`, and public KB CI
installs `v0.2.2`. The closeout does not add runtime behavior.

## Phase B: Plan And ADR Landing

### B.1 Land v0.2.3 Verification Evidence Roadmap

Status: this document and ADR 0022.

This task makes V5 the current durable plan, marks V4 historical after the
`v0.2.2` release closeout, adds the architecture decision for the `v0.2.3`
verification/evidence line, and points the current milestone to C.1. It does
not implement runtime behavior or change schemas.

## Phase C: Verifier Evidence Model And Normalized Result Taxonomy

### C.1 Verifier Evidence Status Audit

Status: complete in `docs/VERIFIER_EVIDENCE_AUDIT.md`.

Audit current verifier adapters, gate integration, result records, formal-link
surfaces, and tests before changing any schema or runtime behavior.

The audit must answer:

- Which verifier adapters actually invoke external or local tools?
- Which result states already exist and where are they serialized?
- Which logs, commands, cwd, tool versions, exit codes, stdout, and stderr are
  captured?
- Which evidence can block promotion and where is that enforced?
- Where is skipped-not-pass tested?
- Where is Lean `#check` documented and tested as symbol/import resolution
  only?
- Which result records are source-of-truth versus generated sidecars?

### C.2 Evidence Record Taxonomy

Status: verifier evidence record v1 is complete.

Define a normalized evidence vocabulary before broadening verifier behavior.
The design should cover:

- `verifier_request`;
- `verifier_result`;
- `candidate_counterexample`;
- `checked_counterexample`;
- `pass`;
- `fail`;
- `error`;
- `skipped`;
- `unknown`;
- not-applicable cases.

Schema or DTO changes are implemented only after the audit identifies the
current compatibility surface. Backward compatibility with existing verifier
results is required unless a narrow migration is explicitly justified.

### C.3 Gate And Promotion Evidence Reporting

Status: read-only promotion-readiness reporting is implemented in the current
framework line.

Improve reports so operators can see which evidence is missing, skipped,
failed, stale, or sufficient for a specific lifecycle decision. Reporting must
not promote artifacts or convert skipped results into passes.

The implemented `cosheaf promotion readiness` CLI supports artifact and issue
targets, emits deterministic JSON, reports `accepted_write_performed: false`,
and distinguishes missing human review, failed verifiers, skipped verifiers,
missing source metadata, dependency risk, private dependencies, draft status,
readonly KB roots, and repository gatekeeper blockers. It is advisory and does
not replace `cosheaf artifact promote`.

## Phase D: Optional SAT/SMT/Lean Backend Deepening

Deepen optional backend ergonomics without making any external tool mandatory.

Potential work:

- SAT: clearer DIMACS command metadata, model/counterexample capture, and
  unavailable-tool skips.
- SMT: clearer solver command metadata, `sat`/`unsat`/`unknown` distinctions,
  timeout handling, and model capture where available.
- Lean: clearer plain-file and external-library `#check` logs, lake/lean
  version capture when available, and better skipped/error diagnostics.

All tests must use fake backends, mocked command runners, local fixtures, or
tool-absence skips. CI must not require SAT, SMT, Lean, lake, CSLib, mathlib,
network access, or API keys.

## Phase E: Failure And Counterexample Evidence Workflow

Strengthen the path from worker/provider output into reviewable failure and
counterexample evidence:

- Preserve failed proof attempts without treating them as proof artifacts.
- Preserve candidate counterexamples without treating them as checked
  refutations.
- Require explicit checking method and result before calling a counterexample
  checked.
- Make context packs and review reports surface known failures and candidate
  counterexamples clearly.

## Phase F: Review And Promotion Readiness Reporting

Add operator-facing readiness summaries that explain what remains before a
draft artifact can be reviewed or promoted:

- source metadata status;
- human-review status;
- dependency status;
- verifier evidence status;
- formal-link status;
- skipped/error/fail evidence;
- public/private boundary status.

Readiness reports are advisory. They must not bypass validation, gates, human
review, verifier evidence requirements, or `cosheaf artifact promote`.

The C.3 promotion-readiness CLI provides the first artifact/issue-scoped
read-only report. Later Phase F work may broaden review UX and evidence
explanations, but it must keep the same no-accepted-write and skipped-not-pass
boundaries.

## Phase G: Three-Repository v0.2.3 Readiness

Before a `v0.2.3` release candidate:

- The framework command ladder must pass.
- The ecosystem smoke matrix must cover framework, workspace-template, and
  public KB against local checkouts.
- Workspace-template must continue to show default fake/local workflows and no
  default real provider calls.
- Public KB policy guard must continue to enforce source metadata, human
  review for accepted content, no private dependencies, and skipped-not-pass
  boundaries.
- Release notes must remain conservative and must not claim production
  readiness, automatic theorem proving, automatic accepted promotion, or
  informal/formal semantic alignment.

## Per-PR Requirements

Each task should remain one issue, one branch, one PR, and one reviewable
increment. Pull request summaries should include:

```text
Goal:
Scope:
Files changed:
Tests run:
Commands unavailable:
Invariants checked:
Security/privacy impact:
Known limitations:
Follow-up tasks:
```

Every PR should attempt the repository command ladder when available:

```bash
make lint
make typecheck
make test
make validate
make gate
git diff --check
```

Documentation-only PRs should still run the full ladder when feasible because
project workflow docs can affect validation, gate expectations, and release
readiness. If a command cannot run, report the exact reason. Do not report
skipped or unavailable checks as passes.

## Completion Guardrails

Before completing each phase, check:

- no docs make MCP the primary or required agent path;
- no docs describe the product as production-ready;
- no real provider call enters CI/default tests;
- no API key, bearer token, environment dump, hidden reasoning, or unapproved
  private context enters committed logs;
- provider output cannot directly write accepted knowledge;
- AI/provider review is never marked as human review;
- skipped provider/verifier results are not passes;
- Lean `#check` is not described as semantic alignment;
- retrieval ranking cannot bypass public/private policy;
- workspace-template demos do not default to real API calls;
- public KB changes remain policy/content scoped;
- public KB accepted content remains source-reviewed and human-reviewed;
- any public interface changes update `context/INTERFACE_REGISTRY.md`;
- new behavior has tests;
- release notes do not claim production readiness.
