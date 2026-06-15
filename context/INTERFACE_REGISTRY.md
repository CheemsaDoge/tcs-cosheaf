# Interface Registry

## Current Public Python Interfaces

### Planned Interfaces Not Yet Implemented

- Artifact failure-memory surfacing is implemented for read-only inspection,
  controlled append-only draft writes, WorkerBundle-to-failure-log planning
  and controlled append, artifact cards, memory search, compact context card
  summaries, explicit context-pack `Known Failed Directions` sections, and
  read-only promotion-readiness warning reasons, with deterministic
  retrieval/governance eval coverage. Future failure-memory work must keep
  failure memory labeled as non-authoritative and must not promote it into
  proof, review, verifier, checked-counterexample, accepted-status, or
  promotion authority.
- Hosted worker CLI commands and hosted-provider MCP tools are not implemented
  yet. Role-specific hosted worker service bridging for fake and mocked
  provider calls is implemented under `cosheaf.agent.hosted_workers`, the
  optional stdlib `OpenAICompatibleHttpTransport` exists for explicitly
  injected/configured OpenAI-compatible calls, `cosheaf provider real-run`
  exposes a deliberately hard-to-trigger real-provider CLI path, and the
  internal orchestrator can explicitly dispatch planned nodes to that bridge
  through fake or OpenAI-compatible provider boundaries.
- `docs/ADR/0019-hosted-provider-gateway.md`: ADR for the planned hosted
  provider gateway. It records provider modes, fake-provider test
  requirements, private-context preview and consent, output discipline,
  logging/redaction metadata, and no-accepted-write boundaries. The runtime
  now implements the gateway core with fake, injected mocked
  OpenAI-compatible, optional stdlib HTTP transport, and explicit real-run CLI
  paths; the ADR still governs future hosted worker work.
- `docs/AGENT_PROVIDERS.md`: operator-facing provider policy document. It
  describes the implemented provider gateway core, provider CLI commands,
  orchestrator hosted-worker dispatch, planned configuration, context policy,
  output rules, logging, OpenAI-compatible transport boundary, and
  fake-provider requirements.
- MCP controlled-write tools are not implemented yet.
- `docs/ADR/0017-mcp-agent-interface.md`: ADR for the optional MCP adapter. It
  records stdio transport, resource/tool/prompt boundaries, controlled-write
  requirements, forbidden tools, and private KB policy constraints. The current
  runtime implements only the read-only stdio subset, and MCP is not required
  for CLI-first agent workflows.

### CLI Entry Point

- Entry point: `cosheaf`
- Implementation: `cosheaf.cli:app`
- Framework: Typer

### CLI Commands

- `cosheaf --help`: shows CLI help.
- `cosheaf version`: prints the package version.
- `cosheaf version --json`: emits deterministic JSON with `schema_version`,
  package name, and version.
- `cosheaf workspace info`: shows the active workspace name, configured/legacy
  mode, repository root, and KB roots.
- `cosheaf workspace info --repo-root <path>`: shows workspace configuration for
  an explicit repository root.
- `cosheaf workspace info --json`: emits a deterministic
  `WorkspaceInfoResult` JSON payload with KB root scope, readonly, priority,
  and policy fields.
- `cosheaf validate`: validates repository YAML records discovered under the
  active workspace KB roots plus `issues/` and `examples/`. Without
  `cosheaf.toml`, the KB root remains `kb/`.
- `cosheaf validate --repo-root <path>`: validates a repository rooted at `<path>`.
- `cosheaf validate --debug`: shows tracebacks for unexpected validation errors.
- `cosheaf validate --json`: emits a deterministic `ValidateResult` JSON
  payload. Expected validation failures are represented as structured
  `ErrorResult` entries and exit nonzero without Rich markup.
- `cosheaf artifact validate <path>`: validates one YAML file with file-local checks.
- `cosheaf artifact validate <path> --repo-root <path>`: resolves the artifact path against an explicit repository root.
- `cosheaf artifact validate <path> --debug`: shows tracebacks for unexpected validation errors.
- `cosheaf artifact create --id <artifact-id> --type <artifact-type> --title <title> --domain <domain> --status <status> --statement <statement>`: creates a deterministic artifact YAML record under the lifecycle tree and validates it before reporting success. In configured workspaces, it writes to the writable private KB root by default.
- `cosheaf artifact create ... --repo-root <path>`: creates the artifact for an explicit repository root.
- `cosheaf artifact create ... --author <author>`: records one author value; repeat for multiple authors.
- `cosheaf artifact create ... --tag <tag>`: records one tag value; repeat for multiple tags.
- `cosheaf artifact create ... --depends-on <artifact-id>`: records one dependency; repeat for multiple dependencies.
- `cosheaf artifact create ... --supersedes <artifact-id>`: records one superseded artifact ID; repeat for multiple IDs.
- `cosheaf artifact create ... --created-at <timestamp>`: sets `created_at` and `updated_at`; defaults to current UTC if omitted.
- `cosheaf artifact move-status <artifact-id> <new-status>`: moves a unique artifact ID through a non-accepted lifecycle status transition after status/path and repository validation. In configured workspaces, it refuses artifacts loaded from readonly KB roots.
- `cosheaf artifact move-status <artifact-id> <new-status> --repo-root <path>`: moves the artifact status for an explicit repository root.
- `cosheaf artifact promote <artifact-id>`: promotes an eligible lifecycle artifact into `kb/accepted/<type-dir>/<artifact-id>.yaml` after repository validation, gatekeeper, target verifier, dependency, review, readonly-root, and accepted-public source metadata checks.
- `cosheaf artifact promote <artifact-id> --repo-root <path>`: promotes the artifact for an explicit repository root.
- `cosheaf artifact failures <artifact-id>`: prints a read-only summary of
  the target artifact's `failure_log` entries with an explicit
  non-authority notice. It does not write files, create verifier results, mark
  human review, run gates, or promote artifacts.
- `cosheaf artifact failures <artifact-id> --json`: emits deterministic JSON
  with `schema_version`, `kind=artifact_failure_log`, artifact ID/path, KB root
  name/scope/readonly metadata, `failure_count`, `failure_log` entries, and an
  authority notice.
- `cosheaf artifact failures <artifact-id> --repo-root <path>`: inspects an
  explicit repository root.
- `cosheaf artifact failure add --artifact <artifact-id> --input-json <path>`:
  appends one validated `FailureLogEntry` to a writable draft/pre-accepted
  artifact and refreshes `updated_at`. It refuses direct `kb/accepted/`
  mutation, accepted artifact status, readonly KB roots, and input fields that
  claim human review, accepted status, verifier pass, or checked counterexample
  authority.
- `cosheaf artifact failure add --artifact <artifact-id> --input-json <path> --json`:
  emits deterministic controlled-write JSON with `schema_version`,
  `kind=artifact_failure_log_entry`, target `path`, `written_paths`, `dry_run`,
  `accepted_write_performed=false`, and `record_id` set to the failure ID.
  Expected failures emit `ErrorResult`.
- `cosheaf artifact failure add --artifact <artifact-id> --input-json <path> --dry-run`:
  validates the failure-log entry and reports the target artifact path without
  changing the artifact file or `updated_at`.
- `cosheaf artifact failure add ... --repo-root <path>`: performs the
  controlled append for an explicit repository root.
- `cosheaf artifact failure plan-from-bundle --bundle <path> --target-artifact <artifact-id> --json`:
  validates a WorkerBundle v2 and returns proposed `FailureLogEntry` values
  derived from `failed_attempts` without writing files. Typed
  `counterexample_candidates` are linked by candidate ID only.
- `cosheaf artifact failure plan-from-bundle ... --repo-root <path>`: plans the
  WorkerBundle-derived entries for an explicit repository root.
- `cosheaf artifact failure add-from-bundle --bundle <path> --target-artifact <artifact-id> --json`:
  appends WorkerBundle-derived failure-log entries to a writable non-accepted
  artifact through the same controlled failure-log write boundary. It refuses
  accepted paths/status, readonly KB roots, and unsafe WorkerBundle authority
  claims.
- `cosheaf artifact failure add-from-bundle ... --dry-run`: validates the
  bundle conversion and target artifact without writing files or refreshing
  `updated_at`.
- `cosheaf counterexample evidence validate --input-json <path> --json`:
  validates one checked counterexample evidence JSON record without writing
  files. Expected failures emit `ErrorResult` with checked-evidence error
  codes.
- `cosheaf counterexample evidence stage --input-json <path> --json`: stages a
  checked counterexample evidence record under
  `reviews/evidence/checked-counterexamples/<evidence-id>.yaml`. It refuses
  accepted KB paths, path traversal, absolute paths, duplicate staged records,
  and authority-spoofing fields such as `human_reviewed`, `review_state`,
  `accepted`, `artifact_status`, and `promote`.
- `cosheaf counterexample evidence stage --input-json <path> --dry-run --json`:
  validates and reports the target checked-evidence path without writing files.
- `cosheaf counterexample evidence show --evidence <path-or-id> --json`: reads
  staged checked counterexample evidence by repository-local path or evidence
  ID and returns deterministic JSON with an authority notice.
- `cosheaf promotion readiness --artifact <artifact-id> --json`: emits a
  read-only promotion-readiness report for a single artifact. The command
  runs validation and gatekeeper reporting, distinguishes missing review,
  failed verifier, skipped verifier, missing source metadata, dependency risk,
  private dependency, draft status, readonly-root conditions, and repository
  gatekeeper blockers. It also reports unresolved artifact failure memory as
  `unresolved_failure_memory` warning reasons and checked counterexample
  evidence as `checked_counterexample_evidence` warning reasons distinct from
  verifier failures. It does not write accepted knowledge.
- `cosheaf promotion readiness --issue <issue-id> --json`: emits the same
  read-only report for the issue record's direct `related_artifacts`.
- `cosheaf promotion readiness ... --repo-root <path>`: evaluates readiness
  for an explicit repository root.
- `cosheaf index rebuild`: rebuilds `.cosheaf/index.sqlite` and `.cosheaf/artifact_manifest.json`.
- `cosheaf index rebuild --repo-root <path>`: rebuilds index outputs for an explicit repository root.
- `cosheaf ingest convert <path>`: converts a repository-local source file into staged Markdown plus provenance metadata under `.cosheaf/ingest/` when optional MarkItDown support is installed.
- `cosheaf ingest convert <path> --out <dir>`: writes staged Markdown and provenance metadata under an explicit repository-local output directory. Accepted KB paths such as `kb/accepted/` or `kb/public/accepted/` are rejected.
- `cosheaf ingest convert <path> --metadata-json`: emits deterministic conversion provenance JSON to stdout.
- `cosheaf ingest convert <path> --repo-root <path>`: resolves the source and output paths against an explicit repository root.
- `cosheaf draft write-artifact --input-json <path>`: writes a controlled
  draft/pre-accepted artifact from an explicit JSON request through the
  service layer. It refuses accepted status, accepted paths, readonly KB roots,
  duplicate IDs, and schema-invalid artifact payloads.
- `cosheaf draft write-artifact --input-json <path> --json`: emits
  deterministic JSON with `schema_version`, `kind`, target `path`,
  `written_paths`, `dry_run`, `accepted_write_performed`, and `record_id`.
  Expected failures emit `ErrorResult`.
- `cosheaf draft write-artifact --input-json <path> --dry-run`: validates the
  request and reports the target path without writing files.
- `cosheaf draft write-artifact --input-json <path> --repo-root <path>`:
  performs the controlled draft-artifact write for an explicit repository root.
- `cosheaf draft write-source-note --input-json <path>`: writes a staged draft
  source-note YAML record, normally under `sources/notes/`, with nested
  `SourceMetadata` validation. It is staging metadata only and is not loaded as
  an accepted artifact.
- `cosheaf draft write-source-note --input-json <path> --json`: emits the same
  deterministic controlled-write JSON shape as `write-artifact` and uses
  `ErrorResult` for expected failures.
- `cosheaf draft write-source-note --input-json <path> --dry-run`: validates
  the source-note request and reports the target path without writing files.
- `cosheaf bundle submit --input-json <path>`: validates a worker bundle v2
  manifest for review using `WorkerBundleSubmitRequest`. It does not complete
  tasks, merge outputs, run promotion, write accepted knowledge, or create
  human review.
- `cosheaf bundle submit --input-json <path> --json`: emits
  `WorkerBundleSubmitResult` with bundle ID, task ID, review-acceptance flag,
  proposed output paths, and warnings.
- `cosheaf bundle submit --input-json <path> --dry-run`: validates the bundle
  and reports review-submission output without changing task state.
- `cosheaf review request --input-json <path>`: writes a draft informational
  review-request record under `reviews/requests/`. It refuses
  `human_reviewed`, `accepted`, approval, rejection, and changes-requested
  decisions through this controlled surface.
- `cosheaf review request --input-json <path> --json`: emits the deterministic
  controlled-write JSON shape and uses `ErrorResult` for expected failures.
- `cosheaf review request --input-json <path> --dry-run`: validates the review
  request and reports the target path without writing files.
- `cosheaf review request-from-bundle --bundle <path>`: validates a
  WorkerBundle v2 manifest and writes a draft informational review-request
  record under `reviews/requests/`. It preserves bundle assumptions,
  uncertainty, failed attempts, verifier requests, legacy and typed
  counterexample candidates, dependency questions, risk flags, next steps,
  confidence, and candidate limitations as findings. It does not approve or
  reject claims, mark `human_reviewed`, create verifier results, write accepted
  knowledge, or promote artifacts.
- `cosheaf review request-from-bundle --bundle <path> --json`: emits
  deterministic JSON with `kind`, `bundle_id`, `task_id`, `review_id`, `path`,
  `written_paths`, `dry_run`, `accepted_write_performed=false`, and the
  generated draft informational request payload.
- `cosheaf review request-from-bundle --bundle <path> --dry-run`: validates
  the bundle and generated review request, reports the target path and payload,
  and writes no files.
- `cosheaf eval retrieval`: runs the default deterministic retrieval
  regression suite from `evals/retrieval/cases.yaml`.
- `cosheaf eval retrieval --repo-root <path>`: runs retrieval evals against an
  explicit repository root.
- `cosheaf eval retrieval --cases <path>`: uses an explicit repository-local
  YAML case file.
- `cosheaf eval retrieval --k <n>`: sets the top-k cutoff used for `hit@k`;
  the default is `5`.
- `cosheaf eval retrieval --json`: emits deterministic JSON report output.
- `cosheaf eval context`: runs the default deterministic context-pack
  regression suite from `evals/context/cases.yaml`.
- `cosheaf eval context --repo-root <path>`: runs context evals against an
  explicit repository root.
- `cosheaf eval context --cases <path>`: uses an explicit repository-local
  YAML case file.
- `cosheaf eval context --json`: emits deterministic JSON report output.
- `cosheaf eval checked-evidence-run-loop`: runs the default deterministic
  checked-evidence boundary suite from
  `evals/checked_evidence_run_loop/cases.yaml`.
- `cosheaf eval checked-evidence-run-loop --repo-root <path>`: runs
  checked-evidence evals against an explicit repository root.
- `cosheaf eval checked-evidence-run-loop --cases <path>`: uses an explicit
  repository-local YAML case file.
- `cosheaf eval checked-evidence-run-loop --json`: emits deterministic JSON
  report output.
- `cosheaf eval research-run-loop`: runs the default deterministic
  research-run boundary suite from `evals/research_run_loop/cases.yaml`.
- `cosheaf eval research-run-loop --repo-root <path>`: runs research-run evals
  against an explicit repository root.
- `cosheaf eval research-run-loop --cases <path>`: uses an explicit
  repository-local YAML case file.
- `cosheaf eval research-run-loop --json`: emits deterministic JSON report
  output.
- `cosheaf eval strategy-planner`: runs the default deterministic strategy
  planner boundary suite from `evals/strategy_planner/cases.yaml`.
- `cosheaf eval strategy-planner --repo-root <path>`: runs strategy-planner
  evals against an explicit repository root.
- `cosheaf eval strategy-planner --cases <path>`: uses an explicit
  repository-local YAML case file.
- `cosheaf eval strategy-planner --json`: emits deterministic JSON report
  output.
- `cosheaf run start --issue <issue-id> --operator external --json`: creates
  `.cosheaf/runs/<run-id>/run.json` and emits deterministic JSON with
  `accepted_write_performed=false`.
- `cosheaf run append-command --run <run-id> --input-json <path> --json`:
  appends a sanitized command record to an in-progress research run.
- `cosheaf run append-artifact --run <run-id> --artifact <artifact-id>
  --mode read|touched --json`: records artifact read/touched provenance.
- `cosheaf run append-output --run <run-id> --input-json <path> --json`:
  appends a repository-local output/reference record.
- `cosheaf run finalize --run <run-id> --status <status> --stop-reason <text>
  --json`: finalizes an in-progress run with a terminal status.
- `cosheaf run show <run-id> --json`: shows one runtime research run record.
- `cosheaf run evidence-report --run <run-id> --json`: emits read-only counts
  over commands, artifacts, evidence, failure logs, validation, and gate
  reports.
- `cosheaf run export-review --run <run-id> --dry-run --json`: reports the
  `reviews/runs/<run-id>.yaml` target without writing.
- `cosheaf run export-review --run <run-id> --json`: writes a review export
  under `reviews/runs/`.
- `cosheaf run replay-plan --run <run-id> --json`: emits a read-only command
  replay plan and performs no execution.
- `cosheaf strategy plan --issue <issue-id> --json`: builds a deterministic
  strategy plan for one issue, writes
  `.cosheaf/strategy/<plan-id>/strategy.json`, and emits deterministic JSON
  with `accepted_write_performed=false` and the strategy authority notice.
- `cosheaf strategy plan --issue <issue-id> --from-context <context-dir>
  --json`: builds the same runtime plan and attaches a repository-local
  context-pack reference to the context-build task.
- `cosheaf strategy show <plan-id> --json`: loads one runtime strategy plan
  from `.cosheaf/strategy/<plan-id>/strategy.json`.
- `cosheaf strategy graph <plan-id> --json`: emits the task graph from one
  runtime strategy plan without executing tasks.
- `cosheaf strategy next <plan-id> --json`: emits ranked next-step guidance
  from one runtime strategy plan without executing tasks.
- `cosheaf strategy update-from-run --plan <plan-id> --run <run-id> --json`:
  reads `.cosheaf/runs/<run-id>/run.json`, attaches non-authoritative
  command/output/artifact references to strategy nodes, preserves
  failed/skipped status, and rewrites the runtime strategy plan.
- `cosheaf strategy export-review --plan <plan-id> --dry-run --json`:
  reports the `reviews/strategy/<plan-id>.yaml` target without writing.
- `cosheaf strategy export-review --plan <plan-id> --json`: writes a
  non-authoritative review-context export under `reviews/strategy/`.
- `cosheaf graph show`: prints the directed artifact dependency graph.
- `cosheaf graph show --repo-root <path>`: prints the graph for an explicit repository root.
- `cosheaf gate`: runs the gatekeeper with default options and writes reports under `.cosheaf/reports/`.
- `cosheaf gate --repo-root <path>`: runs the gatekeeper for an explicit repository root.
- `cosheaf gate --persist-review`: also persists report copies under `reviews/gatekeeper/`.
- `cosheaf gate --pr-checklist <path>`: validates a local PR checklist markdown file through G8 when running the default gate command.
- `cosheaf gate --json`: emits a deterministic `GateRunResult` JSON payload.
- `cosheaf gate run`: explicit gatekeeper run command.
- `cosheaf gate run --repo-root <path>`: runs the gatekeeper for an explicit repository root.
- `cosheaf gate run --persist-review`: also persists report copies under `reviews/gatekeeper/`.
- `cosheaf gate run --pr-checklist <path>`: validates a local PR checklist markdown file through G8 without using GitHub API or network access.
- `cosheaf gate run --json`: emits a deterministic `GateRunResult` JSON
  payload with repository-local report paths and structured blocking and
  nonblocking issue entries.
