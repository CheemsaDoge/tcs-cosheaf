"""Worker output bundle contract for the agent harness."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Literal

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from yaml import YAMLError

from cosheaf.agent.task import AgentTask, WorkerType
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path
from cosheaf.gates.schema_gate import load_schema_valid_record
from cosheaf.storage.repo import RepoContext


class OutputBundleError(ValueError):
    """Raised when a worker output bundle does not satisfy the contract."""


class WorkerOutputKind(StrEnum):
    """Kinds of local outputs a worker may reference."""

    ARTIFACT = "artifact"
    REVIEW = "review"
    EVIDENCE = "evidence"
    REPORT = "report"


class WorkerOutput(BaseModel):
    """A repository-local worker output reference."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    kind: WorkerOutputKind
    path: str
    summary: str

    @field_validator("path")
    @classmethod
    def _validate_repo_local_path(cls, value: str) -> str:
        normalized = normalize_repo_path(value)
        if (
            not normalized
            or Path(value).is_absolute()
            or PureWindowsPath(value).is_absolute()
            or normalized == ".."
            or normalized.startswith("../")
        ):
            raise ValueError("path must be repository-local")
        return normalized


class WorkerOutputBundle(BaseModel):
    """Machine-readable manifest for a completed worker task."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    schema_version: Literal[1] = 1
    task_id: str
    worker_type: WorkerType
    outputs: list[WorkerOutput] = Field(min_length=1)
    notes: str = ""

    @field_validator("task_id")
    @classmethod
    def _validate_task_id(cls, value: str) -> str:
        return validate_artifact_id(value)


SCHEMA_GATE_OUTPUT_KINDS = frozenset(
    {
        WorkerOutputKind.ARTIFACT,
        WorkerOutputKind.REVIEW,
    }
)


def validate_output_bundle(
    context: RepoContext,
    bundle_path: str | Path,
    *,
    task: AgentTask | None = None,
) -> WorkerOutputBundle:
    """Validate a worker output bundle without merging accepted knowledge."""
    manifest_path = _resolve_manifest_path(context, bundle_path)
    raw = _read_yaml_mapping(manifest_path)

    try:
        bundle = WorkerOutputBundle.model_validate(raw)
    except ValidationError as exc:
        message = _format_errors(exc)
        raise OutputBundleError(f"invalid output bundle: {message}") from exc

    if task is not None:
        _validate_bundle_matches_task(bundle, task)

    for output in bundle.outputs:
        _validate_output_reference(context, output)

    return bundle


def _resolve_manifest_path(context: RepoContext, bundle_path: str | Path) -> Path:
    path = Path(bundle_path)
    resolved = path.resolve() if path.is_absolute() else context.resolve(path)
    if resolved.is_dir():
        resolved = resolved / "bundle.yaml"

    try:
        resolved.relative_to(context.repo_root)
    except ValueError:
        raise OutputBundleError("output bundle must be inside the repository") from None

    if not resolved.is_file():
        raise OutputBundleError(f"output bundle not found: {resolved}")
    return resolved


def _read_yaml_mapping(path: Path) -> dict[str, object]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except YAMLError as exc:
        raise OutputBundleError(f"invalid output bundle YAML: {exc}") from exc
    except OSError as exc:
        raise OutputBundleError(f"cannot read output bundle: {exc}") from exc

    if not isinstance(raw, dict):
        raise OutputBundleError("output bundle must be a YAML mapping")
    return raw


def _validate_bundle_matches_task(
    bundle: WorkerOutputBundle,
    task: AgentTask,
) -> None:
    if bundle.task_id != task.task_id:
        raise OutputBundleError(
            f"bundle task_id {bundle.task_id!r} does not match {task.task_id!r}"
        )
    if bundle.worker_type is not task.worker_type:
        raise OutputBundleError(
            "bundle worker_type "
            f"{bundle.worker_type.value!r} does not match {task.worker_type.value!r}"
        )


def _validate_output_reference(context: RepoContext, output: WorkerOutput) -> None:
    relative_path = Path(output.path)
    resolved = context.resolve(relative_path)
    try:
        resolved.relative_to(context.repo_root)
    except ValueError:
        raise OutputBundleError(
            f"output path must be repository-local: {output.path}"
        ) from None

    if not resolved.exists():
        raise OutputBundleError(f"output path does not exist: {output.path}")

    if output.path.startswith("kb/accepted/"):
        raise OutputBundleError(
            "worker output must not target accepted knowledge: "
            f"{output.path}"
        )

    if output.kind in SCHEMA_GATE_OUTPUT_KINDS:
        gate_result = load_schema_valid_record(context, relative_path)
        if gate_result.failures:
            messages = "; ".join(failure.message for failure in gate_result.failures)
            raise OutputBundleError(
                f"output did not pass schema gate: {output.path}: {messages}"
            )


def _format_errors(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )
