# Gates

## Purpose

Gates enforce repository invariants before artifacts or behavior changes are accepted.

## Initial Gates

### Schema Gate

Checks that every discovered YAML record parses and conforms to the current
Pydantic model contracts for artifacts, issues, or reviews.

### ID Uniqueness Gate

Checks that loaded record IDs are globally unique across the repository
discovery roots. In configured workspaces, this includes all configured KB
roots plus repository-local `issues/` and `examples/`.

### Status/Path Gate

Checks that accepted artifacts live only under `kb/accepted/`, draft or
pre-accepted artifacts live under non-accepted paths such as `kb/draft/`, and
terminal failure states are consistent with their terminal paths when present.
In configured workspaces, status/path checks are evaluated relative to the
artifact's configured KB root.

### Dependency Gate

Checks that artifact dependencies are valid, that accepted artifacts do not
depend on draft artifacts, and that public KB artifacts do not depend on private
KB artifacts. Dependency references beginning with `external:` are explicit
external references; they are not required to resolve to local artifacts and do
not satisfy local accepted-artifact dependencies.

## Accepted Promotion Requirements

Moving an artifact into `kb/accepted/` is intentionally not a plain file move.
Accepted promotion is mediated by `cosheaf artifact promote <artifact-id>` so
the following conditions are checked before accepted knowledge is created:

- repository schema/model validation passes;
- artifact IDs remain globally unique;
- the target record is a lifecycle artifact under `kb/`;
- issue, task, and review records are never promoted as lifecycle artifacts;
- the gatekeeper has no blocking issues;
- target verifier results do not contain `fail` or `error`;
- dependency references are either accepted lifecycle artifacts or explicit
  external references such as `external:<reference>`;
- `review.state` is `human_reviewed` or `accepted`;
- accepted public artifacts require complete structured source metadata when
  the workspace policy has `accepted_requires_source = true`;
- the target path is `kb/accepted/<type-dir>/<artifact-id>.yaml` relative to
  the artifact's KB root;
- the promoted artifact is written with status `accepted`, a fresh
  `updated_at`, and deterministic YAML output.

Skipped verifier results are not treated as pass results. They remain recorded
as skipped/nonblocking gatekeeper evidence; optional formal tools therefore
stay optional, but skipped output must not be described as a successful
verification.

Formal declaration references under `formalizations` are schema/model metadata,
not verifier evidence. They are not stored in `evidence`, do not make Lean run
automatically, and do not satisfy target verifier checks for accepted
promotion.

Formal library manifest metadata, such as
`formal-libs/lean-libraries.example.yaml`, pins external library IDs and
versions for reference checking. The manifest does not change gate or promotion
semantics: no gate fetches external Lean libraries or treats a manifest entry
as proof that a symbol exists. Optional external Lean `#check` execution is a
G6 verifier-adapter result when matching formalization metadata is present and
Lean or lake is available.

Direct accepted creation remains refused by `cosheaf artifact create`.
`cosheaf artifact move-status <artifact-id> accepted` also fails clearly
instead of moving anything into `kb/accepted/`. This preserves the invariant
that accepted knowledge is introduced only through the explicit promotion flow.

## Read-Only Promotion Readiness Reports

`cosheaf promotion readiness` explains whether a target artifact, or the
artifacts directly listed on an issue, appear ready for the explicit promotion
workflow. It is a report-only command. It does not move files, does not set
`status: accepted`, does not create human review, and does not replace
`cosheaf artifact promote`.

Supported forms are:

```bash
cosheaf promotion readiness --artifact <artifact-id> --json
cosheaf promotion readiness --issue <issue-id> --json
```

The JSON report includes `accepted_write_performed: false`, the gate report
paths written under `.cosheaf/reports/`, artifact status, KB root readonly
state, review state, source metadata state, target verifier results, and
readiness reasons. Blocking reasons make the command exit nonzero.

The report distinguishes at least these promotion-readiness conditions:

- `missing_review`: `review.state` is not `human_reviewed` or `accepted`.
  AI/provider output cannot satisfy this human-review requirement.
- `failed_verifier`: a target verifier result is `fail` or `error`.
- `skipped_verifier`: a target verifier result is `skipped`. Skipped verifier
  evidence is not a pass; it blocks readiness when the artifact policy requires
  that checker.
