# ADR 0003: Define an Artifact Status Lattice

## Status

Accepted

## Context

The knowledge base needs to distinguish draft research artifacts from accepted artifacts. Accepted artifacts must be reviewable and must not depend on draft or pre-accepted work. Future workflows may need intermediate states for review, rejected work, superseded work, or archived material.

## Decision

The project will define artifact status as an explicit lattice rather than an informal string. The initial repository invariant is that `kb/accepted/` contains accepted artifacts only, `kb/draft/` contains draft or pre-accepted artifacts only, and accepted artifacts must not depend on draft artifacts.

## Consequences

Future schema and gate work must model status explicitly. Dependency checks must account for status. Any expansion of statuses or allowed transitions must update the artifact schema documentation and, if architectural, add a new ADR.
