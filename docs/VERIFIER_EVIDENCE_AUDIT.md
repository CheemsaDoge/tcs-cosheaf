# Verifier Evidence Audit

Date: 2026-06-14

Scope: audit the current verifier adapters, gate integration, result records,
formal-link surface, and tests before changing schemas or runtime behavior for
`v0.2.3` Verification Evidence Hardening.

This is a documentation-only audit. It does not change verifier behavior, gate
semantics, promotion policy, schemas, provider/MCP behavior, or KB artifacts.

## Inspected Surface

- `cosheaf/verification/base.py`
- `cosheaf/verification/result.py`
- `cosheaf/verification/registry.py`
- `cosheaf/verification/python_checker.py`
- `cosheaf/verification/sat_adapter.py`
- `cosheaf/verification/smt_adapter.py`
- `cosheaf/verification/lean_adapter.py`
- `cosheaf/verification/lean_external.py`
- `cosheaf/gates/gatekeeper.py`
- `cosheaf/gates/formal_link_gate.py`
- `cosheaf/gates/reproducibility_gate.py`
- `cosheaf/cli.py` promotion lifecycle helpers
- `schemas/verifier.schema.json`
- verifier, gatekeeper, formal-link, Lean, SAT, SMT, promotion, and
  reproducibility tests under `tests/`
- `docs/GATES.md`
- `docs/FORMALIZATION_LINKS.md`

The v5 runbook names `docs/FORMAL_LINKS.md`, but the repository's current
formal-link documentation file is `docs/FORMALIZATION_LINKS.md`. This audit
uses the current repository file and does not create a parallel stale document.

## Adapter Invocation Matrix

The default verifier registry currently registers five adapters in
deterministic name order.

| Adapter | Registered name | Trigger surface | Tool invocation | Missing tool behavior | Notes |
| --- | --- | --- | --- | --- | --- |
| `PythonCheckerAdapter` | `python_checker` | Evidence entries with `kind: python_checker` and a local `path` | Runs the configured Python executable from the repository root, defaulting to the current interpreter. If no custom command is recorded, argv is Python, checker path, artifact source path. | Not an optional external-tool skip path; missing checker script, timeout, or start failure is `error`. | Checks only the first matching evidence item for the artifact. |
| `SatAdapter` | `sat` | Evidence kinds `sat`, `sat_solver`, `sat_checker` | Runs an optional SAT backend, default command `kissat <cnf-path>`, or a fake backend in tests. | `skipped` when matching evidence exists but the backend command is unavailable. | SAT backend outcomes are `sat`, `unsat`, or `unknown`; top-level `unknown` is normalized to `error`. |
| `SmtAdapter` | `smt` | Evidence kinds `smt`, `smt_solver`, `smt_checker` | Runs an optional SMT backend, default command `z3 -smt2 <smt-path>`, or a fake backend in tests. | `skipped` when matching evidence exists but the backend command is unavailable. | SMT backend outcomes are `sat`, `unsat`, or `unknown`; top-level `unknown` is normalized to `error`. |
| `LeanAdapter` | `lean` | Evidence kinds `lean`, `lean4`, `lean_checker`, `lean_proof` | Runs optional plain Lean file checking, default command `lean <lean-path>`. | `skipped` when matching evidence exists but Lean is unavailable. | This is a local plain-file check only. It does not fetch mathlib/CSLib and does not autoformalize statements. |
| `LeanLibraryRefAdapter` | `lean_library_ref` | `formalizations` entries with `system: lean4`, `check_mode: external_library_ref`, and `status: linked` or `checked` | Generates a temporary Lean file containing `import <import_path>` and `#check <symbol>`, then runs `lean <tempfile>` or `lake env lean <tempfile>` when configured. | `skipped` when matching external Lean references exist but the selected backend is unavailable. | Checks only the first applicable formalization per `verify(...)` call. A pass is import/symbol resolution only, not semantic alignment. |

No Coq, Isabelle, SAT theorem-proving integration, SMT theorem-proving
integration, Lean autoformalization, or hosted prover integration exists in the
current registry.

## Normalized Result States

`VerificationStatus` currently defines exactly four normalized statuses:

- `pass`
- `fail`
- `error`
- `skipped`

There is no top-level normalized `unknown` status. `unknown` exists only as a
SAT/SMT backend outcome during solver parsing. The SAT and SMT adapters convert
an `unknown` solver outcome into a normalized `error` `VerificationResult`.

Current meaning:

