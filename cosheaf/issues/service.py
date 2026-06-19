"""Repository-local file-backed issue operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from cosheaf.core.ids import validate_artifact_id
from cosheaf.storage.loader import IssueRecord, LoadedRecord, load_artifacts
from cosheaf.storage.repo import RepoContext
from cosheaf.storage.writer import write_yaml_deterministic

IssueStatus = Literal["open", "blocked", "closed"]

ISSUE_AUTHORITY_NOTICE = (
    "Local issue records are repository workflow memory only; they do not "
    "create GitHub issues, accept or refute artifacts, grant human review, "
    "run verifiers, pass gates, or promote knowledge."
)


class LocalIssueError(ValueError):
    """Raised when local issue operations cannot be completed."""


@dataclass(frozen=True)
class IssueResult:
    """Machine-readable local issue operation result."""

    issue: IssueRecord
    relative_path: Path
    writes_performed: bool
    github_issue_created: bool = False
    artifact_status_changed: bool = False
    authority_notice: str = ISSUE_AUTHORITY_NOTICE

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "issue": self.issue.model_dump(mode="json"),
            "path": self.relative_path.as_posix(),
            "writes_performed": self.writes_performed,
            "github_issue_created": self.github_issue_created,
            "artifact_status_changed": self.artifact_status_changed,
            "authority_notice": self.authority_notice,
        }


@dataclass(frozen=True)
class IssueListResult:
    """Machine-readable local issue list result."""

    issues: tuple[IssueRecord, ...]
    paths: tuple[Path, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "issues": [
                {
                    **issue.model_dump(mode="json"),
                    "path": path.as_posix(),
                }
                for issue, path in zip(self.issues, self.paths, strict=True)
            ],
            "count": len(self.issues),
            "authority_notice": ISSUE_AUTHORITY_NOTICE,
        }


class LocalIssueService:
    """Read and write repository-local issue YAML records."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context

    def create(
        self,
        *,
        issue_id: str,
        title: str,
        summary: str | None = None,
        authors: tuple[str, ...] = (),
        labels: tuple[str, ...] = (),
        related_artifacts: tuple[str, ...] = (),
        related_sources: tuple[str, ...] = (),
        scope: Literal["private", "public"] = "private",
        dry_run: bool = False,
    ) -> IssueResult:
        """Create an open repository-local issue YAML record."""
        normalized_id = validate_artifact_id(issue_id)
        self._ensure_unique_id(normalized_id)
        now = _now_utc()
        issue = IssueRecord(
            id=normalized_id,
            type="issue",
            title=title,
            status="open",
            summary=summary if summary is not None else title,
            created_at=now,
            updated_at=now,
            authors=list(authors),
            labels=list(labels),
            related_artifacts=list(related_artifacts),
            related_sources=list(related_sources),
            scope=scope,
        )
        relative_path = _issue_path(issue.status, issue.id)
        absolute_path = self.context.resolve(relative_path)
        if absolute_path.exists():
            raise LocalIssueError(f"issue path already exists: {relative_path}")
        if not dry_run:
            write_yaml_deterministic(absolute_path, _issue_yaml_data(issue))
        return IssueResult(
            issue=issue,
            relative_path=relative_path,
            writes_performed=not dry_run,
        )

    def show(self, issue_id: str) -> IssueResult:
        """Return one issue record without writing files."""
        loaded = self._find_issue(issue_id)
        issue = cast(IssueRecord, loaded.record)
        return IssueResult(
            issue=issue,
            relative_path=loaded.source_path,
            writes_performed=False,
        )

    def list(self) -> IssueListResult:
        """Return all issue records in deterministic order."""
        loaded_issues = sorted(
            self._loaded_issues(),
            key=lambda loaded: (loaded.record.id, loaded.source_path.as_posix()),
        )
        return IssueListResult(
            issues=tuple(cast(IssueRecord, loaded.record) for loaded in loaded_issues),
            paths=tuple(loaded.source_path for loaded in loaded_issues),
        )

    def close(self, issue_id: str, *, reason: str) -> IssueResult:
        """Close an open or blocked local issue without changing artifacts."""
        loaded = self._find_issue(issue_id)
        issue = cast(IssueRecord, loaded.record)
        if issue.status == "closed":
            raise LocalIssueError(f"issue already closed: {issue.id}")
        if not _is_mutable_issue_path(loaded.source_path):
            raise LocalIssueError(
                "local issue close only writes repository YAML under "
                "issues/open or issues/blocked"
            )

        updated = IssueRecord.model_validate(
            {
                **issue.model_dump(mode="json"),
                "status": "closed",
                "updated_at": _now_utc(),
                "close_reason": reason,
            }
        )
        relative_path = _issue_path("closed", updated.id)
        source = self.context.resolve(loaded.source_path)
        target = self.context.resolve(relative_path)
        if target.exists() and target.resolve() != source.resolve():
            raise LocalIssueError(f"issue path already exists: {relative_path}")
        write_yaml_deterministic(target, _issue_yaml_data(updated))
        if source.resolve() != target.resolve():
            source.unlink()
        return IssueResult(
            issue=updated,
            relative_path=relative_path,
            writes_performed=True,
        )

    def _loaded_issues(self) -> tuple[LoadedRecord, ...]:
        loaded: list[LoadedRecord] = []
        for record in load_artifacts(self.context):
            if isinstance(record.record, IssueRecord):
                loaded.append(record)
        return tuple(loaded)

    def _find_issue(self, issue_id: str) -> LoadedRecord:
        normalized_id = validate_artifact_id(issue_id)
        matches = [
            record for record in self._loaded_issues() if record.id == normalized_id
        ]
        if not matches:
            raise LocalIssueError(f"issue not found: {normalized_id}")
        return sorted(matches, key=lambda loaded: loaded.source_path.as_posix())[0]

    def _ensure_unique_id(self, issue_id: str) -> None:
        for record in load_artifacts(self.context):
            if record.id == issue_id:
                raise LocalIssueError(f"issue already exists: {issue_id}")


def _issue_path(status: IssueStatus, issue_id: str) -> Path:
    return Path("issues") / status / f"{issue_id}.yaml"


def _is_mutable_issue_path(path: Path) -> bool:
    parts = path.parts
    return len(parts) >= 3 and parts[0] == "issues" and parts[1] in {
        "open",
        "blocked",
    }


def _now_utc() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _issue_yaml_data(issue: IssueRecord) -> dict[str, object]:
    data = issue.model_dump(mode="json", exclude={"severity"})
    if data.get("parent_issue") is None:
        data.pop("parent_issue", None)
    if data.get("close_reason") is None:
        data.pop("close_reason", None)
    if data.get("external_links") == []:
        data.pop("external_links", None)
    return data
