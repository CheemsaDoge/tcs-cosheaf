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

## Relationship To Existing Surfaces

### WorkerBundle `failed_attempts`

WorkerBundle `failed_attempts` are run/task outputs. They are useful for
reducers and review request generation, but they are not automatically durable
on a target artifact.

Artifact `failure_log` entries should preserve the relevant subset of those
attempts when a human or controlled CLI path decides that the memory belongs on
the artifact. The bridge must preserve agent/provider origin and must not
create review authority.

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
