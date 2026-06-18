"""Dry-run forge planning service."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

from pydantic import ValidationError

from cosheaf.core.paths import normalize_repo_path
from cosheaf.forge.models import (
    ForgePreviewResult,
    GitHubIssuePlan,
    GitHubPrPlan,
    LocalGitPlan,
)
from cosheaf.storage.loader import IssueRecord, LoadError, load_yaml_file
from cosheaf.storage.repo import RepoContext


class ForgePreviewError(ValueError):
    """Raised when a dry-run forge preview cannot be constructed."""


class ForgeService:
    """Build dry-run plans for local git and GitHub workflow surfaces."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context

    def status(self) -> ForgePreviewResult:
        """Return forge status without reading tokens or mutating git state."""
        return ForgePreviewResult(
            kind="status",
            local_git_plan=LocalGitPlan(repo_root=self.context.repo_root.as_posix()),
        )

    def issue_preview(self, source_path: str | Path) -> ForgePreviewResult:
        """Preview GitHub issue creation from a repository-local issue file."""
        relative_path = _repo_local_input_path(source_path)
        absolute_path = self.context.resolve(relative_path)
        _ensure_inside_repo(self.context, absolute_path)
        if not absolute_path.exists():
            raise ForgePreviewError(
                f"issue source path does not exist: {relative_path}"
            )

        try:
            loaded = load_yaml_file(self.context, absolute_path)
        except (LoadError, ValidationError, ValueError) as exc:
            raise ForgePreviewError(str(exc)) from exc
        if not isinstance(loaded.record, IssueRecord):
            raise ForgePreviewError(
                f"forge issue preview requires an issue record: {relative_path}"
            )

        issue = loaded.record
        plan = GitHubIssuePlan(
            source_path=loaded.source_path.as_posix(),
            issue_id=issue.id,
            title=issue.title,
            body=issue.summary,
            labels=issue.labels,
        )
        return ForgePreviewResult(
            kind="github_issue",
            github_issue_plan=plan,
        )

    def pr_preview(self, *, base: str, head: str) -> ForgePreviewResult:
        """Preview GitHub pull request creation without touching git or GitHub."""
        normalized_base = _non_empty(base, "base")
        normalized_head = _non_empty(head, "head")
        return ForgePreviewResult(
            kind="github_pr",
            local_git_plan=LocalGitPlan(
                repo_root=self.context.repo_root.as_posix(),
                base=normalized_base,
                head=normalized_head,
            ),
            github_pr_plan=GitHubPrPlan(
                base=normalized_base,
                head=normalized_head,
                title=f"Merge {normalized_head} into {normalized_base}",
                body=(
                    "Dry-run PR preview only. No git push, GitHub PR creation, "
                    "network call, or repository mutation was performed."
                ),
            ),
        )


def _repo_local_input_path(path: str | Path) -> Path:
    value = str(path)
    normalized = normalize_repo_path(value)
    parts = PurePosixPath(normalized).parts
    if (
        not normalized
        or PureWindowsPath(value).is_absolute()
        or normalized == ".."
        or normalized.startswith("../")
        or ".." in parts
    ):
        raise ForgePreviewError("forge preview paths must be repository-local")
    return Path(normalized)


def _ensure_inside_repo(context: RepoContext, path: Path) -> None:
    try:
        path.resolve().relative_to(context.repo_root.resolve())
    except ValueError as exc:
        raise ForgePreviewError(
            "forge preview paths must stay inside repo root"
        ) from exc


def _non_empty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ForgePreviewError(f"{field_name} must be non-empty")
    return normalized


__all__ = ["ForgePreviewError", "ForgeService"]
