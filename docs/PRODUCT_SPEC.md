# Product Spec

## Purpose

TCS-Cosheaf is a Git-backed typed knowledge base and agent harness for theoretical computer science research. The product exists to make research artifacts explicit, reviewable, verifiable, and reproducible inside the repository.

## MVP Scope

The MVP includes:

- Git-backed typed knowledge base.
- schema validation.
- artifact loader.
- dependency graph.
- gatekeeper.
- context pack generator.
- verifier adapter interface.
- Python checker adapter.
- minimal optional SAT DIMACS adapter.
- SMT/Lean skeleton adapters.
- small draft pilot artifacts that exercise both Python-checker and optional
  SAT-style evidence paths.
- GitHub Actions CI.

## Explicitly Out of Scope for MVP

The MVP does not include:

- no web UI.
- no model training.
- no automatic theorem proving agent.
- no full Lean autoformalization.
- no multi-user permission system.

## MVP Success Criteria

The MVP should allow a contributor or agent to add typed artifacts, validate them, inspect dependencies, run gates, generate task context, and report verifier results without relying on non-reproducible local state.

The current pilots are intentionally small and draft-only. The graph pilot
demonstrates local Python-checker evidence over a finite graph. The SAT/CNF
pilot demonstrates a tiny satisfiable formula, a recorded assignment, optional
SAT solver evidence that may be skipped or executed when a backend is
available, and a Python fallback checker. These pilots exercise workflow
plumbing; they do not claim new theorems or full automated theorem proving.

## Non-Goals

The project does not attempt to replace peer review, formal proof assistants, or domain expert judgment. It provides a structured substrate for preserving and checking research state.
