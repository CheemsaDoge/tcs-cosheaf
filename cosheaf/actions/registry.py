"""Deterministic local action registry and action execution models.

Local actions are whitelisted repository operations that the research loop can
execute without arbitrary shell, network, hosted providers, or accepted-knowledge
authority. Every action records input refs, output refs, status, timestamps,
error code, scanner status, and an authority notice.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

LOCAL_ACTION_AUTHORITY_NOTICE = (
    "Local action results are review context only; they are not proof, "
    "verifier pass, gate pass, human review, accepted status, accepted "
    "refutation, or promotion authority. Action success never means "
    "accepted knowledge."
)

class LocalActionStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    BLOCKED = "blocked"

class LocalActionInputRefKind(StrEnum):
    ISSUE_ID = "issue_id"
    ARTIFACT_ID = "artifact_id"
    KB_ROOT = "kb_root"
    HANDOFF_ID = "handoff_id"
    LOOP_ID = "loop_id"
    SESSION_ID = "session_id"
    STRATEGY_ID = "strategy_id"
    RUN_ID = "run_id"

class LocalActionOutputRefKind(StrEnum):
    RUNTIME_FILE = "runtime_file"
    REVIEW_FILE = "review_file"
    JSON_REPORT = "json_report"
    CONTEXT_PACK = "context_pack"
    HANDOFF_BUNDLE = "handoff_bundle"

class LocalActionSpec(BaseModel):
    """Serializable spec for one whitelisted local action."""
    model_config = ConfigDict(frozen=True)

    action_id: str = Field(..., description="Unique action identifier")
    description: str = Field(default="", description="Human-readable description")
    authority_notice: str = Field(default=LOCAL_ACTION_AUTHORITY_NOTICE)
    allowed_input_refs: list[LocalActionInputRefKind] = Field(default_factory=list)
    allowed_output_refs: list[LocalActionOutputRefKind] = Field(default_factory=list)
    writes_accepted: bool = Field(default=False)
    requires_network: bool = Field(default=False)
    calls_hosted_provider: bool = Field(default=False)
    executes_shell: bool = Field(default=False)
    max_timeout_seconds: int = Field(default=120)

class LocalActionError(BaseModel):
    """Structured error for a failed or blocked local action."""
    error_code: str = Field(default="UNKNOWN")
    message: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)
    scanner_blocker: bool = Field(default=False)

class LocalActionResult(BaseModel):
    """Result of executing one local action."""
    action_id: str
    status: LocalActionStatus
    input_refs: dict[str, str] = Field(default_factory=dict)
    output_refs: dict[str, str] = Field(default_factory=dict)
    started_at: datetime | None = Field(default=None)
    finished_at: datetime | None = Field(default=None)
    duration_seconds: float | None = Field(default=None)
    error: LocalActionError | None = Field(default=None)
    scanner_status: Literal["clean", "blocked", "not_applicable"] = Field(default="not_applicable")
    authority_notice: str = Field(default=LOCAL_ACTION_AUTHORITY_NOTICE)
    stdout_snippet: str = Field(default="")
    stderr_snippet: str = Field(default="")

class LocalActionRunRequest(BaseModel):
    """Request to run one local action."""
    action_id: str
    input_refs: dict[str, str] = Field(default_factory=dict)
    dry_run: bool = Field(default=False)

class LocalActionPolicy(BaseModel):
    """Policy constraints evaluated before action execution."""
    model_config = ConfigDict(frozen=True)

    allow_accepted_writes: bool = Field(default=False)
    allow_network: bool = Field(default=False)
    allow_hosted_provider: bool = Field(default=False)
    allow_shell: bool = Field(default=False)
    mode: Literal["public_only", "private_research"] = Field(default="private_research")
    max_timeout_seconds: int = Field(default=120)

# Action execution function signature
ActionFunc = Callable[[LocalActionRunRequest, LocalActionPolicy, Path], LocalActionResult]
"""Action function: (request, policy, repo_root) -> result."""

@dataclass(frozen=True)
class _RegistryEntry:
    spec: LocalActionSpec
    func: ActionFunc


class LocalActionRegistry:
    """Static, deterministic registry of whitelisted local actions."""

    def __init__(self) -> None:
        self._actions: dict[str, _RegistryEntry] = {}

    def register(self, spec: LocalActionSpec, func: ActionFunc) -> None:
        if spec.action_id in self._actions:
            raise ValueError(f"Duplicate action id: {spec.action_id}")
        self._actions[spec.action_id] = _RegistryEntry(spec=spec, func=func)

    def list_actions(self) -> list[LocalActionSpec]:
        return sorted(
            [entry.spec for entry in self._actions.values()],
            key=lambda s: s.action_id,
        )

    def get_spec(self, action_id: str) -> LocalActionSpec | None:
        entry = self._actions.get(action_id)
        return entry.spec if entry else None

    def run(
        self,
        request: LocalActionRunRequest,
        policy: LocalActionPolicy,
        repo_root: Path,
    ) -> LocalActionResult:
        entry = self._actions.get(request.action_id)
        if entry is None:
            return LocalActionResult(
                action_id=request.action_id,
                status=LocalActionStatus.ERROR,
                error=LocalActionError(
                    error_code="UNKNOWN_ACTION",
                    message=f"Action {request.action_id!r} is not in the registry",
                ),
            )

        spec = entry.spec
        if spec.writes_accepted and not policy.allow_accepted_writes:
            return LocalActionResult(
                action_id=request.action_id,
                status=LocalActionStatus.BLOCKED,
                error=LocalActionError(
                    error_code="ACCEPTED_WRITE_BLOCKED",
                    message=f"Action {request.action_id!r} requires accepted-write permission",
                ),
            )
        if spec.requires_network and not policy.allow_network:
            return LocalActionResult(
                action_id=request.action_id,
                status=LocalActionStatus.BLOCKED,
                error=LocalActionError(
                    error_code="NETWORK_BLOCKED",
                    message=f"Action {request.action_id!r} requires network access",
                ),
            )
        if spec.calls_hosted_provider and not policy.allow_hosted_provider:
            return LocalActionResult(
                action_id=request.action_id,
                status=LocalActionStatus.BLOCKED,
                error=LocalActionError(
                    error_code="PROVIDER_BLOCKED",
                    message=f"Action {request.action_id!r} requires hosted provider access",
                ),
            )
        if spec.executes_shell and not policy.allow_shell:
            return LocalActionResult(
                action_id=request.action_id,
                status=LocalActionStatus.BLOCKED,
                error=LocalActionError(
                    error_code="SHELL_BLOCKED",
                    message=f"Action {request.action_id!r} requires shell execution permission",
                ),
            )
        if request.dry_run:
            return LocalActionResult(
                action_id=request.action_id,
                status=LocalActionStatus.SUCCESS,
                input_refs=request.input_refs,
                output_refs={},
                scanner_status="not_applicable",
                authority_notice=(
                    "DRY RUN: No persistent output was written. " + spec.authority_notice
                ),
            )
        if not request.input_refs and spec.allowed_input_refs:
            return LocalActionResult(
                action_id=request.action_id,
                status=LocalActionStatus.ERROR,
                error=LocalActionError(
                    error_code="MISSING_INPUT_REFS",
                    message=f"Action {request.action_id!r} requires input refs",
                ),
            )

        started_at = datetime.now(UTC)
        try:
            result = entry.func(request, policy, repo_root)
            if result.started_at is None:
                result = result.model_copy(update={"started_at": started_at})
            if result.finished_at is None:
                result = result.model_copy(update={"finished_at": datetime.now(UTC)})
            if result.duration_seconds is None and result.started_at and result.finished_at:
                result = result.model_copy(
                    update={
                        "duration_seconds": (
                            result.finished_at - result.started_at
                        ).total_seconds()
                    }
                )
            return result
        except Exception as exc:
            finished_at = datetime.now(UTC)
            return LocalActionResult(
                action_id=request.action_id,
                status=LocalActionStatus.ERROR,
                started_at=started_at,
                finished_at=finished_at,
                duration_seconds=(finished_at - started_at).total_seconds(),
                error=LocalActionError(
                    error_code="EXECUTION_EXCEPTION",
                    message=str(exc),
                ),
            )
