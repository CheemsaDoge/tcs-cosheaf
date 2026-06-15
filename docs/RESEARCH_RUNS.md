# Research Runs

Research run records are repository-local provenance for external operator
work. They record what a Codex-style operator did through CLI/Git, which files
or evidence records were referenced, and how the run stopped.

They are not proof, verifier pass, gate pass, human review, accepted status, or
promotion authority.

## Runtime And Review Paths

Runtime records are generated sidecars:

```text
.cosheaf/runs/<run-id>/run.json
```

Review exports are controlled, explicit exports:

```text
reviews/runs/<run-id>.yaml
```

`export-review --dry-run` reports the target path without writing. The runtime
record under `.cosheaf/` remains generated output and should not be committed.

## CLI

Start a run:

```bash
cosheaf run start \
  --issue issue.example \
  --operator external \
  --operator-label "Codex CLI" \
  --json
```

Append a command record:

```bash
cosheaf run append-command \
  --run run.issue.example.r20260615.t010000z \
  --input-json command.json \
  --json
```

Append artifact and output references:

```bash
cosheaf run append-artifact \
  --run run.issue.example.r20260615.t010000z \
  --artifact claim.example \
  --mode read \
  --json

cosheaf run append-output \
  --run run.issue.example.r20260615.t010000z \
  --input-json output.json \
  --json
```

Finalize, inspect, export, and plan replay:

```bash
cosheaf run finalize \
  --run run.issue.example.r20260615.t010000z \
  --status completed \
  --stop-reason "full verification ladder passed" \
  --json

cosheaf run show run.issue.example.r20260615.t010000z --json
cosheaf run evidence-report --run run.issue.example.r20260615.t010000z --json
cosheaf run export-review --run run.issue.example.r20260615.t010000z --dry-run --json
cosheaf run export-review --run run.issue.example.r20260615.t010000z --json
cosheaf run replay-plan --run run.issue.example.r20260615.t010000z --json
```

`replay-plan` is read-only. It does not execute commands and does not prove that
a replay has happened.

`append-artifact` defaults to `--mode read`. Use `--mode touched` only for
artifacts that the run actually modified.

## Command Records

Command records store explicit argv lists, repository-local cwd, timestamps,
exit code, normalized status, and optional stdout/stderr sidecar paths or
hashes. Secret-looking argv values are redacted before persistence.

Skipped command records must include a reason that says skipped is not pass
evidence.

## Output Records

Output references can record workspace summaries, context packs, controlled
writes, worker bundles, verifier evidence, checked counterexample evidence,
failure logs, validation reports, gate reports, PR references, issue references,
or other operator notes.

Output paths must be repository-local and cannot point at `kb/accepted/`.
Authority fields such as `human_reviewed`, `review_state`, `accepted`,
`artifact_status`, `verifier_pass`, `gate_pass`, and `promote` are rejected.

## Boundaries

- No provider or MCP behavior is added by research-run records.
- No accepted knowledge is written.
- No human review is created.
- No validation, gate, verifier, SAT, SMT, Lean, lake, or optional-tool skipped
  result is converted into a pass.
- No hidden reasoning, API keys, bearer tokens, `.env` dumps, or full
  environment dumps should be stored.
- Review exports are provenance only and still need ordinary human review,
  validation, gates, verifier policy where applicable, and explicit promotion
  before any accepted-knowledge change.
