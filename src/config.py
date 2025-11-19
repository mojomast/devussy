"""Configuration loader for DevPlan Orchestrator."""

import os
import json
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
        default=600, ge=1, description="API request timeout in seconds"
    )
    reasoning_effort: Optional[str] = Field(
        default=None,
        description="Reasoning effort for GPT-5 models (one of: low, medium, high)",
    )
    spoof_as: Optional[str] = Field(default=None, description="AgentRouter spoof profile")
    extra_headers: Optional[dict] = Field(default=None, description="Provider-specific extra headers")
    streaming_enabled: bool = Field(default=False, description="Enable token streaming for this stage")
    
    # Per-stage model overrides (Phase 18/20)
    design_model: Optional[str] = Field(
        default=None, description="Model override for Design stage"
    )
    devplan_model: Optional[str] = Field(
        default=None, description="Model override for DevPlan stages"
    )
    handoff_model: Optional[str] = Field(
        default=None, description="Model override for Handoff stage"
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is one of the supported options."""
        allowed = ["openai", "generic", "aether", "agentrouter", "requesty"]
        if v.lower() not in allowed:
            raise ValueError(f"Provider must be one of {allowed}, got: {v}")
        return v.lower()

    @field_validator("reasoning_effort")
    @classmethod
    def validate_reasoning_effort(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        allowed = {"low", "medium", "high"}
        if str(v).lower() not in allowed:
            raise ValueError(f"reasoning_effort must be one of {sorted(allowed)} or None, got: {v}")
        return str(v).lower()

    @field_validator("spoof_as")
    @classmethod
    def validate_spoof_as(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        allowed = {"roocode", "claude-code", "codex"}
        val = str(v).lower()
        if val not in allowed:
            raise ValueError(f"spoof_as must be one of {sorted(allowed)} or None, got: {v}")
        return val

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


class DetourConfig(BaseModel):
    """Feature flags for detour experimentation."""

    enabled: bool = Field(
        default=False, description="Enable detour experimentation features"
    )
    instrumentation_enabled: bool = Field(
        default=False,
        description="Enable detour instrumentation (timing, counters, metadata logging)",
    )

    metadata_logging_enabled: bool = Field(
        default=False,
        description="Enable detailed metadata persistence logging",
    )


class AppConfig(BaseModel):
    """Main application configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    documentation: DocumentationConfig = Field(default_factory=DocumentationConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    detour: DetourConfig = Field(default_factory=DetourConfig)

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
        """Validate and normalize log level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Log level must be one of {sorted(allowed)}, got: {v}")
        return v_upper

    def get_llm_config_for_stage(self, stage: str) -> LLMConfig:
        """Return the effective LLM config for a pipeline stage.

        Args:
            stage: Name of the stage (e.g. "design", "devplan", "handoff")

        Returns:
            LLMConfig merged with any stage-specific override.
        """

        stage = (stage or "").lower()
        override_map = {
            "design": self.design_llm,
            "devplan": self.devplan_llm,
            "handoff": self.handoff_llm,
        }

        override = override_map.get(stage)
        return self.llm.merge_with(override)


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
    # Load .env.local for local overrides (gitignored)
    load_dotenv(".env.local", override=True)

    # Determine config file path
    if config_path is None:
        env_path = os.getenv("CONFIG_PATH")
        if env_path:
            config_path = env_path
        else:
            # Default to project_root/config/config.yaml
            # src/config.py -> project_root is parent of parent
            project_root = Path(__file__).resolve().parent.parent
            config_path = str(project_root / "config" / "config.yaml")

    config_file = Path(config_path)
    if not config_file.exists():
        # Fallback: try relative to CWD if absolute resolve failed or wasn't used
        if not config_file.is_absolute():
             config_file = Path.cwd() / config_path
        
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
        """Load LLM configuration with optional prefix for stage-specific configs.

        Env design:
        - Global (no prefix):
            - Provider: llm_provider (YAML) -> LLM_PROVIDER.
            - Model: model (YAML) -> MODEL (canonical).
            - FINAL_MODEL is not applied here; final-phase code may read it separately.
        - Stage-specific (design_, devplan_, handoff_):
            - Provider: {prefix}llm_provider -> {PREFIX}LLM_PROVIDER.
            - Model: {prefix}model -> {PREFIX}MODEL.
            - API key: {PREFIX}API_KEY.
            - Base URL: {PREFIX}BASE_URL.
        """
        llm_config: dict = {}

        # Provider
        provider_key = f"{prefix}llm_provider" if prefix else "llm_provider"
        env_provider_key = f"{prefix.upper()}LLM_PROVIDER" if prefix else "LLM_PROVIDER"

        if provider_key in config_data:
            llm_config["provider"] = config_data[provider_key]
        env_provider_val = os.getenv(env_provider_key)
        if env_provider_val:
            llm_config["provider"] = env_provider_val

        # Model
        model_key = f"{prefix}model" if prefix else "model"

        if prefix:
            # Stage-specific: YAML {prefix}model, then {PREFIX}MODEL
            env_model_key = f"{prefix.upper()}MODEL"
            if model_key in config_data:
                llm_config["model"] = config_data[model_key]
            env_model_val = os.getenv(env_model_key)
            if env_model_val:
                llm_config["model"] = env_model_val
        else:
            # Global: YAML model, then MODEL as canonical override
            if "model" in config_data:
                llm_config["model"] = config_data["model"]
            model_env = os.getenv("MODEL")
            if model_env:
                llm_config["model"] = model_env

        # API Key (global, provider-based)
        if not prefix:
            provider = llm_config.get("provider") or config_data.get("llm_provider", "openai")

            if provider == "requesty" and os.getenv("REQUESTY_API_KEY"):
                llm_config["api_key"] = os.getenv("REQUESTY_API_KEY")
            elif provider == "aether" and os.getenv("AETHER_API_KEY"):
                llm_config["api_key"] = os.getenv("AETHER_API_KEY")
            elif provider == "agentrouter" and os.getenv("AGENTROUTER_API_KEY"):
                llm_config["api_key"] = os.getenv("AGENTROUTER_API_KEY")
            elif provider == "openai" and os.getenv("OPENAI_API_KEY"):
                llm_config["api_key"] = os.getenv("OPENAI_API_KEY")
            elif provider == "generic" and os.getenv("GENERIC_API_KEY"):
                llm_config["api_key"] = os.getenv("GENERIC_API_KEY")
            # Legacy fallback: accept any known key
            elif os.getenv("OPENAI_API_KEY"):
                llm_config["api_key"] = os.getenv("OPENAI_API_KEY")
            elif os.getenv("REQUESTY_API_KEY"):
                llm_config["api_key"] = os.getenv("REQUESTY_API_KEY")
            elif os.getenv("AETHER_API_KEY"):
                llm_config["api_key"] = os.getenv("AETHER_API_KEY")
            elif os.getenv("AGENTROUTER_API_KEY"):
                llm_config["api_key"] = os.getenv("AGENTROUTER_API_KEY")
            elif os.getenv("GENERIC_API_KEY"):
                llm_config["api_key"] = os.getenv("GENERIC_API_KEY")

        # Stage-specific API key override
        if prefix:
            api_key_env = f"{prefix.upper()}API_KEY"
            api_key_val = os.getenv(api_key_env)
            if api_key_val:
                llm_config["api_key"] = api_key_val

        # Organization ID
        if not prefix:
            org = os.getenv("OPENAI_ORG_ID")
            if org:
                llm_config["org_id"] = org
        else:
            org_id_env = f"{prefix.upper()}ORG_ID"
            org_val = os.getenv(org_id_env)
            if org_val:
                llm_config["org_id"] = org_val

        # Base URL
        if not prefix:
            provider_for_base = (llm_config.get("provider") or config_data.get("llm_provider") or "").lower()

            if provider_for_base == "generic":
                gen_base = os.getenv("GENERIC_BASE_URL")
                if gen_base:
                    llm_config["base_url"] = gen_base
                elif "base_url" in config_data:
                    llm_config["base_url"] = config_data["base_url"]
            elif provider_for_base == "aether":
                abase = os.getenv("AETHER_BASE_URL")
                if abase:
                    llm_config["base_url"] = abase
            elif provider_for_base == "agentrouter":
                rbase = os.getenv("AGENTROUTER_BASE_URL")
                if rbase:
                    llm_config["base_url"] = rbase
            elif provider_for_base == "requesty":
                rbase = os.getenv("REQUESTY_BASE_URL")
                if rbase:
                    llm_config["base_url"] = rbase
            elif provider_for_base == "openai":
                obase = os.getenv("OPENAI_BASE_URL")
                if obase:
                    llm_config["base_url"] = obase

        base_url_env = f"{prefix.upper()}BASE_URL" if prefix else None
        if base_url_env:
            bval = os.getenv(base_url_env)
            if bval:
                llm_config["base_url"] = bval

        # AgentRouter extras (global only)
        if not prefix and ((llm_config.get("provider") or "").lower() == "agentrouter" or os.getenv("LLM_PROVIDER", "").lower() == "agentrouter"):
            spoof = os.getenv("AGENTROUTER_SPOOF_AS")
            if spoof:
                llm_config["spoof_as"] = spoof
            extra_headers_raw = os.getenv("AGENTROUTER_EXTRA_HEADERS")
            if extra_headers_raw:
                try:
                    llm_config["extra_headers"] = json.loads(extra_headers_raw)
                except Exception:
                    pass

        # Temperature, max_tokens, api_timeout, reasoning_effort
        temp_key = f"{prefix}temperature" if prefix else "temperature"
        if temp_key in config_data:
            llm_config["temperature"] = config_data[temp_key]

        tokens_key = f"{prefix}max_tokens" if prefix else "max_tokens"
        if tokens_key in config_data:
            llm_config["max_tokens"] = config_data[tokens_key]

        timeout_key = f"{prefix}api_timeout" if prefix else "api_timeout"
        if timeout_key in config_data:
            llm_config["api_timeout"] = config_data[timeout_key]

        reasoning_key = f"{prefix}reasoning_effort" if prefix else "reasoning_effort"
        if reasoning_key in config_data:
            llm_config["reasoning_effort"] = config_data[reasoning_key]

        return llm_config
    
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

    # Detour configuration
    if "detour" in config_data:
        env_overrides["detour"] = config_data["detour"]
    
    # Detour environment variable overrides
    if os.getenv("DETOUR_ENABLED"):
        env_overrides.setdefault("detour", {})["enabled"] = (
            os.getenv("DETOUR_ENABLED").lower() == "true"
        )
    if os.getenv("DETOUR_INSTRUMENTATION_ENABLED"):
        env_overrides.setdefault("detour", {})["instrumentation_enabled"] = (
            os.getenv("DETOUR_INSTRUMENTATION_ENABLED").lower() == "true"
        )
    if os.getenv("DETOUR_METADATA_LOGGING_ENABLED"):
        env_overrides.setdefault("detour", {})["metadata_logging_enabled"] = (
            os.getenv("DETOUR_METADATA_LOGGING_ENABLED").lower() == "true"
        )

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
