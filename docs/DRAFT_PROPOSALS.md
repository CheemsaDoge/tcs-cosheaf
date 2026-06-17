# Draft Proposals

Draft proposals convert persisted workflow runtime output into reviewable
candidate material. They are a handoff surface for humans and later review
workflows, not accepted knowledge.

## Commands

Preview a proposal without writing files:

```bash
cosheaf workflow draft-proposal <workflow-id> --dry-run --json
```

Write review-context JSON under a repository-local non-public, non-accepted
path:

```bash
cosheaf workflow draft-proposal <workflow-id> --out .cosheaf/workflows/<workflow-id>/proposal.json --json
```

Write a draft claim artifact under a writable private root:

```bash
cosheaf workflow draft-proposal <workflow-id> --private-root kb/private --artifact-id claim.example.proposal --json
```

The private-root form writes:

```text
kb/private/draft/claims/<artifact-id>.yaml
```

It keeps `status: draft`, records workflow provenance as evidence, and does
not mark the artifact human reviewed.

## Output Model

The Python surface lives in `cosheaf.workflow.proposal` and includes:

- `DraftResearchArtifactProposal`
- `DraftClaimCandidate`
- `DraftProofSketchCandidate`
- `DraftCounterexampleCandidate`
- `DraftEvidenceSummary`
- `DraftKnownFailureSummary`
- `DraftDependencySummary`
- `DraftReviewChecklist`
- `WorkflowProposalProvenance`
- `DraftProposalWriteResult`

Generated proposals include provenance back to the workflow record, event log,
readiness report, and workflow runtime component paths. Candidate claims remain
`draft` and `candidate_claim`.

## Boundaries

Draft proposals are review context only. They are not:

- proof;
- source metadata;
- human review;
- verifier pass;
- gate pass;
- accepted status;
- accepted refutation;
- promotion authority.

The command refuses output paths under `kb/accepted/`, refuses public/readonly
KB output paths, refuses candidate status overclaims, and supports dry-run
execution. Validation, gates, source review, human review, and accepted
promotion remain separate lifecycle steps.
