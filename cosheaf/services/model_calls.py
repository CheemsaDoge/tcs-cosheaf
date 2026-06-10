"""Service wrapper for provider gateway model calls."""

from __future__ import annotations

from cosheaf.agent.providers import (
    OpenAICompatibleProvider,
    ProviderConfig,
    ProviderError,
    ProviderGateway,
    ProviderGatewayRequest,
)
from cosheaf.services.models import ModelCallResult
from cosheaf.storage.repo import RepoContext


class ModelCallService:
    """Typed service boundary for provider gateway calls."""

    def __init__(self, context: RepoContext) -> None:
        self.gateway = ProviderGateway(context)

    def call(
        self,
        request: ProviderGatewayRequest,
        *,
        config: ProviderConfig | None = None,
        provider: OpenAICompatibleProvider | None = None,
    ) -> ModelCallResult | ProviderError:
        """Call the configured provider gateway."""
        return self.gateway.call(request, config=config, provider=provider)


__all__ = ["ModelCallService"]
