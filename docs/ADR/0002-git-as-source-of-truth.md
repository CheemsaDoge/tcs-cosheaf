# ADR 0002: Use Git as the Source of Truth

## Status

Accepted

## Context

TCS-Cosheaf must preserve research state across agent sessions, local machines, reviews, and CI runs. Conversation history is incomplete, mutable, and unavailable to many future tools.

## Decision

The Git repository is the source of truth for project memory, artifacts, documentation, context files, architectural decisions, and verification evidence. Agents and contributors must read repository files before acting and must write durable state back to the repository.

## Consequences

Project state should be reproducible from a checkout. Task handoffs must point to repository files, not chat-only assumptions. Generated outputs and indexes must be deterministic for a given repository state.
