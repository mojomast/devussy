# Adding New LLM Providers

This guide explains how to add support for new LLM providers to DevPlan Orchestrator.

## Overview

DevPlan Orchestrator uses a **provider-agnostic architecture** with a factory pattern that makes it easy to add new LLM providers. All providers implement the same `LLMClient` abstract interface, ensuring consistent behavior across the system.

## Architecture

```
src/clients/
├── __init__.py           # Exports all client classes
├── factory.py            # create_llm_client() factory function
├── generic_client.py     # Base for OpenAI-compatible APIs
├── openai_client.py      # OpenAI-specific client
└── requesty_client.py    # Requesty-specific client
```

## Step-by-Step Guide

### 1. Create a New Client Class

Create a new file `src/clients/your_provider_client.py`:

```python
"""Client for YourProvider LLM API."""

import logging
from typing import AsyncIterator, Dict, List, Optional

from src.llm_client import LLMClient
from src.models import Message

logger = logging.getLogger(__name__)


class YourProviderClient(LLMClient):
    """LLM client for YourProvider API.
    
    Implements the LLMClient interface for YourProvider's API.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "your-default-model",
        base_url: Optional[str] = None,
        timeout: int = 60,
    ):
        """Initialize YourProvider client.
        
        Args:
            api_key: API key for authentication
            model: Model identifier to use
            base_url: Optional custom API endpoint
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.yourprovider.com/v1"
        self.timeout = timeout
        logger.info(f"Initialized YourProviderClient with model {model}")

    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> str:
        """Generate completion from messages.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Generated text completion
            
        Raises:
            Exception: If API request fails
        """
        if stream:
            # For streaming, collect all chunks
            chunks = []
            async for chunk in self.generate_stream(messages, temperature, max_tokens):
                chunks.append(chunk)
            return "".join(chunks)
        
        # Implement your non-streaming API call here
        # This is provider-specific
        try:
            # Example structure (adapt to your provider):
            # response = await your_api_call(
            #     messages=[{"role": m.role, "content": m.content} for m in messages],
            #     temperature=temperature,
            #     max_tokens=max_tokens,
            # )
            # return response["choices"][0]["message"]["content"]
            
            raise NotImplementedError(
                "Implement your provider's API call here"
            )
        except Exception as e:
            logger.error(f"YourProvider API error: {e}")
            raise

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Generate streaming completion from messages.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            
        Yields:
            Text chunks as they arrive
            
        Raises:
            Exception: If API request fails
        """
        # Implement your streaming API call here
        # This is provider-specific
        try:
            # Example structure (adapt to your provider):
            # async for chunk in your_streaming_api_call(
            #     messages=[{"role": m.role, "content": m.content} for m in messages],
            #     temperature=temperature,
            #     max_tokens=max_tokens,
            # ):
            #     if "delta" in chunk and "content" in chunk["delta"]:
            #         yield chunk["delta"]["content"]
            
            raise NotImplementedError(
                "Implement your provider's streaming API call here"
            )
        except Exception as e:
            logger.error(f"YourProvider streaming error: {e}")
            raise
            
        yield ""  # Make this a generator
```

### 2. Register in Factory

Update `src/clients/factory.py` to recognize your new provider:

```python
from src.clients.your_provider_client import YourProviderClient

def create_llm_client(
    provider: str,
    api_key: str,
    model: str,
    **kwargs
) -> LLMClient:
    """Factory function to create LLM clients.
    
    Args:
        provider: Provider name ('openai', 'generic', 'requesty', 'yourprovider')
        api_key: API key for authentication
        model: Model identifier
        **kwargs: Additional provider-specific arguments
        
    Returns:
        Instantiated LLMClient
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider.lower() == "openai":
        return OpenAIClient(api_key=api_key, model=model, **kwargs)
    elif provider.lower() == "generic":
        return GenericClient(api_key=api_key, model=model, **kwargs)
    elif provider.lower() == "requesty":
        return RequestyClient(api_key=api_key, model=model, **kwargs)
    elif provider.lower() == "yourprovider":
        return YourProviderClient(api_key=api_key, model=model, **kwargs)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
```