- `cosheaf context build <issue-id>`: builds a bounded deterministic context
  pack under `context/TASKS/<issue-id>/`.
- `cosheaf context build <issue-id> --repo-root <path>`: builds a context
  pack for an explicit repository root.
- `cosheaf context build <issue-id> --role <role>`: records the retrieval role
  used for context-pack budgets. The default role is `orchestrator`.
- `cosheaf context build <issue-id> --max-cards <n>`: bounds card search
  before issue-local filtering. The default is `20`.
- `cosheaf context build <issue-id> --max-full-artifacts <n>`: explicitly
  allows at most `n` full YAML artifact pulls into `FULL_ARTIFACTS.md`. The
  default is `0`, so default context is cards-only.
- `cosheaf context build <issue-id> --public-only`: excludes private cards and
  private artifact IDs from the rendered context and retrieval audit.
- `cosheaf context build <issue-id> --json`: emits a deterministic
  `ContextBuildResult` JSON payload with repository-local written file paths,
  public-only status, whether private context was included, card count,
  full-artifact count, and content mode.
  `RETRIEVAL_AUDIT.json` includes visible
  `checked_counterexample_evidence` entries and
  `context_payload.checked_counterexample_evidence_count`; public-only context
  excludes private checked evidence text and private target artifact IDs.
- `cosheaf context show <issue-id>`: builds the context pack and prints
  `CONTEXT.md`.
- `cosheaf context show <issue-id> --repo-root <path>`: shows context for an
  explicit repository root.
- `cosheaf context show <issue-id> --role <role>`: uses the same retrieval role
  option as `context build`.
- `cosheaf context show <issue-id> --max-cards <n>`: uses the same card bound
  option as `context build`.
- `cosheaf context show <issue-id> --max-full-artifacts <n>`: uses the same
  explicit full-artifact budget option as `context build`.
- `cosheaf context show <issue-id> --public-only`: uses the same private
  exclusion behavior as `context build`.
- `cosheaf context show <issue-id> --json`: emits deterministic JSON with
  issue ID, task directory, repository-local context file path, public-only
  status, private-context-included flag, and rendered `CONTEXT.md` content.
- `cosheaf memory cards`: builds deterministic artifact cards from existing
  repository metadata. Default output is compact text lines, not full artifact
  YAML or statements.
- `cosheaf memory cards --repo-root <path>`: builds cards for an explicit
  repository root.
- `cosheaf memory cards --issue <issue-id>`: limits cards to the issue record's
  direct `related_artifacts`, after scope/status filters.
- `cosheaf memory cards --status <status>`: filters cards by artifact-card
  lifecycle/trust status, such as `accepted` or `draft`.
- `cosheaf memory cards --json`: emits deterministic JSON card DTOs,
  including `failure_count` and `recent_failure_directions` for artifact-level
  failed-attempt memory when present.
- `cosheaf memory search <query>`: searches deterministic artifact cards with
  local SQLite FTS5/BM25 when available, deterministic lexical fallback
  otherwise, and issue-conditioned graph ranking signals. Default text output
  prints compact card lines with total score, not full artifact YAML or
  statements. Recent failure-log directions are searchable with explicit
  failure-memory relevance reasons; they do not alter trust score, review
  state, verifier state, artifact status, gate results, or promotion
  authority.
- `cosheaf memory search <query> --repo-root <path>`: searches cards for an
  explicit repository root.
- `cosheaf memory search <query> --issue <issue-id>`: uses the issue and its
  direct `related_artifacts` as Personalized PageRank seeds after
  scope/status filters, without granting accepted-promotion authority.
- `cosheaf memory search <query> --seed-artifact <artifact-id>`: adds an
  explicit artifact seed to personalized ranking; repeat for multiple seeds.
- `cosheaf memory search <query> --pin-artifact <artifact-id>`: adds a
  stronger pinned artifact seed to personalized ranking; repeat for multiple
  pins.
- `cosheaf memory search <query> --status <status>`: filters search candidates
  by artifact-card lifecycle/trust status.
- `cosheaf memory search <query> --include-refuted`: includes refuted cards
  with an explicit score penalty.
- `cosheaf memory search <query> --include-obsolete`: includes obsolete and
  superseded cards with an explicit score penalty.
- `cosheaf memory search <query> --explain`: prints score component
  breakdowns and relevance reasons in text output.
- `cosheaf memory search <query> --json`: emits a deterministic
  `RetrievalResult` JSON payload with card hits, score breakdowns, failure
  memory card metadata, and audit metadata. Results that surface failure-log
  memory include warnings that failure memory is not proof, verifier success,
  human review, checked counterexample evidence, or accepted-status evidence.
- `cosheaf memory graph build`: rebuilds
  `.cosheaf/memory/graph_snapshot.json` from repository YAML plus optional
  local sidecar signals such as gate reports and task run records.
- `cosheaf memory graph build --repo-root <path>`: rebuilds the memory graph
  sidecar for an explicit repository root.
- `cosheaf memory graph build --json`: emits a deterministic JSON build
  summary with the graph fingerprint, node count, edge count, sidecar path,
  and warnings.
- `cosheaf memory graph pagerank`: computes deterministic weighted global
  PageRank from an existing `.cosheaf/memory/graph_snapshot.json` sidecar.
- `cosheaf memory graph pagerank --repo-root <path>`: computes PageRank for an
  explicit repository root.
- `cosheaf memory graph pagerank --json`: emits a deterministic
  `PageRankResult` JSON payload.
- `cosheaf provider list`: lists provider gateway modes currently exposed
  through the CLI.
- `cosheaf provider list --json`: emits deterministic JSON with
  `schema_version` and provider metadata for `fake` and `openai`, including
  mode, default-enabled status, network policy, API-key requirement, fake-run
  availability, and real-run availability.
- `cosheaf provider config-check`: checks provider CLI configuration without
  revealing secret values.
- `cosheaf provider config-check --repo-root <path>`: checks configuration for
  an explicit repository root.
- `cosheaf provider config-check --provider <provider>`: checks `fake` or
  `openai`. Other `ProviderName` values currently return the structured
  `provider_unsupported` error because their CLI/provider behavior is not
  implemented.
- `cosheaf provider config-check --api-key-env <name>`: uses an explicit
  environment variable name for API-key presence checks. Output reports
  presence only and prints `<redacted>` instead of secret values.
- `cosheaf provider config-check --json`: emits deterministic JSON with
  provider id, mode, enabled flag, API-key environment variable name,
  API-key presence, redacted API-key value status, real-run CLI availability,
  and network mode.
- `cosheaf provider preview-send --issue <issue-id> --provider <provider>`:
  previews the provider-send context payload shape for an issue without
  sending artifact text or making a hosted provider call.
- `cosheaf provider preview-send --repo-root <path>`: previews context for an
  explicit repository root.
- `cosheaf provider preview-send --include-private --policy-mode private_research --allow-private-context`:
  permits private-context preview only when private-research policy and
  explicit private-context permission are both supplied. Without those flags,
  private-context previews return structured policy errors.
- `cosheaf provider preview-send --json`: emits deterministic JSON with
  provider id, mode, `real_run_performed: false`, the
  `ProviderContextPreview` payload, artifact count, card count,
  full-artifact count, content mode, root scopes, estimated token count,
  private-context inclusion, and risk flags.
- `cosheaf provider fake-run --input-json <path>`: runs the deterministic fake
  provider from a JSON `ProviderGatewayRequest`-compatible object. The command
  forces `provider: fake`, defaults the model and public consent when omitted,
  writes redacted provider logs under `.cosheaf/providers/`, performs no
  hosted network call, writes no accepted knowledge, and performs no
  promotion.
- `cosheaf provider fake-run --repo-root <path>`: runs the fake provider using
  an explicit repository root for provider logs.
- `cosheaf provider fake-run --json`: emits deterministic `ModelCallResult`
  JSON plus the redacted provider log payload. It is allowed in CI.
- `cosheaf provider real-run --input-json <path> --provider openai-compatible --confirm-send --allow-network --json`:
  performs one explicitly consented OpenAI-compatible provider call from an
  input envelope containing `provider_config` and inline `context_preview`.
  The command fails closed without `--confirm-send`, without
  `--allow-network`, without valid endpoint/API-key environment configuration,
  without an inline context preview, or when private context is present without
  private-research preview policy and `--allow-private-context`.
- `cosheaf provider real-run --repo-root <path>`: writes redacted provider run
  records under `.cosheaf/providers/` for the selected repository root.
- `cosheaf provider real-run --json`: emits deterministic `ModelCallResult`
  JSON with `real_run_performed: true`, the inline context preview, and the
  redacted provider log payload. Tests use mocked transport injection; CI does
  not call live provider networks.
- `cosheaf mcp list-tools`: prints the read-only MCP tool whitelist, one tool
  name per line.
- `cosheaf mcp list-tools --repo-root <path>`: validates command context
  against an explicit repository root before listing the same tool whitelist.
- `cosheaf mcp serve --stdio`: starts the minimal read-only stdio JSON-RPC MCP
  surface for the current repository. It reads one JSON-RPC request per input
  line and writes one JSON-RPC response per output line.
- `cosheaf mcp serve --stdio --repo-root <path>`: serves the same read-only
  MCP surface for an explicit repository root.
- `cosheaf task create --issue <issue-id> --worker <worker-type>`: creates an open local agent task under `.cosheaf/tasks/` after confirming the issue exists.
- `cosheaf task create --issue <issue-id> --worker <worker-type> --repo-root <path>`: creates the task for an explicit repository root.
- `cosheaf task list`: lists local task records in deterministic task ID order.
- `cosheaf task list --repo-root <path>`: lists local task records for an explicit repository root.
- `cosheaf task complete <task-id> --bundle <path>`: validates a local worker output bundle and marks the task completed without merging accepted knowledge.
- `cosheaf task complete <task-id> --bundle <path> --repo-root <path>`: completes the task for an explicit repository root.
- `cosheaf task run <task-id> -- <command> [args...]`: runs an explicit local argv command for an existing task, logs stdout/stderr and run metadata under `.cosheaf/tasks/<task-id>/runs/<run-id>/`, and does not complete the task by default.
- `cosheaf task run <task-id> --timeout-seconds <seconds> -- <command> [args...]`: enforces a positive command timeout.
- `cosheaf task run <task-id> --cwd <repo-local-path> -- <command> [args...]`: runs from an optional repository-local working directory. Paths outside the repository are rejected.
- `cosheaf task run <task-id> --bundle <path> -- <command> [args...]`: requires a repository-local bundle path, validates a worker output bundle after a successful command without completing the task, and accepts either a YAML manifest or a directory containing `bundle.yaml`.
- `cosheaf task run <task-id> --complete-with-bundle <path> -- <command> [args...]`: requires a repository-local bundle path, validates a worker output bundle after a successful command, accepts either a YAML manifest or a directory containing `bundle.yaml`, and delegates task completion to the existing orchestrator stub.
- `cosheaf task run <task-id> ... --repo-root <path> -- <command> [args...]`: runs the local worker command for an explicit repository root.
- `cosheaf orchestrator plan --issue <issue-id>`: creates a deterministic
  local-only task-DAG plan for an existing issue and prints a compact text
  summary. It does not build context packs, execute workers, run gates, request
  review, write accepted knowledge, or promote artifacts.
- `cosheaf orchestrator plan --issue <issue-id> --json`: emits the
  deterministic `Plan` payload as JSON with top-level `schema_version: 1`.
- `cosheaf orchestrator plan --issue <issue-id> --repo-root <path>`: creates
  the plan for an explicit repository root.
- `cosheaf orchestrator run --issue <issue-id> --dry-run --local-only`: runs a
  deterministic local-only orchestrator dry-run for an existing issue. It
  creates issue-scoped local task records for the planned nodes, executes
  explicit local argv commands through the existing local worker runner,
  validates worker bundle v2 manifests, reduces them into reducer records,
  writes an inspectable run record and structured `run_log.json` under
  `.cosheaf/orchestrator/`, and does not call hosted LLMs, use network
  services, run gates, request human review, write accepted knowledge, or
  promote artifacts.
- `cosheaf orchestrator run --issue <issue-id> --dry-run --local-only --timeout-seconds <seconds>`:
  enforces a positive timeout for each local worker command.
- `cosheaf orchestrator run --issue <issue-id> --dry-run --local-only --repo-root <path>`:
  runs the local-only dry-run for an explicit repository root.
- `cosheaf orchestrator run --issue <issue-id> --provider fake --json`: runs
  the explicit hosted-worker orchestrator path for an existing issue with the
  deterministic fake provider. It plans the issue, previews provider-send
  context shape, dispatches planned nodes to role-specific hosted workers,
  writes run-local provider-record copies under
  `.cosheaf/orchestrator/<issue-id>/runs/<run-id>/providers/`, writes hosted
  WorkerBundle v2 manifests under run-local `bundles/`, writes typed
  sub-results under `typed-results/`, reduces only validated WorkerBundle
  outputs, performs no hosted network call, and writes no accepted knowledge.
- `cosheaf orchestrator run --issue <issue-id> --provider openai-compatible --confirm-send --json`:
  enters the explicit OpenAI-compatible hosted-worker dispatch boundary after
  context preview and consent checks. The default CLI path does not instantiate
  the optional stdlib HTTP transport and reports missing transport instead of
  making a network call unless a configured/injected transport exists.
- `cosheaf orchestrator run --issue <issue-id> --provider <provider> --include-private --policy-mode private_research --allow-private-context --confirm-send --json`:
  permits private-context hosted-worker dispatch only when private-research
  policy and explicit private-context consent are supplied. Public mode remains
  public-only by default.

### Python API

#### Agent Access DTOs

- `cosheaf.services.models.AgentAccessModel`: strict Pydantic v2 base class for
  versioned agent-access DTOs with deterministic `to_dict()` and `to_json()`.
- `cosheaf.services.models.WorkspaceInfoResult`: public workspace-info DTO with
  `schema_version`, workspace name, repository root, configured/legacy mode,
  ordered KB roots, public/private root scopes, readonly flags, priorities, and
  workspace policy fields.
- `cosheaf.services.models.ValidateResult`: public validation DTO with
  checked-record count and structured failures.
- `cosheaf.services.models.GateRunResult`: public gate-run DTO with verdict,
  report paths, blocking issues, and nonblocking issues.
- `cosheaf.services.models.MemorySearchRequest`: public memory-search request
  DTO with query, issue, allowed scopes, allowed statuses, public-only flag,
  refuted/obsolete inclusion flags, and card budget.
- `cosheaf.services.models.MemorySearchResult`: public memory-search response
  DTO with request, compact artifact cards, and warnings.
- `cosheaf.services.models.ContextBuildRequest`: public context-build request
  DTO with issue, role, card/full-artifact budgets, policy mode, public-only
  flag, and private-context permission flag.
- `cosheaf.services.models.ContextBuildResult`: public context-build response
  DTO with issue, task directory, written files, public-only flag, and private
  context inclusion flag. It also reports `card_count`,
  `full_artifact_count`, and `content_mode` so callers can distinguish
  cards-only context from context that included full artifact pulls.
- `cosheaf.services.models.CreateTaskRequest` and
  `cosheaf.services.models.CreateTaskResult`: public task-creation DTOs.
- `cosheaf.services.models.WorkerBundleSubmitRequest` and
  `cosheaf.services.models.WorkerBundleSubmitResult`: public worker-bundle
  validation/submission DTOs that preserve review-only output semantics.
- `cosheaf.services.models.DraftArtifactWriteRequest` and
  `cosheaf.services.models.DraftArtifactWriteResult`: public draft-write DTOs
  that reject accepted artifact writes.
- `cosheaf.services.models.ProviderConsent`: public provider-send consent DTO
  with consent required/granted flags, private-context permission, and policy
  scope.
- `cosheaf.services.models.ProviderContextPreviewItem`: public provider-send
  preview item DTO with artifact id, root scope, status, estimated token count,
  and risk flags. It does not include artifact text.
- `cosheaf.services.models.ProviderContextPreview`: public provider-send
  preview DTO with issue id, policy mode, public/private inclusion flags,
  artifact ids, root scopes, estimated token count, card count,
  full-artifact count, content mode, risk flags, and preview items. It does
  not include issue text, full artifact text, API keys, provider credentials,
  or secrets.
- `cosheaf.services.models.ModelCallRequest` and
  `cosheaf.services.models.ModelCallResult`: public provider-neutral model-call
  DTOs for future hosted workers.
- `cosheaf.services.models.ProviderRunRecord`: public provider-run audit DTO
  with provider/model, policy scope, consent, private-context-sent flag,
  status, timestamps, request fingerprint, and optional repository-local log
  path.
- `cosheaf.research.run.ResearchRunRecord`: strict Pydantic v2 DTO for one
  repository-local research run. It records issue ID, operator kind/label,
  timestamps, status, command records, artifact references, controlled outputs,
  evidence references, validation/gate report references, limitations, and the
  non-authority notice.
- `cosheaf.research.run.ResearchRunCommandRecord`: sanitized command metadata
  with explicit argv, cwd, timestamps, exit code, status, optional stdout/stderr
  sidecar paths or hashes, skipped/unavailable reasons, and redaction metadata.
- `cosheaf.research.run.ResearchRunOutputRef`: repository-local output or
  reference metadata for workspace summaries, context packs, controlled writes,
  worker bundles, verifier evidence, checked counterexample evidence, failure
  logs, validation reports, gate reports, PR/issue refs, or other notes.
- `cosheaf.strategy.models.StrategyPlan`: strict Pydantic v2 DTO for one
  generated strategy plan. It records `plan_id`, `issue_id`, timezone-aware
  `created_at`, a `StrategyProblem`, a `StrategyTaskGraph`, ranked
  `StrategyNextStep` entries, the strategy authority notice, and
  `accepted_write_performed=false`.
- `cosheaf.strategy.models.StrategyTaskGraph`: strict Pydantic v2 DTO for a
  directed task graph with unique `StrategyTaskNode.node_id` values and
  validated task edges, dependencies, and blocked-by references.
- `cosheaf.strategy.models.StrategyTaskNode`: strict Pydantic v2 DTO for one
  bounded research task. It records kind, status, public/private/workspace
  scope, expected evidence kinds, related artifacts, failure-log entries,
  candidate counterexamples, checked counterexample evidence, research-run
  IDs, optional command argv, repository-local input paths, and controlled
  non-accepted write paths. Phase 2 nodes may also include
  `StrategyTaskReference` entries for non-authoritative commands, context
  packs, research runs, artifacts, checked evidence, review exports,
  validation reports, gate reports, failure logs, or other references.
- `cosheaf.strategy.models.StrategyTaskReference`: strict Pydantic v2 DTO for
  one strategy node reference. Paths are repository-local and cannot point
  into accepted KB paths. Text fields reject common secret-looking token
  shapes.
- `cosheaf.strategy.planner.build_strategy_plan(context, issue_id)`: builds a
  deterministic Phase 1 plan from issue metadata, direct related artifacts,
  one-hop dependencies, artifact failure memory, candidate counterexample
  references, staged checked counterexample evidence, and research-run records.
  It performs no task execution, provider call, review creation, accepted
  write, or promotion.
- `cosheaf.strategy.storage.write_strategy_plan(context, plan)`: writes a
  generated plan under `.cosheaf/strategy/<plan-id>/strategy.json`.
- `cosheaf.strategy.storage.load_strategy_plan(context, plan_id)`: loads and
  validates one runtime strategy plan by ID.
- `cosheaf.strategy.storage.attach_context_reference(context, plan,
  context_dir)`: attaches a repository-local context-pack reference to a plan
  before writing it.
- `cosheaf.strategy.storage.update_strategy_plan_from_run(context, *,
  plan_id, run_id)`: reads one research-run record, attaches provenance
  references to matching task nodes, preserves failed/skipped state, and
  rewrites the runtime strategy plan.
