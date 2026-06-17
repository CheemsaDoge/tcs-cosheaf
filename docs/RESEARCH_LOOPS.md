# Research Loops

Research loops are bounded, issue-scoped runtime records for multi-attempt
research workflows. They help an external operator record attempts, preserve
failed directions, and keep evidence organized without changing knowledge
authority.

Research loop success never means accepted status. Loop records are review
context only. They are not proof, verifier pass, gate pass, human review,
accepted knowledge, source metadata, or promotion authority.

## Scope

Implemented through Phase C.1:

- core DTOs for loops, attempts, budgets, decisions, stop conditions, failure
  records, evidence summaries, policy findings, next actions, and review
  summaries;
- runtime JSON storage under `.cosheaf/research-loops/`;
- `events.jsonl` creation and bounded event append;
- CLI JSON smoke path for `start`, `show`, `append-attempt`, `list`, and
  `finalize`;
- safety checks for accepted KB paths, authority overclaims, hidden-reasoning
  fields, terminal attempt requirements, ordered attempts, and public-mode
  private references.
- deterministic runner and external operator protocol surface:

- `cosheaf research-loop next <loop-id> --json`;
- `cosheaf research-loop step <loop-id> --json`;
- `cosheaf research-loop run <loop-id> --max-attempts <n>
  --wallclock-minutes <n> --dry-run --json`;
- `cosheaf research-loop export-task <loop-id> --out <path> --json`;
- `cosheaf research-loop import-result <loop-id> --input-json <path> --json`;
- DTOs for previous-failure summaries, next/step/run results, operator task
  packets, operator result imports, and imported operator failures.

These C.1 commands are still review-context infrastructure. They do not call
hosted providers, run arbitrary shell commands, mark review, create verifier
passes, run gates, write accepted knowledge, or promote artifacts. `run`
currently supports dry-run planning only; non-dry-run local execution remains
explicitly refused until a later deterministic implementation.

Not implemented yet:

- attempt-memory clustering;
- scanner CLI;
- loop handoff export beyond explicit operator task JSON packets;
- hosted provider calls;
- automatic theorem proving or Lean semantic alignment.

## Runtime Layout

Research loops write ignored runtime files only:

```text
.cosheaf/research-loops/
  <loop-id>/
    loop.json
    events.jsonl
    attempts/
      <attempt-id>.json
```

The `.cosheaf/` directory is ignored by Git. Review-context export, when
implemented later, must remain explicit and non-authoritative.

## Models

`ResearchLoop` is the top-level container for one issue. It records:

- `loop_id`
- `issue_id`
- `status`: `created`, `running`, `blocked`, `finalized`, `abandoned`, or
  `failed`
- `budget`
- `attempts`
- `decisions`
- `stop_conditions`
- timestamps and authority notice

`ResearchLoopAttempt` records one bounded attempt. Terminal attempts must be
inspectable:

- `succeeded` attempts require `result_summary` or evidence;
- `failed`, `inconclusive`, and `abandoned` attempts require structured
  failures;
- `blocked` attempts require `blocked_reason` or structured failures;
- all terminal attempts require `completed_at`.

`AttemptFailureRecord` is first-class memory. It records:

- `attempted_direction`
- `why_it_failed`
- `evidence_for_failure`
- `related_artifacts`
- `related_previous_attempts`
- `counterexample_candidate_ids`
- `checked_counterexample_ids`
- `verifier_or_gate_errors`
- `should_retry`
- `retry_conditions`
- `avoid_in_future`
- `tags`
- `signature`

Other DTOs:

- `ResearchLoopBudget`
- `ResearchLoopStopCondition`
- `ResearchLoopDecision`
- `AttemptEvidenceSummary`
- `AttemptPolicyFinding`
- `AttemptNextAction`
- `LoopReviewSummary`

JSON schemas live under `schemas/` for each DTO family.

## CLI

Start a loop:

```bash
cosheaf research-loop start --issue <issue-id> --json
```

Use a deterministic ID when needed:

```bash
cosheaf research-loop start --issue issue.example --loop-id loop.issue.example --json
```

Show a loop:

```bash
cosheaf research-loop show <loop-id> --json
```

List loops:

```bash
cosheaf research-loop list --json
```

Append an attempt from JSON:

```bash
cosheaf research-loop append-attempt <loop-id> --input-json attempt.json --json
```

Finalize a loop:

```bash
cosheaf research-loop finalize <loop-id> --reason "operator stopped" --json
```

Terminal status can be changed explicitly:

```bash
cosheaf research-loop finalize <loop-id> --status failed --json
```

Preview the deterministic next action:

```bash
cosheaf research-loop next <loop-id> --json
```

