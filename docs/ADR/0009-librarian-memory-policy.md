# ADR 0009: Deterministic Librarian Memory Policy

## Status

Accepted

## Context

TCS-Cosheaf already has Git-backed artifact YAML, workspace-aware storage,
validation, gatekeeper checks, deterministic index rebuilds, dependency graph
construction, formal-link metadata surfaces, context-pack generation, and a
local task harness. The next longplan phase adds a librarian/memory layer.

This layer is useful because context packs and future orchestration need
retrieval that is bounded, auditable, and aware of public/private KB policy.
The risky alternative is to add an agent-style runtime that reads arbitrary
repository content, summarizes freely, and hands large context dumps to workers
before the project has deterministic memory contracts.

The project invariants require:

- YAML remains source of truth.
- Sidecars are rebuildable.
- Public/private filtering is enforced.
- Skipped verifier results are not passes.
- Accepted public knowledge requires source metadata and human review.
- Workers and agents cannot write accepted artifacts directly.
- Formal links are metadata unless a checker actually verifies them.

## Decision

Define the Phase 3 librarian as deterministic-first retrieval infrastructure.

The librarian will produce artifact cards, retrieval rankings, graph weights,
and retrieval audit records from existing repository data. It will not create
claims, edit artifacts, perform human review, promote artifacts, or merge
worker output.

The memory policy is recorded in `docs/MEMORY_POLICY.md` and establishes:

- hot, warm, and cold memory tiers;
- artifact-card fields;
- retrieval request/result shapes;
- score-breakdown requirements;
- memory graph node and edge kinds;
- sidecar locations under `.cosheaf/memory/`;
- public/private filtering rules;
- the no-whole-repo-dump rule;
- the librarian authority boundary.

Future implementation PRs should follow this order:

1. Add typed card and retrieval models.
2. Build cards deterministically from existing YAML/index data.
3. Add lexical or SQLite FTS retrieval before embeddings.
4. Add deterministic graph weights and PageRank.
5. Add issue-conditioned retrieval.
6. Integrate cards into context-pack v2.

## Consequences

The librarian starts as infrastructure, not autonomy. It can be tested with
local fixtures, deterministic index output, fake run records, and no hosted
LLM calls.

Context packs can become more useful while staying bounded: default outputs are
cards, and full artifact pulls require explicit policy plus audit records.

Public/private filtering becomes a first-class retrieval boundary rather than
a post-hoc UI choice. Public-only retrieval must exclude private records and
private-derived summaries.

The memory sidecars can speed up retrieval and ranking without becoming
project truth. If sidecars are deleted or corrupt, they can be rebuilt from
YAML and deterministic indexes.

The approach delays embeddings, hosted model calls, and free-form agent
behavior until deterministic retrieval behavior is reviewable and tested.

## Non-Goals

- Do not implement librarian code in this ADR task.
- Do not add hosted LLM execution.
- Do not add a web service or web UI.
- Do not add automatic theorem proving or autoformalization.
- Do not add external Lean library `#check` behavior.
- Do not change artifact schema or gate semantics in this ADR.
- Do not let memory sidecars become source of truth.
- Do not let the librarian promote accepted artifacts or mark human review.
- Do not treat formal links, graph scores, retrieval scores, or context-pack
  inclusion as proof.

## Follow-Up Requirements

Each implementation step must be a separate issue, branch, and PR. Public CLI,
Python API, schema, sidecar layout, context-pack format, or gate behavior
changes must update `context/INTERFACE_REGISTRY.md` and tests in the same PR.

Any future ranking-weight change must preserve deterministic output and update
`docs/MEMORY_POLICY.md`. Any future embedding or vector sidecar must remain
optional, rebuildable, and disabled in tests unless backed by deterministic
fixtures.
