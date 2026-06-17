"""Typer CLI for the checker registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from cosheaf.checkers.builtins import default_checker_registry
from cosheaf.checkers.models import CheckerInput
from cosheaf.checkers.registry import CheckerRegistryError
from cosheaf.checkers.storage import (
    run_checker_and_store,
    run_suite_and_store,
    suite_payload,
)
from cosheaf.services.models import ErrorResult
from cosheaf.storage.repo import RepoContext

checker_app = typer.Typer(
    add_completion=False,
    help="Typed checker registry commands.",
    no_args_is_help=True,
)


@checker_app.command("list")
def checker_list(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON.",
    ),
) -> None:
    """List available built-in checkers."""
    registry = default_checker_registry()
    payload = {
        "schema_version": 1,
        "kind": "checker_registry",
        "checkers": [spec.to_dict() for spec in registry.specs],
    }
    if json_output:
        _emit_json(payload)
        return
    console = Console(width=120, markup=False)
    for spec in registry.specs:
        console.print(f"{spec.checker_id}: {spec.title}")


@checker_app.command("describe")
def checker_describe(
    checker_id: str = typer.Argument(..., help="Checker ID to describe."),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON.",
    ),
) -> None:
    """Describe one checker."""
    registry = default_checker_registry()
    spec = registry.get(checker_id)
    if spec is None:
        _exit_with_error(
            ErrorResult(
                code="checker_not_found",
                message=f"checker not found: {checker_id}",
                remediation="Run `cosheaf checker list --json` to inspect IDs.",
                blocking=True,
                details={"checker_id": checker_id},
            ),
            json_output=json_output,
        )
    assert spec is not None
    payload = {
        "schema_version": 1,
        "kind": "checker_spec",
        "checker": spec.to_dict(),
    }
    if json_output:
        _emit_json(payload)
        return
    Console(width=120, markup=False).print(
        f"{spec.checker_id}: {spec.description}"
    )


@checker_app.command("run")
def checker_run(
    checker_id: str = typer.Argument(..., help="Checker ID to run."),
    input_json: Path = typer.Option(
        ...,
        "--input-json",
        help="Path to checker input JSON.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root for checker storage and policy.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON.",
    ),
) -> None:
    """Run one checker and write a checker-run record."""
    checker_input = _read_checker_input(input_json, json_output=json_output)
    registry = default_checker_registry()
    try:
        record = run_checker_and_store(
            registry,
            RepoContext(repo_root),
            checker_id,
            checker_input,
        )
    except CheckerRegistryError as exc:
        _exit_with_error(
            ErrorResult(
                code="checker_not_found",
                message=str(exc),
                remediation="Run `cosheaf checker list --json` to inspect IDs.",
                blocking=True,
                related_path=str(input_json),
                details={"checker_id": checker_id},
            ),
            json_output=json_output,
        )
    payload = record.to_dict()
    if json_output:
        _emit_json(payload)
    else:
        Console(width=120, markup=False).print(
            f"{record.run_id}: {record.result.status.value} - "
            f"{record.result.message}"
        )
    if record.result.is_blocking:
        raise typer.Exit(code=1)


@checker_app.command("run-suite")
def checker_run_suite(
    input_json: Path = typer.Option(
        ...,
        "--input-json",
        help="Path to checker input JSON.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root for checker storage and policy.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON.",
    ),
) -> None:
    """Run the default checker suite and write checker-run records."""
    checker_input = _read_checker_input(input_json, json_output=json_output)
    registry = default_checker_registry()
    records = run_suite_and_store(registry, RepoContext(repo_root), checker_input)
    payload = suite_payload(records)
    if json_output:
        _emit_json(payload)
    else:
        Console(width=120, markup=False).print(
            "checker suite: "
            f"{payload['run_count']} run(s), "
            f"blocking={str(payload['has_blocking_result']).lower()}"
        )
    if any(record.result.is_blocking for record in records):
        raise typer.Exit(code=1)


def _read_checker_input(path: Path, *, json_output: bool) -> CheckerInput:
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        return CheckerInput.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        _exit_with_error(
            ErrorResult(
                code="invalid_checker_input",
                message=f"invalid checker input JSON: {exc}",
                remediation="Provide a readable checker input JSON object.",
                blocking=True,
                related_path=str(path),
            ),
            json_output=json_output,
        )
    raise AssertionError("unreachable")


def _emit_json(payload: dict[str, Any] | list[Any]) -> None:
    typer.echo(json.dumps(payload, ensure_ascii=True, indent=2))


def _exit_with_error(error: ErrorResult, *, json_output: bool) -> None:
    if json_output:
        typer.echo(error.to_json(), nl=False)
    else:
        Console(width=120, markup=False).print(
            f"{error.code}: {error.message}\n{error.remediation}"
        )
    raise typer.Exit(code=1)
