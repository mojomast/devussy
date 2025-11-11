"""
Storage layer for configuration management.

Handles persistence of credentials, global config, presets, and project overrides
using JSON files with file locking for concurrent access safety.
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict
import logging
from datetime import datetime, timezone
from filelock import FileLock

from .config_models import (
    ProviderCredentials,
    GlobalConfig,
    ProjectConfigOverride,
    ConfigPreset,
    PipelineStage,
    ProjectTemplate,
)
from .security import get_secure_storage

logger = logging.getLogger(__name__)


class ConfigStorage:
    """
    Storage layer for configuration using JSON files.
    
    Directory structure:
        .config/
            global_config.json
            credentials/
                cred_abc123.json
                cred_def456.json
            presets/
                cost_optimized.json
                max_quality.json
                anthropic_claude.json
            projects/
                proj_abc123_override.json
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize storage layer.
        
        Args:
            config_dir: Base directory for configuration files.
                       Defaults to "./web_projects/.config"
        """
        if config_dir is None:
            config_dir = os.path.join(".", "web_projects", ".config")
        
        self.config_dir = Path(config_dir)
        self.credentials_dir = self.config_dir / "credentials"
        self.presets_dir = self.config_dir / "presets"
        self.projects_dir = self.config_dir / "projects"
        self.templates_dir = self.config_dir / "templates"
        
        # Create directories if they don't exist
        self._ensure_directories()
        
        # Security instance for masking
        self.security = get_secure_storage()
    
    def _ensure_directories(self):
        """Create configuration directories if they don't exist."""
        for directory in [self.config_dir, self.credentials_dir, 
                         self.presets_dir, self.projects_dir, self.templates_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_lock(self, file_path: Path) -> FileLock:
        """Get a file lock for safe concurrent access."""
        lock_path = f"{file_path}.lock"
        return FileLock(lock_path, timeout=10)
    
    def _read_json_file(self, file_path: Path) -> Optional[Dict]:
        """Read a JSON file with locking."""
        if not file_path.exists():
            return None
        
        try:
            with self._get_lock(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return None
    
    def _write_json_file(self, file_path: Path, data: Dict):
        """Write a JSON file with locking."""
        try:
            with self._get_lock(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to write {file_path}: {e}")
            raise ValueError(f"Failed to save configuration: {e}")
    
    # Credential Management
    
    def save_credential(self, credential: ProviderCredentials):
        """Save a credential to storage."""
        file_path = self.credentials_dir / f"{credential.id}.json"
        
        # Create a copy for storage (mask the key for logging)
        data = credential.model_dump()
        
        self._write_json_file(file_path, data)
        logger.info(f"Saved credential: {credential.name} (ID: {credential.id})")
    
    def load_credential(self, credential_id: str) -> Optional[ProviderCredentials]:
        """Load a credential by ID."""
        file_path = self.credentials_dir / f"{credential_id}.json"
        data = self._read_json_file(file_path)
        
        if data is None:
            return None
        
        try:
            return ProviderCredentials(**data)
        except Exception as e:
            logger.error(f"Failed to parse credential {credential_id}: {e}")
            return None
    
    def load_all_credentials(self) -> List[ProviderCredentials]:
        """Load all credentials."""
        credentials = []
        
        for file_path in self.credentials_dir.glob("*.json"):
            data = self._read_json_file(file_path)
            if data:
                try:
                    credentials.append(ProviderCredentials(**data))
                except Exception as e:
                    logger.error(f"Failed to parse credential {file_path.name}: {e}")
        
        return credentials
    
    def delete_credential(self, credential_id: str) -> bool:
        """Delete a credential."""
        file_path = self.credentials_dir / f"{credential_id}.json"
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            logger.info(f"Deleted credential: {credential_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete credential {credential_id}: {e}")
            return False
    
    def find_credentials_by_provider(self, provider: str) -> List[ProviderCredentials]:
        """Find all credentials for a specific provider."""
        all_creds = self.load_all_credentials()
        return [c for c in all_creds if c.provider == provider]
    
    # Global Configuration
    
    def save_global_config(self, config: GlobalConfig):
        """Save global configuration."""
        file_path = self.config_dir / "global_config.json"
        
        # Update timestamp
        config.updated_at = datetime.now(timezone.utc)
        
        data = config.model_dump()
        self._write_json_file(file_path, data)
        logger.info("Saved global configuration")
    
    def load_global_config(self) -> Optional[GlobalConfig]:
        """Load global configuration."""
        file_path = self.config_dir / "global_config.json"
        data = self._read_json_file(file_path)
        
        if data is None:
            logger.info("No global config found, will use defaults")
            return None
        
        try:
            return GlobalConfig(**data)
        except Exception as e:
            logger.error(f"Failed to parse global config: {e}")
            return None
    
    # Project Configuration Overrides
    
    def save_project_override(self, override: ProjectConfigOverride):
        """Save project-specific configuration override."""
        file_path = self.projects_dir / f"{override.project_id}_override.json"
        
        data = override.model_dump()
        self._write_json_file(file_path, data)
        logger.info(f"Saved project override for: {override.project_id}")
    
    def load_project_override(self, project_id: str) -> Optional[ProjectConfigOverride]:
        """Load project-specific configuration override."""
        file_path = self.projects_dir / f"{project_id}_override.json"
        data = self._read_json_file(file_path)
        
        if data is None:
            return None
        
        try:
            return ProjectConfigOverride(**data)
        except Exception as e:
            logger.error(f"Failed to parse project override {project_id}: {e}")
            return None
    
    def delete_project_override(self, project_id: str) -> bool:
        """Delete a project configuration override."""
        file_path = self.projects_dir / f"{project_id}_override.json"
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            logger.info(f"Deleted project override: {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete project override {project_id}: {e}")
            return False
    
    # Preset Management
    
    def save_preset(self, preset: ConfigPreset):
        """Save a configuration preset."""
        file_path = self.presets_dir / f"{preset.id}.json"
        
        data = preset.model_dump()
        self._write_json_file(file_path, data)
        logger.info(f"Saved preset: {preset.name} (ID: {preset.id})")
    
    def load_preset(self, preset_id: str) -> Optional[ConfigPreset]:
        """Load a configuration preset by ID."""
        file_path = self.presets_dir / f"{preset_id}.json"
        data = self._read_json_file(file_path)
        
        if data is None:
            return None
        
        try:
            return ConfigPreset(**data)
        except Exception as e:
            logger.error(f"Failed to parse preset {preset_id}: {e}")
            return None
    
    def load_all_presets(self) -> List[ConfigPreset]:
        """Load all configuration presets."""
        presets = []
        
        for file_path in self.presets_dir.glob("*.json"):
            data = self._read_json_file(file_path)
            if data:
                try:
                    presets.append(ConfigPreset(**data))
                except Exception as e:
                    logger.error(f"Failed to parse preset {file_path.name}: {e}")
        
        return presets
    
    def delete_preset(self, preset_id: str) -> bool:
        """Delete a configuration preset."""
        file_path = self.presets_dir / f"{preset_id}.json"
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            logger.info(f"Deleted preset: {preset_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete preset {preset_id}: {e}")
            return False
    
    # Template Management
    
    def save_template(self, template: ProjectTemplate) -> bool:
        """Save a project template."""
        file_path = self.templates_dir / f"{template.id}.json"
        
        try:
            data = template.model_dump(mode='json')
            self._write_json_file(file_path, data)
            logger.info(f"Saved template: {template.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save template {template.id}: {e}")
            return False
    
    def load_template(self, template_id: str) -> Optional[ProjectTemplate]:
        """Load a project template by ID."""
        file_path = self.templates_dir / f"{template_id}.json"
        data = self._read_json_file(file_path)
        
        if not data:
            return None
        
        try:
            return ProjectTemplate(**data)
        except Exception as e:
            logger.error(f"Failed to parse template {template_id}: {e}")
            return None
    
    def load_all_templates(self) -> List[ProjectTemplate]:
        """Load all project templates."""
        templates = []
        
        for file_path in self.templates_dir.glob("*.json"):
            data = self._read_json_file(file_path)
            if data:
                try:
                    templates.append(ProjectTemplate(**data))
                except Exception as e:
                    logger.error(f"Failed to parse template {file_path.name}: {e}")
        
        # Sort by usage count (most used first), then by name
        templates.sort(key=lambda t: (-t.usage_count, t.name))
        return templates
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a project template."""
        file_path = self.templates_dir / f"{template_id}.json"
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            logger.info(f"Deleted template: {template_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete template {template_id}: {e}")
            return False
    
    def increment_template_usage(self, template_id: str) -> bool:
        """Increment usage count for a template."""
        template = self.load_template(template_id)
        if not template:
            return False
        
        template.usage_count += 1
        template.last_used_at = datetime.now(timezone.utc)
        return self.save_template(template)


# Global storage instance
_storage: Optional[ConfigStorage] = None


def get_storage(config_dir: Optional[str] = None) -> ConfigStorage:
    """
    Get the global ConfigStorage instance (singleton pattern).
    
    Args:
        config_dir: Base directory for configuration files (only used on first call)
    
    Returns:
        The global ConfigStorage instance
    """
    global _storage
    if _storage is None:
        _storage = ConfigStorage(config_dir)
    return _storage
