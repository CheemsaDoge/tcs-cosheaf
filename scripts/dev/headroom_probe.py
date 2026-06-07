"""Developer-only Headroom experiment scaffold.

This script is intentionally outside the runtime package. Headroom is optional,
default-off, and limited to noncanonical developer-facing text views. It never
rewrites source-of-truth files and never feeds compressed text into artifacts,
retrieval ranking, gates, or promotion.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT_DIR = ".cosheaf/dev/headroom"

PROTECTED_EXACT_PATHS = {
    "AGENTS.md",
    "docs/CODEX_WORKFLOW.md",
    "context/INTERFACE_REGISTRY.md",
}

PROTECTED_PREFIXES = (
    ".github/",
    ".cosheaf/memory/",
    ".cosheaf/reports/",
    "context/",
    "docs/ADR/",
    "kb/",
    "reviews/",
    "schemas/",
    "sources/",
)

PROTECTED_SUFFIXES = (
    ".yaml",
    ".yml",
    "RETRIEVAL_AUDIT.json",
    "artifact_manifest.json",
    "index.sqlite",
)

ALLOWED_PREFIXES = (
    ".cosheaf/dev/headroom/",
    ".cosheaf/logs/",
)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = probe_headroom(
        enabled=args.enable,
        command=args.command,
        source=args.source,
        output_dir=args.output_dir,
        timeout_seconds=args.timeout_seconds,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        _print_text(result)
    if result["status"] == "refused":
        return 3
    if result["status"] == "unavailable" and args.strict:
        return 2
    return 0


def probe_headroom(
    *,
    enabled: bool,
    command: str,
    source: str,
    output_dir: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Return deterministic metadata for a default-off Headroom experiment."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    normalized_source = _normalize_repo_path(source)
    normalized_output_dir = _normalize_repo_path(output_dir)
    allowed, reason = _is_allowed_source(normalized_source)
    base = {
        "tool": "Headroom",
        "enabled": enabled,
        "command": command,
        "source": normalized_source,
        "source_allowed": allowed,
        "source_policy_reason": reason,
        "output_dir": normalized_output_dir,
        "compressed_output": None,
        "fallback": "use_original_text",
        "truth_path": "none",
        "original_remains_retrievable": True,
        "allowed_use": "noncanonical_log_or_tool_output_view_only",
        "feeds_artifact_truth": False,
        "feeds_retrieval_ranking": False,
        "feeds_gates": False,
        "feeds_promotion": False,
        "writes_canonical_files": False,
        "runs_learn_mode": False,
    }

    if not enabled:
        return {
            **base,
            "status": "disabled",
            "executable": None,
            "version_command": None,
            "version_returncode": None,
            "version_stdout": "",
            "version_stderr": "",
            "message": (
                "Headroom experiment is disabled by default; original text is used."
            ),
        }

    if not allowed:
        return {
            **base,
            "status": "refused",
            "executable": None,
            "version_command": None,
            "version_returncode": None,
            "version_stdout": "",
            "version_stderr": "",
            "message": f"Refused protected or canonical source path: {reason}.",
        }

    executable = shutil.which(command)
    if executable is None:
        return {
            **base,
            "status": "unavailable",
            "executable": None,
            "version_command": None,
            "version_returncode": None,
            "version_stdout": "",
            "version_stderr": "Headroom command not found; use original text.",
            "message": "Headroom command not found; compression experiment skipped.",
        }

    version = _run_version(executable, timeout_seconds)
    return {
        **base,
        "status": "available",
        "executable": executable,
        "version_command": version["command"],
        "version_returncode": version["returncode"],
        "version_stdout": version["stdout"],
        "version_stderr": version["stderr"],
        "message": (
            "Headroom command is available; this scaffold records an experiment "
            "boundary only and does not run compression automatically."
        ),
    }


def _run_version(executable: str, timeout_seconds: int) -> dict[str, Any]:
    command = [executable, "--version"]
    try:
        completed = subprocess.run(
            command,
            cwd=Path.cwd(),
            timeout=timeout_seconds,
            shell=False,
            check=False,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _normalize_repo_path(value: str) -> str:
    path = Path(value)
    normalized = path.as_posix()
    if not normalized or normalized == ".":
        raise ValueError("path must be repository-local and non-empty")
    if path.is_absolute() or normalized == ".." or normalized.startswith("../"):
        raise ValueError("path must be repository-local")
    return normalized


def _is_allowed_source(source: str) -> tuple[bool, str]:
    if source in PROTECTED_EXACT_PATHS:
        return False, "protected governance document"
    if source.startswith(PROTECTED_PREFIXES):
        return False, "protected canonical or governance path"
    if source.endswith(PROTECTED_SUFFIXES):
        return False, "protected canonical file type"
    if source.startswith(ALLOWED_PREFIXES):
        return True, "allowed noncanonical developer output"
    if _is_allowed_stdout_stderr(source):
        return True, "allowed stdout/stderr sidecar"
    return False, "not an approved noncanonical Headroom experiment input"


def _is_allowed_stdout_stderr(source: str) -> bool:
    if not (
        source.startswith(".cosheaf/tasks/")
        or source.startswith(".cosheaf/orchestrator/")
    ):
        return False
    return source.endswith("/stdout.txt") or source.endswith("/stderr.txt")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe optional default-off Headroom experiment boundaries."
    )
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--source", required=True)
    parser.add_argument("--command", default="headroom")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def _print_text(result: dict[str, Any]) -> None:
    print(f"Headroom status: {result['status']}")
    print(f"Enabled: {result['enabled']}")
    print(f"Source: {result['source']}")
    print(f"Source allowed: {result['source_allowed']}")
    print("Truth path: none")
    print("Fallback: use original text")


if __name__ == "__main__":
    raise SystemExit(main())
