# ADR 0030: Reviewable Research Workflow MVP

## Status

Accepted for v0.9.0.

## Context

v0.8.0 delivered librarian, orchestrator FSM, whitelisted action registry, non-dry-run local loop execution, worker profiles, and deterministic memory feedback. The next useful capability is a single end-to-end reviewable research workflow: issue -> librarian context -> FSM plan -> bounded local loop -> evidence/failures -> draft artifact proposal -> review handoff -> benchmark/eval.

## Decision

v0.9.0 adds cosheaf workflow CLI that wires existing Cosheaf primitives into one deterministic workflow record. Every step records inputs/outputs/authority-notice. Workflow records, draft proposals, and review handoffs remain review context only. No accepted writes, human review creation, verifier/gate mutation, or promotion authority.
