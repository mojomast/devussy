"""Factory for creating LLMClient instances from configuration."""

from __future__ import annotations

from typing import Any

from ..llm_client import LLMClient
from .generic_client import GenericOpenAIClient
from .openai_client import OpenAIClient
from .requesty_client import RequestyClient


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
    if provider == "requesty":
        return RequestyClient(config)

    raise ValueError(f"Unsupported LLM provider: {provider}")
