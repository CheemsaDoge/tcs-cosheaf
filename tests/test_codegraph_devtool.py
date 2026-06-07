from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dev" / "codegraph_probe.py"


def test_codegraph_probe_missing_tool_falls_back_without_failure() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--command",
            "definitely-missing-codegraph-command",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["tool"] == "CodeGraph"
    assert payload["status"] == "unavailable"
    assert payload["fallback"] == "run_full_verification"
    assert payload["output_dir"] == ".cosheaf/dev/codegraph"
    assert payload["truth_path"] == "none"


def test_codegraph_probe_strict_mode_fails_when_missing() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--command",
            "definitely-missing-codegraph-command",
            "--strict",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "unavailable"
    assert payload["fallback"] == "run_full_verification"


def test_codegraph_generated_outputs_are_gitignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert ".codegraph/" in gitignore
    assert ".cosheaf/dev/codegraph/" in gitignore
    assert "codegraph*.db" in gitignore