- `cosheaf.strategy.storage.export_strategy_review(context, *, plan_id,
  dry_run)`: writes or previews a non-authoritative strategy review export
  under `reviews/strategy/`.
- `cosheaf.evals.strategy_planner`: deterministic strategy-planner eval
  harness. Default cases live in `evals/strategy_planner/cases.yaml` and do
  not require hosted providers, API keys, MCP, network, SAT, SMT, Lean, or
  lake.
- `cosheaf.evals.research_run_loop`: deterministic research-run loop eval
  harness. Default cases live in `evals/research_run_loop/cases.yaml` and do
  not require hosted providers, API keys, MCP, network, SAT, SMT, Lean, or
  lake.
- `cosheaf.services.models.ErrorResult`: public standard error DTO with code,
  message, remediation, blocking flag, optional repository-local
  `related_path`, optional `related_artifact`, and string-to-string details.
- `cosheaf.services.models.AGENT_ACCESS_STABLE_ERROR_CODES`: sorted tuple of
  currently stable machine-readable agent-access error codes. Current values:
  `accepted_write_forbidden`, `artifact_file_validation_failed`,
  `artifact_id_exists`, `artifact_model_validation_failed`,
  `artifact_not_found`, `artifact_path_exists`, `authority_claim_forbidden`,
  `bundle_complete_forbidden`, `bundle_submit_failed`, `context_build_failed`,
  `context_show_failed`,
  `draft_write_failed`, `failure_log_from_bundle_failed`, `gate_issue`,
  `hosted_worker_policy_violation`,
  `human_review_forbidden`,
  `invalid_artifact_id`, `invalid_artifact_target_path`,
  `invalid_input_json`, `invalid_staging_path`, `invalid_timestamp`,
  `memory_cards_failed`, `memory_search_failed`, `missing_required_domain`,
  `no_writable_kb_root`, `orchestrator_plan_failed`,
  `orchestrator_run_failed`, `private_context_requires_consent`,
  `private_context_requires_policy`, `provider_confirm_send_required`,
  `provider_context_preview_failed`, `provider_context_scope_violation`,
  `provider_output_validation_failed`, `provider_request_validation_failed`,
  `provider_unsupported`, `readonly_kb_root`, `repository_load_failed`,
  `review_request_failed`, `source_note_write_failed`,
  `timestamp_missing_timezone`, `unknown_context_policy_mode`,
  `validation_failed`, `validation_unexpected_error`, and
  `workspace_config_failed`.
- `cosheaf.services.models.AGENT_ACCESS_SCHEMA_MODELS`: mapping used to
  generate the versioned JSON Schema files under `schemas/agent_access/`.

#### Agent Access JSON Schemas

- `schemas/agent_access/workspace_info_result.schema.json`
- `schemas/agent_access/validate_result.schema.json`
- `schemas/agent_access/gate_run_result.schema.json`
- `schemas/agent_access/memory_search_request.schema.json`
- `schemas/agent_access/memory_search_result.schema.json`
- `schemas/agent_access/context_build_request.schema.json`
- `schemas/agent_access/context_build_result.schema.json`
- `schemas/agent_access/create_task_request.schema.json`
- `schemas/agent_access/create_task_result.schema.json`
- `schemas/agent_access/worker_bundle_submit_request.schema.json`
- `schemas/agent_access/worker_bundle_submit_result.schema.json`
- `schemas/agent_access/draft_artifact_write_request.schema.json`
- `schemas/agent_access/draft_artifact_write_result.schema.json`
- `schemas/agent_access/model_call_request.schema.json`
- `schemas/agent_access/model_call_result.schema.json`
- `schemas/agent_access/provider_run_record.schema.json`
- `schemas/agent_access/error_result.schema.json`

#### Service Layer

- `cosheaf.services.WorkspaceService`: typed service for workspace inspection.
- `cosheaf.services.WorkspaceService.info() -> WorkspaceInfoResult`: returns
  workspace name, resolved repository root, configured/legacy mode, and ordered
  KB root metadata.
- `cosheaf.services.ValidationService`: typed service for repository and
  artifact validation.
- `cosheaf.services.ValidationService.validate_repository() -> ValidationReport`:
  validates discovered repository YAML records and invariants.
- `cosheaf.services.ValidationService.validate_artifact_file(path) -> ValidationReport`:
  validates one repository-local artifact file.
- `cosheaf.services.GateService`: typed service for gatekeeper execution.
- `cosheaf.services.GateService.run(...) -> GatekeeperRunResult`: runs
  gatekeeper checks and returns report metadata and written report paths.
- `cosheaf.services.MemorySearchService`: typed service for deterministic
  artifact-card construction and search.
- `cosheaf.services.MemorySearchService.cards(...) -> tuple[ArtifactCard, ...]`:
  returns compact artifact cards without writing sidecars or full artifact
  content.
- `cosheaf.services.MemorySearchService.search(...) -> RetrievalResult`:
  returns deterministic card-search results with retrieval audit metadata.
- `cosheaf.services.OrchestratorPlanService`: typed service for deterministic
  issue-scoped orchestrator plans.
- `cosheaf.services.OrchestratorPlanService.plan_for_issue(issue_id) -> Plan`:
  creates a deterministic plan for an existing issue without executing
  workers, calling hosted providers, running gates, writing accepted knowledge,
  or promoting artifacts.
- `cosheaf.services.ContextPackService`: typed service for bounded
  issue-scoped context packs.
- `cosheaf.services.ContextPackService.build(...) -> ContextPackResult`:
  writes a deterministic context pack for an issue.
- `cosheaf.services.ContextPackService.show(...) -> str`: builds and returns
  the rendered `CONTEXT.md` text for an issue.
- `cosheaf.services.ContextSendPolicyService`: typed provider-send context
  preview policy service.
- `cosheaf.services.ContextSendPolicyService.provider_preview(request) -> ProviderContextPreview | ErrorResult`:
  returns a safe provider-send preview for a `ContextBuildRequest`, or a
  structured `ErrorResult` when policy denies the request. Public mode
  (`policy_mode=public`; the v4 plan name is `public_research`) uses public KB
  scope only. Private KB context requires `policy_mode=private_research`,
  `public_only=false`, and explicit private-context permission. Workspace and
  framework scope cards are excluded from provider-send previews under the
  current matrix. The method returns metadata only: artifact IDs, root scopes,
  token estimates, card count, full-artifact count, content mode, and risk
  flags. The implemented provider-send preview path remains cards-only and
  reports `full_artifact_count=0`. It does not call providers, implement MCP,
  include full artifact text, include full issue text, or write files. Denials
  use stable `ErrorResult` codes including `private_context_requires_policy`,
  `private_context_requires_consent`, and `provider_context_scope_violation`.
- `cosheaf.services.model_calls.ModelCallService`: service wrapper around the
  provider gateway core.
- `cosheaf.services.model_calls.ModelCallService.call(request, *, config=None, provider=None) -> ModelCallResult | ProviderError`:
  calls the configured provider gateway. The fake path performs no network
  call. The OpenAI-compatible path requires explicit enabled configuration and
  uses an injected transport object; it does not import hosted-provider SDKs or
  perform real network calls by itself.
- `cosheaf.services.TaskService`: typed service for local task records and
  explicit local worker command runs.
- `cosheaf.services.TaskService.create_task(...) -> AgentTask`: creates an
  open local task for an existing issue.
- `cosheaf.services.TaskService.list_tasks() -> tuple[AgentTask, ...]`:
  returns local tasks in deterministic order.
- `cosheaf.services.TaskService.complete_task(...) -> TaskCompletionResult`:
  validates a local worker output bundle and marks the task completed without
  merging accepted knowledge.
- `cosheaf.services.TaskService.run_task(...) -> LocalWorkerRunResult`: runs an
  explicit local argv command for an existing task.
- `cosheaf.services.BundleValidationService`: typed service for worker bundle
  v2 validation and reduction.
- `cosheaf.services.BundleValidationService.validate(path) -> WorkerBundleV2`:
  validates a worker bundle v2 manifest.
- `cosheaf.services.BundleValidationService.reduce(path, *, reducer_id) -> ReducerResult`:
  validates and reduces a worker bundle v2 manifest into review context.
- `cosheaf.services.BundleValidationService.submit(request, *, dry_run=False) -> WorkerBundleSubmitResult`:
  validates a worker bundle v2 manifest for review without completing tasks,
  merging outputs, writing accepted knowledge, or promoting artifacts.
- `cosheaf.services.DraftWriteService`: controlled draft/pre-accepted
  lifecycle artifact write service.
- `cosheaf.services.DraftWriteService.create_artifact(...) -> ArtifactWriteResult`:
  creates deterministic draft/pre-accepted artifact YAML and refuses direct
  accepted artifact creation.
- `cosheaf.services.DraftWriteService.write_artifact_request(request, *, dry_run=False) -> ControlledWriteResult`:
  writes or previews a controlled draft artifact request and reports exact
  target/written paths.
- `cosheaf.services.DraftWriteService.write_source_note(request, *, dry_run=False) -> ControlledWriteResult`:
  writes or previews a staged draft source-note record with nested
  `SourceMetadata` validation.
- `cosheaf.services.DraftWriteService.write_review_request(request, *, dry_run=False) -> ControlledWriteResult`:
  writes or previews a draft informational review-request record and refuses
  human-review spoofing.
- `cosheaf.services.DraftWriteService.write_review_request_from_bundle(bundle_path, *, dry_run=False) -> ReviewRequestFromBundleResult`:
  validates a WorkerBundle v2, generates a draft informational review request
  from its failure/counterexample/review-only fields, and writes or previews it
  through `write_review_request`.
- `cosheaf.services.DraftWriteService.append_failure_log_entry(artifact_id, request, *, dry_run=False) -> ControlledWriteResult`:
  validates and appends one `FailureLogEntry` to a writable non-accepted
  artifact, or previews the append in dry-run mode. It refuses accepted paths,
  accepted artifact status, readonly KB roots, and authority-spoofing fields.
- `cosheaf.services.DraftWriteService.plan_failure_log_entries_from_bundle(bundle_path, *, target_artifact_id) -> FailureLogFromBundlePlanResult`:
  validates a WorkerBundle v2 and plans proposed artifact failure-log entries
  from `failed_attempts` without writing files.
- `cosheaf.services.DraftWriteService.append_failure_log_entries_from_bundle(bundle_path, *, target_artifact_id, dry_run=False) -> FailureLogFromBundleWriteResult`:
  appends or previews WorkerBundle-derived failure-log entries through the same
  controlled write boundary as `append_failure_log_entry`.
- `cosheaf.services.FailureLogFromBundlePlanResult`: frozen dataclass with the
  validated bundle, target artifact ID/path, and proposed
  `FailureLogEntry` values.
- `cosheaf.services.FailureLogFromBundleWriteResult`: frozen dataclass with the
  WorkerBundle-derived plan and the `ControlledWriteResult`.
- `cosheaf.services.ReviewRequestFromBundleResult`: frozen dataclass with the
  validated `bundle`, generated request mapping, and `ControlledWriteResult`.
  It is review context only and has no accepted-write, verifier-result,
  human-review, or promotion authority.
- `cosheaf.services.ServiceError`: expected service-layer failure base class
  with stable `code`, `remediation`, `blocking`, `details`, and
  `to_error_result() -> ErrorResult`.
- `cosheaf.services.DraftWriteServiceError`: expected error for controlled
  draft-write failures. Current stable codes are included in
  `AGENT_ACCESS_STABLE_ERROR_CODES`.
- `cosheaf.services.WorkspaceInfoResult`, `KbRootInfo`, and
  `ArtifactWriteResult`: frozen dataclass result DTOs returned by service
  methods.
- `cosheaf.services.ControlledWriteResult`: frozen dataclass result for
  controlled draft/staging write commands with `kind`, `relative_path`,
  `written_paths`, `dry_run`, `accepted_write_performed`, and `record_id`.

#### MCP Server

- `cosheaf.mcp.READ_ONLY_TOOL_NAMES`: ordered read-only MCP tool whitelist:
  `workspace_info`, `validate`, `gate_run`, `memory_search`, `context_build`,
  `context_show`, and `orchestrator_plan`.
- `cosheaf.mcp.READ_ONLY_PROMPT_NAMES`: ordered governance-safe MCP prompt
  whitelist: `start_issue_work`, `reason_about_issue`, `verify_draft`,
  `prepare_review_bundle`, and `public_kb_contribution_check`.
- `cosheaf.mcp.tool_definitions() -> list[dict[str, Any]]`: returns
  deterministic MCP-style tool metadata and JSON schemas for the read-only
  whitelist.
- `cosheaf.mcp.prompt_definitions() -> list[dict[str, Any]]`: returns
  deterministic MCP-style prompt metadata for the governance-safe prompt
  whitelist.
- `cosheaf.mcp.resource_definitions() -> list[dict[str, str]]`: returns
  deterministic MCP-style resource metadata for `cosheaf://workspace`,
  `cosheaf://issues/{issue_id}`,
  `cosheaf://artifacts/public/{artifact_id}/card`,
  `cosheaf://artifacts/private/{artifact_id}/card`,
  `cosheaf://context/public/{issue_id}`,
  `cosheaf://context/private/{issue_id}`, and `cosheaf://gate/latest`.
- `cosheaf.mcp.ReadOnlyMcpServer`: protocol-level read-only JSON-RPC handler
  over the shared service layer. It exposes `tools/list`, `tools/call`,
  `resources/list`, `resources/read`, `prompts/list`, `prompts/get`, and
  `initialize`.
- `cosheaf.mcp.ReadOnlyMcpServer.handle(request) -> dict[str, Any]`: handles
  one JSON-RPC request mapping and returns one JSON-RPC response mapping.
- `cosheaf.mcp.serve_stdio(context, ...) -> None`: serves line-delimited
  JSON-RPC requests over stdio streams.

The read-only MCP surface does not expose arbitrary shell, draft writes,
accepted writes, artifact promotion, hosted provider calls, environment dumps,
or unrestricted filesystem access. Public-mode artifact-card resources deny
private artifact cards with a structured `private_resource_denied` error.
`gate_run` and `context_build` may write deterministic runtime sidecars, but
they do not modify source-of-truth artifact YAML or accepted knowledge.
Prompt templates are static governance guidance. They do not read or include
private KB content, artifact statements, provider credentials, or environment
data.

#### Source Ingestion

- `cosheaf.ingest.MarkItDownIngestAdapter`: optional local source-ingestion
  adapter. It converts repository-local files to staged Markdown and
  provenance metadata when MarkItDown is installed.
- `cosheaf.ingest.MarkItDownIngestAdapter.convert(context, source_path, *, out_dir=Path(".cosheaf/ingest"), generated_at=None) -> MarkItDownIngestResult`:
  converts one source file, rejects remote URL inputs, rejects paths outside
  the repository, rejects accepted KB output paths, and returns unavailable
  metadata when MarkItDown is absent.
- `cosheaf.ingest.MarkItDownIngestResult`: frozen dataclass carrying
  deterministic provenance metadata for one conversion attempt.
- `cosheaf.ingest.MarkItDownIngestResult.to_dict() -> dict[str, Any]`: returns
  JSON-serializable conversion provenance.
- `cosheaf.ingest.MarkItDownIngestResult.to_json() -> str`: returns
  deterministic indented JSON with a trailing newline.
- `cosheaf.ingest.IngestError`: expected error for source-ingestion boundary
  failures such as nonlocal source paths or accepted KB output paths.

Default MarkItDown ingest options are disabled:

- `allow_remote_urls: false`
- `allow_plugins: false`
- `allow_ocr: false`
- `allow_llm_vision: false`
- `allow_azure_document_intelligence: false`

The adapter writes staging output only. It does not write artifact YAML,
review records, verifier results, accepted knowledge, or promotion evidence.
MarkItDown remains an optional package and is not required for validation,
gates, index rebuilds, context packs, promotion, or default installation.

#### Workspace Configuration

- `cosheaf.config.workspace.KbRootConfig`: Pydantic v2 model for one KB root
  with `name`, repository-relative `path`, `readonly`, and `priority`.
- `cosheaf.config.workspace.WorkspacePolicy`: Pydantic v2 model for workspace
  policy fields `private_can_depend_on_public`,
  `public_can_depend_on_private`, and `accepted_requires_source`.
- `cosheaf.config.workspace.WorkspaceConfig`: Pydantic v2 model for workspace
  configuration with `name`, `kb`, `policy`, and `configured` fields.
- `cosheaf.config.workspace.WorkspaceConfig.legacy(repo_root: Path) -> WorkspaceConfig`:
  returns the no-config default with one writable `kb` root.
- `cosheaf.config.workspace.WorkspaceConfig.ordered_kb -> tuple[KbRootConfig, ...]`:
  returns KB roots sorted by `(priority, name, path)`.
- `cosheaf.config.workspace.WorkspaceConfig.root_by_name(name: str) -> KbRootConfig | None`:
  returns one KB root by name when configured.
- `cosheaf.config.workspace.WorkspaceConfigError`: expected config load or
  validation error.
- `cosheaf.config.workspace.load_workspace_config(repo_root: str | Path) -> WorkspaceConfig`:
  loads `cosheaf.toml`, or returns legacy single-root config when absent.

`cosheaf.toml` uses:

- `[workspace]`
- `workspace.name`
- `[[kb]]`
- `kb.name`
- `kb.path`
- `kb.readonly`
- `kb.priority`
- `[policy]`
- `policy.private_can_depend_on_public`
- `policy.public_can_depend_on_private`
- `policy.accepted_requires_source`

#### Core Models

- `cosheaf.core.artifact.BaseArtifact`: Pydantic v2 base model for typed artifacts.
- `cosheaf.core.artifact.Evidence`: Pydantic v2 model for evidence references.
- `cosheaf.core.artifact.Risk`: Pydantic v2 model for artifact risk metadata.
- `cosheaf.core.artifact.ReviewRef`: Pydantic v2 model for inline review state.
- `cosheaf.core.artifact.SourceMetadata`: Pydantic v2 model for structured source/citation metadata.
- `cosheaf.core.artifact.FormalizationRef`: Pydantic v2 model for one external
  formal declaration reference.
- `cosheaf.core.artifact.AlignmentReview`: Pydantic v2 model for semantic
  alignment review between an informal artifact statement and a formal
  declaration.
- `cosheaf.core.artifact.VerificationPolicy`: Pydantic v2 model for
  per-artifact formal-link, Lean-check, and alignment-review expectations.
- `cosheaf.core.artifact.FailureLogEntry`: Pydantic v2 model for one
  artifact-local failed-attempt memory entry.
- `cosheaf.core.formal_library.FormalLibrary`: Pydantic v2 model for one
  pinned external Lean library manifest entry.
- `cosheaf.core.formal_library.FormalLibraryManifest`: Pydantic v2 model for a
  manifest of external Lean libraries referenced by artifact metadata.
- `cosheaf.core.formal_library.FormalLibraryManifestError`: expected manifest
  or library-reference validation error.
- `cosheaf.core.formal_library.validate_library_ref(value: str) -> str`:
  validates the manifest library ID syntax used by
  `formalizations[].library_ref`.
- `cosheaf.core.formal_library.validate_formalization_library_refs(refs,
  manifest) -> None`: requires each formalization reference to resolve against
  a loaded formal library manifest.
- `cosheaf.core.formal_library.load_formal_library_manifest(path) ->
  FormalLibraryManifest`: loads a YAML formal library manifest.
- `cosheaf.core.task.AgentTask`: Pydantic v2 model for local task records, re-exported through `cosheaf.agent.task.AgentTask`.

`BaseArtifact` fields include:

- `sources: list[SourceMetadata]`
- `formalizations: list[FormalizationRef]`
- `alignment: AlignmentReview`
- `verification_policy: VerificationPolicy`
- `failure_log: list[FailureLogEntry]`

`FailureLogEntry` fields are:

