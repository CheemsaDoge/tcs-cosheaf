"""Deterministic sidecar memory updates from workflow and campaign history."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, field_validator

from cosheaf.campaigns import CampaignError, load_campaign
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path, repo_relative_posix
from cosheaf.memory.models import MemoryModel
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.engine import WorkflowError, load_workflow

MEMORY_UPDATES_AUTHORITY_NOTICE = (
    "Memory weights are deterministic sidecar guidance only; they are not "
    "proof, source metadata, human review, verifier pass, gate pass, accepted "
    "status, or promotion authority."
)
MEMORY_WEIGHTS_PATH = Path(".cosheaf") / "memory" / "weights.json"
MEMORY_UPDATE_RUNS_ROOT = Path(".cosheaf") / "memory" / "update-runs"
DETERMINISTIC_GENERATED_AT = datetime(1970, 1, 1, tzinfo=UTC)


class MemoryUpdateError(ValueError):
    """Expected memory update failure."""


class MemorySignal(StrEnum):
    """Bounded update signal vocabulary."""

    RETRIEVED = "retrieved"
    USED_IN_PLAN = "used_in_plan"
    USED_IN_ATTEMPT = "used_in_attempt"
    USED_IN_SUCCESSFUL_DRAFT = "used_in_successful_draft"
    CHECKER_PASS = "checker_pass"
    CHECKER_FAIL = "checker_fail"
    GATE_BLOCKED = "gate_blocked"
    REVIEW_REQUESTED = "review_requested"
    HUMAN_ACCEPT_REFERENCE = "human_accept_reference"
    REPEAT_FAILURE = "repeat_failure"
    UNSAFE_OUTPUT = "unsafe_output"


class MemoryUpdatePolicy(MemoryModel):
    """Deterministic bounded weight policy."""

    schema_version: Literal[1] = 1
    min_weight: float = 0.0
    max_weight: float = 3.0
    signal_deltas: dict[str, float] = Field(default_factory=dict)
    authority_notice: str = MEMORY_UPDATES_AUTHORITY_NOTICE

    @field_validator("min_weight", "max_weight")
    @classmethod
    def _finite_weight(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("weight bounds must be finite")
        return value

    @field_validator("signal_deltas")
    @classmethod
    def _known_signals(cls, values: dict[str, float]) -> dict[str, float]:
        allowed = {signal.value for signal in MemorySignal}
        unknown = sorted(set(values) - allowed)
        if unknown:
            raise ValueError(f"unknown memory signal delta(s): {', '.join(unknown)}")
        for value in values.values():
            if not math.isfinite(value):
                raise ValueError("signal deltas must be finite")
        return dict(values)

    def delta_for(self, signal: MemorySignal) -> float:
        """Return the configured deterministic delta for one signal."""
        return self.signal_deltas[signal.value]


class MemoryEdgeUpdate(MemoryModel):
    """One source-to-target memory weight update."""

    source_id: str
    target_id: str
    signal: MemorySignal
    delta: float
    old_weight: float
    new_weight: float
    evidence: tuple[str, ...] = ()
    authority_notice: str = MEMORY_UPDATES_AUTHORITY_NOTICE

    @field_validator("source_id", "target_id")
    @classmethod
    def _non_empty_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("memory update endpoints must not be empty")
        return normalized

    @field_validator("delta", "old_weight", "new_weight")
    @classmethod
    def _finite_number(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("memory update weights must be finite")
        return round(value, 6)

    @field_validator("evidence", mode="before")
    @classmethod
    def _evidence(cls, value: object) -> tuple[str, ...]:
        return tuple(sorted(set(_interesting_refs(value))))


class MemoryUpdateRun(MemoryModel):
    """One rebuildable memory update run sidecar."""

    schema_version: Literal[1] = 1
    run_id: str
    source_kind: Literal["workflow", "campaign"]
    source_id: str
    generated_at: datetime = DETERMINISTIC_GENERATED_AT
    updates: tuple[MemoryEdgeUpdate, ...] = ()
    accepted_write_performed: Literal[False] = False
    yaml_artifacts_mutated: Literal[False] = False
    authority_notice: str = MEMORY_UPDATES_AUTHORITY_NOTICE

    @field_validator("run_id")
    @classmethod
    def _run_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("source_id")
    @classmethod
    def _source_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())


class MemoryWeightEdge(MemoryModel):
    """Aggregated memory weight for one edge."""

    source_id: str
    target_id: str
    weight: float
    signals: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()

    @field_validator("weight")
    @classmethod
    def _weight(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("memory weight must be finite")
        return round(value, 6)


class MemoryWeightStore(MemoryModel):
    """Rebuildable sidecar weight store."""

    schema_version: Literal[1] = 1
    generated_at: datetime = DETERMINISTIC_GENERATED_AT
    weight_count: int
    edges: tuple[MemoryWeightEdge, ...] = ()
    authority_notice: str = MEMORY_UPDATES_AUTHORITY_NOTICE


class MemoryExplainResult(MemoryModel):
    """Explanation for one artifact or memory target."""

    schema_version: Literal[1] = 1
    artifact_id: str
    edges: tuple[MemoryWeightEdge, ...] = ()
    authority_notice: str = MEMORY_UPDATES_AUTHORITY_NOTICE

    @field_validator("artifact_id")
    @classmethod
    def _artifact_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())


class MemoryUpdateResult(MemoryModel):
    """Write result for one memory update command."""

    schema_version: Literal[1] = 1
    run: MemoryUpdateRun
    weights: MemoryWeightStore
    run_path: str
    weights_path: str = MEMORY_WEIGHTS_PATH.as_posix()
    accepted_write_performed: Literal[False] = False
    yaml_artifacts_mutated: Literal[False] = False
    authority_notice: str = MEMORY_UPDATES_AUTHORITY_NOTICE


def default_memory_update_policy() -> MemoryUpdatePolicy:
    """Return the v1 deterministic policy."""
    return MemoryUpdatePolicy(
        signal_deltas={
            MemorySignal.RETRIEVED.value: 0.1,
            MemorySignal.USED_IN_PLAN.value: 0.25,
            MemorySignal.USED_IN_ATTEMPT.value: 0.5,
            MemorySignal.USED_IN_SUCCESSFUL_DRAFT.value: 1.0,
            MemorySignal.CHECKER_PASS.value: 0.75,
            MemorySignal.CHECKER_FAIL.value: -0.5,
            MemorySignal.GATE_BLOCKED.value: -0.75,
            MemorySignal.REVIEW_REQUESTED.value: 0.25,
            MemorySignal.HUMAN_ACCEPT_REFERENCE.value: 1.0,
            MemorySignal.REPEAT_FAILURE.value: -0.5,
            MemorySignal.UNSAFE_OUTPUT.value: -1.0,
        }
    )


def update_memory_from_workflow(
    context: RepoContext,
    workflow_id: str,
    *,
    policy: MemoryUpdatePolicy | None = None,
) -> MemoryUpdateResult:
    """Build and persist a workflow-derived update run, then rebuild weights."""
    policy = policy or default_memory_update_policy()
    try:
        workflow = load_workflow(context, workflow_id)
    except WorkflowError as exc:
        raise MemoryUpdateError(str(exc)) from exc

    updates = _updates_from_workflow(workflow, policy=policy)
    run = MemoryUpdateRun(
        run_id=f"memory.update.workflow.{workflow.workflow_id}",
        source_kind="workflow",
        source_id=workflow.workflow_id,
        updates=tuple(updates),
    )
    run_path = write_memory_update_run(context, run)
    weights = rebuild_memory_weights(context, policy=policy)
    return MemoryUpdateResult(
        run=run,
        weights=weights,
        run_path=run_path.as_posix(),
    )


def update_memory_from_campaign(
    context: RepoContext,
    campaign_id: str,
    *,
    policy: MemoryUpdatePolicy | None = None,
) -> MemoryUpdateResult:
    """Build and persist a campaign-derived update run, then rebuild weights."""
    policy = policy or default_memory_update_policy()
    try:
        loaded = load_campaign(context, campaign_id)
    except CampaignError as exc:
        raise MemoryUpdateError(str(exc)) from exc

    updates = _updates_from_campaign(loaded.campaign, policy=policy)
    run = MemoryUpdateRun(
        run_id=f"memory.update.campaign.{loaded.campaign.campaign_id}",
        source_kind="campaign",
        source_id=loaded.campaign.campaign_id,
        updates=tuple(updates),
    )
    run_path = write_memory_update_run(context, run)
    weights = rebuild_memory_weights(context, policy=policy)
    return MemoryUpdateResult(
        run=run,
        weights=weights,
        run_path=run_path.as_posix(),
    )


def write_memory_update_run(context: RepoContext, run: MemoryUpdateRun) -> Path:
    """Write one deterministic memory update run sidecar."""
    relative_path = memory_update_run_path(run.run_id)
    target = context.resolve(relative_path)
    _ensure_runtime_path(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(run.to_json(), encoding="utf-8", newline="\n")
    return relative_path


def rebuild_memory_weights(
    context: RepoContext,
    *,
    policy: MemoryUpdatePolicy | None = None,
) -> MemoryWeightStore:
    """Rebuild aggregate weights from update-run sidecars."""
    policy = policy or default_memory_update_policy()
    aggregate: dict[tuple[str, str], float] = defaultdict(float)
    signals: dict[tuple[str, str], set[str]] = defaultdict(set)
    evidence: dict[tuple[str, str], set[str]] = defaultdict(set)
    for run in load_memory_update_runs(context):
        for update in run.updates:
            key = (update.source_id, update.target_id)
            aggregate[key] = _clamp(
                aggregate[key] + update.delta,
                minimum=policy.min_weight,
                maximum=policy.max_weight,
            )
            signals[key].add(update.signal.value)
            evidence[key].update(update.evidence)

    edges = tuple(
        MemoryWeightEdge(
            source_id=source,
            target_id=target,
            weight=weight,
            signals=tuple(sorted(signals[(source, target)])),
            evidence=tuple(sorted(evidence[(source, target)])),
        )
        for (source, target), weight in sorted(aggregate.items())
    )
    store = MemoryWeightStore(weight_count=len(edges), edges=edges)
    write_memory_weights(context, store)
    return store


def explain_memory_weight(
    context: RepoContext,
    artifact_id: str,
) -> MemoryExplainResult:
    """Explain sidecar weights touching one artifact ID."""
    resolved = validate_artifact_id(artifact_id.strip())
    store = load_memory_weights(context)
    edges = tuple(
        edge
        for edge in store.edges
        if edge.source_id == resolved or edge.target_id == resolved
    )
    return MemoryExplainResult(artifact_id=resolved, edges=edges)


def write_memory_weights(context: RepoContext, store: MemoryWeightStore) -> Path:
    """Persist aggregate memory weights."""
    target = context.resolve(MEMORY_WEIGHTS_PATH)
    _ensure_runtime_path(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(store.to_json(), encoding="utf-8", newline="\n")
    return MEMORY_WEIGHTS_PATH


def load_memory_weights(context: RepoContext) -> MemoryWeightStore:
    """Load aggregate memory weights."""
    target = context.resolve(MEMORY_WEIGHTS_PATH)
    _ensure_runtime_path(context, target)
    if not target.is_file():
        raise MemoryUpdateError(
            "memory weights sidecar is missing; run "
            "`cosheaf memory rebuild` first"
        )
    try:
        return MemoryWeightStore.model_validate_json(target.read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError) as exc:
        raise MemoryUpdateError(f"invalid memory weights sidecar: {exc}") from exc


def load_memory_update_runs(context: RepoContext) -> tuple[MemoryUpdateRun, ...]:
    """Load all memory update-run sidecars."""
    root = context.resolve(MEMORY_UPDATE_RUNS_ROOT)
    _ensure_runtime_path(context, root)
    if not root.exists():
        return ()
    runs: list[MemoryUpdateRun] = []
    for path in sorted(root.glob("*.json")):
        try:
            runs.append(MemoryUpdateRun.model_validate_json(path.read_text("utf-8")))
        except (OSError, ValidationError, ValueError) as exc:
            relative = repo_relative_posix(context.repo_root, path)
            raise MemoryUpdateError(
                f"invalid memory update run sidecar: {relative}: {exc}"
            ) from exc
    return tuple(sorted(runs, key=lambda run: run.run_id))


def memory_update_run_path(run_id: str) -> Path:
    """Return the deterministic update-run path."""
    return MEMORY_UPDATE_RUNS_ROOT / f"{validate_artifact_id(run_id)}.json"


def _updates_from_workflow(
    workflow: Any,
    *,
    policy: MemoryUpdatePolicy,
) -> list[MemoryEdgeUpdate]:
    builder = _UpdateBuilder(source_id=workflow.workflow_id, policy=policy)
    if workflow.issue_id:
        builder.add(
            workflow.issue_id,
            MemorySignal.USED_IN_PLAN,
            evidence=f".cosheaf/workflows/{workflow.workflow_id}/workflow.json",
        )
    for step in workflow.steps:
        if _interesting_ref(step.action):
            builder.add(step.action, MemorySignal.USED_IN_ATTEMPT)
        for ref in _interesting_refs(step.input_refs):
            builder.add(ref, MemorySignal.RETRIEVED)
        for ref in _interesting_refs(step.output_refs):
            builder.add(ref, MemorySignal.USED_IN_ATTEMPT)
        if step.status == "blocked":
            builder.add(workflow.issue_id, MemorySignal.GATE_BLOCKED)
        elif step.status in {"failed", "error"}:
            builder.add(workflow.issue_id, MemorySignal.REPEAT_FAILURE)
    return builder.updates


def _updates_from_campaign(
    campaign: Any,
    *,
    policy: MemoryUpdatePolicy,
) -> list[MemoryEdgeUpdate]:
    builder = _UpdateBuilder(source_id=campaign.campaign_id, policy=policy)
    builder.add(campaign.issue_id, MemorySignal.USED_IN_PLAN)
    for attempt in campaign.attempts:
        for ref in _interesting_refs(attempt.workflow_refs):
            builder.add(ref, MemorySignal.USED_IN_ATTEMPT)
        for ref in _interesting_refs(attempt.check_report_refs):
            builder.add(ref, MemorySignal.USED_IN_ATTEMPT)
        for ref in _interesting_refs(attempt.proof_obligation_refs):
            builder.add(ref, MemorySignal.USED_IN_ATTEMPT)
        for ref in _interesting_refs(attempt.handoff_refs):
            builder.add(ref, MemorySignal.USED_IN_ATTEMPT)
        for ref in _interesting_refs(attempt.benchmark_report_refs):
            builder.add(ref, MemorySignal.USED_IN_ATTEMPT)
        for ref in _interesting_refs(attempt.draft_proposal_refs):
            signal = (
                MemorySignal.USED_IN_SUCCESSFUL_DRAFT
                if attempt.outcome.value == "result"
                else MemorySignal.USED_IN_ATTEMPT
            )
            builder.add(ref, signal)
        if attempt.outcome.value == "failure":
            builder.add(campaign.issue_id, MemorySignal.REPEAT_FAILURE)
        elif attempt.outcome.value == "blocked":
            builder.add(campaign.issue_id, MemorySignal.GATE_BLOCKED)
        for finding in attempt.risk_findings:
            if finding.severity.value == "blocker":
                builder.add(
                    finding.path or campaign.campaign_id,
                    MemorySignal.UNSAFE_OUTPUT,
                )
    for finding in campaign.risk_findings:
        if finding.severity.value == "blocker":
            builder.add(
                finding.path or campaign.campaign_id,
                MemorySignal.UNSAFE_OUTPUT,
            )
    return builder.updates


class _UpdateBuilder:
    def __init__(self, *, source_id: str, policy: MemoryUpdatePolicy) -> None:
        self.source_id = source_id
        self.policy = policy
        self._weights: dict[str, float] = defaultdict(float)
        self.updates: list[MemoryEdgeUpdate] = []

    def add(
        self,
        target_id: str,
        signal: MemorySignal,
        *,
        evidence: str | Iterable[str] = (),
    ) -> None:
        target = str(target_id).strip()
        if not target:
            return
        delta = self.policy.delta_for(signal)
        old = self._weights[target]
        new = _clamp(
            old + delta,
            minimum=self.policy.min_weight,
            maximum=self.policy.max_weight,
        )
        self._weights[target] = new
        self.updates.append(
            MemoryEdgeUpdate(
                source_id=self.source_id,
                target_id=target,
                signal=signal,
                delta=delta,
                old_weight=old,
                new_weight=new,
                evidence=tuple(_interesting_refs(evidence)),
            )
        )


def _interesting_refs(value: object) -> tuple[str, ...]:
    refs: list[str] = []
    if isinstance(value, str):
        ref = _interesting_ref(value)
        if ref:
            refs.append(ref)
    elif isinstance(value, dict):
        for item in value.values():
            refs.extend(_interesting_refs(item))
    elif isinstance(value, Iterable):
        for item in value:
            refs.extend(_interesting_refs(item))
    return tuple(dict.fromkeys(refs))


def _interesting_ref(value: str) -> str | None:
    text = value.strip()
    if not text:
        return None
    try:
        return validate_artifact_id(text)
    except ValueError:
        pass
    normalized = normalize_repo_path(text)
    if (
        normalized
        and normalized != "."
        and not normalized.startswith("../")
        and ("/" in normalized or normalized.startswith(".cosheaf/"))
    ):
        return normalized
    return None


def _clamp(value: float, *, minimum: float, maximum: float) -> float:
    return round(max(minimum, min(maximum, value)), 6)


def _ensure_runtime_path(context: RepoContext, target: Path) -> None:
    root = context.repo_root.resolve()
    resolved = target.resolve()
    if resolved != root and root not in resolved.parents:
        raise MemoryUpdateError(f"memory sidecar path escapes repository: {target}")
    relative = repo_relative_posix(context.repo_root, resolved)
    if relative.startswith("kb/accepted/") or "/accepted/" in relative:
        raise MemoryUpdateError("memory sidecars must not write accepted KB paths")


__all__ = [
    "MEMORY_UPDATES_AUTHORITY_NOTICE",
    "MEMORY_UPDATE_RUNS_ROOT",
    "MEMORY_WEIGHTS_PATH",
    "MemoryEdgeUpdate",
    "MemoryExplainResult",
    "MemorySignal",
    "MemoryUpdateError",
    "MemoryUpdatePolicy",
    "MemoryUpdateResult",
    "MemoryUpdateRun",
    "MemoryWeightEdge",
    "MemoryWeightStore",
    "default_memory_update_policy",
    "explain_memory_weight",
    "load_memory_update_runs",
    "load_memory_weights",
    "memory_update_run_path",
    "rebuild_memory_weights",
    "update_memory_from_campaign",
    "update_memory_from_workflow",
    "write_memory_update_run",
    "write_memory_weights",
]
