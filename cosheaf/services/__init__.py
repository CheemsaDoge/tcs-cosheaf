"""Typed service layer shared by CLI and future agent-access surfaces.

Services are thin boundaries over existing repository logic. They return typed
results and enforce the same local path, public/private KB, gate, review, and
promotion boundaries as the CLI.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from cosheaf.agent.context_pack import (
    CONTEXT_MAX_CARDS,
    ContextPackResult,
    build_context_pack,
    show_context_pack,
)
from cosheaf.agent.local_runner import (
    LocalWorkerRunConfig,
    LocalWorkerRunner,
    LocalWorkerRunResult,
)
from cosheaf.agent.orchestrator_planner import plan_for_issue
from cosheaf.agent.orchestrator_state import Plan, ReducerResult
from cosheaf.agent.orchestrator_stub import OrchestratorStub, TaskCompletionResult
from cosheaf.agent.task import AgentTask, WorkerType
from cosheaf.agent.worker_bundle_v2 import (
    WorkerBundleV2,
    reduce_worker_bundle_v2,
    validate_worker_bundle_v2,
)
from cosheaf.config.workspace import KbRootConfig
from cosheaf.core.artifact import BaseArtifact
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import lifecycle_artifact_path
from cosheaf.core.status import ArtifactStatus, ArtifactType
from cosheaf.gates.gatekeeper import (
    GatekeeperRunResult,
    ValidationReport,
    run_gatekeeper,
    validate_artifact_file,
    validate_repository,
)
from cosheaf.memory import (
    ArtifactCard,
    ArtifactCardStatus,
    RetrievalResult,
    RetrievalRole,
    build_artifact_cards,
    search_artifact_cards,
)
from cosheaf.services.context_policy import ContextSendPolicyService
from cosheaf.services.models import ErrorResult
from cosheaf.storage.loader import LoadedRecord, LoadError, load_artifacts
from cosheaf.storage.repo import RepoContext
from cosheaf.storage.writer import write_yaml_deterministic


@dataclass(frozen=True)
class KbRootInfo:
    """One KB root exposed through the service boundary."""

    name: str
    path: str
    readonly: bool
    priority: int


@dataclass(frozen=True)
class WorkspaceInfoResult:
    """Typed workspace information for machine and CLI callers."""

    name: str
    repo_root: Path
    mode: str
    kb_roots: tuple[KbRootInfo, ...]


@dataclass(frozen=True)
class ArtifactWriteResult:
    """Result of a controlled draft/pre-accepted artifact write."""

    artifact: BaseArtifact
    relative_path: Path


class ServiceError(ValueError):
    """Expected service-layer failure with a stable machine-readable code."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        remediation: str,
        blocking: bool = True,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.remediation = remediation
        self.blocking = blocking
        self.details = dict(details or {})

    def to_error_result(self) -> ErrorResult:
        """Convert this service error to the public agent-access error DTO."""
        return ErrorResult(
            code=self.code,
            message=str(self),
            remediation=self.remediation,
            blocking=self.blocking,
            details=self.details,
        )


class DraftWriteServiceError(ServiceError):
    """Raised for expected draft-write service failures."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "draft_write_failed",
        remediation: str = (
            "Fix the draft artifact request and retry. Accepted knowledge must "
            "enter through explicit review, gates, and promotion."
        ),
        blocking: bool = True,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message,
            code=code,
            remediation=remediation,
            blocking=blocking,
            details=details,
        )


class WorkspaceService:
    """Service for workspace inspection."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context

    def info(self) -> WorkspaceInfoResult:
        """Return active workspace metadata and ordered KB roots."""
        config = self.context.workspace_config
        return WorkspaceInfoResult(
            name=config.name,
            repo_root=self.context.repo_root,
            mode="configured" if config.configured else "legacy",
            kb_roots=tuple(
                KbRootInfo(
                    name=root.name,
                    path=root.path,
                    readonly=root.readonly,
                    priority=root.priority,
                )
                for root in config.ordered_kb
            ),
        )


