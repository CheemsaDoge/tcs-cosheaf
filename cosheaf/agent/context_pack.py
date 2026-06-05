"""Context pack generation for bounded Codex task handoffs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from textwrap import shorten

from cosheaf.core.artifact import BaseArtifact
from cosheaf.core.status import (
    ArtifactStatus,
    is_accepted_status,
    is_preaccepted_status,
)
from cosheaf.storage.loader import IssueRecord, LoadedRecord, load_artifacts
from cosheaf.storage.repo import RepoContext

PACK_FILENAMES = (
    "CONTEXT.md",
    "ACCEPTANCE.md",
    "RELEVANT_ARTIFACTS.md",
    "KNOWN_FAILURES.md",
    "COMMANDS.md",
)

DEFAULT_COMMANDS = (
    "make lint",
    "make typecheck",
    "make test",
    "make validate",
    "make gate",
)

KNOWN_FAILURE_STATUSES = frozenset(
    {
        ArtifactStatus.REFUTED,
        ArtifactStatus.OBSOLETE,
        ArtifactStatus.SUPERSEDED,
    }
)


class ContextPackError(ValueError):
    """Raised when a context pack cannot be generated from repository data."""


@dataclass(frozen=True)
class ContextPackResult:
    """Written context pack files for an issue."""

    issue_id: str
    task_dir: Path
    files: tuple[Path, ...]


@dataclass(frozen=True)
class RankedArtifact:
    """A selected artifact plus deterministic ranking reasons."""

    record: LoadedRecord
    reasons: tuple[str, ...]


def build_context_pack(context: RepoContext, issue_id: str) -> ContextPackResult:
    """Build a deterministic bounded context pack for an issue."""
    records = tuple(load_artifacts(context))
    issue = _find_issue(records, issue_id)
    artifacts = _select_relevant_artifacts(records, issue)
    task_dir = context.resolve(Path("context") / "TASKS" / issue_id)
    task_dir.mkdir(parents=True, exist_ok=True)

    contents = {
        "CONTEXT.md": _render_context(context, issue, artifacts),
        "ACCEPTANCE.md": _render_acceptance(issue),
        "RELEVANT_ARTIFACTS.md": _render_relevant_artifacts(artifacts),
        "KNOWN_FAILURES.md": _render_known_failures(artifacts),
        "COMMANDS.md": _render_commands(),
    }
    files: list[Path] = []
    for filename in PACK_FILENAMES:
        path = task_dir / filename
        path.write_text(contents[filename], encoding="utf-8")
        files.append(path)

    return ContextPackResult(
        issue_id=issue.id,
        task_dir=task_dir,
        files=tuple(files),
    )


def show_context_pack(context: RepoContext, issue_id: str) -> str:
    """Build a context pack if needed and return its main context document."""
    result = build_context_pack(context, issue_id)
    return (result.task_dir / "CONTEXT.md").read_text(encoding="utf-8")


def _find_issue(records: tuple[LoadedRecord, ...], issue_id: str) -> IssueRecord:
    issues = [
        record.record
        for record in records
        if isinstance(record.record, IssueRecord) and record.record.id == issue_id
    ]
    if not issues:
        raise ContextPackError(f"issue not found: {issue_id}")
    return sorted(issues, key=lambda issue: issue.id)[0]


def _select_relevant_artifacts(
    records: tuple[LoadedRecord, ...],
    issue: IssueRecord,
) -> tuple[RankedArtifact, ...]:
    artifact_records = [
        record for record in records if isinstance(record.record, BaseArtifact)
    ]
    artifact_by_id = {record.id: record for record in artifact_records}
    direct_ids = set(issue.related_artifacts)
    dependency_ids: set[str] = set()

    for artifact_id in sorted(issue.related_artifacts):
        record = artifact_by_id.get(artifact_id)
        if isinstance(record, LoadedRecord) and isinstance(record.record, BaseArtifact):
            dependency_ids.update(record.record.depends_on)

    issue_terms = _issue_terms(issue)
    issue_tags = {_normalize_term(tag) for tag in issue.tags}
    selected: list[RankedArtifact] = []

    for record in artifact_records:
        artifact = _as_artifact(record)
        reasons = _relevance_reasons(
            artifact,
            direct_ids=direct_ids,
            dependency_ids=dependency_ids,
            issue_terms=issue_terms,
            issue_tags=issue_tags,
        )
        if reasons:
            selected.append(RankedArtifact(record=record, reasons=reasons))

    return tuple(sorted(selected, key=_artifact_sort_key))


def _relevance_reasons(
    artifact: BaseArtifact,
    *,
    direct_ids: set[str],
    dependency_ids: set[str],
    issue_terms: set[str],
    issue_tags: set[str],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if artifact.id in direct_ids:
        reasons.append("direct reference")
    if artifact.id in dependency_ids:
        reasons.append("dependency neighbor")
    if _artifact_domain_matches_issue(artifact, issue_terms):
        reasons.append("domain match")
    if issue_tags.intersection({_normalize_term(tag) for tag in artifact.tags}):
        reasons.append("tag match")
    return tuple(reasons)


def _artifact_domain_matches_issue(
    artifact: BaseArtifact,
    issue_terms: set[str],
) -> bool:
    for domain in artifact.domain:
        terms = _term_variants(domain)
        if terms.intersection(issue_terms):
            return True
        parts = _term_parts(domain)
        if parts and parts.issubset(issue_terms):
            return True
    return False


def _artifact_sort_key(record: RankedArtifact) -> tuple[int, int, str, str]:
    artifact = _as_artifact(record.record)
    return (
        _reason_priority(record.reasons),
        _status_priority(artifact.status),
        artifact.id,
        record.record.source_path.as_posix(),
    )


def _reason_priority(reasons: tuple[str, ...]) -> int:
    priorities = {
        "direct reference": 0,
        "dependency neighbor": 1,
        "domain match": 2,
        "tag match": 3,
    }
    return min(priorities[reason] for reason in reasons)


def _issue_terms(issue: IssueRecord) -> set[str]:
    terms: set[str] = set()
    for value in (issue.title, issue.description, *issue.tags):
        terms.update(_term_variants(value))
    return terms


def _term_variants(value: str) -> set[str]:
    normalized = _normalize_term(value)
    variants = {normalized}
    variants.update(
        match.group(0)
        for match in re.finditer(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized)
    )
    return {variant for variant in variants if variant}


def _term_parts(value: str) -> set[str]:
    normalized = _normalize_term(value)
    return set(re.findall(r"[a-z0-9]+", normalized))


def _normalize_term(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def _status_priority(status: ArtifactStatus) -> int:
    if is_accepted_status(status):
        return 0
    if is_preaccepted_status(status):
        return 1
    if status in KNOWN_FAILURE_STATUSES:
        return 2
    return 3


def _render_context(
    context: RepoContext,
    issue: IssueRecord,
    artifacts: tuple[RankedArtifact, ...],
) -> str:
    accepted = [
        record
        for record in artifacts
        if is_accepted_status(_as_artifact(record.record).status)
    ]
    drafts = [
        record
        for record in artifacts
        if is_preaccepted_status(_as_artifact(record.record).status)
    ]
    known_failures = [
        record
        for record in artifacts
        if _as_artifact(record.record).status in KNOWN_FAILURE_STATUSES
    ]

    lines = [
        f"# Context Pack: {issue.id}",
        "",
        "## Issue Summary",
        "",
        f"- Title: {issue.title}",
        f"- Status: {issue.status}",
        f"- Severity: {issue.severity}",
        f"- Source: {_issue_source_path(context, issue.id)}",
        f"- Summary: {_one_line(issue.description)}",
        "",
        "## Relevant Accepted Artifacts",
        "",
    ]
    lines.extend(_artifact_lines(accepted))
    lines.extend(["", "## Relevant Draft Artifacts", ""])
    lines.extend(_artifact_lines(drafts))
    lines.extend(["", "## Relevant Known Failures", ""])
    lines.extend(_artifact_lines(known_failures))
    lines.extend(
        [
            "",
            "## Current Project State",
            "",
            _read_markdown_excerpt(context.resolve("context/PROJECT_STATE.md")),
            "",
            "## Relevant Interfaces",
            "",
            _read_markdown_excerpt(
                context.resolve("context/INTERFACE_REGISTRY.md"),
                keywords=("context", "RepoContext", "load_artifacts", "IssueRecord"),
            ),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _render_acceptance(issue: IssueRecord) -> str:
    task_criteria = _extract_acceptance_criteria(issue.description)
    lines = [
        f"# Acceptance: {issue.id}",
        "",
        "## Task-Specific Acceptance Criteria",
        "",
    ]
    if task_criteria:
        lines.extend(f"- {criterion}" for criterion in task_criteria)
    else:
        lines.append(
            "- No task-specific acceptance criteria recorded in the issue file."
        )

    lines.extend(
        [
            "",
            "## Default Engineering Acceptance Criteria",
            "",
            "- New behavior includes tests.",
            "- Public interface changes update `context/INTERFACE_REGISTRY.md`.",
            "- Workflow or behavior changes update relevant docs.",
            "- Verification failures are reported, not hidden.",
            "- Generated outputs are deterministic.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_relevant_artifacts(artifacts: tuple[RankedArtifact, ...]) -> str:
    lines = ["# Relevant Artifacts", ""]
    if artifacts:
        lines.extend(_artifact_reference_line(record) for record in artifacts)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def _render_known_failures(artifacts: tuple[RankedArtifact, ...]) -> str:
    known_failures = [
        record
        for record in artifacts
        if _as_artifact(record.record).status in KNOWN_FAILURE_STATUSES
    ]
    lines = ["# Known Failures", ""]
    if known_failures:
        lines.extend(_artifact_reference_line(record) for record in known_failures)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def _render_commands() -> str:
    lines = ["# Commands", "", "Run these commands before handoff:", ""]
    lines.extend(f"- `{command}`" for command in DEFAULT_COMMANDS)
    return "\n".join(lines) + "\n"


def _artifact_lines(
    records: list[RankedArtifact],
) -> list[str]:
    if not records:
        return ["- None"]
    lines = []
    for record in records:
        lines.extend(_artifact_reference_lines(record))
    return lines


def _artifact_reference_line(record: RankedArtifact) -> str:
    return "\n".join(_artifact_reference_lines(record))


def _artifact_reference_lines(record: RankedArtifact) -> list[str]:
    artifact = _as_artifact(record.record)
    prefix = _status_prefix(artifact.status)
    lines = [
        f"- {prefix}{artifact.id} | {artifact.title} | "
        f"{artifact.status.value} | {record.record.source_path.as_posix()} | "
        f"reasons: {_format_reasons(record.reasons)}"
    ]
    lines.extend(_formal_metadata_lines(artifact))
    return lines


def _formal_metadata_lines(artifact: BaseArtifact) -> list[str]:
    if not _has_formal_metadata(artifact):
        return []

    lines: list[str] = []
    if artifact.formalizations:
        lines.append("  - Formal links:")
        for ref in sorted(artifact.formalizations, key=lambda item: item.id):
            lines.append(
                f"    - {ref.library}@{ref.library_ref}:"
                f"{ref.import_path}#{ref.symbol} "
                f"[{ref.declaration_kind}, {ref.status}, {ref.check_mode}]"
            )
    else:
        lines.append("  - Formal links: none")

    reviewer = artifact.alignment.reviewer or "-"
    policy = artifact.verification_policy
    lines.extend(
        [
            f"  - Alignment: {artifact.alignment.status}; reviewer={reviewer}",
            "  - Verification policy: "
            f"{policy.level}; formal_link={_bool_text(policy.require_formal_link)}; "
            f"lean_check={_bool_text(policy.require_lean_check)}; "
            f"alignment_review={_bool_text(policy.require_alignment_review)}",
            f"  - G10-relevant: yes; {'; '.join(_formal_hints(artifact))}",
        ]
    )
    return lines


def _has_formal_metadata(artifact: BaseArtifact) -> bool:
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


def _formal_hints(artifact: BaseArtifact) -> list[str]:
    hints: list[str] = []
    policy = artifact.verification_policy
    if policy.require_formal_link:
        hints.append("requires formal link")
    if policy.require_lean_check:
        hints.append("requires Lean check")
    if policy.require_alignment_review:
        hints.append("requires alignment review")
    if artifact.alignment.status == "rejected":
        hints.append("alignment rejected")
    if any(ref.status == "planned" for ref in artifact.formalizations):
        hints.append("planned formalization")
    if any(ref.status == "broken" for ref in artifact.formalizations):
        hints.append("broken formalization")
    if any(ref.status == "deprecated" for ref in artifact.formalizations):
        hints.append("deprecated formalization")
    return hints or ["metadata present"]


def _bool_text(value: bool) -> str:
    return str(value).lower()


def _status_prefix(status: ArtifactStatus) -> str:
    if is_preaccepted_status(status):
        return "[DRAFT] "
    if status in KNOWN_FAILURE_STATUSES:
        return f"[{status.value.upper()}] "
    return ""


def _format_reasons(reasons: tuple[str, ...]) -> str:
    return ", ".join(reasons)


def _as_artifact(record: LoadedRecord) -> BaseArtifact:
    if not isinstance(record.record, BaseArtifact):
        raise TypeError(f"loaded record is not an artifact: {record.id}")
    return record.record


def _extract_acceptance_criteria(description: str) -> list[str]:
    criteria: list[str] = []
    for raw_line in description.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- [ ] "):
            criteria.append(line.removeprefix("- [ ] ").strip())
        elif line.startswith("- "):
            criteria.append(line.removeprefix("- ").strip())
        elif line.startswith("* "):
            criteria.append(line.removeprefix("* ").strip())
        elif _starts_numbered_item(line):
            criteria.append(line.split(".", 1)[1].strip())
    return criteria


def _starts_numbered_item(line: str) -> bool:
    prefix, separator, rest = line.partition(".")
    return bool(separator and rest.strip() and prefix.isdecimal())


def _read_markdown_excerpt(
    path: Path,
    *,
    keywords: tuple[str, ...] = (),
    max_lines: int = 18,
    max_chars: int = 1600,
) -> str:
    if not path.exists():
        return f"{path.name} is not available."

    lines = path.read_text(encoding="utf-8").splitlines()
    selected = _select_excerpt_lines(lines, keywords=keywords, max_lines=max_lines)
    excerpt = "\n".join(selected).strip()
    if len(excerpt) > max_chars:
        return excerpt[: max_chars - 4].rstrip() + "\n..."
    return excerpt or "No excerpt available."


def _select_excerpt_lines(
    lines: list[str],
    *,
    keywords: tuple[str, ...],
    max_lines: int,
) -> list[str]:
    if not keywords:
        return lines[:max_lines]

    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    selected = [
        line
        for line in lines
        if any(keyword in line.lower() for keyword in lowered_keywords)
    ]
    if selected:
        return selected[:max_lines]
    return lines[:max_lines]


def _one_line(value: str) -> str:
    return shorten(" ".join(value.split()), width=240, placeholder="...")


def _issue_source_path(context: RepoContext, issue_id: str) -> str:
    for record in load_artifacts(context):
        if isinstance(record.record, IssueRecord) and record.record.id == issue_id:
            return record.source_path.as_posix()
    return "-"
