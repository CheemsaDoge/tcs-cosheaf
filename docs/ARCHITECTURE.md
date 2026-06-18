# Architecture

## Overview

TCS-Cosheaf is organized as a layered system. Each layer should expose narrow interfaces upward and avoid depending on higher layers.

## Layers

### Knowledge Layer

Defines the artifact model, artifact status concepts, artifact type vocabulary,
formalization-link metadata, and domain-level invariants.

### Configuration Layer

Loads optional repository-local workspace configuration from `cosheaf.toml`.
When the file is absent, configuration falls back to the legacy single-root
repository behavior with one writable KB root at `kb/`.

The workspace configuration model contains a workspace name, public/private
policy fields, and one or more KB roots. Each KB root has a `name`,
repository-relative `path`, `readonly` flag, and integer `priority`.

### Source Ingestion Layer

Defines the boundary for local source conversion before source material enters
artifact or source-note review workflows. The policy is documented in [Source
Ingestion](SOURCE_INGESTION.md).

This layer is staging only. The optional MarkItDown adapter can convert
repository-local source files to Markdown with provenance metadata through
`cosheaf ingest convert`, but converted output is not validation, gatekeeper
evidence, verifier evidence, human review, accepted artifact truth, or
promotion evidence. Converted Markdown may feed source notes, explorer tasks,
or draft proposals only.

URL, OCR, plugins, LLM vision, and cloud-document capabilities are disabled by
default. The MVP adapter is not a sandbox for hostile documents; untrusted
source files require a future bounded subprocess or documented sandbox
boundary. Missing MarkItDown does not affect core validation, gates, index
rebuilds, context packs, promotion, tests, or default installation.

### Storage/Index Layer

Loads artifacts from Git-backed paths, builds deterministic indexes, and records repository-local metadata needed by other layers.

When `cosheaf.toml` exists, storage discovers YAML records under each configured
KB root plus repository-local `issues/` and `examples/`. Loaded records retain
their source KB root name, root path, readonly flag, and path relative to the KB
root. When `cosheaf.toml` is absent, storage keeps the previous discovery roots:
`kb/`, `issues/`, and `examples/`.

Current index outputs are:

- `.cosheaf/index.sqlite`
- `.cosheaf/artifact_manifest.json`

Index rebuilds load repository YAML records, normalize artifact rows, write
SQLite from scratch, and emit a deterministic JSON manifest ordered by artifact
ID and dependency tuple. Artifact rows include the source KB root name. Formal
link metadata is indexed into `formalizations` and `artifact_formal_policy`
tables and into compact manifest fields.

The SQLite query API is a read-only convenience layer over
`.cosheaf/index.sqlite`. YAML remains the source of truth; callers should
rebuild the index after YAML changes before querying. Query results are ordered
deterministically and expose artifact metadata, domain membership, dependency
edges, reverse dependency edges, formalization references, formal policy rows,
and the indexed source KB root. Query methods do not rebuild indexes
implicitly.

### Issue Layer

Repository-local issues are first-class YAML records under `issues/open/`,
`issues/blocked/`, and `issues/closed/`. They are modeled by
`cosheaf.storage.loader.IssueRecord` and managed through `cosheaf issue ...`.
The issue layer is independent of GitHub: local issue creation and closure are
filesystem writes only, do not require a token or network call, and do not
change artifact lifecycle state.

Local issues provide task-scoped retrieval and context inputs. Context-pack
commands resolve local issue records by ID and use `related_artifacts` to seed
bounded context, but an issue status is workflow memory only. Closing an issue
does not accept, refute, review, verify, gate, or promote any artifact.

### Forge Layer

The forge layer is the typed boundary for local git and GitHub workflow
planning. It is implemented under `cosheaf.forge` and initially exposes
dry-run previews only: forge status, GitHub issue preview from a local issue
YAML file, and GitHub PR preview from base/head branch names.

Forge previews do not run `git`, `gh`, or any subprocess. They do not call the
network, create GitHub issues, create GitHub PRs, commit, push, read or store
tokens, or write repository files. Preview DTOs explicitly report dry-run
status and no-write/no-network flags, and each result carries an authority
warning.