class ValidationService:
    """Service for repository and artifact validation."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context

    def validate_repository(self) -> ValidationReport:
        """Validate repository YAML records and invariants."""
        return validate_repository(self.context)

    def validate_artifact_file(self, path: str | Path) -> ValidationReport:
        """Validate one repository-local artifact YAML file."""
        return validate_artifact_file(self.context, Path(path))


class GateService:
    """Service for gatekeeper execution."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context

    def run(
        self,
        *,
        persist_review: bool = False,
        pr_checklist_path: str | Path | None = None,
        timestamp: str | None = None,
    ) -> GatekeeperRunResult:
        """Run gatekeeper checks and return written report metadata."""
        return run_gatekeeper(
            self.context,
            persist_review=persist_review,
            pr_checklist_path=Path(pr_checklist_path)
            if pr_checklist_path is not None
            else None,
            timestamp=timestamp,
        )


class MemorySearchService:
    """Service for deterministic artifact-card search."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context

    def cards(
        self,
        *,
        issue_id: str | None = None,
        status: ArtifactCardStatus | None = None,
    ) -> tuple[ArtifactCard, ...]:
        """Build compact artifact cards from existing repository metadata."""
        return build_artifact_cards(
            self.context,
            issue_id=issue_id,
            status=status,
        )

    def search(
        self,
        query: str,
        *,
        issue_id: str | None = None,
        status: ArtifactCardStatus | None = None,
        max_cards: int = CONTEXT_MAX_CARDS,
        seed_artifacts: Sequence[str] = (),
        pinned_artifacts: Sequence[str] = (),
        include_refuted: bool = False,
        include_obsolete: bool = False,
    ) -> RetrievalResult:
        """Search artifact cards with deterministic local scoring."""
        return search_artifact_cards(
            self.context,
            query=query,
            issue_id=issue_id,
            status=status,
            max_cards=max_cards,
            seed_artifacts=tuple(seed_artifacts),
            pinned_artifacts=tuple(pinned_artifacts),
            include_refuted=include_refuted,
            include_obsolete=include_obsolete,
        )


class ContextPackService:
    """Service for bounded issue-scoped context packs."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context

    def build(
        self,
        issue_id: str,
        *,
        role: RetrievalRole | str = RetrievalRole.ORCHESTRATOR,
        max_cards: int = CONTEXT_MAX_CARDS,
        max_full_artifacts: int | None = None,
        public_only: bool = False,
    ) -> ContextPackResult:
        """Build a deterministic context pack for an issue."""
        return build_context_pack(
            self.context,
            issue_id,
            role=role,
            max_cards=max_cards,
            max_full_artifacts=max_full_artifacts,
            public_only=public_only,
        )

    def show(
        self,
        issue_id: str,
        *,
        role: RetrievalRole | str = RetrievalRole.ORCHESTRATOR,
        max_cards: int = CONTEXT_MAX_CARDS,
        max_full_artifacts: int | None = None,
        public_only: bool = False,
    ) -> str:
        """Build and return the rendered main context document."""
        return show_context_pack(
            self.context,
            issue_id,
            role=role,
            max_cards=max_cards,
            max_full_artifacts=max_full_artifacts,
            public_only=public_only,
        )


