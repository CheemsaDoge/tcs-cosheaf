"""Checker registry and execution helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from cosheaf.checkers.models import CheckerInput, CheckerResult, CheckerSpec
from cosheaf.storage.repo import RepoContext


class CheckerRegistryError(ValueError):
    """Raised when checker registry operations fail."""


@dataclass(frozen=True)
class CheckerExecution:
    """Internal checker execution payload including bounded stdout/stderr."""

    result: CheckerResult
    stdout: str = ""
    stderr: str = ""


class CheckerHandler(Protocol):
    """Callable protocol implemented by checker handlers."""

    def __call__(
        self,
        context: RepoContext,
        checker_input: CheckerInput,
        spec: CheckerSpec,
    ) -> CheckerExecution:
        """Run one checker and return an execution payload."""
        ...


class CheckerRegistry:
    """Instance-local registry for checker specs and handlers."""

    def __init__(self) -> None:
        self._specs: dict[str, CheckerSpec] = {}
        self._handlers: dict[str, CheckerHandler] = {}

    def register(self, spec: CheckerSpec, handler: CheckerHandler) -> None:
        """Register one checker spec and handler."""
        checker_id = spec.checker_id
        if checker_id in self._specs:
            raise CheckerRegistryError(f"duplicate checker: {checker_id}")
        self._specs[checker_id] = spec
        self._handlers[checker_id] = handler

    def get(self, checker_id: str) -> CheckerSpec | None:
        """Return a checker spec by ID."""
        return self._specs.get(checker_id)

    def handler(self, checker_id: str) -> CheckerHandler | None:
        """Return a checker handler by ID."""
        return self._handlers.get(checker_id)

    def run(
        self,
        checker_id: str,
        context: RepoContext,
        checker_input: CheckerInput,
    ) -> CheckerExecution:
        """Run one registered checker."""
        spec = self.get(checker_id)
        handler = self.handler(checker_id)
        if spec is None or handler is None:
            raise CheckerRegistryError(f"unknown checker: {checker_id}")
        return handler(context, checker_input, spec)

    @property
    def checker_ids(self) -> tuple[str, ...]:
        """Return registered checker IDs in deterministic order."""
        return tuple(sorted(self._specs))

    @property
    def specs(self) -> tuple[CheckerSpec, ...]:
        """Return checker specs in deterministic ID order."""
        return tuple(self._specs[checker_id] for checker_id in self.checker_ids)
