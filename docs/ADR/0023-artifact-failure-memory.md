# ADR 0023: Artifact Failure Memory

## Status

Accepted for the `v0.2.4` planning line.

## Context

The `v0.2.3` release made verifier evidence, candidate counterexamples,
promotion-readiness reporting, and failure-preserving review-request generation
more explicit. WorkerBundle v2 can already preserve:

- `failed_attempts`;
- uncertainty and assumptions;
- verification requests;
- legacy counterexample strings;
- typed `counterexample_candidates`;
- dependency questions;
- risk flags; and
- next steps.

`cosheaf review request-from-bundle` can turn those WorkerBundle fields into
draft informational review requests. Verifier evidence records and deterministic
evals also make skipped, failed, and candidate evidence visible without granting
truth authority.

The remaining gap is durability on artifact records. A long-lived artifact can
outlast a task, WorkerBundle, or draft review request, but it does not yet carry
a structured place for failed proof attempts, dead reduction directions, failed
construction attempts, counterexample-search dead ends, formalization stalls,
retrieval misses, or verifier attempts that should not be repeated.

## Decision

Add an artifact-level failure-memory line for `v0.2.4`: Artifact Failure Memory
+ Attempt Traceability.

The central model is an optional artifact field named `failure_log`. It will be
designed before implementation and then added as a backward-compatible optional
field with default empty list.

`failure_log` is durable research memory. It is not:

- proof;
- verifier success;
- human review;
- checked counterexample evidence;
- accepted refutation;
- gate success; or
- accepted-promotion evidence by itself.

Failure memory may be used by retrieval, context packs, review requests, and
promotion-readiness reports to help operators and agents avoid repeated dead
directions. It must remain clearly labeled as failed, blocked, unresolved,
superseded, invalidated, resolved, or archived attempt memory.

## Planned Schema

The first implementation should add an optional top-level artifact field:

```yaml
failure_log:
  - failure_id: failure.example.0001
    attempted_at: 2026-06-14T00:00:00Z
    recorded_by: CheemsaDoge
    origin: human
    attempt_kind: proof_attempt
    target: claim.example
    direction: "Try induction on the number of edges."
    summary: "Attempted to reduce the claim by deleting one edge."
    failed_because: "The induction step does not preserve the required invariant."
    evidence_paths: []
    related_verifier_results: []
    related_counterexample_candidates: []
    next_possible_directions: []
    status: open
    limitations: "This records one failed direction and does not refute the claim."
```

`failure_log` is optional on every artifact and defaults to an empty list.
Existing artifacts without the field must remain valid.

Each entry should require:

- `failure_id`
- `attempted_at`
- `recorded_by`
- `origin`
- `attempt_kind`
- `direction`
- `summary`
- `failed_because`
- `status`
- `limitations`

Optional reference/list fields should default to empty or to the containing
artifact where that is unambiguous. They are references only and do not create
new verifier results, checked counterexamples, review decisions, or promotion
state.

## Field Authority Boundaries

| Field | Validation expectation | Authority boundary |
| --- | --- | --- |
| `failure_id` | Dot-separated lowercase failure identifier unique within the containing artifact. | Identifies a memory entry only; it is not an evidence ID, verifier result ID, review ID, or promotion token. |
| `attempted_at` | Timezone-aware timestamp. | Records when the attempt happened or was reconstructed; it does not prove the attempt was complete or reviewed. |
| `recorded_by` | Non-empty human, agent, provider, verifier, or import label. | Records who or what wrote the entry; it does not create human review. |
| `origin` | One of `human`, `agent`, `provider`, `verifier`, or `imported_bundle`. | Provenance label only. `origin: human` is not equivalent to `review.state: human_reviewed`. |
| `attempt_kind` | One of `proof_attempt`, `reduction_attempt`, `construction_attempt`, `counterexample_search`, `formalization_attempt`, `verifier_attempt`, `retrieval_attempt`, or `other`. | Classifies the attempt so retrieval and review can route it; it does not grant checker or proof authority. |
| `target` | Optional current artifact ID, another local artifact ID, or explicit `external:<ref>` reference. | Identifies what the attempt was aimed at; it does not create a dependency or a refutation. |
| `direction` | Non-empty short attempted direction. | Search/retrieval hint only. |
| `summary` | Non-empty concise account of what was tried. | Explanatory text only; it is not proof or verifier output. |
| `failed_because` | Non-empty reason the attempt failed, stalled, or was abandoned. | Explains a failed direction; it does not refute a claim unless separate checked or reviewed evidence exists. |
| `evidence_paths` | Repository-local paths, normalized and kept out of direct accepted-write targets. | Supporting references only. The referenced files keep their own authority and may still be draft or runtime sidecars. |
| `related_verifier_results` | Stable verifier evidence IDs or repository-local verifier result paths when available. | Links to verifier evidence without changing `pass`, `fail`, `error`, or `skipped` semantics. Skipped remains not pass. |
| `related_counterexample_candidates` | Candidate IDs or repository-local candidate references. | Candidate references only; they are not checked counterexamples or accepted refutations. |
| `next_possible_directions` | Optional non-empty strings. | Advisory follow-up hints only; they do not assign tasks or create obligations. |
| `status` | One of `open`, `superseded`, `invalidated`, `resolved`, or `archived`. | Lifecycle state of the memory entry only. `resolved` does not mean the artifact is proven, refuted, reviewed, or accepted. |
| `limitations` | Non-empty statement explaining why the entry should not be overread. | Required anti-overclaiming field; it does not weaken other validation, gate, review, verifier, or promotion requirements. |