- `failure_id`
- `attempted_at`
- `recorded_by`
- `origin`: `human`, `agent`, `provider`, `verifier`, or `imported_bundle`
- `attempt_kind`: `proof_attempt`, `reduction_attempt`,
  `construction_attempt`, `counterexample_search`, `formalization_attempt`,
  `verifier_attempt`, `retrieval_attempt`, or `other`
- `target`
- `direction`
- `summary`
- `failed_because`
- `evidence_paths`
- `related_verifier_results`
- `related_counterexample_candidates`
- `next_possible_directions`
- `status`: `open`, `superseded`, `invalidated`, `resolved`, or `archived`
- `limitations`

`FailureLogEntry` is durable research memory only. It is not proof, verifier
success, checked counterexample evidence, human review, gate success, accepted
status, or promotion evidence. Its `evidence_paths` must be repository-local
and must not target accepted KB paths.

`SourceMetadata` fields are:

- `kind`: `paper`, `book`, `survey`, `lecture_note`, `website`,
  `internal_note`, or `other`
- `title`
- `authors`
- `year`
- `doi`
- `arxiv`
- `url`
- `theorem_number`
- `page`
- `notes`

`FormalizationRef` fields are:

- `id`
- `system`: currently `lean4`
- `library`
- `library_ref`
- `import_path`
- `symbol`
- `declaration_kind`: `definition`, `theorem`, `lemma`, `instance`,
  `structure`, or `other`
- `status`: `planned`, `linked`, `checked`, `broken`, or `deprecated`
- `check_mode`: `external_library_ref` or `local_file`
- `expected_type`: optional, defaults to an empty string
- `notes`: optional, defaults to an empty string

Formalization reference IDs use the same dot-separated lowercase slug format
as artifact IDs. `library_ref` is a formal library manifest ID such as
`cslib-main` or `mathlib-main`; it is not a Lean module path. `library`,
`import_path`, and `symbol` are required non-empty strings.

`FormalLibrary` fields are:

- `id`: manifest library ID, matching the `library_ref` syntax.
- `name`
- `system`: currently `lean4`
- `git`
- `commit`
- `lean_version`
- `lake_manifest`
- `notes`

`FormalLibraryManifest` fields are:

- `schema_version`: currently `1`
- `libraries: list[FormalLibrary]`

`FormalLibraryManifest.library_ids -> tuple[str, ...]` returns manifest IDs in
manifest order. `FormalLibraryManifest.get_library(library_ref)` returns a
library entry or `None`. `FormalLibraryManifest.require_library_ref(library_ref)`
returns the entry or raises `FormalLibraryManifestError`. Unknown
`library_ref` errors include the requested ID and the manifest's available
library IDs, preserving the same validation semantics while making operator
diagnostics clearer.

`AlignmentReview` fields are:

- `status`: `none`, `requested`, `human_reviewed`, or `rejected`
- `reviewer`
- `reviewed_at`
- `convention_notes`
- `limitations`

Alignment statuses `human_reviewed` and `rejected` require a non-empty
`reviewer`. `reviewed_at`, when present, must include timezone information.

`VerificationPolicy` fields are:

- `level`: `source_reviewed`, `source_reviewed_with_formal_link`,
  `machine_checked`, or `lean_required`
- `require_formal_link`
- `require_lean_check`
- `require_alignment_review`

`source_reviewed_with_formal_link` requires `require_formal_link: true`.
`lean_required` requires both `require_formal_link: true` and
`require_lean_check: true`.

Formalization links and formal library manifests are metadata references to
external declarations and library pins. They are not copied Lean proof bodies
and are not stored in `evidence`. G10 checks consistency between
`formalizations`, `alignment`, `verification_policy`, local formal library
manifests, and normalized Lean verifier results when policy requires a Lean
check. It does not execute Lean, inspect CSLib/mathlib libraries, resolve
manifest checkouts, prove informal/formal alignment, or change accepted
promotion semantics beyond ordinary gatekeeper blocking behavior.

#### Memory/Retrieval Models

- `cosheaf.memory.ArtifactCard`: Pydantic v2 model for compact retrieval cards
  derived from existing repository metadata.
- `cosheaf.memory.ScoreBreakdown`: Pydantic v2 model for inspectable retrieval
  score components.
- `cosheaf.memory.RetrievalRequest`: Pydantic v2 model for bounded local
  retrieval requests.
- `cosheaf.memory.RetrievedArtifactCard`: Pydantic v2 model pairing an
  `ArtifactCard` with a `ScoreBreakdown` and relevance reasons.
- `cosheaf.memory.FullArtifactPull`: Pydantic v2 audit entry for explicit full
  artifact pulls beyond card metadata.
- `cosheaf.memory.RetrievalExclusion`: Pydantic v2 audit entry for records
  excluded by scope, status, or policy.
- `cosheaf.memory.RetrievalAudit`: Pydantic v2 model for retrieval filters,
  exclusions, and warnings.
- `cosheaf.memory.RetrievalResult`: Pydantic v2 model for ordered retrieved
  cards, full-artifact pull audit entries, and retrieval audit metadata.
- `cosheaf.memory.RetrievalScoreWeights`: frozen dataclass for configurable
  retrieval formula weights. Defaults are `0.50` retrieval hybrid, `0.20`
  personalized PageRank, `0.15` global PageRank, `0.10` quality prior, and
  `0.05` freshness. Penalty is always subtracted after weighted components.
- `cosheaf.memory.MemoryGraphNode`: Pydantic v2 model for one deterministic
  memory graph node.
- `cosheaf.memory.MemoryGraphEdge`: Pydantic v2 model for one weighted memory
  graph edge.
- `cosheaf.memory.MemoryGraphSnapshot`: Pydantic v2 model for the rebuildable
  `.cosheaf/memory/graph_snapshot.json` sidecar.
- `cosheaf.memory.PageRankRow`: Pydantic v2 model for one global PageRank row.
- `cosheaf.memory.PageRankResult`: Pydantic v2 model for deterministic
  weighted global PageRank output.
- `cosheaf.memory.MemoryCardError`: expected error for card-builder failures,
  such as an unknown issue ID or a repository load failure.
- `cosheaf.memory.MemorySearchError`: expected error for memory-search
  failures, such as invalid query text or card-builder errors.
- `cosheaf.memory.MemoryGraphError`: expected error for memory graph build,
  sidecar read, or PageRank failures.

#### Evaluation Models

- `cosheaf.evals.RetrievalEvalCase`: Pydantic v2 model for one deterministic
  retrieval regression case with `query`, optional `issue_id`,
  `expected_relevant_artifacts`, `forbidden_artifacts`, and `allowed_scope`.
- `cosheaf.evals.RetrievalEvalSuite`: Pydantic v2 model for a YAML suite of
  retrieval eval cases.
- `cosheaf.evals.RetrievalEvalMetrics`: frozen dataclass with `hit@k`,
  `forbidden_hit_count`, `accepted_priority_score`, and
  `private_leakage_count` output.
- `cosheaf.evals.RetrievalEvalCaseResult`: frozen dataclass for one scored
  case, including returned, forbidden, private, and missing expected artifact
  IDs.
- `cosheaf.evals.RetrievalEvalReport`: frozen dataclass for aggregate suite
  output with deterministic `to_dict()` and `to_json()` helpers.
- `cosheaf.evals.RetrievalEvalError`: expected error for retrieval eval loading
  or execution failures.
- `cosheaf.evals.DEFAULT_RETRIEVAL_EVAL_CASES`: default case path
  `evals/retrieval/cases.yaml`.
- `cosheaf.evals.agent_workflow.AgentWorkflowEvalKind`: enum for
  `cli_agent_workflow`, `provider_worker_fake`, `context_privacy`,
  `bundle_validity`, `gate_regression`, and `optional_mcp_readonly` cases.
- `cosheaf.evals.agent_workflow.AgentWorkflowEvalSurface`: enum for `cli`,
  `provider`, and `optional_mcp` surface labels.
- `cosheaf.evals.agent_workflow.AgentWorkflowEvalCase`: Pydantic v2 model for
  one deterministic CLI-agent/provider workflow eval case with `kind`,
  `surface`, command, exit-code, JSON, artifact-hit, forbidden-substring,
  expected-error, and provider-redaction expectations.
- `cosheaf.evals.agent_workflow.AgentWorkflowEvalSuite`: Pydantic v2 model for
  a YAML suite of agent workflow eval cases.
- `cosheaf.evals.agent_workflow.AgentWorkflowEvalMetrics`: frozen dataclass
  with `command_success_rate`, `json_parse_success_rate`,
  `required_artifact_hit`, `private_leakage_count`,
  `accepted_write_rejection_count`, `malformed_bundle_rejection_count`, and
  `provider_redaction_pass_count` output.
- `cosheaf.evals.agent_workflow.AgentWorkflowEvalCaseResult`: frozen dataclass
  for one executed workflow eval case, including surface, command, exit code,
  JSON parse status, policy rejection booleans, redaction status, and failures.
- `cosheaf.evals.agent_workflow.AgentWorkflowEvalReport`: frozen dataclass for
  aggregate suite output with deterministic `to_dict()` and `to_json()`
  helpers plus `surface_counts`.
- `cosheaf.evals.agent_workflow.AgentWorkflowEvalError`: expected error for
  agent workflow eval loading or execution failures.
- `cosheaf.evals.agent_workflow.DEFAULT_AGENT_WORKFLOW_EVAL_CASES`: default
  case path `evals/agent_workflow/cases.yaml`.
- `cosheaf.evals.agent_workflow.load_agent_workflow_eval_suite(path)`:
  loads an agent workflow eval YAML suite.
- `cosheaf.evals.agent_workflow.resolve_agent_workflow_eval_case_path(context, cases_path)`:
  resolves and constrains an eval case path to the repository root.
- `cosheaf.evals.agent_workflow.run_agent_workflow_eval_suite(context, suite)`:
  invokes existing CLI commands through `CliRunner` and returns an
  `AgentWorkflowEvalReport`.
- `cosheaf.evals.agent_workflow.run_agent_workflow_eval_case(context, case)`:
  runs and scores one eval case.
- `cosheaf.evals.provider_workflow.ProviderWorkflowEvalKind`: enum for
  `fake_provider_success`, `mocked_openai_success`, `missing_config`,
  `missing_consent`, `private_context_denied`, `malformed_output`,
  `policy_violating_verifier_output`, `rate_limit`, `timeout`, and
  `cancellation` cases.
- `cosheaf.evals.provider_workflow.ProviderWorkflowEvalCase`: Pydantic v2
  model for one deterministic provider workflow eval case with expected error
  code, policy-denial, validation-rejection, malformed-output,
  context-scope, bundle-validity, and forbidden-substring expectations.
- `cosheaf.evals.provider_workflow.ProviderWorkflowEvalSuite`: Pydantic v2
  model for a YAML suite of provider workflow eval cases.
- `cosheaf.evals.provider_workflow.ProviderWorkflowEvalMetrics`: frozen
  dataclass with `policy_denial_accuracy`,
  `validation_rejection_accuracy`, `secret_leak_count`,
  `malformed_output_reject_count`, `bundle_validity_rate`, and
  `context_scope_violation_count` output.
- `cosheaf.evals.provider_workflow.ProviderWorkflowEvalCaseResult`: frozen
  dataclass for one executed provider workflow eval case, including provider,
  role, status, error code, bundle validity, accepted-write flag, matched
  expectations, provider-log secret findings, runtime paths, and failures.
- `cosheaf.evals.provider_workflow.ProviderWorkflowEvalReport`: frozen
  dataclass for aggregate suite output with deterministic `to_dict()` and
  `to_json()` helpers plus runtime paths.
- `cosheaf.evals.provider_workflow.ProviderWorkflowEvalError`: expected error
  for provider workflow eval loading or execution failures.
- `cosheaf.evals.provider_workflow.DEFAULT_PROVIDER_WORKFLOW_EVAL_CASES`:
  default case path `evals/provider_workflow/cases.yaml`.
- `cosheaf.evals.provider_workflow.load_provider_workflow_eval_suite(path)`:
  loads a provider workflow eval YAML suite.
- `cosheaf.evals.provider_workflow.resolve_provider_workflow_eval_case_path(context, cases_path)`:
  resolves and constrains an eval case path to the repository root.
- `cosheaf.evals.provider_workflow.run_provider_workflow_eval_suite(context, suite)`:
  invokes existing provider gateway, hosted-worker, and context-policy service
  boundaries with fake or mocked transports and returns a
  `ProviderWorkflowEvalReport`.
- `cosheaf.evals.provider_workflow.run_provider_workflow_eval_case(context, case)`:
  runs and scores one provider workflow eval case.
- `cosheaf.evals.failure_counterexample.FailureCounterexampleEvalKind`: enum
  for `reasoner_uncertainty`, `counterexample_candidate`,
  `verifier_rejects_invalid_proof`, `reducer_preserves_failure`, and
  `accepted_write_boundary` cases.
- `cosheaf.evals.failure_counterexample.FailureCounterexampleEvalCase`:
  Pydantic v2 model for one deterministic failure/counterexample eval case
  with failure-preservation, uncertainty, candidate-counterexample,
  verifier-request, reducer-rejection, and forbidden-output-path expectations.
- `cosheaf.evals.failure_counterexample.FailureCounterexampleEvalSuite`:
  Pydantic v2 model for a YAML suite of failure/counterexample eval cases.
- `cosheaf.evals.failure_counterexample.FailureCounterexampleEvalMetrics`:
  frozen dataclass with `failure_preservation_rate`,
  `uncertainty_field_presence`, `counterexample_candidate_flag_accuracy`,
  `verifier_request_presence`, and `accepted_write_violation_count` output.
- `cosheaf.evals.failure_counterexample.FailureCounterexampleEvalCaseResult`:
  frozen dataclass for one executed failure/counterexample eval case,
  including worker role, reducer status, output paths, reducer warnings,
  preserved-field flags, accepted-write flag, runtime paths, and failures.
- `cosheaf.evals.failure_counterexample.FailureCounterexampleEvalReport`:
  frozen dataclass for aggregate suite output with deterministic `to_dict()`
  and `to_json()` helpers plus runtime paths.
- `cosheaf.evals.failure_counterexample.FailureCounterexampleEvalError`:
  expected error for failure/counterexample eval loading or execution
  failures.
- `cosheaf.evals.failure_counterexample.DEFAULT_FAILURE_COUNTEREXAMPLE_EVAL_CASES`:
  default case path `evals/failure_counterexample/cases.yaml`.
- `cosheaf.evals.failure_counterexample.load_failure_counterexample_eval_suite(path)`:
  loads a failure/counterexample eval YAML suite.
- `cosheaf.evals.failure_counterexample.resolve_failure_counterexample_eval_case_path(context, cases_path)`:
  resolves and constrains an eval case path to the repository root.
- `cosheaf.evals.failure_counterexample.run_failure_counterexample_eval_suite(context, suite)`:
  writes deterministic WorkerBundle v2 fixtures under `.cosheaf/evals/`,
  invokes the existing reducer boundary, and returns a
  `FailureCounterexampleEvalReport`.
- `cosheaf.evals.failure_counterexample.run_failure_counterexample_eval_case(context, case)`:
  runs and scores one failure/counterexample eval case.
- `cosheaf.evals.artifact_failure_memory.ArtifactFailureMemoryEvalKind`: enum
  for `failure_retrieval`, `repeat_failed_direction`,
  `public_scope_boundary`, `authority_boundary`, and
  `candidate_counterexample_boundary` cases.
- `cosheaf.evals.artifact_failure_memory.ArtifactFailureMemoryEvalCase`:
  Pydantic v2 model for one deterministic artifact failure-memory eval case
  with query, public-only, failure-retrieval, repeat-direction, scope,
  authority, and candidate-counterexample expectations.
- `cosheaf.evals.artifact_failure_memory.ArtifactFailureMemoryEvalSuite`:
  Pydantic v2 model for a YAML suite of artifact failure-memory eval cases.
- `cosheaf.evals.artifact_failure_memory.ArtifactFailureMemoryEvalMetrics`:
  frozen dataclass with `failure_retrieval_recall`,
  `repeat_failed_direction_rate`, `failure_scope_leak_count`,
  `failure_authority_violation_count`, and
  `candidate_counterexample_mislabel_count` output.
- `cosheaf.evals.artifact_failure_memory.ArtifactFailureMemoryEvalCaseResult`:
  frozen dataclass for one executed artifact failure-memory eval case,
  including retrieved artifact IDs, retrieved failure directions, repeated
  failed-direction detection, scope leak, authority violation,
  candidate-counterexample mislabel status, warnings, runtime paths, and
  failures.
- `cosheaf.evals.artifact_failure_memory.ArtifactFailureMemoryEvalReport`:
  frozen dataclass for aggregate suite output with deterministic `to_dict()`
  and `to_json()` helpers plus runtime paths.
- `cosheaf.evals.artifact_failure_memory.ArtifactFailureMemoryEvalError`:
  expected error for artifact failure-memory eval loading or execution
  failures.
- `cosheaf.evals.artifact_failure_memory.DEFAULT_ARTIFACT_FAILURE_MEMORY_EVAL_CASES`:
  default case path `evals/artifact_failure_memory/cases.yaml`.
- `cosheaf.evals.artifact_failure_memory.load_artifact_failure_memory_eval_suite(path)`:
  loads an artifact failure-memory eval YAML suite.
- `cosheaf.evals.artifact_failure_memory.resolve_artifact_failure_memory_eval_case_path(context, cases_path)`:
  resolves and constrains an eval case path to the repository root.
- `cosheaf.evals.artifact_failure_memory.run_artifact_failure_memory_eval_suite(context, suite)`:
  writes deterministic workspace fixtures under
  `.cosheaf/evals/artifact_failure_memory/`, invokes the existing artifact-card
  search surface, and returns an `ArtifactFailureMemoryEvalReport`.
- `cosheaf.evals.artifact_failure_memory.run_artifact_failure_memory_eval_case(context, case)`:
  runs and scores one artifact failure-memory eval case.
- `cosheaf.evals.verifier_evidence.VerifierEvidenceEvalKind`: enum for
  `pass_evidence_policy_allowed`, `failed_evidence_blocks_readiness`,
  `skipped_checker_required`, `counterexample_remains_candidate`, and
  `lean_check_symbol_only` cases.
- `cosheaf.evals.verifier_evidence.VerifierEvidenceEvalCase`: Pydantic v2
  model for one deterministic verifier evidence eval case with readiness,
  expected verifier result, reason-code, skipped-not-pass,
  candidate-counterexample, Lean symbol-only, and semantic-alignment
  expectations.
- `cosheaf.evals.verifier_evidence.VerifierEvidenceEvalSuite`: Pydantic v2
  model for a YAML suite of verifier evidence eval cases.
- `cosheaf.evals.verifier_evidence.VerifierEvidenceEvalMetrics`: frozen
  dataclass with `readiness_boundary_accuracy`,
  `failed_evidence_block_count`, `skipped_not_pass_count`,
  `candidate_counterexample_review_only_count`,
  `lean_alignment_claim_count`, and `accepted_write_violation_count` output.
- `cosheaf.evals.verifier_evidence.VerifierEvidenceEvalCaseResult`: frozen
  dataclass for one executed verifier evidence eval case, including readiness,
  evidence result, verifier kind, reason codes, skipped/pass boundary,
  candidate-counterexample flags, Lean symbol-only flag, semantic-alignment
  claim flag, accepted-write flag, and failures.
- `cosheaf.evals.verifier_evidence.VerifierEvidenceEvalReport`: frozen
  dataclass for aggregate suite output with deterministic `to_dict()` and
  `to_json()` helpers.
- `cosheaf.evals.verifier_evidence.VerifierEvidenceEvalError`: expected error
  for verifier evidence eval loading or execution failures.
- `cosheaf.evals.verifier_evidence.DEFAULT_VERIFIER_EVIDENCE_EVAL_CASES`:
  default case path `evals/verifier_evidence/cases.yaml`.
- `cosheaf.evals.verifier_evidence.load_verifier_evidence_eval_suite(path)`:
  loads a verifier evidence eval YAML suite.
