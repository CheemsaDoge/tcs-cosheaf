# Campaigns

V16 introduces bounded research campaigns as runtime review context for many
attempts against one issue.

The boundary is deliberately narrow:

- external operators remain outside Cosheaf;
- campaign records are deterministic sidecars under `.cosheaf/campaigns/`;
- attempts can reference workflows, check reports, proof obligations, draft
  proposals, handoffs, and benchmark reports by safe ID or repository-local
  path only;
- campaign scorecards summarize attempts for inspection; and
- no campaign output creates proof, source metadata, human review, verifier
  pass, gate pass, accepted status, accepted refutation, or promotion
  authority.

## Current Surface

The current B.1 surface is:

```bash
cosheaf campaign start --issue <issue-id> --json
cosheaf campaign show <campaign-id> --json
cosheaf campaign append-attempt <campaign-id> --input-json <path> --json
cosheaf campaign scorecard <campaign-id> --json
cosheaf campaign finalize <campaign-id> --json
```

`campaign start` creates one runtime campaign record. Optional flags include
`--campaign-id <campaign-id>`, `--max-attempts <n>`, and
`--repo-root <path>`.

`campaign append-attempt` validates one `CampaignAttempt` JSON payload, writes
the attempt under the campaign runtime directory, updates `campaign.json`,
refreshes `scorecard.json`, and appends one event line. Attempt records require
one of these outcomes:

- `result`, with `result_summary`;
- `failure`, with `failure_summary`;
- `inconclusive`, with `inconclusive_reason`; or
- `blocked`, with `blocked_reason`.

`campaign scorecard` rebuilds the current deterministic scorecard from the
stored campaign record. It does not run checks or evaluate mathematical truth.

`campaign finalize` marks a campaign terminal with `finalized` by default.
Optional terminal statuses are `abandoned` and `failed`. Finalized campaigns are
immutable for attempt appends.

## Runtime Layout

Campaign runtime records are ignored sidecars:

```text
.cosheaf/campaigns/<campaign-id>/campaign.json
.cosheaf/campaigns/<campaign-id>/attempts/<attempt-id>.json
.cosheaf/campaigns/<campaign-id>/scorecard.json
.cosheaf/campaigns/<campaign-id>/events.jsonl
```

These files are not YAML lifecycle artifacts and are not accepted knowledge.
They should not be copied into public KB accepted paths.

## Model Summary

The B.1 campaign model includes:

- `ResearchCampaign`;
- `CampaignAttempt`;
- `CampaignBudget`;
- `CampaignStopCondition`;
- `CampaignScorecard`;
- `CampaignOperatorPolicy`;
- `CampaignRiskFinding`; and
- `CampaignComparison`.

Campaign statuses are:

```text
created
running
paused
blocked
budget_exhausted
finalized
abandoned
failed
```

`CampaignOperatorPolicy` defaults to private research mode, but still records
`allow_network=false`, `allow_hosted_provider=false`, `allow_shell=false`, and
`allow_accepted_writes=false`.

Public-only attempts reject private references. All attempts reject accepted KB
paths, hidden-reasoning fields, and authority-overclaim fields.

## Non-Goals

The current B.1 implementation does not provide:

- external operator task/result packet export/import;
- campaign runner loops;
- budget-controller execution;
- campaign scanner or handoff reports;
- `cosheaf eval campaign`;
- hosted provider integration;
- arbitrary shell execution;
- automatic proof checking; or
- accepted-artifact promotion.

Those items remain later V16 tasks and must preserve the same authority
boundary when implemented.

## Authority Boundary

Campaign output is review context only. It is not:

- proof;
- source metadata;
- human review;
- verifier pass;
- gate pass;
- accepted status;
- accepted refutation;
- promotion authority.

Validation, gate, checker, workflow, scorecard, or campaign success is not a
substitute for human review. Skipped, unsupported, unavailable, and
inconclusive rows are not passes.
