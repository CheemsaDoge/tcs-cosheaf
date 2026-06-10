"""Versioned DTOs for agent-access service, MCP, and provider surfaces."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cosheaf.agent.model_provider import (
    FinishReason,
    NetworkPolicy,
    ProviderName,
    ReasoningEffort,
    ToolPolicy,
)
from cosheaf.agent.task import WorkerType
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path
from cosheaf.core.status import ArtifactStatus, ArtifactType
from cosheaf.memory import ArtifactCardStatus, MemoryRootScope, RetrievalRole


class AgentAccessModel(BaseModel):
    """Strict versioned base class for public agent-access DTOs."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        use_enum_values=False,
        json_schema_extra={"additionalProperties": False},
    )

    schema_version: Literal[1] = 1

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable mapping."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic indented JSON with a trailing newline."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class AgentAccessStatus(StrEnum):
    """Normalized status for service and provider DTOs."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"


class ProviderRunStatus(StrEnum):
    """Normalized provider run status."""

    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class ContextPolicyMode(StrEnum):
    """Context exposure policy mode."""

    PUBLIC = "public"
    PRIVATE_RESEARCH = "private_research"


class KbRootPolicy(AgentAccessModel):
    """Public/private policy fields for an active workspace."""

    private_can_depend_on_public: bool
    public_can_depend_on_private: bool
    accepted_requires_source: bool


class AgentKbRoot(AgentAccessModel):
    """Machine-readable KB root metadata."""

    name: str
    path: str
    scope: MemoryRootScope
    readonly: bool
    priority: int

    @field_validator("name", "path")
    @classmethod
    def _non_empty_text(cls, value: str) -> str:
        return _validate_non_empty(value)

    @field_validator("path")
    @classmethod
    def _repo_local_path(cls, value: str) -> str:
        return _validate_repo_local_path(value)


class ErrorResult(AgentAccessModel):
    """Standard machine-readable error response."""

    code: str
    message: str
    remediation: str
    blocking: bool
    related_path: str | None = None
    related_artifact: str | None = None
    details: dict[str, str] = Field(default_factory=dict)

    @field_validator("code", "message", "remediation")
    @classmethod
    def _non_empty_text(cls, value: str) -> str:
        return _validate_non_empty(value)

    @field_validator("related_path")
    @classmethod
    def _related_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_repo_local_path(value)

    @field_validator("related_artifact")
    @classmethod
    def _related_artifact(cls, value: str | None) -> str | None:
        return _validate_optional_id(value)

    @field_validator("details")
    @classmethod
    def _normalize_details(cls, values: dict[str, str]) -> dict[str, str]:
        return {
            _validate_non_empty(key): _validate_non_empty(value)
            for key, value in values.items()
        }


AGENT_ACCESS_STABLE_ERROR_CODES: tuple[str, ...] = (
    "accepted_write_forbidden",
    "artifact_file_validation_failed",
    "artifact_id_exists",
    "artifact_model_validation_failed",
    "artifact_path_exists",
    "bundle_complete_forbidden",
    "bundle_submit_failed",
    "context_build_failed",
    "context_show_failed",
    "draft_write_failed",
    "gate_issue",
    "human_review_forbidden",
    "invalid_artifact_id",
    "invalid_artifact_target_path",
    "invalid_input_json",
    "invalid_staging_path",
    "invalid_timestamp",
    "memory_cards_failed",
    "memory_search_failed",
    "missing_required_domain",
    "no_writable_kb_root",
    "orchestrator_plan_failed",
    "private_context_requires_consent",
    "private_context_requires_policy",
    "provider_context_preview_failed",
    "provider_context_scope_violation",
    "provider_unsupported",
    "readonly_kb_root",
    "repository_load_failed",
    "review_request_failed",
    "source_note_write_failed",
    "timestamp_missing_timezone",
    "unknown_context_policy_mode",
    "validation_failed",
    "validation_unexpected_error",
    "workspace_config_failed",
)


class WorkspaceInfoResult(AgentAccessModel):
    """Stable workspace information response for agent callers."""

    workspace_name: str
    repo_root: str
    mode: Literal["configured", "legacy"]
    kb_roots: list[AgentKbRoot]
    policy: KbRootPolicy

    @field_validator("workspace_name", "repo_root")
    @classmethod
    def _non_empty_text(cls, value: str) -> str:
        return _validate_non_empty(value)


class ValidateResult(AgentAccessModel):
    """Stable validation response."""

    ok: bool
    checked_count: int
    failures: list[ErrorResult] = Field(default_factory=list)

    @field_validator("checked_count")
    @classmethod
    def _non_negative_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("checked_count must be non-negative")
        return value


class GateRunResult(AgentAccessModel):
    """Stable gatekeeper run response."""

    verdict: Literal["pass", "fail"]
    report_json_path: str
    report_markdown_path: str
    blocking_issues: list[ErrorResult] = Field(default_factory=list)
    nonblocking_issues: list[ErrorResult] = Field(default_factory=list)

    @field_validator("report_json_path", "report_markdown_path")
    @classmethod
    def _repo_local_paths(cls, value: str) -> str:
        return _validate_repo_local_path(value)


class MemorySearchRequest(AgentAccessModel):
    """Bounded memory-search request."""

    query: str
    issue_id: str | None = None
    allowed_scopes: list[MemoryRootScope] = Field(
        default_factory=lambda: [MemoryRootScope.PUBLIC]
    )
    allowed_statuses: list[ArtifactCardStatus] = Field(
        default_factory=lambda: [ArtifactCardStatus.ACCEPTED]
    )
    public_only: bool = True
    include_refuted: bool = False
    include_obsolete: bool = False
    max_cards: int = 20

    @field_validator("query")
    @classmethod
    def _query(cls, value: str) -> str:
        return _validate_non_empty(value)

    @field_validator("issue_id")
    @classmethod
    def _issue_id(cls, value: str | None) -> str | None:
        return _validate_optional_id(value)

    @field_validator("max_cards")
    @classmethod
    def _max_cards(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("max_cards must be positive")
        return value


class AgentArtifactCard(AgentAccessModel):
    """Public DTO for compact artifact search/context results."""

    artifact_id: str
    title: str
    status: ArtifactCardStatus
    root_scope: MemoryRootScope
    path: str
    risk_flags: list[str] = Field(default_factory=list)

    @field_validator("artifact_id")
    @classmethod
    def _artifact_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        return _validate_non_empty(value)

    @field_validator("path")
    @classmethod
    def _path(cls, value: str) -> str:
        return _validate_repo_local_path(value)


class MemorySearchResult(AgentAccessModel):
    """Stable memory-search response."""

    request: MemorySearchRequest
    cards: list[AgentArtifactCard] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("warnings")
    @classmethod
    def _warnings(cls, values: list[str]) -> list[str]:
        return _normalize_text_list(values)


class ContextBuildRequest(AgentAccessModel):
    """Request to build a bounded context pack."""

    issue_id: str
    role: RetrievalRole = RetrievalRole.ORCHESTRATOR
    max_cards: int = 20
    max_full_artifacts: int = 0
    policy_mode: ContextPolicyMode = ContextPolicyMode.PUBLIC
    public_only: bool = True
    allow_private_context: bool = False

    @field_validator("issue_id")
    @classmethod
    def _issue_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("max_cards")
    @classmethod
    def _max_cards(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("max_cards must be positive")
        return value

    @field_validator("max_full_artifacts")
    @classmethod
    def _max_full_artifacts(cls, value: int) -> int:
        if value < 0:
            raise ValueError("max_full_artifacts must be non-negative")
        return value


class ContextBuildResult(AgentAccessModel):
    """Result of building a bounded context pack."""

    issue_id: str
    task_dir: str
    files: list[str]
    public_only: bool
    private_context_included: bool = False

    @field_validator("issue_id")
    @classmethod
    def _issue_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("task_dir")
    @classmethod
    def _task_dir(cls, value: str) -> str:
        return _validate_repo_local_path(value)

    @field_validator("files")
    @classmethod
    def _files(cls, values: list[str]) -> list[str]:
        return [_validate_repo_local_path(value) for value in values]


class CreateTaskRequest(AgentAccessModel):
    """Request to create a local task record."""

    issue_id: str
    worker_type: WorkerType

    @field_validator("issue_id")
    @classmethod
    def _issue_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())


class CreateTaskResult(AgentAccessModel):
    """Result of creating a local task record."""

    task_id: str
    issue_id: str
    worker_type: WorkerType
    status: str
    task_path: str

    @field_validator("task_id", "issue_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("status")
    @classmethod
    def _status(cls, value: str) -> str:
        return _validate_non_empty(value)

    @field_validator("task_path")
    @classmethod
    def _task_path(cls, value: str) -> str:
        return _validate_repo_local_path(value)


class WorkerBundleSubmitRequest(AgentAccessModel):
    """Request to validate or submit a worker bundle for review."""

    task_id: str
    bundle_path: str
    complete_task: bool = False

    @field_validator("task_id")
    @classmethod
    def _task_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("bundle_path")
    @classmethod
    def _bundle_path(cls, value: str) -> str:
        return _validate_repo_local_path(value)


class WorkerBundleSubmitResult(AgentAccessModel):
    """Result of worker bundle validation/submission."""

    task_id: str
    bundle_id: str
    accepted_for_review: bool
    output_paths: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("task_id", "bundle_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("output_paths")
    @classmethod
    def _paths(cls, values: list[str]) -> list[str]:
        return [_validate_repo_local_path(value) for value in values]

    @field_validator("warnings")
    @classmethod
    def _warnings(cls, values: list[str]) -> list[str]:
        return _normalize_text_list(values)


class DraftArtifactWriteRequest(AgentAccessModel):
    """Request to write a draft/pre-accepted artifact proposal."""

    artifact_id: str
    artifact_type: ArtifactType
    title: str
    domain: list[str]
    status: ArtifactStatus = ArtifactStatus.DRAFT
    statement: str
    authors: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)
    target_surface: Literal["draft"] = "draft"

    @field_validator("artifact_id")
    @classmethod
    def _artifact_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("title", "statement")
    @classmethod
    def _text(cls, value: str) -> str:
        return _validate_non_empty(value)

    @field_validator("domain", "authors", "tags")
    @classmethod
    def _text_list(cls, values: list[str]) -> list[str]:
        return _normalize_text_list(values)

    @field_validator("depends_on", "supersedes")
    @classmethod
    def _ids_list(cls, values: list[str]) -> list[str]:
        return [validate_artifact_id(value.strip()) for value in values]

    @model_validator(mode="after")
    def _refuse_accepted_status(self) -> DraftArtifactWriteRequest:
        if self.status is ArtifactStatus.ACCEPTED:
            raise ValueError("draft artifact write requests cannot target accepted")
        return self


class DraftArtifactWriteResult(AgentAccessModel):
    """Result of writing a draft/pre-accepted artifact proposal."""

    artifact_id: str
    status: ArtifactStatus
    path: str
    accepted_write_performed: Literal[False] = False

    @field_validator("artifact_id")
    @classmethod
    def _artifact_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("path")
    @classmethod
    def _path(cls, value: str) -> str:
        return _validate_repo_local_path(value)

    @model_validator(mode="after")
    def _refuse_accepted_status(self) -> DraftArtifactWriteResult:
        if self.status is ArtifactStatus.ACCEPTED:
            raise ValueError("draft artifact write results cannot be accepted")
        return self


class ProviderConsent(AgentAccessModel):
    """Consent and scope metadata for provider-send flows."""

    consent_required: bool
    consent_granted: bool
    allow_private_context: bool
    policy_scope: ContextPolicyMode
    operator_note: str = ""

    @field_validator("operator_note")
    @classmethod
    def _note(cls, value: str) -> str:
        return value.strip()


class ProviderContextPreviewItem(AgentAccessModel):
    """One artifact card included in a provider-send preview."""

    artifact_id: str
    root_scope: MemoryRootScope
    status: ArtifactCardStatus
    estimated_tokens: int
    risk_flags: list[str] = Field(default_factory=list)

    @field_validator("artifact_id")
    @classmethod
    def _artifact_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("estimated_tokens")
    @classmethod
    def _estimated_tokens(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("estimated_tokens must be positive")
        return value

    @field_validator("risk_flags")
    @classmethod
    def _risk_flags(cls, values: list[str]) -> list[str]:
        return _normalize_text_list(values)


class ProviderContextPreview(AgentAccessModel):
    """Safe provider-send context preview without full text or secrets."""

    issue_id: str
    policy_mode: ContextPolicyMode
    public_only: bool
    private_context_requested: bool
    private_context_included: bool
    artifact_ids: list[str]
    root_scopes: list[MemoryRootScope]
    estimated_tokens: int
    risk_flags: list[str] = Field(default_factory=list)
    items: list[ProviderContextPreviewItem] = Field(default_factory=list)

    @field_validator("issue_id")
    @classmethod
    def _issue_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("artifact_ids")
    @classmethod
    def _artifact_ids(cls, values: list[str]) -> list[str]:
        return [validate_artifact_id(value.strip()) for value in values]

    @field_validator("estimated_tokens")
    @classmethod
    def _estimated_tokens(cls, value: int) -> int:
        if value < 0:
            raise ValueError("estimated_tokens must be non-negative")
        return value

    @field_validator("risk_flags")
    @classmethod
    def _risk_flags(cls, values: list[str]) -> list[str]:
        return _normalize_text_list(values)


class ModelCallRequest(AgentAccessModel):
    """Provider-neutral model call request for future hosted workers."""

    provider: ProviderName = ProviderName.FAKE
    model: str
    worker_role: WorkerType
    prompt: str
    context_artifact_ids: list[str] = Field(default_factory=list)
    root_scopes: list[MemoryRootScope] = Field(default_factory=list)
    consent: ProviderConsent
    temperature: float | None = None
    top_p: float | None = None
    reasoning_effort: ReasoningEffort | None = None
    max_output_tokens: int | None = None
    tool_policy: ToolPolicy = ToolPolicy.NONE
    network_policy: NetworkPolicy = NetworkPolicy.DISABLED

    @field_validator("model", "prompt")
    @classmethod
    def _text(cls, value: str) -> str:
        return _validate_non_empty(value)

    @field_validator("context_artifact_ids")
    @classmethod
    def _artifact_ids(cls, values: list[str]) -> list[str]:
        return [validate_artifact_id(value.strip()) for value in values]

    @field_validator("temperature")
    @classmethod
    def _temperature(cls, value: float | None) -> float | None:
        if value is not None and not 0 <= value <= 2:
            raise ValueError("temperature must be between 0 and 2")
        return value

    @field_validator("top_p")
    @classmethod
    def _top_p(cls, value: float | None) -> float | None:
        if value is not None and not 0 < value <= 1:
            raise ValueError("top_p must be greater than 0 and at most 1")
        return value

    @field_validator("max_output_tokens")
    @classmethod
    def _max_output_tokens(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("max_output_tokens must be positive")
        return value


class ProviderRunRecord(AgentAccessModel):
    """Audit record for one provider call attempt."""

    run_id: str
    provider: ProviderName
    model: str
    policy_scope: ContextPolicyMode
    consent: ProviderConsent
    private_context_sent: bool
    status: ProviderRunStatus
    started_at: datetime | None = None
    ended_at: datetime | None = None
    request_fingerprint: str | None = None
    log_path: str | None = None

    @field_validator("run_id")
    @classmethod
    def _run_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("model")
    @classmethod
    def _model(cls, value: str) -> str:
        return _validate_non_empty(value)

    @field_validator("log_path")
    @classmethod
    def _log_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_repo_local_path(value)


class ModelCallResult(AgentAccessModel):
    """Provider-neutral model call response for future hosted workers."""

    request_id: str
    provider: ProviderName
    model: str
    status: ProviderRunStatus
    content: str
    finish_reason: FinishReason = FinishReason.STOP
    provider_run: ProviderRunRecord
    warnings: list[str] = Field(default_factory=list)

    @field_validator("request_id")
    @classmethod
    def _request_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("model", "content")
    @classmethod
    def _text(cls, value: str) -> str:
        return _validate_non_empty(value)

    @field_validator("warnings")
    @classmethod
    def _warnings(cls, values: list[str]) -> list[str]:
        return _normalize_text_list(values)


AGENT_ACCESS_SCHEMA_MODELS: dict[str, type[AgentAccessModel]] = {
    "context_build_request": ContextBuildRequest,
    "context_build_result": ContextBuildResult,
    "create_task_request": CreateTaskRequest,
    "create_task_result": CreateTaskResult,
    "draft_artifact_write_request": DraftArtifactWriteRequest,
    "draft_artifact_write_result": DraftArtifactWriteResult,
    "error_result": ErrorResult,
    "gate_run_result": GateRunResult,
    "memory_search_request": MemorySearchRequest,
    "memory_search_result": MemorySearchResult,
    "model_call_request": ModelCallRequest,
    "model_call_result": ModelCallResult,
    "provider_run_record": ProviderRunRecord,
    "validate_result": ValidateResult,
    "worker_bundle_submit_request": WorkerBundleSubmitRequest,
    "worker_bundle_submit_result": WorkerBundleSubmitResult,
    "workspace_info_result": WorkspaceInfoResult,
}


def _validate_optional_id(value: str | None) -> str | None:
    if value is None:
        return None
    return validate_artifact_id(value.strip())


def _validate_non_empty(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("text field must be non-empty")
    return normalized


def _normalize_text_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = _validate_non_empty(value)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _validate_repo_local_path(value: str) -> str:
    normalized = normalize_repo_path(value)
    is_absolute = PureWindowsPath(value).is_absolute()
    parts = PurePosixPath(normalized).parts
    if (
        not normalized
        or is_absolute
        or normalized == ".."
        or normalized.startswith("../")
        or ".." in parts
    ):
        raise ValueError("path must be repository-local")
    return normalized


__all__ = [
    "AGENT_ACCESS_STABLE_ERROR_CODES",
    "AGENT_ACCESS_SCHEMA_MODELS",
    "AgentAccessModel",
    "AgentAccessStatus",
    "AgentArtifactCard",
    "AgentKbRoot",
    "ContextBuildRequest",
    "ContextBuildResult",
    "ContextPolicyMode",
    "DraftArtifactWriteRequest",
    "DraftArtifactWriteResult",
    "ErrorResult",
    "GateRunResult",
    "KbRootPolicy",
    "MemoryRootScope",
    "MemorySearchRequest",
    "MemorySearchResult",
    "ModelCallRequest",
    "ModelCallResult",
    "ProviderConsent",
    "ProviderContextPreview",
    "ProviderContextPreviewItem",
    "ProviderRunRecord",
    "ProviderRunStatus",
    "ValidateResult",
    "WorkspaceInfoResult",
    "WorkerBundleSubmitRequest",
    "WorkerBundleSubmitResult",
]
