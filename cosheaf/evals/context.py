"""Small deterministic context-pack regression evaluation harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import Field, field_validator

from cosheaf.agent.context_pack import ContextPackError, build_context_pack
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path
from cosheaf.memory import ArtifactCardStatus, MemoryRootScope, RetrievalRole
from cosheaf.memory.models import MemoryModel
from cosheaf.storage.repo import RepoContext

DEFAULT_CONTEXT_EVAL_CASES = Path("evals") / "context" / "cases.yaml"


class ContextEvalError(ValueError):
    """Raised for expected context eval loading or execution failures."""


class ContextEvalCase(MemoryModel):
    """One deterministic context-pack regression case."""

    id: str | None = None
    issue_id: str
    required_artifacts: list[str] = Field(default_factory=list)
    role: RetrievalRole = RetrievalRole.ORCHESTRATOR
    public_only: bool = False
    max_cards: int = 20
    max_full_artifacts: int = 0
    max_allowed_cards: int | None = None
    max_allowed_full_artifacts: int | None = None
    max_token_estimate: int | None = None
    min_accepted_ratio: float = 0.0
    max_draft_ratio: float = 1.0
    allow_private_cards: bool = False
    allow_known_failures: bool = False
    require_all_required_artifacts: bool = True

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_artifact_id(value.strip())

    @field_validator("issue_id")
    @classmethod
    def _validate_issue_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("required_artifacts")
    @classmethod
    def _validate_required_artifacts(cls, values: list[str]) -> list[str]:
        normalized = [validate_artifact_id(value.strip()) for value in values]
        if not normalized:
            raise ValueError("required_artifacts must not be empty")
        return normalized

    @field_validator("max_cards")
    @classmethod
    def _validate_max_cards(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("max_cards must be positive")
        return value

    @field_validator("max_full_artifacts")
    @classmethod
    def _validate_max_full_artifacts(cls, value: int) -> int:
        if value < 0:
            raise ValueError("max_full_artifacts must be non-negative")
        return value

    @field_validator("max_allowed_cards", "max_allowed_full_artifacts")
    @classmethod
    def _validate_optional_non_negative(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 0:
            raise ValueError("budget thresholds must be non-negative")
        return value

    @field_validator("max_token_estimate")
    @classmethod
    def _validate_max_token_estimate(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value <= 0:
            raise ValueError("max_token_estimate must be positive")
        return value

    @field_validator("min_accepted_ratio", "max_draft_ratio")
    @classmethod
    def _validate_ratio(cls, value: float) -> float:
        if value < 0.0 or value > 1.0:
            raise ValueError("ratio thresholds must be between 0 and 1")
        return value


class ContextEvalSuite(MemoryModel):
    """A small collection of context-pack regression cases."""

    schema_version: Literal[1] = 1
    cases: list[ContextEvalCase]

    @field_validator("cases")
    @classmethod
    def _validate_cases(
        cls,
        values: list[ContextEvalCase],
    ) -> list[ContextEvalCase]:
        if not values:
            raise ValueError("cases must not be empty")
        return values


@dataclass(frozen=True)
class ContextEvalMetrics:
    """Deterministic boundedness and policy-safety metrics."""

    max_cards: int
    max_full_artifacts: int
    token_estimate: int
    accepted_ratio: float
    draft_ratio: float
    private_leakage_count: int
    required_artifact_hit: float

    def to_dict(self) -> dict[str, int | float]:
        """Return deterministic machine-readable metrics."""
        return {
            "max_cards": self.max_cards,
            "max_full_artifacts": self.max_full_artifacts,
            "token_estimate": self.token_estimate,
            "accepted_ratio": self.accepted_ratio,
            "draft_ratio": self.draft_ratio,
            "private_leakage_count": self.private_leakage_count,
            "required_artifact_hit": self.required_artifact_hit,
        }


@dataclass(frozen=True)
class ContextEvalCaseResult:
    """One scored context-pack eval case."""

    id: str
    issue_id: str
    role: RetrievalRole
    public_only: bool
    metrics: ContextEvalMetrics
    required_artifacts: tuple[str, ...]
    returned_artifacts: list[str]
    full_artifact_pulls: list[str]
    private_artifacts_returned: list[str]
    known_failure_artifacts_returned: list[str]
    missing_required_artifacts: list[str]
    failures: list[str]

    @property
    def passed(self) -> bool:
        """Return whether this case satisfied every configured policy threshold."""
        return not self.failures

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic machine-readable case output."""
        return {
            "id": self.id,
            "issue_id": self.issue_id,
            "role": self.role.value,
            "public_only": self.public_only,
            **self.metrics.to_dict(),
            "required_artifacts": list(self.required_artifacts),
            "returned_artifacts": self.returned_artifacts,
            "full_artifact_pulls": self.full_artifact_pulls,
            "private_artifacts_returned": self.private_artifacts_returned,
            "known_failure_artifacts_returned": self.known_failure_artifacts_returned,
            "missing_required_artifacts": self.missing_required_artifacts,
            "failures": self.failures,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class ContextEvalReport:
    """Scored context-pack eval suite output."""

    schema_version: Literal[1]
    case_count: int
    passed: bool
    metrics: ContextEvalMetrics
    cases: list[ContextEvalCaseResult]

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic machine-readable report output."""
        return {
            "schema_version": self.schema_version,
            "case_count": self.case_count,
            "passed": self.passed,
            "metrics": self.metrics.to_dict(),
            "cases": [case.to_dict() for case in self.cases],
        }

    def to_json(self) -> str:
        """Return deterministic JSON for CLI output."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


def load_context_eval_suite(path: Path) -> ContextEvalSuite:
    """Load a context eval suite from a YAML file."""
    if not path.exists():
        raise ContextEvalError(f"context eval case file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ContextEvalError(f"cannot read context eval case file: {exc}") from exc
    if data is None:
        raise ContextEvalError("context eval case file is empty")
    try:
        return ContextEvalSuite.model_validate(data)
    except ValueError as exc:
        raise ContextEvalError(f"invalid context eval case file: {exc}") from exc


def resolve_context_eval_case_path(context: RepoContext, cases_path: Path) -> Path:
    """Resolve and constrain the case file path to the repository root."""
    repo_root = context.repo_root
    path = cases_path if cases_path.is_absolute() else repo_root / cases_path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ContextEvalError(
            "context eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(cases_path).is_absolute():
        raise ContextEvalError("context eval case file must be repository-local")
    return resolved


def run_context_eval_suite(
    context: RepoContext,
    suite: ContextEvalSuite,
) -> ContextEvalReport:
    """Run every context-pack eval case against repository metadata."""
    case_results = [
        run_context_eval_case(context, case, case_index=index)
        for index, case in enumerate(suite.cases, start=1)
    ]
    metrics = _aggregate_metrics(case_results)
    return ContextEvalReport(
        schema_version=1,
        case_count=len(case_results),
        passed=all(case.passed for case in case_results),
        metrics=metrics,
        cases=case_results,
    )


def run_context_eval_case(
    context: RepoContext,
    case: ContextEvalCase,
    *,
    case_index: int = 1,
) -> ContextEvalCaseResult:
    """Build and score one context pack regression case."""
    try:
        result = build_context_pack(
            context,
            case.issue_id,
            role=case.role,
            max_cards=case.max_cards,
            max_full_artifacts=case.max_full_artifacts,
            public_only=case.public_only,
        )
    except ContextPackError as exc:
        raise ContextEvalError(
            f"context eval case failed ({_case_id(case, case_index)}): {exc}"
        ) from exc

    audit_path = result.task_dir / "RETRIEVAL_AUDIT.json"
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextEvalError(
            f"context eval case failed ({_case_id(case, case_index)}): "
            f"cannot read retrieval audit: {exc}"
        ) from exc

    cards = list(audit.get("retrieval", {}).get("cards", []))
    pulls = list(audit.get("full_artifact_pulls", []))
    returned_artifacts = [str(card.get("artifact_id", "")) for card in cards]
    full_artifact_pulls = [str(pull.get("artifact_id", "")) for pull in pulls]
    private_artifacts_returned = [
        str(card.get("artifact_id", ""))
        for card in cards
        if card.get("root_scope") == MemoryRootScope.PRIVATE.value
    ]
    known_failure_artifacts_returned = [
        str(card.get("artifact_id", ""))
        for card in cards
        if card.get("status")
        in {
            ArtifactCardStatus.REFUTED.value,
            ArtifactCardStatus.OBSOLETE.value,
            ArtifactCardStatus.SUPERSEDED.value,
        }
    ]
    required = tuple(case.required_artifacts)
    missing_required = [
        artifact_id for artifact_id in required if artifact_id not in returned_artifacts
    ]
    accepted_count = sum(
        1 for card in cards if card.get("status") == ArtifactCardStatus.ACCEPTED.value
    )
    draft_count = sum(
        1
        for card in cards
        if card.get("status")
        in {
            ArtifactCardStatus.RAW.value,
            ArtifactCardStatus.DRAFT.value,
            ArtifactCardStatus.LOCALLY_TESTED.value,
            ArtifactCardStatus.ADVERSARIALLY_TESTED.value,
            ArtifactCardStatus.MACHINE_CHECKED.value,
            ArtifactCardStatus.HUMAN_REVIEWED.value,
        }
    )
    card_count = len(cards)
    required_hits = len(required) - len(missing_required)
    metrics = ContextEvalMetrics(
        max_cards=card_count,
        max_full_artifacts=len(pulls),
        token_estimate=_estimate_context_pack_tokens(result.files),
        accepted_ratio=_ratio(accepted_count, card_count),
        draft_ratio=_ratio(draft_count, card_count),
        private_leakage_count=len(private_artifacts_returned),
        required_artifact_hit=_ratio(required_hits, len(required)),
    )
    failures = _case_failures(case, metrics, missing_required)
    if private_artifacts_returned and (
        case.public_only or not case.allow_private_cards
    ):
        failures.append(
            "private_leakage_count "
            f"{metrics.private_leakage_count} exceeds allowed 0"
        )
    if known_failure_artifacts_returned and not case.allow_known_failures:
        failures.append(
            "known_failure_count "
            f"{len(known_failure_artifacts_returned)} exceeds allowed 0"
        )

    return ContextEvalCaseResult(
        id=_case_id(case, case_index),
        issue_id=case.issue_id,
        role=case.role,
        public_only=case.public_only,
        metrics=metrics,
        required_artifacts=required,
        returned_artifacts=returned_artifacts,
        full_artifact_pulls=full_artifact_pulls,
        private_artifacts_returned=private_artifacts_returned,
        known_failure_artifacts_returned=known_failure_artifacts_returned,
        missing_required_artifacts=missing_required,
        failures=failures,
    )


def _case_failures(
    case: ContextEvalCase,
    metrics: ContextEvalMetrics,
    missing_required: list[str],
) -> list[str]:
    failures: list[str] = []
    max_allowed_cards = (
        case.max_cards if case.max_allowed_cards is None else case.max_allowed_cards
    )
    max_allowed_full_artifacts = (
        case.max_full_artifacts
        if case.max_allowed_full_artifacts is None
        else case.max_allowed_full_artifacts
    )
    if metrics.max_cards > max_allowed_cards:
        failures.append(
            f"max_cards {metrics.max_cards} exceeds allowed {max_allowed_cards}"
        )
    if metrics.max_full_artifacts > max_allowed_full_artifacts:
        failures.append(
            "max_full_artifacts "
            f"{metrics.max_full_artifacts} exceeds allowed "
            f"{max_allowed_full_artifacts}"
        )
    if (
        case.max_token_estimate is not None
        and metrics.token_estimate > case.max_token_estimate
    ):
        failures.append(
            "token_estimate "
            f"{metrics.token_estimate} exceeds allowed {case.max_token_estimate}"
        )
    if metrics.accepted_ratio < case.min_accepted_ratio:
        failures.append(
            f"accepted_ratio {metrics.accepted_ratio:.6f} below required "
            f"{case.min_accepted_ratio:.6f}"
        )
    if metrics.draft_ratio > case.max_draft_ratio:
        failures.append(
            f"draft_ratio {metrics.draft_ratio:.6f} exceeds allowed "
            f"{case.max_draft_ratio:.6f}"
        )
    if case.require_all_required_artifacts and missing_required:
        failures.append(
            "required_artifact_hit "
            f"{metrics.required_artifact_hit:.6f} missing "
            f"{','.join(missing_required)}"
        )
    return failures


def _aggregate_metrics(cases: list[ContextEvalCaseResult]) -> ContextEvalMetrics:
    if not cases:
        raise ContextEvalError("cannot aggregate empty context eval results")
    return ContextEvalMetrics(
        max_cards=max(case.metrics.max_cards for case in cases),
        max_full_artifacts=max(case.metrics.max_full_artifacts for case in cases),
        token_estimate=max(case.metrics.token_estimate for case in cases),
        accepted_ratio=round(
            sum(case.metrics.accepted_ratio for case in cases) / len(cases),
            6,
        ),
        draft_ratio=round(
            sum(case.metrics.draft_ratio for case in cases) / len(cases),
            6,
        ),
        private_leakage_count=sum(
            case.metrics.private_leakage_count for case in cases
        ),
        required_artifact_hit=round(
            sum(case.metrics.required_artifact_hit for case in cases) / len(cases),
            6,
        ),
    )


def _estimate_context_pack_tokens(paths: tuple[Path, ...]) -> int:
    text = "".join(path.read_text(encoding="utf-8") for path in sorted(paths))
    return max(1, (len(text) + 3) // 4)


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)


def _case_id(case: ContextEvalCase, index: int) -> str:
    if case.id:
        return case.id
    normalized_issue = normalize_repo_path(case.issue_id.lower())
    slug = ".".join(part for part in normalized_issue.split("/") if part)
    if slug:
        return f"case.context.{slug}"
    return f"case.context.{index:04d}"
