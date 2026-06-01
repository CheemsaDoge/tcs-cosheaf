"""Verifier adapter registry."""

from __future__ import annotations

from cosheaf.verification.base import VerifierAdapter


class VerifierRegistryError(ValueError):
    """Raised when verifier adapter registration fails."""


class VerifierRegistry:
    """Instance-local registry for verifier adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, VerifierAdapter] = {}

    def register(self, adapter: VerifierAdapter) -> None:
        """Register a verifier adapter by name."""
        name = adapter.name.strip()
        if not name:
            raise VerifierRegistryError("verifier adapter name must not be empty")
        if name in self._adapters:
            raise VerifierRegistryError(f"duplicate verifier adapter: {name}")
        self._adapters[name] = adapter

    def get(self, name: str) -> VerifierAdapter | None:
        """Return a registered adapter by name."""
        return self._adapters.get(name)

    @property
    def names(self) -> tuple[str, ...]:
        """Return registered adapter names in deterministic order."""
        return tuple(sorted(self._adapters))

    @property
    def adapters(self) -> tuple[VerifierAdapter, ...]:
        """Return registered adapters in deterministic name order."""
        return tuple(self._adapters[name] for name in self.names)
