"""Durable strategy plan and research task graph DTOs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from cosheaf.agent.run_logging import SECRET_VALUE_PATTERN
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path

STRATEGY_AUTHORITY_NOTICE = (
    "Strategy plans are guidance for review only; they are not proof, evidence, "
    "verifier pass, gate pass, human review, accepted status, or promotion "
    "authority."
)


class StrategyError(ValueError):
    """Expected strategy planner or storage failure."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        remediation: str,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.remediation = remediation
        self.details = dict(details or {})


class StrategyTaskScope(StrEnum):
    """Where a task can safely operate."""

    PUBLIC = "public"
    PRIVATE = "private"
    WORKSPACE = "workspace"
    FRAMEWORK = "framework"
    UNKNOWN = "unknown"


class StrategyTaskStatus(StrEnum):
    """Task graph node status."""

    READY = "ready"
    BLOCKED = "blocked"
    DEFERRED = "deferred"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StrategyTaskNodeKind(StrEnum):
    """Research task categories."""

    UNDERSTAND = "understand"
    RETRIEVAL_CONTEXT = "retrieval_context"
    PROOF_ATTEMPT = "proof_attempt"
    CONSTRUCTION_SEARCH = "construction_search"
    COUNTEREXAMPLE_SEARCH = "counterexample_search"
    VERIFICATION = "verification"
    FORMALIZATION_ATTEMPT = "formalization_attempt"
    LITERATURE_SOURCE_LOOKUP = "literature_source_lookup"
    REVIEW_DECISION = "review_decision"
    REVIEW = "review_decision"
    BLOCKED_DEFERRED = "blocked_deferred"
    VALIDATION = "validation"
    GATE = "gate"
    RUN_REVIEW = "run_review"


class StrategyTaskReferenceKind(StrEnum):
    """Reviewable references attached to strategy task nodes."""

    COMMAND = "command"
    CONTEXT_PACK = "context_pack"
    RESEARCH_RUN = "research_run"
    ARTIFACT = "artifact"
    CHECKED_COUNTEREXAMPLE_EVIDENCE = "checked_counterexample_evidence"
    REVIEW_EXPORT = "review_export"
    VALIDATION_REPORT = "validation_report"
    GATE_REPORT = "gate_report"
    FAILURE_LOG = "failure_log"
    OTHER = "other"


class StrategyEdgeKind(StrEnum):
    """Task graph edge categories."""

    PREREQUISITE = "prerequisite"
    EVIDENCE_DEPENDENCY = "evidence_dependency"
    BLOCKED_BY = "blocked_by"


