"""Deterministic artifact failure-memory retrieval/governance eval harness."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import field_validator

from cosheaf.core.ids import validate_artifact_id
from cosheaf.memory.models import MemoryModel, MemoryRootScope, RetrievalRole
from cosheaf.memory.search import search_artifact_cards
from cosheaf.storage.repo import RepoContext

DEFAULT_ARTIFACT_FAILURE_MEMORY_EVAL_CASES = (
    Path("evals") / "artifact_failure_memory" / "cases.yaml"
)
ISSUE_ID = "issue.failure-memory.eval"
PUBLIC_ARTIFACT_ID = "claim.failure.public"
PRIVATE_ARTIFACT_ID = "claim.failure.private"
PUBLIC_DIRECTION = "separator induction dead end"
PRIVATE_MARKER = "private-failure-secret-do-not-leak"
NON_AUTHORITY_WARNING = "failure memory is not proof"


class ArtifactFailureMemoryEvalError(ValueError):
    """Raised for expected artifact failure-memory eval loading failures."""


class ArtifactFailureMemoryEvalKind(StrEnum):
    """Supported artifact failure-memory eval scenarios."""

    FAILURE_RETRIEVAL = "failure_retrieval"
    REPEAT_FAILED_DIRECTION = "repeat_failed_direction"
    PUBLIC_SCOPE_BOUNDARY = "public_scope_boundary"
    AUTHORITY_BOUNDARY = "authority_boundary"
    CANDIDATE_COUNTEREXAMPLE_BOUNDARY = "candidate_counterexample_boundary"


class ArtifactFailureMemoryEvalCase(MemoryModel):
    """One deterministic artifact failure-memory eval case."""

    id: str | None = None
    kind: ArtifactFailureMemoryEvalKind
    query: str
    public_only: bool = False
    expect_failure_retrieved: bool = False
    expect_repeat_detected: bool = False
    expect_no_scope_leak: bool = True
    expect_no_authority_violation: bool = True
    expect_no_candidate_mislabel: bool = True

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_artifact_id(value.strip())

    @field_validator("kind", mode="before")
    @classmethod
    def _validate_kind(
        cls,
        value: ArtifactFailureMemoryEvalKind | str,
    ) -> ArtifactFailureMemoryEvalKind:
        return (
            value
            if isinstance(value, ArtifactFailureMemoryEvalKind)
            else ArtifactFailureMemoryEvalKind(value)
        )

    @field_validator("query")
    @classmethod
    def _validate_query(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("query must not be empty")
        return normalized


class ArtifactFailureMemoryEvalSuite(MemoryModel):
    """A small collection of artifact failure-memory eval cases."""

    schema_version: Literal[1] = 1
    cases: list[ArtifactFailureMemoryEvalCase]

    @field_validator("cases")
    @classmethod
    def _validate_cases(
        cls,
        values: list[ArtifactFailureMemoryEvalCase],
    ) -> list[ArtifactFailureMemoryEvalCase]:
        if not values:
            raise ValueError("cases must not be empty")
        return values


@dataclass(frozen=True)
class ArtifactFailureMemoryEvalMetrics:
    """Aggregate artifact failure-memory retrieval/governance metrics."""

    failure_retrieval_recall: float
    repeat_failed_direction_rate: float
    failure_scope_leak_count: int
    failure_authority_violation_count: int
    candidate_counterexample_mislabel_count: int

    def to_dict(self) -> dict[str, int | float]:
        """Return deterministic machine-readable metrics."""
        return {
            "failure_retrieval_recall": self.failure_retrieval_recall,
            "repeat_failed_direction_rate": self.repeat_failed_direction_rate,
            "failure_scope_leak_count": self.failure_scope_leak_count,
            "failure_authority_violation_count": (
                self.failure_authority_violation_count
            ),
            "candidate_counterexample_mislabel_count": (
                self.candidate_counterexample_mislabel_count
            ),
        }


@dataclass(frozen=True)
class ArtifactFailureMemoryEvalCaseResult:
    """One executed artifact failure-memory eval case."""

    id: str
    kind: ArtifactFailureMemoryEvalKind
    query: str
    public_only: bool
    retrieved_artifact_ids: tuple[str, ...]
    retrieved_failure_directions: tuple[str, ...]
    failure_retrieved: bool
    repeated_failed_direction_detected: bool
    repeated_failed_direction_slipped: bool
    scope_leak: bool
    authority_violation: bool
    candidate_counterexample_mislabel: bool
    warnings: tuple[str, ...]
    expected_failure_retrieved: bool
    expected_repeat_detected: bool
    runtime_paths: tuple[Path, ...]
    failures: list[str]

    @property
    def passed(self) -> bool:
        """Return whether this case satisfied every configured expectation."""
        return not self.failures

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic machine-readable case output."""
        return {
            "id": self.id,
            "kind": self.kind.value,
            "query": self.query,
            "public_only": self.public_only,
            "retrieved_artifact_ids": list(self.retrieved_artifact_ids),
            "retrieved_failure_directions": list(self.retrieved_failure_directions),
            "failure_retrieved": self.failure_retrieved,
            "repeated_failed_direction_detected": (
                self.repeated_failed_direction_detected
            ),
            "repeated_failed_direction_slipped": (
                self.repeated_failed_direction_slipped
            ),
            "scope_leak": self.scope_leak,
            "authority_violation": self.authority_violation,
            "candidate_counterexample_mislabel": (
                self.candidate_counterexample_mislabel
            ),
            "warnings": list(self.warnings),
            "expected_failure_retrieved": self.expected_failure_retrieved,
            "expected_repeat_detected": self.expected_repeat_detected,
            "runtime_paths": [path.as_posix() for path in self.runtime_paths],
            "failures": self.failures,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class ArtifactFailureMemoryEvalReport:
    """Scored artifact failure-memory eval suite output."""

    schema_version: Literal[1]
    case_count: int
    passed: bool
    metrics: ArtifactFailureMemoryEvalMetrics
    runtime_paths: tuple[Path, ...]
    cases: list[ArtifactFailureMemoryEvalCaseResult]

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic machine-readable report output."""
        return {
            "schema_version": self.schema_version,
            "case_count": self.case_count,
            "passed": self.passed,
            "metrics": self.metrics.to_dict(),
            "runtime_paths": [path.as_posix() for path in self.runtime_paths],
            "cases": [case.to_dict() for case in self.cases],
        }

    def to_json(self) -> str:
        """Return deterministic JSON for the report."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


def load_artifact_failure_memory_eval_suite(
    path: Path,
) -> ArtifactFailureMemoryEvalSuite:
    """Load an artifact failure-memory eval suite from a YAML file."""
    if not path.exists():
        raise ArtifactFailureMemoryEvalError(
            f"artifact failure-memory eval case file not found: {path}"
        )
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactFailureMemoryEvalError(
            f"cannot read artifact failure-memory eval case file: {exc}"
        ) from exc
    if data is None:
        raise ArtifactFailureMemoryEvalError(
            "artifact failure-memory eval case file is empty"
        )
    try:
        return ArtifactFailureMemoryEvalSuite.model_validate(data)
    except ValueError as exc:
        raise ArtifactFailureMemoryEvalError(
            f"invalid artifact failure-memory eval case file: {exc}"
        ) from exc


def resolve_artifact_failure_memory_eval_case_path(
    context: RepoContext,
    cases_path: Path,
) -> Path:
    """Resolve and constrain the case file path to the repository root."""
    repo_root = context.repo_root
    path = cases_path if cases_path.is_absolute() else repo_root / cases_path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ArtifactFailureMemoryEvalError(
            "artifact failure-memory eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(cases_path).is_absolute():
        raise ArtifactFailureMemoryEvalError(
            "artifact failure-memory eval case file must be repository-local"
        )
    return resolved


def run_artifact_failure_memory_eval_suite(
    context: RepoContext,
    suite: ArtifactFailureMemoryEvalSuite,
) -> ArtifactFailureMemoryEvalReport:
    """Run every artifact failure-memory eval case."""
    case_results = [
        run_artifact_failure_memory_eval_case(context, case, case_index=index)
        for index, case in enumerate(suite.cases, start=1)
    ]
    metrics = _aggregate_metrics(case_results)
    runtime_paths = _unique_runtime_paths(case_results)
    return ArtifactFailureMemoryEvalReport(
        schema_version=1,
        case_count=len(case_results),
        passed=all(case.passed for case in case_results),
        metrics=metrics,
        runtime_paths=runtime_paths,
        cases=case_results,
    )


def run_artifact_failure_memory_eval_case(
    context: RepoContext,
    case: ArtifactFailureMemoryEvalCase,
    *,
    case_index: int = 1,
) -> ArtifactFailureMemoryEvalCaseResult:
    """Run and score one artifact failure-memory eval case."""
    case_id = _case_id(case, case_index)
    workspace_root = _prepare_case_workspace(context, case_id)
    case_context = RepoContext(workspace_root)
    result = search_artifact_cards(
        case_context,
        query=case.query,
        issue_id=ISSUE_ID,
        allowed_scopes=(
            (MemoryRootScope.PUBLIC,)
            if case.public_only
            else (MemoryRootScope.PUBLIC, MemoryRootScope.PRIVATE)
        ),
        role=RetrievalRole.LIBRARIAN,
        max_cards=10,
    )
    result_json = result.to_json()
    retrieved_artifact_ids = tuple(hit.card.id for hit in result.cards)
    retrieved_failure_directions = tuple(
        direction
        for hit in result.cards
        for direction in hit.card.recent_failure_directions
    )
    failure_retrieved = (
        PUBLIC_ARTIFACT_ID in retrieved_artifact_ids
        and PUBLIC_DIRECTION in retrieved_failure_directions
        and _direction_matches_query(case.query, PUBLIC_DIRECTION)
    )
    repeated_detected = (
        PUBLIC_DIRECTION in case.query.lower()
        and PUBLIC_DIRECTION in retrieved_failure_directions
    )
    repeated_slipped = case.expect_repeat_detected and not repeated_detected
    scope_leak = _scope_leak(result_json, retrieved_artifact_ids)
    authority_violation = _authority_violation(result)
    candidate_mislabel = _candidate_counterexample_mislabel(case_context)
    failures = _case_failures(
        case,
        failure_retrieved=failure_retrieved,
        repeated_failed_direction_detected=repeated_detected,
        scope_leak=scope_leak,
        authority_violation=authority_violation,
        candidate_counterexample_mislabel=candidate_mislabel,
    )
    return ArtifactFailureMemoryEvalCaseResult(
        id=case_id,
        kind=case.kind,
        query=case.query,
        public_only=case.public_only,
        retrieved_artifact_ids=retrieved_artifact_ids,
        retrieved_failure_directions=retrieved_failure_directions,
        failure_retrieved=failure_retrieved,
        repeated_failed_direction_detected=repeated_detected,
        repeated_failed_direction_slipped=repeated_slipped,
        scope_leak=scope_leak,
        authority_violation=authority_violation,
        candidate_counterexample_mislabel=candidate_mislabel,
        warnings=tuple(result.audit.warnings),
        expected_failure_retrieved=case.expect_failure_retrieved,
        expected_repeat_detected=case.expect_repeat_detected,
        runtime_paths=(_runtime_case_root(context, case_id),),
        failures=failures,
    )


def _prepare_case_workspace(context: RepoContext, case_id: str) -> Path:
    case_root = context.repo_root / _runtime_case_root(context, case_id)
    workspace_root = case_root / "workspace"
    if case_root.exists():
        _remove_runtime_case_root(context, case_root)
    workspace_root.mkdir(parents=True, exist_ok=True)
    _write_workspace_config(workspace_root)
    _write_yaml(
        workspace_root / "kb/public/accepted/claims/claim.failure.public.yaml",
        _artifact(
            PUBLIC_ARTIFACT_ID,
            status="accepted",
            statement="Public failure-memory retrieval fixture.",
            review_state="accepted",
            failure_log=[_public_failure_log_entry()],
        ),
    )
    _write_yaml(
        workspace_root / "kb/private/draft/claims/claim.failure.private.yaml",
        _artifact(
            PRIVATE_ARTIFACT_ID,
            status="draft",
            statement=f"Private fixture containing {PRIVATE_MARKER}.",
            depends_on=[PUBLIC_ARTIFACT_ID],
            failure_log=[_private_failure_log_entry()],
        ),
    )
    _write_yaml(workspace_root / "issues/open/failure-memory.yaml", _issue())
    return workspace_root


def _write_workspace_config(workspace_root: Path) -> None:
    workspace_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "artifact-failure-memory-eval"',
                "",
                "[[kb]]",
                'name = "public"',
                'path = "kb/public"',
                "readonly = true",
                "priority = 10",
                "",
                "[[kb]]",
                'name = "private"',
                'path = "kb/private"',
                "readonly = false",
                "priority = 20",
                "",
                "[policy]",
                "private_can_depend_on_public = true",
                "public_can_depend_on_private = false",
                "accepted_requires_source = true",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _artifact(
    artifact_id: str,
    *,
    status: str,
    statement: str,
    review_state: str = "requested",
    depends_on: list[str] | None = None,
    failure_log: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": artifact_id,
        "type": "claim",
        "title": artifact_id,
        "domain": ["eval"],
        "status": status,
        "created_at": "2026-06-15T00:00:00Z",
        "updated_at": "2026-06-15T00:00:00Z",
        "authors": ["eval-fixture"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": ["artifact-failure-memory-eval"],
        "statement": statement,
        "evidence": [],
        "sources": [
            {
                "kind": "website",
                "title": "Artifact failure-memory eval fixture",
                "authors": ["TCS-Cosheaf maintainers"],
                "year": 2026,
                "url": "https://example.invalid/tcs-cosheaf/evals",
                "notes": (
                    "Repository-local deterministic eval fixture metadata; "
                    "not mathematical evidence or human source review."
                ),
            }
        ],
        "review": {
            "state": review_state,
            "notes": "Deterministic eval fixture only.",
        },
        "risk": {"level": "low", "notes": "Eval fixture only."},
    }
    if failure_log is not None:
        data["failure_log"] = failure_log
    return data


def _public_failure_log_entry() -> dict[str, Any]:
    return {
        "failure_id": "failure.eval.public.0001",
        "attempted_at": "2026-06-15T00:00:00Z",
        "recorded_by": "eval-fixture",
        "origin": "human",
        "attempt_kind": "proof_attempt",
        "target": PUBLIC_ARTIFACT_ID,
        "direction": PUBLIC_DIRECTION,
        "summary": "The separator induction direction was tried and failed.",
        "failed_because": "The induction hypothesis did not preserve separators.",
        "evidence_paths": [],
        "related_verifier_results": [],
        "related_counterexample_candidates": ["candidate.failure.eval.0001"],
        "next_possible_directions": ["Try a decomposition lemma first."],
        "status": "open",
        "limitations": (
            "Failure memory and candidate reference only; not proof, "
            "refutation, verifier evidence, human review, or checked "
            "counterexample evidence."
        ),
    }


def _private_failure_log_entry() -> dict[str, Any]:
    return {
        "failure_id": "failure.eval.private.0001",
        "attempted_at": "2026-06-15T00:00:00Z",
        "recorded_by": "eval-fixture",
        "origin": "agent",
        "attempt_kind": "proof_attempt",
        "target": PRIVATE_ARTIFACT_ID,
        "direction": f"private repeated direction {PRIVATE_MARKER}",
        "summary": f"Private failure summary {PRIVATE_MARKER}.",
        "failed_because": f"Private failure reason {PRIVATE_MARKER}.",
        "evidence_paths": [],
        "related_verifier_results": [],
        "related_counterexample_candidates": [],
        "next_possible_directions": [],
        "status": "open",
        "limitations": f"Private failure memory {PRIVATE_MARKER}.",
    }


def _issue() -> dict[str, Any]:
    return {
        "id": ISSUE_ID,
        "type": "issue",
        "title": "Artifact failure-memory eval issue",
        "status": "open",
        "created_at": "2026-06-15T00:00:00Z",
        "updated_at": "2026-06-15T00:00:00Z",
        "authors": ["eval-fixture"],
        "severity": "low",
        "description": "Evaluate artifact failure-memory retrieval and governance.",
        "related_artifacts": [PUBLIC_ARTIFACT_ID, PRIVATE_ARTIFACT_ID],
        "tags": ["artifact-failure-memory-eval"],
    }


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _remove_runtime_case_root(context: RepoContext, case_root: Path) -> None:
    runtime_root = context.repo_root / Path(".cosheaf/evals/artifact_failure_memory")
    try:
        case_root.resolve().relative_to(runtime_root.resolve())
    except ValueError as exc:
        raise ArtifactFailureMemoryEvalError(
            f"refusing to remove unexpected eval path: {case_root}"
        ) from exc
    shutil.rmtree(case_root)


def _runtime_case_root(context: RepoContext, case_id: str) -> Path:
    return Path(".cosheaf") / "evals" / "artifact_failure_memory" / case_id


def _case_failures(
    case: ArtifactFailureMemoryEvalCase,
    *,
    failure_retrieved: bool,
    repeated_failed_direction_detected: bool,
    scope_leak: bool,
    authority_violation: bool,
    candidate_counterexample_mislabel: bool,
) -> list[str]:
    failures: list[str] = []
    if case.expect_failure_retrieved and not failure_retrieved:
        failures.append("expected failure memory was not retrieved")
    if case.expect_repeat_detected and not repeated_failed_direction_detected:
        failures.append("repeated failed direction was not detected")
    if case.expect_no_scope_leak and scope_leak:
        failures.append("private failure memory leaked into public-only output")
    if case.expect_no_authority_violation and authority_violation:
        failures.append("failure memory was surfaced as authority")
    if case.expect_no_candidate_mislabel and candidate_counterexample_mislabel:
        failures.append("candidate counterexample was mislabeled as checked")
    return failures


def _scope_leak(result_json: str, retrieved_artifact_ids: tuple[str, ...]) -> bool:
    return (
        PRIVATE_MARKER in result_json
        or PRIVATE_ARTIFACT_ID in retrieved_artifact_ids
        or PRIVATE_ARTIFACT_ID in result_json
    )


def _authority_violation(result: Any) -> bool:
    has_failure_hit = any(hit.card.failure_count for hit in result.cards)
    if not has_failure_hit:
        return False
    warnings = " ".join(result.audit.warnings).lower()
    if NON_AUTHORITY_WARNING not in warnings:
        return True
    for hit in result.cards:
        if not hit.card.failure_count:
            continue
        why = hit.card.why_relevant.lower()
        if "verifier pass" in why or "human review" in why:
            return True
    return False


def _candidate_counterexample_mislabel(context: RepoContext) -> bool:
    artifact_path = (
        context.repo_root / "kb/public/accepted/claims/claim.failure.public.yaml"
    )
    artifact = yaml.safe_load(artifact_path.read_text(encoding="utf-8"))
    entries = artifact.get("failure_log", [])
    for entry in entries:
        candidates = entry.get("related_counterexample_candidates", [])
        if not candidates:
            continue
        text = " ".join(
            str(entry.get(field, ""))
            for field in ("summary", "failed_because", "limitations", "status")
        ).lower()
        if (
            "checked_counterexample" in text
            or "checked refutation" in text
            or "is a checked counterexample" in text
            or "as checked counterexample" in text
        ):
            return True
    return False


def _direction_matches_query(query: str, direction: str) -> bool:
    query_tokens = {token for token in query.lower().replace("-", " ").split() if token}
    direction_tokens = {
        token for token in direction.lower().replace("-", " ").split() if token
    }
    return bool(query_tokens.intersection(direction_tokens))


def _aggregate_metrics(
    cases: list[ArtifactFailureMemoryEvalCaseResult],
) -> ArtifactFailureMemoryEvalMetrics:
    if not cases:
        raise ArtifactFailureMemoryEvalError(
            "cannot aggregate empty artifact failure-memory eval"
        )
    expected_failure_cases = [
        case for case in cases if case.expected_failure_retrieved
    ]
    expected_repeat_cases = [case for case in cases if case.expected_repeat_detected]
    return ArtifactFailureMemoryEvalMetrics(
        failure_retrieval_recall=_ratio(
            sum(1 for case in expected_failure_cases if case.failure_retrieved),
            len(expected_failure_cases),
        ),
        repeat_failed_direction_rate=_ratio(
            sum(
                1
                for case in expected_repeat_cases
                if case.repeated_failed_direction_slipped
            ),
            len(expected_repeat_cases),
        ),
        failure_scope_leak_count=sum(1 for case in cases if case.scope_leak),
        failure_authority_violation_count=sum(
            1 for case in cases if case.authority_violation
        ),
        candidate_counterexample_mislabel_count=sum(
            1 for case in cases if case.candidate_counterexample_mislabel
        ),
    )


def _unique_runtime_paths(
    cases: list[ArtifactFailureMemoryEvalCaseResult],
) -> tuple[Path, ...]:
    paths = {
        path.as_posix(): path
        for case in cases
        for path in case.runtime_paths
        if path.as_posix().startswith(".cosheaf/")
    }
    return tuple(paths[key] for key in sorted(paths))


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 6)


def _case_id(case: ArtifactFailureMemoryEvalCase, index: int) -> str:
    if case.id:
        return case.id
    return f"case.failure-memory.{index:04d}"


__all__ = [
    "DEFAULT_ARTIFACT_FAILURE_MEMORY_EVAL_CASES",
    "ArtifactFailureMemoryEvalCase",
    "ArtifactFailureMemoryEvalCaseResult",
    "ArtifactFailureMemoryEvalError",
    "ArtifactFailureMemoryEvalKind",
    "ArtifactFailureMemoryEvalMetrics",
    "ArtifactFailureMemoryEvalReport",
    "ArtifactFailureMemoryEvalSuite",
    "load_artifact_failure_memory_eval_suite",
    "resolve_artifact_failure_memory_eval_case_path",
    "run_artifact_failure_memory_eval_case",
    "run_artifact_failure_memory_eval_suite",
]
