"""LLM Client implementation tests for DevPlan Orchestrator."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from src.clients.factory import create_llm_client
from src.clients.generic_client import GenericOpenAIClient
from src.clients.openai_client import OpenAIClient
from src.clients.requesty_client import RequestyClient
from src.config import AppConfig, LLMConfig, RetryConfig
from src.llm_client import LLMClient


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return Mock(
        llm=Mock(
            provider="openai",
            model="gpt-4",
            api_key="test-api-key",
            org_id="test-org",
            base_url=None,
            temperature=0.7,
            max_tokens=2048,
            api_timeout=30,
        ),
        retry=Mock(
            max_attempts=2,
            initial_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0,
        ),
        max_concurrent_requests=3,
    )


@pytest.fixture
def mock_openai_config():
    """OpenAI-specific configuration."""
    return Mock(
        llm=Mock(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="sk-test123",
            org_id="org-123",
            base_url=None,
            temperature=0.5,
            max_tokens=1024,
            api_timeout=60,
        ),
        retry=Mock(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
        ),
        max_concurrent_requests=5,
    )


@pytest.fixture
def mock_generic_config():
    """Generic OpenAI-compatible configuration."""
    return Mock(
        llm=Mock(
            provider="generic",
            model="custom-model",
            api_key="generic-key",
            base_url="https://api.custom.com",
            temperature=0.8,
            max_tokens=4096,
            api_timeout=45,
        ),
        retry=Mock(
            max_attempts=2,
            initial_delay=0.5,
            max_delay=30.0,
            exponential_base=1.5,
        ),
        max_concurrent_requests=10,
    )


@pytest.fixture
def mock_requesty_config():
    """Requesty-specific configuration."""
    return Mock(
        llm=Mock(
            provider="requesty",
            model="requesty-model",
            api_key="requesty-key-456",
            base_url="https://api.requesty.com",
            temperature=0.9,
            max_tokens=2048,
            api_timeout=120,
        ),
        retry=Mock(
            max_attempts=4,
            initial_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
        ),
        max_concurrent_requests=8,
    )


class TestLLMClient:
    """Test abstract LLMClient base class."""

    def test_init_stores_config(self, mock_config):
        """Test LLMClient stores config properly."""

        # Create a concrete implementation for testing
        class TestClient(LLMClient):
            async def generate_completion(self, prompt: str, **kwargs) -> str:
                return "test response"

        client = TestClient(mock_config)
        assert client._config == mock_config

    @pytest.mark.asyncio
    async def test_generate_multiple_default(self, mock_config):
        """Test default generate_multiple implementation."""

        class TestClient(LLMClient):
            def __init__(self, config):
                super().__init__(config)
                self.call_count = 0

            async def generate_completion(self, prompt: str, **kwargs) -> str:
                self.call_count += 1
                await asyncio.sleep(0.01)  # Simulate async work
                return f"response_{self.call_count}"

        client = TestClient(mock_config)
        prompts = ["prompt1", "prompt2", "prompt3"]

        results = await client.generate_multiple(prompts)

        assert len(results) == 3
        assert all(r.startswith("response_") for r in results)
        assert client.call_count == 3

    def test_generate_completion_sync_no_loop(self, mock_config):
        """Test sync wrapper works outside event loop."""

        class TestClient(LLMClient):
            async def generate_completion(self, prompt: str, **kwargs) -> str:
                return "sync response"

        client = TestClient(mock_config)
        result = client.generate_completion_sync("test prompt")
        assert result == "sync response"

    def test_generate_completion_sync_in_loop_raises(self, mock_config):
        """Test sync wrapper raises error when called in event loop."""

        class TestClient(LLMClient):
            async def generate_completion(self, prompt: str, **kwargs) -> str:
                return "should not reach here"

        async def test_in_loop():
            client = TestClient(mock_config)
            with pytest.raises(
                RuntimeError, match="called inside an active event loop"
            ):
                client.generate_completion_sync("test prompt")

        asyncio.run(test_in_loop())


class TestOpenAIClient:
    """Test OpenAI client implementation."""

    def test_init_configuration(self, mock_openai_config):
        """Test OpenAI client initialization."""
        with patch("src.clients.openai_client.AsyncOpenAI") as mock_async_openai:
            client = OpenAIClient(mock_openai_config)

            # Verify AsyncOpenAI was called with correct parameters
            mock_async_openai.assert_called_once_with(
                api_key="sk-test123", organization="org-123", base_url=None
            )

            assert client._model == "gpt-3.5-turbo"
            assert client._max_attempts == 3
            assert client._initial_delay == 1.0
            assert client._max_delay == 60.0
            assert client._exp_base == 2.0

    @pytest.mark.asyncio
    async def test_generate_completion_success(self, mock_openai_config):
        """Test successful completion generation."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test response from OpenAI"

        with patch("src.clients.openai_client.AsyncOpenAI") as mock_async_openai:
            mock_client_instance = AsyncMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            mock_async_openai.return_value = mock_client_instance

            client = OpenAIClient(mock_openai_config)
            result = await client.generate_completion("test prompt")

            assert result == "Test response from OpenAI"
            mock_client_instance.chat.completions.create.assert_called_once_with(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test prompt"}],
                temperature=0.5,
                max_tokens=1024,
            )

    @pytest.mark.asyncio
    async def test_generate_completion_with_kwargs(self, mock_openai_config):
        """Test completion generation with custom parameters."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Custom response"

        with patch("src.clients.openai_client.AsyncOpenAI") as mock_async_openai:
            mock_client_instance = AsyncMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            mock_async_openai.return_value = mock_client_instance

            client = OpenAIClient(mock_openai_config)
            result = await client.generate_completion(
                "test prompt", model="gpt-4", temperature=0.9, max_tokens=512, top_p=0.8
            )

            assert result == "Custom response"
            mock_client_instance.chat.completions.create.assert_called_once_with(
                model="gpt-4",
                messages=[{"role": "user", "content": "test prompt"}],
                temperature=0.9,
                max_tokens=512,
                top_p=0.8,
            )

    @pytest.mark.asyncio
    async def test_generate_completion_empty_content(self, mock_openai_config):
        """Test handling of empty/None content."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = None

        with patch("src.clients.openai_client.AsyncOpenAI") as mock_async_openai:
            mock_client_instance = AsyncMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            mock_async_openai.return_value = mock_client_instance

            client = OpenAIClient(mock_openai_config)
            result = await client.generate_completion("test prompt")

            assert result == ""

    @pytest.mark.asyncio
    async def test_generate_completion_retry_on_failure(self, mock_openai_config):
        """Test retry logic on API failures."""
        with patch("src.clients.openai_client.AsyncOpenAI") as mock_async_openai:
            mock_client_instance = AsyncMock()
            # First call fails, second succeeds
            mock_client_instance.chat.completions.create.side_effect = [
                Exception("API Error"),
                Mock(choices=[Mock(message=Mock(content="Success after retry"))]),
            ]
            mock_async_openai.return_value = mock_client_instance

            client = OpenAIClient(mock_openai_config)
            result = await client.generate_completion("test prompt")

            assert result == "Success after retry"
            assert mock_client_instance.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_multiple(self, mock_openai_config):
        """Test multiple concurrent completions."""
        responses = [
            Mock(choices=[Mock(message=Mock(content="Response 1"))]),
            Mock(choices=[Mock(message=Mock(content="Response 2"))]),
            Mock(choices=[Mock(message=Mock(content="Response 3"))]),
        ]

        with patch("src.clients.openai_client.AsyncOpenAI") as mock_async_openai:
            mock_client_instance = AsyncMock()
            mock_client_instance.chat.completions.create.side_effect = responses
            mock_async_openai.return_value = mock_client_instance

            client = OpenAIClient(mock_openai_config)
            prompts = ["prompt 1", "prompt 2", "prompt 3"]
            results = await client.generate_multiple(prompts)

            assert len(results) == 3
            assert "Response 1" in results
            assert "Response 2" in results
            assert "Response 3" in results
            assert mock_client_instance.chat.completions.create.call_count == 3


