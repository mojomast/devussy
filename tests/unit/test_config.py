"""Configuration loader tests for DevPlan Orchestrator."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from src.config import (
    AppConfig,
    DocumentationConfig,
    GitConfig,
    LLMConfig,
    PipelineConfig,
    RetryConfig,
    load_config,
)


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        "llm_provider": "openai",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2048,
        "api_timeout": 30,
        "max_concurrent_requests": 3,
        "retry": {
            "max_attempts": 2,
            "initial_delay": 0.5,
            "max_delay": 30,
            "exponential_base": 2.5,
        },
        "streaming_enabled": True,
        "output_dir": "./test_output",
        "state_dir": "./.test_state",
        "log_level": "DEBUG",
        "log_file": "test.log",
        "log_format": "%(levelname)s - %(message)s",
        "git_enabled": False,
        "git_commit_after_design": False,
        "git_commit_after_devplan": True,
        "git_commit_after_handoff": True,
        "documentation": {
            "auto_generate": False,
            "include_citations": True,
            "timestamp_updates": False,
            "generate_index": True,
        },
        "pipeline": {
            "save_intermediate_results": False,
            "validate_output": True,
            "enable_checkpoints": False,
        },
    }


@pytest.fixture
def temp_config_file(sample_config_data):
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(sample_config_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if Path(temp_path).exists():
        os.unlink(temp_path)


class TestRetryConfig:
    """Test RetryConfig model."""

    def test_default_values(self):
        """Test default retry configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0

    def test_valid_values(self):
        """Test valid retry configuration values."""
        config = RetryConfig(
            max_attempts=5, initial_delay=0.5, max_delay=120.0, exponential_base=1.5
        )
        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 120.0
        assert config.exponential_base == 1.5

    def test_invalid_max_attempts(self):
        """Test invalid max_attempts raises ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            RetryConfig(max_attempts=0)
        assert "max_attempts" in str(excinfo.value)

    def test_invalid_initial_delay(self):
        """Test negative initial_delay raises ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            RetryConfig(initial_delay=-1.0)
        assert "initial_delay" in str(excinfo.value)

    def test_invalid_exponential_base(self):
        """Test exponential_base less than 1 raises ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            RetryConfig(exponential_base=0.5)
        assert "exponential_base" in str(excinfo.value)


class TestLLMConfig:
    """Test LLMConfig model."""

    def test_default_values(self):
        """Test default LLM configuration values."""
        config = LLMConfig()
        # Defaults from code (not environment)
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.api_key is None
        assert config.base_url is None
        assert config.temperature == 0.7
    assert config.max_tokens == 4096
    assert config.api_timeout == 600

    def test_valid_provider_openai(self):
        """Test valid OpenAI provider."""
        config = LLMConfig(provider="OpenAI")
        assert config.provider == "openai"

    def test_valid_provider_generic(self):
        """Test valid generic provider."""
        config = LLMConfig(provider="GENERIC")
        assert config.provider == "generic"

    def test_valid_provider_requesty(self):
        """Test valid Requesty provider."""
        config = LLMConfig(provider="requesty")
        assert config.provider == "requesty"

    def test_invalid_provider(self):
        """Test invalid provider raises ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            LLMConfig(provider="invalid_provider")
        assert "Provider must be one of" in str(excinfo.value)

    def test_temperature_bounds(self):
        """Test temperature validation bounds."""
        # Valid temperatures
        LLMConfig(temperature=0.0)
        LLMConfig(temperature=1.0)
        LLMConfig(temperature=2.0)

        # Invalid temperatures
        with pytest.raises(ValidationError):
            LLMConfig(temperature=-0.1)

        with pytest.raises(ValidationError):
            LLMConfig(temperature=2.1)

    def test_max_tokens_validation(self):
        """Test max_tokens must be positive."""
        LLMConfig(max_tokens=1)
        LLMConfig(max_tokens=8192)

        with pytest.raises(ValidationError):
            LLMConfig(max_tokens=0)

    def test_api_timeout_validation(self):
        """Test api_timeout must be positive."""
        LLMConfig(api_timeout=1)
        LLMConfig(api_timeout=300)

        with pytest.raises(ValidationError):
            LLMConfig(api_timeout=0)


class TestDocumentationConfig:
    """Test DocumentationConfig model."""

    def test_default_values(self):
        """Test default documentation configuration."""
        config = DocumentationConfig()
        assert config.auto_generate is True
        assert config.include_citations is True
        assert config.timestamp_updates is True
        assert config.generate_index is True

    def test_custom_values(self):
        """Test custom documentation configuration."""
        config = DocumentationConfig(
            auto_generate=False,
            include_citations=False,
            timestamp_updates=False,
            generate_index=False,
        )
        assert config.auto_generate is False
        assert config.include_citations is False
        assert config.timestamp_updates is False
        assert config.generate_index is False


