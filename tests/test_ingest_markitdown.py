from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.ingest.markitdown_adapter import (
    IngestError,
    MarkItDownIngestAdapter,
    MarkItDownIngestResult,
)
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


@dataclass(frozen=True)
class FakeMarkItDownBackend:
    available: bool = True
    markdown: str = "# Converted\n\nBody text.\n"
    version_value: str | None = "fake-markitdown 1.0"

    @property
    def name(self) -> str:
        return "fake-markitdown"

    def is_available(self) -> bool:
        return self.available

    def version(self) -> str | None:
        return self.version_value

    def convert(self, source_path: Path) -> tuple[str, tuple[str, ...]]:
        return self.markdown, ()


def _write_source(
    repo_root: Path,
    relative_path: str = "sources/raw/paper.txt",
) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("source text\n", encoding="utf-8")
    return path


def test_adapter_reports_unavailable_without_writing_outputs(tmp_path: Path) -> None:
    source = _write_source(tmp_path)
    adapter = MarkItDownIngestAdapter(
        backend=FakeMarkItDownBackend(available=False),
    )

    result = adapter.convert(
        RepoContext(tmp_path),
        source,
        out_dir=Path("sources/markdown"),
        generated_at="2026-06-07T00:00:00Z",
    )

    assert isinstance(result, MarkItDownIngestResult)
    assert result.status == "unavailable"
    assert result.output_path is None
    assert result.metadata_path is None
    assert "pip install markitdown" in result.message
    assert not (tmp_path / "sources" / "markdown").exists()


def test_adapter_converts_local_file_with_provenance_metadata(
    tmp_path: Path,
) -> None:
    source = _write_source(tmp_path)
    adapter = MarkItDownIngestAdapter(backend=FakeMarkItDownBackend())

    result = adapter.convert(
        RepoContext(tmp_path),
        source,
        out_dir=Path("sources/markdown"),
        generated_at="2026-06-07T00:00:00Z",
    )

    assert result.status == "converted"
    assert result.input_path == "sources/raw/paper.txt"
    assert result.output_path == "sources/markdown/paper.md"
    assert result.metadata_path == "sources/markdown/paper.metadata.json"
    assert result.input_sha256
    assert result.options == {
        "allow_remote_urls": False,
        "allow_plugins": False,
        "allow_ocr": False,
        "allow_llm_vision": False,
        "allow_azure_document_intelligence": False,
    }

    output_path = tmp_path / result.output_path
    metadata_path = tmp_path / result.metadata_path
    assert output_path.read_text(encoding="utf-8") == "# Converted\n\nBody text.\n"

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["status"] == "converted"
    assert metadata["input_path"] == "sources/raw/paper.txt"
    assert metadata["input_sha256"] == result.input_sha256
    assert metadata["converter_name"] == "fake-markitdown"
    assert metadata["converter_version"] == "fake-markitdown 1.0"
    assert metadata["generated_at"] == "2026-06-07T00:00:00Z"
    assert metadata["output_path"] == "sources/markdown/paper.md"
    assert metadata["metadata_path"] == "sources/markdown/paper.metadata.json"
    assert metadata["options"] == result.options
    assert metadata["warnings"] == []


def test_adapter_rejects_source_path_outside_repository(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-source.txt"
    outside.write_text("private text\n", encoding="utf-8")
    adapter = MarkItDownIngestAdapter(backend=FakeMarkItDownBackend())

    with pytest.raises(IngestError, match="source path must stay inside repository"):
        adapter.convert(
            RepoContext(tmp_path),
            outside,
            out_dir=Path("sources/markdown"),
        )


def test_adapter_rejects_remote_source_urls(tmp_path: Path) -> None:
    adapter = MarkItDownIngestAdapter(backend=FakeMarkItDownBackend())

    with pytest.raises(IngestError, match="remote URL inputs"):
        adapter.convert(
            RepoContext(tmp_path),
            "https://example.invalid/paper.pdf",
            out_dir=Path("sources/markdown"),
        )

    assert not (tmp_path / "sources" / "markdown").exists()


def test_adapter_rejects_accepted_kb_output_paths(tmp_path: Path) -> None:
    source = _write_source(tmp_path)
    adapter = MarkItDownIngestAdapter(backend=FakeMarkItDownBackend())

    with pytest.raises(IngestError, match="accepted KB paths"):
        adapter.convert(
            RepoContext(tmp_path),
            source,
            out_dir=Path("kb/accepted/sources"),
        )

    assert not (tmp_path / "kb" / "accepted").exists()


def test_cli_convert_metadata_json_uses_default_runtime_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_source(tmp_path, "sources/raw/note.txt")

    import cosheaf.ingest.markitdown_adapter as adapter_module

    monkeypatch.setattr(
        adapter_module,
        "MarkItDownBackend",
        lambda: FakeMarkItDownBackend(markdown="converted note\n"),
    )

    result = runner.invoke(
        app,
        [
            "ingest",
            "convert",
            "sources/raw/note.txt",
            "--repo-root",
            str(tmp_path),
            "--metadata-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "converted"
    assert payload["input_path"] == "sources/raw/note.txt"
    assert payload["output_path"] == ".cosheaf/ingest/note.md"
    assert payload["metadata_path"] == ".cosheaf/ingest/note.metadata.json"
    assert (tmp_path / ".cosheaf" / "ingest" / "note.md").read_text(
        encoding="utf-8"
    ) == "converted note\n"


def test_cli_convert_missing_dependency_exits_cleanly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_source(tmp_path, "sources/raw/note.txt")

    import cosheaf.ingest.markitdown_adapter as adapter_module

    monkeypatch.setattr(
        adapter_module,
        "MarkItDownBackend",
        lambda: FakeMarkItDownBackend(available=False),
    )

    result = runner.invoke(
        app,
        [
            "ingest",
            "convert",
            "sources/raw/note.txt",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "MarkItDown unavailable" in result.output
    assert "pip install markitdown" in result.output
    assert not (tmp_path / ".cosheaf" / "ingest").exists()


def test_cli_convert_rejects_accepted_output_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_source(tmp_path, "sources/raw/note.txt")

    import cosheaf.ingest.markitdown_adapter as adapter_module

    monkeypatch.setattr(adapter_module, "MarkItDownBackend", FakeMarkItDownBackend)

    result = runner.invoke(
        app,
        [
            "ingest",
            "convert",
            "sources/raw/note.txt",
            "--out",
            "kb/public/accepted/ingest",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "accepted KB paths" in result.output
    assert not (tmp_path / "kb" / "public" / "accepted").exists()
