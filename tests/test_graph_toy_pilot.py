from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "experiments" / "evaluators" / "check_graph_toy.py"
ARTIFACT = (
    ROOT
    / "kb"
    / "draft"
    / "constructions"
    / "construction.graph-toy.0001.yaml"
)


def test_graph_toy_checker_passes_on_pilot_artifact() -> None:
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(ARTIFACT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "toy graph verified" in result.stdout


def test_graph_toy_checker_rejects_tampered_graph(tmp_path: Path) -> None:
    tampered_artifact = tmp_path / "construction.graph-toy.0001.yaml"
    text = ARTIFACT.read_text(encoding="utf-8")
    text = text.replace("    - [v4, v0]\n", "")
    tampered_artifact.write_text(text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CHECKER), str(tampered_artifact)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "edge count mismatch" in result.stderr
