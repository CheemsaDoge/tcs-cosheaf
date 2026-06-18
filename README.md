# TCS-Cosheaf

中文文档：[中文简介](README.zh-CN.md) | [中文文档导航](docs/README.zh-CN.md)

TCS-Cosheaf is a Git-backed typed research knowledge base and agent harness for
AI-assisted theoretical computer science. It keeps definitions, claims, proofs,
constructions, algorithms, reductions, counterexamples, experiments, reviews,
issues, and verifier evidence in reviewable repository files.

Current status: **v0.12.0 Research Memory Learning + Benchmark Suite v1
published release**. Package metadata records `0.12.0`. The public `v0.12.0`
tag, GitHub release, post-tag release smoke, and downstream
workspace-template/public KB pin updates are complete.

The `v0.12.0` release packages the V17 memory and benchmark line:
deterministic sidecar memory updates under `.cosheaf/memory/`, benchmark suite
v1, comparative reports, and static Markdown/JSON review reports. Memory
weights, benchmark runs, comparisons, and static reports remain review context
or sidecar guidance only and do not create proof, source metadata, human
review, verifier pass, gate pass, accepted status, accepted refutation, or
promotion authority.

The latest published release is `v0.12.0`:
<https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.12.0>.

The `v0.12.0` release does not add production autonomy, hosted-provider
defaults, model training, automatic correctness improvement, automatic theorem
proving, Lean semantic alignment, human review, accepted writes, verifier
passes without real checker evidence, gate-pass authority, source metadata
authority, accepted theorem/refutation authority, or promotion authority.

Earlier published baselines include `v0.1.1` Formal Link Layer support,
`v0.2.0` deterministic local-MVP workflow, `v0.2.1` CLI-first agent and
hosted-provider gateway surfaces, `v0.2.2` provider transport hardening,
`v0.2.3` verification evidence hardening, `v0.2.4` artifact failure memory,
`v0.3.0` Checked Evidence + Research Run Loop, `v0.4.0` Strategy Planner +
Research Task Graph, `v0.5.0` Operator MCP + Codex Application Layer,
`v0.6.0` Operator Session + Review Handoff, `v0.7.0` Bounded Research Loop +
Attempt Memory, `v0.8.0` Deterministic Execution Kernel + Librarian + FSM,
`v0.9.0` Reviewable Research Workflow MVP, and `v0.10.0` Cross-Check Evidence
+ Checker Registry, and `v0.11.0` External Operator Campaigns.
The repository has working
Python scaffolding, typed artifact models, filesystem loading, validation,
dependency graph indexing, workspace-aware KB root loading, artifact lifecycle
CLI
commands, gatekeeper reports including the G10 Formal Link Gate, ranked
context-pack generation with compact formal-link display, local task harness
and orchestrator dry-run surfaces, controlled draft-write CLI commands,
provider gateway and fake/mocked hosted-worker dispatch paths, verifier
adapters including a Python checker, a minimal optional SAT DIMACS path, a
minimal optional SMT-LIB path, a minimal optional plain Lean file path, and an
optional external Lean library reference `#check` path, an optional stdlib
OpenAI-compatible HTTP transport object plus a deliberately hard-to-trigger
provider `real-run` CLI path that is not used by default, GitHub Actions CI,
checked counterexample evidence CLI/eval surfaces, research-run provenance
CLI/eval surfaces, and collaboration templates. It is not production-ready
software and does not
yet provide a web UI, a default real hosted provider path, hosted worker CLI
commands, automatic theorem proving, full Lean autoformalization, automatic
accepted promotion, or multi-user permissions.

## Problem

Research projects in theoretical computer science accumulate claims, proof
attempts, constructions, counterexamples, experiments, and review notes across
papers, chats, scripts, and local files. That makes it hard to answer basic
questions:

- Which claims are accepted, draft, refuted, or obsolete?
- Which artifacts depend on which assumptions?
- Which evidence was checked, by what command, and from what repository state?
- What context should a human or agent read before working on an issue?

TCS-Cosheaf treats the repository as the durable project memory so research
state can be reviewed, validated, indexed, and handed to agents without relying
on conversation history.