- `missing_source_metadata`: a public KB artifact lacks source metadata needed
  for accepted public knowledge under `accepted_requires_source = true`.
- `dependency_risk`: a dependency is missing or not accepted.
- `private_dependency`: a public artifact depends on a private artifact.
- `draft_status`: the target is still raw/draft rather than review-grade
  pre-accepted status.
- `readonly_kb_root`: the target is loaded from a readonly KB root.
- `repository_gate_blocker`: another blocking gatekeeper issue in the
  repository would prevent accepted promotion even if the target artifact looks
  locally ready.

Readiness reports are intentionally conservative and advisory. Promotion still
uses a fresh repository validation and gatekeeper run, still enforces review,
dependency, readonly-root, target verifier, and source-metadata checks, and
still performs the only accepted write.

### Evidence Path Gate

Checks that referenced evidence paths exist, are repository-local, and are appropriate for the artifact status.
Evidence entries marked with `kind: external` or paths starting with `external:`
are treated as external references and are not required to resolve locally.

### Verifier Gate

Runs configured verifier adapters and normalizes results. Missing optional
external tools should produce skipped verifier results, not core system crashes.
See `docs/VERIFIER_EVIDENCE_AUDIT.md` for the current adapter, result-state,
log-capture, gate-integration, promotion-blocking, and test-coverage audit that
precedes the `v0.2.3` verifier evidence record work.

#### Verification Capability Matrix

The current verifier surface is intentionally small and optional-tool friendly.

| Backend | Current status | Evidence kinds or metadata | Default external command | CI requirement | Boundary |
| --- | --- | --- | --- | --- | --- |
| Python checker | Available | `python_checker` | current Python executable | Available through repo-local scripts when evidence is present | Runs repository-local checker scripts and records normalized verifier results. |
| SAT | Minimal optional adapter available | `sat`, `sat_solver`, `sat_checker` | `kissat` | No SAT solver required; unavailable solver is `skipped` | Supports repository-local DIMACS CNF evidence, not full SAT theorem-proving integration. |
| SMT | Minimal optional adapter available | `smt`, `smt_solver`, `smt_checker` | `z3` | No SMT solver required; unavailable solver is `skipped` | Supports repository-local SMT-LIB evidence, not full SMT theorem-proving integration. |
| Lean plain file | Minimal optional adapter available | `lean`, `lean4`, `lean_checker`, `lean_proof` | `lean` | No Lean installation required; unavailable Lean is `skipped` | Checks repository-local plain `.lean` files only when Lean is available. It does not autoformalize natural language. |
| External Lean library references | Optional adapter available | `formalizations` entries with `system: lean4`, `check_mode: external_library_ref`, and `status: linked` or `checked` | `lean`, or `lake env lean` when configured | No Lean or lake installation required; unavailable backend is `skipped` | Generates a temporary file with `import <import_path>` and `#check <symbol>`. It does not fetch CSLib/mathlib, manage checkouts, autoformalize natural language, or prove informal/formal alignment. |
| Coq | Not implemented | None | None | Not required | No current adapter or roadmap item in this repository. |
| Isabelle | Not implemented | None | None | Not required | No current adapter or roadmap item in this repository. |

The verifier adapter interface is defined by `VerifierAdapter`, with:

- `name: str`
- `can_verify(artifact, repo) -> bool`
- `verify(artifact, repo) -> VerificationResult`

`VerificationResult` records verifier name, artifact ID, normalized status,
timestamps, command metadata, working directory, exit code, stdout/stderr log
paths, evidence paths, timeout, input/output paths, tool metadata, optional
random seed metadata, environment notes, and a review message. Status values
are:

- `pass`: the verifier checked the artifact and accepted it.
- `fail`: the verifier checked the artifact and found an artifact-level failure.
- `error`: the verifier or runtime errored before producing a verification
  judgment.
- `skipped`: the verifier did not run, for example because an optional external
  tool is unavailable.

`skipped` is not `pass`, and `error` is not `fail`. External command-backed
verifiers must record the command and working directory they used.

#### Verifier Evidence Record v1