### 3. Export in Package

Update `src/clients/__init__.py`:

```python
"""LLM client implementations."""

from src.clients.factory import create_llm_client
from src.clients.generic_client import GenericClient
from src.clients.openai_client import OpenAIClient
from src.clients.requesty_client import RequestyClient
from src.clients.your_provider_client import YourProviderClient

__all__ = [
    "create_llm_client",
    "OpenAIClient",
    "GenericClient",
    "RequestyClient",
    "YourProviderClient",
]
```

### 4. Add Configuration Support

Update `config/config.yaml` to include your provider:

```yaml
llm_providers:
  yourprovider:
    model: "your-default-model"
    temperature: 0.7
    max_tokens: 8000
    timeout: 60
    base_url: "https://api.yourprovider.com/v1"  # Optional
```

Update `src/config.py` to validate your provider config:

```python
class LLMProviderConfig(BaseModel):
    """Configuration for a single LLM provider."""
    
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 60
    base_url: Optional[str] = None
    
    @validator("temperature")
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v


class LLMConfig(BaseModel):
    """LLM-related configuration."""
    
    default_provider: str = "openai"
    providers: Dict[str, LLMProviderConfig]
    
    @validator("default_provider")
    def validate_default_provider(cls, v, values):
        if "providers" in values and v not in values["providers"]:
            raise ValueError(f"default_provider '{v}' not in providers")
        return v
```

### 5. Add Environment Variables

Update `.env.example`:

```bash
# YourProvider Configuration
YOURPROVIDER_API_KEY=your_api_key_here
YOURPROVIDER_API_BASE_URL=https://api.yourprovider.com/v1  # Optional
```

### 6. Write Tests

Create `tests/unit/test_your_provider_client.py`:

```python
"""Tests for YourProvider LLM client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.clients.your_provider_client import YourProviderClient
from src.models import Message


class TestYourProviderClient:
    """Tests for YourProviderClient."""

    @pytest.fixture
    def client(self):
        """Create test client instance."""
        return YourProviderClient(
            api_key="test_key",
            model="test-model",
        )

    @pytest.mark.asyncio
    async def test_generate_success(self, client):
        """Test successful generation."""
        messages = [Message(role="user", content="Hello")]
        
        # Mock your API call
        with patch("your_api_module.api_call") as mock_call:
            mock_call.return_value = {
                "choices": [{"message": {"content": "Hi there!"}}]
            }
            
            result = await client.generate(messages)
            
            assert result == "Hi there!"
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_stream(self, client):
        """Test streaming generation."""
        messages = [Message(role="user", content="Hello")]
        
        # Mock your streaming API call
        async def mock_stream():
            yield {"delta": {"content": "Hi "}}
            yield {"delta": {"content": "there!"}}
        
        with patch("your_api_module.stream_call", return_value=mock_stream()):
            chunks = []
            async for chunk in client.generate_stream(messages):
                chunks.append(chunk)
            
            assert "".join(chunks) == "Hi there!"

    @pytest.mark.asyncio
    async def test_generate_error_handling(self, client):
        """Test error handling."""
        messages = [Message(role="user", content="Hello")]
        
        with patch("your_api_module.api_call", side_effect=Exception("API Error")):
            with pytest.raises(Exception) as exc_info:
                await client.generate(messages)
            
            assert "API Error" in str(exc_info.value)
```

### 7. Document Usage

Add your provider to README.md:

