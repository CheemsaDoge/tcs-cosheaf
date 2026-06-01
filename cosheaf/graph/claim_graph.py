"""Directed dependency graph for loaded research artifacts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from cosheaf.core.artifact import BaseArtifact
from cosheaf.core.status import ArtifactStatus, is_preaccepted_status
from cosheaf.storage.loader import LoadedRecord


@dataclass(frozen=True)
class GraphNode:
    """A deterministic graph node for one loaded artifact."""

    artifact_id: str
    artifact_type: str
    status: str
    path: str
    title: str
    domain: tuple[str, ...]


@dataclass(frozen=True)
class GraphEdge:
    """A dependency edge directed from artifact to dependency."""

    source_id: str
    target_id: str


@dataclass(frozen=True)
class GraphIssue:
    """A deterministic graph issue row."""

    source_id: str
    target_id: str
    source_path: str
    message: str


@dataclass(frozen=True)
class DependencyGraph:
    """Loaded artifact dependency graph and detected issues."""

    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    missing_dependencies: tuple[GraphIssue, ...]
    cycles: tuple[tuple[str, ...], ...]
    accepted_draft_violations: tuple[GraphIssue, ...]

    @property
    def has_issues(self) -> bool:
        return bool(
            self.missing_dependencies
            or self.cycles
            or self.accepted_draft_violations
        )


def build_dependency_graph(records: Iterable[LoadedRecord]) -> DependencyGraph:
    """Build a deterministic dependency graph from loaded artifact records."""
    artifact_records = [
        record for record in records if isinstance(record.record, BaseArtifact)
    ]
    artifact_records = sorted(
        artifact_records,
        key=lambda loaded: (loaded.id, loaded.source_path.as_posix()),
    )
    records_by_id = {loaded.id: loaded for loaded in artifact_records}

    nodes = tuple(_node_from_loaded(loaded) for loaded in artifact_records)
    edges = tuple(sorted(_edges_from_records(artifact_records), key=_edge_sort_key))
    missing_dependencies = _find_missing_dependencies(artifact_records, records_by_id)
    accepted_draft_violations = _find_accepted_draft_violations(
        artifact_records,
        records_by_id,
    )
    cycles = _find_cycles(edges, frozenset(records_by_id))

    return DependencyGraph(
        nodes=nodes,
        edges=edges,
        missing_dependencies=missing_dependencies,
        cycles=cycles,
        accepted_draft_violations=accepted_draft_violations,
    )


def _node_from_loaded(loaded: LoadedRecord) -> GraphNode:
    artifact = loaded.record
    if not isinstance(artifact, BaseArtifact):
        raise TypeError("graph nodes can only be built from BaseArtifact records")
    return GraphNode(
        artifact_id=artifact.id,
        artifact_type=artifact.type.value,
        status=artifact.status.value,
        path=loaded.source_path.as_posix(),
        title=artifact.title,
        domain=tuple(artifact.domain),
    )


def _edges_from_records(artifact_records: list[LoadedRecord]) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    for loaded in artifact_records:
        artifact = loaded.record
        if not isinstance(artifact, BaseArtifact):
            continue
        edges.extend(
            GraphEdge(source_id=artifact.id, target_id=dependency_id)
            for dependency_id in artifact.depends_on
        )
    return edges


def _find_missing_dependencies(
    artifact_records: list[LoadedRecord],
    records_by_id: dict[str, LoadedRecord],
) -> tuple[GraphIssue, ...]:
    issues: list[GraphIssue] = []
    for loaded in artifact_records:
        artifact = loaded.record
        if not isinstance(artifact, BaseArtifact):
            continue
        for dependency_id in artifact.depends_on:
            if dependency_id in records_by_id:
                continue
            issues.append(
                GraphIssue(
                    source_id=artifact.id,
                    target_id=dependency_id,
                    source_path=loaded.source_path.as_posix(),
                    message=f"missing dependency: {dependency_id}",
                )
            )
    return _sort_issues(issues)


def _find_accepted_draft_violations(
    artifact_records: list[LoadedRecord],
    records_by_id: dict[str, LoadedRecord],
) -> tuple[GraphIssue, ...]:
    issues: list[GraphIssue] = []
    for loaded in artifact_records:
        artifact = loaded.record
        if not isinstance(artifact, BaseArtifact):
            continue
        for dependency_id in artifact.depends_on:
            dependency = records_by_id.get(dependency_id)
            if dependency is None or not isinstance(dependency.record, BaseArtifact):
                continue
            if (
                artifact.status is ArtifactStatus.ACCEPTED
                and is_preaccepted_status(dependency.record.status)
            ):
                issues.append(
                    GraphIssue(
                        source_id=artifact.id,
                        target_id=dependency_id,
                        source_path=loaded.source_path.as_posix(),
                        message=(
                            "accepted artifact depends on draft artifact: "
                            f"{dependency_id}"
                        ),
                    )
                )
    return _sort_issues(issues)


def _find_cycles(
    edges: tuple[GraphEdge, ...],
    known_ids: frozenset[str],
) -> tuple[tuple[str, ...], ...]:
    adjacency: dict[str, tuple[str, ...]] = {
        artifact_id: tuple() for artifact_id in sorted(known_ids)
    }
    mutable_adjacency: dict[str, list[str]] = {
        artifact_id: [] for artifact_id in sorted(known_ids)
    }
    for edge in edges:
        if edge.source_id in known_ids and edge.target_id in known_ids:
            mutable_adjacency[edge.source_id].append(edge.target_id)
    for artifact_id, dependencies in mutable_adjacency.items():
        adjacency[artifact_id] = tuple(sorted(dependencies))

    cycles: set[tuple[str, ...]] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(artifact_id: str) -> None:
        if artifact_id in stack:
            cycle = stack[stack.index(artifact_id) :] + [artifact_id]
            cycles.add(_canonical_cycle(tuple(cycle)))
            return
        if artifact_id in visited:
            return

        stack.append(artifact_id)
        for dependency_id in adjacency[artifact_id]:
            visit(dependency_id)
        stack.pop()
        visited.add(artifact_id)

    for artifact_id in sorted(known_ids):
        visit(artifact_id)

    return tuple(sorted(cycles))


def _canonical_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    members = cycle[:-1]
    rotations = [
        members[index:] + members[:index] + (members[index],)
        for index in range(len(members))
    ]
    return min(rotations)


def _sort_issues(issues: list[GraphIssue]) -> tuple[GraphIssue, ...]:
    return tuple(
        sorted(
            issues,
            key=lambda issue: (
                issue.source_id,
                issue.target_id,
                issue.source_path,
                issue.message,
            ),
        )
    )


def _edge_sort_key(edge: GraphEdge) -> tuple[str, str]:
    return (edge.source_id, edge.target_id)