`VerifierEvidenceRecord` is a typed serialization boundary for verifier
outputs. It is derived from a `VerificationResult` through
`VerificationResult.to_evidence_record()` or
`VerifierEvidenceRecord.from_verification_result(...)`.

The v1 record is documented by `schemas/verifier_evidence.schema.json` and
includes a stable `evidence_id`, optional artifact/claim IDs, verifier kind,
tool metadata, command argv, cwd, normalized `result`, explicit `reason_code`,
stdout/stderr/log paths, creation timestamp, optional checker input/output
hashes, and limitations.

The record does not change gatekeeper or promotion semantics. Promotion still
uses a fresh validation and gatekeeper run. A verifier evidence record is not
human review, does not auto-promote accepted knowledge, and does not make
skipped output pass.

The current concrete verifier is the Python checker adapter. It runs artifact
evidence entries with `kind: python_checker` from the repository root, writes
stdout and stderr logs under `.cosheaf/logs/`, enforces a timeout, and records
the command, working directory, exit code, log paths, and evidence paths in a
`VerificationResult`. With the current artifact evidence model, the checker
derives the command as:

- current Python executable
- evidence `path`
- artifact source path

Exit code `0` produces `pass`, a nonzero exit code produces `fail`, and timeout
or missing checker scripts produce `error`.

The SAT verifier adapter supports a minimal optional DIMACS CNF invocation path.
It does not add a hard dependency on PySAT or any external solver binary. The
default backend checks for the configured external command, currently `kissat`,
through PATH detection; tests may inject a fake backend instead of requiring a
real solver in CI. When matching SAT evidence exists but no supported backend is
available, the adapter returns a `skipped` `VerificationResult`; this is not a
pass.

When a SAT backend is available, the adapter verifies that the evidence path is
repository-local, runs the backend from the repository root against the DIMACS
CNF file, writes stdout and stderr logs under `.cosheaf/logs/`, parses
`sat`/`unsat`/`unknown`, and records the input path, backend/tool metadata,
command, working directory, timeout, exit code, stdout/stderr paths, output
paths, and result summary. If the artifact statement has a `CHECKER_DATA`
`expected.satisfiable` value, the adapter reports `pass` only when the solver
result matches it, `fail` on mismatch, and `error` for unknown, timeout, missing
evidence, or runtime errors.

The SAT result-depth fixtures use fake backends so CI does not require a real
SAT solver. They cover satisfiable and unsatisfiable matches, mismatches,
malformed DIMACS surfaced as backend parse-error/`unknown` output, timeout
errors, and unavailable backend skips. Skipped SAT results remain skipped, not
pass, and no fixture turns SAT output into a theorem-proving claim.

The SMT verifier adapter supports a minimal optional SMT-LIB invocation path.
It does not add a hard dependency on Z3, cvc5, or any external solver binary.
The default backend checks for the configured external command, currently `z3`,
through PATH detection; tests may inject a fake backend instead of requiring a
real solver in CI. When matching SMT evidence exists but no supported backend is
available, the adapter returns a `skipped` `VerificationResult`; this is not a
pass.

When an SMT backend is available, the adapter verifies that the evidence path is
repository-local, runs the backend from the repository root against the SMT-LIB
file using command metadata equivalent to `z3 -smt2 <file.smt2>`, writes stdout
and stderr logs under `.cosheaf/logs/`, parses exact `sat`/`unsat`/`unknown`
solver status lines, and records the input path, backend/tool metadata,
command, working directory, timeout, exit code, stdout/stderr paths, output
paths, and result summary. If the artifact statement has a `CHECKER_DATA`
`expected.satisfiable` value, the adapter reports `pass` only when the solver
result matches it, `fail` on mismatch, and `error` for unknown, timeout, missing
evidence, malformed metadata, or runtime errors.

The SMT result-depth fixtures use fake backends so CI does not require a real
SMT solver. They cover `sat` and `unsat` matches, mismatches, `unknown`
results, malformed SMT-LIB surfaced as backend parse-error/`unknown` output,
timeout errors, exact status-line parsing, and unavailable backend skips.
Skipped and unknown SMT results remain non-pass evidence, and no fixture turns
SMT output into a theorem-proving claim.