```markdown
## Supported Providers

- **OpenAI** - Official OpenAI models (GPT-4, GPT-3.5, etc.)
- **Generic** - Any OpenAI-compatible API
- **Requesty** - Requesty API integration
- **YourProvider** - Your custom provider description

### YourProvider Setup

1. Get an API key from [YourProvider](https://yourprovider.com)
2. Add to `.env`:
   ```bash
   YOURPROVIDER_API_KEY=your_key_here
   ```
3. Use in CLI:
   ```bash
   devussy run-full-pipeline --provider yourprovider --name "My Project"
   ```
```

## Best Practices

### Error Handling
- Always wrap API calls in try/except blocks
- Log errors with context for debugging
- Raise exceptions with helpful messages
- Handle rate limits and timeouts gracefully

### Async Implementation
- Use `async`/`await` consistently
- Don't block the event loop with sync operations
- Use `aiohttp` for HTTP requests (don't use `requests`)
- Clean up resources (close sessions) properly

### Testing
- Test both streaming and non-streaming modes
- Mock external API calls
- Test error scenarios (timeouts, rate limits, auth failures)
- Verify correct message formatting

### Configuration
- Provide sensible defaults
- Make all timeouts configurable
- Support custom base URLs for flexibility
- Document all configuration options

### Logging
- Log initialization with key parameters
- Log API calls at DEBUG level
- Log errors at ERROR level with full context
- Don't log sensitive data (API keys, tokens)

## Example: Anthropic Provider

Here's a complete example for adding Anthropic Claude support:

```python
"""Client for Anthropic Claude API."""

import logging
from typing import AsyncIterator, List, Optional

import aiohttp

from src.llm_client import LLMClient
from src.models import Message

logger = logging.getLogger(__name__)


class AnthropicClient(LLMClient):
    """LLM client for Anthropic Claude API."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-opus-20240229",
        base_url: str = "https://api.anthropic.com",
        timeout: int = 60,
    ):
        """Initialize Anthropic client."""
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        logger.info(f"Initialized AnthropicClient with model {model}")

    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
        stream: bool = False,
    ) -> str:
        """Generate completion from messages."""
        if stream:
            chunks = []
            async for chunk in self.generate_stream(messages, temperature, max_tokens):
                chunks.append(chunk)
            return "".join(chunks)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Anthropic API error: {error_text}")
                    raise Exception(f"Anthropic API error: {error_text}")

                data = await response.json()
                return data["content"][0]["text"]

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
    ) -> AsyncIterator[str]:
        """Generate streaming completion from messages."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "stream": True,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Anthropic streaming error: {error_text}")
                    raise Exception(f"Anthropic streaming error: {error_text}")

                async for line in response.content:
                    line_str = line.decode("utf-8").strip()
                    if not line_str or not line_str.startswith("data: "):
                        continue

                    try:
                        import json
                        data = json.loads(line_str[6:])  # Remove "data: " prefix
                        
                        if data["type"] == "content_block_delta":
                            if "delta" in data and "text" in data["delta"]:
                                yield data["delta"]["text"]
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Failed to parse streaming chunk: {e}")
                        continue
```

## Testing Your Provider

After implementation, test your provider:

```bash
# Run unit tests
pytest tests/unit/test_your_provider_client.py -v

# Test in CLI
devussy generate-design \
  --provider yourprovider \
  --name "Test Project" \
  --languages "Python" \
  --requirements "Build a simple API"

# Test with streaming
devussy run-full-pipeline \
  --provider yourprovider \
  --streaming \
  --name "Test Project"
```

## Contributing

When contributing a new provider:

1. Implement the `LLMClient` interface completely
2. Add comprehensive tests (aim for >80% coverage)
3. Document configuration options
4. Update README.md with usage examples
5. Add to factory and configuration
6. Submit a pull request with your changes

## Support

For questions or issues adding providers:
- Open an issue on GitHub
- Check existing provider implementations for reference
- Review the `LLMClient` abstract base class documentation

---

**Next Steps**: Check out [EXAMPLES.md](EXAMPLES.md) for real-world usage scenarios!
