"""Check the toy graph pilot construction."""

from __future__ import annotations

import sys
from collections import deque
from itertools import combinations
from pathlib import Path
from textwrap import dedent
from typing import Any

import yaml  # type: ignore[import-untyped]

CHECKER_MARKER = "CHECKER_DATA:\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_graph_toy.py <artifact-yaml>", file=sys.stderr)
        return 2

    artifact_path = Path(argv[1])
    if not artifact_path.exists():
        print(f"artifact not found: {artifact_path}", file=sys.stderr)
        return 2

    artifact = yaml.safe_load(artifact_path.read_text(encoding="utf-8"))
    if not isinstance(artifact, dict):
        print("artifact YAML root must be a mapping", file=sys.stderr)
        return 1

    errors = check_toy_graph_artifact(artifact)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    graph = _load_graph_data(str(artifact["statement"]))
    vertex_count = len(graph["vertices"])
    edge_count = len(graph["edges"])
    print(f"toy graph verified: {vertex_count} vertices, {edge_count} edges")
    return 0


def check_toy_graph_artifact(artifact: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if artifact.get("type") != "construction":
        errors.append("artifact type must be construction")
    if artifact.get("status") not in {"draft", "locally_tested"}:
        errors.append("artifact status must remain draft or locally_tested")
    if "graph-theory" not in artifact.get("domain", []):
        errors.append("artifact domain must include graph-theory")

    statement = artifact.get("statement")
    if not isinstance(statement, str):
        errors.append("artifact statement must be a string")
        return errors

    try:
        graph = _load_graph_data(statement)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    errors.extend(_validate_graph_shape(graph))
    if errors:
        return errors

    expected = graph["expected"]
    vertices = tuple(graph["vertices"])
    edges = tuple(tuple(edge) for edge in graph["edges"])
    properties = _graph_properties(vertices, edges)
    errors.extend(_compare_expected(properties, expected))
    return errors


def _load_graph_data(statement: str) -> dict[str, Any]:
    if CHECKER_MARKER not in statement:
        raise ValueError("statement is missing CHECKER_DATA block")
    raw_data = statement.split(CHECKER_MARKER, 1)[1]
    data = yaml.safe_load(dedent(raw_data))
    if not isinstance(data, dict):
        raise ValueError("CHECKER_DATA must parse as a mapping")
    return data


def _validate_graph_shape(graph: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    vertices = graph.get("vertices")
    edges = graph.get("edges")
    expected = graph.get("expected")
    if not isinstance(vertices, list) or not all(
        isinstance(vertex, str) for vertex in vertices
    ):
        errors.append("vertices must be a list of strings")
    elif len(set(vertices)) != len(vertices):
        errors.append("vertices must be unique")

    if not isinstance(edges, list):
        errors.append("edges must be a list")
    elif isinstance(vertices, list):
        errors.extend(_validate_edges(edges, set(vertices)))

    if not isinstance(expected, dict):
        errors.append("expected must be a mapping")
    return errors


def _validate_edges(edges: list[Any], vertices: set[str]) -> list[str]:
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for edge in edges:
        if not _is_edge(edge):
            errors.append(f"invalid edge entry: {edge!r}")
            continue
        left, right = edge
        if left == right:
            errors.append(f"loop edge is not allowed: {edge!r}")
        if left not in vertices or right not in vertices:
            errors.append(f"edge endpoint is not a vertex: {edge!r}")
        normalized = tuple(sorted((left, right)))
        if normalized in seen:
            errors.append(f"duplicate undirected edge: {edge!r}")
        seen.add(normalized)
    return errors


def _is_edge(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[0], str)
        and isinstance(value[1], str)
    )


def _graph_properties(
    vertices: tuple[str, ...],
    edges: tuple[tuple[str, str], ...],
) -> dict[str, Any]:
    adjacency = {vertex: set[str]() for vertex in vertices}
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)

    return {
        "vertex_count": len(vertices),
        "edge_count": len(edges),
        "degree_sequence": sorted(len(adjacency[vertex]) for vertex in vertices),
        "connected": _is_connected(vertices, adjacency),
        "triangle_free": not _contains_triangle(vertices, adjacency),
        "contains_triangle": _contains_triangle(vertices, adjacency),
    }


def _is_connected(
    vertices: tuple[str, ...],
    adjacency: dict[str, set[str]],
) -> bool:
    if not vertices:
        return True
    visited = {vertices[0]}
    queue: deque[str] = deque([vertices[0]])
    while queue:
        vertex = queue.popleft()
        for neighbor in sorted(adjacency[vertex]):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            queue.append(neighbor)
    return len(visited) == len(vertices)


def _contains_triangle(
    vertices: tuple[str, ...],
    adjacency: dict[str, set[str]],
) -> bool:
    for left, middle, right in combinations(vertices, 3):
        if (
            middle in adjacency[left]
            and right in adjacency[left]
            and right in adjacency[middle]
        ):
            return True
    return False


def _compare_expected(
    properties: dict[str, Any],
    expected: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    labels = {
        "vertex_count": "vertex count",
        "edge_count": "edge count",
        "degree_sequence": "degree sequence",
        "connected": "connectedness",
        "triangle_free": "triangle-freeness",
        "contains_triangle": "contains-triangle property",
    }
    for key, label in labels.items():
        if expected.get(key) != properties[key]:
            errors.append(
                f"{label} mismatch: expected {expected.get(key)!r}, "
                f"computed {properties[key]!r}"
            )
    return errors


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