The Lean verifier adapter supports a minimal optional plain Lean file
invocation path. It does not add a hard dependency on Lean, mathlib, or lake.
The default backend checks for external `lean` through PATH detection; tests may
inject a fake backend instead of requiring Lean in CI. When matching Lean
evidence exists but no supported backend is available, the adapter returns a
`skipped` `VerificationResult`; this is not a pass.

When a Lean backend is available, the adapter verifies that the evidence path is
repository-local, requires the evidence file to exist before backend skipping,
runs the backend from the repository root against the `.lean` file using command
metadata equivalent to `lean <file.lean>`, writes stdout and stderr logs under
`.cosheaf/logs/`, and records the input path, backend/tool metadata, command,
working directory, timeout, exit code, stdout/stderr paths, and output paths.
Exit code `0` reports `pass`, nonzero exit code reports `fail`, and timeout or
command startup errors report `error`. This path does not inspect theorem
semantics beyond Lean's own exit code and does not autoformalize natural
language. It also does not fetch or check external CSLib/mathlib declarations
recorded in `formalizations`.

Optional-tool evidence kinds are:

- SAT: `sat`, `sat_solver`, `sat_checker`
- SMT: `smt`, `smt_solver`, `smt_checker`
- Lean: `lean`, `lean4`, `lean_checker`, `lean_proof`

The SAT/CNF pilot uses `sat` evidence to exercise this optional SAT path. When
no SAT solver is available, the SAT adapter returns `skipped`, not `pass`; when
a backend is available, it can execute the tiny DIMACS CNF evidence and compare
the result with the artifact's expected satisfiability metadata. A separate
`python_checker` evidence item still provides the local fallback check for the
tiny formula and assignment. This pilot is workflow evidence, not a full
SAT/SMT theorem-proving integration.

SMT support remains similarly minimal and optional. It can execute
repository-local SMT-LIB evidence only when a supported backend is available,
defaults to optional `z3`, and does not make skipped SMT checks pass. Lean
support is also minimal and optional: the plain-file adapter can execute
repository-local Lean files only when a supported backend is available, and the
external-library adapter can generate a temporary `import`/`#check` file from
linked formalization metadata. Both default to optional Lean tooling and do not
make skipped Lean checks pass. SAT, SMT, plain Lean, and external Lean
reference adapters remain separate minimal paths.

### Formal Link Metadata Gate Boundary

G1 schema/model validation parses optional `formalizations`, `alignment`, and
`verification_policy` fields. G10 Formal Link Gate then enforces consistency
between those fields, local formal library manifests, and normalized verifier
results when policy requires a Lean check. G10 does not treat formal links,
Lean evidence, or alignment metadata as proof of informal/formal semantic
alignment.

Alignment review is separate from Lean checking. A formal declaration may exist
or a local Lean file may pass while the informal artifact still needs human
review for convention and statement alignment.

G10 is metadata and verifier-result consistency validation. It does not execute
Lean, fetch external libraries, inspect CSLib/mathlib declarations, or require
network access. Optional external `#check` output is recorded by G6 when the
`lean_library_ref` verifier runs; G10 consumes that normalized result in the
same gatekeeper run when policy requires a Lean check. This does not turn G10
into an execution gate, and skipped verifier results are not passes. G10
enforces policy consistency only:

- `require_formal_link: true` requires at least one `formalizations` entry.
- `require_alignment_review: true` requires `alignment.status:
  human_reviewed`.
- `require_lean_check: true` requires at least one formalization with
  `status: checked` and a matching Lean verifier result with status `pass`.
  For `check_mode: external_library_ref`, the matching result must come from
  `lean_library_ref` for the same formalization ID. A plain local Lean pass
  does not satisfy an external-library reference check.
- `lean_required` policy is expected to require both a formal link and a Lean
  check; schema/model validation normally catches violations first.
- `library_ref` values must resolve in a local formal library manifest such as
  `formal-libs/lean-libraries.yaml` or the checked-in example manifest.
  Unknown `library_ref` blocking issues include the available manifest IDs when
  a manifest was loaded, so operators can correct stale or mistyped metadata.
- `import_path` and `symbol` must be non-empty for `linked` and `checked`
  references; model validation normally catches empty values first.
- `alignment.status: rejected` is blocking when alignment review is required
  and is always blocking on accepted artifacts.
