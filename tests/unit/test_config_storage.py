"""
Unit tests for the configuration storage layer.
"""

import pytest
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone

from src.web.config_storage import ConfigStorage
from src.web.config_models import (
    ProviderCredentials,
    ProviderType,
    GlobalConfig,
    ModelConfig,
    StageConfig,
    PipelineStage,
    ProjectConfigOverride,
    ConfigPreset,
)
from src.web.security import get_secure_storage


class TestConfigStorage:
    """Tests for ConfigStorage class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Use a temporary test directory
        self.test_dir = Path("./test_config_storage")
        self.storage = ConfigStorage(str(self.test_dir))
        self.security = get_secure_storage()
    
    def teardown_method(self):
        """Clean up after each test."""
        # Remove test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    # Credential Tests
    
    def test_save_and_load_credential(self):
        """Test saving and loading a credential."""
        credential = ProviderCredentials(
            id="test_cred_1",
            name="Test OpenAI",
            provider=ProviderType.OPENAI,
            api_key_encrypted=self.security.encrypt("sk-test123"),
            created_at=datetime.now(timezone.utc),
        )
        
        # Save
        self.storage.save_credential(credential)
        
        # Load
        loaded = self.storage.load_credential("test_cred_1")
        
        assert loaded is not None
        assert loaded.id == credential.id
        assert loaded.name == credential.name
        assert loaded.provider == credential.provider
        assert loaded.api_key_encrypted == credential.api_key_encrypted
    
    def test_load_nonexistent_credential(self):
        """Test loading a credential that doesn't exist."""
        loaded = self.storage.load_credential("nonexistent")
        assert loaded is None
    
    def test_load_all_credentials(self):
        """Test loading all credentials."""
        # Create multiple credentials
        creds = [
            ProviderCredentials(
                id=f"cred_{i}",
                name=f"Test Cred {i}",
                provider=ProviderType.OPENAI,
                api_key_encrypted=self.security.encrypt(f"key-{i}"),
                created_at=datetime.now(timezone.utc),
            )
            for i in range(3)
        ]
        
        # Save all
        for cred in creds:
            self.storage.save_credential(cred)
        
        # Load all
        loaded = self.storage.load_all_credentials()
        
        assert len(loaded) == 3
        assert all(c.id in [cred.id for cred in creds] for c in loaded)
    
    def test_delete_credential(self):
        """Test deleting a credential."""
        credential = ProviderCredentials(
            id="test_delete",
            name="To Delete",
            provider=ProviderType.OPENAI,
            api_key_encrypted=self.security.encrypt("sk-delete"),
            created_at=datetime.now(timezone.utc),
        )
        
        # Save
        self.storage.save_credential(credential)
        
        # Delete
        result = self.storage.delete_credential("test_delete")
        assert result is True
        
        # Verify deleted
        loaded = self.storage.load_credential("test_delete")
        assert loaded is None
    
    def test_delete_nonexistent_credential(self):
        """Test deleting a credential that doesn't exist."""
        result = self.storage.delete_credential("nonexistent")
        assert result is False
    
    def test_find_credentials_by_provider(self):
        """Test finding credentials by provider type."""
        # Create credentials for different providers
        creds = [
            ProviderCredentials(
                id="openai_1",
                name="OpenAI 1",
                provider=ProviderType.OPENAI,
                api_key_encrypted=self.security.encrypt("key1"),
                created_at=datetime.now(timezone.utc),
            ),
            ProviderCredentials(
                id="openai_2",
                name="OpenAI 2",
                provider=ProviderType.OPENAI,
                api_key_encrypted=self.security.encrypt("key2"),
                created_at=datetime.now(timezone.utc),
            ),
            ProviderCredentials(
                id="anthropic_1",
                name="Anthropic 1",
                provider=ProviderType.ANTHROPIC,
                api_key_encrypted=self.security.encrypt("key3"),
                created_at=datetime.now(timezone.utc),
            ),
        ]
        
        # Save all
        for cred in creds:
            self.storage.save_credential(cred)
        
        # Find OpenAI credentials
        openai_creds = self.storage.find_credentials_by_provider("openai")
        assert len(openai_creds) == 2
        assert all(c.provider == ProviderType.OPENAI for c in openai_creds)
    
    # Global Config Tests
    
    def test_save_and_load_global_config(self):
        """Test saving and loading global configuration."""
        config = GlobalConfig(
            id="global",
            default_model_config=ModelConfig(
                provider_credential_id="test_cred",
                model_name="gpt-4",
                temperature=0.7,
                max_tokens=4096,
            ),
            max_concurrent_requests=10,
            output_dir="./test_output",
        )
        
        # Save
        self.storage.save_global_config(config)
        
        # Load
        loaded = self.storage.load_global_config()
        
        assert loaded is not None
        assert loaded.id == "global"
        assert loaded.default_model_config.model_name == "gpt-4"
        assert loaded.max_concurrent_requests == 10
    
    def test_load_nonexistent_global_config(self):
        """Test loading global config when none exists."""
        loaded = self.storage.load_global_config()
        assert loaded is None
    
    # Project Override Tests
    
    def test_save_and_load_project_override(self):
        """Test saving and loading project configuration override."""
        override = ProjectConfigOverride(
            project_id="proj_123",
            override_global=True,
            llm_config=ModelConfig(
                provider_credential_id="test_cred",
                model_name="gpt-3.5-turbo",
                temperature=0.5,
                max_tokens=2048,
            ),
            created_at=datetime.now(timezone.utc),
        )
        
        # Save
        self.storage.save_project_override(override)
        
        # Load
        loaded = self.storage.load_project_override("proj_123")
        
        assert loaded is not None
        assert loaded.project_id == "proj_123"
        assert loaded.override_global is True
        assert loaded.llm_config.model_name == "gpt-3.5-turbo"
    
    def test_delete_project_override(self):
        """Test deleting a project override."""
        override = ProjectConfigOverride(
            project_id="proj_delete",
            override_global=False,
            created_at=datetime.now(timezone.utc),
        )
        
        # Save
        self.storage.save_project_override(override)
        
        # Delete
        result = self.storage.delete_project_override("proj_delete")
        assert result is True
        
        # Verify deleted
        loaded = self.storage.load_project_override("proj_delete")
        assert loaded is None
    
    # Preset Tests
    
    def test_save_and_load_preset(self):
        """Test saving and loading a configuration preset."""
        preset = ConfigPreset(
            id="test_preset",
            name="Test Preset",
            description="A test preset",
            default_model_config=ModelConfig(
                provider_credential_id="test_cred",
                model_name="gpt-4",
                temperature=0.7,
                max_tokens=4096,
            ),
            estimated_cost_per_project="$1.00",
        )
        
        # Save
        self.storage.save_preset(preset)
        
        # Load
        loaded = self.storage.load_preset("test_preset")
        
        assert loaded is not None
        assert loaded.id == "test_preset"
        assert loaded.name == "Test Preset"
        assert loaded.default_model_config.model_name == "gpt-4"
    
    def test_load_all_presets(self):
        """Test loading all presets."""
        # Create multiple presets
        presets = [
            ConfigPreset(
                id=f"preset_{i}",
                name=f"Preset {i}",
                description=f"Description {i}",
                default_model_config=ModelConfig(
                    provider_credential_id="test_cred",
                    model_name="gpt-4",
                    temperature=0.7,
                    max_tokens=4096,
                ),
            )
            for i in range(3)
        ]
        
        # Save all
        for preset in presets:
            self.storage.save_preset(preset)
        
        # Load all
        loaded = self.storage.load_all_presets()
        
        assert len(loaded) == 3
        assert all(p.id in [preset.id for preset in presets] for p in loaded)
    
    def test_delete_preset(self):
        """Test deleting a preset."""
        preset = ConfigPreset(
            id="preset_delete",
            name="To Delete",
            description="Will be deleted",
            default_model_config=ModelConfig(
                provider_credential_id="test_cred",
                model_name="gpt-4",
                temperature=0.7,
                max_tokens=4096,
            ),
        )
        
        # Save
        self.storage.save_preset(preset)
        
        # Delete
        result = self.storage.delete_preset("preset_delete")
        assert result is True
        
        # Verify deleted
        loaded = self.storage.load_preset("preset_delete")
        assert loaded is None


class TestConfigStorageDirectories:
    """Tests for directory structure and initialization."""
    
    def test_ensure_directories_created(self):
        """Test that all necessary directories are created."""
        test_dir = Path("./test_dir_creation")
        storage = ConfigStorage(str(test_dir))
        
        try:
            assert test_dir.exists()
            assert (test_dir / "credentials").exists()
            assert (test_dir / "presets").exists()
            assert (test_dir / "projects").exists()
        finally:
            if test_dir.exists():
                shutil.rmtree(test_dir)
