"""Optional MarkItDown source-ingestion adapter.

This adapter stages converted source material only. It does not write artifact
YAML, review records, verifier results, or accepted knowledge.
"""

from __future__ import annotations

import hashlib
import importlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath
from typing import Any, Literal, Protocol

from cosheaf.core.paths import normalize_repo_path
from cosheaf.storage.repo import RepoContext

IngestStatus = Literal["converted", "unavailable"]

DEFAULT_INGEST_OPTIONS: dict[str, bool] = {
    "allow_remote_urls": False,
    "allow_plugins": False,
    "allow_ocr": False,
    "allow_llm_vision": False,
    "allow_azure_document_intelligence": False,
}


class IngestError(ValueError):
    """Raised for expected source-ingestion failures."""


class MarkItDownBackendProtocol(Protocol):
    """Small backend protocol for MarkItDown-like converters."""

    @property
    def name(self) -> str:
        """Return stable backend name metadata."""
        ...

    def is_available(self) -> bool:
        """Return whether the backend can currently convert files."""
        ...

    def version(self) -> str | None:
        """Return backend version metadata when available."""
        ...

    def convert(self, source_path: Path) -> tuple[str, tuple[str, ...]]:
        """Convert a local source file to Markdown and warnings."""
        ...


@dataclass(frozen=True)
class MarkItDownIngestResult:
    """Result and provenance metadata for one source-ingestion conversion."""

    status: IngestStatus
    input_path: str
    input_sha256: str | None
    converter_name: str
    converter_version: str | None
    generated_at: str
    output_path: str | None
    metadata_path: str | None
    options: dict[str, bool] = field(
        default_factory=lambda: dict(DEFAULT_INGEST_OPTIONS)
    )
    warnings: tuple[str, ...] = ()
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-serializable metadata."""
        return {
            "status": self.status,
            "input_path": self.input_path,
            "input_sha256": self.input_sha256,
            "converter_name": self.converter_name,
            "converter_version": self.converter_version,
            "generated_at": self.generated_at,
            "output_path": self.output_path,
            "metadata_path": self.metadata_path,
            "options": dict(self.options),
            "warnings": list(self.warnings),
            "message": self.message,
        }

    def to_json(self) -> str:
        """Return deterministic JSON metadata."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class MarkItDownBackend:
    """Backend wrapper that imports optional MarkItDown only when needed."""

    name = "markitdown"

    def __init__(self) -> None:
        self._module: Any | None = None

    def is_available(self) -> bool:
        """Return whether the optional MarkItDown package is importable."""
        return self._load_module() is not None

    def version(self) -> str | None:
        """Return MarkItDown package version metadata when available."""
        module = self._load_module()
        if module is None:
            return None
        version = getattr(module, "__version__", None)
        return str(version) if version else None

    def convert(self, source_path: Path) -> tuple[str, tuple[str, ...]]:
        """Convert a local source file with the optional MarkItDown package."""
        module = self._load_module()
        if module is None:
            raise IngestError(_install_message())
        converter_cls = getattr(module, "MarkItDown", None)
        if converter_cls is None:
            raise IngestError("MarkItDown package does not expose MarkItDown")

        converter = converter_cls()
        converted = converter.convert(str(source_path))
        markdown = _extract_markdown_text(converted)
        return markdown, ()

    def _load_module(self) -> Any | None:
        if self._module is not None:
            return self._module
        try:
            self._module = importlib.import_module("markitdown")
        except ImportError:
            return None
        return self._module