- a required formal link whose only formalizations are `broken` or
  `deprecated` is blocking.

G10 warnings are nonblocking and are not proof failures. Current warnings
include formal links present when policy does not require them, planned
formalizations on accepted artifacts, requested alignment review on accepted
artifacts, `broken` or `deprecated` formalizations when another active link is
available or no formal link is required, and `checked` external-library
references that do not yet have verifier-result linkage.

Context-pack display and SQLite/query indexing of formal-link metadata do not
change G10. They expose the same metadata for handoff and local inspection, but
they do not run Lean, load gate reports, or turn formal links into verifier
passes.

Formal library manifests are also metadata-only. The gatekeeper loads a local
manifest only to validate shape and check that artifact `library_ref` values
resolve to manifest IDs. It does not fetch or build external libraries from
manifests, and a manifest entry is not proof that a Lean import or symbol
exists.

### Reproducibility Metadata Gate

Checks executable evidence and verifier results for metadata needed to reproduce
or interpret generated outputs.

The gate is applicable to executable evidence kinds:

- `python_checker`
- `sat`, `sat_solver`, `sat_checker`
- `smt`, `smt_solver`, `smt_checker`
- `lean`, `lean4`, `lean_checker`, `lean_proof`

For executed verifier results, the gate requires:

- `command`
- `cwd`
- `timeout_seconds`
- `input_paths`
- `stdout_path`
- `stderr_path`
- `output_paths`
- `tool_name`
- `exit_code` for `pass` and `fail` results

For skipped verifier results, such as optional external tools that are absent,
the gate requires enough metadata to explain the attempted verifier:

- `command`
- `cwd`
- `evidence_paths`
- `tool_name`

The external Lean library reference checker uses formalization metadata rather
than `evidence` entries. Its verifier result still records reproducibility
metadata, but G7 currently applies to executable evidence kinds under
`evidence`, not to formalization-only references.

Randomized evidence, detected from artifact/evidence text such as
`randomized`, `randomness`, `stochastic`, or `monte carlo`, must include
`seed` metadata in the verifier result. Deterministic artifacts do not require a
seed. Non-executable evidence is reported as `not_applicable`, not `pass`.

### PR Checklist Gate

Checks that an available PR checklist records the required review items. The
gate is local and filesystem-only; it does not call the GitHub API and does not
require network access.

When no checklist source is available, G8 is reported as `skipped` with a clear
reason. This keeps `make gate` and CI-compatible local runs usable before a PR
body exists. Skipped remains distinct from pass.

Use `cosheaf gate run --pr-checklist <path>` to check an explicit markdown file
such as a local PR body draft. When a checklist source is provided, G8 fails if
any required section is missing.

Required markdown sections are:

- `Summary`
- `Changed Files`
- `Tests Run`
- `Risks`
- `Interface Changes`
- `Documentation Changes`
- `Artifact/Schema Changes`
- `Gatekeeper Result`

### Source Metadata Gate

Checks that accepted artifacts in configured public KB roots carry structured,
citable source metadata when `accepted_requires_source = true`.

The gate applies only to artifacts that are all of:

- loaded from a configured KB root named `public`;
- `status: accepted`;
- evaluated under a configured workspace whose policy enables
  `accepted_requires_source`.

Draft public artifacts are not blocked solely for missing source metadata.
Accepted private artifacts are not blocked by this gate unless a later policy
adds that requirement. Without `cosheaf.toml`, legacy single-root mode has no
public KB root, so the gate reports `not_applicable` and preserves existing
single-repository behavior.

Accepted public artifacts must have at least one `sources` entry. Each source
entry must include:

- `kind`
- non-empty `title`
- at least one non-empty `authors` value
- `year`
- at least one citation locator: `doi`, `arxiv`, `url`, `theorem_number`, or
  `page`

External dependency references such as `external:doi/...` are dependency edges,
not citation metadata, and do not satisfy this gate.

## Gate Result Semantics

Gate results should distinguish pass, fail, skipped, and not implemented. A skipped result must explain why the gate could not run. A failed result must preserve enough evidence for review.

## Gatekeeper Reports

`cosheaf gate run` writes both machine-readable JSON and human-readable
Markdown reports. By default, reports are written under `.cosheaf/reports/` so
local runs do not create review noise:

