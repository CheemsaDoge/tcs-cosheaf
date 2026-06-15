# Post-v0.2.4 to v0.3.0 Kickoff Audit

Status: kickoff audit for issue 332.

This audit starts the `v0.3.0` Checked Evidence + Research Run Loop line after
the published `v0.2.4` Artifact Failure Memory + Attempt Traceability release.
It is a documentation and state audit only. It does not change runtime
behavior, schemas, verifier semantics, provider or MCP behavior, accepted
promotion policy, public/private KB policy, or KB artifacts.

## Baseline

At kickoff:

- `tcs-cosheaf` package metadata and `cosheaf.__version__` record `0.2.4`.
- The public `v0.2.4` tag and GitHub release are published.
- `tcs-cosheaf-workspace-template` active demo and install paths pin
  `tcs-cosheaf@v0.2.4`.
- `tcs-kb-public` CI installs `tcs-cosheaf@v0.2.4`.
- V6 is complete. Artifact-level `failure_log` exists, has read and controlled
  draft-write CLI surfaces, is indexed in memory/context, and remains
  non-authoritative research memory.
- CLI remains the primary interface for external Codex-style operators.
- MCP remains an optional read-only adapter surface and is not required for
  `v0.3.0`.

## Candidate Counterexamples Today

Candidate counterexamples are represented as review-only metadata, not checked
evidence or accepted refutations.

Current surfaces include:

- `WorkerBundleV2.counterexample_candidates` in
  `cosheaf/agent/worker_bundle_v2.py`.
- `CounterexampleCandidate` and `CounterexampleCandidateStatus`, including
  `proposed`, `needs_check`, `checked_false`, `checked_true`, `rejected`, and
  `superseded`.
- Reducer warnings produced by `worker_bundle_review_warnings`.
- Failure/counterexample eval fixtures and docs that preserve candidate
  evidence for review.
- Artifact `failure_log` links to related candidate IDs through controlled
  draft-write and WorkerBundle bridge flows.

Even when a WorkerBundle candidate uses a status name such as `checked_false`
or `checked_true`, it remains bundle-local review metadata. It does not create
durable checked counterexample evidence, verifier evidence, human review,
accepted refutation, accepted status, or promotion authority.

## Missing Checked Counterexample Evidence

The repository does not yet have a dedicated checked-counterexample evidence
surface.

Missing pieces:

- No `cosheaf counterexample evidence ...` CLI group.
- No `cosheaf/verification/counterexample_evidence.py` model.
- No `schemas/counterexample_evidence.schema.json`.
- No controlled staging path such as
  `reviews/evidence/checked-counterexamples/<evidence-id>.yaml`.
- No context-pack or promotion-readiness surface that separately lists
  candidate evidence and checked counterexample evidence.
- No security tests that reject checked-evidence authority spoofing.
- No eval suite that scores candidate-vs-checked separation.

Existing `VerifierEvidenceRecord` v1 records normalized verifier outputs. It is
not a checked counterexample evidence record, not human review, and not
promotion authority.

## Run Logging Today

Run-related logging exists but is fragmented:

- `cosheaf task run <task-id> -- <command>` writes command run records under
  `.cosheaf/tasks/<task-id>/runs/<run-id>/`.
- Local and hosted orchestrator paths write run records under
  `.cosheaf/orchestrator/<issue-id>/runs/<run-id>/`.
- Provider paths write redacted records under `.cosheaf/providers/`.
- `StructuredRunLog` in `cosheaf/agent/run_logging.py` records sanitized
  orchestrator metadata.

These records are useful sidecars, but they are not yet a complete
external-operator research-run provenance ledger. They do not provide one
stable lifecycle for start, append command, append artifact/output, finalize,
show, export review, evidence report, and replay plan. They also do not give a
single controlled export path into reviewable repository files.

## Existing CLI Support For External Operators

The framework already has CLI surfaces that an external operator can drive:

- `cosheaf workspace info`
- `cosheaf validate`
- `cosheaf gate run`
- `cosheaf index rebuild`
- `cosheaf context build` and `cosheaf context show`
- `cosheaf memory cards`, `cosheaf memory search`, and memory graph commands
- `cosheaf task create`, `cosheaf task list`, `cosheaf task complete`, and
  `cosheaf task run`
- `cosheaf draft write-artifact` and `cosheaf draft write-source-note`
- `cosheaf bundle submit`
- `cosheaf review request` and `cosheaf review request-from-bundle`
- `cosheaf artifact failures` and controlled `cosheaf artifact failure ...`
  commands
- `cosheaf promotion readiness`
- `cosheaf orchestrator plan` and controlled orchestrator run paths
- `cosheaf provider list`, `config-check`, `preview-send`, `fake-run`, and the
  deliberately explicit `real-run` path
- optional read-only `cosheaf mcp ...` commands

The missing v0.3.0 layer is a checked-evidence surface and a unified research
run record that tie these operations together without increasing authority.

## Downstream Changes Needed

After the framework checked-evidence and research-run surfaces land, downstream
repositories need aligned updates:

- `tcs-cosheaf-workspace-template` should add an external-operator research-run
  demo that starts a run, records commands, builds context, finalizes the run,
  and exports a review summary without provider calls, MCP requirements,
  accepted writes, or human-review spoofing.
- `tcs-kb-public` should document checked evidence policy and may add at most
  one draft-only example. Accepted public content must still require complete
  source metadata and human review.
- Three-repository smoke/eval coverage should verify candidate-vs-checked
  separation, skipped-not-pass behavior, private leakage prevention, and no
  authority escalation.

## Kickoff Conclusion

The next functional task may start after this kickoff PR merges:

```text
checked-counterexample-evidence-core
```

That task should implement the model, schema, CLI, context/readiness surfacing,
security tests, eval fixtures, and docs in one reviewable PR. It must not
automatically refute artifacts, change accepted status, create human review,
change promotion behavior, call providers, or expand MCP.
