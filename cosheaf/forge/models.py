"""Dry-run forge planning models."""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import Field, field_validator

from cosheaf.core.ids import validate_artifact_id
from cosheaf.services.models import AgentAccessModel

FORGE_AUTHORITY_WARNING = (
    "Forge previews are dry-run planning output only; they do not perform git "
    "commits, git pushes, GitHub issue creation, GitHub PR creation, token "
    "storage, network calls, human review, verifier passes, gate passes, "
    "artifact acceptance, refutation, or promotion."
)


class ForgeCredentialProvider(Protocol):
    """Protocol for future explicit forge credential lookup."""

    def provider_name(self) -> str:
        """Return a human-readable provider name."""
        ...

    def has_github_token(self) -> bool:
        """Return whether a GitHub token is available without exposing it."""
        ...


class LocalGitPlan(AgentAccessModel):
    """Dry-run local git plan."""

    repo_root: str
    base: str = ""
    head: str = ""
    planned_git_commands: list[str] = Field(default_factory=list)
    commit_performed: Literal[False] = False
    push_performed: Literal[False] = False

    @field_validator("repo_root")
    @classmethod
    def _repo_root(cls, value: str) -> str:
        return _non_empty(value)

    @field_validator("base", "head")
    @classmethod
    def _optional_ref(cls, value: str) -> str:
        return value.strip()

    @field_validator("planned_git_commands")
    @classmethod
    def _commands(cls, values: list[str]) -> list[str]:
        return [_non_empty(value) for value in values]


class GitHubIssuePlan(AgentAccessModel):
    """Dry-run GitHub issue creation plan."""

    source_path: str
    issue_id: str
    title: str
    body: str
    labels: list[str] = Field(default_factory=list)
    github_issue_created: Literal[False] = False

    @field_validator("source_path", "title", "body")
    @classmethod
    def _text(cls, value: str) -> str:
        return _non_empty(value)

    @field_validator("issue_id")
    @classmethod
    def _issue_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("labels")
    @classmethod
    def _labels(cls, values: list[str]) -> list[str]:
        return _unique_text(values)


class GitHubPrPlan(AgentAccessModel):
    """Dry-run GitHub pull request creation plan."""

    base: str
    head: str
    title: str
    body: str
    github_pr_created: Literal[False] = False

    @field_validator("base", "head", "title", "body")
    @classmethod
    def _text(cls, value: str) -> str:
        return _non_empty(value)


class ForgePreviewResult(AgentAccessModel):
    """Dry-run forge preview result."""

    kind: Literal["status", "github_issue", "github_pr"]
    dry_run_only: Literal[True] = True
    network_calls_performed: Literal[False] = False
    git_writes_performed: Literal[False] = False
    github_writes_performed: Literal[False] = False
    authority_warning: str = FORGE_AUTHORITY_WARNING
    local_git_plan: LocalGitPlan | None = None
    github_issue_plan: GitHubIssuePlan | None = None
    github_pr_plan: GitHubPrPlan | None = None
    warnings: list[str] = Field(default_factory=list)

    @field_validator("warnings")
    @classmethod
    def _warnings(cls, values: list[str]) -> list[str]:
        return _unique_text(values)


class ForgeActionResult(AgentAccessModel):
    """Result for explicit forge actions."""

    action: str
    action_performed: bool = False
    network_calls_performed: Literal[False] = False
    git_writes_performed: bool = False
    github_writes_performed: Literal[False] = False
    push_performed: Literal[False] = False
    github_pr_created: Literal[False] = False
    branch: str | None = None
    commit_hash: str | None = None
    validation_performed: bool = False
    gate_performed: bool = False
    authority_warning: str = FORGE_AUTHORITY_WARNING

    @field_validator("action")
    @classmethod
    def _action(cls, value: str) -> str:
        return _non_empty(value)

    @field_validator("branch", "commit_hash")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _non_empty(value)


def _non_empty(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("text field must be non-empty")
    return normalized


def _unique_text(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = _non_empty(value)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
