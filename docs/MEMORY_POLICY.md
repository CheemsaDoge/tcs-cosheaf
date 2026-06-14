# Memory Policy

This document defines the Phase 3 memory and retrieval policy before the full
librarian runtime is implemented. The core request/result/card data transfer
models, deterministic artifact-card builder, bounded local text search,
rebuildable memory graph sidecar, global PageRank, issue-conditioned ranking,
and context-pack v2 integration now exist under local framework surfaces, but
they remain deterministic metadata and handoff surfaces. They are not a claim
that embedding retrieval, hosted LLM workers, a worker runtime, automatic
theorem proving, or any Lean result proves informal/formal alignment. External
Lean-library `#check` results, when produced by a separate optional verifier,
remain verifier metadata rather than retrieval truth.

The policy is deterministic-first. The librarian may retrieve, rank, summarize,
and audit existing repository records. It must not create new claims, modify
artifacts, perform human review, run promotion, or write accepted knowledge.

## Scope

The memory layer sits between the current storage/index/graph surfaces and the
agent/context-pack surfaces.

It may read:

- Git-backed YAML artifacts, issues, reviews, and source notes.
- Deterministic index outputs such as `.cosheaf/index.sqlite`.
- Dependency graph output.
- Verifier result metadata and local task/run metadata when available.
- Rebuildable sidecar files under `.cosheaf/memory/`.

It may write only rebuildable or auditable sidecars under `.cosheaf/memory/` by
default. Durable facts remain in YAML records reviewed through the existing
artifact lifecycle.

## Memory Tiers

### Hot Memory

Hot memory is the bounded material placed in a current prompt, context pack, or
worker input. By default it contains artifact cards rather than full artifact
YAML.

Hot memory may include full artifact text only when a worker role or explicit
request allows it. Full artifact pulls must be counted and recorded in the
retrieval audit. The audit must distinguish cards-only payloads from payloads
that also pulled full artifacts, and every full-artifact pull must record the
caller role and policy scope that justified it.

### Warm Memory

Warm memory is recent, workspace-local retrieval state that can be rebuilt or
discarded without losing project truth. It includes:

- recent issue-conditioned retrieval cache entries;
- recent run feedback used as weak ranking signals;
- recent successful or failed artifact-use signals;
- temporary summary records derived from YAML and index data.

Warm memory is not source of truth. Cache corruption must not break
`cosheaf validate` or `cosheaf gate`.

### Cold Memory

Cold memory is the durable repository state:

- artifact YAML;
- issue YAML;
- review records;
- source notes;
- formalization metadata;
- verifier result records;
- deterministic SQLite index output;
- dependency graph facts derived from YAML.

Cold memory is authoritative only where the underlying YAML or persisted review
record is authoritative. Generated indexes and graph snapshots are still
rebuildable views.

## Artifact Cards

Artifact cards are compact retrieval units. They are the default librarian
output and the default context-pack v2 input. Cards should be enough for
triage, ranking, and routing without dumping full artifacts into a prompt.

The Pydantic model for this contract is `cosheaf.memory.ArtifactCard`.
Card fields are:

```yaml
id: string
path: string
root_scope: public | private | workspace | framework
type: definition | theorem | claim | conjecture | proof | proof_attempt | construction | algorithm | reduction | counterexample | experiment | review | verifier | issue | source_note
status: raw | draft | locally_tested | adversarially_tested | machine_checked | human_reviewed | accepted | refuted | obsolete | superseded
title: string
summary: string
domain: [string]
tags: [string]
depends_on: [string]
sources: [string]
review_state: string
verifier_state: string
formalization_state: string
failure_count: integer
recent_failure_directions: [string]
trust_score: number
retrieval_score: number
why_relevant: string
risk_flags: [string]
can_pull_full: boolean
```

Card summaries must be derived from existing records or explicitly labeled as
generated summaries. A generated summary does not change the artifact
statement, review state, status, verifier state, or accepted state.

`cosheaf memory cards` builds these cards from current repository YAML metadata
and prints compact card output by default. It does not print full artifact YAML,
does not print artifact statements, and does not write `.cosheaf/memory/`
sidecars. The command accepts `--json`, `--status <status>`, and optional
`--issue <issue-id>` filters. Issue filtering is limited to direct
`related_artifacts` in the issue record. Graph-conditioned ranking is provided
by `cosheaf memory search` and the context-pack v2 integration rather than the
card-listing command.

Artifact cards also expose concise artifact-level failure memory metadata when
an artifact has `failure_log` entries. `failure_count` is the number of stored
failure-log entries, and `recent_failure_directions` contains a bounded,
deterministically ordered list of recent attempted directions. These fields are
retrieval/context hints only. They are not proof, verifier success, human
review, checked counterexample evidence, accepted status, gate success, or
promotion evidence.

