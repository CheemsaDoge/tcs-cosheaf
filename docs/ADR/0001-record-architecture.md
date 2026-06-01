# ADR 0001: Record Architecture Decisions

## Status

Accepted

## Context

TCS-Cosheaf is intended to become a durable research knowledge base and agent harness. Architectural choices will affect artifact layout, validation semantics, verifier behavior, gate results, and future agent workflows. Chat transcripts are not durable project memory.

## Decision

All architectural decisions must be recorded as ADR files under `docs/ADR/`. Each ADR must include Status, Context, Decision, and Consequences sections.

## Consequences

Future tasks that change architecture must add or update ADRs. Reviewers should reject architecture changes that exist only in code, task notes, or conversation history.