class OrchestratorPlanService:
    """Service for deterministic issue-scoped orchestrator plans."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context

    def plan_for_issue(self, issue_id: str) -> Plan:
        """Create a deterministic plan for an existing issue without execution."""
        return plan_for_issue(self.context, issue_id)


class TaskService:
    """Service for local task records and explicit local worker runs."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context
        self.orchestrator = OrchestratorStub(context)

    def create_task(
        self,
        *,
        issue_id: str,
        worker_type: WorkerType | str,
    ) -> AgentTask:
        """Create an open local task for an existing issue."""
        return self.orchestrator.create_task(
            issue_id=issue_id,
            worker_type=worker_type,
        )

    def list_tasks(self) -> tuple[AgentTask, ...]:
        """List local tasks in deterministic order."""
        return self.orchestrator.list_tasks()

    def complete_task(
        self,
        *,
        task_id: str,
        bundle_path: str | Path,
    ) -> TaskCompletionResult:
        """Validate a worker output bundle and complete a task."""
        return self.orchestrator.complete_task(
            task_id=task_id,
            bundle_path=bundle_path,
        )

    def run_task(
        self,
        task_id: str,
        *,
        command: Sequence[str],
        timeout_seconds: int = 60,
        cwd: str | Path | None = None,
        bundle_path: str | Path | None = None,
    ) -> LocalWorkerRunResult:
        """Run an explicit local command for an existing task."""
        return LocalWorkerRunner(self.context).run_task(
            task_id,
            LocalWorkerRunConfig(
                command=command,
                timeout_seconds=timeout_seconds,
                cwd=cwd,
                bundle_path=bundle_path,
            ),
        )


class BundleValidationService:
    """Service for worker bundle v2 validation and reduction."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context

    def validate(self, bundle_path: str | Path) -> WorkerBundleV2:
        """Load and validate a worker bundle v2 manifest."""
        return validate_worker_bundle_v2(self.context, bundle_path)

    def reduce(self, bundle_path: str | Path, *, reducer_id: str) -> ReducerResult:
        """Validate and reduce a worker bundle v2 manifest."""
        return reduce_worker_bundle_v2(
            self.context,
            bundle_path,
            reducer_id=reducer_id,
        )


class DraftWriteService:
    """Service for controlled draft/pre-accepted lifecycle artifact writes."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context

    def create_artifact(
        self,
        *,
        artifact_id: str,
        artifact_type: ArtifactType,
        title: str,
        domain: Sequence[str],
        status: ArtifactStatus,
        statement: str,
        authors: Sequence[str],
        tags: Sequence[str],
        depends_on: Sequence[str],
        supersedes: Sequence[str],
        created_at: str | None = None,
    ) -> ArtifactWriteResult:
        """Create a deterministic draft/pre-accepted artifact YAML record."""
        if not domain:
            raise DraftWriteServiceError(
                "at least one --domain value is required",
                code="missing_required_domain",
                remediation="Provide at least one domain for the draft artifact.",
            )
        if status is ArtifactStatus.ACCEPTED:
            raise DraftWriteServiceError(
                "accepted artifacts must be promoted through a dedicated "
                "gate/review workflow",
                code="accepted_write_forbidden",
                remediation=(
                    "Create a draft or pre-accepted artifact first, then use the "
                    "explicit promotion workflow after review and gates pass."
                ),
            )

        try:
            validate_artifact_id(artifact_id)
        except ValueError as exc:
            raise DraftWriteServiceError(
                str(exc),
                code="invalid_artifact_id",
                remediation="Use a dot-separated lowercase artifact id.",
            ) from exc

        timestamp = _parse_artifact_timestamp(created_at)
        try:
            relative_path = _workspace_lifecycle_artifact_path(
                context=self.context,
                artifact_type=artifact_type,
                status=status,
                artifact_id=artifact_id,
            )
        except ValueError as exc:
            raise DraftWriteServiceError(
                str(exc),
                code="invalid_artifact_target_path",
                remediation=(
                    "Choose a status and artifact type with a valid draft path."
                ),
            ) from exc

        _ensure_artifact_id_is_available(self.context, artifact_id)
        target_path = self.context.resolve(relative_path)
        if target_path.exists():
            raise DraftWriteServiceError(
                f"artifact path already exists: {relative_path.as_posix()}",
                code="artifact_path_exists",
                remediation="Choose a new artifact id or inspect the existing path.",
                details={"path": relative_path.as_posix()},
            )

        try:
            artifact = BaseArtifact.model_validate(
                {
                    "id": artifact_id,
                    "type": artifact_type,
                    "title": title,
                    "domain": list(domain),
                    "status": status,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "authors": list(authors),
                    "depends_on": list(depends_on),
                    "supersedes": list(supersedes),
                    "tags": list(tags),
                    "statement": statement,
                    "evidence": [],
                    "review": {"state": "requested", "notes": "Created by CLI."},
                    "risk": {"level": "low", "notes": ""},
                }
            )
        except ValidationError as exc:
            raise DraftWriteServiceError(
                _format_pydantic_errors(exc),
                code="artifact_model_validation_failed",
                remediation="Fix the draft artifact fields and retry.",
            ) from exc

        write_yaml_deterministic(target_path, artifact)
        report = validate_artifact_file(self.context, relative_path)
        if report.ok:
            return ArtifactWriteResult(artifact=artifact, relative_path=relative_path)

        target_path.unlink(missing_ok=True)
        raise DraftWriteServiceError(
            _format_report_failures(report),
            code="artifact_file_validation_failed",
            remediation="Fix validation failures before writing the draft artifact.",
        )


