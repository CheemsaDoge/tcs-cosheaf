# Three-Repository Release Checklist

This checklist records the `v0.4.0` Strategy Planner + Research Task Graph
release-candidate state after the published `v0.3.0` Checked Evidence +
Research Run Loop release, the published `v0.2.4` Artifact Failure Memory +
Attempt Traceability release, the `v0.2.3` Verification Evidence Hardening
release, the `v0.2.2` Provider Transport + Agent Workflow Hardening release,
the `v0.2.1` CLI Agent Access + Hosted Provider Gateway prerelease, the
`v0.2.0` local-MVP release, and the `v0.1.1` Formal Link Layer support
baseline. It is an operator checklist for the framework package, public KB,
and workspace template together. It is not a production-readiness claim.

`v0.1.1` remains the downstream tag baseline for early formal-link metadata.
`v0.2.0` packages the deterministic local-MVP workflow. `v0.2.1` packages the
CLI-first agent-access layer, controlled draft/staging write CLI, provider
gateway, fake/mocked hosted-worker path, and conservative release docs.
`v0.2.2` packages the default-off real-provider transport path, context-send
policy matrix, provider log leak scanner, failure/counterexample workflow
hardening, provider workflow evals, and ecosystem smoke matrix. Do not assume a
downstream pin to `@v0.2.0` includes `v0.2.1` or `v0.2.2` agent/provider
surfaces.
`v0.2.3` packages verification-evidence hardening after the readiness audit.
Package metadata records `0.2.3`; the public tag, GitHub release, release
smoke, and downstream workspace/public KB pin updates are complete.
`v0.2.4` packages Artifact Failure Memory + Attempt Traceability after the
readiness audit. Package metadata records `0.2.4`; the public tag, GitHub
release, release smoke, and downstream workspace/public KB pin updates are
complete.
`v0.3.0` packages checked counterexample evidence, research-run provenance,
external-operator run-loop docs, downstream demo/policy surfaces, and
integration/eval smoke coverage. Package metadata records `0.3.0`; the public
tag, GitHub release, release smoke, and downstream pin updates are complete.
`v0.4.0` packages Strategy Planner + Research Task Graph surfaces. Package
metadata records `0.4.0` in the release-candidate branch; the public tag,
GitHub release, post-tag release smoke, and downstream pin updates are not
complete yet.

## Scope

- Framework repository: `tcs-cosheaf`.
- Public knowledge repository: `tcs-kb-public`.
- User entry point: `tcs-cosheaf-workspace-template`.
- Current framework package metadata version:
  `0.4.0`.
- Current downstream dependency baseline for formal-link metadata:
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.1.1`.
- Intended downstream dependency for local-MVP workflows:
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.0`.
- Intended downstream dependency for CLI-agent/provider-gateway workflows after
  publication:
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.1`.
- Downstream dependency for provider-transport/workflow-hardening workflows:
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.2`.
- Downstream dependency for verification-evidence-hardening workflows:
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.3`.
- Downstream dependency for artifact-failure-memory workflows:
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.4`.
- Intended downstream dependency for checked-evidence and research-run
  workflows after publication:
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.3.0`.
- Intended downstream dependency for Strategy Planner + Research Task Graph
  workflows after publication:
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.4.0`.

## v0.4.0 Release Candidate Baseline

`docs/releases/v0.4.0.md` is the release-candidate note for Strategy Planner +
Research Task Graph. This release-candidate task prepares package metadata and
status docs; a later publication closeout must create the public tag, publish
the GitHub release, run post-tag release smoke, and update downstream pins.

- [x] Strategy/task-graph model, schema, deterministic planner, storage, CLI,
  docs, interface registry updates, and tests are merged.
- [x] Planner/run-loop integration, strategy review export, context/retrieval
  surfacing, promotion-readiness advisory warnings, deterministic evals, and
  security tests are merged.
- [x] Strategy plans remain guidance only and do not create proof, checked
  evidence, verifier evidence, verifier pass, gate pass, human review,
  accepted status, accepted refutation, or promotion authority.
- [x] Workspace-template strategy demo and public KB strategy-plan policy
  surfaces are merged.
- [x] Framework ecosystem-smoke matrix includes strategy-planner eval,
  workspace-template strategy demo, and public KB strategy-plan policy docs.
- [x] Optional verifier, provider, network, SAT, SMT, Lean, lake, and MCP rows
  remain skipped, not pass, when unavailable.