`cosheaf memory search "query"` searches the same compact cards with
deterministic local scoring. It uses an in-memory SQLite FTS5/BM25 table when
available and falls back to deterministic lexical scoring when FTS5 is not
available. It also builds an in-memory memory graph to blend
issue-conditioned Personalized PageRank, global PageRank, freshness, quality,
and penalty signals into the default ranking formula. The command accepts
`--json`, `--status <status>`, optional `--issue <issue-id>` seeds,
repeatable `--seed-artifact <artifact-id>`, repeatable
`--pin-artifact <artifact-id>`, `--include-refuted`, `--include-obsolete`, and
`--explain`. JSON output is a `RetrievalResult` with `RetrievedArtifactCard`
entries, score breakdowns, and audit metadata. Text output remains card-level
and does not print full artifact YAML or statements; `--explain` prints score
components and relevance reasons. The command does not write
`.cosheaf/memory/` sidecars, does not create accepted knowledge, and does not
perform embeddings, full-artifact pulls, hosted LLM calls, or formal checking.
Failure-log directions are included in the searchable card text with explicit
failure-memory relevance reasons and a warning that failure memory is not
authority. Matching failure memory does not change `trust_score`,
`QualityPrior`, review state, verifier state, artifact status, gate results, or
promotion eligibility.

## Retrieval Request Schema

The initial retrieval request is a deterministic local data structure. The
Pydantic model for this contract is `cosheaf.memory.RetrievalRequest`, with
JSON serialization available through Pydantic and the model `to_json()` helper.

```yaml
schema_version: 1
query: string
issue_id: string | null
seed_artifacts: [string]
pinned_artifacts: [string]
allowed_scopes:
  - public
  - private
  - workspace
  - framework
allowed_statuses:
  - accepted
  - human_reviewed
  - machine_checked
  - locally_tested
  - draft
include_refuted: false
include_obsolete: false
max_cards: 20
max_full_artifacts: 0
role: librarian | orchestrator | reasoner | verifier | formalizer | literature_scout | counterexampleer | construction_searcher
```

Defaults must be conservative:

- public-only requests must not include private cards;
- orchestrator requests default to `max_full_artifacts: 0`;
- draft/private/refuted/obsolete material appears only when requested or
  issue-relevant and visibly flagged;
- accepted-only requests must exclude draft and private material unless the
  caller explicitly widens scope.

## Retrieval Result Schema

Retrieval results are ordered card lists with score explanations and audit
metadata. The Pydantic models for this contract are
`cosheaf.memory.RetrievalResult`, `RetrievedArtifactCard`, `ScoreBreakdown`,
`FullArtifactPull`, `RetrievalExclusion`, and `RetrievalAudit`.

```yaml
schema_version: 1
request_id: string
generated_at: datetime
index_fingerprint: string
cards:
  - card: ArtifactCard
    score_breakdown:
      retrieval_hybrid: number
      personalized_pagerank: number
      global_pagerank: number
      quality_prior: number
      freshness: number
      penalty: number
      total: number
    why_relevant:
      - string
full_artifact_pulls:
  - artifact_id: string
    path: string
    reason: string
audit:
  filters_applied:
    - string
  excluded:
    - artifact_id: string
      reason: string
  warnings:
    - string
```

The result must make filtering and ranking decisions inspectable. It must not
silently hide a public/private policy exclusion or make a skipped verifier look
like a pass.

## Context Pack V2

`cosheaf context build <issue-id>` and `cosheaf context show <issue-id>` now
use artifact-card retrieval before rendering issue handoff context. The default
role is `orchestrator`, and the default full-artifact budget is
`max_full_artifacts: 0`, so the main context remains cards-only unless the
caller explicitly widens the budget.

Context pack v2 writes the existing handoff files plus:

- `FULL_ARTIFACTS.md`: empty by default except for a statement that no full
  artifacts were pulled. When `--max-full-artifacts <n>` is greater than zero,
  this file contains at most `n` explicit full YAML pulls.
- `RETRIEVAL_AUDIT.json`: deterministic request, retrieval, score, exclusion,
  warning, context payload shape, and full-artifact-pull metadata.

The CLI accepts:

- `--role <role>` to record the retrieval caller role.
- `--max-cards <n>` to bound the card search before issue-local filtering.
- `--max-full-artifacts <n>` to explicitly allow bounded full YAML pulls.
- `--public-only` to exclude private cards and private artifact IDs from the
  rendered context and retrieval audit.