Forge output is workflow planning context only. It does not grant proof, source
metadata, human review, verifier pass, gate pass, accepted status, accepted
theorem/refutation status, or promotion authority.

### Formal Link Layer

Records references from artifacts to external formal declarations, currently
Lean 4 declarations in libraries such as CSLib or mathlib. This layer stores
library, import-path, symbol, declaration-kind, status, check-mode, expected
type, and notes metadata under `formalizations`.

Formal links are references, not copied proof bodies. Cosheaf does not replace
CSLib, mathlib, or other formal libraries, and artifact YAML should not vendor
Lean proofs. Semantic alignment between an informal artifact statement and a
formal declaration is recorded separately under `alignment`; a Lean pass does
not automatically prove informal/formal alignment.

`verification_policy` records whether a formal link, Lean check, or alignment
review is expected for an artifact. G10 Formal Link Gate enforces consistency
between `verification_policy`, `formalizations`, `alignment`, local formal
library manifests, and normalized Lean verifier results when policy requires a
Lean check. This gate does not execute Lean, fetch external libraries, prove
informal/formal alignment, or change accepted-promotion semantics. The optional
external Lean library reference checker lives in the Verification Layer and can
turn linked formalization metadata into `import`/`#check` verifier results when
Lean or lake is available. Formal-link context-pack display and SQLite/query
support are metadata-only surfaces built on the same artifact fields; they do
not execute Lean or claim proof status.

### Graph Layer

Builds a directed artifact dependency graph from `depends_on`. Edge direction is
artifact-to-dependency, for example `claim -> dependency`. The graph layer
detects missing dependencies, directed cycles, and accepted artifacts that depend
on draft or otherwise pre-accepted artifacts.

### Memory/Retrieval Layer

The memory/retrieval layer provides deterministic librarian behavior between
storage/index/graph data and context-pack or future orchestrator consumers. It
is documented in [Memory Policy](MEMORY_POLICY.md).

The default retrieval unit is an artifact card, not a full artifact dump. Cards
carry compact metadata such as ID, path, root scope, type, status, title,
summary, domain, dependency IDs, source/review/verifier/formalization states,
trust score, retrieval score, relevance explanation, risk flags, and whether a
caller may pull the full artifact.

Retrieval requests are expected to be issue-scoped and bounded. They should
declare allowed scopes, allowed statuses, seed artifacts, role, maximum card
count, and maximum full-artifact pulls. Public-only retrieval must exclude
private records and private-derived summaries. Orchestrator context defaults to
cards only.

The local implementation builds artifact cards, searches them with
deterministic lexical or SQLite FTS/BM25 matching, blends issue-conditioned
Personalized PageRank, global PageRank, quality, freshness, and penalty
signals, and records retrieval audit metadata. The memory graph extends the
dependency graph with review, source, formalization, verifier, task-run,
worker-bundle, and issue-context signals. Graph weights and retrieval caches
are sidecars under `.cosheaf/memory/`. Sidecars are rebuildable views and must
not become artifact truth.

The librarian may build cards, rank/filter them, compute graph weights, produce
context-pack candidates, and record retrieval audits. It must not create
claims, edit artifacts, mark review as human-reviewed, run promotion, or treat
retrieval scores as proof. Accepted knowledge still enters only through
validation, gates, human review, and explicit promotion.

### Verification Layer

Runs verifier adapters and normalizes verifier outcomes. Optional external
tools must remain optional; missing tools should produce skipped verifier
results instead of crashing the core system. The Python checker adapter runs
repository-local checker scripts. The SAT adapter supports a minimal optional
DIMACS CNF invocation path when a supported backend is available, while keeping
SAT solver binaries optional and recording skipped results when no backend is
available. The SMT adapter similarly supports a minimal optional SMT-LIB
invocation path through a supported backend, currently external `z3` when
available, while keeping solver binaries optional and recording skipped results
when no backend is available. The Lean adapter supports a minimal optional plain
Lean file invocation path through a supported backend, currently external
`lean` when available, while keeping Lean optional and recording skipped results
when no backend is available. The external Lean library reference adapter
supports a minimal optional generated-file path for linked Lean formalization
metadata: it writes a temporary file containing `import <import_path>` and
`#check <symbol>`, then runs `lean` or configured `lake env lean` when
available. It records skipped when Lean/lake is unavailable and does not fetch
CSLib/mathlib or manage external library checkouts. No verifier adapter
performs natural-language autoformalization, and no Lean verifier result proves
informal/formal semantic alignment.

