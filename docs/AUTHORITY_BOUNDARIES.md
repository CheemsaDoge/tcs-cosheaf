# Authority Boundaries

Cosheaf separates review context from accepted knowledge. A command can be
useful without being authoritative.

## Boundary Table

| Surface | Writes | Authority |
| --- | --- | --- |
| `validate` / `gate run` | reports under `.cosheaf/` | workflow checks only; not accepted status |
| context packs | `context/TASKS/` | retrieval context only; not proof |
| workflows and draft proposals | `.cosheaf/workflows/`, optional private draft paths | review context or draft only |
| workflow handoffs / cross-check / gap reports | `.cosheaf/` or `reviews/workflow/` | review context only |
| checker runs | `.cosheaf/checkers/` | checker evidence only; skipped is not pass |
| verifier adapters | `.cosheaf/logs/` and verifier result records | result of that checker only |
| campaigns and operator packets | `.cosheaf/campaigns/` | bounded attempt context only |
| memory updates | `.cosheaf/memory/` | sidecar ranking guidance only |
| benchmarks / comparisons / static reports | `.cosheaf/benchmark-runs/`, reports | regression evidence only |
| provider fake/preview paths | `.cosheaf/` | transport preview or fake output only |
| MCP / skills | adapter docs or optional tool surface | not a source of truth |
| `artifact promote` | accepted KB path | promotion path, still gated by review and policy |

## Non-Authority Rules

- Workflow success is not proof.
- Campaign success is not proof.
- Benchmark success is not proof.
- A checker pass is not human review.
- A Lean `#check` pass means only that the import and symbol resolved.
- Validation/gate success is not accepted status.
- AI output is not human review.
- Source metadata cannot be fabricated from handoff, checker, or benchmark
  output.
- Skipped, unavailable, unsupported, and inconclusive rows are not passes.

## Accepted Knowledge Boundary

Accepted artifacts must enter through the governed artifact lifecycle. They
need the required source metadata, human review where policy requires it,
valid dependencies, validation, gates, and promotion checks. Runtime records,
operator packets, handoffs, benchmark reports, memory sidecars, and provider
outputs must not be copied into accepted KB as substitutes for that process.

See [Artifact lifecycle](ARTIFACT_LIFECYCLE.md),
[Security](SECURITY.md), and [Public/private policy](PUBLIC_PRIVATE_POLICY.md).
