"""CLI commands for deterministic website export."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from cosheaf.app import open_app
from cosheaf.site.export import SiteExportError

site_app = typer.Typer(
    add_completion=False,
    help="Static website export commands.",
    no_args_is_help=True,
)


@site_app.command("export")
def site_export(
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output directory for deterministic site JSON files.",
    ),
    public_only: bool = typer.Option(
        False,
        "--public-only",
        help="Exclude private KB roots and private-scope issues.",
    ),
    demo: bool = typer.Option(
        False,
        "--demo",
        help="Force public-safe demo export mode.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Export sanitized deterministic JSON for the read-only website."""
    console = Console(width=120, markup=False)
    try:
        result = open_app(repo_root).export_site_data(
            out,
            public_only=public_only,
            demo=demo,
        )
    except SiteExportError as exc:
        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "schema_version": 1,
                        "code": "site_export_failed",
                        "message": str(exc),
                        "remediation": "Fix repository records and retry the export.",
                        "blocking": True,
                    },
                    ensure_ascii=True,
                    indent=2,
                    sort_keys=True,
                )
            )
            raise typer.Exit(code=1) from None
        console.print(f"site_export_failed: {exc}")
        raise typer.Exit(code=1) from None

    if json_output:
        typer.echo(
            json.dumps(
                result.to_dict(),
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            )
        )
        return

    console.print(f"Site export written: {result.out}")
    console.print(f"- files: {result.file_count}")
    console.print(f"- public_only: {str(result.public_only).lower()}")
    console.print(f"- demo: {str(result.demo).lower()}")
    console.print(f"- authority: {result.authority_notice}")