### Gate/Review Layer

Combines schema checks, repository invariants, dependency checks, verifier
outcomes, reproducibility metadata, source metadata, and PR checklist checks
into gate results.

Alignment review remains separate from verifier execution. Missing optional
Lean tooling remains a skipped verifier result, not a pass. The gate layer
records formal-link fields through schema/model validation and G10 metadata and
verifier-result consistency validation. G10 may block ordinary gatekeeper runs
when policy metadata is inconsistent or a required Lean check has no matching
verifier `pass`, which means accepted promotion is blocked through the existing
gatekeeper blocking-issue mechanism. It does not add a new promotion policy
path.

Workspace-aware dependency checks additionally reject public artifacts that
depend on private artifacts. Status/path checks evaluate artifact lifecycle
paths relative to each configured KB root, so `kb/public/accepted/...` and
`kb/private/accepted/...` both use accepted-path semantics inside their own
roots.

### Agent Harness Layer

Builds bounded context packs for Codex and other agents, records task assumptions, and keeps task execution anchored to repository files rather than conversation state.

Current agent harness outputs are:

- `context/TASKS/<issue-id>/` context packs.
- `.cosheaf/tasks/<task-id>.yaml` runtime task records.
- `.cosheaf/tasks/<task-id>/runs/<run-id>/` local worker run records with
  separate stdout and stderr files.

Context packs use deterministic card retrieval and issue-local relevance
ranking. The generated files are `CONTEXT.md`, `ACCEPTANCE.md`,
`RELEVANT_ARTIFACTS.md`, `KNOWN_FAILURES.md`, `FULL_ARTIFACTS.md`,
`RETRIEVAL_AUDIT.json`, and `COMMANDS.md`. The rendered artifact sections use
compact `ArtifactCard` rows by default, including score metadata, root scope,
and relevance reasons. Full artifact YAML is written only to
`FULL_ARTIFACTS.md` when the caller sets an explicit nonzero
`--max-full-artifacts` budget. The default orchestrator role uses
`max_full_artifacts = 0`, so default handoff context is cards-only.

Context-pack relevance still preserves the existing issue-local constraints:
direct issue artifact references, one-hop dependency neighbors, artifact
domains that match issue text or tags, and artifact tags that match issue tags.
Accepted artifacts are preferred over draft artifacts within the same
relevance class. Refuted, obsolete, and superseded artifacts are included only
when relevant and are marked as known failures, not current truth. Public-only
context packs exclude private cards and private artifact IDs from the rendered
context and retrieval audit.

When a relevant artifact carries formal-link metadata or policy-relevant formal
settings, context packs include compact formalization, alignment, verification
policy, and G10-relevant hint lines. These lines are handoff metadata only:
they do not load gate reports, do not claim a current G10 verdict, and do not
claim Lean verification.

The task harness defines protocol-level worker types only. Creating, listing,
or completing tasks does not call LLMs or external services. The orchestrator
stub validates that tasks are issue-scoped, records deterministic default task
IDs, and can mark a task completed only after a local worker output bundle
passes the worker contract.

The orchestrator state-machine contract is defined separately from runtime
execution. `cosheaf.agent.orchestrator_state` contains strict serializable
models for `OrchestratorRun`, `Plan`, `TaskDAG`, `TaskNode`, `WorkerCall`,
`ReducerResult`, and `StopCondition`. These models validate explicit run
states, state transitions, task-DAG dependencies, and repository-local paths,
but they do not execute workers, call hosted LLMs, run gates, request human
review, merge outputs, or promote accepted knowledge.