| Status | Meaning | Blocking in G6 | Promotion impact |
| --- | --- | --- | --- |
| `pass` | The verifier ran and accepted the checked input under that adapter's scope. | No | Does not promote by itself. |
| `fail` | The verifier ran and found an artifact-level mismatch or nonzero checker failure. | Yes | Blocks promotion through the gatekeeper run. |
| `error` | The verifier path hit a runtime, metadata, timeout, missing-file, invalid-output, or startup error before a valid pass/fail judgment. | Yes | Blocks promotion through the gatekeeper run. |
| `skipped` | The verifier did not run, usually because an optional external tool is unavailable or no applicable evidence exists in a direct adapter call. | Nonblocking in G6, reported as skipped | Not a pass; can still leave policy-required checks unsatisfied through G10 or readiness reporting. |

`skipped` is not `pass`. A skipped optional tool result must not be used as
proof, Lean verification, source review, human review, or accepted promotion
evidence.

## Captured Logs And Metadata

`VerificationResult` is the current normalized runtime record. It carries:

- `verifier`
- `artifact_id`
- `status`
- `started_at`
- `ended_at`
- `command`
- `cwd`
- `exit_code`
- `stdout_path`
- `stderr_path`
- `evidence_paths`
- `timeout_seconds`
- `input_paths`
- `output_paths`
- `tool_name`
- `tool_version`
- `seed`
- `environment`
- `message`

Executed Python, SAT, SMT, plain Lean, and external Lean reference checks write
stdout and stderr logs under `.cosheaf/logs/`. Timeout and command-start errors
also write diagnostic stderr logs for adapters that reached the execution
path.

Skipped optional-tool results usually do not create stdout/stderr log files.
They still record command/cwd/evidence/tool metadata where the adapter can
derive it. Current skipped-result metadata is enough for "skipped-not-pass"
reporting, but it is not a durable evidence object.

## Gate Integration

`run_gatekeeper(...)` loads records, runs all applicable default verifier
adapters, then passes the in-memory `verification_results` tuple into:

- G6 verifier gate
- G7 reproducibility metadata gate
- G10 formal-link gate

G6 behavior:

- no applicable verifier results: `skipped`, nonblocking
- any `fail` or `error`: `fail`, blocking
- any `skipped` and no blockers: `skipped`, nonblocking
- all results `pass`: `pass`

G7 behavior:

- applies to executable evidence kinds such as Python checker, SAT, SMT, and
  plain Lean evidence
- requires executed-result metadata such as command, cwd, timeout, input paths,
  stdout/stderr paths, output paths, and tool name
- requires reduced skipped-result metadata for skipped verifier evidence
- fails if executable evidence lacks a matching verifier result or required
  reproducibility metadata

G10 behavior:

- consumes same-run verifier results; it does not execute Lean
- checks static formalization, alignment, verification-policy, and formal
  library manifest metadata
- for `require_lean_check: true`, requires a matching same-run passing Lean
  verifier result for a checked formalization
- skipped, failed, or errored Lean verifier results do not satisfy
  `require_lean_check`

## Promotion Blocking Surface

Promotion currently runs fresh validation and a fresh gatekeeper run. It does
not promote from an old `.cosheaf/reports` sidecar.

Promotion can be blocked by:

- repository validation failures before promotion
- target artifact verifier results with status `fail` or `error`
- any gatekeeper blocking issue, including G6, G7, G9, or G10 blockers
- missing human review state for promotion
- non-accepted dependencies
- missing source metadata for public promotion
- readonly or non-lifecycle path constraints

`BLOCKING_VERIFIER_STATUSES` is currently `{"fail", "error"}`. Skipped
verifier results are not target verifier blockers by themselves, but skipped is
not pass. If an artifact policy requires a Lean check and the required matching
Lean result is skipped instead of passed, G10 blocks because the policy remains
unsatisfied.

## Lean `#check` Boundary

The external Lean library reference checker generates a temporary file:

```lean
import <import_path>
#check <symbol>
```

A passing external Lean reference check means only that the configured Lean
environment resolved the import and symbol for that generated file. It does not
prove:

- the informal statement
- the formal theorem
- semantic alignment between informal and formal statements
- mathlib/CSLib coverage
- source-review quality
- human review
- accepted promotion readiness by itself

This boundary is documented in `docs/FORMALIZATION_LINKS.md` and reinforced in
adapter messages with `alignment not checked`.

Artifact-level `failure_log` entries are separate from verifier evidence.
Promotion-readiness reports may surface unresolved failure memory as
`unresolved_failure_memory` warning reasons so reviewers can see dead
directions, but those warnings are not verifier failures, verifier passes,
checked counterexamples, proof, refutation, human review, or automatic
promotion blockers by themselves.

Checked counterexample evidence is also separate from verifier evidence.
`schemas/counterexample_evidence.schema.json` and
`CheckedCounterexampleEvidenceRecord` record how a specific candidate
counterexample was checked. Such records may reference `verifier_evidence_ids`,
review-record paths, or evidence paths, but they do not create verifier pass,
human review, accepted refutation, accepted status, or promotion authority.
`checked_refutes` requires supporting evidence, and `skipped` checked evidence
must explicitly say skipped is not pass evidence.