- [x] `v0.4.0` release-candidate metadata is prepared in the
  release-candidate branch.
- [ ] The annotated `v0.4.0` tag is published.
- [ ] GitHub release `v0.4.0 Strategy Planner + Research Task Graph` is
  published.
- [ ] Release smoke from
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.4.0` passed.
- [ ] Workspace-template active pins moved to `@v0.4.0` after tag publication
  and release smoke.
- [ ] Public KB CI moved to `@v0.4.0` after tag publication and release smoke.

## v0.3.0 Published Release Baseline

`docs/releases/v0.3.0.md` is the published release note for Checked Evidence +
Research Run Loop. The release-candidate task prepared package metadata and
status docs; the later publication closeout created the public tag, published
the GitHub release, ran post-tag release smoke, and updated downstream pins.

- [x] Checked counterexample evidence is implemented as non-authoritative
  review evidence, separate from candidate counterexamples, verifier evidence,
  human review, accepted refutation, accepted status, and promotion authority.
- [x] Controlled checked-evidence CLI staging writes only under
  `reviews/evidence/checked-counterexamples/` and refuses accepted-path,
  path-traversal, duplicate, readonly-root, and authority-spoofing inputs.
- [x] Research-run records are implemented as repository-local provenance
  with start, append, finalize, show, evidence-report, export-review, and
  replay-plan CLI surfaces.
- [x] Research-run records remain provenance only and do not create proof,
  human review, verifier pass, gate pass, accepted status, or promotion
  authority.
- [x] External operator docs describe the CLI/Git run loop without embedding
  GPT, Claude, hosted providers, or MCP as the default runtime.
- [x] Workspace-template research-run demo and public KB checked-evidence
  policy surfaces are merged.
- [x] Integration/eval/ecosystem smoke coverage includes checked-evidence eval,
  research-run eval, workspace-template research-run demo, and public KB
  checked-evidence policy rows.
- [x] Optional verifier, provider, network, SAT, SMT, Lean, lake, and MCP rows
  remain skipped, not pass, when unavailable.
- [x] `v0.3.0` release-candidate metadata was prepared in the release-candidate
  branch.
- [x] The annotated `v0.3.0` tag is published.
- [x] GitHub release `v0.3.0 Checked Evidence + Research Run Loop` is
  published.
- [x] Release smoke from
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.3.0` passed.
- [x] Workspace-template active pins moved to `@v0.3.0` after tag publication
  and release smoke.
- [x] Public KB CI moved to `@v0.3.0` after tag publication and release smoke.

## v0.2.4 Readiness Audit Baseline

`docs/releases/v0.2.4.md` is the published release note for Artifact Failure
Memory + Attempt Traceability. The earlier readiness audit and release
candidate did not create the public tag, publish a GitHub release, or update
downstream pins; the later maintainer release action completed those steps
after the release-candidate PR merged cleanly.

- [x] Artifact-level `failure_log` is optional and backward compatible.
- [x] `cosheaf artifact failures` is read-only and reports an explicit
  non-authority notice.
- [x] Controlled failure-log writes are limited to writable
  draft/pre-accepted artifacts and reject accepted-path/status, readonly-root,
  and authority-spoofing inputs.
- [x] WorkerBundle failed attempts can be planned or appended into
  failure-log entries without granting proof, review, verifier, checked
  counterexample, accepted-status, or promotion authority.
- [x] Artifact cards, memory search, context packs, and promotion-readiness
  reports surface failure memory as review context only.
- [x] Public-only context excludes private failure-log text and private
  artifact IDs.
- [x] Workspace-template failure-memory demo and public KB failure-log policy
  surfaces are in place.
- [x] Security and deterministic eval regression coverage exists for
  authority spoofing, public/private scope, retrieval, repeated failed
  directions, and candidate-counterexample mislabel boundaries.
- [x] At audit start, all three repositories had no open issues and no open
  pull requests before the audit issue was created.
- [x] `v0.2.4` release-candidate metadata update is prepared in the release
  candidate branch.
