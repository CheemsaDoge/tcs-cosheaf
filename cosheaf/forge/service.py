"""Dry-run forge planning service."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
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
from cosheaf.storage.writer import write_yaml_deterministic


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
        loaded_path, issue = _load_issue_file(self.context, source_path)
        plan = GitHubIssuePlan(
            source_path=loaded_path.as_posix(),
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

    def github_issue_create(
        self,
        source_path: str | Path,
        *,
        confirm: bool,
    ) -> ForgeActionResult:
        """Create a GitHub issue from local issue YAML through gh."""
        if not confirm:
            raise ForgeActionError(
                "forge_confirm_required",
                "forge issue create requires --confirm",
            )
        loaded_path, issue = _load_issue_file_for_action(self.context, source_path)
        args = [
            "issue",
            "create",
            "--title",
            issue.title,
            "--body",
            issue.summary,
        ]
        for label in issue.labels:
            args.extend(["--label", label])
        url = _run_gh(self.context, *args)
        updated_links = _unique_strings([*issue.external_links, url])
        updated = IssueRecord.model_validate(
            {
                **issue.model_dump(mode="json"),
                "updated_at": _now_utc(),
                "external_links": updated_links,
            }
        )
        write_yaml_deterministic(
            self.context.resolve(loaded_path),
            _issue_yaml_data(updated),
        )
        return ForgeActionResult(
            action="github_issue_create",
            action_performed=True,
            network_calls_performed=True,
            github_writes_performed=True,
            github_issue_created=True,
            github_issue_url=url,
            source_path=loaded_path.as_posix(),
            issue_id=issue.id,
        )

    def github_pr_create(
        self,
        *,
        base: str,
        head: str,
        draft: bool,
        confirm: bool,
    ) -> ForgeActionResult:
        """Create a GitHub PR through gh."""
        normalized_base = _git_ref(base, "base")
        normalized_head = _git_ref(head, "head")
        if not confirm:
            raise ForgeActionError(
                "forge_confirm_required",
                "forge pr create requires --confirm",
            )
        title = f"Merge {normalized_head} into {normalized_base}"
        body = f"Forge-created PR for {normalized_head} into {normalized_base}."
        args = [
            "pr",
            "create",
            "--base",
            normalized_base,
            "--head",
            normalized_head,
            "--title",
            title,
            "--body",
            body,
        ]
        if draft:
            args.append("--draft")
        url = _run_gh(self.context, *args)
        return ForgeActionResult(
            action="github_pr_create",
            action_performed=True,
            network_calls_performed=True,
            github_writes_performed=True,
            github_pr_created=True,
            github_pr_url=url,
            base=normalized_base,
            head=normalized_head,
        )

    def sync(self) -> ForgeActionResult:
        """Return a read-only sync placeholder for future link reconciliation."""
        return ForgeActionResult(action="sync")

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


def _load_issue_file(
    context: RepoContext,
    path: str | Path,
) -> tuple[Path, IssueRecord]:
    relative_path = _repo_local_input_path(path)
    absolute_path = context.resolve(relative_path)
    _ensure_inside_repo(context, absolute_path)
    if not absolute_path.exists():
        raise ForgePreviewError(f"issue source path does not exist: {relative_path}")

    try:
        loaded = load_yaml_file(context, absolute_path)
    except (LoadError, ValidationError, ValueError) as exc:
        raise ForgePreviewError(str(exc)) from exc
    if not isinstance(loaded.record, IssueRecord):
        raise ForgePreviewError(
            f"forge issue preview requires an issue record: {relative_path}"
        )
    return loaded.source_path, loaded.record


def _load_issue_file_for_action(
    context: RepoContext,
    path: str | Path,
) -> tuple[Path, IssueRecord]:
    try:
        return _load_issue_file(context, path)
    except ForgePreviewError as exc:
        raise ForgeActionError("forge_invalid_input", str(exc)) from exc


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


def _run_gh(context: RepoContext, *args: str) -> str:
    result = subprocess.run(
        ["gh", *args],
        cwd=context.repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "gh command failed"
        raise ForgeActionError("forge_github_failed", message)
    output = result.stdout.strip()
    if not output:
        raise ForgeActionError("forge_github_failed", "gh did not return a URL")
    return output.splitlines()[0].strip()


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


def _now_utc() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _issue_yaml_data(issue: IssueRecord) -> dict[str, object]:
    data = issue.model_dump(mode="json", exclude={"severity"})
    if data.get("parent_issue") is None:
        data.pop("parent_issue", None)
    if data.get("close_reason") is None:
        data.pop("close_reason", None)
    if data.get("external_links") == []:
        data.pop("external_links", None)
    return data


__all__ = ["ForgeActionError", "ForgePreviewError", "ForgeService"]
