"""Factory for creating LLMClient instances from configuration."""

from __future__ import annotations

from typing import Any

from ..llm_client import LLMClient
from .aether_client import AetherClient
from .generic_client import GenericOpenAIClient
from .openai_client import OpenAIClient
from .requesty_client import RequestyClient
from .agentrouter_client import AgentRouterClient


def create_llm_client(config: Any) -> LLMClient:
    """Instantiate the appropriate LLM client based on configuration.

    Args:
        config: Application configuration with `.llm.provider` and other fields.

    Returns:
        An instance of a concrete `LLMClient`.

    Raises:
        ValueError: If the provider is unknown/unsupported.
    """
    provider = getattr(getattr(config, "llm", None), "provider", "openai").lower()

    if provider == "openai":
        return OpenAIClient(config)
    if provider == "generic":
        return GenericOpenAIClient(config)
    if provider == "aether":
        return AetherClient(config)
    if provider == "agentrouter":
        return AgentRouterClient(config)
    if provider == "requesty":
        return RequestyClient(config)

    raise ValueError(f"Unsupported LLM provider: {provider}")
