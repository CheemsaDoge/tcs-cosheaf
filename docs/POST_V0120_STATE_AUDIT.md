# Post-v0.12.0 State Audit

Date: 2026-06-18

This audit starts V18 after the published `v0.12.0 Research Memory Learning +
Benchmark Suite v1` closeout. It is a scope-freeze audit only. It does not
change runtime behavior, schemas, artifact status, verifier behavior, gates,
promotion policy, public KB content, or workspace-template behavior.

## Release Evidence

- Package metadata reports `0.12.0`.
- `python -m cosheaf.cli version --json` reports `0.12.0`.
- Git tag `v0.12.0` exists.
- GitHub release is published:
  <https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.12.0>.
- Annotated tag object:
  `be58f818f3f8dd75803f514b74acd7485ade2f69`.
- Tagged main commit:
  `8c5e5651acf290883488785b553f623742fca1f6`.
- Post-tag release smoke from `@v0.12.0` passed during release closeout.

## Three-Repo State

- `tcs-cosheaf` main records the v0.12.0 publication closeout.
- `tcs-cosheaf-workspace-template` active install/demo pins use `v0.12.0`.
- `tcs-kb-public` CI/docs install the framework from `v0.12.0`.
- Open PR audit at V18 kickoff: no open PRs across the three repositories.
- Open issue audit at V18 kickoff:
  - stale framework issue #462 was closed as completed V17 work;
  - framework issue #474 tracks this V18 scope-freeze task;
  - workspace-template and public KB had no open issues.

## Capability Baseline

The v1.0.0 baseline starts from the published V14-V17 surfaces:

- reviewable workflow records, draft proposals, handoffs, and evals;
- checker registry, cross-check evidence reports, gap reports, and evals;
- bounded external-operator campaigns, task/result packets, scans, handoffs,
  and evals;
- deterministic memory update sidecars;
- benchmark suite v1;
- comparative reports;
- static Markdown/JSON review reports;
- workspace-template demos for the published workflow lines;
- public KB policy guards for workflow, checker, campaign, research-loop, and
  operator outputs.

## Authority Boundary

The authority boundary is unchanged:

- no automatic theorem proving;
- no automatic accepted promotion;
- no AI-as-human-review;
- no default hosted LLM runtime;
- no accepted writes from workflow, campaign, memory, benchmark, report,
  checker, operator, or provider outputs;
- no source metadata fabrication;
- no informal/formal semantic-alignment claim from Lean `#check`;
- skipped, unsupported, unavailable, and inconclusive rows are not passes.

## V18 Entry Decision

The next line is V18 / `v1.0.0 AI Math Collaborator MVP`. The scope is frozen
to packaging, polishing, documenting, auditing, and releasing the existing safe
research harness as a stable MVP. Broad feature expansion is deferred until
after v1.0.0.

