# Release Checklist

This checklist is for the `v0.1.1` Formal Link Layer support release. The
project is still pre-MVP; the tag is a reproducible framework baseline for
public KB and workspace-template repositories that want formal-link metadata,
not a production-stability claim.

## CI

- [ ] `make lint`
- [ ] `make typecheck`
- [ ] `make test`
- [ ] `make validate`
- [ ] `make gate`
- [ ] GitHub Actions CI passes on the v0.1.1 release PR.
- [ ] Human review approves the v0.1.1 release PR.

## License

- [x] `LICENSE` contains Apache License 2.0.
- [x] README license text states Apache License 2.0.
- [x] `pyproject.toml` project metadata uses `Apache-2.0`.

## Docs

- [x] README describes the current implemented framework surface.
- [x] README states that `v0.1.1` is the Formal Link Layer support release.
- [x] README and Formal Link docs state that Cosheaf does not replace CSLib or
  mathlib.
- [x] Formal Link docs state that the support is metadata plus gate,
  context-pack, index, and query surfaces only.
- [x] Formal Link docs state that external Lean `#check` for CSLib/mathlib
  references remains future work.
- [x] `docs/ROADMAP.md` does not list implemented SQLite query APIs as future
  work.
- [x] `context/CURRENT_MILESTONE.md` describes the v0.1.0 release-candidate
  cleanup state that produced the first framework baseline.
- [x] `context/PROJECT_STATE.md` records the v0.1.1 Formal Link Layer support
  release boundary.
- [x] `context/INTERFACE_REGISTRY.md` records `ArtifactIndexQuery` and the
  read-only SQLite query API.

## Demo

- [ ] Run `python scripts/release_smoke.py --source
  git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.1.1` after the release
  tag exists.
- [ ] Run the framework validation and gatekeeper commands against the framework
  repository.
- [ ] Confirm the workspace-template smoke coverage remains part of the test
  suite.
- [ ] After `v0.1.1` exists, validate `tcs-kb-public` and
  `tcs-cosheaf-workspace-template` against the pinned framework tag before
  adding downstream formal-link metadata.

## Tag

- [ ] Merge the v0.1.1 release PR through normal review.
- [ ] Create tag `v0.1.1` on the reviewed merge commit.
- [ ] Push tag `v0.1.1`.
- [ ] Do not retarget public KB or workspace-template CI to `@v0.1.1` until
  this tag exists.

## Known Limitations

- The framework is pre-MVP and not production software.
- No web UI.
- No automatic theorem-proving agent.
- No hosted LLM/model-provider worker execution.
- No full Lean autoformalization.
- No Lean execution for external formal library references.
- No CSLib, mathlib, lake, or Lean dependency is added.
- No external formal library fetching.
- No automatic informal/formal alignment checking.
- No multi-user permission system.
- SAT, SMT, and Lean adapters are intentionally minimal optional invocation
  paths; unavailable tools produce skipped verifier results.
- Formal Link Layer support is metadata-only plus G10, context-pack,
  index/manifest, and read-only query surfaces.
- Accepted-promotion semantics are unchanged beyond ordinary gatekeeper
  blocking behavior.
- Public KB repository integration is local-workspace based; downstream
  repositories should pin to `v0.1.1` after the tag exists instead of tracking
  `main`.