Retrieved cards are filtered again through issue-local relevance before they
are rendered in context packs. This preserves the previous direct-reference,
dependency-neighbor, domain-match, and tag-match behavior while using the
librarian score as card metadata. Retrieval scores and graph signals remain
ranking metadata only; they do not authorize promotion, human review,
verification claims, or public/private policy bypasses.

The retrieval audit includes a `context_payload` object with `card_count`,
`full_artifact_count`, and `content_mode`. `content_mode` is `cards_only` when
no full artifact YAML was pulled and `cards_with_full_artifacts` when an
explicit full-artifact budget produced at least one full pull. Full-artifact
pull records include a reason string naming the explicit budget, retrieval
role, policy scope (`public_only` or `workspace`), and maximum pull count. This
metadata is audit context only; it does not make the pulled content accepted,
reviewed, verified, or safe to send to a provider.

Context-pack artifact-card lines and `RETRIEVAL_AUDIT.json` include
`failure_count` and `recent_failure_directions` for visible cards. This is a
compact failed-attempt memory cue, not the structured failure section planned
for later work. Public-only context packs must still exclude private artifacts,
private artifact IDs, and private failure-log text from rendered files and
retrieval audit details.

## Ranking Formula

The default ranking formula is:

```text
Score(q, a) =
  0.50 * RetrievalHybrid(q, a)
+ 0.20 * PersonalizedPageRank(q, a)
+ 0.15 * GlobalPageRank(a)
+ 0.10 * QualityPrior(a)
+ 0.05 * Freshness(a)
- Penalty(a)
```

Interpretation:

- `RetrievalHybrid` combines deterministic lexical retrieval, SQLite FTS/BM25
  when available, and optional embeddings only in later phases.
- `PersonalizedPageRank` starts from the current issue, seed artifacts, pinned
  artifacts, and recent successful runs.
- `GlobalPageRank` is calculated deterministically from the memory graph.
- `QualityPrior` prefers accepted, source-reviewed, human-reviewed, and
  verifier-passed artifacts over weaker records, without treating skipped
  verification as pass.
- `Freshness` may lightly prefer active-issue and recent-run context, but must
  not override trust and policy filters.
- `Penalty` covers private leakage risk, missing source metadata where relevant,
  failed verifier results, refuted/obsolete status unless requested, and draft
  artifacts when accepted-only context is required.

Implementations must emit score breakdowns. Exact constants can change only
through a focused PR that updates this document and relevant tests.

`cosheaf memory search` now populates the implemented components of this
formula:

- `RetrievalHybrid` from SQLite FTS/BM25 or lexical card matching.
- `PersonalizedPageRank` from the issue node, issue `related_artifacts`,
  explicit seed artifacts, pinned artifacts, and recent successful task runs
  when available.
- `GlobalPageRank` from the same deterministic memory graph algorithm exposed
  by `cosheaf memory graph pagerank`.
- `QualityPrior` from existing card trust metadata.
- `Freshness` from recent successful task-run context for the current issue.
- `Penalty` from policy caution signals such as private, draft, refuted,
  obsolete, superseded, and verifier-failure flags.
- Failure-memory keyword matches contribute only to `RetrievalHybrid` with
  explicit caution labels. They do not increase `QualityPrior` or
  `trust_score`.

The formula weights are configurable through the Python
`RetrievalScoreWeights` interface. The CLI uses the documented defaults.
Refuted, obsolete, and superseded artifacts remain excluded unless explicitly
requested. Including them only makes them visible with a penalty; it does not
make them accepted, reviewed, or trustworthy.

## Memory Graph

The memory graph is a deterministic graph over repository and sidecar records.
It extends the current dependency graph with review, source, verifier, and run
signals.

`cosheaf memory graph build` rebuilds `.cosheaf/memory/graph_snapshot.json`
from current repository YAML plus optional local sidecar signals such as gate
reports and task run records. The sidecar includes deterministic node and edge
rows, a graph fingerprint, and warnings that the graph is not source of truth
and formal links remain metadata unless checked by a real checker.

`cosheaf memory graph pagerank` reads the existing graph sidecar and computes a
deterministic weighted PageRank. It does not rebuild the graph implicitly; if
the sidecar is missing, users must run `cosheaf memory graph build` first.

Node kinds:

- `artifact`
- `issue`
- `review`
- `source_note`
- `verifier_result`
- `task_run`
- `worker_bundle`
- `formalization`

Edge kinds:

- `depends_on`
- `supersedes`
- `cites_source`
- `reviews`
- `formalizes`
- `retrieved_for`
- `used_in_success`
- `used_in_failure`
- `rejected_by_verifier`
- `promoted_after_review`
- `same_domain`
- `same_issue_context`