## Approach

- Store typed research artifacts as Git-backed YAML files.
- Validate artifact shape, IDs, status/path invariants, dependencies, and local
  evidence paths.
- Build deterministic dependency graphs and repository indexes.
- Run gatekeeper checks before accepting behavior or artifact changes.
- Normalize verifier outputs through optional adapters.
- Generate ranked bounded context packs for issue-scoped Codex or agent tasks.
- Run explicit local worker commands against issue-scoped tasks and validate
  structured output bundles without merging accepted knowledge automatically.
- Record metadata-only references to external formal declarations through the
  Formal Link Layer without copying Lean proofs.

Optional formal tools stay optional. Missing SAT, SMT, Lean, or similar tools
must produce skipped verifier results rather than crashing the core system.
Cosheaf does not replace CSLib, mathlib, or Lean: formal links are metadata
plus gate, context-pack, index, query, and optional verifier surfaces. The
external Lean library reference checker can run `import <module>` and
`#check <symbol>` when Lean or lake is available, but a successful `#check`
only means the import and symbol resolved. It does not prove informal/formal
semantic alignment.

## Current Status

Implemented:

- Python 3.11+ package scaffold with Typer CLI.
- Pydantic v2 artifact models and status helpers.
- Initial JSON Schemas and example YAML records.
- Filesystem-backed artifact/issue/review loading and deterministic YAML
  writing.
- Optional `cosheaf.toml` workspace configuration with multiple KB roots,
  readonly roots, public/private dependency policy, and legacy fallback.
- `cosheaf validate`, `cosheaf artifact validate <path>`,
  `cosheaf artifact create`, `cosheaf artifact move-status`,
  `cosheaf artifact promote`, `cosheaf promotion readiness`, and
  `cosheaf workspace info`.
- Dependency graph inspection and deterministic SQLite/manifest index rebuilds.
- Read-only SQLite query API over rebuilt index output through
  `ArtifactIndexQuery`, including artifact, status, type, domain, dependency,
  reverse-dependency, formalization, and formal-policy queries.
- `cosheaf gate` and `cosheaf gate run` report generation.
- Ranked issue-scoped context pack generation with
  `cosheaf context build <issue-id>`.
- Formal Link Layer artifact metadata fields `formalizations`, `alignment`,
  and `verification_policy`.
- G10 Formal Link Gate metadata and verifier-result consistency checks.
- SQLite `formalizations` and `artifact_formal_policy` index tables plus
  compact manifest metadata.
- Context-pack display of formal-link metadata without claiming Lean
  verification or informal/formal alignment.
- Local task harness and local orchestrator dry-run surfaces with
  `cosheaf task ...`, `cosheaf orchestrator plan`, and
  `cosheaf orchestrator run --dry-run --local-only`.
- CLI-first agent-access surfaces with deterministic `--json` output for core
  read/check commands.
- Controlled draft, source-note, bundle, and review-request write commands
  that refuse accepted writes and readonly KB roots.
- Provider gateway commands for configuration inspection, context-send
  preview, and deterministic fake provider runs.
- Role-specific hosted worker services and explicit orchestrator dispatch
  through fake or OpenAI-compatible provider boundaries, with fake/mocked tests
  only.
- Optional stdlib OpenAI-compatible HTTP transport object for explicitly
  configured and injected provider calls; no default CLI path instantiates it.
- Explicit `cosheaf provider real-run --input-json <path> --provider
  openai-compatible --confirm-send --allow-network --json` path that requires
  inline context preview, operator send consent, explicit network permission,
  endpoint/API-key environment configuration, and redacted run logging.
- Verifier adapter protocol, Python checker adapter, minimal optional SAT
  DIMACS adapter, minimal optional SMT-LIB adapter, minimal optional Lean
  plain-file adapter, and optional external Lean library reference checker.
- Reproducibility metadata gate for executable evidence verifier results.
- Local PR checklist gate support through `cosheaf gate run --pr-checklist
  <path>`.
- First graph-theory pilot workflow with draft artifact evidence and a local
  Python checker.
