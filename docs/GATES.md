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

Direct accepted creation remains refused by `cosheaf artifact create`.
`cosheaf artifact move-status <artifact-id> accepted` also fails clearly
instead of moving anything into `kb/accepted/`. This preserves the invariant
that accepted knowledge is introduced only through the explicit promotion flow.

### Evidence Path Gate

Checks that referenced evidence paths exist, are repository-local, and are appropriate for the artifact status.
Evidence entries marked with `kind: external` or paths starting with `external:`
are treated as external references and are not required to resolve locally.

### Verifier Gate

Runs configured verifier adapters and normalizes results. Missing optional
external tools should produce skipped verifier results, not core system crashes.

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
language.

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
support is also minimal and optional: it can execute repository-local plain Lean
files only when a supported backend is available, defaults to optional `lean`,
does not make skipped Lean checks pass, and does not implement SAT or SMT. SAT,
SMT, and Lean adapters remain separate minimal paths.

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

`cosheaf gate run` now runs:

- G1 schema gate
- G2 ID uniqueness gate
- G3 status/path gate
- G4 dependency gate
- G5 evidence path gate
- G6 verifier gate with the Python checker adapter, optional minimal SAT DIMACS
  adapter, optional minimal SMT-LIB adapter, and optional minimal Lean adapter
- G7 reproducibility metadata gate
- G8 PR checklist gate
- G9 source metadata gate for accepted public artifacts

G7 is reported as `pass` when applicable executable evidence has reproducibility
metadata, `fail` when required metadata is missing, and `not_applicable` when no
loaded evidence is executable. G8 is reported as `skipped` when no PR checklist
source is available, `fail` when an explicit checklist source is missing
required sections, and `pass` when all required sections are present. G9 is
reported as `fail` when accepted public artifacts lack complete source metadata,
`pass` when applicable accepted public artifacts are complete, and
`not_applicable` for legacy mode, disabled policy, or workspaces with no
accepted public artifacts. G6 is reported as skipped when no verifier adapters
are applicable. `cosheaf gate` with no subcommand also runs the gatekeeper so
the existing `make gate` target performs real gate enforcement.