- [x] The annotated `v0.2.4` tag is published.
- [x] GitHub release `v0.2.4 Artifact Failure Memory` is published.
- [x] Release smoke from
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.4` passed.
- [x] Workspace-template active pins moved to `@v0.2.4` after tag publication
  and release smoke.
- [x] Public KB CI moved to `@v0.2.4` after tag publication and release smoke.

## v0.2.2 Release Delta

The `v0.2.2` tag and release were published after `docs/releases/v0.2.2.md`,
the readiness audit, the pre-tag audit, and the release-candidate PR recorded
no publication blockers.

- [x] Optional OpenAI-compatible HTTP transport exists and remains default-off.
- [x] Explicit `provider real-run` fails closed without context preview,
  consent, network permission, endpoint/key config, and private-context consent
  when needed.
- [x] CI and default tests use fake, mocked, or local non-live-network fixtures;
  they do not call real providers or require API keys.
- [x] Provider logs and run records have redaction and leak-scanner regression
  coverage.
- [x] Failure/counterexample workflows have deterministic eval coverage.
- [x] Workspace-template provider setup and public-preview smoke docs are
  updated without adding real provider calls to default demos.
- [x] Public KB changes since the v0.2.1 compatibility update are explicitly
  scoped policy/content PRs and do not add or promote accepted artifacts.
- [x] MCP remains optional read-only adapter work; controlled-write MCP and
  provider MCP tools remain out of scope.

## v0.2.3 Completed Planning Baseline

`v0.2.3` was the framework milestone after the `v0.2.2` release closeout. It
is Verification Evidence Hardening, not provider/MCP expansion.

- [x] `docs/CODEX_DEVELOPMENT_PLAN_V5.md` records the completed durable
  `v0.2.3` plan.
- [x] ADR 0022 records the verification/evidence hardening decision.
- [x] `docs/CODEX_DEVELOPMENT_PLAN_V4.md` is marked historical/completed after
  the `v0.2.2` closeout.
- [x] The verifier evidence status audit identifies existing verifier
  adapters, result records, log capture, gate integration, promotion evidence,
  skipped-not-pass tests, and Lean `#check` boundaries before runtime/schema
  changes.
- [x] The `verifier_result` record v1 schema/model is implemented for
  serialized verifier evidence records; request and counterexample records
  remain follow-up work.
- [x] Promotion-readiness reporting is read-only, reports
  `accepted_write_performed: false`, distinguishes missing review, failed and
  skipped verifier results, missing source metadata, dependency risk, private
  dependencies, draft status, readonly KB roots, and repository gatekeeper
  blockers, and does not replace `cosheaf artifact promote`.
- [x] WorkerBundle v2 typed counterexample candidate records distinguish
  proposed/needs-check candidates from checked candidate evidence while still
  keeping all candidates review-only and outside accepted promotion authority.
- [x] Failure-preserving review request generation writes or previews draft
  informational `reviews/requests/*.yaml` records from WorkerBundle v2
  assumptions, uncertainty, failed attempts, verifier requests, counterexample
  candidates, risk flags, next steps, and limitations without creating human
  review, verifier results, accepted knowledge, or promotion authority.
- [x] Follow-up evidence taxonomy work is now addressed in the active
  `v0.3.0` line through the checked counterexample evidence surface. This was
  not part of the `v0.2.3` release itself.
- [x] SAT result-depth fixture coverage keeps the SAT solver optional and
  covers satisfiable, unsatisfiable, malformed DIMACS, timeout, and
  unavailable-solver paths without treating skipped as pass.
- [x] SMT result-depth fixture coverage keeps the SMT solver optional and
  covers `sat`, `unsat`, `unknown`, malformed SMT-LIB, timeout, and
  unavailable-solver paths without treating skipped or unknown as pass.
- [x] Lean external reference ergonomics keeps all external tools optional,
  preserves unavailable Lean/lake as skipped or unavailable rather than pass,
  records missing import/symbol stderr logs through fake-backend coverage, and
  keeps external `#check` documented as symbol/import resolution only.
- [x] The v0.2.3 ecosystem readiness matrix includes framework verifier
  evidence eval smoke, workspace-template verifier-evidence demo coverage, a
  public KB verifier-policy self-test, and an optional verifier availability
  row that counts unavailable SAT/SMT/Lean/lake tools as skipped rather than
  pass.

## v0.2.3 Release Readiness Audit, Candidate, And Publication

`docs/releases/v0.2.3.md` is now the published release note. The maintainer
release action created and verified the public tag, GitHub release, release
smoke, and downstream pin updates.

- [x] The previous readiness-audit PR recorded that package metadata and
  `cosheaf.__version__` still reported `0.2.2` before the release-candidate
  branch.
- [x] The audit does not create a tag, GitHub release, downstream pin update,
  or runtime behavior.
- [x] Verifier evidence records are stable enough for the release-candidate
  task through `VerifierEvidenceRecord` v1 serialization.