- `cosheaf.evals.verifier_evidence.resolve_verifier_evidence_eval_case_path(context, cases_path)`:
  resolves and constrains an eval case path to the repository root.
- `cosheaf.evals.verifier_evidence.run_verifier_evidence_eval_suite(context, suite)`:
  runs deterministic fake verifier evidence, typed counterexample candidate,
  and Lean `#check` boundary fixtures and returns a
  `VerifierEvidenceEvalReport`.
- `cosheaf.evals.verifier_evidence.run_verifier_evidence_eval_case(context, case)`:
  runs and scores one verifier evidence eval case.

The agent workflow, provider workflow, failure/counterexample, artifact
failure-memory, and verifier evidence eval harnesses are intentionally direct
submodule APIs in this phase. They are not exported from
`cosheaf.evals.__init__`, and no `cosheaf eval agent-workflow`,
`cosheaf eval provider-workflow`, `cosheaf eval failure-counterexample`,
`cosheaf eval artifact-failure-memory`, or `cosheaf eval verifier-evidence`
CLI command is added.

All memory models are strict (`extra="forbid"`), frozen, preserve enum values as
enum instances in Python, and expose:

- `to_dict() -> dict[str, Any]`: deterministic `model_dump(mode="json")`.
- `to_json() -> str`: deterministic indented JSON with a trailing newline.

`ArtifactCard` fields are:

- `id`
- `path`
- `root_scope`
- `type`
- `status`
- `title`
- `summary`
- `domain`
- `tags`
- `depends_on`
- `sources`
- `review_state`
- `verifier_state`
- `formalization_state`
- `failure_count`
- `recent_failure_directions`
- `trust_score`
- `retrieval_score`
- `why_relevant`
- `risk_flags`
- `can_pull_full`

`RetrievalRequest` fields are:

- `schema_version`
- `query`
- `issue_id`
- `seed_artifacts`
- `pinned_artifacts`
- `allowed_scopes`
- `allowed_statuses`
- `include_refuted`
- `include_obsolete`
- `max_cards`
- `max_full_artifacts`
- `role`

`RetrievalResult` fields are:

- `schema_version`
- `request_id`
- `generated_at`
- `index_fingerprint`
- `cards`
- `full_artifact_pulls`
- `audit`

`MemoryGraphSnapshot` fields are:

- `schema_version`
- `generated_at`
- `graph_fingerprint`
- `nodes`
- `edges`
- `warnings`

`MemoryGraphNode` fields are:

- `node_id`
- `kind`
- `record_id`
- `path`
- `title`
- `status`
- `metadata`

`MemoryGraphEdge` fields are:

- `source`
- `target`
- `kind`
- `weight`
- `evidence`

`PageRankResult` fields are:

- `schema_version`
- `algorithm`
- `damping`
- `iterations`
- `graph_fingerprint`
- `rows`
- `warnings`

The memory package also exposes:

- `cosheaf.memory.build_artifact_cards(context: RepoContext, *, issue_id: str | None = None, status: ArtifactCardStatus | str | None = None, allowed_scopes: Iterable[MemoryRootScope | str] = DEFAULT_CARD_SCOPES) -> tuple[ArtifactCard, ...]`:
  builds deterministic cards from loaded repository YAML metadata.
- `cosheaf.memory.artifact_card_from_loaded_record(loaded: LoadedRecord) -> ArtifactCard`:
  builds one card from a loaded lifecycle artifact record.
- `cosheaf.memory.DEFAULT_CARD_SCOPES`: default public-output scope set,
  containing `public`, `workspace`, and `framework`, excluding `private`.
- `cosheaf.memory.search_artifact_cards(context: RepoContext, *, query: str, issue_id: str | None = None, status: ArtifactCardStatus | str | None = None, max_cards: int = 20, allowed_scopes: tuple[MemoryRootScope, ...] | None = None, seed_artifacts: tuple[str, ...] = (), pinned_artifacts: tuple[str, ...] = (), include_refuted: bool = False, include_obsolete: bool = False, role: RetrievalRole | str = RetrievalRole.LIBRARIAN, max_full_artifacts: int = 0, score_weights: RetrievalScoreWeights = RetrievalScoreWeights()) -> RetrievalResult`:
  searches deterministic artifact cards with SQLite FTS5/BM25 when available,
  deterministic lexical fallback otherwise, and in-memory Personalized
  PageRank/global PageRank/freshness/penalty scoring. It records retrieval
  role and full-artifact budget metadata in the request but still returns
  cards by default and does not write memory sidecars.
- `cosheaf.memory.build_memory_graph(context: RepoContext, *, persist: bool = False) -> MemoryGraphSnapshot`:
  builds the deterministic memory graph from repository YAML plus optional
  local sidecar signals. With `persist=True`, it writes the rebuildable
  `.cosheaf/memory/graph_snapshot.json` sidecar.
- `cosheaf.memory.load_memory_graph_snapshot(context: RepoContext) -> MemoryGraphSnapshot`:
  loads the existing graph sidecar and fails clearly if users need to run
  `cosheaf memory graph build` first.
- `cosheaf.memory.compute_global_pagerank(graph: MemoryGraphSnapshot, *, damping: float = 0.85, max_iterations: int = 50, tolerance: float = 1e-12) -> PageRankResult`:
  computes deterministic weighted global PageRank rows from the memory graph.
- `cosheaf.memory.write_memory_graph_snapshot(context: RepoContext, snapshot: MemoryGraphSnapshot) -> Path`:
  writes the deterministic rebuildable graph sidecar.
- `cosheaf.memory.MEMORY_GRAPH_SIDECAR`: repository-relative graph sidecar path,
  `.cosheaf/memory/graph_snapshot.json`.

The card builder and search read existing YAML records through the storage
loader. Search uses an in-memory SQLite FTS5 table and in-memory memory graph
ranking when available and does not write `.cosheaf/memory/` sidecars. Memory
graph build writes only the rebuildable graph snapshot sidecar, and PageRank
reads that sidecar without implicitly rebuilding it. The memory package does
not add embeddings, hosted LLM workers, accepted-promotion shortcuts, formal
checking, or artifact schema changes. Context-pack v2 consumes memory search
cards while preserving bounded output and issue-local relevance filters. By
default, configured private KB roots are excluded from `cosheaf memory cards`
and `cosheaf memory search`; callers must not treat memory output, graph
scores, or context-pack scores as accepted knowledge or human review.

#### Core Enums

- `cosheaf.core.status.ArtifactType`: artifact type enum.
- `cosheaf.core.status.ArtifactStatus`: artifact lifecycle status enum.
- `cosheaf.core.task.WorkerType`: protocol worker type enum, re-exported through `cosheaf.agent.task.WorkerType`.
- `cosheaf.core.task.TaskStatus`: task lifecycle status enum, re-exported through `cosheaf.agent.task.TaskStatus`.
- `cosheaf.memory.MemoryRootScope`: memory root scope enum with values
  `public`, `private`, `workspace`, and `framework`.
- `cosheaf.memory.ArtifactCardType`: artifact-card type enum with values
  `definition`, `theorem`, `claim`, `conjecture`, `proof`, `proof_attempt`,
  `construction`, `algorithm`, `reduction`, `counterexample`, `experiment`,
  `review`, `verifier`, `issue`, and `source_note`.
- `cosheaf.memory.ArtifactCardStatus`: artifact-card lifecycle/trust status enum
  with values `raw`, `draft`, `locally_tested`, `adversarially_tested`,
  `machine_checked`, `human_reviewed`, `accepted`, `refuted`, `obsolete`, and
  `superseded`.
- `cosheaf.memory.RetrievalRole`: retrieval caller role enum with values
  `librarian`, `orchestrator`, `reasoner`, `verifier`, `formalizer`,
  `literature_scout`, `counterexampleer`, and `construction_searcher`.

#### Core Helpers

- `cosheaf.core.ids.validate_artifact_id(value: str) -> str`
  - IDs are dot-separated. The first segment must be a lowercase slug; later
    segments may be lowercase slugs or numeric version/index segments such as
    `0001`.
- `cosheaf.core.artifact.is_external_dependency_ref(value: str) -> bool`
- `cosheaf.core.artifact.validate_dependency_ref(value: str) -> str`
  - Dependency references are either local artifact IDs or explicit external
    references beginning with `external:`.
- `cosheaf.core.paths.normalize_repo_path(path: str | Path) -> str`
- `cosheaf.core.paths.repo_relative_path(repo_root: Path, path: Path) -> Path`
- `cosheaf.core.paths.repo_relative_posix(repo_root: Path, path: Path) -> str`
- `cosheaf.core.paths.is_yaml_path(path: Path) -> bool`
- `cosheaf.core.paths.ARTIFACT_TYPE_DIRECTORIES`: mapping from lifecycle artifact type enums to knowledge-base directory names.
- `cosheaf.core.paths.artifact_type_directory(artifact_type: ArtifactType) -> str`
- `cosheaf.core.paths.lifecycle_artifact_path(artifact_type: ArtifactType, status: ArtifactStatus, artifact_id: str) -> Path`
- `cosheaf.core.status.is_terminal_status(status: ArtifactStatus) -> bool`
- `cosheaf.core.status.is_preaccepted_status(status: ArtifactStatus) -> bool`
- `cosheaf.core.status.is_accepted_status(status: ArtifactStatus) -> bool`
- `cosheaf.core.status.expected_status_for_path(path: str) -> frozenset[ArtifactStatus]`
- `cosheaf.core.task.create_task_id(issue_id: str, worker_type: WorkerType | str) -> str`

These helpers are pure validation, path-formatting, status-classification, or deterministic ID/reference helpers. They do not scan the repository, use SQLite, or run gatekeeper behavior.

#### Storage Models and Context

- `cosheaf.storage.repo.RepoContext`: immutable filesystem repository context
  with `repo_root` and loaded `workspace_config`.
- `cosheaf.storage.repo.RepoContext.discovery_roots() -> tuple[str, ...]`:
  returns active repository-relative YAML discovery roots. The roots are
  configured KB root paths plus `issues` and `examples`; in legacy mode this is
  `kb`, `issues`, and `examples`.
- `cosheaf.storage.repo.RepoContext.kb_root_for_path(path: str | Path) -> KbRootConfig | None`:
  returns the configured KB root containing a repository-relative path.
- `cosheaf.storage.repo.RepoContext.kb_relative_path(path: str | Path) -> Path | None`:
  returns a path relative to its configured KB root when applicable.
- `cosheaf.storage.loader.IssueRecord`: Pydantic v2 model for issue YAML records loaded by storage.
- `cosheaf.storage.loader.ReviewRecord`: Pydantic v2 model for review YAML records loaded by storage.
- `cosheaf.storage.loader.LoadedRecord`: loaded record wrapper with repository-relative `source_path`, typed `record`, and optional KB root metadata (`kb_root_name`, `kb_root_path`, `kb_root_readonly`, `kb_relative_path`).

#### Storage Loader

- `cosheaf.storage.loader.discover_yaml_paths(context: RepoContext) -> list[Path]`
- `cosheaf.storage.loader.load_yaml_file(context: RepoContext, path: Path) -> LoadedRecord`
- `cosheaf.storage.loader.load_artifacts(context: RepoContext) -> list[LoadedRecord]`

The loader discovers `.yaml` and `.yml` files under the active workspace KB
roots plus `issues/` and `examples/`, parses YAML without swallowing parse
errors, and returns loaded records in deterministic order by source path then
ID. Without `cosheaf.toml`, the active KB root is the legacy `kb/` path. Loaded
models currently include `BaseArtifact`, `IssueRecord`, `ReviewRecord`, and
`AgentTask` example records. Runtime task records under `.cosheaf/tasks/` are
not part of repository discovery.

#### Storage Writer

- `cosheaf.storage.writer.dump_yaml_deterministic(data: Any) -> str`
- `cosheaf.storage.writer.write_yaml_deterministic(path: Path, data: Any) -> None`

The writer preserves mapping insertion order by disabling YAML key sorting.

#### Storage Errors

- `cosheaf.storage.loader.LoadError`
- `cosheaf.storage.loader.UnsupportedArtifactTypeError`

The storage loader and writer do not use SQLite and do not implement gatekeeper
behavior.

#### Storage Index

- `cosheaf.storage.index.IndexRebuildResult`: paths and counts produced by an index rebuild.
- `cosheaf.storage.index.rebuild_index(context: RepoContext) -> IndexRebuildResult`

The index rebuild writes `.cosheaf/index.sqlite` and
`.cosheaf/artifact_manifest.json` from scratch. The SQLite index stores artifact
ID, type, status, path, title, domain, source KB root, dependency rows,
formalization rows, and artifact formal-policy rows. The manifest is ordered
deterministically by artifact ID and dependency tuple.

SQLite tables:

- `artifacts(id, type, status, path, title, domain, kb_root)`
- `dependencies(source_id, target_id)`
- `formalizations(artifact_id, formalization_id, system, library, library_ref,
  import_path, symbol, declaration_kind, status, check_mode, expected_type,
  notes)`
- `artifact_formal_policy(artifact_id, alignment_status, alignment_reviewer,
  verification_level, require_formal_link, require_lean_check,
  require_alignment_review)`

`formalizations` has a primary key on `(artifact_id, formalization_id)` and
indexes on `symbol`, `library`, `status`, and `import_path`. The manifest
includes per-artifact `formalizations`, `alignment_status`, and
`verification_policy` fields. These are metadata-only generated surfaces; they
do not run Lean or check external library symbol existence.

#### Storage Query

- `cosheaf.storage.query.ArtifactQueryRow`: immutable row with `id`, `type`,
  `status`, `path`, `title`, `domain`, and `kb_root`.
- `cosheaf.storage.query.DependencyQueryRow`: immutable dependency edge row
  with `source_id` and `target_id`.
- `cosheaf.storage.query.FormalizationQueryRow`: immutable formalization row
  with `artifact_id`, `formalization_id`, `system`, `library`, `library_ref`,
  `import_path`, `symbol`, `declaration_kind`, `status`, `check_mode`,
  `expected_type`, and `notes`.
- `cosheaf.storage.query.FormalPolicyQueryRow`: immutable formal policy row
  with `artifact_id`, `alignment_status`, `alignment_reviewer`,
  `verification_level`, `require_formal_link`, `require_lean_check`, and
  `require_alignment_review`.
- `cosheaf.storage.query.IndexQueryError`: expected query-layer error.
- `cosheaf.storage.query.ArtifactIndexQuery(sqlite_path: str | Path)`: read-only
  SQLite query facade over `.cosheaf/index.sqlite`.