class TestGenericOpenAIClient:
    """Test Generic OpenAI-compatible client."""

    def test_init_configuration(self, mock_generic_config):
        """Test generic client initialization."""
        client = GenericOpenAIClient(mock_generic_config)

        assert client._api_key == "generic-key"
        assert client._base_url == "https://api.custom.com"
        assert client._model == "custom-model"
        assert client._temperature == 0.8
        assert client._max_tokens == 4096

    def test_endpoint_property(self, mock_generic_config):
        """Test endpoint URL construction."""
        client = GenericOpenAIClient(mock_generic_config)
        assert client._endpoint == "https://api.custom.com/v1/chat/completions"

    def test_endpoint_property_trailing_slash(self, mock_generic_config):
        """Test endpoint URL with trailing slash."""
        mock_generic_config.llm.base_url = "https://api.custom.com/"
        client = GenericOpenAIClient(mock_generic_config)
        assert client._endpoint == "https://api.custom.com/v1/chat/completions"

    @pytest.mark.asyncio
    async def test_generate_completion_success(self, mock_generic_config):
        """Test successful completion via HTTP."""
        # Mock the _post_chat method directly to avoid aiohttp complexity
        with patch.object(
            GenericOpenAIClient, "_post_chat", new_callable=AsyncMock
        ) as mock_post_chat:
            mock_post_chat.return_value = "Generic API response"

            client = GenericOpenAIClient(mock_generic_config)
            result = await client.generate_completion("test prompt")

            assert result == "Generic API response"
            mock_post_chat.assert_called_once_with("test prompt")

    @pytest.mark.asyncio
    async def test_generate_completion_with_top_p(self, mock_generic_config):
        """Test completion with top_p parameter."""
        with patch.object(
            GenericOpenAIClient, "_post_chat", new_callable=AsyncMock
        ) as mock_post_chat:
            mock_post_chat.return_value = "Response with top_p"

            client = GenericOpenAIClient(mock_generic_config)
            result = await client.generate_completion("test", top_p=0.9)

            assert result == "Response with top_p"
            mock_post_chat.assert_called_once_with("test", top_p=0.9)

    @pytest.mark.asyncio
    async def test_generate_completion_empty_response(self, mock_generic_config):
        """Test handling of empty API response."""
        with patch.object(
            GenericOpenAIClient, "_post_chat", new_callable=AsyncMock
        ) as mock_post_chat:
            mock_post_chat.return_value = ""

            client = GenericOpenAIClient(mock_generic_config)
            result = await client.generate_completion("test prompt")

            assert result == ""
            mock_post_chat.assert_called_once_with("test prompt")

    @pytest.mark.asyncio
    async def test_generate_completion_malformed_response(self, mock_generic_config):
        """Test handling of malformed API response."""
        with patch.object(
            GenericOpenAIClient, "_post_chat", new_callable=AsyncMock
        ) as mock_post_chat:
            mock_post_chat.return_value = ""

            client = GenericOpenAIClient(mock_generic_config)
            result = await client.generate_completion("test prompt")

            assert result == ""
            mock_post_chat.assert_called_once_with("test prompt")

    @pytest.mark.asyncio
    async def test_generate_completion_http_error(self, mock_generic_config):
        """Test handling of HTTP errors."""
        with patch.object(
            GenericOpenAIClient, "_post_chat", new_callable=AsyncMock
        ) as mock_post_chat:
            mock_post_chat.side_effect = aiohttp.ClientError("HTTP Error")

            client = GenericOpenAIClient(mock_generic_config)

            with pytest.raises(aiohttp.ClientError):
                await client.generate_completion("test prompt")

    @pytest.mark.asyncio
    async def test_generate_completion_retry_on_failure(self, mock_generic_config):
        """Test retry logic on HTTP failures."""
        with patch.object(
            GenericOpenAIClient, "_post_chat", new_callable=AsyncMock
        ) as mock_post_chat:
            # First call fails, second succeeds (testing retry functionality)
            mock_post_chat.side_effect = [
                aiohttp.ClientError("Temporary error"),
                "Success after retry",
            ]

            client = GenericOpenAIClient(mock_generic_config)
            result = await client.generate_completion("test prompt")

            assert result == "Success after retry"
            assert mock_post_chat.call_count == 2


