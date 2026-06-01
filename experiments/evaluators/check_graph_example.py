"""Check the example triangle graph construction."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_graph_example.py <artifact-yaml>", file=sys.stderr)
        return 2

    artifact_path = Path(argv[1])
    if not artifact_path.exists():
        print(f"artifact not found: {artifact_path}", file=sys.stderr)
        return 2

    artifact = yaml.safe_load(artifact_path.read_text(encoding="utf-8"))
    if not isinstance(artifact, dict):
        print("artifact YAML root must be a mapping", file=sys.stderr)
        return 1

    errors = _check_triangle_graph(artifact)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("triangle graph example verified")
    return 0


def _check_triangle_graph(artifact: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if artifact.get("id") != "construction.example.triangle-graph":
        errors.append("unexpected artifact id")
    if artifact.get("type") != "construction":
        errors.append("artifact is not a construction")
    statement = str(artifact.get("statement", ""))
    for expected in ("K_3", "vertices", "edges", "ab", "ac", "bc"):
        if expected not in statement:
            errors.append(f"statement is missing {expected!r}")
    return errors


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
