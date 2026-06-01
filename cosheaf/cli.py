from __future__ import annotations

import typer
from rich.console import Console

from cosheaf import __version__

app = typer.Typer(
    add_completion=False,
    help="TCS-Cosheaf research knowledge base harness.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Print the TCS-Cosheaf version."""
    Console().print(f"tcs-cosheaf {__version__}")


@app.command()
def validate() -> None:
    """Report scaffold-only validation status."""
    Console().print(
        "scaffold-only: artifact schema validation is not implemented yet; "
        "no artifacts were checked."
    )


@app.command()
def gate() -> None:
    """Report scaffold-only gate status."""
    Console().print(
        "scaffold-only: gatekeeper is not implemented yet; "
        "no repository gates were enforced."
    )


if __name__ == "__main__":
    app()
