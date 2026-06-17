# Reviewable Research Workflows

This file is a stable entry point for the V14 reviewable-workflow line.
Operational details live in:

- [Reviewable workflows](WORKFLOWS.md)
- [Draft proposals](DRAFT_PROPOSALS.md)
- [Review handoffs](REVIEW_HANDOFFS.md)

The current workflow path is:

```text
issue -> workflow runtime -> readiness -> draft proposal -> review handoff
```

Workflow runtime records, draft proposals, handoff scan reports, handoff
bundles, and handoff exports are review context only. They do not create proof,
source metadata, human review, verifier pass, gate pass, accepted status,
accepted theorem/refutation, or promotion authority.
