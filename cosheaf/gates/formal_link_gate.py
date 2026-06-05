"""Static formal-link metadata policy gate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cosheaf.core.artifact import BaseArtifact
from cosheaf.core.status import ArtifactStatus
from cosheaf.gates.schema_gate import ValidationFailure, sort_failures
from cosheaf.storage.loader import LoadedRecord

CheckStatus = Literal["pass", "fail", "warning", "not_applicable"]

ACTIVE_FORMALIZATION_STATUSES = frozenset({"planned", "linked", "checked"})


@dataclass(frozen=True)
class FormalLinkCheck:
    """One artifact formal-link metadata check row."""

    artifact_id: str
    source_path: str
    artifact_status: str
    policy_level: str
    require_formal_link: bool
    require_lean_check: bool
    require_alignment_review: bool
    formalization_count: int
    checked_formalization_count: int
    alignment_status: str
    status: CheckStatus
    blocking_messages: tuple[str, ...] = ()
    warning_messages: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "source_path": self.source_path,
            "artifact_status": self.artifact_status,
            "policy_level": self.policy_level,
            "require_formal_link": self.require_formal_link,
            "require_lean_check": self.require_lean_check,
            "require_alignment_review": self.require_alignment_review,
            "formalization_count": self.formalization_count,
            "checked_formalization_count": self.checked_formalization_count,
            "alignment_status": self.alignment_status,
            "status": self.status,
            "blocking_messages": list(self.blocking_messages),
            "warning_messages": list(self.warning_messages),
        }


@dataclass(frozen=True)
class FormalLinkResult:
    """Aggregate result for the static formal-link metadata gate."""

    checks: tuple[FormalLinkCheck, ...]
    failures: tuple[ValidationFailure, ...]
    warnings: tuple[ValidationFailure, ...]

    @property
    def applicable_count(self) -> int:
        return sum(1 for check in self.checks if check.status != "not_applicable")

    @property
    def ok(self) -> bool:
        return not self.failures


def validate_formal_link_policy(
    records: tuple[LoadedRecord, ...],
) -> FormalLinkResult:
    """Validate static consistency of formal-link metadata."""
    checks: list[FormalLinkCheck] = []
    failures: list[ValidationFailure] = []
    warnings: list[ValidationFailure] = []

    for loaded in sorted(records, key=_record_sort_key):
        artifact = loaded.record
        if not isinstance(artifact, BaseArtifact):
            continue

        check = _check_artifact(loaded, artifact)
        checks.append(check)
        failures.extend(
            _failures_from_messages(check, check.blocking_messages)
        )
        warnings.extend(_failures_from_messages(check, check.warning_messages))

    return FormalLinkResult(
        checks=tuple(sorted(checks, key=_check_sort_key)),
        failures=sort_failures(failures),
        warnings=sort_failures(warnings),
    )


def _check_artifact(
    loaded: LoadedRecord,
    artifact: BaseArtifact,
) -> FormalLinkCheck:
    blocking: list[str] = []
    warnings: list[str] = []
    policy = artifact.verification_policy
    alignment = artifact.alignment
    formalizations = artifact.formalizations
    checked_count = sum(1 for ref in formalizations if ref.status == "checked")
    active_count = sum(
        1 for ref in formalizations if ref.status in ACTIVE_FORMALIZATION_STATUSES
    )

    if policy.require_formal_link and not formalizations:
        blocking.append(
            "verification_policy requires a formal link but has no formalizations"
        )

    if policy.require_alignment_review and alignment.status != "human_reviewed":
        blocking.append(
            "verification_policy requires alignment review but "
            f"alignment.status is {alignment.status}"
        )

    if policy.require_lean_check and checked_count == 0:
        blocking.append(
            "verification_policy requires a Lean check but no formalization is checked"
        )

    if policy.level == "lean_required" and not policy.require_formal_link:
        blocking.append("lean_required policy must require a formal link")

    if policy.level == "lean_required" and not policy.require_lean_check:
        blocking.append("lean_required policy must require a Lean check")

    if artifact.status is ArtifactStatus.ACCEPTED and alignment.status == "rejected":
        blocking.append("accepted artifact has rejected formal alignment")

    if artifact.status is ArtifactStatus.ACCEPTED and alignment.status == "requested":
        warnings.append("accepted artifact has requested formal alignment review")

    if formalizations and _formal_link_is_not_required(artifact):
        warnings.append(
            "formalizations are present but verification_policy does not "
            "require a formal link"
        )

    for ref in sorted(formalizations, key=lambda item: item.id):
        if ref.status == "checked" and ref.check_mode == "external_library_ref":
            warnings.append(
                f"formalization {ref.id} is checked through external_library_ref "
                "without verifier evidence linkage"
            )
        if artifact.status is ArtifactStatus.ACCEPTED and ref.status == "planned":
            warnings.append("accepted artifact has a planned formalization")
        if ref.status in {"broken", "deprecated"}:
            message = f"formalization {ref.id} has status {ref.status}"
            if policy.require_formal_link and active_count == 0:
                blocking.append(message)
            else:
                warnings.append(message)

    status: CheckStatus
    if blocking:
        status = "fail"
    elif warnings:
        status = "warning"
    elif _is_applicable(artifact):
        status = "pass"
    else:
        status = "not_applicable"

    return FormalLinkCheck(
        artifact_id=artifact.id,
        source_path=loaded.source_path.as_posix(),
        artifact_status=artifact.status.value,
        policy_level=policy.level,
        require_formal_link=policy.require_formal_link,
        require_lean_check=policy.require_lean_check,
        require_alignment_review=policy.require_alignment_review,
        formalization_count=len(formalizations),
        checked_formalization_count=checked_count,
        alignment_status=alignment.status,
        status=status,
        blocking_messages=tuple(sorted(dict.fromkeys(blocking))),
        warning_messages=tuple(sorted(dict.fromkeys(warnings))),
    )


def _formal_link_is_not_required(artifact: BaseArtifact) -> bool:
    policy = artifact.verification_policy
    return policy.level == "source_reviewed" and not policy.require_formal_link


def _is_applicable(artifact: BaseArtifact) -> bool:
    policy = artifact.verification_policy
    return any(
        (
            artifact.formalizations,
            artifact.alignment.status != "none",
            policy.level != "source_reviewed",
            policy.require_formal_link,
            policy.require_lean_check,
            policy.require_alignment_review,
        )
    )


def _failures_from_messages(
    check: FormalLinkCheck,
    messages: tuple[str, ...],
) -> tuple[ValidationFailure, ...]:
    return tuple(
        ValidationFailure(
            gate="formal link",
            source_path=check.source_path,
            artifact_id=check.artifact_id,
            message=message,
        )
        for message in messages
    )


def _record_sort_key(record: LoadedRecord) -> tuple[str, str]:
    return (record.source_path.as_posix(), record.id)


def _check_sort_key(check: FormalLinkCheck) -> tuple[str, str]:
    return (check.source_path, check.artifact_id)
