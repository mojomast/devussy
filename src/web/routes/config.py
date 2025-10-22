"""
Configuration API routes for credential and settings management.

This module provides REST endpoints for:
- Credential CRUD operations (create, read, update, delete)
- Credential testing (validate API keys)
- Global configuration management
- Configuration presets
- Project-specific overrides
- Cost estimation
"""

import uuid
import logging
from typing import List, Optional, Dict
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..config_models import (
    ProviderCredentials,
    GlobalConfig,
    ProjectConfigOverride,
    ConfigPreset,
    CreateCredentialRequest,
    UpdateCredentialRequest,
    TestCredentialResponse,
    CostEstimate,
    CostEstimateRequest,
    ProviderType,
    PipelineStage,
    ModelConfig,
    StageConfig,
)
from ..security import get_secure_storage
from ..config_storage import get_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["Configuration"])

# Global instances
security = get_secure_storage()
storage = get_storage()


# Credential Management Endpoints

@router.post("/credentials", response_model=ProviderCredentials, status_code=status.HTTP_201_CREATED)
async def create_credential(request: CreateCredentialRequest):
    """
    Create a new API credential.
    
    The API key will be encrypted before storage and never returned in plaintext.
    """
    try:
        # Encrypt the API key
        encrypted_key = security.encrypt(request.api_key)
        
        # Create credential object
        credential = ProviderCredentials(
            id=f"cred_{uuid.uuid4().hex[:12]}",
            name=request.name,
            provider=request.provider,
            api_key_encrypted=encrypted_key,
            api_base=request.api_base,
            organization_id=request.organization_id,
            created_at=datetime.utcnow(),
            is_valid=False  # Not tested yet
        )
        
        # Save to storage
        storage.save_credential(credential)
        
        logger.info(f"Created credential: {credential.name} (ID: {credential.id})")
        
        return credential
        
    except Exception as e:
        logger.error(f"Failed to create credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create credential: {str(e)}"
        )


@router.get("/credentials", response_model=List[ProviderCredentials])
async def list_credentials():
    """
    List all stored credentials.
    
    API keys are always returned encrypted (never plaintext).
    """
    try:
        credentials = storage.load_all_credentials()
        return credentials
    except Exception as e:
        logger.error(f"Failed to list credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load credentials: {str(e)}"
        )


@router.get("/credentials/{credential_id}", response_model=ProviderCredentials)
async def get_credential(credential_id: str):
    """
    Get a specific credential by ID.
    
    API key is returned encrypted (never plaintext).
    """
    credential = storage.load_credential(credential_id)
    
    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credential not found: {credential_id}"
        )
    
    return credential


@router.put("/credentials/{credential_id}", response_model=ProviderCredentials)
async def update_credential(credential_id: str, request: UpdateCredentialRequest):
    """
    Update an existing credential.
    
    Only provided fields will be updated. If api_key is provided, it will be re-encrypted.
    """
    credential = storage.load_credential(credential_id)
    
    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credential not found: {credential_id}"
        )
    
    try:
        # Update fields if provided
        if request.name is not None:
            credential.name = request.name
        
        if request.api_key is not None:
            # Re-encrypt the new API key
            credential.api_key_encrypted = security.encrypt(request.api_key)
            # Mark as not tested since key changed
            credential.is_valid = False
            credential.last_tested = None
        
        if request.api_base is not None:
            credential.api_base = request.api_base
        
        if request.organization_id is not None:
            credential.organization_id = request.organization_id
        
        # Save updated credential
        storage.save_credential(credential)
        
        logger.info(f"Updated credential: {credential_id}")
        
        return credential
        
    except Exception as e:
        logger.error(f"Failed to update credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update credential: {str(e)}"
        )


