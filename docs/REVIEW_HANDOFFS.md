# Review Handoffs

Review handoffs are compact review-context packets. They help a maintainer
inspect what an operator session or reviewable workflow produced, but they are
not source-of-truth knowledge and they do not create review authority.

## Workflow Handoffs

The workflow handoff surface is:

```bash
cosheaf workflow handoff build <workflow-id> --json
cosheaf workflow handoff show <handoff-id> --json
cosheaf workflow handoff scan <handoff-id> --json
cosheaf workflow handoff export <handoff-id> --dry-run --json
```

`build` reads persisted workflow runtime records from
`.cosheaf/workflows/<workflow-id>/`, scans the workflow inputs, and writes:

```text
.cosheaf/workflows/<workflow-id>/handoff.json
.cosheaf/workflows/<workflow-id>/handoff-scan.json
```

The deterministic handoff ID is:

```text
handoff.<workflow-id>
```

The packet includes issue summary, query/objective, librarian context summary,
FSM trace, actions executed, failures and avoided directions, candidate claims,
evidence and limitations, scanner findings, a human-review checklist, and an
explicit non-authority notice. Current handoff bundles also include a compact
`review_gaps` summary derived from the workflow gap report. The gap summary is
review guidance only; it does not mark a defect, close a proof obligation, or
create human review.

`scan` fails closed on blocking findings after emitting JSON. It checks for
accepted-write attempts, private path leakage, hidden reasoning markers, raw
provider payload dumps, API keys/secrets/environment dumps, human-review
overclaims, verifier/gate pass overclaims, source-metadata fabrication, and
accepted theorem/refutation claims without promotion. Skipped workflow results
remain warnings and are preserved as non-pass evidence.

`export --dry-run` reports the deterministic review-context target:

```text
reviews/workflow/<handoff-id>.yaml
```

Dry-run export writes nothing. Non-dry-run export writes only under
`reviews/workflow/` after a clean scan. It rejects accepted KB targets and
does not create human review.

## Operator Handoffs

Operator-session handoffs remain available through:

```bash
cosheaf operator handoff build --session <session-id> --json
cosheaf operator handoff show <handoff-id> --json
cosheaf operator handoff export --handoff <handoff-id> --dry-run --json
cosheaf operator handoff export --handoff <handoff-id> --json
```

They summarize finalized operator sessions and write runtime handoff JSON under
`.cosheaf/operator-sessions/<session-id>/`.

## Authority Boundary

Workflow and operator handoffs are review context only. They are not:

- proof;
- source metadata;
- human review;
- verifier pass;
- gate pass;
- accepted status;
- accepted refutation;
- accepted theorem status;
- promotion authority.

Accepted knowledge still requires normal validation, gates, source metadata
where policy requires it, explicit human review, and controlled promotion.
Cross-check reports, gap reports, and handoff `review_gaps` fields do not
change that lifecycle.
