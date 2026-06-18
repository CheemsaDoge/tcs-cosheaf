# External Operator Run Loop

This runbook is for Codex-style external operators that use the repository
through CLI and Git. It is not an embedded agent runtime, not an MCP
requirement, and not a hosted provider workflow.

The CLI remains the first machine interface and the human/CI review path
remains the authority boundary.

For a concrete framework-side command sequence, see
[`docs/OPERATOR_WORKSPACE_DEMO.md`](OPERATOR_WORKSPACE_DEMO.md).

## Authority Boundary

Research-run records are provenance only. They are not proof, verifier pass,
gate pass, human review, accepted status, accepted refutation, or promotion
authority.

Checked counterexample evidence is durable review evidence only. A
`candidate_counterexample` is proposed evidence and must not be described as
checked evidence unless a checked evidence record exists. Neither candidate nor
checked evidence automatically changes accepted knowledge.

External operators must not:

- write directly to `kb/accepted/`;
- mark AI output or agent review as `human_reviewed`;
- treat validation, gate, verifier, Lean, SAT, SMT, provider, MCP, memory,
  retrieval, context, or run-record output as human review;
- treat skipped results as passes;
- send private KB context to hosted providers without explicit policy,
  preview, configuration, and operator consent;
- use `codex/`, `codex-`, or other agent prefixes in issue titles, branch
  names, or PR titles unless the maintainer explicitly asks for that prefix.

## Required Loop

Use this sequence for nontrivial issue work when a research-run record is
expected.

1. Read `AGENTS.md`, `context/CURRENT_MILESTONE.md`, the GitHub issue, and
   relevant docs.
2. Create or select one focused GitHub issue.
3. Create one focused branch from current `main`.
4. Start a research run:

   ```bash
   cosheaf research-run start --issue <issue-id> --operator external --json
   ```

5. Inspect workspace state:

   ```bash
   cosheaf workspace info --json
   ```

6. Establish the baseline:

   ```bash
   cosheaf validate --json
   cosheaf gate run --json
   ```

7. Search bounded memory and build context:

   ```bash
   cosheaf memory search "<query>" --issue <issue-id> --json
   cosheaf context build <issue-id> --json
   ```

8. Create or inspect a strategy plan:

   ```bash
   cosheaf strategy plan --issue <issue-id> --from-context context/TASKS/<issue-id> --json
   cosheaf strategy next strategy.<issue-id>.plan --json
   ```

   Strategy plans are guidance only. They do not execute tasks, create
   evidence, mark verifier/gate pass, create human review, write accepted
   knowledge, or authorize promotion.

9. Read the generated context pack when it exists:

   ```text
   context/TASKS/<issue-id>/CONTEXT.md
   context/TASKS/<issue-id>/RELEVANT_ARTIFACTS.md
   context/TASKS/<issue-id>/KNOWN_FAILURES.md
   context/TASKS/<issue-id>/COMMANDS.md
   context/TASKS/<issue-id>/ACCEPTANCE.md
   ```

10. Read known failure memory, candidate counterexamples, checked
   counterexample evidence, verifier evidence, and promotion-readiness output
   when relevant to the issue.
11. Make only issue-scoped edits.
12. Record relevant commands, artifact reads/touches, and controlled outputs
    with:

    ```bash
    cosheaf research-run append-command --run <run-id> --input-json <command.json> --json
    cosheaf research-run append-artifact --run <run-id> --artifact <artifact-id> --json
    cosheaf research-run append-output --run <run-id> --input-json <output.json> --json
    ```

13. Stage draft artifacts, source notes, bundles, failure logs, checked
    evidence, or review requests only through the controlled CLI commands
    documented in `docs/CODEX_WORKFLOW.md` and `docs/AGENT_ACCESS.md`.
14. Re-run the required verification commands:

    ```bash
    make lint
    make typecheck
    make test
    make validate
    make gate
    git diff --check
    ```

15. Finalize and inspect the research run:

    ```bash
    cosheaf research-run finalize --run <run-id> --status completed --stop-reason "<reason>" --json
    cosheaf research-run evidence-report --run <run-id> --json
    cosheaf research-run replay-plan --run <run-id> --json
    ```

16. Preview review export first, then export only when a review record is
    intended:

    ```bash
    cosheaf research-run export-review --run <run-id> --dry-run --json
    cosheaf research-run export-review --run <run-id> --json
    ```

17. Open one PR. The PR must record the run ID/path when a run was used,
    commands run, skipped rows, runtime outputs, limitations, non-goals,
    public/private scope handling, candidate-vs-checked evidence status, and
    the authority boundary.

## Optional MCP Adapter

MCP can expose the same bounded service-layer operations to compatible clients,
but it is optional. CLI commands and CI checks remain the reviewable oracle.

The MCP adapter may list workspace state, validation/gate results, memory
cards/search, context packs, strategy plans, research-run provenance, and eval
smoke results. Controlled MCP tools may stage draft/review/runtime records
through existing service-layer policy checks. They still must not write
accepted knowledge, promote artifacts, mark human review, mutate verifier
results, run arbitrary shell, call hosted providers, or bypass gates.

## Recording Commands

`append-command` accepts a repository-local JSON payload. Store argv lists,
cwd, timestamps, exit code, status, and optional stdout/stderr sidecar paths or
hashes. Do not store secrets, hidden reasoning, full environment dumps, or API
keys.

Skipped command records must include the skipped-not-pass limitation.

## Recording Outputs

`append-output` can reference workspace summaries, context packs, controlled
writes, worker bundles, verifier evidence, checked counterexample evidence,
failure logs, validation reports, gate reports, PR references, issue
references, or concise operator notes.

Output references must stay repository-local and must not target accepted KB
paths. Authority-spoofing fields such as `human_reviewed`, `accepted`,
`accepted_write_performed`, `verifier_pass`, `gate_pass`, and `promote` are
forbidden.

## PR Requirements

Every PR using this loop should include:

- issue number and branch name;
- research run ID and runtime path, or an explicit reason no run record was
  used;
- review export path if `export-review` was used;
- exact verification commands and outcomes;
- generated runtime output locations;
- skipped/unavailable rows, clearly labeled as not pass;
- candidate counterexamples and checked evidence separately labeled when
  applicable;
- confirmation that no accepted write, promotion bypass, human-review spoofing,
  provider/MCP expansion, or automatic theorem-proving claim was added.