class TestPipelineConfig:
    """Test PipelineConfig model."""

    def test_default_values(self):
        """Test default pipeline configuration."""
        config = PipelineConfig()
        assert config.save_intermediate_results is True
        assert config.validate_output is True
        assert config.enable_checkpoints is True

    def test_custom_values(self):
        """Test custom pipeline configuration."""
        config = PipelineConfig(
            save_intermediate_results=False,
            validate_output=False,
            enable_checkpoints=False,
        )
        assert config.save_intermediate_results is False
        assert config.validate_output is False
        assert config.enable_checkpoints is False


class TestGitConfig:
    """Test GitConfig model."""

    def test_default_values(self):
        """Test default Git configuration."""
        config = GitConfig()
        assert config.enabled is True
        assert config.commit_after_design is True
        assert config.commit_after_devplan is True
        assert config.commit_after_handoff is True
        assert config.auto_push is False

    def test_custom_values(self):
        """Test custom Git configuration."""
        config = GitConfig(
            enabled=False,
            commit_after_design=False,
            commit_after_devplan=False,
            commit_after_handoff=False,
            auto_push=True,
        )
        assert config.enabled is False
        assert config.commit_after_design is False
        assert config.commit_after_devplan is False
        assert config.commit_after_handoff is False
        assert config.auto_push is True