def _parse_artifact_timestamp(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0)
    try:
        normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise DraftWriteServiceError(
            f"invalid --created-at timestamp: {value}",
            code="invalid_timestamp",
            remediation="Use an ISO 8601 timestamp with timezone information.",
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DraftWriteServiceError(
            "--created-at must include timezone information",
            code="timestamp_missing_timezone",
            remediation="Use an ISO 8601 timestamp with a timezone or trailing Z.",
        )
    return parsed.astimezone(UTC).replace(microsecond=0)


def _workspace_lifecycle_artifact_path(
    *,
    context: RepoContext,
    artifact_type: ArtifactType,
    status: ArtifactStatus,
    artifact_id: str,
) -> Path:
    legacy_path = lifecycle_artifact_path(artifact_type, status, artifact_id)
    if not context.workspace_config.configured:
        return legacy_path
    root = _default_writable_kb_root(context)
    return Path(root.path) / _strip_legacy_kb_prefix(legacy_path)


def _strip_legacy_kb_prefix(path: Path) -> Path:
    parts = path.parts
    if not parts or parts[0] != "kb":
        return path
    return Path(*parts[1:])


def _default_writable_kb_root(context: RepoContext) -> KbRootConfig:
    for root in context.workspace_config.ordered_kb:
        if not root.readonly and root.name == "private":
            return root
    for root in context.workspace_config.ordered_kb:
        if not root.readonly:
            return root
    raise DraftWriteServiceError(
        "no writable KB root is configured",
        code="no_writable_kb_root",
        remediation="Configure a writable private KB root before writing drafts.",
    )


def _ensure_artifact_id_is_available(context: RepoContext, artifact_id: str) -> None:
    records = _load_records_for_lifecycle(context)
    if any(record.id == artifact_id for record in records):
        raise DraftWriteServiceError(
            f"artifact already exists: {artifact_id}",
            code="artifact_id_exists",
            remediation="Choose a new artifact id or update the existing draft.",
            details={"artifact_id": artifact_id},
        )


def _load_records_for_lifecycle(context: RepoContext) -> tuple[LoadedRecord, ...]:
    try:
        return tuple(load_artifacts(context))
    except LoadError as exc:
        raise DraftWriteServiceError(
            f"cannot load repository records: {exc}",
            code="repository_load_failed",
            remediation="Fix repository load errors before writing new drafts.",
        ) from exc


def _format_pydantic_errors(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )


def _format_report_failures(report: ValidationReport) -> str:
    return "; ".join(
        f"{failure.gate} | {failure.source_path or '-'} | "
        f"{failure.artifact_id or '-'} | {failure.message}"
        for failure in report.failures
    )


__all__ = [
    "ArtifactWriteResult",
    "BundleValidationService",
    "ContextPackService",
    "ContextSendPolicyService",
    "DraftWriteService",
    "DraftWriteServiceError",
    "GateService",
    "KbRootInfo",
    "MemorySearchService",
    "OrchestratorPlanService",
    "ServiceError",
    "TaskService",
    "ValidationService",
    "WorkspaceInfoResult",
    "WorkspaceService",
]