class MarkItDownIngestAdapter:
    """Convert repository-local source files into staged Markdown."""

    def __init__(
        self,
        *,
        backend: MarkItDownBackendProtocol | None = None,
    ) -> None:
        self.backend = backend or MarkItDownBackend()

    def convert(
        self,
        context: RepoContext,
        source_path: str | Path,
        *,
        out_dir: str | Path = Path(".cosheaf/ingest"),
        generated_at: str | None = None,
    ) -> MarkItDownIngestResult:
        """Convert one source file into staged Markdown and metadata."""
        source = _resolve_repo_local_file(
            context,
            source_path,
            label="source path",
        )
        relative_source = _repo_relative(context, source)
        output_dir = _resolve_output_dir(context, out_dir)

        options = dict(DEFAULT_INGEST_OPTIONS)
        timestamp = generated_at or _utc_now()
        converter_version = self.backend.version()
        input_sha256 = _sha256_file(source)

        if not self.backend.is_available():
            return MarkItDownIngestResult(
                status="unavailable",
                input_path=relative_source,
                input_sha256=input_sha256,
                converter_name=self.backend.name,
                converter_version=converter_version,
                generated_at=timestamp,
                output_path=None,
                metadata_path=None,
                options=options,
                warnings=(),
                message=f"MarkItDown unavailable: {_install_message()}",
            )

        markdown, warnings = self.backend.convert(source)
        output_path = output_dir / f"{source.stem}.md"
        metadata_path = output_dir / f"{source.stem}.metadata.json"
        relative_output = _repo_relative(context, output_path)
        relative_metadata = _repo_relative(context, metadata_path)

        result = MarkItDownIngestResult(
            status="converted",
            input_path=relative_source,
            input_sha256=input_sha256,
            converter_name=self.backend.name,
            converter_version=converter_version,
            generated_at=timestamp,
            output_path=relative_output,
            metadata_path=relative_metadata,
            options=options,
            warnings=tuple(warnings),
            message="Converted source material for staging only.",
        )

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8", newline="\n")
        metadata_path.write_text(result.to_json(), encoding="utf-8", newline="\n")
        return result


def _resolve_repo_local_file(
    context: RepoContext,
    path: str | Path,
    *,
    label: str,
) -> Path:
    if _looks_like_remote(path):
        raise IngestError("remote URL inputs are disabled by default")
    raw_path = Path(path)
    resolved = (
        raw_path.resolve() if raw_path.is_absolute() else context.resolve(raw_path)
    )
    try:
        resolved.relative_to(context.repo_root)
    except ValueError:
        raise IngestError(f"{label} must stay inside repository") from None
    if not resolved.is_file():
        raise IngestError(f"{label} is not a file: {_display_path(path)}")
    return resolved


def _resolve_output_dir(context: RepoContext, out_dir: str | Path) -> Path:
    if _looks_like_remote(out_dir):
        raise IngestError("remote URL output paths are disabled by default")
    raw_path = Path(out_dir)
    resolved = (
        raw_path.resolve() if raw_path.is_absolute() else context.resolve(raw_path)
    )
    try:
        relative = resolved.relative_to(context.repo_root)
    except ValueError:
        raise IngestError("output directory must stay inside repository") from None
    normalized = normalize_repo_path(relative)
    if _is_accepted_kb_path(normalized):
        raise IngestError("source ingestion cannot write accepted KB paths")
    return resolved


def _is_accepted_kb_path(path: str) -> bool:
    parts = PureWindowsPath(path).as_posix().split("/")
    return "kb" in parts and "accepted" in parts[parts.index("kb") + 1 :]


def _looks_like_remote(path: str | Path) -> bool:
    text = str(path).strip().lower()
    return text.startswith("http://") or text.startswith("https://")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_relative(context: RepoContext, path: Path) -> str:
    return path.relative_to(context.repo_root).as_posix()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )


def _extract_markdown_text(converted: Any) -> str:
    if isinstance(converted, str):
        return converted
    for attr in ("text_content", "markdown", "content"):
        value = getattr(converted, attr, None)
        if isinstance(value, str):
            return value
    if isinstance(converted, Mapping):
        for key in ("text_content", "markdown", "content"):
            value = converted.get(key)
            if isinstance(value, str):
                return value
    raise IngestError("MarkItDown conversion did not return Markdown text")


def _install_message() -> str:
    return "install optional source ingestion support with `pip install markitdown`"


def _display_path(path: str | Path) -> str:
    if isinstance(path, PureWindowsPath):
        return path.as_posix()
    return str(path)