- [x] SAT, SMT, plain Lean, and external Lean reference paths have
  fake-backend, mocked, local-fixture, or tool-absence coverage without making
  optional tools mandatory.
- [x] Skipped verifier, provider, optional-tool, and network rows remain
  separate from pass results.
- [x] Candidate counterexamples remain review-only candidates until explicitly
  checked and reviewed through later workflow.
- [x] Promotion-readiness reports remain read-only and record
  `accepted_write_performed: false`.
- [x] The three-repository readiness matrix covers local framework,
  workspace-template, and public KB compatibility without default remote
  clones or network installs.
- [x] At audit start, the only open issue was the audit issue itself and there
  were no open PRs.
- [x] The release-candidate branch updates `pyproject.toml` and
  `cosheaf.__version__` to `0.2.3`.
- [x] The release-candidate note states optional verifier evidence hardening,
  skipped-not-pass preservation, no automatic theorem proving, no automatic
  accepted promotion, no production hosted multi-agent claim, and unchanged
  provider/MCP boundaries.
- [x] The release-candidate branch reran the full local command ladder and
  ecosystem matrix before any tag or release was created.
- [x] The public `v0.2.3` tag was created only after the release-candidate PR
  merged cleanly and main was re-synced.
- [x] GitHub release `v0.2.3 Verification Evidence Hardening` is published.
- [x] Release smoke from
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.3` passed.
- [x] Workspace-template active pins moved to `@v0.2.3` after tag publication
  and release smoke.
- [x] Public KB CI moved to `@v0.2.3` after tag publication and release smoke.

## Framework Checklist

### v0.2.2 Pre-Tag Audit

- [x] Issue 261 created to track the pre-tag release audit.
- [x] `pyproject.toml` and `cosheaf.__version__` both record `0.2.2`.
- [x] `python -m cosheaf.cli version --json` reports `0.2.2`.
- [x] No open PRs or issues existed before issue 261 was opened for this
  audit.
- [x] `v0.2.2` was absent locally and on `origin` at pre-tag audit time.
- [x] README, release notes, roadmap, and current milestone avoid production
  overclaims.
- [x] Release notes keep provider transport default-off and state that
  CI/default tests do not call real providers.
- [x] Default ecosystem matrix reports network-install rows as `skipped`, not
  `pass` (4 pass, 0 fail, 2 skipped in the pre-tag audit run).
- [x] The plan/document naming difference is recorded:
  `docs/FORMAL_LINKS.md` is referenced by the v5 runbook, while the current
  repository document is `docs/FORMALIZATION_LINKS.md`.
- [x] Tag publication proceeded after the audit PR was merged and the
  maintainer release action re-verified main and tag absence.

### Version And Tag

- [x] `pyproject.toml` records package version `0.4.0`.
- [x] `cosheaf.__version__` records `0.4.0`.
- [x] Remote tag `v0.1.1` exists as the formal-link support baseline.
- [x] Remote tag `v0.2.0` exists as the local-MVP baseline.
- [x] Remote tag `v0.2.1` points to the reviewed default-branch merge commit.
- [x] Remote tag `v0.2.2` exists and points to the reviewed post-audit main
  commit.
- [x] Remote tag `v0.2.3` exists and points through the annotated tag to the
  reviewed release-candidate main commit.
- [x] Remote tag `v0.2.4` exists and points through the annotated tag to the
  reviewed release-candidate main commit.
- [x] Remote tag `v0.3.0` exists and points through the annotated tag to the
  reviewed release-candidate main commit.
- [x] Remote tag `v0.4.0` is absent before publication. It must remain absent
  until the release-candidate PR merges cleanly and the maintainer publication
  action creates the annotated tag.
- [x] Downstream repositories pin to an explicit release tag rather than
  tracking `main`.
- [x] Historical workspace-template artifact-failure-memory verification remains
  recorded against `@v0.2.4`.
- [x] Workspace-template and public KB active pins moved to `@v0.2.3` only
  after v0.2.3 tag publication and release smoke succeeded.
- [x] Workspace-template and public KB active pins moved to `@v0.2.4` only
  after v0.2.4 tag publication and release smoke succeeded.
- [x] Workspace-template and public KB active pins moved to `@v0.3.0` only
  after v0.3.0 tag publication and release smoke succeeded.
- [ ] Workspace-template and public KB active pins moved to `@v0.4.0` only
  after v0.4.0 tag publication and release smoke succeeded.

### License

- [x] `LICENSE` contains Apache License 2.0.
- [x] README license text states Apache License 2.0.
- [x] `pyproject.toml` project metadata uses `Apache-2.0`.

### CI And Local Verification

Run these before framework release-candidate, release-followup, or consistency
PRs:

- [x] `make lint`
- [x] `make typecheck`
- [x] `make test`
- [x] `make validate`
- [x] `make gate`
- [x] `git diff --check`
- GitHub Actions checks for release-candidate PRs are verified in GitHub PR
  status before merge rather than recorded as a static checkbox in this file.

Skipped verifier output is not a pass. Optional-tool skips must stay visible in
gate output and release notes.

### Validate/Gate Status

- [x] `cosheaf validate` passes on the framework checkout.
- [x] `cosheaf gate run` passes or reports only intentional nonblocking
  skipped/not-applicable gates.
- [x] `cosheaf gate run --pr-checklist <local-pr-body.md>` passes before a PR
  is marked ready when a local PR body draft is available.
- [x] Gate reports are generated under `.cosheaf/reports/` and are not
  committed unless explicitly persisted for review.

### Smoke And Evaluation Status

- [x] `python scripts/release_smoke.py --source
  git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.2` runs against a
  clean environment after the `v0.2.2` tag exists.
- [x] `python scripts/release_smoke.py --source
  git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.3` runs against a
  clean environment after the `v0.2.3` tag exists.
- [x] `python scripts/ecosystem_smoke.py --cosheaf cosheaf` runs without
  cloning remote repositories.
- [x] `python scripts/ecosystem_smoke.py --matrix --include-network --framework-tag v0.2.3 --cosheaf "python -m cosheaf.cli" --framework-root . --workspace-template-root ..\tcs-cosheaf-workspace-template --public-kb-root ..\tcs-kb-public --json`
  reports a structured three-repository compatibility matrix. The default
  no-network run executes local framework smoke, framework verifier-evidence
  eval smoke, workspace-template CLI-agent demo, workspace-template
  fake-provider smoke, workspace-template verifier-evidence demo, public KB
  policy guard, and public KB verifier-policy self-test. With
  `--include-network`, the framework tag release smoke and workspace-template
  install demo ran against `v0.2.3`; the matrix reported 9 pass, 0 fail, and 1
  skipped. The skipped row was optional verifier availability because
  SAT/SMT/Lean/lake tools were unavailable, and it was not counted as pass.
- [x] The ecosystem smoke covers a readonly public KB root, writable private KB
  root, private draft depending on public accepted knowledge, validation,
  gatekeeper, index rebuild, and context-pack generation.
- [x] Expected policy failures in smoke helpers are verified as failures, not
  described as passes.
- [x] Retrieval, context-pack, security, agent-workflow, provider-workflow,
  failure/counterexample, verifier-evidence, artifact failure-memory, and
  ecosystem readiness evals remain deterministic and do not require network
  access or API keys.

## Agent Access And Provider Status

Framework surfaces introduced through `v0.2.2` and retained in the `v0.2.3`
release:

- CLI-first operator workflow with stable JSON output for core read/check
  commands.
- Controlled draft artifact, staged source-note, worker-bundle submission, and
  draft review-request CLI commands.
- Typed service-layer DTOs and stable `ErrorResult` codes for agent-facing
  workflows.
- Provider gateway with deterministic fake provider and OpenAI-compatible
  mocked transport boundary.
- Provider CLI commands for `list`, `config-check`, `preview-send`, and
  `fake-run`.
- Optional stdlib OpenAI-compatible HTTP transport, default-off and explicitly
  configured/injected.
- Explicit `provider real-run` CLI path with inline context preview, send
  consent, network permission, endpoint/key configuration, and private-context
  consent checks.
- Provider context-send policy matrix for public/private preview scope.
- Provider log leak scanner and redacted provider run-record regression
  coverage.
- WorkerBundle v2 failure/counterexample preservation fields and reducer
  warnings.
- Role contracts for structured uncertainty, failures, verifier requests,
  candidate counterexamples, formal-link limitations, and no-claim-invention
  librarian summaries.
- Provider malformed-output recovery and deterministic provider-workflow evals.
- Failure/counterexample workflow evals.
- Three-repository ecosystem smoke matrix.
- Role-specific hosted worker service for fake or mocked provider worker
  calls.
- Internal orchestrator dispatch to hosted workers through explicit provider
  selection.
- Agent-access security regression tests and agent workflow evaluation suite.
- Optional operator Skill package.
- Optional read-only MCP surface. MCP is not required for `v0.2.2`.

Boundaries:

- Built-in real hosted HTTP transport is not enabled by default.
- CI and default tests must not call real hosted providers.
- Real provider paths require explicit configuration, credentials, policy
  scope, preview, and consent.
- Provider output is untrusted and may become WorkerBundle, typed sub-result,
  draft proposal, draft artifact input, or review context only.
- Provider output must not write accepted knowledge, mark human review, or
  bypass reducers, validation, gates, verifier results, review, or promotion.
- API keys, secrets, hidden reasoning, and unapproved private context must not
  be committed or logged.

## Workspace Template Checklist

- [x] The template remains the recommended user entry point.
- [x] The one-command demo runs from a clean clone.
- [x] Makefile shortcuts remain thin wrappers around documented `cosheaf`
  commands.
- [x] CLI-agent workflow commands demonstrate JSON output.
- [x] Fake provider smoke uses the deterministic fake provider only.
- [x] `.env.example`, if present, names variables only and contains no secrets.
- [x] `kb/public` is documented as seed/demo content unless replaced or mounted
  from `tcs-kb-public`.
- [x] `kb/private` is documented as the writable private research overlay.
- [x] The docs warn users not to manually merge framework, public KB, and
  private workspace repositories into one mixed tree.
- [x] Runtime output stays ignored under `.cosheaf/` or another ignored runtime
  directory.

## Public KB Checklist

- [x] Public KB accepted artifacts have complete structured source metadata.
- [x] Public KB accepted artifacts have human review records or explicit
  maintainer review evidence.
- [x] Validation and gate success are recorded as checks, not as substitutes
  for human review.
- [x] No accepted public artifact depends on private or draft artifacts.
- [x] No private conjecture, unpublished idea, or unreviewed LLM output is
  committed under accepted public KB paths.
- [x] Source-note conventions and foundation backlog stay updated before
  adding new accepted theorem/proof-sketch batches.

## Public/Private Policy Status

- Public KB roots are readonly from downstream workspaces.
- Private KB roots are writable overlays.
- Private artifacts may depend on public accepted artifacts.
- Public artifacts must not depend on private artifacts.
- Accepted artifacts must not depend on draft or otherwise pre-accepted
  artifacts, even across KB roots.
- Readonly KB roots must reject lifecycle write commands.
- Provider-send previews must keep public/private root scopes visible.
- Private KB context must not be sent to a real provider without explicit
  private-research policy and operator consent.

## Formal Link Status

Implemented framework surfaces:

- Artifact metadata fields: `formalizations`, `alignment`, and
  `verification_policy`.
- Formal library manifest metadata and schema.
- G10 Formal Link Gate metadata and verifier-result consistency checks.
- Context-pack display of formal-link metadata.
- SQLite/index/query formal-link surfaces.
- Optional external Lean library reference checker for generated
  `import <module>` / `#check <symbol>` runs when Lean or lake is available.