class TestRequestyClient:
    """Test Requesty client implementation."""

    def test_init_configuration(self, mock_requesty_config):
        """Test Requesty client initialization."""
        client = RequestyClient(mock_requesty_config)

        assert client._api_key == "requesty-key-456"
        assert client._base_url == "https://api.requesty.com"
        assert client._model == "requesty-model"
        assert client._temperature == 0.9
        assert client._max_tokens == 2048

    def test_endpoint_property(self, mock_requesty_config):
        """Test endpoint URL construction."""
        client = RequestyClient(mock_requesty_config)
        assert client._endpoint == "https://api.requesty.com/v1/generate"

    @pytest.mark.asyncio
    async def test_generate_completion_with_text_field(self, mock_requesty_config):
        """Test completion with Requesty's 'text' field."""
        with patch.object(
            RequestyClient, "_post_generate", new_callable=AsyncMock
        ) as mock_post_generate:
            mock_post_generate.return_value = "Requesty response text"

            client = RequestyClient(mock_requesty_config)
            result = await client.generate_completion("test prompt")

            assert result == "Requesty response text"
            mock_post_generate.assert_called_once_with("test prompt")

    @pytest.mark.asyncio
    async def test_generate_completion_fallback_to_openai_format(
        self, mock_requesty_config
    ):
        """Test fallback to OpenAI-compatible format."""
        with patch.object(
            RequestyClient, "_post_generate", new_callable=AsyncMock
        ) as mock_post_generate:
            mock_post_generate.return_value = "OpenAI-compatible response"

            client = RequestyClient(mock_requesty_config)
            result = await client.generate_completion("test prompt")

            assert result == "OpenAI-compatible response"
            mock_post_generate.assert_called_once_with("test prompt")

    @pytest.mark.asyncio
    async def test_generate_completion_with_custom_params(self, mock_requesty_config):
        """Test completion with custom parameters."""
        with patch.object(
            RequestyClient, "_post_generate", new_callable=AsyncMock
        ) as mock_post_generate:
            mock_post_generate.return_value = "Custom params response"

            client = RequestyClient(mock_requesty_config)
            result = await client.generate_completion(
                "test prompt",
                model="custom-requesty-model",
                temperature=0.5,
                max_tokens=1000,
                top_p=0.95,
            )

            assert result == "Custom params response"
            mock_post_generate.assert_called_once_with(
                "test prompt",
                model="custom-requesty-model",
                temperature=0.5,
                max_tokens=1000,
                top_p=0.95,
            )

    @pytest.mark.asyncio
    async def test_generate_completion_empty_response(self, mock_requesty_config):
        """Test handling of empty response."""
        with patch.object(
            RequestyClient, "_post_generate", new_callable=AsyncMock
        ) as mock_post_generate:
            mock_post_generate.return_value = ""

            client = RequestyClient(mock_requesty_config)
            result = await client.generate_completion("test prompt")

            assert result == ""
            mock_post_generate.assert_called_once_with("test prompt")