- Second SAT/CNF pilot workflow with optional SAT evidence, a known satisfying
  assignment, and a Python fallback checker.
- Lean core formal-link pilot with draft metadata for `import Init` / `#check
  Nat`; missing Lean remains `skipped`, and the pilot does not claim alignment
  or accepted knowledge.
- GitHub Actions CI with separate `lint`, `typecheck`, `test`, `validate`, and
  `gate` checks.
- Published `v0.4.0` strategy-planner surfaces with
  `cosheaf strategy plan/show/graph/next/update-from-run/export-review`,
  deterministic runtime plans under `.cosheaf/strategy/`, non-authoritative
  review exports under `reviews/strategy/`, context/readiness surfacing, and
  public schemas for strategy plans and task graphs.
- Published `v0.5.0` operator surfaces with optional MCP
  `list-tools`/`serve --stdio`, read-only operator tools, controlled
  draft/review/runtime MCP write tools that call service-layer policy, operator
  runbook/demo docs, public KB operator policy smoke, and an optional
  documentation-only operator Skill package.
- Published `v0.6.0` operator-session and review handoff surfaces: bounded
  operator-session records, optional MCP session recording, leak scanning,
  runtime handoff bundles, review-context handoff export, downstream
  demo/policy smoke, and ecosystem matrix rows.
- Published `v0.7.0` research-loop surfaces: core loop/attempt runtime records,
  structured failure memory, deterministic next/step/run dry-run planning,
  external operator task/result packet commands, attempt-memory indexing,
  repeat-failure surfacing, retry-justification enforcement, loop scanning,
  research-loop eval/smoke rows, downstream workspace-template
  research-loop demo coverage, and public-KB research-loop policy guard.
- Published `v0.8.0` deterministic execution-kernel surfaces: librarian v0,
  orchestrator FSM v1, whitelisted local action registry, bounded local action
  execution, worker profiles, and deterministic memory feedback.
- Published `v0.9.0` initial reviewable-workflow surfaces:
  `cosheaf workflow start`, `cosheaf workflow step`, and
  `cosheaf workflow readiness`, with explicit authority notices. The current
  development line extends that surface with persisted workflow state,
  `cosheaf workflow show`, bounded `cosheaf workflow run` through the
  whitelisted local action registry, and `cosheaf workflow draft-proposal` for
  review-context JSON or writable private draft artifact output, plus
  `cosheaf workflow handoff build/show/scan/export` for review-context handoff
  packets with fail-closed scanner guards, and
  `cosheaf eval reviewable-workflow --json` for deterministic benchmark
  coverage.
- V15 checker and cross-check development surfaces: `cosheaf checker ...`
  commands record typed local checker sidecars, `cosheaf workflow cross-check`
  writes workflow evidence matrices under `.cosheaf/workflows/<workflow-id>/`,
  `cosheaf workflow evidence-report` wraps cross-check/gap counts,
  `cosheaf workflow export-crosscheck` exports review context under
  `reviews/workflow/`, and `cosheaf gap list/export` summarizes
  proof/source/formalization/review gaps. These outputs remain review context
  only.
- V16 campaign model-core development surfaces: `cosheaf.campaigns` defines
  campaign, attempt, budget, stop-condition, scorecard, operator-policy,
  risk-finding, and comparison DTOs; runtime records are stored under
  `.cosheaf/campaigns/<campaign-id>/`; and `cosheaf campaign
  start/show/append-attempt/scorecard/finalize` records and summarizes bounded
  attempts without accepted-write, human-review, verifier/gate, source-metadata,
  or promotion authority.
- V16 external operator protocol v2 development surfaces:
  `cosheaf campaign next <campaign-id> --json` previews the next bounded
  operator task; `cosheaf campaign export-task <campaign-id> --out <path>
  --json` writes an `operator_task_v2` JSON packet; and
  `cosheaf campaign import-result <campaign-id> --input-json <path> --json`
  validates `operator_result_v2`, rejects authority overclaims, unsafe paths,
  accepted KB writes, and public-mode private leaks, then records a runtime
  campaign attempt. These packets remain review context only.
