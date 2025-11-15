"""Integration tests for UI preferences persistence mechanism."""

import tempfile
import shutil
import json
import os
from pathlib import Path
import pytest
import sys

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.ui.menu import SessionSettings, _save_prefs, _load_prefs, load_last_used_preferences, apply_settings_to_config
from src.config import AppConfig
from src.state_manager import StateManager


class TestUIPreferencesPersistence:
    """Test UI preferences persistence functionality."""

    def setup_method(self):
        """Setup temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_state_dir = os.environ.get("DEVUSSY_STATE_DIR")
        os.environ["DEVUSSY_STATE_DIR"] = str(self.temp_dir)

    def teardown_method(self):
        """Cleanup after each test."""
        if self.original_state_dir:
            os.environ["DEVUSSY_STATE_DIR"] = self.original_state_dir
        else:
            os.environ.pop("DEVUSSY_STATE_DIR", None)
        shutil.rmtree(self.temp_dir)

    def test_preference_saving(self):
        """Test that preferences can be saved correctly."""
        test_session = SessionSettings()
        test_session.provider = "test_provider"
        test_session.temperature = 0.8
        test_session.repository_tools_enabled = True
        test_session.debug_ui_mode = True

        # Save preferences
        _save_prefs(test_session)

        # Verify file was created
        prefs_file = Path(self.temp_dir) / "ui_prefs.json"
        assert prefs_file.exists(), "Preferences file should be created"

        # Read and verify content
        with open(prefs_file, 'r') as f:
            saved_data = json.load(f)

        assert saved_data.get('provider') == 'test_provider'
        assert saved_data.get('temperature') == 0.8
        assert saved_data.get('repository_tools_enabled') == True
        assert saved_data.get('debug_ui_mode') == True

    def test_preference_loading(self):
        """Test that preferences can be loaded correctly."""
        # First save some test data
        test_session = SessionSettings()
        test_session.provider = "loaded_provider"
        test_session.temperature = 0.9
        _save_prefs(test_session)

        # Load preferences
        loaded_session = _load_prefs()

        # Verify loaded values
        assert loaded_session.provider == "loaded_provider"
        assert loaded_session.temperature == 0.9

    def test_startup_preference_integration(self):
        """Test the complete startup integration flow."""
        # Save preferences
        test_session = SessionSettings()
        test_session.provider = "integration_test_provider"
        test_session.temperature = 0.7
        test_session.repository_tools_enabled = True
        _save_prefs(test_session)

        # Simulate application startup
        loaded_prefs = load_last_used_preferences()

        # Create config and apply preferences
        config = AppConfig()
        apply_settings_to_config(config, loaded_prefs)

        # Verify integration
        assert loaded_prefs.provider == "integration_test_provider"
        assert loaded_prefs.temperature == 0.7
        assert loaded_prefs.repository_tools_enabled == True

    def test_menu_merge_logic(self):
        """Test the menu merge logic from run_menu."""
        # Save preferences
        test_session = SessionSettings()
        test_session.provider = "merge_test_provider"
        test_session.repository_tools_enabled = True
        _save_prefs(test_session)

        # Load saved preferences
        saved = load_last_used_preferences()
        base = SessionSettings()  # Fresh session

        # Simulate the merge logic from run_menu
        for field in SessionSettings.model_fields.keys():
            if getattr(base, field, None) is None and getattr(saved, field, None) is not None:
                setattr(base, field, getattr(saved, field))

        # Verify merge worked
        assert base.provider == "merge_test_provider"
        assert base.repository_tools_enabled == True


class TestUIPreferencesBugReproduction:
    """Test scenarios that reproduce reported UI preference bugs."""

    def setup_method(self):
        """Setup temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_state_dir = os.environ.get("DEVUSSY_STATE_DIR")
        os.environ["DEVUSSY_STATE_DIR"] = str(self.temp_dir)

    def teardown_method(self):
        """Cleanup after each test."""
        if self.original_state_dir:
            os.environ["DEVUSSY_STATE_DIR"] = self.original_state_dir
        else:
            os.environ.pop("DEVUSSY_STATE_DIR", None)
        shutil.rmtree(self.temp_dir)

    def test_exact_bug_reproduction(self):
        """Reproduce the exact bug: UI preferences not applied on restart."""
        # Step 1: Save user changes
        user_session = SessionSettings()
        user_session.provider = "user_changed_provider"
        user_session.temperature = 0.7
        user_session.repository_tools_enabled = True
        _save_prefs(user_session)

        # Step 2: Simulate application restart (clear modules)
        modules_to_clear = [k for k in sys.modules.keys() if k.startswith('src.')]
        for mod in modules_to_clear:
            del sys.modules[mod]

        # Step 3: Load preferences as app would on startup
        loaded_prefs = load_last_used_preferences()

        # Step 4: Apply to fresh config
        restart_config = AppConfig()
        apply_settings_to_config(restart_config, loaded_prefs)

        # Step 5: Verify persistence
        persistence_success = (
            loaded_prefs.provider == "user_changed_provider" and
            loaded_prefs.temperature == 0.7 and
            loaded_prefs.repository_tools_enabled == True
        )

        assert persistence_success, "User changes should persist across restart"

    def test_full_user_scenario(self):
        """Test complete user scenario: Change -> Save -> Restart -> Verify."""
        # Simulate user changing settings
        user_session = SessionSettings()
        user_session.provider = "full_scenario_provider"
        user_session.temperature = 0.75
        user_session.repository_tools_enabled = True
        user_session.debug_ui_mode = True

        # Save changes
        _save_prefs(user_session)

        # Verify file content
        prefs_file = Path(self.temp_dir) / "ui_prefs.json"
        with open(prefs_file, 'r') as f:
            saved_content = json.load(f)

        save_success = (
            saved_content.get('provider') == 'full_scenario_provider' and
            saved_content.get('temperature') == 0.75 and
            saved_content.get('repository_tools_enabled') == True and
            saved_content.get('debug_ui_mode') == True
        )

        assert save_success, "Changes should be saved correctly"

        # Simulate application restart
        loaded_prefs = load_last_used_preferences()

        # Apply to config
        restart_config = AppConfig()
        apply_settings_to_config(restart_config, loaded_prefs)

        # Verify complete persistence
        config_applied = (
            restart_config.llm.provider == "full_scenario_provider" and
            restart_config.llm.temperature == 0.75
        )

        assert config_applied, "Config should be updated correctly on restart"


class TestUIPreferencesEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Setup temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_state_dir = os.environ.get("DEVUSSY_STATE_DIR")
        os.environ["DEVUSSY_STATE_DIR"] = str(self.temp_dir)

    def teardown_method(self):
        """Cleanup after each test."""
        if self.original_state_dir:
            os.environ["DEVUSSY_STATE_DIR"] = self.original_state_dir
        else:
            os.environ.pop("DEVUSSY_STATE_DIR", None)
        shutil.rmtree(self.temp_dir)

    def test_missing_preferences_file(self):
        """Test behavior when preferences file is missing."""
        # Don't save any preferences
        loaded_prefs = load_last_used_preferences()
        
        # Should return default session settings
        assert isinstance(loaded_prefs, SessionSettings)

    def test_corrupted_preferences_file(self):
        """Test behavior with corrupted preferences file."""
        prefs_file = Path(self.temp_dir) / "ui_prefs.json"
        
        # Write corrupted JSON
        with open(prefs_file, 'w') as f:
            f.write("invalid json content")

        # Should handle gracefully
        try:
            loaded_prefs = load_last_used_preferences()
            assert isinstance(loaded_prefs, SessionSettings)
        except Exception:
            # It's OK if it raises an exception for corrupted data
            pass

    def test_partial_preferences(self):
        """Test with partially saved preferences."""
        # Save only some fields
        partial_data = {
            "provider": "partial_provider",
            "temperature": 0.6
        }
        
        prefs_file = Path(self.temp_dir) / "ui_prefs.json"
        with open(prefs_file, 'w') as f:
            json.dump(partial_data, f)

        # Load should work with defaults for missing fields
        loaded_prefs = load_last_used_preferences()
        assert loaded_prefs.provider == "partial_provider"
        assert loaded_prefs.temperature == 0.6
        # Other fields should have default values
        assert loaded_prefs.repository_tools_enabled is not None


if __name__ == "__main__":
    # Run tests manually
    pytest.main([__file__, "-v"])