- `cosheaf.storage.query.ArtifactIndexQuery.from_context(context: RepoContext) -> ArtifactIndexQuery`
- `cosheaf.storage.query.ArtifactIndexQuery.from_repo_root(repo_root: str | Path) -> ArtifactIndexQuery`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts() -> tuple[ArtifactQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.get_artifact(artifact_id: str) -> ArtifactQueryRow | None`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts_by_status(status: ArtifactStatus | str) -> tuple[ArtifactQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts_by_type(artifact_type: ArtifactType | str) -> tuple[ArtifactQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts_by_domain(domain: str) -> tuple[ArtifactQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_dependencies(artifact_id: str) -> tuple[DependencyQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_reverse_dependencies(artifact_id: str) -> tuple[DependencyQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_formalizations() -> tuple[FormalizationQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_formalizations_for_artifact(artifact_id: str) -> tuple[FormalizationQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_formalizations_by_library(library: str) -> tuple[FormalizationQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_formalizations_by_symbol(symbol: str) -> tuple[FormalizationQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_formalizations_by_status(status: str) -> tuple[FormalizationQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_formalizations_by_import(import_path: str) -> tuple[FormalizationQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.get_formal_policy(artifact_id: str) -> FormalPolicyQueryRow | None`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts_requiring_formal_link() -> tuple[FormalPolicyQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts_requiring_lean_check() -> tuple[FormalPolicyQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts_requiring_alignment_review() -> tuple[FormalPolicyQueryRow, ...]`

The query API reads the deterministic SQLite output produced by
`rebuild_index`; it does not parse YAML, rebuild indexes implicitly, or modify
repository files. Result ordering is deterministic. `ArtifactQueryRow.kb_root`
contains the indexed source KB root, such as `default`, `public`, or `private`,
and is empty when a row was indexed outside a KB root. Formalization query
methods are metadata-only and do not execute Lean, fetch external libraries, or
check CSLib/mathlib symbol existence.

#### Dependency Graph

- `cosheaf.graph.claim_graph.GraphNode`: deterministic artifact graph node.
- `cosheaf.graph.claim_graph.GraphEdge`: directed dependency edge from artifact to dependency.
- `cosheaf.graph.claim_graph.GraphIssue`: deterministic graph issue row.
- `cosheaf.graph.claim_graph.DependencyGraph`: graph nodes, edges, and detected issues.
- `cosheaf.graph.claim_graph.build_dependency_graph(records: Iterable[LoadedRecord]) -> DependencyGraph`

Graph edge direction is artifact-to-dependency, for example
`claim.example.a -> claim.example.b` means artifact `a` depends on artifact `b`.
The graph reports missing dependencies, directed cycles, and accepted artifacts
depending on draft or otherwise pre-accepted artifacts.

#### Validation Gates

- `cosheaf.gates.schema_gate.ValidationFailure`: deterministic validation failure row.
- `cosheaf.gates.schema_gate.SchemaGateResult`: schema/model loading result.
- `cosheaf.gates.schema_gate.load_schema_valid_records(context: RepoContext) -> SchemaGateResult`
- `cosheaf.gates.schema_gate.load_schema_valid_record(context: RepoContext, path: Path) -> SchemaGateResult`
- `cosheaf.gates.schema_gate.sort_failures(failures: Iterable[ValidationFailure]) -> tuple[ValidationFailure, ...]`
- `cosheaf.gates.status_gate.validate_status_paths(records: tuple[LoadedRecord, ...]) -> list[ValidationFailure]`
- `cosheaf.gates.status_gate.validate_evidence_paths(context: RepoContext, records: tuple[LoadedRecord, ...]) -> list[ValidationFailure]`
- `cosheaf.gates.dependency_gate.validate_id_uniqueness(records: tuple[LoadedRecord, ...]) -> list[ValidationFailure]`
- `cosheaf.gates.dependency_gate.validate_dependencies(records: tuple[LoadedRecord, ...]) -> list[ValidationFailure]`
- `cosheaf.gates.reproducibility_gate.ReproducibilityCheck`: one executable evidence metadata check row.
- `cosheaf.gates.reproducibility_gate.ReproducibilityMetadataResult`: aggregate reproducibility metadata gate result.
- `cosheaf.gates.reproducibility_gate.validate_reproducibility_metadata(records: tuple[LoadedRecord, ...], verification_results: tuple[VerificationResult, ...]) -> ReproducibilityMetadataResult`
- `cosheaf.gates.source_metadata_gate.SourceMetadataCheck`: one accepted public artifact source metadata check row.
- `cosheaf.gates.source_metadata_gate.SourceMetadataResult`: aggregate source metadata policy gate result.
- `cosheaf.gates.source_metadata_gate.missing_required_source_metadata(artifact: BaseArtifact) -> tuple[str, ...]`: returns missing required source metadata fields for an artifact.
- `cosheaf.gates.source_metadata_gate.validate_source_metadata_policy(context: RepoContext, records: tuple[LoadedRecord, ...]) -> SourceMetadataResult`
- `cosheaf.gates.formal_link_gate.FormalLinkCheck`: one static formal-link metadata check row.
- `cosheaf.gates.formal_link_gate.FormalLinkResult`: aggregate formal-link metadata policy gate result.
- `cosheaf.gates.formal_link_gate.validate_formal_link_policy(records: tuple[LoadedRecord, ...], *, context: RepoContext | None = None, verification_results: tuple[VerificationResult, ...] = ()) -> FormalLinkResult`
- `cosheaf.gates.gatekeeper.ValidationReport`: validation report with loaded records and failures.
- `cosheaf.gates.gatekeeper.validate_repository(context: RepoContext) -> ValidationReport`
- `cosheaf.gates.gatekeeper.validate_artifact_file(context: RepoContext, path: Path) -> ValidationReport`
- `cosheaf.gates.gatekeeper.GateIssue`: blocking or nonblocking gatekeeper issue row.
- `cosheaf.gates.gatekeeper.GateResult`: one gate result in a gatekeeper run, including optional machine-readable `details`.
- `cosheaf.gates.gatekeeper.GatekeeperReport`: machine-readable gatekeeper report.
- `cosheaf.gates.gatekeeper.GatekeeperRunResult`: report and written report paths.
- `cosheaf.gates.gatekeeper.GateStatus`: gate status literal type.
- `cosheaf.gates.gatekeeper.GateVerdict`: gatekeeper verdict literal type.
- `cosheaf.gates.gatekeeper.REQUIRED_PR_CHECKLIST_SECTIONS`: ordered tuple of required G8 PR checklist section names.
- `cosheaf.gates.gatekeeper.run_gatekeeper(context: RepoContext, *, persist_review: bool = False, pr_checklist_path: Path | None = None, timestamp: str | None = None) -> GatekeeperRunResult`

The dependency gate validates missing dependencies, accepted-to-draft
dependencies across KB roots, and public-artifact-to-private-artifact
dependencies.

The validation orchestrator is deterministic and filesystem-backed.
`validate_repository` does not run verifier adapters. It treats dependency
references beginning with `external:` as explicit external references rather
than missing local artifacts. `run_gatekeeper` runs G1-G5 validation gates, runs
the G6 verifier gate through the default verifier registry, runs the G7
reproducibility metadata gate over executable evidence and verifier results,
runs the G8 PR checklist gate, runs the G9 source metadata gate, and runs the
G10 formal link gate. G8 is `skipped` when
`pr_checklist_path`/`--pr-checklist` is omitted, `fail` when the explicit local
markdown checklist is missing required sections, and `pass` when all required
sections are present. G9 is `fail` when accepted artifacts in configured public
KB roots are missing complete source metadata while `accepted_requires_source`
is true, `pass` when applicable accepted public artifacts are complete, and
`not_applicable` for legacy mode, disabled source policy, or no accepted public
artifacts. G10 is `not_applicable` when no artifact has formal-link policy
metadata to check, `fail` when policy or verifier-result consistency is
violated, and `pass` when applicable formal-link metadata has no blocking
issue. G10 warnings are emitted as nonblocking issues and are not proof
failures. It does not call GitHub, require network access, run Lean, fetch
external libraries, or prove CSLib/mathlib semantic alignment. When artifacts
carry `formalizations`, G10 resolves each `library_ref` against a local formal
library manifest and blocks missing or unknown manifest references. When
`require_lean_check` is true, G10 consumes G6 verifier results and requires a
matching Lean verifier `pass`; `skipped`, `fail`, and `error` are not passes.
For `check_mode: external_library_ref`, the matching verifier is
`lean_library_ref` for the same formalization ID. Alignment review remains
separate from Lean checking. It writes JSON and Markdown reports under
`.cosheaf/reports/` by default.

G9 `GateResult.details` entries use:

- `artifact_id`
- `source_path`
- `kb_root`
- `status`
- `source_count`
- `missing_metadata`

G10 `GateResult.details` entries use:

- `artifact_id`
- `source_path`
- `artifact_status`
- `policy_level`
- `require_formal_link`
- `require_lean_check`
- `require_alignment_review`
- `formalization_count`
- `checked_formalization_count`
- `resolved_library_ref_count`
- `lean_check_pass_count`
- `alignment_status`
- `status`
- `blocking_messages`
- `warning_messages`

#### Agent Context Packs

- `cosheaf.agent.context_pack.ContextPackError`: expected context pack generation error, such as a missing issue ID.
- `cosheaf.agent.context_pack.ContextPackResult`: written context pack metadata with issue ID, task directory, and file paths.
- `cosheaf.agent.context_pack.build_context_pack(context: RepoContext, issue_id: str, *, role: RetrievalRole | str = RetrievalRole.ORCHESTRATOR, max_cards: int = 20, max_full_artifacts: int | None = None, public_only: bool = False) -> ContextPackResult`
- `cosheaf.agent.context_pack.show_context_pack(context: RepoContext, issue_id: str, *, role: RetrievalRole | str = RetrievalRole.ORCHESTRATOR, max_cards: int = 20, max_full_artifacts: int | None = None, public_only: bool = False) -> str`

Context pack generation loads repository YAML records, finds an issue by ID,
retrieves compact `ArtifactCard` rows, and filters those cards through the
issue-local relevance rules used by the previous context-pack implementation:
direct `related_artifacts`, one-hop dependency neighbors, artifact domains that
match issue text or tags, and artifact tags that match issue tags. Ranking is
deterministic. Accepted artifacts are preferred over draft artifacts within the
same relevance class. Draft artifacts are visibly labeled as `[DRAFT]`;
refuted, obsolete, and superseded artifacts are included only when relevant and
are labeled with their terminal status. Context pack files are written under
`context/TASKS/<issue-id>/`.

Generated context pack files are:

- `CONTEXT.md`
- `ACCEPTANCE.md`
- `RELEVANT_ARTIFACTS.md`
- `KNOWN_FAILURES.md`
- `FULL_ARTIFACTS.md`
- `RETRIEVAL_AUDIT.json`
- `COMMANDS.md`

`RELEVANT_ARTIFACTS.md`, `KNOWN_FAILURES.md`, and the artifact sections inside
`CONTEXT.md` use card-level lines containing artifact ID, title, status,
source path, retrieval score, root scope, optional `failure_count` plus recent
failed directions, and combined issue/retrieval reasons. Full artifact YAML is
not included in those card sections. The orchestrator default is
`max_full_artifacts = 0`; full YAML can appear only in `FULL_ARTIFACTS.md` when
the caller explicitly passes a positive `max_full_artifacts` budget.
`RETRIEVAL_AUDIT.json` records the request, role, card bound, public-only flag,
score breakdowns, failure memory card metadata, filters, exclusions, warnings,
`context_payload` (`card_count`, `full_artifact_count`, and `content_mode`),
`failure_memory` structured entries, and full-artifact pull audit entries.
`context_payload` also includes `failure_entry_count` and
`checked_counterexample_evidence_count`; when an associated strategy plan
exists, it also includes `strategy_plan_count` and top-level `strategy_plans`
summary entries. Full-artifact pull reasons include the retrieval role, policy
scope, and explicit maximum pull budget.
`public_only=True` excludes private cards and private artifact IDs from both
rendered context and audit output, including private failure-log text and
private strategy-plan node text.

When visible artifacts carry artifact-level `failure_log` entries, context
packs render a `Known Failed Directions` section in `CONTEXT.md` and
`KNOWN_FAILURES.md`. Each entry includes artifact ID, direction,
`failed_because`, failure status, next possible directions, origin, attempt
kind, path, root scope, and source/origin label. The section is explicitly
failed/unresolved attempt memory only and is not proof, refutation, verifier
pass, checked counterexample evidence, human review, gate success, accepted
status, or promotion evidence. Empty failure logs do not add the markdown
section.

When a relevant artifact has formal-link metadata or policy-relevant formal
settings, the artifact entry also includes compact formal-link metadata lines:

- `Formal links:` entries ordered by formalization ID, rendered as
  `<library>@<library_ref>:<import_path>#<symbol> [<kind>, <status>, <mode>]`
- `Alignment: <status>; reviewer=<reviewer-or-dash>`
- `Verification policy: <level>; formal_link=<bool>; lean_check=<bool>;
  alignment_review=<bool>`
- `G10-relevant: yes; ...` policy hints derived from artifact metadata

These context-pack lines are metadata-only handoff context. They do not load
gate reports, do not claim the current G10 verdict, and do not claim Lean
verification. Retrieval scores are ranking metadata only and do not authorize
review, promotion, proof, or public/private policy bypasses.

#### Agent Tasks

- `cosheaf.agent.roles.RoleName`: enum for role prompt/context contracts with
  values `librarian`, `reasoner`, `verifier`, `formalizer`, `explorer`,
  `counterexampleer`, `collector`, and `librarian_summarizer`.
- `cosheaf.agent.roles.RoleOutputSchema`: strict Pydantic v2 model describing
  required and optional fields expected from one role's worker output.
- `cosheaf.agent.roles.RoleContextBudget`: strict Pydantic v2 model for
  bounded role context budgets, including maximum cards, maximum full artifact
  pulls, maximum prompt characters, and private-context allowance.
- `cosheaf.agent.roles.RoleContextPolicy`: strict Pydantic v2 model for one
  role's provider-send context policy, including allowed root scopes, private
  context allowance, preview requirement, and explicit private-context consent
  requirement.
- `cosheaf.agent.roles.RoleProviderCapabilityRequirements`: strict Pydantic v2
  model for one role's provider-output expectations, including output kinds,
  JSON-output requirement, WorkerBundle requirement, and network requirement
  flag. Current contracts do not require provider network access.
- `cosheaf.agent.roles.RoleToolPolicy`: strict Pydantic v2 model for one
  role's tool and network policy. Current role contracts keep network access
  disabled.
- `cosheaf.agent.roles.RoleContract`: strict Pydantic v2 model for
  machine-readable role boundaries. It records role-specific prompt text,
  allowed inputs, forbidden actions, required output schema, context budget,
  context policy, provider capability requirements, tool policy, stop
  conditions, risk flags, `provider: fake`, and `hosted_llm_enabled: false`.
  Role-specific validators require structured output fields for reasoner
  conjectures/proof ideas/assumptions, verifier natural-language concerns vs
  tool results, counterexample candidate vs verified status, explorer
  uncertainty and dependency questions, formalizer symbol resolution vs
  semantic-alignment questions, and librarian-summarizer retrieval uncertainty.
  Validators also enforce role-specific forbidden authority such as no invented
  claims, no unverified refutations, no hidden skipped verifier results, and no
  informal/formal equivalence claims without alignment review.
- `cosheaf.agent.roles.REQUIRED_ROLE_NAMES`: deterministic tuple of required
  hosted-worker role names in contract order: `reasoner`, `verifier`,
  `counterexampleer`, `explorer`, `formalizer`, and
  `librarian_summarizer`.
- `cosheaf.agent.roles.ROLE_CONTRACTS`: deterministic tuple of the built-in
  required hosted-worker role contracts. The built-in contracts do not write
  accepted knowledge, do not promote artifacts, do not mark human review, and
  do not enable hosted LLMs.
- `cosheaf.agent.roles.list_role_contracts() -> tuple[RoleContract, ...]`:
  returns all required hosted-worker role contracts in deterministic order.
- `cosheaf.agent.roles.get_role_contract(role: RoleName | str) -> RoleContract`:
  returns one built-in role contract by enum value or role-name string.
  Legacy local role names `librarian` and `collector` resolve to
  `librarian_summarizer`.
- `cosheaf.agent.model_provider.ModelRequest`: strict Pydantic v2 model for a
  provider-neutral model request. Fields include `provider`, `model`, `prompt`,
  `temperature`, `top_p`, `reasoning_effort`, `max_output_tokens`,
  `tool_policy`, `network_policy`, and `metadata`.
- `cosheaf.agent.model_provider.ModelResponse`: strict Pydantic v2 model for a
  provider-neutral model response with `provider`, `model`, `content`,
  `finish_reason`, negotiated `capability`, warnings, and metadata.
- `cosheaf.agent.model_provider.ProviderCapability`: strict Pydantic v2 model
  recording supported and unsupported request parameters for one provider/model
  pair. Capability negotiation metadata is informational and does not grant
  review, verifier, gate, or promotion authority.
- `cosheaf.agent.model_provider.ModelProvider`: protocol for provider-neutral
  model adapters. Implementations expose `negotiate_capability(...)` and
  `generate(...)`.
- `cosheaf.agent.model_provider.FakeModelProvider`: deterministic local fake
  provider. It performs no network call, imports no hosted-provider SDK, and
  records unsupported requested parameters instead of crashing.
- `cosheaf.agent.model_provider.ProviderName`: enum with `fake`, `openai`,
  `anthropic`, `google`, and `local`. The provider gateway currently supports
  fake calls and OpenAI-compatible calls through explicitly injected transport,
  including the optional stdlib HTTP transport object.
- `cosheaf.agent.model_provider.ReasoningEffort`: enum with `low`, `medium`,
  and `high`.
- `cosheaf.agent.model_provider.ToolPolicy`: enum with `none`, `read_only`,
  `local_tools`, and `verifier_tools`.
- `cosheaf.agent.model_provider.NetworkPolicy`: enum with `disabled` and
  `explicit_allow`.
- `cosheaf.agent.model_provider.FinishReason`: enum with `stop`, `length`, and
  `error`.
- `cosheaf.agent.providers.ProviderMode`: provider gateway mode enum with
  `fake` and `openai_compatible`.
- `cosheaf.agent.providers.ProviderTransportStatus`: normalized transport
  status enum with `completed`, `cancelled`, `failed`, `timeout`,
  `rate_limited`, and `error`.
- `cosheaf.agent.providers.ProviderConfig`: strict Pydantic v2 runtime
  configuration for provider id, mode, model, enabled flag, optional API-key
  environment variable name, timeout, retry count, optional base URL, and
  supported parameter list.
- `cosheaf.agent.providers.ProviderGatewayRequest`: strict Pydantic v2 gateway
  request carrying provider/model, worker role, prompt, consent, context
  artifact IDs, root scopes, output kind, expected output paths, model
  parameters, tool policy, and network policy. It rejects private context
  without explicit private-research policy and consent, and rejects expected
  output paths that target accepted knowledge.
- `cosheaf.agent.providers.ProviderTransportResult`: strict Pydantic v2 DTO for
  an injected transport response, including normalized status, finish reason,
  latency, token counts, cost, error fields, and raw metadata.
- `cosheaf.agent.providers.ProviderError`: expected provider gateway error DTO
  with stable code, message, remediation, blocking flag, and details.
- `cosheaf.agent.providers.OpenAICompatibleProvider`: adapter over an injected
  transport object. It does not perform network calls by itself.
- `cosheaf.agent.providers.OpenAICompatibleHttpTransport`: optional stdlib
  HTTP transport for OpenAI-compatible chat-completions calls. It is inert
  unless explicitly injected into `OpenAICompatibleProvider`, requires
  `ProviderConfig.enabled`, `mode=openai_compatible`, explicit `base_url`,
  `api_key_env`, `NetworkPolicy.EXPLICIT_ALLOW`, and an environment-provided
  API key, and returns `ProviderTransportResult` statuses/errors instead of
  raising expected timeout, HTTP, network, JSON, or malformed-response
  failures. Tests use injected local fixtures rather than live provider
  network.
- `cosheaf.agent.providers.ProviderGateway.call(request, *, config=None, provider=None) -> ModelCallResult | ProviderError`:
  executes the fake provider path or the OpenAI-compatible injected-transport
  path, writes redacted run logs under `.cosheaf/providers/`, validates
  WorkerBundle v2 outputs when requested, handles timeout, retry,
  cancellation, and rate-limit statuses, may perform one configured
  output-validation retry for malformed WorkerBundle v2 payloads with a stricter
  schema reminder, records output-validation retry metadata in provider logs,
  and does not write accepted knowledge or perform promotion.
- `cosheaf.agent.providers.redact_text(value) -> tuple[str, bool]` and
  `cosheaf.agent.providers.redact_mapping(values) -> tuple[dict[str, str], bool]`:
  redact common secret value shapes and secret-looking metadata fields before
  provider logs are written.
- `cosheaf.security.provider_logs.ProviderLogLeakFinding`: dataclass for one
  deterministic generated-provider-log scanner finding. It records stable
  `kind`, explanatory `message`, optional `path`, optional `line`, and optional
  `key` metadata.
- `cosheaf.security.provider_logs.scan_provider_log_text(text, *, path=None) -> list[ProviderLogLeakFinding]`
  and `scan_provider_log_file(path) -> list[ProviderLogLeakFinding]`: scan
  generated provider logs and run records for API-key-shaped values, bearer
  tokens, environment-like dumps, secret-looking key/value pairs, hidden
  reasoning markers, unapproved private context markers, and avoidable absolute
  user/workspace filesystem paths. The scanner is a regression/security helper;
  it does not make provider calls, write logs, redact data, validate knowledge,
  run gates, or authorize promotion.
- `cosheaf.agent.hosted_workers.HostedWorkerStatus`: normalized hosted worker
  status enum with `completed`, `rejected`, `failed`, and `skipped`.
- `cosheaf.agent.hosted_workers.HostedWorkerInput`: strict Pydantic v2 model
  for one role-specific hosted worker request. It records issue ID, role,
  prompt, context artifact IDs, root scopes, and provider consent.
- `cosheaf.agent.hosted_workers.HostedWorkerTypedResult`: strict Pydantic v2
  model for review-only typed sub-results from roles that do not map directly
  to WorkerBundle v2 worker roles, such as `explorer` and
  `librarian_summarizer`.
- `cosheaf.agent.hosted_workers.HostedWorkerOutput`: strict Pydantic v2 model
  for one hosted worker result. It records issue ID, role, status, provider
  run/log metadata, optional WorkerBundle v2, optional typed sub-result,
  optional `ErrorResult`, and `accepted_write_performed: false`.
- `cosheaf.agent.hosted_workers.HostedWorkerService.run(input, *, config=None, provider=None) -> HostedWorkerOutput`:
  calls the provider gateway through `ModelCallService`, validates fake or
  mocked provider output as WorkerBundle v2 or typed review-only sub-result,
  includes the role contract's required/optional output fields and forbidden
  authority in the provider prompt, writes provider audit logs through the
  gateway, and returns structured rejected output for expected provider,
  validation, or hosted-worker policy failures. It does not add a CLI command,
  perform a real network call by itself, write proposed artifacts, write
  accepted knowledge, create human review records, or promote artifacts.
- `cosheaf.agent.task.WorkerType`: protocol worker type enum with values `reasoner`, `verifier`, `counterexampleer`, `construction_searcher`, `formalizer`, `literature_scout`, and `orchestrator`.
- `cosheaf.agent.task.TaskStatus`: task status enum with values `open`, `in_progress`, `blocked`, `completed`, `failed`, and `cancelled`.
- `cosheaf.agent.task.AgentTask`: Pydantic v2 model for local task records with fields `task_id`, `issue_id`, `worker_type`, `status`, `input_context`, `budget`, `expected_outputs`, `created_at`, and `updated_at`.
- `cosheaf.agent.task.create_task_id(issue_id: str, worker_type: WorkerType | str) -> str`: deterministic default task ID helper. It returns `task.<issue-id>.<worker-type-slug>`, with underscores in worker type values rendered as hyphens.
- `cosheaf.agent.orchestrator_state.OrchestratorState`: orchestrator run state enum with values `created`, `planned`, `running`, `waiting_for_worker`, `waiting_for_gate`, `waiting_for_review`, `blocked`, `completed`, `failed`, and `abandoned`.
- `cosheaf.agent.orchestrator_state.OrchestratorRun`: strict serializable Pydantic v2 model for one orchestrator run record. It exposes `create(...)`, `transition(...)`, `to_dict()`, and `to_json()` helpers and validates the explicit transition graph.
- `cosheaf.agent.orchestrator_state.Plan`: strict serializable Pydantic v2 model for an auditable orchestrator plan.
- `cosheaf.agent.orchestrator_state.TaskDAG`: strict serializable Pydantic v2 model for task nodes. It rejects duplicate node IDs, unknown dependencies, and cycles.
- `cosheaf.agent.orchestrator_state.TaskNode`: strict serializable Pydantic v2 model for one task-DAG node.
- `cosheaf.agent.orchestrator_state.WorkerCall`: strict serializable Pydantic v2 model for worker invocation metadata. It records command, cwd, timestamps, exit code, output log paths, and optional bundle path without executing anything.
- `cosheaf.agent.orchestrator_state.ReducerResult`: strict serializable Pydantic v2 model for reducer decisions. Its output paths must be repository-local and must not target accepted knowledge.
- `cosheaf.agent.orchestrator_state.StopCondition`: strict serializable Pydantic v2 model for stop or pause conditions.
- `cosheaf.agent.orchestrator_planner.plan_for_issue(context: RepoContext, issue_id: str) -> Plan`: deterministic local-only planner stub. It loads an existing issue and returns a `Plan` with librarian-retrieval, reasoner-draft, verifier-check, and review-request task nodes. It does not write files or execute workers.
- `cosheaf.agent.orchestrator_planner.OrchestratorPlannerError`: expected planner failure, including missing issue records and repository load failures.
- `cosheaf.agent.worker_contract.WorkerOutputKind`: output kind enum with values `artifact`, `review`, `evidence`, and `report`.
- `cosheaf.agent.worker_contract.WorkerOutput`: Pydantic v2 model for one repository-local output reference.
- `cosheaf.agent.worker_contract.WorkerOutputBundle`: Pydantic v2 model for a local worker output bundle manifest.
- `cosheaf.agent.worker_contract.OutputBundleError`: expected worker output bundle validation error.
- `cosheaf.agent.worker_contract.validate_output_bundle(context: RepoContext, bundle_path: str | Path, *, task: AgentTask | None = None) -> WorkerOutputBundle`: validates a local bundle manifest and referenced output paths without merging accepted knowledge.
- `cosheaf.agent.worker_bundle_v2.WorkerBundleConfidence`: confidence enum with values `low`, `medium`, and `high`.
- `cosheaf.agent.worker_bundle_v2.CounterexampleCandidateStatus`: typed
  counterexample candidate status enum with values `proposed`, `needs_check`,
  `checked_false`, `checked_true`, `rejected`, and `superseded`.
- `cosheaf.agent.worker_bundle_v2.ProposedArtifact`: strict Pydantic v2 model for one repository-local proposed artifact path and summary.
- `cosheaf.agent.worker_bundle_v2.CounterexampleCandidate`: strict Pydantic
  v2 model for one typed counterexample candidate review record. It records
  `candidate_id`, optional `target_claim`, `construction_summary`,
  `evidence_paths`, `verifier_request_ids`, `status`, and `limitations`.
  Checked statuses require at least one evidence path, but the record remains
  review-only and does not create verifier results, human review, accepted
  refutations, or promotion authority.
- `cosheaf.agent.worker_bundle_v2.WorkerBundleV2`: strict Pydantic v2 model for reducer-oriented worker bundles with fields `bundle_id`, `task_id`, `worker_role`, `created_at`, `summary`, `used_artifacts`, `used_sources`, `claims`, `proposed_artifacts`, optional review-preservation fields `assumptions`, `uncertainty`, `failed_attempts`, `counterexamples`, `counterexample_candidates`, and `dependency_questions`, legacy-compatible `verification_requests` and `failures_or_counterexamples`, plus `risk_flags`, `next_steps`, and `confidence`.
- `cosheaf.agent.worker_bundle_v2.WorkerBundleV2Error`: expected worker bundle v2 validation or reducer-boundary failure.
- `cosheaf.agent.worker_bundle_v2.validate_worker_bundle_v2(context: RepoContext, bundle_path: str | Path) -> WorkerBundleV2`: loads and validates a worker bundle v2 manifest without executing workers, writing files, requesting review, or promoting accepted knowledge. It rejects non-repository-local bundle paths, non-repository-local proposed artifact paths, accepted-KB proposals, schema-invalid existing proposed artifacts, and worker-created `human_reviewed` or `accepted` review states.
- `cosheaf.agent.worker_bundle_v2.reduce_worker_bundle_v2(context: RepoContext, bundle_path: str | Path, *, reducer_id: str) -> ReducerResult`: validates a worker bundle v2 manifest and returns a deterministic `ReducerResult`, preserving assumptions, uncertainty, verification requests, failed attempts, legacy string counterexamples, typed counterexample candidates, dependency questions, legacy failure/counterexample notes, risk flags, and confidence as labeled warnings. Verification requests are preserved as requests, not verifier results; counterexamples remain candidate review evidence, not accepted refutations.
- `cosheaf.agent.worker_bundle_v2.worker_bundle_review_warnings(bundle: WorkerBundleV2) -> list[str]`: returns the labeled reducer/review warnings used by bundle reduction and bundle submission.
- `cosheaf.agent.orchestrator_runner.OrchestratorLocalRunConfig`: dataclass for one local-only orchestrator dry-run with fields `issue_id`, `timeout_seconds`, optional `worker_command`, optional `proposal_path`, optional `run_id`, and optional `now`.
- `cosheaf.agent.orchestrator_runner.OrchestratorLocalRunResult`: dataclass containing the final `OrchestratorRun`, run root, run record path, and structured run-log path.
- `cosheaf.agent.orchestrator_runner.OrchestratorLocalRunner`: local-only orchestrator runner that converts a deterministic plan into local task records, runs explicit argv commands through `LocalWorkerRunner`, validates worker bundle v2 outputs, reduces them into `ReducerResult` records, and writes the final run record plus sanitized structured `run_log.json`. It does not call hosted LLMs, make network calls, run gates, request human review, write accepted knowledge, or promote artifacts.
- `cosheaf.agent.orchestrator_runner.OrchestratorLocalRunner.run_issue(config: OrchestratorLocalRunConfig) -> OrchestratorLocalRunResult`: runs one issue-scoped local-only dry-run and returns the final persisted run metadata.
- `cosheaf.agent.orchestrator_runner.OrchestratorLocalRunError`: expected local orchestrator run failure, including invalid configuration, missing issue records, duplicate run IDs, and local runner boundary failures.
- `cosheaf.agent.orchestrator_runner.OrchestratorHostedRunConfig`: dataclass
  for one explicit hosted-worker orchestrator run with fields `issue_id`,
  `provider`, `confirm_send`, `include_private`, `policy_mode`,
  `allow_private_context`, `max_cards`, optional `run_id`, and optional `now`.
- `cosheaf.agent.orchestrator_runner.OrchestratorHostedRunResult`: dataclass
  containing the final `OrchestratorRun`, run root, run record path,
  structured run-log path, provider-send context preview, provider mode,
  run-local provider record paths, and `accepted_write_performed: false`.
- `cosheaf.agent.orchestrator_runner.OrchestratorHostedRunner`: explicit
  hosted-worker orchestrator runner that converts a deterministic plan into
  role-specific `HostedWorkerService` calls, validates and reduces only
  WorkerBundle v2 outputs, writes typed sub-results and provider-record copies
  under the run-local `.cosheaf/orchestrator/...` directory, and refuses real
  provider dispatch unless `confirm_send` is set. The fake path performs no
  hosted network call; the OpenAI-compatible path requires an injected or
  configured transport and does not include built-in HTTP transport.
- `cosheaf.agent.orchestrator_runner.OrchestratorHostedRunner.run_issue(config, *, provider_config=None, provider=None) -> OrchestratorHostedRunResult`:
  runs one issue-scoped hosted-worker dispatch and returns the final persisted
  run metadata without writing accepted knowledge, marking human review,
  promoting artifacts, running gates, or treating provider output as verifier
  success.
- `cosheaf.agent.orchestrator_runner.OrchestratorHostedRunError`: expected
  hosted-worker orchestrator run failure carrying an `ErrorResult`, including
  unsupported providers, missing `--confirm-send`, context policy denials,
  duplicate run IDs, and planning failures.
- `cosheaf.agent.run_logging.StructuredRunLog`: strict Pydantic v2 JSON DTO for local run observability with run/task/artifact/bundle IDs, timing, status, stop reason, and sanitized worker-call metadata.
- `cosheaf.agent.run_logging.RunLogWorkerCall`: strict Pydantic v2 DTO for sanitized worker-call metadata. It records redacted command argv but does not inline stdout or stderr contents.
- `cosheaf.agent.run_logging.structured_log_from_orchestrator_run(run: OrchestratorRun) -> StructuredRunLog`: derives a structured local run log from an orchestrator run DTO.
- `cosheaf.agent.run_logging.write_orchestrator_run_log(path: Path, run: OrchestratorRun) -> StructuredRunLog`: writes deterministic `run_log.json` for a local orchestrator run.
- `cosheaf.agent.run_logging.redact_command(command: list[str]) -> list[str]`: redacts common secret flags and token-like values from command argv metadata before logging.
- `cosheaf.observability.otel.OTelTelemetryConfig`: dataclass controlling optional OpenTelemetry-style export with `enabled=False` and `strict=False` by default.
- `cosheaf.observability.otel.OTelSpanExporter`: minimal exporter protocol for caller-provided span exporters. The framework does not require the OpenTelemetry SDK or configure a collector.
- `cosheaf.observability.otel.emit_run_log_span(run_log, *, exporter=None, config=None) -> OTelExportResult`: optionally exports sanitized `StructuredRunLog` metadata as one span. Export is disabled by default; non-strict exporter failures return an error result instead of failing the research workflow.
- `cosheaf.observability.otel.run_log_span_attributes(run_log: StructuredRunLog) -> dict[str, object]`: converts safe run/task/artifact IDs and status fields to span attributes without command argv, stdout, stderr, hidden reasoning, or secret values.
- `cosheaf.agent.dry_run_workers.dry_run_worker_command(...) -> list[str]`: returns the explicit local argv used by the orchestrator runner's default fake dry-run worker. The command writes a worker bundle v2 manifest only; it does not call hosted LLMs, use network services, run gates, request review, write proposal artifacts, write accepted knowledge, or promote artifacts.
- `cosheaf.agent.dry_run_workers.build_dry_run_bundle(...) -> dict[str, object]`: builds a role-aware fake worker bundle mapping for orchestrator, reasoner, or verifier dry-runs. Reasoner bundles are draft proposal context only, verifier bundles record that no real gate/Lean/SAT/SMT/promotion result was produced, and all bundles remain low-confidence dry-run output.
- `cosheaf.agent.dry_run_workers.main(argv: list[str] | None = None) -> int`: CLI entry point invoked by the local runner command to write one deterministic dry-run worker bundle.
- `cosheaf.agent.orchestrator_stub.OrchestratorStub`: local filesystem task harness stub. It creates, lists, loads, and completes task records without LLM calls, network calls, concrete worker execution, or accepted knowledge merges.
- `cosheaf.agent.orchestrator_stub.TaskHarnessError`: expected task harness error.
- `cosheaf.agent.orchestrator_stub.AcceptedKnowledgeMergeProhibitedError`: raised when a caller asks the stub to merge accepted knowledge.
- `cosheaf.agent.orchestrator_stub.TaskCompletionResult`: completed task, validated bundle, and task path.
- `cosheaf.agent.local_runner.LocalWorkerRunner`: filesystem-backed local runner for existing task records. It executes explicit command argv lists with `shell=False`, rejects `cwd` and `bundle_path` values outside the repository, enforces timeouts, captures stdout/stderr, writes deterministic run records, optionally validates worker output bundles, and never merges outputs or promotes accepted knowledge.
- `cosheaf.agent.local_runner.LocalWorkerRunConfig`: dataclass for one run with fields `command`, `timeout_seconds`, `cwd`, `bundle_path`, `run_id`, and `started_at`.
- `cosheaf.agent.local_runner.LocalWorkerRunResult`: dataclass containing `task`, `run_id`, `status`, `returncode`, `run_dir`, `record_path`, `stdout_path`, `stderr_path`, and `bundle_valid`.
- `cosheaf.agent.local_runner.LocalWorkerRunError`: expected local runner failure, including missing tasks, invalid argv, invalid timeouts, invalid run IDs, `cwd` outside the repository, and `bundle_path` outside the repository.

Task records are written under:

- `.cosheaf/tasks/<task-id>.yaml`

Local worker run records are written under:

- `.cosheaf/tasks/<task-id>/runs/<run-id>/run.yaml`
- `.cosheaf/tasks/<task-id>/runs/<run-id>/stdout.txt`
- `.cosheaf/tasks/<task-id>/runs/<run-id>/stderr.txt`

Strategy planner runtime records are written under:

- `.cosheaf/strategy/<plan-id>/strategy.json`

Strategy runtime records are generated guidance. They are not review records,
accepted knowledge, verifier evidence, gate reports, human review, or
promotion authority.

Local worker run record YAML fields are:

- `schema_version`
- `task_id`
- `worker_type`
- `command`
- `cwd`
- `started_at`
- `finished_at`
- `timeout_seconds`
- `returncode`
- `stdout_path`
- `stderr_path`
- `bundle_path`
- `bundle_valid`
- `status`

Local worker run status values are:

- `completed`
- `failed`
- `timed_out`
- `bundle_invalid`

Orchestrator run records use `schemas/orchestrator_run.schema.json` and these
top-level fields:

- `schema_version`
- `run_id`
- `issue_id`
- `state`
- `plan`
- `worker_calls`
- `reducer_results`
- `stop_conditions`
- `created_at`
- `updated_at`

The state model is a pure contract. It does not dispatch workers, run hosted
models, run gates, request human review, complete tasks, merge worker outputs,
or promote accepted knowledge.

Worker output bundles may be passed as a YAML file path or as a directory
containing `bundle.yaml`. Bundle manifests use:

- `schema_version`
- `task_id`
- `worker_type`
- `outputs`
- `notes`

Artifact and review outputs must point to repository-local YAML records that
pass the schema gate. Outputs under `kb/accepted/` are rejected.

Worker bundle v2 manifests use `schemas/worker_bundle_v2.schema.json` and these
top-level fields:

- `bundle_id`
- `task_id`
- `worker_role`
- `created_at`
- `summary`
- `used_artifacts`
- `used_sources`
- `claims`
- `proposed_artifacts`
- `assumptions` (optional; defaults to empty)
- `uncertainty` (optional; defaults to empty)
- `verification_requests`
- `failed_attempts` (optional; defaults to empty)
- `counterexamples` (optional; defaults to empty candidate evidence)
- `counterexample_candidates` (optional; defaults to empty typed candidate records)
- `failures_or_counterexamples`
- `dependency_questions` (optional; defaults to empty)
- `risk_flags`
- `next_steps`
- `confidence`

Worker bundle v2 is a reducer-oriented contract. It is used by bundle services,
local dry-run workers, hosted-worker outputs, and task-run bundle validation,
but it still does not authorize gates, verifier results, human review, accepted
knowledge writes, accepted refutations, or promotion.

#### Promotion Readiness

- `cosheaf.gates.promotion_readiness.build_promotion_readiness_report(context, *, artifact_id=None, issue_id=None) -> PromotionReadinessReport`:
  builds a read-only readiness report for exactly one artifact target or one
  issue target. It runs repository validation and gatekeeper reporting but does
  not promote artifacts or write accepted knowledge.
- `cosheaf.gates.promotion_readiness.PromotionReadinessReport`: dataclass with
  `schema_version`, target mode, target IDs, gate report paths, artifact
  reports, top-level reasons, `ready`, `accepted_write_performed`, and
  `to_dict()`.
- `cosheaf.gates.promotion_readiness.ArtifactPromotionReadiness`: per-artifact
  readiness dataclass with status, source path, KB root, readonly flag, review
  state, checker-required flag, source metadata status, gate verdict, verifier
  results, reasons, `ready`, and `to_dict()`. Unresolved artifact failure
  memory appears as warning reasons with code `unresolved_failure_memory`.
  Open strategy-plan blockers may appear as warning reasons with code
  `strategy_open_blocker`.
- `cosheaf.gates.promotion_readiness.PromotionReadinessReason`: reason
  dataclass with `code`, `severity`, `message`, artifact/source/gate/verifier
  metadata, `blocking`, and `to_dict()`.

Promotion readiness objects are advisory reporting surfaces only. They do not
change accepted-promotion semantics, do not satisfy human review, and do not
convert skipped verifier results into passes. Failure-memory warning reasons
and strategy-plan warning reasons are not verifier evidence and are not
promotion blockers by themselves.

#### Verification

- `cosheaf.verification.base.VerifierAdapter`: protocol for verifier adapters.
- `cosheaf.verification.evidence.VerifierEvidenceKind`: verifier evidence
  backend-family enum with `python`, `sat`, `smt`, `lean`,
  `external_reference`, and `manual_note`.
- `cosheaf.verification.evidence.VerifierEvidenceRecord`: Pydantic v2 model
  for serialized verifier evidence records.
- `cosheaf.verification.result.VerificationStatus`: normalized result status enum with `pass`, `fail`, `error`, and `skipped`.
- `cosheaf.verification.result.VerificationResult`: Pydantic v2 model for normalized verifier output.
- `cosheaf.verification.registry.VerifierRegistry`: instance-local verifier adapter registry.
- `cosheaf.verification.registry.VerifierRegistryError`: registry registration error.
- `cosheaf.verification.registry.default_verifier_registry() -> VerifierRegistry`
- `cosheaf.verification.python_checker.PythonCheckerAdapter`: verifier adapter for `kind: python_checker` evidence.
- `cosheaf.verification.python_checker.PythonCheckerSpec`: normalized Python checker evidence command specification.
- `cosheaf.verification.sat_adapter.SatBackendResult`: normalized SAT backend invocation result.
- `cosheaf.verification.sat_adapter.SatBackend`: protocol for optional SAT backends.
- `cosheaf.verification.sat_adapter.ExternalSatCommandBackend`: optional external-command SAT backend.
- `cosheaf.verification.sat_adapter.SatAdapter`: optional minimal SAT DIMACS verifier adapter.
- `cosheaf.verification.smt_adapter.SmtBackendResult`: normalized SMT backend invocation result.
- `cosheaf.verification.smt_adapter.SmtBackend`: protocol for optional SMT backends.
- `cosheaf.verification.smt_adapter.ExternalSmtCommandBackend`: optional external-command SMT backend.
- `cosheaf.verification.smt_adapter.SmtAdapter`: optional minimal SMT-LIB verifier adapter.
- `cosheaf.verification.lean_adapter.LeanBackendResult`: normalized Lean backend invocation result.
- `cosheaf.verification.lean_adapter.LeanBackend`: protocol for optional Lean backends.
- `cosheaf.verification.lean_adapter.ExternalLeanCommandBackend`: optional external-command Lean backend.
- `cosheaf.verification.lean_adapter.LeanAdapter`: optional minimal Lean verifier adapter.
- `cosheaf.verification.lean_external.LeanLibraryRefSpec`: normalized external
  Lean library formalization reference to check.
- `cosheaf.verification.lean_external.LeanLibraryRefBackendResult`: normalized
  external Lean library reference backend invocation result.
- `cosheaf.verification.lean_external.LeanLibraryRefBackend`: protocol for
  optional external Lean library reference backends.
- `cosheaf.verification.lean_external.ExternalLeanLibraryRefBackend`: optional
  external-command backend for generated Lean `import`/`#check` files.
- `cosheaf.verification.lean_external.LeanLibraryRefAdapter`: optional
  external Lean library reference verifier adapter.

`VerifierAdapter` requires:

- `name: str`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

`VerificationResult` fields are:

- `verifier`
- `artifact_id`
- `status`
- `started_at`
- `ended_at`
- `command`
- `cwd`
- `exit_code`
- `stdout_path`
- `stderr_path`
- `evidence_paths`
- `timeout_seconds`
- `input_paths`
- `output_paths`
- `tool_name`
- `tool_version`
- `seed`
- `environment`
- `message`

`VerificationResult.to_dict() -> dict[str, Any]` returns a deterministic
machine-readable mapping in model field order. `VerificationResult.to_json() ->
str` returns deterministic JSON for the result. Timestamps are the only expected
run-to-run variation when callers construct results with live clock values.
`VerificationResult.to_evidence_record() -> VerifierEvidenceRecord` returns a
typed v1 evidence record derived from the runtime result without changing
gatekeeper or promotion semantics.

`VerificationResult` exposes status helpers:

- `is_pass`
- `is_fail`
- `is_error`
- `is_skipped`

`VerifierEvidenceRecord` fields are:

- `evidence_id`
- `artifact_id` (optional)
- `claim_id` (optional)
- `verifier_kind`
- `tool_name`
- `tool_version` (optional)
- `command_argv` (optional)
- `cwd` (optional)
- `result`
- `reason_code`
- `stdout_path` (optional)
- `stderr_path` (optional)
- `log_path` (optional)
- `created_at`
- `checker_input_hash` (optional)
- `checker_output_hash` (optional)
- `limitations`

`VerifierEvidenceRecord.from_verification_result(...)` derives a stable
evidence ID, verifier kind, default reason code, and explicit limitations from
an existing `VerificationResult`. The evidence record is serialization support
only: it is not human review, does not auto-promote accepted knowledge, and
does not make skipped verifier output pass.

`VerifierEvidenceRecord.to_dict() -> dict[str, Any]` and
`VerifierEvidenceRecord.to_json() -> str` return deterministic serialized
forms.

`CheckedCounterexampleEvidenceRecord` fields are:

- `schema_version`
- `evidence_id`
- `target_artifact_id`
- `candidate_id`
- `candidate_source`
- `check_method`
- `checked_result`
- `verifier_evidence_ids`
- `review_record_paths`
- `evidence_paths`
- `created_at`
- `checker`
- `limitations`

`checked_result` accepts `checked_refutes`, `checked_does_not_refute`,
`inconclusive`, `error`, and `skipped`. `checked_refutes` requires at least one
supporting verifier evidence ID, review-record path, or evidence path.
`skipped` requires an explicit skipped-not-pass limitation. Repository paths
must be repository-local and must not target accepted KB paths.

`CheckedCounterexampleEvidenceRecord.to_dict() -> dict[str, Any]` and
`CheckedCounterexampleEvidenceRecord.to_json() -> str` return deterministic
serialized forms. `stage_checked_counterexample_evidence(...)` writes only to
`reviews/evidence/checked-counterexamples/`; `show_checked_counterexample_evidence(...)`
loads staged records by ID or path.

`VerifierRegistry` exposes:

- `register(adapter: VerifierAdapter) -> None`
- `get(name: str) -> VerifierAdapter | None`
- `names -> tuple[str, ...]`
- `adapters -> tuple[VerifierAdapter, ...]`

Registry ordering is deterministic by adapter name. Duplicate adapter names
raise `VerifierRegistryError`.

The default verifier registry currently registers `LeanAdapter`,
`LeanLibraryRefAdapter`, `PythonCheckerAdapter`, `SatAdapter`, and `SmtAdapter`.
Registry ordering is deterministic by adapter name.

`PythonCheckerAdapter` exposes:

- `name = "python_checker"`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

The adapter runs evidence entries with `kind: python_checker` from the
repository root. With the current artifact evidence model, it derives the command
from the active Python executable, the evidence `path`, and the artifact source
path. It writes stdout and stderr under `.cosheaf/logs/`, records command, cwd,
timeout, input path, output path, tool, tool version, and environment metadata,
returns `pass` for exit code `0`, `fail` for nonzero exit code, and `error` for
timeout or missing checker scripts.

`SatAdapter` exposes:

- `name = "sat"`
- `__init__(solver_command: str = "kissat", *, backend: SatBackend | None = None, timeout_seconds: float = 30.0)`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

It recognizes evidence kinds `sat`, `sat_solver`, and `sat_checker`. It first
requires the SAT evidence path to resolve inside the repository. When no
backend is supplied, it uses `ExternalSatCommandBackend` with the configured
solver command, defaulting to `kissat`. If no supported backend is available,
the adapter returns `skipped`, which is not a pass. If a backend is available,
the adapter runs the backend from the repository root against the DIMACS CNF
evidence, writes stdout and stderr logs under `.cosheaf/logs/`, parses
`sat`/`unsat`/`unknown`, compares against `CHECKER_DATA.expected.satisfiable`
when present, and returns normalized `pass`, `fail`, or `error` results with
command, cwd, timeout, input/output paths, backend metadata, exit code, and
result diagnostics.

`SatBackendResult` exposes:

- `exit_code: int | None`
- `stdout: str`
- `stderr: str`
- `result: Literal["sat", "unsat", "unknown"]`

`SatBackend` requires:

- `name: str`
- `is_available() -> bool`
- `command(cnf_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `solve(cnf_path: Path, *, cwd: Path, timeout_seconds: float) -> SatBackendResult`

`ExternalSatCommandBackend` exposes:

- `__init__(solver_command: str = "kissat")`
- `name`
- `solver_command`
- `is_available() -> bool`
- `command(cnf_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `solve(cnf_path: Path, *, cwd: Path, timeout_seconds: float) -> SatBackendResult`

The external backend detects availability with PATH lookup, obtains version
metadata from `<solver> --version` when possible, runs the solver with the
repository root as cwd, and parses common SAT solver output or exit codes:
`sat` from output containing SAT or exit code `10`, `unsat` from output
containing UNSAT or exit code `20`, and `unknown` otherwise.

`SmtAdapter` exposes:

- `name = "smt"`
- `__init__(solver_command: str = "z3", *, backend: SmtBackend | None = None, timeout_seconds: float = 30.0)`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

It recognizes evidence kinds `smt`, `smt_solver`, and `smt_checker`. It first
requires the SMT evidence path to resolve inside the repository. When no
backend is supplied, it uses `ExternalSmtCommandBackend` with the configured
solver command, defaulting to `z3`. If no supported backend is available, the
adapter returns `skipped`, which is not a pass. If a backend is available, the
adapter runs the backend from the repository root against the SMT-LIB evidence,
writes stdout and stderr logs under `.cosheaf/logs/`, parses exact
`sat`/`unsat`/`unknown` status lines, compares against
`CHECKER_DATA.expected.satisfiable` when present, and returns normalized
`pass`, `fail`, or `error` results with command, cwd, timeout, input/output
paths, backend metadata, exit code, and result diagnostics.

`SmtBackendResult` exposes:

- `exit_code: int | None`
- `stdout: str`
- `stderr: str`
- `result: Literal["sat", "unsat", "unknown"]`

`SmtBackend` requires:

- `name: str`
- `is_available() -> bool`
- `command(smt_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `solve(smt_path: Path, *, cwd: Path, timeout_seconds: float) -> SmtBackendResult`

`ExternalSmtCommandBackend` exposes:

- `__init__(solver_command: str = "z3")`
- `name`
- `solver_command`
- `is_available() -> bool`
- `command(smt_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `solve(smt_path: Path, *, cwd: Path, timeout_seconds: float) -> SmtBackendResult`

The external backend detects availability with PATH lookup, obtains version
metadata from `<solver> --version` when possible, runs `z3 -smt2 <file.smt2>`
style commands with the repository root as cwd, and parses solver output only
from exact status lines: `sat`, `unsat`, or `unknown`.

`LeanAdapter` exposes:

- `name = "lean"`
- `__init__(lean_command: str = "lean", *, backend: LeanBackend | None = None, timeout_seconds: float = 30.0)`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

It recognizes evidence kinds `lean`, `lean4`, `lean_checker`, and
`lean_proof`. It first requires the Lean evidence path to resolve inside the
repository and requires the referenced file to exist. When no backend is
supplied, it uses `ExternalLeanCommandBackend` with the configured Lean command,
defaulting to `lean`. If no supported backend is available, the adapter returns
`skipped`, which is not a pass. If a backend is available, the adapter runs the
backend from the repository root against the plain Lean file, writes stdout and
stderr logs under `.cosheaf/logs/`, and returns normalized `pass`, `fail`, or
`error` results with command, cwd, timeout, input/output paths, backend
metadata, exit code, and diagnostics. Exit code `0` is `pass`, nonzero exit
code is `fail`, and timeout or startup errors are `error`. The adapter does not
autoformalize natural language and does not implement SAT or SMT behavior.

`LeanBackendResult` exposes:

- `exit_code: int | None`
- `stdout: str`
- `stderr: str`

`LeanBackend` requires:

- `name: str`
- `is_available() -> bool`
- `command(lean_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `check(lean_path: Path, *, cwd: Path, timeout_seconds: float) -> LeanBackendResult`

`ExternalLeanCommandBackend` exposes:

- `__init__(lean_command: str = "lean")`
- `name`
- `lean_command`
- `is_available() -> bool`
- `command(lean_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `check(lean_path: Path, *, cwd: Path, timeout_seconds: float) -> LeanBackendResult`

The external backend detects availability with PATH lookup, obtains version
metadata from `lean --version` when possible, and runs `lean <file.lean>` with
the repository root as cwd.

`LeanLibraryRefAdapter` exposes:

- `name = "lean_library_ref"`
- `__init__(lean_command: str = "lean", *, lake_command: str = "lake", use_lake: bool = False, backend: LeanLibraryRefBackend | None = None, cwd: str | Path | None = None, timeout_seconds: float = 30.0)`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

It recognizes artifact `formalizations` entries with `system: lean4`,
`check_mode: external_library_ref`, and `status: linked` or `checked`. Planned
formalizations are skipped by default and are not treated as checked. When a
checkable formalization exists, the adapter generates a temporary Lean file
outside the repository with:

```lean
import <import_path>
#check <symbol>
```

When no backend is supplied, it uses `ExternalLeanLibraryRefBackend` with the
configured Lean command, defaulting to `lean`; `use_lake=True` switches command
metadata and execution to `lake env lean <tempfile>`. If the selected backend
is unavailable, the adapter returns `skipped`, which is not a pass. If a backend
is available, it runs the generated file, writes stdout and stderr logs under
`.cosheaf/logs/`, and returns normalized `pass`, `fail`, or `error` results
with command, cwd, timeout, formalization input label, output paths, backend
metadata, exit code, and diagnostics. Exit code `0` is `pass`, nonzero exit
code is `fail`, and timeout or startup errors are `error`.

The external reference adapter does not fetch CSLib, mathlib, or any other
library; does not manage lake checkouts; does not autoformalize natural
language; does not update `formalizations[].status`; and does not prove
informal/formal semantic alignment. Under the current one-result verifier
adapter contract, one `verify(...)` call checks the first applicable
formalization for an artifact.

`LeanLibraryRefBackendResult` exposes:

- `exit_code: int | None`
- `stdout: str`
- `stderr: str`

`LeanLibraryRefBackend` requires:

- `name: str`
- `is_available() -> bool`
- `command(lean_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `check(lean_path: Path, *, cwd: Path, timeout_seconds: float) -> LeanLibraryRefBackendResult`

`ExternalLeanLibraryRefBackend` exposes:

- `__init__(lean_command: str = "lean", *, lake_command: str = "lake", use_lake: bool = False)`
- `name`
- `lean_command`
- `lake_command`
- `use_lake`
- `is_available() -> bool`
- `command(lean_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `check(lean_path: Path, *, cwd: Path, timeout_seconds: float) -> LeanLibraryRefBackendResult`

The external backend detects availability with PATH lookup for the selected
command, obtains version metadata from `<command> --version` when possible, and
runs either `lean <tempfile>` or `lake env lean <tempfile>` with the configured
working directory.

### Makefile Targets

- `make lint`: runs `python -m ruff check .`
- `make typecheck`: runs `python -m mypy cosheaf tests`
- `make test`: runs `python -m pytest`
- `make validate`: runs `python -m cosheaf.cli validate`.
- `make gate`: runs `python -m cosheaf.cli gate`, which defaults to a real gatekeeper run.

### Release And Smoke Scripts

- `python scripts/release_smoke.py --source <package-source>`: creates a clean
  temporary environment, installs the requested package source, and exercises
  the release fixture with help, version, validate, gate, index rebuild, and
  context-pack commands.
- `python scripts/ecosystem_smoke.py --cosheaf <command>`: runs the local
  network-free three-repository fixture smoke against a Cosheaf command. It
  checks workspace info, validation, gatekeeper, index rebuild, context build,
  readonly public-root write refusal, public-to-private dependency rejection,
  and accepted-to-draft dependency rejection.
- `python scripts/ecosystem_smoke.py --matrix`: runs the structured
  three-repository compatibility matrix. Matrix rows cover framework local
  checkout, framework verifier-evidence eval smoke, framework
  checked-evidence run-loop eval, framework research-run loop eval, optional
  verifier availability, framework git tag release smoke, workspace-template
  demo, workspace-template CLI-agent demo, workspace-template research-run
  demo, workspace-template fake-provider smoke, workspace-template
  verifier-evidence demo, public KB policy guard, public KB checked-evidence
  policy docs smoke, and public KB verifier-policy self-test. By default,
  network-install rows are
  reported as `skipped`, not `pass`. Optional verifier availability returns a
  skipped matrix row when SAT/SMT/Lean/lake tools are unavailable; that skipped
  result is not counted as pass.
- `python scripts/ecosystem_smoke.py --matrix --framework-tag <tag>`: selects
  the framework tag used by the opt-in network release-smoke row. The default
  remains the compatibility baseline `v0.2.4`; pass `--framework-tag v0.3.0`
  when checking the current published release.
- `python scripts/ecosystem_smoke.py --matrix --include-network`: also runs
  matrix rows that perform normal framework package install or git clone steps.
  This still does not run real hosted providers or require API keys.
- `python scripts/ecosystem_smoke.py --matrix --json`: emits a deterministic
  JSON report with `pass_count`, `fail_count`, `skip_count`, and per-row
  `repo`, `command`, `status`, `returncode`, and `message` fields. Failure
  messages include the repository name and failing command.
- `python scripts/ecosystem_smoke.py --verifier-evidence-eval`: runs the local
  verifier-evidence eval smoke used by the matrix. It loads
  `evals/verifier_evidence/cases.yaml`, runs deterministic fake evidence and
  candidate fixtures, emits JSON, and exits nonzero if the eval report fails.
- `python scripts/ecosystem_smoke.py --optional-verifier-availability`: probes
  optional SAT/SMT/Lean/lake command availability for matrix accounting. Exit
  code `77` means the row is skipped, not pass. The probe does not run those
  tools and does not make any external verifier mandatory.

### Schemas

- `schemas/artifact.schema.json`: artifact YAML schema. Inline
  `review.state` accepts `none`, `requested`, `in_review`, `approved`,
  `changes_requested`, `human_reviewed`, and `accepted`; accepted promotion
  requires `human_reviewed` or `accepted`. Artifact `depends_on` accepts local
  artifact IDs and explicit external references beginning with `external:`.
  Artifact `sources` accepts structured source metadata entries with `kind`,
  `title`, `authors`, `year`, `doi`, `arxiv`, `url`, `theorem_number`, `page`,
  and `notes`. Artifact `formalizations` accepts strict formal declaration
  reference entries with `system`, `library`, manifest-ID `library_ref`,
  `import_path`, `symbol`, `declaration_kind`, `status`, `check_mode`,
  `expected_type`, and `notes`.
  Artifact `alignment` accepts semantic alignment review metadata. Artifact
  `verification_policy` accepts formal-link, Lean-check, and alignment-review
  policy metadata. Formalization references are separate from `evidence`; this
  schema does not add formal-link CLI commands or verifier execution, but G10,
  context packs, and the deterministic index/query surfaces read this metadata.
  Artifact-level `failure_log` is optional and records durable failed-attempt
  memory with strict origin, attempt-kind, status, timestamp, ID, required-text,
  and repository-local non-accepted evidence-path validation. It does not add
  failure-log CLI commands and does not grant proof, verifier, review, gate, or
  promotion authority.
- `schemas/formal_library.schema.json`: formal library manifest schema for
  pinned external Lean library metadata. It requires `schema_version: 1` and at
  least one library entry with `id`, `name`, `system`, `git`, `commit`,
  `lean_version`, and `lake_manifest`; `notes` is optional. This schema is
  metadata-only and does not imply Lean, lake, CSLib, or mathlib execution.
- `schemas/issue.schema.json`: issue YAML schema.
- `schemas/review.schema.json`: review YAML schema.
- `schemas/verifier.schema.json`: verifier result schema.
- `schemas/verifier_evidence.schema.json`: verifier evidence record v1 schema.
  It serializes verifier output records with stable evidence IDs, optional
  artifact/claim IDs, verifier kind, tool metadata, command/cwd metadata,
  normalized `pass`/`fail`/`error`/`skipped` result, reason code, optional log
  paths, optional checker hashes, creation timestamp, and limitations. It does
  not authorize human review, accepted writes, or promotion.
- `schemas/counterexample_evidence.schema.json`: checked counterexample
  evidence record v1 schema. It serializes durable review evidence for a
  checked counterexample candidate with candidate source, check method,
  checked result, support references, checker label, timestamp, and
  limitations. It does not authorize human review, accepted writes, accepted
  refutation, or promotion.
- `schemas/research_strategy.schema.json`: strategy plan v1 schema. It
  serializes a generated plan with issue/problem metadata, task graph,
  ranked next steps, the strategy authority notice, and
  `accepted_write_performed=false`. It does not authorize proof, evidence,
  verifier pass, gate pass, human review, accepted status, accepted
  refutation, accepted writes, or promotion.
- `schemas/research_task_graph.schema.json`: strategy task-graph v1 schema.
  It serializes task nodes, task edges, task status, public/private/workspace
  scope labels, expected evidence kinds, related artifacts, failure-log
  entries, candidate counterexamples, checked evidence references,
  research-run IDs, commands, input paths, write paths, non-authoritative
  task references, and notes. It does not execute tasks or grant write
  authority to accepted KB paths.
- `schemas/task.schema.json`: agent task YAML schema.
- `schemas/orchestrator_run.schema.json`: orchestrator run state schema.
- `schemas/worker_bundle_v2.schema.json`: strict reducer-oriented worker
  bundle schema. It requires `bundle_id`, `task_id`, `worker_role`,
  `created_at`, `summary`, `used_artifacts`, `used_sources`, `claims`,
  `proposed_artifacts`, `verification_requests`,
  `failures_or_counterexamples`, `risk_flags`, `next_steps`, and
  `confidence`, while accepting optional `assumptions`, `uncertainty`,
  `failed_attempts`, legacy string `counterexamples`, typed
  `counterexample_candidates`, and `dependency_questions` for
  backward-compatible failure/counterexample preservation. Typed candidates
  carry candidate IDs, optional target claims, construction summaries,
  evidence paths, verifier-request IDs, status, and limitations; checked
  statuses require at least one evidence path. The schema does not authorize
  accepted writes, review-state changes, verifier results, accepted
  refutations, worker execution, or promotion.

### Formal Library Manifest Files

- `formal-libs/lean-libraries.example.yaml`: example Lean formal library
  manifest. The example includes `lean-core`, `cslib-main`, and
  `mathlib-main` manifest IDs. It uses illustrative commit/version values and
  `example.invalid` repositories for CSLib/mathlib entries. It is a template
  for pinned metadata, not evidence that Lean, CSLib, or mathlib was fetched,
  built, or checked.

### Workspace Config Files

- `cosheaf.toml`: optional repository-root workspace configuration file.
  Absence preserves legacy single-root behavior.
- `[workspace] name`: workspace display name.
- `[[kb]] name`: KB root name.
- `[[kb]] path`: repository-relative KB root path.
- `[[kb]] readonly`: whether write commands may modify that root.
- `[[kb]] priority`: integer priority used for deterministic root ordering and
  reporting.
- `[policy] private_can_depend_on_public`: whether private artifacts may depend
  on public artifacts.
- `[policy] public_can_depend_on_private`: whether public artifacts may depend
  on private artifacts.
- `[policy] accepted_requires_source`: whether accepted public artifacts require
  complete structured source metadata in configured public KB roots.

## Registration Rule

Future public interface changes must be recorded here. Public interfaces include CLI commands, Python APIs, artifact schemas, gate result formats, verifier adapter contracts, context pack formats, and documented file layouts.