class TestAppConfig:
    """Test AppConfig model."""

    def test_default_values(self):
        """Test default app configuration."""
        config = AppConfig()
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.retry, RetryConfig)
        assert isinstance(config.documentation, DocumentationConfig)
        assert isinstance(config.pipeline, PipelineConfig)
        assert isinstance(config.git, GitConfig)
        assert config.max_concurrent_requests == 5
        assert config.streaming_enabled is False
        assert config.output_dir == Path("./docs")
        assert config.state_dir == Path("./.devussy_state")
        assert config.log_level == "INFO"
        assert config.log_file == Path("logs/devussy.log")

    def test_max_concurrent_requests_validation(self):
        """Test max_concurrent_requests must be positive."""
        AppConfig(max_concurrent_requests=1)
        AppConfig(max_concurrent_requests=10)

        with pytest.raises(ValidationError):
            AppConfig(max_concurrent_requests=0)

    def test_log_level_validation(self):
        """Test log level validation."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            config = AppConfig(log_level=level)
            assert config.log_level == level.upper()

        # Test case insensitive
        config = AppConfig(log_level="debug")
        assert config.log_level == "DEBUG"

        # Test invalid log level
        with pytest.raises(ValidationError) as excinfo:
            AppConfig(log_level="INVALID")
        assert "Log level must be one of" in str(excinfo.value)

    def test_nested_config_override(self):
        """Test overriding nested configuration."""
        config = AppConfig(
            llm=LLMConfig(provider="generic", model="custom-model"),
            retry=RetryConfig(max_attempts=5),
            max_concurrent_requests=10,
        )
        assert config.llm.provider == "generic"
        assert config.llm.model == "custom-model"
        assert config.retry.max_attempts == 5
        assert config.max_concurrent_requests == 10


class TestLoadConfig:
    """Test load_config function."""

    def test_load_from_file(self, temp_config_file):
        """Test loading configuration from YAML file."""
        # Load config with environment (production behavior)
        config = load_config(temp_config_file)

        # The temp config has openai/gpt-4, but .env has LLM_PROVIDER=requesty and MODEL=openai/gpt-5-mini
        # which overrides it (this is expected production behavior)
        assert config.llm.provider == "requesty"  # From .env LLM_PROVIDER
        assert config.llm.model == "openai/gpt-5-mini"  # From .env MODEL
        assert config.llm.temperature == 0.7
        assert config.llm.max_tokens == 2048
        assert config.retry.max_attempts == 2
        assert config.streaming_enabled is True
        assert config.log_level == "DEBUG"
        assert config.git.enabled is False

    def test_load_nonexistent_file(self):
        """Test loading non-existent config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as excinfo:
            load_config("nonexistent_config.yaml")
        assert "Configuration file not found" in str(excinfo.value)

    def test_environment_variable_overrides(self, temp_config_file):
        """Test environment variables override config file values."""
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "generic",
                "OPENAI_API_KEY": "test_api_key",
                "OPENAI_ORG_ID": "test_org",
                "GENERIC_BASE_URL": "https://api.example.com",
                "MAX_CONCURRENT_REQUESTS": "8",
                "STREAMING_ENABLED": "false",
                "OUTPUT_DIR": "/custom/output",
                "STATE_DIR": "/custom/state",
                "LOG_LEVEL": "ERROR",
                "LOG_FILE": "/custom/log.log",
                "GIT_ENABLED": "true",
                "GIT_AUTO_PUSH": "true",
                "ENABLE_CHECKPOINTS": "false",
            },
        ):
            config = load_config(temp_config_file)

            assert config.llm.provider == "generic"
            assert config.llm.api_key == "test_api_key"
            assert config.llm.org_id == "test_org"
            assert config.llm.base_url == "https://api.example.com"
            assert config.max_concurrent_requests == 8
            assert config.streaming_enabled is False
            assert config.output_dir == Path("/custom/output")
            assert config.state_dir == Path("/custom/state")
            assert config.log_level == "ERROR"
            assert config.log_file == Path("/custom/log.log")
            assert config.git.enabled is True
            assert config.git.auto_push is True
            assert config.pipeline.enable_checkpoints is False

    def test_api_key_priority(self, temp_config_file):
        """Test API key environment variable is provider-specific."""
        # With requesty provider (from .env), should use REQUESTY_API_KEY
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "requesty",
                "OPENAI_API_KEY": "openai_key",
                "REQUESTY_API_KEY": "requesty_key",
                "GENERIC_API_KEY": "generic_key",
            },
        ):
            config = load_config(temp_config_file)
            assert config.llm.provider == "requesty"
            assert config.llm.api_key == "requesty_key"

        # With openai provider, should use OPENAI_API_KEY
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "openai",
                "OPENAI_API_KEY": "openai_key",
                "REQUESTY_API_KEY": "requesty_key",
            },
            clear=True,
        ):
            config = load_config(temp_config_file)
            assert config.llm.provider == "openai"
            assert config.llm.api_key == "openai_key"

        # With generic provider, should use GENERIC_API_KEY
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "generic",
                "GENERIC_API_KEY": "generic_key",
            },
            clear=True,
        ):
            config = load_config(temp_config_file)
            assert config.llm.provider == "generic"
            assert config.llm.api_key == "generic_key"

    def test_base_url_priority(self, temp_config_file):
        """Test base URL environment variable is provider-specific."""
        # With requesty provider (from .env), should use REQUESTY_BASE_URL
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "requesty",
                "GENERIC_BASE_URL": "https://generic.api.com",
                "REQUESTY_BASE_URL": "https://requesty.api.com",
            },
        ):
            config = load_config(temp_config_file)
            assert config.llm.provider == "requesty"
            assert config.llm.base_url == "https://requesty.api.com"

        # With openai provider, should use OPENAI_BASE_URL
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "openai",
                "OPENAI_BASE_URL": "https://openai.custom.com",
            },
            clear=True,
        ):
            config = load_config(temp_config_file)
            assert config.llm.provider == "openai"
            assert config.llm.base_url == "https://openai.custom.com"

    def test_config_path_from_env(self, temp_config_file):
        """Test CONFIG_PATH environment variable."""
        with patch.dict(os.environ, {"CONFIG_PATH": temp_config_file}):
            config = load_config()  # No path specified
            # Provider comes from .env (requesty) which overrides temp config
            assert config.llm.provider == "requesty"

    def test_empty_config_file(self):
        """Test loading empty config file uses defaults plus environment."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write("")  # Empty file
            temp_path = f.name

        try:
            config = load_config(temp_path)
            # Should use code defaults + environment overrides
            # .env has LLM_PROVIDER=requesty and MODEL=openai/gpt-5-mini
            assert config.llm.provider == "requesty"  # From .env LLM_PROVIDER
            assert config.llm.model == "openai/gpt-5-mini"  # From .env MODEL
            assert config.max_concurrent_requests == 5
        finally:
            if Path(temp_path).exists():
                os.unlink(temp_path)

    def test_malformed_yaml(self):
        """Test loading malformed YAML raises ValueError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write("invalid_yaml: [unclosed")
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as excinfo:
                load_config(temp_path)
            assert "Invalid YAML configuration" in str(excinfo.value)
        finally:
            if Path(temp_path).exists():
                os.unlink(temp_path)

    def test_invalid_config_values(self, temp_config_file):
        """Test invalid configuration values raise ValueError."""
        # Modify config to have invalid values
        invalid_config = {
            "llm_provider": "invalid_provider",
            "max_concurrent_requests": 0,
            "log_level": "INVALID_LEVEL",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(invalid_config, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as excinfo:
                load_config(temp_path)
            assert "Invalid configuration" in str(excinfo.value)
        finally:
            if Path(temp_path).exists():
                os.unlink(temp_path)

    def test_boolean_string_conversion(self, temp_config_file):
        """Test boolean string conversion from environment variables."""
        test_cases = [
            ("true", True),
            ("TRUE", True),
            ("True", True),
            ("false", False),
            ("FALSE", False),
            ("False", False),
        ]

        for env_value, expected in test_cases:
            with patch.dict(
                os.environ,
                {
                    "STREAMING_ENABLED": env_value,
                    "GIT_ENABLED": env_value,
                    "GIT_AUTO_PUSH": env_value,
                    "ENABLE_CHECKPOINTS": env_value,
                },
            ):
                config = load_config(temp_config_file)
                assert config.streaming_enabled is expected
                assert config.git.enabled is expected
                assert config.git.auto_push is expected
                assert config.pipeline.enable_checkpoints is expected

    def test_path_conversion(self, temp_config_file):
        """Test Path object conversion from strings."""
        config = load_config(temp_config_file)
        assert isinstance(config.output_dir, Path)
        assert isinstance(config.state_dir, Path)
        assert isinstance(config.log_file, Path)
        assert str(config.output_dir) == "test_output"