- V16 campaign runner budget-controller development surfaces:
  `cosheaf campaign pause/resume` records human pause state, `cosheaf campaign
  scan` writes a deterministic runtime scan report under
  `.cosheaf/campaigns/<campaign-id>/scan.json`, and `cosheaf campaign run`
  applies stop policies for attempt budgets, draft-output budgets, repeated
  failures, pauses, and unsafe runtime output. `run` is a controller pass only:
  it does not execute shell commands, call providers, create human review, or
  write accepted knowledge.
- V16 campaign handoff/eval development surfaces:
  `cosheaf campaign handoff <campaign-id> --out <dir> --json` exports
  `campaign_handoff.json` review context with attempt summaries, scan
  findings, and metrics for attempts, unique directions, repeated failures,
  drafts, checked evidence refs, gaps, unsafe outputs, budget-stop accuracy,
  and operator-contract handling. `cosheaf eval campaign --json` runs
  deterministic temporary campaign fixtures and reports the same boundary
  metrics without writing accepted knowledge in the caller repository.
- V17 memory update development surfaces: `cosheaf.memory.updates` converts
  persisted workflow and campaign history into deterministic sidecar weights
  under `.cosheaf/memory/update-runs/` and `.cosheaf/memory/weights.json`.
  `cosheaf memory update-from-workflow`, `cosheaf memory
  update-from-campaign`, `cosheaf memory rebuild`, and `cosheaf memory explain`
  expose the v1 policy. Memory weights remain sidecar guidance only; they are
  not proof, source metadata, human review, verifier/gate pass, accepted
  status, or promotion authority.
- V17 benchmark suite development surfaces: `cosheaf.benchmark` aggregates the
  existing deterministic eval harnesses behind `cosheaf benchmark list`,
  `cosheaf benchmark run --suite <suite> --json`, and `cosheaf benchmark
  report <run-id> --out <path> --json`. Benchmark runs are persisted under
  `.cosheaf/benchmark-runs/` and remain regression evidence only, not accepted
  status or promotion authority.
- V17 comparison development surfaces: `cosheaf.compare` reads existing
  workflow, campaign, and benchmark records through `cosheaf compare
  workflows`, `cosheaf compare campaigns`, and `cosheaf compare benchmarks`.
  Comparison reports are metric-scoped review context only and highlight
  safety regressions without claiming a globally better result.
- V17 static report development surfaces: `cosheaf.reports` writes static
  Markdown/JSON report directories for existing workflow, campaign, and
  benchmark records through `cosheaf report workflow`, `cosheaf report
  campaign`, and `cosheaf report benchmark`. Static reports are review context
  only and are refused under accepted KB paths.

Planned or incomplete:

- Full SAT backend coverage beyond the minimal optional DIMACS invocation path.
- Full SMT backend coverage beyond the minimal optional SMT-LIB invocation path.
- Full Lean proof-assistant integration beyond optional plain-file and external
  library reference checks.
- V17 `v0.12.0` publication closeout.
- Hosted PR checklist source discovery beyond explicit local markdown files.
- Hosted worker CLI commands.
- External public KB repository integration beyond local workspace roots.
- Automatic informal/formal semantic alignment checking.

## Worker, Provider, And Orchestrator Boundary

TCS-Cosheaf includes a lightweight task-execution and provider-worker layer.
Tasks are issue-scoped records, context packs provide bounded repository
context, and local worker runs execute explicit command argv lists with
repository-local working directories, timeout metadata, stdout, stderr, and
return-code records. Workers and hosted-worker services can return structured
output bundles that the existing contract validates for review.

The orchestrator surface has two controlled paths. The local dry-run path is
deterministic and uses fake local workers. The hosted-worker path is explicit:
`cosheaf orchestrator run --issue <issue-id> --provider fake --json` uses the
deterministic fake provider, while the OpenAI-compatible boundary requires
explicit `--confirm-send` and configured or injected transport. Default tests
and CI use fake or mocked providers only. These paths do not write accepted
knowledge, do not mark human review, do not run real provider network calls in
CI, do not bypass reducers, validation, gates, verifier results, review, or
promotion. Accepted knowledge still enters through review, gates, and
`cosheaf artifact promote`.

