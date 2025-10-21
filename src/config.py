"""Configuration loader for DevPlan Orchestrator."""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


class RetryConfig(BaseModel):
    """Retry configuration for API requests."""

    max_attempts: int = Field(
        default=3, ge=1, description="Maximum number of retry attempts"
    )
    initial_delay: float = Field(
        default=1.0, ge=0, description="Initial delay in seconds"
    )
    max_delay: float = Field(default=60.0, ge=0, description="Maximum delay in seconds")
    exponential_base: float = Field(
        default=2.0, ge=1, description="Exponential backoff base"
    )


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = Field(default="openai", description="LLM provider name")
    model: str = Field(default="gpt-4", description="Model identifier")
    api_key: Optional[str] = Field(default=None, description="API key for the provider")
    base_url: Optional[str] = Field(
        default=None, description="Base URL for generic providers"
    )
    org_id: Optional[str] = Field(default=None, description="Organization ID (OpenAI)")
    temperature: float = Field(
        default=0.7, ge=0, le=2, description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=4096, ge=1, description="Maximum tokens to generate"
    )
    api_timeout: int = Field(
        default=60, ge=1, description="API request timeout in seconds"
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is one of the supported options."""
        allowed = ["openai", "generic", "requesty"]
        if v.lower() not in allowed:
            raise ValueError(f"Provider must be one of {allowed}, got: {v}")
        return v.lower()

    def merge_with(self, override: Optional["LLMConfig"]) -> "LLMConfig":
        """Merge this config with an override config.
        
        Args:
            override: Optional override config (takes precedence)
            
        Returns:
            New LLMConfig with overrides applied
        """
        if override is None:
            return self.model_copy()
        
        # Start with base config values
        merged_data = self.model_dump()
        
        # Override with non-None values from override config
        override_data = override.model_dump()
        for key, value in override_data.items():
            if value is not None:
                merged_data[key] = value
        
        return LLMConfig(**merged_data)


class DocumentationConfig(BaseModel):
    """Documentation generation configuration."""

    auto_generate: bool = Field(
        default=True, description="Automatically generate documentation"
    )
    include_citations: bool = Field(
        default=True, description="Include citations in documentation"
    )
    timestamp_updates: bool = Field(
        default=True, description="Add timestamps to documentation updates"
    )
    generate_index: bool = Field(
        default=True, description="Generate documentation index"
    )


class PipelineConfig(BaseModel):
    """Pipeline execution configuration."""

    save_intermediate_results: bool = Field(
        default=True, description="Save intermediate pipeline results"
    )
    validate_output: bool = Field(default=True, description="Validate pipeline output")
    enable_checkpoints: bool = Field(
        default=True, description="Enable progress checkpoints"
    )


class GitConfig(BaseModel):
    """Git integration configuration."""

    enabled: bool = Field(default=True, description="Enable automatic git commits")
    commit_after_design: bool = Field(
        default=True, description="Commit after design generation"
    )
    commit_after_devplan: bool = Field(
        default=True, description="Commit after devplan generation"
    )
    commit_after_handoff: bool = Field(
        default=True, description="Commit after handoff generation"
    )
    auto_push: bool = Field(
        default=False, description="Automatically push commits to remote"
    )


class AppConfig(BaseModel):
    """Main application configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    documentation: DocumentationConfig = Field(default_factory=DocumentationConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    git: GitConfig = Field(default_factory=GitConfig)

    # Per-stage LLM configurations (optional overrides)
    design_llm: Optional[LLMConfig] = Field(
        default=None, description="LLM config for project design stage"
    )
    devplan_llm: Optional[LLMConfig] = Field(
        default=None, description="LLM config for devplan generation stage"
    )
    handoff_llm: Optional[LLMConfig] = Field(
        default=None, description="LLM config for handoff prompt stage"
    )

    max_concurrent_requests: int = Field(
        default=5, ge=1, description="Maximum concurrent API requests"
    )
    streaming_enabled: bool = Field(default=False, description="Enable token streaming")
    output_dir: Path = Field(
        default=Path("./docs"), description="Output directory for documentation"
    )
    state_dir: Path = Field(
        default=Path("./.devussy_state"), description="State persistence directory"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Path = Field(
        default=Path("logs/devussy.log"), description="Log file path"
    )
    log_format: str = Field(
        default="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
        description="Log format string",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}, got: {v}")
        return v.upper()

    def get_llm_config_for_stage(self, stage: str) -> LLMConfig:
        """Get the effective LLM config for a specific pipeline stage.
        
        Args:
            stage: Pipeline stage name ('design', 'devplan', or 'handoff')
            
        Returns:
            LLMConfig with stage-specific overrides applied
        """
        stage_config = None
        if stage == "design":
            stage_config = self.design_llm
        elif stage == "devplan":
            stage_config = self.devplan_llm
        elif stage == "handoff":
            stage_config = self.handoff_llm
        
        # Merge with base config
        return self.llm.merge_with(stage_config)


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to configuration YAML file.
            If None, defaults to config/config.yaml

    Returns:
        AppConfig: Loaded and validated configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
    """
    # Load environment variables from .env file
    load_dotenv()

    # Determine config file path
    if config_path is None:
        config_path = os.getenv("CONFIG_PATH", "config/config.yaml")

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    # Load YAML configuration
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML configuration: {e}") from e

    # Override with environment variables
    env_overrides = {}

    # Helper function to load LLM config for a specific stage or global
    def _load_llm_config(prefix: str = "") -> dict:
        """Load LLM configuration with optional prefix for stage-specific configs."""
        llm_config = {}
        
        # Provider
        provider_key = f"{prefix}llm_provider" if prefix else "llm_provider"
        env_provider_key = f"{prefix.upper()}LLM_PROVIDER" if prefix else "LLM_PROVIDER"
        
        if provider_key in config_data:
            llm_config["provider"] = config_data[provider_key]
        if os.getenv(env_provider_key):
            llm_config["provider"] = os.getenv(env_provider_key)
        
        # Model
        model_key = f"{prefix}model" if prefix else "model"
        env_model_key = f"{prefix.upper()}MODEL" if prefix else None
        
        if model_key in config_data:
            llm_config["model"] = config_data[model_key]
        if env_model_key and os.getenv(env_model_key):
            llm_config["model"] = os.getenv(env_model_key)
        
        # API Key (check provider-specific env vars for global config)
        if not prefix:
            if os.getenv("OPENAI_API_KEY"):
                llm_config["api_key"] = os.getenv("OPENAI_API_KEY")
            elif os.getenv("REQUESTY_API_KEY"):
                llm_config["api_key"] = os.getenv("REQUESTY_API_KEY")
            elif os.getenv("GENERIC_API_KEY"):
                llm_config["api_key"] = os.getenv("GENERIC_API_KEY")
        
        # Stage-specific API key
        api_key_env = f"{prefix.upper()}API_KEY" if prefix else None
        if api_key_env and os.getenv(api_key_env):
            llm_config["api_key"] = os.getenv(api_key_env)
        
        # Organization ID
        if not prefix and os.getenv("OPENAI_ORG_ID"):
            llm_config["org_id"] = os.getenv("OPENAI_ORG_ID")
        org_id_env = f"{prefix.upper()}ORG_ID" if prefix else None
        if org_id_env and os.getenv(org_id_env):
            llm_config["org_id"] = os.getenv(org_id_env)
        
        # Base URL
        if not prefix:
            if os.getenv("GENERIC_BASE_URL"):
                llm_config["base_url"] = os.getenv("GENERIC_BASE_URL")
            elif os.getenv("REQUESTY_BASE_URL"):
                llm_config["base_url"] = os.getenv("REQUESTY_BASE_URL")
        
        base_url_env = f"{prefix.upper()}BASE_URL" if prefix else None
        if base_url_env and os.getenv(base_url_env):
            llm_config["base_url"] = os.getenv(base_url_env)
        
        # Temperature, max_tokens, api_timeout
        temp_key = f"{prefix}temperature" if prefix else "temperature"
        if temp_key in config_data:
            llm_config["temperature"] = config_data[temp_key]
        
        tokens_key = f"{prefix}max_tokens" if prefix else "max_tokens"
        if tokens_key in config_data:
            llm_config["max_tokens"] = config_data[tokens_key]
        
        timeout_key = f"{prefix}api_timeout" if prefix else "api_timeout"
        if timeout_key in config_data:
            llm_config["api_timeout"] = config_data[timeout_key]
        
        return llm_config if llm_config else None
    
    # Load global LLM configuration
    global_llm = _load_llm_config()
    if global_llm:
        env_overrides["llm"] = global_llm
    
    # Load per-stage LLM configurations
    design_llm = _load_llm_config("design_")
    if design_llm:
        env_overrides["design_llm"] = design_llm
    
    devplan_llm = _load_llm_config("devplan_")
    if devplan_llm:
        env_overrides["devplan_llm"] = devplan_llm
    
    handoff_llm = _load_llm_config("handoff_")
    if handoff_llm:
        env_overrides["handoff_llm"] = handoff_llm

    # Retry configuration
    if "retry" in config_data:
        env_overrides["retry"] = config_data["retry"]

    # Max concurrent requests
    if "max_concurrent_requests" in config_data:
        env_overrides["max_concurrent_requests"] = config_data[
            "max_concurrent_requests"
        ]
    if os.getenv("MAX_CONCURRENT_REQUESTS"):
        env_overrides["max_concurrent_requests"] = int(
            os.getenv("MAX_CONCURRENT_REQUESTS")
        )

    # Streaming
    if "streaming_enabled" in config_data:
        env_overrides["streaming_enabled"] = config_data["streaming_enabled"]
    if os.getenv("STREAMING_ENABLED"):
        env_overrides["streaming_enabled"] = (
            os.getenv("STREAMING_ENABLED").lower() == "true"
        )

    # Directories
    if "output_dir" in config_data:
        env_overrides["output_dir"] = Path(config_data["output_dir"])
    if os.getenv("OUTPUT_DIR"):
        env_overrides["output_dir"] = Path(os.getenv("OUTPUT_DIR"))

    if "state_dir" in config_data:
        env_overrides["state_dir"] = Path(config_data["state_dir"])
    if os.getenv("STATE_DIR"):
        env_overrides["state_dir"] = Path(os.getenv("STATE_DIR"))

    # Logging
    if "log_level" in config_data:
        env_overrides["log_level"] = config_data["log_level"]
    if os.getenv("LOG_LEVEL"):
        env_overrides["log_level"] = os.getenv("LOG_LEVEL")

    if "log_file" in config_data:
        env_overrides["log_file"] = Path(config_data["log_file"])
    if os.getenv("LOG_FILE"):
        env_overrides["log_file"] = Path(os.getenv("LOG_FILE"))

    if "log_format" in config_data:
        env_overrides["log_format"] = config_data["log_format"]

    # Git configuration
    if "git_enabled" in config_data:
        env_overrides.setdefault("git", {})["enabled"] = config_data["git_enabled"]
    if os.getenv("GIT_ENABLED"):
        env_overrides.setdefault("git", {})["enabled"] = (
            os.getenv("GIT_ENABLED").lower() == "true"
        )

    if "git_commit_after_design" in config_data:
        env_overrides.setdefault("git", {})["commit_after_design"] = config_data[
            "git_commit_after_design"
        ]
    if "git_commit_after_devplan" in config_data:
        env_overrides.setdefault("git", {})["commit_after_devplan"] = config_data[
            "git_commit_after_devplan"
        ]
    if "git_commit_after_handoff" in config_data:
        env_overrides.setdefault("git", {})["commit_after_handoff"] = config_data[
            "git_commit_after_handoff"
        ]

    if os.getenv("GIT_AUTO_PUSH"):
        env_overrides.setdefault("git", {})["auto_push"] = (
            os.getenv("GIT_AUTO_PUSH").lower() == "true"
        )

    # Documentation configuration
    if "documentation" in config_data:
        env_overrides["documentation"] = config_data["documentation"]

    # Pipeline configuration
    if "pipeline" in config_data:
        env_overrides["pipeline"] = config_data["pipeline"]

    if os.getenv("ENABLE_CHECKPOINTS"):
        env_overrides.setdefault("pipeline", {})["enable_checkpoints"] = (
            os.getenv("ENABLE_CHECKPOINTS").lower() == "true"
        )

    # Create and validate configuration
    try:
        config = AppConfig(**env_overrides)
        return config
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}") from e
