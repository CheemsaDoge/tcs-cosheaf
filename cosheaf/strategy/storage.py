"""Runtime storage for generated strategy plans."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from cosheaf.core.paths import repo_relative_posix
from cosheaf.research.run import (
    ResearchRunCommandRecord,
    ResearchRunCommandStatus,
    ResearchRunOutputKind,
    ResearchRunOutputRef,
    ResearchRunRecord,
    load_research_run,
)
from cosheaf.storage.repo import RepoContext
from cosheaf.storage.writer import write_yaml_deterministic
from cosheaf.strategy.models import (
    STRATEGY_AUTHORITY_NOTICE,
    StrategyError,
    StrategyPlan,
    StrategyTaskGraph,
    StrategyTaskNode,
    StrategyTaskReference,
    StrategyTaskReferenceKind,
    StrategyTaskStatus,
)

STRATEGY_RUNTIME_ROOT = Path(".cosheaf") / "strategy"
STRATEGY_REVIEW_ROOT = Path("reviews") / "strategy"


@dataclass(frozen=True)
class StrategyPlanStorageResult:
    """One loaded or written runtime strategy plan."""

    plan: StrategyPlan
    relative_path: Path
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "strategy_plan",
            "plan_id": self.plan.plan_id,
            "path": self.relative_path.as_posix(),
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": STRATEGY_AUTHORITY_NOTICE,
            "plan": self.plan.to_dict(),
        }


@dataclass(frozen=True)
class StrategyPlanUpdateResult:
    """Result from updating a plan with research-run provenance."""

    plan: StrategyPlan
    run_id: str
    relative_path: Path
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "strategy_plan_update",
            "plan_id": self.plan.plan_id,
            "run_id": self.run_id,
            "path": self.relative_path.as_posix(),
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": STRATEGY_AUTHORITY_NOTICE,
            "plan": self.plan.to_dict(),
        }


@dataclass(frozen=True)
class StrategyReviewExportResult:
    """Result for review export or dry-run export."""

    plan: StrategyPlan
    relative_path: Path
    written_paths: tuple[Path, ...]
    dry_run: bool
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "strategy_review_export",
            "plan_id": self.plan.plan_id,
            "path": self.relative_path.as_posix(),
            "written_paths": [path.as_posix() for path in self.written_paths],
            "dry_run": self.dry_run,
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": STRATEGY_AUTHORITY_NOTICE,
            "plan": self.plan.to_dict(),
        }


def write_strategy_plan(
    context: RepoContext,
    plan: StrategyPlan,
) -> StrategyPlanStorageResult:
    """Persist a generated strategy plan under runtime storage."""
    relative_path = strategy_plan_path(plan.plan_id)
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(plan.to_json(), encoding="utf-8", newline="\n")
    return StrategyPlanStorageResult(plan=plan, relative_path=relative_path)


def attach_context_reference(
    context: RepoContext,
    plan: StrategyPlan,
    context_dir: Path,
) -> StrategyPlan:
    """Attach a repo-local context-pack reference to the context task."""
    relative_path = _context_pack_relative_path(context, context_dir, plan.issue_id)
    reference = StrategyTaskReference(
        kind=StrategyTaskReferenceKind.CONTEXT_PACK,
        identifier=plan.issue_id,
        path=relative_path,
        status="completed",
        summary="strategy plan was generated from this context pack",
    )
    return _replace_plan_nodes(
        plan,
        {
            "task.context-build": lambda node: _node_with_references(
                node,
                references=(reference,),
                status=StrategyTaskStatus.COMPLETED,
            )
        },
    )


def load_strategy_plan(
    context: RepoContext,
    plan_id: str,
) -> StrategyPlanStorageResult:
    """Load one runtime strategy plan."""
    relative_path = strategy_plan_path(plan_id)
    target = context.resolve(relative_path)
    if not target.is_file():
        raise StrategyError(
            f"strategy plan not found: {plan_id}",
            code="strategy_plan_not_found",
            remediation="Run `cosheaf strategy plan --issue <issue-id>` first.",
            details={"path": relative_path.as_posix()},
        )
    try:
        raw = json.loads(target.read_text(encoding="utf-8-sig"))
        plan = StrategyPlan.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValueError, ValidationError) as exc:
        raise StrategyError(
            f"strategy plan failed validation: {exc}",
            code="strategy_plan_validation_failed",
            remediation="Regenerate the strategy plan or repair the runtime JSON.",
            details={"path": relative_path.as_posix()},
        ) from exc
    return StrategyPlanStorageResult(plan=plan, relative_path=relative_path)


def load_strategy_plans(context: RepoContext) -> tuple[StrategyPlanStorageResult, ...]:
    """Load valid runtime strategy plans from `.cosheaf/strategy`."""
    root = context.resolve(STRATEGY_RUNTIME_ROOT)
    if not root.exists():
        return ()
    results: list[StrategyPlanStorageResult] = []
    for path in sorted(root.glob("*/strategy.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
            plan = StrategyPlan.model_validate(raw)
            relative_path = Path(repo_relative_posix(context.repo_root, path))
        except (OSError, json.JSONDecodeError, ValueError, ValidationError):
            continue
        results.append(
            StrategyPlanStorageResult(plan=plan, relative_path=relative_path)
        )
    return tuple(sorted(results, key=lambda result: result.plan.plan_id))


def update_strategy_plan_from_run(
    context: RepoContext,
    *,
    plan_id: str,
    run_id: str,
) -> StrategyPlanUpdateResult:
    """Update strategy task statuses/references from research-run provenance."""
    loaded_plan = load_strategy_plan(context, plan_id)
    loaded_run = load_research_run(context, run_id)
    plan = _plan_with_research_run(loaded_plan.plan, loaded_run.record)
    write_strategy_plan(context, plan)
    return StrategyPlanUpdateResult(
        plan=plan,
        run_id=loaded_run.record.run_id,
        relative_path=loaded_plan.relative_path,
    )


def export_strategy_review(
    context: RepoContext,
    *,
    plan_id: str,
    dry_run: bool,
) -> StrategyReviewExportResult:
    """Export a strategy plan to non-authoritative review context."""
    loaded = load_strategy_plan(context, plan_id)
    relative_path = STRATEGY_REVIEW_ROOT / f"{loaded.plan.plan_id}.yaml"
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    if target.exists() and not dry_run:
        raise StrategyError(
            f"strategy review export already exists: {relative_path.as_posix()}",
            code="strategy_review_export_exists",
            remediation="Inspect the existing review export before replacing it.",
            details={"path": relative_path.as_posix()},
        )
    written: tuple[Path, ...] = ()
    if not dry_run:
        write_yaml_deterministic(target, loaded.plan.to_dict())
        written = (relative_path,)
    return StrategyReviewExportResult(
        plan=loaded.plan,
        relative_path=relative_path,
        written_paths=written,
        dry_run=dry_run,
    )


def strategy_plan_path(plan_id: str) -> Path:
    """Return runtime path for one strategy plan ID."""
    plan = StrategyPlan.model_validate(
        {
            "schema_version": 1,
            "plan_id": plan_id,
            "issue_id": plan_id.removeprefix("strategy.").removesuffix(".plan"),
            "created_at": "2026-01-01T00:00:00Z",
            "problem": {
                "issue_id": plan_id.removeprefix("strategy.").removesuffix(".plan"),
                "title": "placeholder",
            },
            "graph": {"nodes": [], "edges": []},
            "next_steps": [],
            "authority_notice": STRATEGY_AUTHORITY_NOTICE,
            "accepted_write_performed": False,
        }
    )
    return STRATEGY_RUNTIME_ROOT / plan.plan_id / "strategy.json"


def _plan_with_research_run(
    plan: StrategyPlan,
    record: ResearchRunRecord,
) -> StrategyPlan:
    updates: dict[str, list[StrategyTaskReference]] = {}
    statuses: dict[str, StrategyTaskStatus] = {}

    _append_reference(
        updates,
        "task.review-runs",
        StrategyTaskReference(
            kind=StrategyTaskReferenceKind.RESEARCH_RUN,
            identifier=record.run_id,
            status=record.status.value,
            summary="research-run provenance attached to strategy plan",
        ),
    )
    statuses["task.review-runs"] = _status_from_run(record)

    for command in record.commands:
        node_id = _node_for_command(command)
        if node_id is None:
            node_id = "task.review-runs"
        _append_reference(updates, node_id, _reference_from_command(command))
        statuses[node_id] = _status_from_command(command)

    for output in record.context_packs:
        _append_reference(updates, "task.context-build", _reference_from_output(output))
        statuses.setdefault("task.context-build", StrategyTaskStatus.COMPLETED)
    for output in record.validation_reports:
        _append_reference(updates, "task.validate", _reference_from_output(output))
        statuses["task.validate"] = _status_from_output(output)
    for output in record.gate_reports:
        _append_reference(updates, "task.gate", _reference_from_output(output))
        statuses["task.gate"] = _status_from_output(output)
    for output in record.checked_counterexample_evidence_paths:
        _append_reference(
            updates,
            "task.counterexample-review",
            _reference_from_output(output),
        )
        statuses.setdefault(
            "task.counterexample-review",
            _status_from_output(output),
        )
    for output in record.failure_log_entries_added:
        _append_reference(
            updates,
            "task.review-failures",
            _reference_from_output(output),
        )
        statuses.setdefault("task.review-failures", _status_from_output(output))

    artifact_updates: dict[str, list[StrategyTaskReference]] = {}
    for artifact_id in (*record.artifacts_read, *record.artifacts_touched):
        _append_reference(
            artifact_updates,
            f"artifact.{artifact_id}",
            StrategyTaskReference(
                kind=StrategyTaskReferenceKind.ARTIFACT,
                identifier=artifact_id,
                status="touched"
                if artifact_id in record.artifacts_touched
                else "read",
                summary="artifact referenced by research-run provenance",
            ),
        )
        statuses[f"artifact.{artifact_id}"] = StrategyTaskStatus.COMPLETED

    for node_id, refs in artifact_updates.items():
        updates.setdefault(node_id, []).extend(refs)

    def transform(node: StrategyTaskNode) -> StrategyTaskNode:
        merged_refs = _dedupe_references(
            (*node.references, *updates.get(node.node_id, []))
        )
        related_runs = node.related_research_run_ids
        if node.node_id == "task.review-runs":
            related_runs = _dedupe_text((*related_runs, record.run_id))
        status = statuses.get(node.node_id, node.status)
        return node.model_copy(
            update={
                "references": merged_refs,
                "related_research_run_ids": related_runs,
                "status": status,
            }
        )

    return _replace_plan_nodes(
        plan,
        {node.node_id: transform for node in plan.graph.nodes},
    )


def _replace_plan_nodes(
    plan: StrategyPlan,
    transforms: dict[str, Any],
) -> StrategyPlan:
    nodes = []
    for node in plan.graph.nodes:
        transform = transforms.get(node.node_id)
        nodes.append(transform(node) if transform else node)
    graph = StrategyTaskGraph(nodes=tuple(nodes), edges=plan.graph.edges)
    return StrategyPlan.model_validate(
        plan.model_copy(update={"graph": graph}).to_dict()
    )


def _node_with_references(
    node: StrategyTaskNode,
    *,
    references: tuple[StrategyTaskReference, ...],
    status: StrategyTaskStatus,
) -> StrategyTaskNode:
    return node.model_copy(
        update={
            "references": _dedupe_references((*node.references, *references)),
            "status": status,
        }
    )


def _context_pack_relative_path(
    context: RepoContext,
    context_dir: Path,
    issue_id: str,
) -> str:
    target = context_dir if context_dir.is_absolute() else context.resolve(context_dir)
    try:
        relative = repo_relative_posix(context.repo_root, target)
    except ValueError as exc:
        raise StrategyError(
            "strategy context path must be repository-local",
            code="invalid_strategy_path",
            remediation="Pass a context directory inside the repository.",
            details={"path": str(context_dir)},
        ) from exc
    if not target.is_dir():
        raise StrategyError(
            f"strategy context directory not found: {relative}",
            code="strategy_context_not_found",
            remediation="Run `cosheaf context build <issue-id>` first.",
            details={"path": relative},
        )
    audit_path = target / "RETRIEVAL_AUDIT.json"
    if audit_path.is_file():
        try:
            audit = json.loads(audit_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StrategyError(
                f"strategy context audit is unreadable: {relative}",
                code="strategy_context_invalid",
                remediation="Regenerate the context pack and retry.",
                details={"path": relative},
            ) from exc
        audit_issue = str(audit.get("issue_id", "")).strip()
        if audit_issue and audit_issue != issue_id:
            raise StrategyError(
                "strategy context issue does not match requested issue",
                code="strategy_context_issue_mismatch",
                remediation="Pass a context pack built for the same issue.",
                details={"context_issue": audit_issue, "issue_id": issue_id},
            )
    return relative


def _node_for_command(command: ResearchRunCommandRecord) -> str | None:
    argv = tuple(command.argv)
    if len(argv) >= 2 and argv[:2] == ("cosheaf", "validate"):
        return "task.validate"
    if len(argv) >= 3 and argv[:3] == ("cosheaf", "gate", "run"):
        return "task.gate"
    if len(argv) >= 3 and argv[:3] == ("cosheaf", "context", "build"):
        return "task.context-build"
    return None


def _reference_from_command(command: ResearchRunCommandRecord) -> StrategyTaskReference:
    return StrategyTaskReference(
        kind=StrategyTaskReferenceKind.COMMAND,
        identifier=" ".join(command.argv),
        path=command.stdout_path or command.stderr_path or "",
        status=command.status.value,
        summary=_command_summary(command),
    )


def _command_summary(command: ResearchRunCommandRecord) -> str:
    if command.status is ResearchRunCommandStatus.SKIPPED:
        return (
            command.skipped_reason
            or "Skipped research-run steps are not pass evidence."
        )
    if command.status is ResearchRunCommandStatus.UNAVAILABLE:
        return command.unavailable_reason or "command unavailable"
    if command.exit_code is not None:
        return f"exit_code={command.exit_code}"
    return command.status.value


def _reference_from_output(output: ResearchRunOutputRef) -> StrategyTaskReference:
    return StrategyTaskReference(
        kind=_reference_kind_from_output(output.kind),
        identifier=output.identifier or "",
        path=output.path or "",
        status=output.status or "",
        summary=output.summary or "",
    )


def _reference_kind_from_output(
    kind: ResearchRunOutputKind,
) -> StrategyTaskReferenceKind:
    if kind is ResearchRunOutputKind.CONTEXT_PACK:
        return StrategyTaskReferenceKind.CONTEXT_PACK
    if kind is ResearchRunOutputKind.CHECKED_COUNTEREXAMPLE_EVIDENCE:
        return StrategyTaskReferenceKind.CHECKED_COUNTEREXAMPLE_EVIDENCE
    if kind is ResearchRunOutputKind.VALIDATION_REPORT:
        return StrategyTaskReferenceKind.VALIDATION_REPORT
    if kind is ResearchRunOutputKind.GATE_REPORT:
        return StrategyTaskReferenceKind.GATE_REPORT
    if kind is ResearchRunOutputKind.FAILURE_LOG:
        return StrategyTaskReferenceKind.FAILURE_LOG
    return StrategyTaskReferenceKind.OTHER


def _status_from_run(record: ResearchRunRecord) -> StrategyTaskStatus:
    if record.status.value == "failed":
        return StrategyTaskStatus.FAILED
    if record.status.value in {"cancelled", "blocked"}:
        return StrategyTaskStatus.BLOCKED
    if record.status.value == "completed":
        return StrategyTaskStatus.COMPLETED
    return StrategyTaskStatus.READY


def _status_from_command(command: ResearchRunCommandRecord) -> StrategyTaskStatus:
    if command.status in {
        ResearchRunCommandStatus.FAILED,
        ResearchRunCommandStatus.ERROR,
    }:
        return StrategyTaskStatus.FAILED
    if command.status in {
        ResearchRunCommandStatus.SKIPPED,
        ResearchRunCommandStatus.UNAVAILABLE,
    }:
        return StrategyTaskStatus.SKIPPED
    return StrategyTaskStatus.COMPLETED


def _status_from_output(output: ResearchRunOutputRef) -> StrategyTaskStatus:
    status = (output.status or "").strip().lower()
    if status in {"failed", "error"}:
        return StrategyTaskStatus.FAILED
    if status in {"skipped", "unavailable"}:
        return StrategyTaskStatus.SKIPPED
    if status:
        return StrategyTaskStatus.COMPLETED
    return StrategyTaskStatus.READY


def _append_reference(
    mapping: dict[str, list[StrategyTaskReference]],
    node_id: str,
    reference: StrategyTaskReference,
) -> None:
    mapping.setdefault(node_id, []).append(reference)


def _dedupe_references(
    references: tuple[StrategyTaskReference, ...],
) -> tuple[StrategyTaskReference, ...]:
    seen: set[tuple[str, str, str, str, str]] = set()
    result: list[StrategyTaskReference] = []
    for reference in references:
        key = (
            reference.kind.value,
            reference.identifier,
            reference.path,
            reference.status,
            reference.summary,
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(reference)
    return tuple(result)


def _dedupe_text(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _ensure_repo_local(context: RepoContext, target: Path) -> None:
    try:
        target.resolve().relative_to(context.repo_root.resolve())
    except ValueError as exc:
        raise StrategyError(
            "strategy plan target must stay repository-local",
            code="invalid_strategy_path",
            remediation="Use the controlled .cosheaf/strategy runtime path.",
        ) from exc


__all__ = [
    "STRATEGY_RUNTIME_ROOT",
    "STRATEGY_REVIEW_ROOT",
    "StrategyPlanStorageResult",
    "StrategyPlanUpdateResult",
    "StrategyReviewExportResult",
    "attach_context_reference",
    "export_strategy_review",
    "load_strategy_plan",
    "load_strategy_plans",
    "strategy_plan_path",
    "update_strategy_plan_from_run",
    "write_strategy_plan",
]
