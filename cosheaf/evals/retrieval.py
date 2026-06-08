"""Small deterministic retrieval evaluation harness."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import Field, field_validator

from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path
from cosheaf.memory import (
    ArtifactCardStatus,
    MemoryRootScope,
    RetrievalResult,
    search_artifact_cards,
)
from cosheaf.memory.models import MemoryModel
from cosheaf.memory.search import MemorySearchError
from cosheaf.storage.repo import RepoContext

DEFAULT_RETRIEVAL_EVAL_CASES = Path("evals") / "retrieval" / "cases.yaml"
CASE_SLUG_PATTERN = re.compile(r"[a-z0-9]+")


class RetrievalEvalError(ValueError):
    """Raised for expected retrieval eval loading or execution failures."""


class RetrievalEvalCase(MemoryModel):
    """One deterministic retrieval regression case."""

    id: str | None = None
    query: str
    issue_id: str | None = None
    expected_relevant_artifacts: list[str] = Field(default_factory=list)
    forbidden_artifacts: list[str] = Field(default_factory=list)
    allowed_scope: list[MemoryRootScope] = Field(
        default_factory=lambda: [MemoryRootScope.PUBLIC]
    )

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_artifact_id(value.strip())

    @field_validator("query")
    @classmethod
    def _validate_query(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("query must not be empty")
        return normalized

    @field_validator("issue_id")
    @classmethod
    def _validate_issue_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_artifact_id(value.strip())

    @field_validator("expected_relevant_artifacts")
    @classmethod
    def _validate_expected(cls, values: list[str]) -> list[str]:
        normalized = [validate_artifact_id(value.strip()) for value in values]
        if not normalized:
            raise ValueError("expected_relevant_artifacts must not be empty")
        return normalized

    @field_validator("forbidden_artifacts")
    @classmethod
    def _validate_forbidden(cls, values: list[str]) -> list[str]:
        return [validate_artifact_id(value.strip()) for value in values]

    @field_validator("allowed_scope")
    @classmethod
    def _validate_scope(cls, values: list[MemoryRootScope]) -> list[MemoryRootScope]:
        if not values:
            raise ValueError("allowed_scope must not be empty")
        return list(dict.fromkeys(values))


class RetrievalEvalSuite(MemoryModel):
    """A small collection of retrieval regression cases."""

    schema_version: Literal[1] = 1
    cases: list[RetrievalEvalCase]

    @field_validator("cases")
    @classmethod
    def _validate_cases(
        cls,
        values: list[RetrievalEvalCase],
    ) -> list[RetrievalEvalCase]:
        if not values:
            raise ValueError("cases must not be empty")
        return values


@dataclass(frozen=True)
class RetrievalEvalMetrics:
    """Aggregate deterministic retrieval metrics."""

    hit_at_k: float
    forbidden_hit_count: int
    accepted_priority_score: float
    private_leakage_count: int

    def to_dict(self, *, k: int) -> dict[str, int | float]:
        """Return metrics using the public `hit@k` key spelling."""
        return {
            f"hit@{k}": self.hit_at_k,
            "forbidden_hit_count": self.forbidden_hit_count,
            "accepted_priority_score": self.accepted_priority_score,
            "private_leakage_count": self.private_leakage_count,
        }


@dataclass(frozen=True)
class RetrievalEvalCaseResult:
    """One scored retrieval eval case."""

    id: str
    query: str
    issue_id: str | None
    metrics: RetrievalEvalMetrics
    expected_relevant_artifacts: tuple[str, ...]
    forbidden_artifacts: tuple[str, ...]
    allowed_scope: tuple[MemoryRootScope, ...]
    returned_artifacts: list[str]
    forbidden_artifacts_returned: list[str]
    private_artifacts_returned: list[str]
    missing_expected_artifacts: list[str]

    @property
    def hit_at_k(self) -> float:
        return self.metrics.hit_at_k

    @property
    def forbidden_hit_count(self) -> int:
        return self.metrics.forbidden_hit_count

    @property
    def accepted_priority_score(self) -> float:
        return self.metrics.accepted_priority_score

    @property
    def private_leakage_count(self) -> int:
        return self.metrics.private_leakage_count

    def to_dict(self, *, k: int) -> dict[str, Any]:
        """Return deterministic machine-readable case output."""
        return {
            "id": self.id,
            "query": self.query,
            "issue_id": self.issue_id,
            "expected_relevant_artifacts": list(self.expected_relevant_artifacts),
            "forbidden_artifacts": list(self.forbidden_artifacts),
            "allowed_scope": [scope.value for scope in self.allowed_scope],
            **self.metrics.to_dict(k=k),
            "returned_artifacts": self.returned_artifacts,
            "forbidden_artifacts_returned": self.forbidden_artifacts_returned,
            "private_artifacts_returned": self.private_artifacts_returned,
            "missing_expected_artifacts": self.missing_expected_artifacts,
        }


@dataclass(frozen=True)
class RetrievalEvalReport:
    """Scored retrieval eval suite output."""

    schema_version: Literal[1]
    case_count: int
    k: int
    passed: bool
    metrics: RetrievalEvalMetrics
    cases: list[RetrievalEvalCaseResult]

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic machine-readable report output."""
        return {
            "schema_version": self.schema_version,
            "case_count": self.case_count,
            "k": self.k,
            "passed": self.passed,
            "metrics": self.metrics.to_dict(k=self.k),
            "cases": [case.to_dict(k=self.k) for case in self.cases],
        }

    def to_json(self) -> str:
        """Return deterministic JSON for CLI output."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


def load_retrieval_eval_suite(path: Path) -> RetrievalEvalSuite:
    """Load a retrieval eval suite from a YAML file."""
    if not path.exists():
        raise RetrievalEvalError(f"retrieval eval case file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RetrievalEvalError(
            f"cannot read retrieval eval case file: {exc}"
        ) from exc
    if data is None:
        raise RetrievalEvalError("retrieval eval case file is empty")
    try:
        return RetrievalEvalSuite.model_validate(data)
    except ValueError as exc:
        raise RetrievalEvalError(f"invalid retrieval eval case file: {exc}") from exc


def resolve_retrieval_eval_case_path(context: RepoContext, cases_path: Path) -> Path:
    """Resolve and constrain the case file path to the repository root."""
    repo_root = context.repo_root
    path = cases_path if cases_path.is_absolute() else repo_root / cases_path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise RetrievalEvalError(
            "retrieval eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(cases_path).is_absolute():
        raise RetrievalEvalError("retrieval eval case file must be repository-local")
    return resolved


def run_retrieval_eval_suite(
    context: RepoContext,
    suite: RetrievalEvalSuite,
    *,
    k: int,
) -> RetrievalEvalReport:
    """Run every retrieval eval case against the current repository metadata."""
    if k <= 0:
        raise RetrievalEvalError("k must be positive")

    case_results: list[RetrievalEvalCaseResult] = []
    for index, case in enumerate(suite.cases, start=1):
        try:
            retrieval = search_artifact_cards(
                context,
                query=case.query,
                issue_id=case.issue_id,
                allowed_scopes=tuple(case.allowed_scope),
                max_cards=k,
            )
        except MemorySearchError as exc:
            raise RetrievalEvalError(
                f"retrieval eval case failed ({_case_id(case, index)}): {exc}"
            ) from exc

        case_results.append(
            score_retrieval_case(
                case,
                retrieval,
                k=k,
                case_index=index,
            )
        )

    metrics = _aggregate_metrics(case_results)
    passed = all(
        case.hit_at_k == 1.0
        and case.forbidden_hit_count == 0
        and case.private_leakage_count == 0
        for case in case_results
    )
    return RetrievalEvalReport(
        schema_version=1,
        case_count=len(case_results),
        k=k,
        passed=passed,
        metrics=metrics,
        cases=case_results,
    )


def score_retrieval_case(
    case: RetrievalEvalCase,
    result: RetrievalResult,
    *,
    k: int,
    case_index: int = 1,
) -> RetrievalEvalCaseResult:
    """Score one retrieval result against one eval case."""
    if k <= 0:
        raise RetrievalEvalError("k must be positive")

    top_hits = result.cards[:k]
    returned_artifacts = [hit.card.id for hit in top_hits]
    expected = tuple(case.expected_relevant_artifacts)
    forbidden = tuple(case.forbidden_artifacts)
    expected_set = set(expected)
    forbidden_set = set(forbidden)
    allowed_scopes = tuple(case.allowed_scope)

    expected_hits = [hit for hit in top_hits if hit.card.id in expected_set]
    forbidden_returned = [
        artifact_id
        for artifact_id in returned_artifacts
        if artifact_id in forbidden_set
    ]
    private_returned = [
        hit.card.id
        for hit in top_hits
        if hit.card.root_scope is MemoryRootScope.PRIVATE
        and MemoryRootScope.PRIVATE not in allowed_scopes
    ]
    missing_expected = [
        artifact_id for artifact_id in expected if artifact_id not in returned_artifacts
    ]
    accepted_expected_hits = [
        hit for hit in expected_hits if hit.card.status is ArtifactCardStatus.ACCEPTED
    ]
    accepted_priority_score = (
        round(len(accepted_expected_hits) / len(expected_hits), 6)
        if expected_hits
        else 0.0
    )

    metrics = RetrievalEvalMetrics(
        hit_at_k=1.0 if expected_hits else 0.0,
        forbidden_hit_count=len(forbidden_returned),
        accepted_priority_score=accepted_priority_score,
        private_leakage_count=len(private_returned),
    )
    return RetrievalEvalCaseResult(
        id=_case_id(case, case_index),
        query=case.query,
        issue_id=case.issue_id,
        metrics=metrics,
        expected_relevant_artifacts=expected,
        forbidden_artifacts=forbidden,
        allowed_scope=allowed_scopes,
        returned_artifacts=returned_artifacts,
        forbidden_artifacts_returned=forbidden_returned,
        private_artifacts_returned=private_returned,
        missing_expected_artifacts=missing_expected,
    )


def _aggregate_metrics(
    cases: list[RetrievalEvalCaseResult],
) -> RetrievalEvalMetrics:
    if not cases:
        raise RetrievalEvalError("cannot aggregate empty retrieval eval results")
    return RetrievalEvalMetrics(
        hit_at_k=round(sum(case.hit_at_k for case in cases) / len(cases), 6),
        forbidden_hit_count=sum(case.forbidden_hit_count for case in cases),
        accepted_priority_score=round(
            sum(case.accepted_priority_score for case in cases) / len(cases),
            6,
        ),
        private_leakage_count=sum(case.private_leakage_count for case in cases),
    )


def _case_id(case: RetrievalEvalCase, index: int) -> str:
    if case.id:
        return case.id
    normalized_query = normalize_repo_path(case.query.lower())
    slug = ".".join(CASE_SLUG_PATTERN.findall(normalized_query))
    if not slug:
        slug = f"{index:04d}"
    return f"case.retrieval.{slug}"
