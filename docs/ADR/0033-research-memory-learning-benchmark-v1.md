# ADR 0033: Research Memory Learning and Benchmark Suite v1

Status: accepted

Date: 2026-06-18

## Context

V16 added bounded external-operator campaigns. Those campaigns make repeated
attempts inspectable through task packets, structured result imports,
scorecards, scans, handoffs, and eval reports. Without a deterministic learning
layer, useful operational signals remain scattered across runtime sidecars and
future attempts cannot benefit from prior failures or successful draft paths.

The project needs memory and benchmarks, but not model training and not another
truth source.

## Decision

V17 will add deterministic research memory learning and benchmark suite v1.

Cosheaf memory will be a rebuildable sidecar system:

- read workflow and campaign runtime records;
- extract allowed memory signals;
- apply bounded deterministic update rules;
- persist weights and update-run explanations under ignored `.cosheaf/`
  paths; and
- expose explanations for retrieval and planning priority.

Cosheaf benchmarks will be deterministic regression evidence:

- retrieval quality;
- context relevance;
- workflow completion;
- checker behavior;
- failure memory use;
- campaign budget control;
- authority boundary behavior;
- public/private boundary behavior; and
- review handoff quality.

## Authority Boundary

Memory weights, benchmark runs, comparison reports, and static reports are not:

- proof;
- source metadata;
- human review;
- verifier pass unless a real checker result explicitly records pass;
- gate pass;
- accepted status;
- accepted theorem/refutation; or
- promotion authority.

Memory weights may influence retrieval or prioritization. They must never
modify YAML artifacts, rewrite artifact statuses, create accepted knowledge, or
override review/promotion workflows.

## Safety Boundary

The default V17 path must not require:

- hosted provider calls;
- API keys;
- network access;
- arbitrary shell execution;
- public KB writes;
- accepted KB writes; or
- private-context leakage in public mode.

Benchmarks must report skipped/unsupported/unavailable separately from pass.

## Consequences

- Prior attempts become operationally useful without turning sidecars into
  truth.
- Regressions in retrieval, workflow, checking, campaign control, and authority
  boundaries become measurable.
- Reviewers can compare attempts and benchmark runs using explicit metrics.
- V18 can focus on v1.0.0 scope freeze and user-facing polish instead of adding
  another broad subsystem.

## Rejected Options

- Training or fine-tuning a model from Cosheaf sidecars.
- Treating memory weights as truth judgments.
- Treating benchmark success as accepted status.
- Mutating YAML artifacts from memory update commands.
- Adding a web dashboard instead of static Markdown/JSON reports.
- Combining V17 memory/benchmark work with the V18 v1.0.0 scope freeze before
  `v0.12.0` is published.
