from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dev" / "headroom_probe.py"


def _run_headroom(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_headroom_probe_is_default_off() -> None:
    result = _run_headroom(
        "--source",
        ".cosheaf/logs/example.stdout.txt",
        "--command",
        "definitely-missing-headroom-command",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["tool"] == "Headroom"
    assert payload["status"] == "disabled"
    assert payload["enabled"] is False
    assert payload["fallback"] == "use_original_text"
    assert payload["source"] == ".cosheaf/logs/example.stdout.txt"
    assert payload["compressed_output"] is None
    assert payload["original_remains_retrievable"] is True
    assert payload["feeds_artifact_truth"] is False
    assert payload["feeds_retrieval_ranking"] is False
    assert payload["feeds_gates"] is False
    assert payload["feeds_promotion"] is False


def test_headroom_probe_missing_tool_skips_when_enabled() -> None:
    result = _run_headroom(
        "--enable",
        "--source",
        ".cosheaf/logs/example.stdout.txt",
        "--command",
        "definitely-missing-headroom-command",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "unavailable"
    assert payload["enabled"] is True
    assert payload["fallback"] == "use_original_text"
    assert payload["executable"] is None
    assert payload["source_allowed"] is True
    assert "not found" in payload["message"]


def test_headroom_probe_strict_mode_fails_when_missing() -> None:
    result = _run_headroom(
        "--enable",
        "--strict",
        "--source",
        ".cosheaf/logs/example.stdout.txt",
        "--command",
        "definitely-missing-headroom-command",
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "unavailable"
    assert payload["fallback"] == "use_original_text"


def test_headroom_rejects_canonical_files_and_leaves_them_untouched() -> None:
    protected = ROOT / "AGENTS.md"
    before = protected.read_text(encoding="utf-8")

    result = _run_headroom(
        "--enable",
        "--source",
        "AGENTS.md",
        "--command",
        "definitely-missing-headroom-command",
    )

    assert result.returncode == 3
    assert protected.read_text(encoding="utf-8") == before
    payload = json.loads(result.stdout)
    assert payload["status"] == "refused"
    assert payload["source_allowed"] is False
    assert payload["fallback"] == "use_original_text"
    assert payload["compressed_output"] is None
    assert "protected" in payload["message"]


def test_headroom_generated_outputs_are_gitignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert ".cosheaf/dev/headroom/" in gitignore
    assert ".headroom/" in gitignore
    assert "headroom*.json" in gitignore