The deterministic planner stub in `cosheaf.agent.orchestrator_planner` converts
an existing issue into a small `Plan` / `TaskDAG` through
`cosheaf orchestrator plan --issue <issue-id> --json`. The plan contains fixed
librarian-retrieval, reasoner-draft, verifier-check, and review-request nodes.
It references the expected context-pack location, but it does not build context
packs, write plan files, dispatch workers, run verifier adapters, call model
providers, request human review, or create accepted knowledge.

The local orchestrator runner in `cosheaf.agent.orchestrator_runner` wires that
plan to the existing local worker runner through
`cosheaf orchestrator run --issue <issue-id> --dry-run --local-only`. It creates
issue-scoped local task records for the planned nodes, runs deterministic
repository-local worker commands with `shell=False`, validates worker bundle v2
manifests, reduces them into `ReducerResult` records, and writes an inspectable
run record under `.cosheaf/orchestrator/<issue-id>/runs/<run-id>/run.yaml`.
It also writes a sanitized structured `run_log.json` for local observability;
see [Observability](OBSERVABILITY.md). This is still a dry-run workflow: it
does not call hosted LLMs, make network
calls, run gates, request human review, merge outputs, write accepted
knowledge, or promote artifacts.

The hosted-worker orchestrator runner in the same module wires the deterministic
plan to `HostedWorkerService` only when the operator explicitly supplies a
provider through `cosheaf orchestrator run --issue <issue-id> --provider
<provider>`. The deterministic `fake` provider path performs an end-to-end
hosted-worker dispatch without hosted network access. The OpenAI-compatible
path requires explicit `--confirm-send` plus a configured or injected transport;
the default CLI path reports missing transport instead of making a real hosted
call. Hosted-worker run records stay under
`.cosheaf/orchestrator/<issue-id>/runs/<run-id>/`, copy provider audit records
into a run-local `providers/` directory, write WorkerBundle v2 manifests under
run-local `bundles/`, write typed sub-results under `typed-results/`, and run
the reducer only on validated WorkerBundle outputs. This path does not write
accepted knowledge, mark human review, promote artifacts, run gates, or treat
provider output as verifier success.

The default local dry-run worker command is implemented by
`cosheaf.agent.dry_run_workers`. It generates role-aware worker bundle v2
manifests for the planner's reasoner, verifier, and orchestrator nodes. The
reasoner output is candidate review context only, the verifier output records
that no real gate, Lean, SAT, SMT, or promotion result was produced, and all
proposal paths remain under `.cosheaf/orchestrator/.../proposals/`. The worker
does not write proposed artifacts; it only writes the bundle manifest that the
runner validates and reduces.

The provider-neutral model interface in `cosheaf.agent.model_provider` defines
request, response, capability-negotiation, and provider protocol DTOs for worker
integrations. The deterministic `FakeModelProvider` is used for tests and
offline hosted-worker paths. The OpenAI-compatible provider boundary is
transport-injected and does not import hosted-provider SDKs or perform network
calls by itself. Capability negotiation records unsupported requested
parameters instead of crashing.

The local worker runner is not an LLM runtime or model-provider integration. It
executes only an explicit argv command with `shell=False`, defaults to the
repository root as its working directory, rejects working directories outside
the repository, rejects bundle paths outside the repository before command
execution, enforces a timeout, captures stdout and stderr, and writes a
deterministic run record under the task's `.cosheaf` run directory. Optional
bundle handling validates worker output bundles after command execution; it
does not merge outputs or promote accepted knowledge.

Worker output bundles are local YAML manifests. Artifact and review outputs
must reference repository-local YAML records that pass the existing schema gate.
Bundle manifests may also be passed as repository-local directories containing
`bundle.yaml`. Bundles must not target `kb/accepted/`, and task completion does
not merge anything into accepted knowledge.

