"""Thin app facade over existing Cosheaf services.

The app layer is intentionally boring: it gives future server, MCP, and UI
callers one import surface without moving policy-heavy service code yet.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal, Self

from cosheaf.agent.context_pack import CONTEXT_MAX_CARDS, ContextPackResult
from cosheaf.agent.orchestrator_state import ReducerResult
from cosheaf.agent.worker_bundle_v2 import WorkerBundleV2
from cosheaf.core.status import ArtifactStatus, ArtifactType
from cosheaf.forge import ForgeActionResult, ForgePreviewResult, ForgeService
from cosheaf.gates.gatekeeper import GatekeeperRunResult, ValidationReport
from cosheaf.gates.promotion_readiness import (
    PromotionReadinessReport,
    build_promotion_readiness_report,
)
from cosheaf.issues import IssueListResult, IssueResult, LocalIssueService
from cosheaf.memory import (
    ArtifactCard,
    ArtifactCardStatus,
    RetrievalResult,
    RetrievalRole,
)
from cosheaf.services import (
    ArtifactWriteResult,
    BundleValidationService,
    ContextPackService,
    ControlledWriteResult,
    DraftWriteService,
    GateService,
    MemorySearchService,
    ReviewRequestFromBundleResult,
    ValidationService,
    WorkspaceInfoResult,
    WorkspaceService,
)
from cosheaf.services.models import (
    DraftArtifactWriteRequest,
    WorkerBundleSubmitRequest,
    WorkerBundleSubmitResult,
)
from cosheaf.site import SiteExportResult, export_site_data
from cosheaf.storage.repo import RepoContext


class CosheafApp:
    """Application facade for existing repository use cases."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context

    @classmethod
    def from_repo_root(cls, repo_root: str | Path = ".") -> Self:
        """Create an app facade from a repository root."""
        return cls(RepoContext(Path(repo_root)))

    def workspace_info(self) -> WorkspaceInfoResult:
        """Return active workspace metadata."""
        return WorkspaceService(self.context).info()

    def validate_repository(self) -> ValidationReport:
        """Validate repository YAML records and invariants."""
        return ValidationService(self.context).validate_repository()

    def validate_artifact_file(self, path: str | Path) -> ValidationReport:
        """Validate one repository-local artifact YAML file."""
        return ValidationService(self.context).validate_artifact_file(path)

    def run_gate(
        self,
        *,
        persist_review: bool = False,
        pr_checklist_path: str | Path | None = None,
        timestamp: str | None = None,
    ) -> GatekeeperRunResult:
        """Run gatekeeper checks and return report metadata."""
        return GateService(self.context).run(
            persist_review=persist_review,
            pr_checklist_path=pr_checklist_path,
            timestamp=timestamp,
        )

    def build_context(
        self,
        issue_id: str,
        *,
        role: RetrievalRole | str = RetrievalRole.ORCHESTRATOR,
        max_cards: int = CONTEXT_MAX_CARDS,
        max_full_artifacts: int | None = None,
        public_only: bool = False,
    ) -> ContextPackResult:
        """Build a deterministic issue-scoped context pack."""
        return ContextPackService(self.context).build(
            issue_id,
            role=role,
            max_cards=max_cards,
            max_full_artifacts=max_full_artifacts,
            public_only=public_only,
        )

    def show_context(
        self,
        issue_id: str,
        *,
        role: RetrievalRole | str = RetrievalRole.ORCHESTRATOR,
        max_cards: int = CONTEXT_MAX_CARDS,
        max_full_artifacts: int | None = None,
        public_only: bool = False,
    ) -> str:
        """Build and return the rendered main context document."""
        return ContextPackService(self.context).show(
            issue_id,
            role=role,
            max_cards=max_cards,
            max_full_artifacts=max_full_artifacts,
            public_only=public_only,
        )

    def create_issue(
        self,
        *,
        issue_id: str,
        title: str,
        summary: str | None = None,
        authors: Sequence[str] = (),
        labels: Sequence[str] = (),
        related_artifacts: Sequence[str] = (),
        related_sources: Sequence[str] = (),
        scope: Literal["private", "public"] = "private",
    ) -> IssueResult:
        """Create an open repository-local issue YAML record."""
        return LocalIssueService(self.context).create(
            issue_id=issue_id,
            title=title,
            summary=summary,
            authors=tuple(authors),
            labels=tuple(labels),
            related_artifacts=tuple(related_artifacts),
            related_sources=tuple(related_sources),
            scope=scope,
        )

    def show_issue(self, issue_id: str) -> IssueResult:
        """Return one repository-local issue record."""
        return LocalIssueService(self.context).show(issue_id)

    def list_issues(self) -> IssueListResult:
        """Return all repository-local issue records."""
        return LocalIssueService(self.context).list()

    def close_issue(self, issue_id: str, *, reason: str) -> IssueResult:
        """Close a repository-local issue without changing artifact state."""
        return LocalIssueService(self.context).close(issue_id, reason=reason)

    def forge_status(self) -> ForgePreviewResult:
        """Preview forge status without token lookup or git mutation."""
        return ForgeService(self.context).status()

    def forge_issue_preview(self, source_path: str | Path) -> ForgePreviewResult:
        """Preview GitHub issue creation from a repository-local issue file."""
        return ForgeService(self.context).issue_preview(source_path)

    def forge_pr_preview(self, *, base: str, head: str) -> ForgePreviewResult:
        """Preview GitHub PR creation without git or GitHub writes."""
        return ForgeService(self.context).pr_preview(base=base, head=head)

    def forge_branch_create(self, branch: str, *, confirm: bool) -> ForgeActionResult:
        """Create and switch to a local branch with explicit confirmation."""
        return ForgeService(self.context).create_branch(branch, confirm=confirm)

    def forge_commit(self, *, message: str, confirm: bool) -> ForgeActionResult:
        """Run validation/gate and create one local git commit."""
        return ForgeService(self.context).commit(message=message, confirm=confirm)

    def forge_github_issue_create(
        self,
        source_path: str | Path,
        *,
        confirm: bool,
    ) -> ForgeActionResult:
        """Create a GitHub issue from a local issue file with confirmation."""
        return ForgeService(self.context).github_issue_create(
            source_path,
            confirm=confirm,
        )

    def forge_github_pr_create(
        self,
        *,
        base: str,
        head: str,
        draft: bool = False,
        confirm: bool,
    ) -> ForgeActionResult:
        """Create a GitHub PR with explicit confirmation."""
        return ForgeService(self.context).github_pr_create(
            base=base,
            head=head,
            draft=draft,
            confirm=confirm,
        )

    def forge_sync(self) -> ForgeActionResult:
        """Return read-only forge sync status."""
        return ForgeService(self.context).sync()

    def export_site_data(
        self,
        out: str | Path,
        *,
        public_only: bool = False,
        demo: bool = False,
    ) -> SiteExportResult:
        """Export deterministic sanitized JSON for the read-only website."""
        return export_site_data(
            self.context,
            out,
            public_only=public_only,
            demo=demo,
        )

    def memory_cards(
        self,
        *,
        issue_id: str | None = None,
        status: ArtifactCardStatus | None = None,
    ) -> tuple[ArtifactCard, ...]:
        """Build compact artifact cards from repository metadata."""
        return MemorySearchService(self.context).cards(
            issue_id=issue_id,
            status=status,
        )

    def memory_search(
        self,
        query: str,
        *,
        issue_id: str | None = None,
        status: ArtifactCardStatus | None = None,
        max_cards: int = CONTEXT_MAX_CARDS,
        seed_artifacts: Sequence[str] = (),
        pinned_artifacts: Sequence[str] = (),
        include_refuted: bool = False,
        include_obsolete: bool = False,
    ) -> RetrievalResult:
        """Search artifact cards with deterministic local scoring."""
        return MemorySearchService(self.context).search(
            query,
            issue_id=issue_id,
            status=status,
            max_cards=max_cards,
            seed_artifacts=seed_artifacts,
            pinned_artifacts=pinned_artifacts,
            include_refuted=include_refuted,
            include_obsolete=include_obsolete,
        )

    def create_artifact(
        self,
        *,
        artifact_id: str,
        artifact_type: ArtifactType,
        title: str,
        domain: Sequence[str],
        status: ArtifactStatus,
        statement: str,
        authors: Sequence[str],
        tags: Sequence[str] = (),
        depends_on: Sequence[str] = (),
        supersedes: Sequence[str] = (),
        created_at: str | None = None,
    ) -> ArtifactWriteResult:
        """Create a deterministic draft/pre-accepted artifact YAML record."""
        return DraftWriteService(self.context).create_artifact(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            title=title,
            domain=domain,
            status=status,
            statement=statement,
            authors=authors,
            tags=tags,
            depends_on=depends_on,
            supersedes=supersedes,
            created_at=created_at,
        )

    def write_draft_artifact(
        self,
        request: DraftArtifactWriteRequest,
        *,
        dry_run: bool = False,
    ) -> ControlledWriteResult:
        """Write or preview a controlled draft artifact request."""
        return DraftWriteService(self.context).write_artifact_request(
            request,
            dry_run=dry_run,
        )

    def write_source_note(
        self,
        request: Mapping[str, Any],
        *,
        dry_run: bool = False,
    ) -> ControlledWriteResult:
        """Write or preview a staged draft source note."""
        return DraftWriteService(self.context).write_source_note(
            request,
            dry_run=dry_run,
        )

    def write_review_request(
        self,
        request: Mapping[str, Any],
        *,
        dry_run: bool = False,
    ) -> ControlledWriteResult:
        """Write or preview a draft informational review request."""
        return DraftWriteService(self.context).write_review_request(
            request,
            dry_run=dry_run,
        )

    def write_review_request_from_bundle(
        self,
        bundle_path: str | Path,
        *,
        dry_run: bool = False,
    ) -> ReviewRequestFromBundleResult:
        """Generate and write or preview a draft request from a worker bundle."""
        return DraftWriteService(self.context).write_review_request_from_bundle(
            bundle_path,
            dry_run=dry_run,
        )

    def validate_bundle(self, bundle_path: str | Path) -> WorkerBundleV2:
        """Load and validate a worker bundle v2 manifest."""
        return BundleValidationService(self.context).validate(bundle_path)

    def reduce_bundle(
        self,
        bundle_path: str | Path,
        *,
        reducer_id: str,
    ) -> ReducerResult:
        """Validate and reduce a worker bundle v2 manifest."""
        return BundleValidationService(self.context).reduce(
            bundle_path,
            reducer_id=reducer_id,
        )

    def submit_bundle(
        self,
        request: WorkerBundleSubmitRequest,
        *,
        dry_run: bool = False,
    ) -> WorkerBundleSubmitResult:
        """Validate a worker bundle for review without promotion."""
        return BundleValidationService(self.context).submit(
            request,
            dry_run=dry_run,
        )

    def promotion_readiness(
        self,
        *,
        artifact_id: str | None = None,
        issue_id: str | None = None,
    ) -> PromotionReadinessReport:
        """Build a read-only promotion-readiness report."""
        return build_promotion_readiness_report(
            self.context,
            artifact_id=artifact_id,
            issue_id=issue_id,
        )


def open_app(repo_root: str | Path = ".") -> CosheafApp:
    """Open a repository through the application facade."""
    return CosheafApp.from_repo_root(repo_root)


__all__ = [
    "CosheafApp",
    "open_app",
]
