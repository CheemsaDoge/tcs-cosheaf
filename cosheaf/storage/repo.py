"""Repository context for filesystem-backed storage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cosheaf.config.workspace import (
    KbRootConfig,
    WorkspaceConfig,
    load_workspace_config,
)


@dataclass(frozen=True, init=False)
class RepoContext:
    """Filesystem context for a TCS-Cosheaf repository checkout."""

    repo_root: Path
    workspace_config: WorkspaceConfig

    def __init__(
        self,
        repo_root: str | Path,
        workspace_config: WorkspaceConfig | None = None,
    ) -> None:
        resolved_root = Path(repo_root).resolve()
        object.__setattr__(self, "repo_root", resolved_root)
        object.__setattr__(
            self,
            "workspace_config",
            workspace_config or load_workspace_config(resolved_root),
        )

    def resolve(self, relative_path: str | Path) -> Path:
        """Resolve a repository-relative path inside this checkout."""
        return (self.repo_root / relative_path).resolve()

    def discovery_roots(self) -> tuple[str, ...]:
        """Return repository-relative YAML discovery roots."""
        roots = [root.path for root in self.workspace_config.ordered_kb]
        roots.extend(["issues", "examples"])
        return tuple(dict.fromkeys(roots))

    def kb_root_for_path(self, path: str | Path) -> KbRootConfig | None:
        """Return the configured KB root containing a repository-relative path."""
        relative = Path(path).as_posix()
        matches = [
            root
            for root in self.workspace_config.ordered_kb
            if relative == root.path or relative.startswith(f"{root.path}/")
        ]
        if not matches:
            return None
        return max(matches, key=lambda root: len(root.path))

    def kb_relative_path(self, path: str | Path) -> Path | None:
        """Return a path relative to its configured KB root, when any."""
        root = self.kb_root_for_path(path)
        if root is None:
            return None
        relative = Path(path).as_posix()
        if relative == root.path:
            return Path()
        return Path(relative.removeprefix(f"{root.path}/"))