Boundaries:

- Formal links are metadata unless a verifier actually runs and records a
  result.
- Planned formal links do not mean Lean has checked anything.
- A successful external Lean `#check` means the import and symbol resolved; it
  does not prove informal/formal semantic alignment.
- Alignment review remains human-reviewed metadata.
- Missing Lean/lake is `skipped`, not `pass`.
- Cosheaf does not fetch CSLib/mathlib or vendor Lean proof bodies.

## Known Limitations

- Conservative framework release, not production software.
- No web UI.
- No automatic theorem-proving agent.
- No full Lean autoformalization.
- No automatic informal/formal semantic alignment checking.
- No multi-user permission system.
- No default-on hosted provider calls.
- No default-on real hosted HTTP transport.
- External public KB integration is through local workspace roots, not a hosted
  registry service.
- SAT, SMT, plain Lean, and external Lean reference adapters are intentionally
  minimal optional invocation paths.
- MarkItDown, Headroom, CodeGraph, and Understand-Anything are optional or
  manual developer surfaces and are not source-of-truth dependencies.

## Non-Goals For This Release

- Do not add a web UI.
- Do not make hosted provider calls part of default workflows.
- Do not require real API keys, network access, or real provider calls in CI.
- Do not make MCP mandatory.
- Do not mass-import public KB artifacts.
- Do not change accepted-promotion semantics.
- Do not treat validation, gatekeeper, formal links, provider output, AI review,
  or skipped verifier results as human review or proof.