Record one planning-step event:

```bash
cosheaf research-loop step <loop-id> --json
```

Dry-run bounded planning without writing source-of-truth state:

```bash
cosheaf research-loop run <loop-id> \
  --max-attempts 5 \
  --wallclock-minutes 30 \
  --dry-run \
  --json
```

Export a repository-local external-operator task packet:

```bash
cosheaf research-loop export-task <loop-id> \
  --out .cosheaf/research-loops/<loop-id>/operator_task.json \
  --json
```

Import a structured external-operator result as a loop attempt:

```bash
cosheaf research-loop import-result <loop-id> \
  --input-json operator_result.json \
  --json
```

`export-task` writes only the requested task packet plus a bounded loop event.
`import-result` writes a runtime attempt under `.cosheaf/research-loops/`.
Neither command writes `kb/accepted/`, creates human review, mutates verifier
results, marks a gate pass, or promotes artifacts.

## External Operator Packet

An operator task packet contains:

- `loop_id`
- `attempt_id`
- `issue_id`
- `objective`
- `allowed_actions`
- `forbidden_actions`
- `context_refs`
- `relevant_artifact_cards`
- `previous_failures_to_avoid`
- `required_outputs`
- `budget`
- `stop_conditions`
- `review_handoff_instructions`

The packet is an instruction boundary for an external operator. It is not an
agent runtime and does not grant new write authority.

An operator result import expects structured JSON with:

- `attempted_direction`
- `actions_taken`
- `artifacts_referenced`
- `drafts_created`
- `checks_run`
- `failures`
- `candidate_counterexamples`
- `checked_counterexamples`
- `evidence_refs`
- `next_recommendation`
- `claimed_authority_flags`
- `result_summary`

Every value in `claimed_authority_flags` must be false. The import rejects
accepted-write references, human-review claims, promotion claims, verifier-pass
claims, gate-pass claims, and hidden-reasoning fields.

## Attempt JSON Example

```json
{
  "attempt_id": "loop.issue.example.attempt.1",
  "loop_id": "loop.issue.example",
  "attempt_number": 1,
  "status": "failed",
  "planned_direction": "try direct induction",
  "completed_at": "2026-06-17T12:00:00+00:00",
  "actions_taken": ["cosheaf validate", "cosheaf gate run"],
  "failures": [
    {
      "failure_id": "failure.loop.issue.example.attempt.1",
      "attempt_id": "loop.issue.example.attempt.1",
      "attempted_direction": "try direct induction",
      "why_it_failed": "the induction hypothesis is too weak",
      "evidence_for_failure": ["reviews/runs/failure.json"],
      "related_artifacts": ["claim.example"],
      "related_previous_attempts": [],
      "counterexample_candidate_ids": [],
      "checked_counterexample_ids": [],
      "verifier_or_gate_errors": ["G6 skipped is not pass"],
      "should_retry": true,
      "retry_conditions": "strengthen the invariant first",
      "avoid_in_future": "do not retry without a stronger invariant",
      "tags": ["insufficient_evidence"],
      "signature": "direct-induction:weak-hypothesis",
      "occurred_at": "2026-06-17T12:00:00+00:00"
    }
  ],
  "evidence": {
    "evidence_refs": ["reviews/runs/failure.json"],
    "related_artifacts": ["claim.example"]
  }
}
```

If `loop_id`, `attempt_id`, or `attempt_number` are omitted from
`append-attempt` input, the CLI fills deterministic defaults based on the
target loop and next sequence number. The resulting record is still validated
before writing.

## Boundaries

Research loops cannot:

- write to `kb/accepted/`;
- create human review;
- mutate verifier results;
- create gate pass evidence;
- promote artifacts;
- treat skipped results as passes;
- store hidden reasoning fields;
- claim accepted status or promotion authority.

Public-mode attempts reject private references such as `kb/private/...` or
private-scoped IDs. Private research mode is explicit and still non-authoritative.

## Verification

The regression suite covers:

- model serialization;
- schema file presence for Phase B and C.1 DTO families;
- invalid terminal transition;
- accepted-path rejection;
- missing result/failure rejection;
- deterministic storage paths;
- public-mode private-reference rejection;
- CLI JSON smoke for start/show/append/finalize.
- deterministic `next`;
- `run --dry-run` writes no source-of-truth files;
- `step` writes one planning event;
- task-packet export with previous failures surfaced;
- operator-result import and failure-memory update;
- operator-result import rejection for accepted writes, authority overclaims,
  and missing result/failure evidence;
- budget exhaustion stop conditions.

Phase D remains future work: attempt-memory indexing, repeat-failure detection,
loop scanner CLI, and loop handoff export have not landed in C.1.
