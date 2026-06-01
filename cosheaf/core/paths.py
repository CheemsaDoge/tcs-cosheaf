"""Repository path helpers."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

DISCOVERY_ROOTS = ("kb", "issues", "examples")
YAML_SUFFIXES = frozenset({".yaml", ".yml"})


def normalize_repo_path(path: str | Path) -> str:
    """Return a stable POSIX-style repository path string."""
    return PurePosixPath(PureWindowsPath(str(path)).as_posix()).as_posix()


def repo_relative_path(repo_root: Path, path: Path) -> Path:
    """Return a path relative to the repository root."""
    return path.resolve().relative_to(repo_root.resolve())


def repo_relative_posix(repo_root: Path, path: Path) -> str:
    """Return a POSIX-style path relative to the repository root."""
    return normalize_repo_path(repo_relative_path(repo_root, path))


def is_yaml_path(path: Path) -> bool:
    """Return whether a path has a YAML suffix."""
    return path.suffix.lower() in YAML_SUFFIXES
