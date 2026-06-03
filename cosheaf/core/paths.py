"""Repository path helpers."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

from cosheaf.core.status import ArtifactStatus, ArtifactType

DISCOVERY_ROOTS = ("kb", "issues", "examples")
YAML_SUFFIXES = frozenset({".yaml", ".yml"})

ARTIFACT_TYPE_DIRECTORIES = {
    ArtifactType.DEFINITION: "definitions",
    ArtifactType.CLAIM: "claims",
    ArtifactType.THEOREM: "theorems",
    ArtifactType.CONJECTURE: "conjectures",
    ArtifactType.PROOF: "proofs",
    ArtifactType.PROOF_ATTEMPT: "proof_attempts",
    ArtifactType.CONSTRUCTION: "constructions",
    ArtifactType.ALGORITHM: "algorithms",
    ArtifactType.REDUCTION: "reductions",
    ArtifactType.COUNTEREXAMPLE: "counterexamples",
    ArtifactType.EXPERIMENT: "experiments",
    ArtifactType.VERIFIER: "verifiers",
}


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


def artifact_type_directory(artifact_type: ArtifactType) -> str:
    """Return the knowledge-base directory name for an artifact type."""
    try:
        return ARTIFACT_TYPE_DIRECTORIES[artifact_type]
    except KeyError as exc:
        raise ValueError(
            f"{artifact_type.value} records are not artifact lifecycle records"
        ) from exc


def lifecycle_artifact_path(
    artifact_type: ArtifactType,
    status: ArtifactStatus,
    artifact_id: str,
) -> Path:
    """Return the deterministic repository-relative path for a lifecycle status."""
    if status is ArtifactStatus.ACCEPTED:
        return Path("kb") / "accepted" / artifact_type_directory(artifact_type) / (
            f"{artifact_id}.yaml"
        )
    if status is ArtifactStatus.REFUTED:
        return Path("kb") / "refuted" / f"{artifact_id}.yaml"
    if status in {ArtifactStatus.OBSOLETE, ArtifactStatus.SUPERSEDED}:
        return Path("kb") / "obsolete" / f"{artifact_id}.yaml"
    return Path("kb") / "draft" / artifact_type_directory(artifact_type) / (
        f"{artifact_id}.yaml"
    )
