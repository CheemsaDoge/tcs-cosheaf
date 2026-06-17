"""Checker run storage."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from cosheaf.checkers.models import (
    CheckerInput,
    CheckerRunRecord,
    CheckerSpec,
)
from cosheaf.checkers.registry import CheckerExecution, CheckerRegistry
from cosheaf.storage.repo import RepoContext


def run_checker_and_store(
    registry: CheckerRegistry,
    context: RepoContext,
    checker_id: str,
    checker_input: CheckerInput,
) -> CheckerRunRecord:
    """Run one checker and store its result under .cosheaf/checker-runs."""
    execution = registry.run(checker_id, context, checker_input)
    spec = registry.get(checker_id)
    if spec is None:
        raise ValueError(f"unknown checker: {checker_id}")
    return store_checker_execution(context, spec, checker_input, execution)


def store_checker_execution(
    context: RepoContext,
    spec: CheckerSpec,
    checker_input: CheckerInput,
    execution: CheckerExecution,
) -> CheckerRunRecord:
    """Persist one checker execution."""
    created_at = datetime.now(UTC)
    run_id = _new_run_id(context, spec.checker_id, created_at)
    run_dir = context.resolve(Path(".cosheaf") / "checker-runs" / run_id)
    run_dir.mkdir(parents=True, exist_ok=False)
    result_path = run_dir / "result.json"
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    stdout_path.write_text(execution.stdout, encoding="utf-8", newline="\n")
    stderr_path.write_text(execution.stderr, encoding="utf-8", newline="\n")
    result = execution.result.model_copy(
        update={
            "stdout_path": _relative(context, stdout_path),
            "stderr_path": _relative(context, stderr_path),
            "output_paths": tuple(
                sorted(
                    set(execution.result.output_paths)
                    | {
                        _relative(context, stdout_path),
                        _relative(context, stderr_path),
                    }
                )
            ),
        }
    )
    record = CheckerRunRecord(
        run_id=run_id,
        checker=spec,
        input=checker_input,
        result=result,
        created_at=created_at,
        result_path=_relative(context, result_path),
        stdout_path=_relative(context, stdout_path),
        stderr_path=_relative(context, stderr_path),
        authority_notice=spec.authority_notice,
    )
    result_path.write_text(record.to_json(), encoding="utf-8", newline="\n")
    return record


def run_suite_and_store(
    registry: CheckerRegistry,
    context: RepoContext,
    checker_input: CheckerInput,
) -> tuple[CheckerRunRecord, ...]:
    """Run all registered checkers and store their records."""
    records = [
        run_checker_and_store(registry, context, checker_id, checker_input)
        for checker_id in registry.checker_ids
    ]
    return tuple(records)


def suite_payload(records: tuple[CheckerRunRecord, ...]) -> dict[str, object]:
    """Return deterministic suite JSON payload."""
    status_counts: dict[str, int] = {}
    for record in records:
        status = record.result.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "schema_version": 1,
        "kind": "checker_suite_result",
        "run_count": len(records),
        "status_counts": dict(sorted(status_counts.items())),
        "has_blocking_result": any(record.result.is_blocking for record in records),
        "runs": [record.to_dict() for record in records],
    }


def _new_run_id(context: RepoContext, checker_id: str, created_at: datetime) -> str:
    timestamp = created_at.strftime("%Y%m%dT%H%M%S%fZ")
    safe_checker = _safe_name(checker_id)
    base = f"checker.{safe_checker}.{timestamp}"
    run_root = context.resolve(".cosheaf/checker-runs")
    candidate = base
    suffix = 1
    while (run_root / candidate).exists():
        suffix += 1
        candidate = f"{base}.{suffix}"
    return candidate


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in ".-_" else "_" for char in value)


def _relative(context: RepoContext, path: Path) -> str:
    return path.resolve().relative_to(context.repo_root).as_posix()


def dumps_json(payload: object) -> str:
    """Return deterministic JSON text."""
    return json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
