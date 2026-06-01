"""Repository context for filesystem-backed storage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepoContext:
    """Filesystem context for a TCS-Cosheaf repository checkout."""

    repo_root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "repo_root", self.repo_root.resolve())

    def resolve(self, relative_path: str | Path) -> Path:
        """Resolve a repository-relative path inside this checkout."""
        return (self.repo_root / relative_path).resolve()
