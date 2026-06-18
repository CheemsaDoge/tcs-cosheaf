"""Dry-run forge planning service."""

from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath, PureWindowsPath

from pydantic import ValidationError

from cosheaf.core.paths import normalize_repo_path
from cosheaf.forge.models import (
    ForgeActionResult,
    ForgePreviewResult,
    GitHubIssuePlan,
    GitHubPrPlan,
    LocalGitPlan,
)
from cosheaf.services import GateService, ValidationService
from cosheaf.storage.loader import IssueRecord, LoadError, load_yaml_file
from cosheaf.storage.repo import RepoContext


class ForgePreviewError(ValueError):
    """Raised when a dry-run forge preview cannot be constructed."""


class ForgeActionError(ValueError):
    """Raised when an explicit forge action cannot be completed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


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

    def create_branch(self, branch: str, *, confirm: bool) -> ForgeActionResult:
        """Create and switch to a local branch after explicit confirmation."""
        normalized_branch = _git_ref(branch, "branch")
        if not confirm:
            raise ForgeActionError(
                "forge_confirm_required",
                "forge branch create requires --confirm",
            )
        status = _git_status(self.context)
        if status:
            raise ForgeActionError(
                "forge_dirty_state",
                "dirty state blocks branch creation; commit, stash, or clean it first",
            )
        _run_git(self.context, "switch", "-c", normalized_branch)
        return ForgeActionResult(
            action="branch_create",
            action_performed=True,
            git_writes_performed=True,
            branch=normalized_branch,
        )

    def commit(self, *, message: str, confirm: bool) -> ForgeActionResult:
        """Run validation/gate and create one local git commit."""
        normalized_message = _action_non_empty(message, "message")
        if not confirm:
            raise ForgeActionError(
                "forge_confirm_required",
                "forge commit requires --confirm",
            )
        status = _git_status(self.context)
        staged = _staged_changes(status)
        ambiguous = _ambiguous_dirty_lines(status)
        if ambiguous:
            detail = "; ".join(ambiguous)
            raise ForgeActionError(
                "forge_dirty_state",
                f"dirty or untracked state blocks commit: {detail}",
            )
        if not staged:
            raise ForgeActionError(
                "forge_no_staged_changes",
                "forge commit requires staged changes",
            )

        validation = ValidationService(self.context).validate_repository()
        if not validation.ok:
            raise ForgeActionError(
                "forge_validation_failed",
                "repository validation failed; fix validation before committing",
            )
        gate = GateService(self.context).run()
        if gate.report.verdict != "pass":
            raise ForgeActionError(
                "forge_gate_failed",
                "repository gate failed; fix gate failures before committing",
            )

        _run_git(self.context, "commit", "-m", normalized_message)
        commit_hash = _run_git(self.context, "rev-parse", "HEAD").stdout.strip()
        return ForgeActionResult(
            action="commit",
            action_performed=True,
            git_writes_performed=True,
            commit_hash=commit_hash,
            validation_performed=True,
            gate_performed=True,
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


def _git_ref(value: str, field_name: str) -> str:
    normalized = _action_non_empty(value, field_name)
    if normalized.startswith("-") or any(char.isspace() for char in normalized):
        raise ForgeActionError("forge_invalid_git_ref", f"invalid git ref: {value}")
    return normalized


def _action_non_empty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ForgeActionError("forge_invalid_input", f"{field_name} must be non-empty")
    return normalized


def _run_git(context: RepoContext, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=context.repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise ForgeActionError("forge_git_failed", message)
    return result


def _git_status(context: RepoContext) -> tuple[str, ...]:
    output = _run_git(context, "status", "--porcelain=v1").stdout
    return tuple(line for line in output.splitlines() if line)


def _staged_changes(status: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(line for line in status if line[:2] != "??" and line[0] != " ")


def _ambiguous_dirty_lines(status: tuple[str, ...]) -> tuple[str, ...]:
    ambiguous: list[str] = []
    for line in status:
        if line[:2] == "??":
            ambiguous.append(f"untracked {line[3:]}")
        elif len(line) > 1 and line[1] != " ":
            ambiguous.append(f"unstaged {line[3:]}")
    return tuple(ambiguous)


__all__ = ["ForgeActionError", "ForgePreviewError", "ForgeService"]
