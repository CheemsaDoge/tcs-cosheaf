"""Developer-only CodeGraph availability probe.

This script is intentionally outside the runtime package. It never feeds
CodeGraph output into artifact truth, retrieval ranking, gates, or promotion.
When CodeGraph is unavailable, it reports a full-verification fallback.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT_DIR = ".cosheaf/dev/codegraph"


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = probe_codegraph(
        command=args.command,
        output_dir=args.output_dir,
        timeout_seconds=args.timeout_seconds,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        _print_text(result)
    if result["status"] == "unavailable" and args.strict:
        return 2
    return 0


def probe_codegraph(
    *,
    command: str,
    output_dir: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Return deterministic availability metadata for a CodeGraph command."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    executable = shutil.which(command)
    base = {
        "tool": "CodeGraph",
        "command": command,
        "output_dir": _normalize_output_dir(output_dir),
        "fallback": "run_full_verification",
        "truth_path": "none",
        "allowed_use": "developer_code_navigation_only",
        "feeds_artifact_truth": False,
        "feeds_retrieval_ranking": False,
        "feeds_gates": False,
        "feeds_promotion": False,
    }
    if executable is None:
        return {
            **base,
            "status": "unavailable",
            "executable": None,
            "version_command": None,
            "version_returncode": None,
            "version_stdout": "",
            "version_stderr": "CodeGraph command not found; run full verification.",
        }

    completed = subprocess.run(
        [executable, "--version"],
        cwd=Path.cwd(),
        timeout=timeout_seconds,
        shell=False,
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        **base,
        "status": "available",
        "executable": executable,
        "version_command": [executable, "--version"],
        "version_returncode": completed.returncode,
        "version_stdout": completed.stdout,
        "version_stderr": completed.stderr,
    }


def _normalize_output_dir(value: str) -> str:
    normalized = Path(value).as_posix()
    if not normalized or normalized == ".":
        raise ValueError("output_dir must be repository-local and non-empty")
    if Path(value).is_absolute() or normalized == ".." or normalized.startswith("../"):
        raise ValueError("output_dir must be repository-local")
    return normalized


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe optional developer-only CodeGraph availability."
    )
    parser.add_argument("--command", default="codegraph")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def _print_text(result: dict[str, Any]) -> None:
    print(f"CodeGraph status: {result['status']}")
    print(f"Command: {result['command']}")
    print(f"Output directory: {result['output_dir']}")
    print("Truth path: none")
    print("Fallback: run full verification")


if __name__ == "__main__":
    raise SystemExit(main())