Default edge weights:

- `depends_on`: strong
- `reviews`: strong
- `formalizes`: medium
- `cites_source`: medium
- `retrieved_for`: weak
- `same_domain`: weak
- `used_in_success`: strong positive
- `used_in_failure`: weak negative or caution
- `rejected_by_verifier`: strong negative
- `promoted_after_review`: strong positive

The graph is a ranking surface, not an authority surface. A high graph score
cannot promote an artifact, replace review, or override validation and gates.

## Sidecar Files

Memory sidecars must live under `.cosheaf/memory/` unless a later ADR changes
the location.

Allowed sidecars:

```text
.cosheaf/memory/weights.sqlite
.cosheaf/memory/retrieval_cache.sqlite
.cosheaf/memory/graph_snapshot.json
.cosheaf/memory/vector.index
.cosheaf/memory/vector_manifest.json
```

Rules:

- Sidecars are rebuildable and ignored by Git by default.
- YAML records remain the source of truth.
- Sidecars must not be manually edited as facts.
- Rebuild commands must be deterministic when optional experimental caches are
  disabled.
- Cache corruption must not break core validation or gate behavior.
- Vector indexes, if added later, must have a manifest that records source
  fingerprints and rebuild inputs.
- `.cosheaf/memory/graph_snapshot.json` is implemented as a deterministic
  rebuildable view. It must not be edited as a durable fact.

## Public/Private Filtering

Filtering is a security and research-integrity boundary, not merely a ranking
preference.

Required behavior:

- Public-only retrieval must exclude private records and private-derived
  summaries.
- Public KB artifacts must not depend on private artifacts.
- Private workspace retrieval may include public accepted cards and private
  cards according to the request scope.
- Private cards must be clearly marked with `root_scope: private`.
- Accepted-only retrieval excludes draft, refuted, obsolete, and superseded
  records unless the request explicitly asks for known failures.
- Retrieval results must report excluded records when the exclusion matters for
  auditing.

No public KB contribution, accepted artifact, source note, or human review
record may be derived from private material without explicit maintainer action
outside the librarian.

## No Whole-Repo Dump Rule

The librarian must never hand an entire repository or full KB tree to an agent
by default.

Default limits:

- return cards, not full artifact YAML;
- use bounded `max_cards`;
- use `max_full_artifacts: 0` for orchestrator context by default;
- require explicit role policy or request flags for full artifact pulls;
- record every full artifact pull, context payload mode, role, and policy scope
  in the retrieval audit;
- exclude generated runtime directories such as `.cosheaf/` from source scans
  except for documented sidecar/readback paths.

Large context requests should fail clearly or require explicit overrides rather
than silently widening context.

## Librarian Authority Boundary

The librarian may:

- build artifact cards from existing repository records;
- rank and filter cards;
- compute graph weights;
- generate context-pack candidates;
- write retrieval audit logs and rebuildable memory sidecars.

The librarian must not:

- create new theorems, claims, proofs, or source facts;
- edit artifact YAML;
- move artifact statuses;
- run `cosheaf artifact promote`;
- mark review as human-reviewed;
- treat validation/gate success as human review;
- treat skipped verifier results as passes;
- claim Lean, CSLib, mathlib, SAT, or SMT verification unless a real checker
  result exists;
- claim informal/formal semantic alignment.

Accepted knowledge still enters only through validation, gates, human review,
and explicit promotion.

## Implementation Sequence

Phase 3 should proceed in small PRs:

1. Define Pydantic models for artifact cards, retrieval requests, retrieval
   results, score breakdowns, and audits. Done as model/API groundwork.
2. Build cards deterministically from current artifact/index metadata. Initial
   YAML metadata card builder and `cosheaf memory cards` CLI are implemented.
3. Add lexical/FTS retrieval before optional embeddings. Initial
   `cosheaf memory search` CLI is implemented over artifact cards with SQLite
   FTS5/BM25 when available and deterministic lexical fallback.
4. Add memory graph and deterministic PageRank. Implemented as
   `cosheaf memory graph build` and `cosheaf memory graph pagerank`.
5. Add issue-conditioned Personalized PageRank. Implemented in
   `cosheaf memory search --issue <issue-id> --explain` with explicit seed and
   pin flags.
6. Integrate cards into context-pack v2 with bounded full-artifact pulls.
   Implemented in `cosheaf context build` and `cosheaf context show` with
   cards-only orchestrator defaults, explicit full-artifact budgets,
   public-only filtering, and `RETRIEVAL_AUDIT.json`.

Do not add hosted LLM behavior, agent autonomy, autoformalization, external
Lean library checking, or promotion shortcuts in Phase 3 memory-policy work.