Worker bundle v2 is a stricter Phase 4.3 contract for future reducer-driven
orchestration. `cosheaf.agent.worker_bundle_v2` records bundle ID, task ID,
worker role, creation time, summary, used artifacts and sources, claims,
proposed artifacts, verification requests, failures or counterexamples, risk
flags, next steps, and confidence. Its reducer validates repository-local
paths, rejects accepted-KB proposals, rejects worker-created
`human_reviewed` or `accepted` review states, preserves failures and
uncertainty as reducer warnings, and returns a deterministic `ReducerResult`.
The local orchestrator runner can now validate and reduce these bundles after
local dry-run worker commands, but it does not run gates, request review, merge
outputs, write accepted artifacts, or promote accepted knowledge.

### Service Layer

Provides typed Python service entry points shared by the CLI and other
agent-access surfaces such as optional MCP adapters and future hosted provider
workers. The current service layer is intentionally thin: it wraps existing
workspace, validation, gate, memory search, context-pack, task,
bundle-validation, and draft-write logic while returning typed results instead
of terminal-only output.

The service layer does not grant MCP authority, expose arbitrary shell access,
mark automatic review, or create accepted-promotion authority. Provider calls
are only available through explicit provider gateway services with fake or
injected transports and policy/consent metadata. Controlled write services are
limited to draft/pre-accepted artifact creation, task or run records, worker
bundles, and review context surfaces. Accepted promotion remains the existing
explicit lifecycle path and is not exposed as an agent-authority service.

Expected service-layer failures use stable machine-readable error codes and
can be converted to the public `ErrorResult` DTO. CLI commands may continue to
render the human-readable error text, while provider, MCP, or agent-facing
callers can use the structured code/remediation/blocking fields.

### Application Layer

Provides `cosheaf.app` as the stable Python use-case boundary above existing
services. The initial facade is intentionally thin: `CosheafApp` and
`open_app` delegate to the existing service and read-only domain functions for
workspace info, repository and artifact validation, gate runs, context
build/show, memory cards/search, controlled draft writes, controlled
source-note and review-request writes, WorkerBundle validation/submit/reduce,
and read-only promotion-readiness reports.

The app layer is not a new authority source. It does not change CLI command
names, artifact schemas, accepted-promotion semantics, human-review policy,
verifier semantics, or gate behavior. Future server, website, MCP, and forge
surfaces should call `cosheaf.app` instead of importing Typer command
functions or shelling out to the CLI.

`cosheaf.app.models` exposes stable request/result DTOs for app use cases. The
initial DTO family covers workspace info, validation, gate runs, context builds,
draft artifact/source-note writes, review-request writes, forge dry-run
previews, and shared `ErrorResult` serialization. The DTOs reuse the existing
agent-access model base and keep accepted-write and human-review authority
unavailable through app requests.

### CLI Layer

Provides public commands for validation, gate execution, graph inspection,
context generation, workspace inspection, lifecycle artifact writes, and
verifier invocation.

The validate/gate command group lives in `cosheaf.validation_cli` and calls the
`cosheaf.app` facade for repository validation and gatekeeper runs.
The context command group lives in `cosheaf.context_cli` and calls the same app
facade for context build/show operations.

CLI commands now call typed service functions for workspace inspection,
repository and artifact validation, gate execution, context-pack generation,
memory card/search operations, task operations, forge dry-run previews, and
draft artifact creation.
The CLI remains the human and CI oracle: it parses command-line options,
renders service results, preserves existing exit-code behavior, and keeps
existing promotion and verifier boundaries intact.

Lifecycle write commands are workspace-aware. In configured workspaces,
`cosheaf artifact create` writes to the writable private KB root by default, and
`cosheaf artifact move-status` refuses to modify records loaded from readonly
KB roots.

## Module Dependency Direction

The intended module dependency direction is:

```text
core -> config -> storage -> graph -> gates -> verification -> agent -> services -> forge -> app -> cli
```

Lower-level modules must not import higher-level modules. Public interface changes must be recorded in `context/INTERFACE_REGISTRY.md`.

## Determinism

Indexes, generated outputs, context packs, and gate reports must be deterministic for the same repository state and tool availability.

## Architectural Decisions

Architectural decisions must be recorded under `docs/ADR/` using ADR format.