@router.delete("/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(credential_id: str):
    """Delete a credential."""
    success = storage.delete_credential(credential_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credential not found: {credential_id}"
        )
    
    logger.info(f"Deleted credential: {credential_id}")
    return None


@router.post("/credentials/{credential_id}/test", response_model=TestCredentialResponse)
async def test_credential(credential_id: str):
    """
    Test if a credential is valid by making a test API request.
    
    Updates the credential's is_valid and last_tested fields.
    """
    credential = storage.load_credential(credential_id)
    
    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credential not found: {credential_id}"
        )
    
    try:
        # Decrypt the API key for testing
        api_key = security.decrypt(credential.api_key_encrypted)
        
        # Import here to avoid circular dependency
        from ...clients.factory import create_llm_client
        from ...config import LLMConfig, RetryConfig
        from types import SimpleNamespace
        
        # Create a test LLM config that matches what the clients expect
        # The clients expect config.llm.api_key, config.llm.model, etc.
        # Requesty uses OpenAI-compatible format with models like "openai/gpt-4o"
        if credential.provider == "openai":
            test_model = "gpt-3.5-turbo"
        elif credential.provider == "requesty":
            test_model = "openai/gpt-4o-mini"  # Use a cheap model for testing
        else:
            test_model = "test-model"
        
        llm_config = LLMConfig(
            provider=credential.provider,
            api_key=api_key,
            base_url=credential.api_base,
            org_id=credential.organization_id,
            model=test_model,
            temperature=0.7,
            max_tokens=10  # Just a tiny test
        )
        
        retry_config = RetryConfig(
            max_attempts=2,
            initial_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0
        )
        
        # Wrap in a namespace that matches the expected structure
        test_config = SimpleNamespace(
            llm=llm_config,
            retry=retry_config,
            max_concurrent_requests=1
        )
        
        # Create client and test
        client = create_llm_client(test_config)
        
        # Try a simple test request
        result = await client.generate_completion("Say 'OK' if you can read this.")
        
        # Update credential status
        credential.is_valid = True
        credential.last_tested = datetime.utcnow()
        storage.save_credential(credential)
        
        logger.info(f"Credential test successful: {credential_id}")
        
        return TestCredentialResponse(
            success=True,
            message="API key is valid and working",
            tested_at=credential.last_tested,
            details={"response_length": len(result)}
        )
        
    except Exception as e:
        logger.error(f"Credential test failed: {e}")
        
        # Update credential status
        credential.is_valid = False
        credential.last_tested = datetime.utcnow()
        storage.save_credential(credential)
        
        return TestCredentialResponse(
            success=False,
            message=f"API key test failed: {str(e)}",
            tested_at=credential.last_tested,
            details={"error": str(e)}
        )


@router.get("/credentials/{credential_id}/models")
async def list_available_models(credential_id: str):
    """
    List available models for a credential.
    
    Makes an API call to the provider to fetch available models.
    Currently supports Requesty provider.
    """
    credential = storage.load_credential(credential_id)
    
    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credential not found: {credential_id}"
        )
    
    try:
        # Decrypt the API key
        api_key = security.decrypt(credential.api_key_encrypted)
        
        # Handle different providers
        if credential.provider == "requesty":
            # Requesty models endpoint (OpenAI-compatible)
            import aiohttp
            
            base_url = credential.api_base or "https://router.requesty.ai/v1"
            models_endpoint = f"{base_url.rstrip('/')}/models"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(models_endpoint, headers=headers) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    
                    # Extract model list from response
                    # Requesty returns OpenAI format: {"data": [{"id": "provider/model", ...}]}
                    # or custom format: {"models": [...]}
                    models_list = data.get("data", data.get("models", []))
                    
                    return {
                        "success": True,
                        "provider": credential.provider,
                        "models": [
                            {
                                "id": m.get("id", m.get("name", "unknown")),
                                "name": m.get("name", m.get("id", "Unknown Model")),
                                "description": m.get("description", ""),
                                "context_window": m.get("context_window", m.get("max_tokens", 0))
                            }
                            for m in models_list
                        ]
                    }
        else:
            # For other providers, return a placeholder or error
            return {
                "success": False,
                "provider": credential.provider,
                "message": f"Model listing not yet implemented for {credential.provider}",
                "models": []
            }
    
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )


# Global Configuration Endpoints

@router.get("/global", response_model=GlobalConfig)
async def get_global_config():
    """
    Get the current global configuration.
    
    Returns default values if no config has been saved.
    """
    config = storage.load_global_config()
    
    if config is None:
        # Return a default config (user needs to set it up)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No global configuration found. Please set up your configuration first."
        )
    
    return config


@router.put("/global", response_model=GlobalConfig)
async def update_global_config(config: GlobalConfig):
    """
    Update the global configuration.
    
    This configuration applies to all projects unless overridden.
    """
    try:
        # Ensure ID is 'global'
        config.id = "global"
        
        # Save configuration
        storage.save_global_config(config)
        
        logger.info("Updated global configuration")
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to update global config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update global configuration: {str(e)}"
        )


# Preset Management Endpoints

@router.get("/presets", response_model=List[ConfigPreset])
async def list_presets():
    """
    List all available configuration presets.
    
    Includes both built-in and custom presets.
    """
    try:
        presets = storage.load_all_presets()
        return presets
    except Exception as e:
        logger.error(f"Failed to list presets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load presets: {str(e)}"
        )


@router.get("/presets/{preset_id}", response_model=ConfigPreset)
async def get_preset(preset_id: str):
    """Get a specific preset by ID."""
    preset = storage.load_preset(preset_id)
    
    if preset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset not found: {preset_id}"
        )
    
    return preset


