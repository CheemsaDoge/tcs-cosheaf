"""Context pack generation for bounded Codex task handoffs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import shorten

from cosheaf.core.artifact import BaseArtifact
from cosheaf.core.status import (
    ArtifactStatus,
    is_accepted_status,
    is_preaccepted_status,
)
from cosheaf.storage.loader import IssueRecord, LoadedRecord, load_artifacts
from cosheaf.storage.repo import RepoContext

PACK_FILENAMES = (
    "CONTEXT.md",
    "ACCEPTANCE.md",
    "RELEVANT_ARTIFACTS.md",
    "KNOWN_FAILURES.md",
    "COMMANDS.md",
)

DEFAULT_COMMANDS = (
    "make lint",
    "make typecheck",
    "make test",
    "make validate",
    "make gate",
)

KNOWN_FAILURE_STATUSES = frozenset(
    {
        ArtifactStatus.REFUTED,
        ArtifactStatus.OBSOLETE,
        ArtifactStatus.SUPERSEDED,
    }
)


class ContextPackError(ValueError):
    """Raised when a context pack cannot be generated from repository data."""


@dataclass(frozen=True)
class ContextPackResult:
    """Written context pack files for an issue."""

    issue_id: str
    task_dir: Path
    files: tuple[Path, ...]


def build_context_pack(context: RepoContext, issue_id: str) -> ContextPackResult:
    """Build a deterministic bounded context pack for an issue."""
    records = tuple(load_artifacts(context))
    issue = _find_issue(records, issue_id)
    artifacts = _select_relevant_artifacts(records, issue)
    task_dir = context.resolve(Path("context") / "TASKS" / issue_id)
    task_dir.mkdir(parents=True, exist_ok=True)

    contents = {
        "CONTEXT.md": _render_context(context, issue, artifacts),
        "ACCEPTANCE.md": _render_acceptance(issue),
        "RELEVANT_ARTIFACTS.md": _render_relevant_artifacts(artifacts),
        "KNOWN_FAILURES.md": _render_known_failures(artifacts),
        "COMMANDS.md": _render_commands(),
    }
    files: list[Path] = []
    for filename in PACK_FILENAMES:
        path = task_dir / filename
        path.write_text(contents[filename], encoding="utf-8")
        files.append(path)

    return ContextPackResult(
        issue_id=issue.id,
        task_dir=task_dir,
        files=tuple(files),
    )


def show_context_pack(context: RepoContext, issue_id: str) -> str:
    """Build a context pack if needed and return its main context document."""
    result = build_context_pack(context, issue_id)
    return (result.task_dir / "CONTEXT.md").read_text(encoding="utf-8")


def _find_issue(records: tuple[LoadedRecord, ...], issue_id: str) -> IssueRecord:
    issues = [
        record.record
        for record in records
        if isinstance(record.record, IssueRecord) and record.record.id == issue_id
    ]
    if not issues:
        raise ContextPackError(f"issue not found: {issue_id}")
    return sorted(issues, key=lambda issue: issue.id)[0]


def _select_relevant_artifacts(
    records: tuple[LoadedRecord, ...],
    issue: IssueRecord,
) -> tuple[LoadedRecord, ...]:
    artifact_records = [
        record for record in records if isinstance(record.record, BaseArtifact)
    ]
    artifact_by_id = {record.id: record for record in artifact_records}
    relevant_ids = set(issue.related_artifacts)

    for artifact_id in sorted(issue.related_artifacts):
        record = artifact_by_id.get(artifact_id)
        if isinstance(record, LoadedRecord) and isinstance(record.record, BaseArtifact):
            relevant_ids.update(record.record.depends_on)

    selected = [
        record
        for record in artifact_records
        if record.record.id in relevant_ids and isinstance(record.record, BaseArtifact)
    ]
    return tuple(sorted(selected, key=_artifact_sort_key))


def _artifact_sort_key(record: LoadedRecord) -> tuple[int, str, str]:
    artifact = _as_artifact(record)
    return (
        _status_priority(artifact.status),
        artifact.id,
        record.source_path.as_posix(),
    )


def _status_priority(status: ArtifactStatus) -> int:
    if is_accepted_status(status):
        return 0
    if is_preaccepted_status(status):
        return 1
    if status in KNOWN_FAILURE_STATUSES:
        return 2
    return 3


def _render_context(
    context: RepoContext,
    issue: IssueRecord,
    artifacts: tuple[LoadedRecord, ...],
) -> str:
    accepted = [
        record
        for record in artifacts
        if is_accepted_status(_as_artifact(record).status)
    ]
    drafts = [
        record
        for record in artifacts
        if is_preaccepted_status(_as_artifact(record).status)
    ]

    lines = [
        f"# Context Pack: {issue.id}",
        "",
        "## Issue Summary",
        "",
        f"- Title: {issue.title}",
        f"- Status: {issue.status}",
        f"- Severity: {issue.severity}",
        f"- Source: {_issue_source_path(context, issue.id)}",
        f"- Summary: {_one_line(issue.description)}",
        "",
        "## Relevant Accepted Artifacts",
        "",
    ]
    lines.extend(_artifact_lines(accepted, draft_label=False))
    lines.extend(["", "## Relevant Draft Artifacts", ""])
    lines.extend(_artifact_lines(drafts, draft_label=True))
    lines.extend(
        [
            "",
            "## Current Project State",
            "",
            _read_markdown_excerpt(context.resolve("context/PROJECT_STATE.md")),
            "",
            "## Relevant Interfaces",
            "",
            _read_markdown_excerpt(
                context.resolve("context/INTERFACE_REGISTRY.md"),
                keywords=("context", "RepoContext", "load_artifacts", "IssueRecord"),
            ),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _render_acceptance(issue: IssueRecord) -> str:
    task_criteria = _extract_acceptance_criteria(issue.description)
    lines = [
        f"# Acceptance: {issue.id}",
        "",
        "## Task-Specific Acceptance Criteria",
        "",
    ]
    if task_criteria:
        lines.extend(f"- {criterion}" for criterion in task_criteria)
    else:
        lines.append(
            "- No task-specific acceptance criteria recorded in the issue file."
        )

    lines.extend(
        [
            "",
            "## Default Engineering Acceptance Criteria",
            "",
            "- New behavior includes tests.",
            "- Public interface changes update `context/INTERFACE_REGISTRY.md`.",
            "- Workflow or behavior changes update relevant docs.",
            "- Verification failures are reported, not hidden.",
            "- Generated outputs are deterministic.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_relevant_artifacts(artifacts: tuple[LoadedRecord, ...]) -> str:
    lines = ["# Relevant Artifacts", ""]
    if artifacts:
        lines.extend(_artifact_reference_line(record) for record in artifacts)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def _render_known_failures(artifacts: tuple[LoadedRecord, ...]) -> str:
    known_failures = [
        record
        for record in artifacts
        if _as_artifact(record).status in KNOWN_FAILURE_STATUSES
    ]
    lines = ["# Known Failures", ""]
    if known_failures:
        lines.extend(_artifact_reference_line(record) for record in known_failures)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def _render_commands() -> str:
    lines = ["# Commands", "", "Run these commands before handoff:", ""]
    lines.extend(f"- `{command}`" for command in DEFAULT_COMMANDS)
    return "\n".join(lines) + "\n"


def _artifact_lines(
    records: list[LoadedRecord],
    *,
    draft_label: bool,
) -> list[str]:
    if not records:
        return ["- None"]
    lines = []
    for record in records:
        artifact = _as_artifact(record)
        prefix = "[DRAFT] " if draft_label else ""
        lines.append(
            f"- {prefix}{artifact.id} | {artifact.title} | "
            f"{record.source_path.as_posix()}"
        )
    return lines


def _artifact_reference_line(record: LoadedRecord) -> str:
    artifact = _as_artifact(record)
    prefix = "[DRAFT] " if is_preaccepted_status(artifact.status) else ""
    return (
        f"- {prefix}{artifact.id} | {artifact.title} | "
        f"{artifact.status.value} | {record.source_path.as_posix()}"
    )


def _as_artifact(record: LoadedRecord) -> BaseArtifact:
    if not isinstance(record.record, BaseArtifact):
        raise TypeError(f"loaded record is not an artifact: {record.id}")
    return record.record


def _extract_acceptance_criteria(description: str) -> list[str]:
    criteria: list[str] = []
    for raw_line in description.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- [ ] "):
            criteria.append(line.removeprefix("- [ ] ").strip())
        elif line.startswith("- "):
            criteria.append(line.removeprefix("- ").strip())
        elif line.startswith("* "):
            criteria.append(line.removeprefix("* ").strip())
        elif _starts_numbered_item(line):
            criteria.append(line.split(".", 1)[1].strip())
    return criteria


def _starts_numbered_item(line: str) -> bool:
    prefix, separator, rest = line.partition(".")
    return bool(separator and rest.strip() and prefix.isdecimal())


def _read_markdown_excerpt(
    path: Path,
    *,
    keywords: tuple[str, ...] = (),
    max_lines: int = 18,
    max_chars: int = 1600,
) -> str:
    if not path.exists():
        return f"{path.name} is not available."

    lines = path.read_text(encoding="utf-8").splitlines()
    selected = _select_excerpt_lines(lines, keywords=keywords, max_lines=max_lines)
    excerpt = "\n".join(selected).strip()
    if len(excerpt) > max_chars:
        return excerpt[: max_chars - 4].rstrip() + "\n..."
    return excerpt or "No excerpt available."


def _select_excerpt_lines(
    lines: list[str],
    *,
    keywords: tuple[str, ...],
    max_lines: int,
) -> list[str]:
    if not keywords:
        return lines[:max_lines]

    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    selected = [
        line
        for line in lines
        if any(keyword in line.lower() for keyword in lowered_keywords)
    ]
    if selected:
        return selected[:max_lines]
    return lines[:max_lines]


def _one_line(value: str) -> str:
    return shorten(" ".join(value.split()), width=240, placeholder="...")


def _issue_source_path(context: RepoContext, issue_id: str) -> str:
    for record in load_artifacts(context):
        if isinstance(record.record, IssueRecord) and record.record.id == issue_id:
            return record.source_path.as_posix()
    return "-"