class StrategyModel(BaseModel):
    """Strict deterministic base model for strategy DTOs."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-serializable data."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON text."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class StrategyProblem(StrategyModel):
    """Research problem root for one strategy plan."""

    issue_id: str
    title: str
    description: str = ""
    domains: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    target_artifacts: tuple[str, ...] = ()
    known_constraints: tuple[str, ...] = ()
    public_private_scope_labels: tuple[StrategyTaskScope, ...] = ()

    @field_validator("issue_id")
    @classmethod
    def _issue_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("target_artifacts", mode="before")
    @classmethod
    def _target_artifacts(cls, value: Any) -> tuple[str, ...]:
        return _dedupe(validate_artifact_id(item) for item in _text_items(value))

    @field_validator("domains", "tags", "known_constraints", mode="before")
    @classmethod
    def _text_tuple(cls, value: Any) -> tuple[str, ...]:
        return _dedupe(_safe_text(item) for item in _text_items(value))

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("description")
    @classmethod
    def _description(cls, value: str) -> str:
        return value.strip()


class StrategyTaskNode(StrategyModel):
    """One bounded research task in a strategy graph."""

    node_id: str
    kind: StrategyTaskNodeKind
    title: str
    status: StrategyTaskStatus
    scope: StrategyTaskScope
    description: str = ""
    depends_on: tuple[str, ...] = ()
    blocked_by: tuple[str, ...] = ()
    expected_evidence_kinds: tuple[str, ...] = ()
    related_artifacts: tuple[str, ...] = ()
    related_failure_log_entries: tuple[str, ...] = ()
    related_candidate_counterexamples: tuple[str, ...] = ()
    related_checked_counterexample_evidence: tuple[str, ...] = ()
    related_research_run_ids: tuple[str, ...] = ()
    command: tuple[str, ...] = ()
    input_paths: tuple[str, ...] = ()
    write_paths: tuple[str, ...] = ()
    references: tuple[StrategyTaskReference, ...] = ()
    notes: tuple[str, ...] = ()

    @field_validator("node_id")
    @classmethod
    def _node_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("description")
    @classmethod
    def _description(cls, value: str) -> str:
        return value.strip()

    @field_validator(
        "depends_on",
        "blocked_by",
        "expected_evidence_kinds",
        "related_failure_log_entries",
        "related_candidate_counterexamples",
        "related_checked_counterexample_evidence",
        "related_research_run_ids",
        "command",
        "notes",
        mode="before",
    )
    @classmethod
    def _safe_text_tuple(cls, value: Any) -> tuple[str, ...]:
        return _dedupe(_safe_text(item) for item in _text_items(value))

    @field_validator("related_artifacts", mode="before")
    @classmethod
    def _artifact_ids(cls, value: Any) -> tuple[str, ...]:
        return _dedupe(validate_artifact_id(item) for item in _text_items(value))

    @field_validator("input_paths", mode="before")
    @classmethod
    def _input_paths(cls, value: Any) -> tuple[str, ...]:
        return tuple(_validate_repo_local_path(item) for item in _text_items(value))

    @field_validator("write_paths", mode="before")
    @classmethod
    def _write_paths(cls, value: Any) -> tuple[str, ...]:
        return tuple(
            _validate_repo_local_path(item, forbid_accepted=True)
            for item in _text_items(value)
        )


class StrategyTaskEdge(StrategyModel):
    """A directed task graph edge."""

    from_node: str
    to_node: str
    kind: StrategyEdgeKind
    reason: str

    @field_validator("from_node", "to_node")
    @classmethod
    def _node_ref(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("reason")
    @classmethod
    def _reason(cls, value: str) -> str:
        return _safe_text(value)


class StrategyTaskReference(StrategyModel):
    """One non-authoritative run/context/review reference for a task node."""

    kind: StrategyTaskReferenceKind
    identifier: str = ""
    path: str = ""
    status: str = ""
    summary: str = ""

    @field_validator("identifier", "status", "summary")
    @classmethod
    def _safe_optional_text(cls, value: str) -> str:
        normalized = str(value).strip()
        if not normalized:
            return ""
        return _safe_text(normalized)

    @field_validator("path")
    @classmethod
    def _path(cls, value: str) -> str:
        normalized = str(value).strip()
        if not normalized:
            return ""
        return _validate_repo_local_path(normalized, forbid_accepted=True)


class StrategyTaskGraph(StrategyModel):
    """Directed research task graph."""

    nodes: tuple[StrategyTaskNode, ...]
    edges: tuple[StrategyTaskEdge, ...] = ()

    @model_validator(mode="after")
    def _graph_consistency(self) -> Self:
        ids = [node.node_id for node in self.nodes]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate task node id")
        id_set = set(ids)
        for node in self.nodes:
            missing_deps = set(node.depends_on).difference(id_set)
            missing_blockers = set(node.blocked_by).difference(id_set)
            if missing_deps:
                raise ValueError(f"unknown task dependency: {sorted(missing_deps)[0]}")
            if missing_blockers:
                raise ValueError(f"unknown task blocker: {sorted(missing_blockers)[0]}")
        for edge in self.edges:
            if edge.from_node not in id_set or edge.to_node not in id_set:
                raise ValueError("task graph edges must reference existing nodes")
        return self


class StrategyNextStep(StrategyModel):
    """Ranked next action candidate."""

    rank: int
    node_id: str
    score: float
    reasons: tuple[str, ...]
    command: tuple[str, ...] = ()

    @field_validator("node_id")
    @classmethod
    def _node_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("rank")
    @classmethod
    def _rank(cls, value: int) -> int:
        if value < 1:
            raise ValueError("rank must be positive")
        return value

    @field_validator("score")
    @classmethod
    def _score(cls, value: float) -> float:
        return round(float(value), 6)

    @field_validator("reasons", "command", mode="before")
    @classmethod
    def _text_tuple(cls, value: Any) -> tuple[str, ...]:
        return _dedupe(_safe_text(item) for item in _text_items(value))


class StrategyPlan(StrategyModel):
    """Durable v1 strategy plan."""

    schema_version: Literal[1] = 1
    plan_id: str
    issue_id: str
    created_at: datetime
    problem: StrategyProblem
    graph: StrategyTaskGraph
    next_steps: tuple[StrategyNextStep, ...] = ()
    authority_notice: str = STRATEGY_AUTHORITY_NOTICE
    accepted_write_performed: Literal[False] = False

    @field_validator("plan_id", "issue_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("created_at")
    @classmethod
    def _created_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must include timezone information")
        return value.astimezone(UTC).replace(microsecond=0)

    @model_validator(mode="after")
    def _plan_consistency(self) -> Self:
        if self.problem.issue_id != self.issue_id:
            raise ValueError("problem issue_id must match strategy issue_id")
        if self.authority_notice != STRATEGY_AUTHORITY_NOTICE:
            raise ValueError("authority_notice must preserve strategy boundary")
        graph_ids = {node.node_id for node in self.graph.nodes}
        for step in self.next_steps:
            if step.node_id not in graph_ids:
                raise ValueError("next steps must reference graph nodes")
        return self


def _validate_repo_local_path(value: str, *, forbid_accepted: bool = False) -> str:
    raw = str(value).strip()
    normalized = normalize_repo_path(raw)
    is_absolute = Path(raw).is_absolute() or PureWindowsPath(raw).is_absolute()
    parts = PurePosixPath(normalized).parts
    if (
        not normalized
        or normalized == "."
        or normalized == ".."
        or normalized.startswith("../")
        or normalized.startswith("/")
        or is_absolute
        or ".." in parts
    ):
        raise ValueError("path must be repository-local")
    if forbid_accepted and parts and parts[0] == "kb" and "accepted" in parts[1:]:
        raise ValueError("strategy plans cannot authorize writes to accepted KB paths")
    return normalized


def _text_items(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    values: tuple[str, ...]
    if isinstance(value, str):
        values = (value,)
    else:
        try:
            values = tuple(str(item) for item in value)
        except TypeError as exc:
            raise ValueError("field must be a sequence of strings") from exc
    return tuple(item.strip() for item in values if item.strip())


def _dedupe(values: Any) -> tuple[Any, ...]:
    seen: set[Any] = set()
    result: list[Any] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return tuple(result)


def _safe_text(value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError("text field must be non-empty")
    if SECRET_VALUE_PATTERN.search(normalized):
        raise ValueError("text field contains secret-looking value")
    return normalized


__all__ = [
    "STRATEGY_AUTHORITY_NOTICE",
    "StrategyEdgeKind",
    "StrategyError",
    "StrategyNextStep",
    "StrategyPlan",
    "StrategyProblem",
    "StrategyTaskEdge",
    "StrategyTaskGraph",
    "StrategyTaskNode",
    "StrategyTaskNodeKind",
    "StrategyTaskReference",
    "StrategyTaskReferenceKind",
    "StrategyTaskScope",
    "StrategyTaskStatus",
]
