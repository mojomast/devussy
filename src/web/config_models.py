"""
Configuration models for web-based LLM configuration management.

These models define the structure for storing and managing:
- API credentials (encrypted)
- Model configurations (per-stage and global)
- Configuration presets
- Project-specific overrides
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class ProviderType(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    GENERIC = "generic"
    REQUESTY = "requesty"


class PipelineStage(str, Enum):
    """Pipeline stages that can have custom configurations."""
    DESIGN = "design"
    DEVPLAN = "devplan"
    HANDOFF = "handoff"


class ProviderCredentials(BaseModel):
    """
    Secure storage for provider API keys and endpoints.
    
    API keys are always stored encrypted. When retrieving credentials,
    the api_key_encrypted field contains the encrypted key, never the plaintext.
    """
    id: str = Field(..., description="Unique credential ID")
    name: str = Field(..., description="User-friendly name (e.g., 'OpenAI - Production')")
    provider: ProviderType = Field(..., description="LLM provider type")
    api_key_encrypted: str = Field(..., description="Encrypted API key (never plaintext)")
    api_base: Optional[str] = Field(None, description="Custom API endpoint URL")
    organization_id: Optional[str] = Field(None, description="Organization ID (for OpenAI orgs)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    last_tested: Optional[datetime] = Field(None, description="Last successful test timestamp")
    is_valid: bool = Field(default=False, description="Whether the API key was successfully tested")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "cred_abc123",
                "name": "OpenAI - Production",
                "provider": "openai",
                "api_key_encrypted": "gAAAAA...",  # Encrypted
                "api_base": None,
                "organization_id": "org-123",
                "created_at": "2025-10-21T12:00:00Z",
                "last_tested": "2025-10-21T12:05:00Z",
                "is_valid": True
            }
        }
    }


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    provider_credential_id: str = Field(..., description="References ProviderCredentials.id")
    model_name: str = Field(..., description="Model identifier (e.g., 'gpt-4', 'claude-3-opus')")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=4096, ge=1, le=128000, description="Maximum tokens in response")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Presence penalty")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "provider_credential_id": "cred_abc123",
                "model_name": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
        }
    }


class StageConfig(BaseModel):
    """Configuration for a specific pipeline stage."""
    stage: PipelineStage = Field(..., description="Pipeline stage (design, devplan, handoff)")
    llm_config: ModelConfig = Field(..., description="Model configuration for this stage")
    enabled: bool = Field(default=True, description="Whether this stage is enabled")
    timeout: int = Field(default=60, ge=1, description="Timeout in seconds")
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")


class AvailableModel(BaseModel):
    """Information about an available model from a provider."""
    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(default="", description="Model description")
    context_window: int = Field(default=0, description="Maximum context window size")


class GlobalConfig(BaseModel):
    """
    Global configuration that applies to all projects.
    
    Can be overridden per-stage or per-project.
    """
    id: str = Field(default="global", description="Config ID (always 'global')")
    default_model_config: ModelConfig = Field(..., description="Default model for all stages")
    stage_overrides: Dict[PipelineStage, StageConfig] = Field(
        default_factory=dict, 
        description="Per-stage configuration overrides"
    )
    
    # Retry settings
    retry_initial_delay: float = Field(default=1.0, ge=0.1, description="Initial retry delay (seconds)")
    retry_max_delay: float = Field(default=60.0, ge=1.0, description="Maximum retry delay (seconds)")
    retry_exponential_base: float = Field(default=2.0, ge=1.1, description="Exponential backoff base")
    
    # Concurrency
    max_concurrent_requests: int = Field(default=5, ge=1, description="Max concurrent API requests")
    
    # Output settings
    output_dir: str = Field(default="./web_projects", description="Output directory for projects")
    enable_git: bool = Field(default=True, description="Enable git commits")
    enable_streaming: bool = Field(default=True, description="Enable streaming responses")
    
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class ProjectConfigOverride(BaseModel):
    """
    Per-project configuration overrides.
    
    Allows projects to use different models/settings than global config.
    """
    project_id: str = Field(..., description="Project ID this config applies to")
    override_global: bool = Field(default=False, description="Whether to override global config")
    llm_config: Optional[ModelConfig] = Field(None, description="Custom model config for this project")
    stage_overrides: Dict[PipelineStage, StageConfig] = Field(
        default_factory=dict,
        description="Per-stage overrides for this project"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class ConfigPreset(BaseModel):
    """
    Preset configuration for common use cases.
    
    Presets allow quick setup of common configurations without
    manual configuration of each setting.
    """
    id: str = Field(..., description="Preset ID")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Description of this preset")
    default_model_config: ModelConfig = Field(..., description="Default model configuration")
    stage_overrides: Dict[PipelineStage, StageConfig] = Field(
        default_factory=dict,
        description="Per-stage configuration overrides"
    )
    estimated_cost_per_project: Optional[str] = Field(
        None,
        description="Estimated cost (e.g., '$0.50 per project')"
    )


class CostEstimate(BaseModel):
    """Cost estimation for a project with given configuration."""
    total_estimated_tokens: int = Field(..., description="Estimated total tokens (input + output)")
    estimated_cost_usd: float = Field(..., description="Estimated cost in USD")
    breakdown_by_stage: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Cost breakdown by stage {stage: {tokens: X, cost: Y}}"
    )


# Request/Response models for API endpoints

class CreateCredentialRequest(BaseModel):
    """Request to create a new credential."""
    name: str = Field(..., description="User-friendly name")
    provider: ProviderType = Field(..., description="LLM provider")
    api_key: str = Field(..., description="API key (will be encrypted)")
    api_base: Optional[str] = Field(None, description="Custom endpoint URL")
    organization_id: Optional[str] = Field(None, description="Organization ID")


class UpdateCredentialRequest(BaseModel):
    """Request to update an existing credential."""
    name: Optional[str] = Field(None, description="User-friendly name")
    api_key: Optional[str] = Field(None, description="New API key (will be encrypted)")
    api_base: Optional[str] = Field(None, description="Custom endpoint URL")
    organization_id: Optional[str] = Field(None, description="Organization ID")


class TestCredentialResponse(BaseModel):
    """Response from testing a credential."""
    success: bool = Field(..., description="Whether the test succeeded")
    message: str = Field(..., description="Success/error message")
    tested_at: datetime = Field(default_factory=datetime.utcnow, description="Test timestamp")
    details: Optional[Dict] = Field(None, description="Additional test details")


class CostEstimateRequest(BaseModel):
    """Request to estimate project cost."""
    project_description: str = Field(..., description="Project description/requirements")
    llm_config: Optional[ModelConfig] = Field(None, description="Custom model config (optional)")
    stage_configs: Optional[Dict[PipelineStage, StageConfig]] = Field(
        None,
        description="Per-stage configs (optional)"
    )


class ProjectTemplate(BaseModel):
    """
    Saved project template for quick project creation.
    
    Templates save successful project configurations for reuse.
    """
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    
    # Configuration from the original project
    llm_config: Optional[ModelConfig] = Field(None, description="Model configuration")
    stage_overrides: Dict[PipelineStage, StageConfig] = Field(
        default_factory=dict,
        description="Per-stage configuration overrides"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    created_from_project_id: Optional[str] = Field(None, description="Source project ID if created from project")
    usage_count: int = Field(default=0, description="Number of times used")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    
    # Optional tags for organization
    tags: List[str] = Field(default_factory=list, description="Template tags (e.g., ['web', 'python'])")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "tpl_abc123",
                "name": "Full-Stack Web App",
                "description": "Template for full-stack web applications with React + FastAPI",
                "llm_config": {
                    "provider_credential_id": "cred_abc123",
                    "model_name": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 4096
                },
                "stage_overrides": {},
                "created_at": "2025-10-21T12:00:00Z",
                "usage_count": 5,
                "tags": ["web", "fullstack", "react", "python"]
            }
        }
    }


class CreateTemplateRequest(BaseModel):
    """Request to create a new template."""
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    llm_config: Optional[ModelConfig] = Field(None, description="Model configuration")
    stage_overrides: Dict[PipelineStage, StageConfig] = Field(
        default_factory=dict,
        description="Per-stage configuration overrides"
    )
    tags: List[str] = Field(default_factory=list, description="Template tags")


class UpdateTemplateRequest(BaseModel):
    """Request to update an existing template."""
    name: Optional[str] = Field(None, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    llm_config: Optional[ModelConfig] = Field(None, description="Model configuration")
    stage_overrides: Optional[Dict[PipelineStage, StageConfig]] = Field(
        None,
        description="Per-stage configuration overrides"
    )
    tags: Optional[List[str]] = Field(None, description="Template tags")