The schema should reject entries that try to encode authority in free text or
reference fields, for example claiming human review, verifier pass, accepted
status, checked refutation, or promotion readiness without the ordinary
corresponding records and workflows.

## Relationship To Existing Surfaces

### WorkerBundle `failed_attempts`

WorkerBundle `failed_attempts` are run/task outputs. They are useful for
reducers and review request generation, but they are not automatically durable
on a target artifact.

Artifact `failure_log` entries should preserve the relevant subset of those
attempts when a human or controlled CLI path decides that the memory belongs on
the artifact. The bridge must preserve agent/provider origin and must not
create review authority.

The key distinction is scope and curation:

- WorkerBundle `failed_attempts` are produced by one worker run and may include
  raw provider or local-agent output.
- Artifact `failure_log` entries are durable artifact metadata and should be
  intentionally added through a controlled draft/write path.
- Importing from a WorkerBundle can propose entries, but it must not
  automatically approve, promote, or mark the target artifact reviewed.
- Agent/provider-originated entries must remain labeled as such after import.

### Draft Review Requests

Draft review requests generated from WorkerBundle output are review context.
They can include failed attempts, counterexample candidates, uncertainty, and
limitations, but they do not mutate the target artifact and do not mark human
review.

Artifact `failure_log` entries are artifact-local memory. They may cite review
request paths as evidence, but they must not convert a draft review request
into human review or promotion readiness.

### Verifier Evidence

Verifier evidence records are outputs of executed checkers, adapters, or
documented manual review paths. Failure-log entries may refer to verifier
evidence by ID or path, but they are not verifier results.

A skipped verifier remains skipped. A failed verifier remains failed. A
failure-log entry cannot turn either one into a pass.

### Counterexample Candidates

WorkerBundle typed `counterexample_candidates` preserve proposed or checked
candidate metadata for review. Artifact failure logs may refer to candidates by
ID, but they must not duplicate a candidate as a checked refutation unless a
separate checked-counterexample or reviewed-refutation workflow exists.

### Promotion Readiness

Promotion-readiness reports may surface unresolved failure-log entries as
warnings or evidence notes. They should not make every failure-log entry an
automatic blocker by default. If the underlying issue is already blocking
because of verifier failure, missing review, source metadata, dependency risk,
or gate policy, that existing reason remains the source of authority.

### Public KB Accepted Artifacts

Accepted public KB artifacts may include failure memory only through ordinary
public-KB discipline:

- complete source metadata where policy requires it;
- human review where policy requires it;
- passing validation and gates;
- accepted or explicit external dependencies; and
- explicit promotion through the normal lifecycle path.

Validation/gate success is not a substitute for human review, and a
`failure_log` entry is not a substitute for source metadata, proof, verifier
evidence, or review. Public-KB maintainers may decide that a reviewed failed
direction is useful historical context, but unreviewed agent/provider failure
logs must not be dumped into accepted public artifacts.

## Consequences

Positive:

- Humans and agents can see what has already been tried before repeating a
  failed proof, reduction, construction, formalization, retrieval, verifier, or
  counterexample-search direction.
- Failure memory becomes durable with the artifact instead of being scattered
  only across transient bundles or review requests.
- Context packs and memory search can surface failed directions explicitly and
  with scope labels.

Costs and constraints:

- The artifact schema becomes larger and needs careful validation.
- Public/private scoping must be preserved so private failure memory does not
  leak into public-only context.
- The feature needs security regression tests because failure logs are an
  attractive place for authority spoofing.
- Public KB policy must explain when failure logs are appropriate in accepted
  public artifacts.

## Rejected Alternatives

### Keep Failure Memory Only In WorkerBundle

Rejected because WorkerBundle records are run/task scoped. They do not provide
artifact-local durable memory for future users who inspect the artifact without
the originating bundle.

### Treat Draft Review Requests As The Failure Memory Store

Rejected because draft review requests are review context and may target tasks,
bundles, or claims indirectly. They should not become the canonical place for
artifact-local failed directions.

### Make Failure Logs Promotion Blockers By Default

Rejected because a failed attempt is often useful historical context, not a
current correctness blocker. Blocking should come from existing authority
surfaces: validation, gates, verifier results, review policy, dependency
policy, and source metadata requirements.

### Make Failure Logs Required On All Artifacts

Rejected because the first implementation must be backward compatible with all
existing artifacts and public KB content. `failure_log` should be optional with
default empty list.

## Required Follow-Up

- Define the exact `failure_log` schema and authority boundaries before runtime
  implementation.
- Add Pydantic and JSON Schema support while preserving existing artifact
  compatibility.
- Add read-only inspection CLI before controlled writes.
- Add controlled draft write paths with dry-run and accepted-write refusal.
- Bridge WorkerBundle failures into failure-log proposals without granting
  authority.
- Surface failure logs in memory, context packs, and promotion-readiness
  reports with explicit labels.
- Add workspace and public KB policy documentation.
- Add security and eval coverage before release readiness.