## Core Concepts

- **Artifact**: A typed research record such as a definition, claim, proof,
  construction, algorithm, reduction, counterexample, experiment, review,
  verifier, or issue.
- **Status lattice**: Artifact status values such as `draft`, `accepted`,
  `refuted`, `obsolete`, and `superseded` describe lifecycle state.
- **Accepted knowledge**: `kb/accepted/` contains only accepted artifacts.
  Accepted artifacts must not depend on draft artifacts.
- **Draft knowledge**: `kb/draft/` contains draft or pre-accepted artifacts.
- **Gatekeeper**: Repository checks that turn schema, dependency, evidence,
  verifier, and review invariants into machine-readable and human-readable
  reports.
- **Workspace**: A `cosheaf.toml` configuration that layers one or more KB roots
  such as readonly public KB and writable private KB overlay.
- **Context pack**: A deterministic issue-scoped bundle of ranked repository
  context for Codex or other agents.
- **Verifier adapter**: A pluggable checker interface that records normalized
  `pass`, `fail`, `error`, or `skipped` results.

## Quickstart

This repository is the framework package. For a user-facing research
workspace, start from
[`tcs-cosheaf-workspace-template`](https://github.com/CheemsaDoge/tcs-cosheaf-workspace-template)
instead of manually merging framework and KB repositories. The intended model
is:

- `tcs-cosheaf`: framework, CLI, schema, gates, and agent harness.
- [`tcs-kb-public`](https://github.com/CheemsaDoge/tcs-kb-public): reusable
  public TCS KB, mounted readonly in downstream workspaces.
- `tcs-cosheaf-workspace-template`: user entry point with a readonly public KB
  root plus writable `kb/private` overlay.

Private artifacts may depend on public artifacts. Public artifacts must not
depend on private artifacts.

```bash
git clone https://github.com/CheemsaDoge/tcs-cosheaf.git
cd tcs-cosheaf
python -m pip install -e ".[dev]"
```

Inspect the CLI:

```bash
cosheaf --help
cosheaf version
cosheaf workspace info
```

Run repository validation and gatekeeper checks:

```bash
cosheaf validate
cosheaf gate
```

Create and move draft lifecycle artifacts:

```bash
cosheaf artifact create --id claim.example.new --type claim --title "New claim" --domain graph-theory --status draft --statement "Statement under review."
cosheaf artifact move-status claim.example.new locally_tested
```

Promote eligible reviewed artifacts into accepted knowledge:

```bash
cosheaf artifact promote claim.example.new
```

Direct accepted creation and direct `move-status ... accepted` remain refused.
Promotion requires repository validation, gatekeeper, target verifier,
dependency, and review checks.

Inspect promotion readiness without promoting:

```bash
cosheaf promotion readiness --artifact claim.example.new --json
```

Readiness reports are advisory. They do not write accepted artifacts, do not
create human review, and do not convert skipped verifier output into a pass.

Build an index and inspect the artifact dependency graph:

```bash
cosheaf index rebuild
cosheaf graph show
```

Generate task context for an issue:

```bash
cosheaf context build <issue-id>
cosheaf context show <issue-id>
```

See [Workspace quickstart](docs/WORKSPACE_QUICKSTART.md),
[Workspace model](docs/WORKSPACE.md), and
[Public/private KB policy](docs/PUBLIC_PRIVATE_KB.md) for layered KB roots.
Downstream repositories that only need Formal Link Layer metadata can stay
pinned to `v0.1.1`. Downstream repositories that need the deterministic
local-MVP workflow can pin to `v0.2.0`. Downstream repositories that need the
CLI-agent and hosted-provider gateway surfaces can pin to `v0.2.1`.
Downstream repositories that need the provider transport hardening,
context-send policy matrix, provider log scanner, and failure/counterexample
workflow evals can pin to `v0.2.2`. Downstream repositories that need
verification-evidence hardening can pin to `v0.2.3`. Downstream repositories
that need artifact failure memory and attempt traceability can pin to
`v0.2.4`. Downstream repositories that need checked counterexample evidence
and research-run provenance can pin to `v0.3.0`. Downstream repositories that
need Strategy Planner + Research Task Graph surfaces can pin to `v0.4.0`;
downstream repositories that need Operator MCP + Codex Application Layer
surfaces can pin to `v0.5.0`. Downstream repositories that need Operator
Session + Review Handoff surfaces can pin to `v0.6.0`. Downstream
repositories that need Bounded Research Loop + Attempt Memory surfaces can pin
to `v0.7.0`; deterministic execution-kernel surfaces can pin to `v0.8.0`; and
the initial reviewable-workflow release line can pin to `v0.9.0`. Downstream
repositories that need the V15 checker registry and cross-check evidence
surfaces can pin to `v0.10.0`. Downstream repositories that need the V16
bounded campaign surfaces can pin to `v0.11.0`. Downstream repositories that
need the V17 memory/benchmark release can pin to `v0.12.0`.

## Development Commands

```bash
make lint
make typecheck
make test
make validate
make gate
```

`make validate` runs the current repository validation CLI. `make gate` runs the
gatekeeper and writes reports under `.cosheaf/reports/`. G8 is skipped when no
PR checklist source is provided; use `cosheaf gate run --pr-checklist <path>` to
validate a local PR body markdown file.

## Roadmap

The roadmap is tracked in [docs/ROADMAP.md](docs/ROADMAP.md). Live issue state
is tracked in GitHub issues rather than hard-coded in this README.

## Non-Goals

For the MVP, TCS-Cosheaf does not aim to provide:

- A web UI.
- Model training.
- An automatic theorem-proving agent.
- Full Lean autoformalization.
- A multi-user permission system.
- A replacement for peer review, formal proof assistants, or domain expert
  judgment.
- A replacement for CSLib, mathlib, Lean, or human semantic alignment review.

## Key Documentation

- [Project rules](AGENTS.md)
- [Product spec](docs/PRODUCT_SPEC.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Workspace quickstart](docs/WORKSPACE_QUICKSTART.md)
- [Workspace model](docs/WORKSPACE.md)
- [Public/private KB policy](docs/PUBLIC_PRIVATE_KB.md)
- [Gatekeeper and validation gates](docs/GATES.md)
- [Agent access](docs/AGENT_ACCESS.md)
- [Codex operator runbook](docs/CODEX_OPERATOR_RUNBOOK.md)
- [Research loops](docs/RESEARCH_LOOPS.md)
- [Reviewable workflows](docs/WORKFLOWS.md)
- [Memory updates](docs/MEMORY_UPDATES.md)
- [Benchmarks](docs/BENCHMARKS.md)
- [Comparisons](docs/COMPARISONS.md)
- [Static reports](docs/STATIC_REPORTS.md)
- [Checker registry](docs/CHECKERS.md)
- [Draft proposals](docs/DRAFT_PROPOSALS.md)
- [Review handoffs](docs/REVIEW_HANDOFFS.md)
- [External operator run loop](docs/EXTERNAL_OPERATOR_RUN_LOOP.md)
- [Operator workspace demo](docs/OPERATOR_WORKSPACE_DEMO.md)
- [Operator Skill package](docs/OPERATOR_SKILL.md)
- [Strategy planner](docs/STRATEGY_PLANNER.md)
- [Agent providers](docs/AGENT_PROVIDERS.md)
- [Operator MCP](docs/OPERATOR_MCP.md)
- [MCP server](docs/MCP_SERVER.md)
- [Evaluation](docs/EVALUATION.md)
- [Artifact lifecycle](docs/ARTIFACT_LIFECYCLE.md)
- [Artifact schema](docs/ARTIFACT_SCHEMA.md)
- [Codex workflow](docs/CODEX_WORKFLOW.md)
- [Review policy](docs/REVIEW_POLICY.md)
- [Release checklist](RELEASE_CHECKLIST.md)
- [Current milestone](context/CURRENT_MILESTONE.md)
- [Project state](context/PROJECT_STATE.md)
- [Public interface registry](context/INTERFACE_REGISTRY.md)

## License

This project is licensed under the [Apache License 2.0](LICENSE).
