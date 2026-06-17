# Research Loops

## Overview

Research loops provide structured memory for bounded, multi-attempt research workflows. A research loop tracks multiple attempts to solve a research problem, recording failures, evidence, and learned directions.

## Key Concepts

### ResearchLoop

The main loop model coordinates multiple bounded attempts targeting one issue.

**Fields:**
- `loop_id`: Unique loop identifier
- `issue_id`: Target issue ID
- `status`: Lifecycle state (`active`, `paused`, `finalized`)
- `attempts`: Ordered list of attempts
- `max_attempts`: Maximum attempts allowed (1-100, default 10)
- `budget`: Resource budgets (tokens, time, etc.)
- `created_at`: Loop creation time
- `finalized_at`: When loop was finalized
- `notes`: Operator notes
- `authority_notice`: Authority disclaimer

### ResearchLoopAttempt

One bounded attempt within a research loop.

**Fields:**
- `attempt_id`: Unique attempt identifier
- `loop_id`: Parent loop identifier
- `status`: Lifecycle state (`planned`, `running`, `completed`, `failed`, `abandoned`)
- `planned_direction`: What this attempt intends to explore
- `started_at`: When execution started
- `completed_at`: When execution finished
- `actions`: Actions executed during this attempt
- `failures`: Failures encountered
- `evidence`: Evidence artifact IDs or file paths
- `next_direction`: Recommendation for next attempt if this fails
- `authority_notice`: Authority disclaimer

### AttemptFailureRecord

Structured failure record for one attempt.

**Fields:**
- `tags`: Failure classification tags
- `description`: Human-readable failure explanation
- `evidence`: Evidence paths or artifact IDs
- `occurred_at`: When this failure occurred

**Failure Tags:**
- `verifier_fail`: Verifier rejected the artifact
- `gate_fail`: Gate check failed
- `dependency_missing`: Required dependency not available
- `proof_gap`: Proof has logical gaps
- `resource_exhausted`: Budget or resource limit reached
- `blocked_external`: Blocked by external factor
- `invalid_direction`: Planned direction was invalid
- `other`: Other failure type

## Storage

Research loops are stored under `.cosheaf/research-loops/`:

```
.cosheaf/research-loops/
  <loop-id>/
    loop.json                    # Main loop record
    attempts/
      <attempt-id>.json          # Individual attempt records
```

## CLI Commands

### Start a loop

```bash
cosheaf research-loop-start <issue-id> [--max-attempts 10]
```

Creates a new research loop for the given issue.

### Show a loop

```bash
cosheaf research-loop-show <loop-id>
```

Displays loop details in JSON format.

### List all loops

```bash
cosheaf research-loop-list
```

Lists all research loops in the repository.

### Append an attempt

```bash
cosheaf research-loop-append-attempt <loop-id> <planned-direction>
```

Adds a new planned attempt to the loop.

### Finalize a loop

```bash
cosheaf research-loop-finalize <loop-id> [--reason "..."]
```

Marks the loop as finalized.

## Critical Constraints

Loop attempts **cannot**:
- Write to `kb/accepted/`
- Create human review records
- Mutate verifier results
- Leak private content in public mode
- Bypass gatekeeper checks

Loop success **never** means accepted status. All outputs require explicit human review and promotion.

## Example Workflow

```bash
# Start a loop
cosheaf research-loop-start issue.proof-of-concept

# Append attempts
cosheaf research-loop-append-attempt loop.proof-of-concept.20260617-120000 "Try direct construction"

# Show loop state
cosheaf research-loop-show loop.proof-of-concept.20260617-120000

# Finalize when done
cosheaf research-loop-finalize loop.proof-of-concept.20260617-120000 --reason "Solution found"
```

## Design Principles

1. **Bounded Attempts**: Each loop has a maximum attempt limit
2. **Structured Failure**: Failures are classified with tags and evidence
3. **Memory Persistence**: All attempts and failures are recorded
4. **No Auto-Promotion**: Loop success does not grant accepted status
5. **Human Authority**: All accepted knowledge requires human review

## Future Extensions

- Attempt budget tracking
- Failure pattern analysis
- Loop quality metrics
- Cross-loop learning
- Automated direction suggestion (with explicit bounds)
