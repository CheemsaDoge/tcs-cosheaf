from typer.testing import CliRunner

import cosheaf
from cosheaf.cli import app


def test_package_exposes_version() -> None:
    assert cosheaf.__version__


def test_cli_help() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "TCS-Cosheaf" in result.output
    assert "version" in result.output


def test_cli_version() -> None:
    result = CliRunner().invoke(app, ["version"])

    assert result.exit_code == 0
    assert cosheaf.__version__ in result.output
