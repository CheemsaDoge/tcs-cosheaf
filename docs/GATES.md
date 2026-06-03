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

SAT, SMT, and Lean verifier adapters currently exist as optional-tool
skeletons. They check for configured solver/tool availability without adding
hard dependencies on Lean, Z3, cvc5, Sage, or PySAT. When a matching artifact
evidence entry exists but the configured tool is absent, the adapter returns a
`skipped` `VerificationResult`; this is not a pass. If the tool is present, the
adapter still returns `skipped` with a TODO message until real solver invocation
and result parsing are implemented.

Skeleton evidence kinds are:

- SAT: `sat`, `sat_solver`, `sat_checker`
- SMT: `smt`, `smt_solver`, `smt_checker`
- Lean: `lean`, `lean4`, `lean_checker`

The SAT/CNF pilot uses `sat` evidence to exercise this optional-tool path. When
no SAT solver is available, the SAT adapter returns `skipped`, not `pass`; a
separate `python_checker` evidence item provides the local fallback check for
the tiny formula and assignment. This pilot is workflow evidence, not a full
SAT/SMT theorem-proving integration.

### Reproducibility Metadata Gate

Checks executable evidence and verifier results for metadata needed to reproduce
or interpret generated outputs.

The gate is applicable to executable evidence kinds:

- `python_checker`
- `sat`, `sat_solver`, `sat_checker`
- `smt`, `smt_solver`, `smt_checker`
- `lean`, `lean4`, `lean_checker`

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

Checks that the PR records required review items, public interface updates, ADR updates, and verification status.

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
- G6 verifier gate with the Python checker adapter and optional SAT/SMT/Lean skeleton adapters
- G7 reproducibility metadata gate
- G8 PR checklist gate placeholder

G7 is reported as `pass` when applicable executable evidence has reproducibility
metadata, `fail` when required metadata is missing, and `not_applicable` when no
loaded evidence is executable. G8 is intentionally reported as a skipped
placeholder until its implementation exists. G6 is reported as skipped when no
verifier adapters are applicable. `cosheaf gate` with no subcommand also runs
the gatekeeper so the existing `make gate` target performs real gate
enforcement.
