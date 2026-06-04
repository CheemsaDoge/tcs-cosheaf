# Release Checklist

This checklist is for the `v0.1.0` framework release candidate. The project is
still pre-MVP; the tag is a reproducible framework baseline for the public KB
and workspace-template repositories, not a production-stability claim.

## CI

- [ ] `make lint`
- [ ] `make typecheck`
- [ ] `make test`
- [ ] `make validate`
- [ ] `make gate`
- [ ] GitHub Actions CI passes on the release-cleanup PR.
- [ ] Human review approves the release-cleanup PR.

## License

- [x] `LICENSE` contains Apache License 2.0.
- [x] README license text states Apache License 2.0.
- [x] `pyproject.toml` project metadata uses `Apache-2.0`.

## Docs

- [x] README describes the current implemented framework surface.
- [x] `docs/ROADMAP.md` does not list implemented SQLite query APIs as future
  work.
- [x] `context/CURRENT_MILESTONE.md` describes the v0.1.0 release-candidate
  cleanup state.
- [x] `context/PROJECT_STATE.md` records the release cleanup, license policy,
  and tag gate.
- [x] `context/INTERFACE_REGISTRY.md` records `ArtifactIndexQuery` and the
  read-only SQLite query API.

## Demo

- [ ] Run the framework validation and gatekeeper commands against the framework
  repository.
- [ ] Confirm the workspace-template smoke coverage remains part of the test
  suite.
- [ ] After `v0.1.0` exists, validate `tcs-kb-public` and
  `tcs-cosheaf-workspace-template` against the pinned framework tag.

## Tag

- [ ] Merge the release-cleanup PR through normal review.
- [ ] Create tag `v0.1.0` on the reviewed merge commit.
- [ ] Push tag `v0.1.0`.
- [ ] Do not retarget public KB or workspace-template CI to `@v0.1.0` until
  this tag exists.

## Known Limitations

- The framework is pre-MVP and not production software.
- No web UI.
- No automatic theorem-proving agent.
- No hosted LLM/model-provider worker execution.
- No full Lean autoformalization.
- No multi-user permission system.
- SAT, SMT, and Lean adapters are intentionally minimal optional invocation
  paths; unavailable tools produce skipped verifier results.
- Public KB repository integration is local-workspace based; downstream
  repositories should pin to `v0.1.0` after the tag exists instead of tracking
  `main`.