@router.post("/presets/apply/{preset_id}", response_model=GlobalConfig)
async def apply_preset(preset_id: str):
    """
    Apply a preset to the global configuration.
    
    This will update the global config with the preset's settings.
    """
    preset = storage.load_preset(preset_id)
    
    if preset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset not found: {preset_id}"
        )
    
    try:
        # Load existing global config or create new one
        global_config = storage.load_global_config()
        
        if global_config is None:
            # Create new config from preset
            global_config = GlobalConfig(
                id="global",
                default_model_config=preset.default_model_config,
                stage_overrides=preset.stage_overrides
            )
        else:
            # Update existing config with preset values
            global_config.default_model_config = preset.default_model_config
            global_config.stage_overrides = preset.stage_overrides
        
        # Save updated config
        storage.save_global_config(global_config)
        
        logger.info(f"Applied preset: {preset_id}")
        
        return global_config
        
    except Exception as e:
        logger.error(f"Failed to apply preset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply preset: {str(e)}"
        )


# Project Configuration Override Endpoints

@router.get("/projects/{project_id}", response_model=Optional[ProjectConfigOverride])
async def get_project_config(project_id: str):
    """
    Get project-specific configuration overrides.
    
    Returns None if no override exists for this project.
    """
    override = storage.load_project_override(project_id)
    return override


@router.put("/projects/{project_id}", response_model=ProjectConfigOverride)
async def set_project_config(project_id: str, override: ProjectConfigOverride):
    """
    Set project-specific configuration overrides.
    
    This allows a project to use different models/settings than the global config.
    """
    try:
        # Ensure project_id matches
        override.project_id = project_id
        
        # Save override
        storage.save_project_override(override)
        
        logger.info(f"Set project override: {project_id}")
        
        return override
        
    except Exception as e:
        logger.error(f"Failed to set project override: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set project configuration: {str(e)}"
        )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_config(project_id: str):
    """Delete project-specific configuration overrides."""
    success = storage.delete_project_override(project_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No configuration override found for project: {project_id}"
        )
    
    logger.info(f"Deleted project override: {project_id}")
    return None


# Cost Estimation Endpoint

@router.post("/estimate-cost", response_model=CostEstimate)
async def estimate_cost(request: CostEstimateRequest):
    """
    Estimate the cost of running a project with given configuration.
    
    This provides a rough estimate based on token counts and model pricing.
    """
    try:
        # Simple estimation logic (can be enhanced)
        description_length = len(request.project_description)
        
        # Estimate tokens (rough: ~4 characters per token)
        estimated_input_tokens = description_length // 4
        
        # Estimate output tokens per stage (rough estimates)
        design_tokens = 3000
        devplan_tokens = 5000
        handoff_tokens = 2000
        total_tokens = estimated_input_tokens * 3 + design_tokens + devplan_tokens + handoff_tokens
        
        # Rough cost estimates (GPT-4: $0.03/1K input, $0.06/1K output)
        # Using average of $0.045/1K tokens
        estimated_cost = (total_tokens / 1000) * 0.045
        
        return CostEstimate(
            total_estimated_tokens=total_tokens,
            estimated_cost_usd=round(estimated_cost, 2),
            breakdown_by_stage={
                "design": {"tokens": design_tokens, "cost": round((design_tokens / 1000) * 0.045, 2)},
                "devplan": {"tokens": devplan_tokens, "cost": round((devplan_tokens / 1000) * 0.045, 2)},
                "handoff": {"tokens": handoff_tokens, "cost": round((handoff_tokens / 1000) * 0.045, 2)}
            }
        )
        
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate cost: {str(e)}"
        )


# Model Discovery Endpoint

@router.get("/models/{provider}")
async def list_models_by_provider(provider: ProviderType):
    """
    List available models for a provider.
    
    Returns a list of common models for the specified provider.
    """
    models_by_provider = {
        "openai": [
            {"id": "gpt-4-turbo-preview", "name": "GPT-4 Turbo", "cost_tier": "high"},
            {"id": "gpt-4", "name": "GPT-4", "cost_tier": "high"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "cost_tier": "low"},
            {"id": "gpt-3.5-turbo-16k", "name": "GPT-3.5 Turbo 16K", "cost_tier": "low"},
        ],
        "anthropic": [
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "cost_tier": "high"},
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "cost_tier": "medium"},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "cost_tier": "low"},
        ],
        "google": [
            {"id": "gemini-pro", "name": "Gemini Pro", "cost_tier": "medium"},
        ],
    }
    
    return models_by_provider.get(provider, [])