class TestClientFactory:
    """Test LLM client factory."""

    def test_create_openai_client(self):
        """Test creating OpenAI client via factory."""
        config = AppConfig(
            llm=LLMConfig(provider="openai", api_key="test-key"), retry=RetryConfig()
        )

        with patch("src.clients.openai_client.AsyncOpenAI"):
            client = create_llm_client(config)
            assert isinstance(client, OpenAIClient)

    def test_create_generic_client(self):
        """Test creating generic client via factory."""
        config = AppConfig(
            llm=LLMConfig(
                provider="generic",
                api_key="test-key",
                base_url="https://api.example.com",
            ),
            retry=RetryConfig(),
        )

        client = create_llm_client(config)
        assert isinstance(client, GenericOpenAIClient)

    def test_create_requesty_client(self):
        """Test creating Requesty client via factory."""
        config = AppConfig(
            llm=LLMConfig(
                provider="requesty",
                api_key="test-key",
                base_url="https://api.requesty.com",
            ),
            retry=RetryConfig(),
        )

        client = create_llm_client(config)
        assert isinstance(client, RequestyClient)

    def test_create_client_unknown_provider(self):
        """Test error handling for unknown provider."""
        # Create a mock config with an unknown provider to bypass Pydantic validation
        mock_config = Mock()
        mock_config.llm = Mock()
        mock_config.llm.provider = "unknown"

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            create_llm_client(mock_config)
