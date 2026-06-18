from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from typer.testing import CliRunner

from cosheaf.benchmark import (
    BENCHMARK_AUTHORITY_NOTICE,
    BenchmarkSuiteName,
    list_benchmark_suites,
    run_benchmark_suite,
)
from cosheaf.cli import app
from cosheaf.storage.repo import RepoContext

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[1]


def _json(output: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(output))


def test_benchmark_list_exposes_required_suites() -> None:
    result = list_benchmark_suites()

    names = {suite.name.value for suite in result.suites}
    assert {
        "smoke",
        "regression",
        "authority_negative",
        "private_boundary",
        "research_loop",
        "campaign",
        "review_workflow",
    } <= names
    assert result.authority_notice == BENCHMARK_AUTHORITY_NOTICE


def test_benchmark_smoke_run_persists_sidecar_and_separates_skips() -> None:
    run = run_benchmark_suite(RepoContext(REPO_ROOT), BenchmarkSuiteName.SMOKE)

    assert run.passed is True
    assert run.metrics.pass_count > 0
    assert run.metrics.fail_count == 0
    assert run.metrics.skipped_count > 0
    assert run.skipped_rows_are_passes is False
    assert run.accepted_write_performed is False
    assert run.yaml_artifacts_mutated is False
    assert (REPO_ROOT / ".cosheaf/benchmark-runs" / run.run_id / "run.json").is_file()


def test_benchmark_cli_run_list_and_report_smoke() -> None:
    listed = runner.invoke(app, ["benchmark", "list", "--json"])
    assert listed.exit_code == 0, listed.output
    assert "smoke" in {item["name"] for item in _json(listed.output)["suites"]}

    run = runner.invoke(
        app,
        [
            "benchmark",
            "run",
            "--suite",
            "smoke",
            "--repo-root",
            str(REPO_ROOT),
            "--json",
        ],
    )
    assert run.exit_code == 0, run.output
    run_payload = _json(run.output)
    run_id = run_payload["run_id"]
    assert run_payload["suite"] == "smoke"
    assert run_payload["metrics"]["skipped_count"] > 0
    assert run_payload["skipped_rows_are_passes"] is False

    report = runner.invoke(
        app,
        [
            "benchmark",
            "report",
            run_id,
            "--out",
            ".cosheaf/benchmark-test/smoke.md",
            "--repo-root",
            str(REPO_ROOT),
            "--json",
        ],
    )
    assert report.exit_code == 0, report.output
    report_payload = _json(report.output)
    assert report_payload["report_format"] == "markdown"
    report_path = REPO_ROOT / ".cosheaf/benchmark-test/smoke.md"
    assert report_path.is_file()
    assert "Benchmark Run" in report_path.read_text(encoding="utf-8")


def test_benchmark_report_rejects_accepted_output() -> None:
    run = run_benchmark_suite(RepoContext(REPO_ROOT), BenchmarkSuiteName.CAMPAIGN)

    result = runner.invoke(
        app,
        [
            "benchmark",
            "report",
            run.run_id,
            "--out",
            "kb/accepted/reports/benchmark.md",
            "--repo-root",
            str(REPO_ROOT),
            "--json",
        ],
    )

    assert result.exit_code == 1
    assert "accepted KB" in result.output