- `.cosheaf/reports/<timestamp>-gate-report.json`
- `.cosheaf/reports/<timestamp>-gate-report.md`

Use `cosheaf gate run --persist-review` to also copy the same reports under
`reviews/gatekeeper/` for durable review artifacts.

The JSON report contains:

- `verdict`: `pass` or `fail`
- `blocking_issues`
- `nonblocking_issues`
- `summary`
- `started_at`
- `ended_at`
- `gates`

Any blocking issue makes the verdict `fail` and causes a nonzero CLI exit code.
Placeholder gates must be reported as `skipped` or `not_applicable`; they must
not be reported as `pass`.

## Current Implementation Status

`cosheaf validate` now implements the schema/model gate, ID uniqueness gate,
status/path gate, dependency gate, and evidence path gate over YAML records
discovered under the active workspace KB roots plus `issues/` and `examples/`.
Without `cosheaf.toml`, the active KB root remains the legacy `kb/` path.

`cosheaf artifact validate <path>` validates a single YAML file with
file-local schema/model, status/path, and evidence path checks. Whole-repository
checks such as ID uniqueness and dependency existence run through
`cosheaf validate`.

`cosheaf artifact create` creates deterministic artifact YAML records in the
lifecycle tree, refuses duplicate IDs, and runs single-file validation before
reporting success. `cosheaf artifact move-status <artifact-id> <new-status>`
checks the current artifact's status/path consistency, validates the repository
before the move, refuses direct accepted promotion, and writes the moved artifact
with the deterministic YAML writer. In configured workspaces, artifact creation
writes to the writable private KB root by default, and status movement refuses
records loaded from readonly KB roots. `cosheaf artifact promote <artifact-id>`
performs the accepted-artifact promotion workflow described above, refuses
records loaded from readonly KB roots, and is the only implemented CLI path for
moving eligible artifacts into the accepted area of their KB root.

`cosheaf promotion readiness --artifact <artifact-id> --json` and
`cosheaf promotion readiness --issue <issue-id> --json` run a read-only
readiness report over the same repository, gatekeeper, review, dependency,
source-metadata, readonly-root, and target verifier evidence surfaces. The
command may write ordinary runtime gate reports under `.cosheaf/reports/`, but
it does not write accepted artifacts or change artifact status.

`cosheaf gate run` now runs:

- G1 schema gate
- G2 ID uniqueness gate
- G3 status/path gate
- G4 dependency gate
- G5 evidence path gate
- G6 verifier gate with the Python checker adapter, optional minimal SAT DIMACS
  adapter, optional minimal SMT-LIB adapter, optional minimal plain Lean adapter,
  and optional external Lean library reference checker
- G7 reproducibility metadata gate
- G8 PR checklist gate
- G9 source metadata gate for accepted public artifacts
- G10 formal link gate for metadata and verifier-result consistency

Formal-link fields are parsed by G1 and checked for policy consistency by G10.
Checkable linked external Lean references can also trigger G6
`lean_library_ref` verifier results. They do not alter G7 reproducibility
metadata checks or G9 source metadata checks. G10 contributes ordinary
gatekeeper blocking issues, so accepted promotion is blocked only through the
existing gatekeeper blocking issue mechanism.

G7 is reported as `pass` when applicable executable evidence has reproducibility
metadata, `fail` when required metadata is missing, and `not_applicable` when no
loaded evidence is executable. G8 is reported as `skipped` when no PR checklist
source is available, `fail` when an explicit checklist source is missing
required sections, and `pass` when all required sections are present. G9 is
reported as `fail` when accepted public artifacts lack complete source metadata,
`pass` when applicable accepted public artifacts are complete, and
`not_applicable` for legacy mode, disabled policy, or workspaces with no
accepted public artifacts. G6 is reported as skipped when no verifier adapters
are applicable. G10 is reported as `not_applicable` when no artifact has
formal-link policy metadata to check, `fail` when static policy consistency is
violated, and `pass` when applicable formal-link metadata has no blocking
issues; warnings remain nonblocking. `cosheaf gate` with no subcommand also
runs the gatekeeper so the existing `make gate` target performs real gate
enforcement.
