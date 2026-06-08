from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from cosheaf.core.artifact import BaseArtifact
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.lean_external import (
    LeanLibraryRefAdapter,
    LeanLibraryRefBackendResult,
)
from cosheaf.verification.result import VerificationStatus

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class PilotLeanBackend:
    seen_source: str = ""

    @property
    def name(self) -> str:
        return "fake-lean"

    def is_available(self) -> bool:
        return True

    def command(self, lean_path: Path) -> tuple[str, ...]:
        return ("fake-lean", lean_path.as_posix())

    def version(self) -> str:
        return "fake-lean 1.0"

    def check(
        self,
        lean_path: Path,
        *,
        cwd: Path,
        timeout_seconds: float,
    ) -> LeanLibraryRefBackendResult:
        self.seen_source = lean_path.read_text(encoding="utf-8")
        return LeanLibraryRefBackendResult(
            exit_code=0,
            stdout="Nat : Type\n",
            stderr="",
        )


def test_lean_core_formal_link_pilot_generates_optional_check(
    tmp_path: Path,
) -> None:
    data = yaml.safe_load(
        (
            ROOT / "examples" / "claims" / "claim.lean-core-formal-link-pilot.yaml"
        ).read_text(encoding="utf-8")
    )
    artifact = BaseArtifact.model_validate(data)
    backend = PilotLeanBackend()

    result = LeanLibraryRefAdapter(backend=backend).verify(
        artifact,
        RepoContext(tmp_path),
    )

    assert result.status is VerificationStatus.PASS
    assert result.evidence_paths == ("formalization:lean.core.nat",)
    assert result.input_paths == ("formalization:lean.core.nat",)
    assert result.message.endswith("alignment not checked.")
    assert backend.seen_source == "import Init\n#check Nat\n"
    assert artifact.status.value == "draft"
    assert artifact.formalizations[0].status == "linked"
    assert artifact.alignment.status == "requested"
    assert artifact.verification_policy.require_lean_check is False