## Source Of Truth Versus Sidecars

| Record or file | Current role | Source-of-truth status |
| --- | --- | --- |
| In-memory `VerificationResult` objects from the active gatekeeper run | Immediate normalized verifier evidence consumed by G6/G7/G10 and promotion checks | Source of truth for the active gatekeeper/promotion run |
| `.cosheaf/logs/*` | Runtime stdout/stderr logs referenced by current `VerificationResult` objects | Sidecar evidence logs |
| `.cosheaf/reports/*-gate-report.{json,md}` | Generated gatekeeper reports | Runtime sidecars; ignored by git |
| `reviews/gatekeeper/*` from `--persist-review` | Optional durable review copy of a gatekeeper report | Durable review artifact, but not reused as promotion source of truth |
| `schemas/verifier.schema.json` | Artifact schema for verifier artifact records | Not a schema for runtime `VerificationResult` |
| `schemas/verifier_evidence.schema.json` | v1 schema for serialized verifier evidence records | Added in C.2; not used as promotion source of truth |
| `reviews/evidence/checked-counterexamples/*.yaml` | Durable checked counterexample evidence records | Review evidence only; not human review, accepted refutation, accepted status, or promotion authority |

The current gap is that normalized verifier evidence has a runtime model and
gate-report serialization, but not a dedicated durable evidence schema with a
stable evidence ID.

## Test Coverage Map

| Concern | Coverage |
| --- | --- |
| `VerificationResult` serialization and skipped-not-pass helpers | `tests/test_verification_result.py` |
| Python checker pass/fail/error/log metadata and G6 details | `tests/test_python_checker.py` |
| SAT skipped/pass/fail/error/unknown normalization/log metadata and G6 skipped-not-pass | `tests/test_sat_adapter.py` |
| SMT skipped/pass/fail/error/unknown normalization/log metadata and G6 skipped-not-pass | `tests/test_smt_adapter.py` |
| Plain Lean skipped/pass/fail/error/log metadata and G6 skipped-not-pass | `tests/test_lean_adapter.py` |
| External Lean library reference skipped/pass/fail/error/log metadata, generated `#check`, and alignment boundary | `tests/test_lean_external_adapter.py` |
| Optional verifier skeleton skipped behavior for missing SAT/SMT/Lean tools | `tests/test_optional_verifier_skeletons.py` |
| Gatekeeper G6/G7/G10 integration and skipped-not-pass gate statuses | `tests/test_gatekeeper.py` |
| Promotion blocking for verifier fail/error and nonblocking skipped behavior | `tests/test_promotion_gate_verifier_regressions.py` |
| Reproducibility metadata requirements for executed and skipped verifier results | `tests/test_reproducibility_gate.py` |

Notable existing coverage details:

- `tests/test_verification_result.py::test_skipped_result_serializes_and_is_not_pass`
  asserts skipped serialization and `is_skipped`.
- SAT/SMT tests assert `unknown` backend outcomes become normalized `error`.
- Lean external tests assert generated source contains `import ...` and
  `#check ...`, and successful messages include `alignment not checked`.
- Gatekeeper tests assert skipped G6/G7/G8 statuses are not passes.
- Formal-link gate tests assert `require_lean_check` needs a same-run matching
  passing Lean verifier result and does not accept skipped verifier output.

## C.2 Implementation Boundary

C.2 is narrowed by this evidence:

1. Add a typed, serializable verifier evidence record v1 with a stable
   `evidence_id`.
2. Keep normalized `result` as `pass | fail | error | skipped`; do not add a
   top-level `unknown` unless the semantics are explicitly redesigned.
3. Represent SAT/SMT backend `unknown` as a reason/detail on an `error` result.
4. Add explicit `reason_code` values so readiness reports do not parse free
   text.
5. Preserve current promotion semantics: `fail` and `error` block; skipped is
   not pass and should remain distinguishable.
6. Do not make SAT, SMT, Lean, lake, mathlib, CSLib, or provider tools required
   in CI.
7. Keep external Lean `#check` as import/symbol resolution only; do not claim
   informal/formal semantic alignment.
8. Make runtime result serialization and durable sidecar boundaries explicit in
   schema/docs.
9. Consider recording checker implementation identity or command hash, but do
   not turn it into a trust claim without review policy.
10. Keep provider/MCP surfaces out of the verifier evidence truth path.

The C.2 record remains serialization support for verifier output. It does not
make historical sidecars authoritative, does not replace the fresh gatekeeper
run used by promotion, does not satisfy human review, and does not add a
provider/MCP or accepted-write path.

