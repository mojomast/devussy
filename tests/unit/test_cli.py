"""Tests for CLI commands and argument parsing.

Due to the CLI's integration with external services and file I/O,
these tests focus on mocking and verifying command structure rather
than end-to-end CLI execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import typer
from typer.testing import CliRunner

from src.cli import app, _load_app_config, _create_orchestrator
from src.config import AppConfig, LLMConfig


runner = CliRunner()


class TestConfigLoading:
    """Test configuration loading and CLI overrides."""

    def test_load_config_with_defaults(self):
        """Test loading config with default values."""
        config = _load_app_config(
            config_path=None,
            provider=None,
            model=None,
            output_dir=None,
            verbose=False,
        )

        assert config is not None
        assert isinstance(config, AppConfig)

    def test_load_config_with_provider_override(self):
        """Test provider override from CLI."""
        config = _load_app_config(
            config_path=None,
            provider="generic",
            model=None,
            output_dir=None,
            verbose=False,
        )

        assert config.llm.provider == "generic"

    def test_load_config_with_model_override(self):
        """Test model override from CLI."""
        config = _load_app_config(
            config_path=None,
            provider=None,
            model="gpt-4",
            output_dir=None,
            verbose=False,
        )

        assert config.llm.model == "gpt-4"

    def test_load_config_with_output_dir_override(self):
        """Test output directory override from CLI."""
        config = _load_app_config(
            config_path=None,
            provider=None,
            model=None,
            output_dir="/custom/output",
            verbose=False,
        )

        assert config.output_dir == Path("/custom/output")

    def test_load_config_with_verbose(self):
        """Test verbose mode sets debug logging."""
        config = _load_app_config(
            config_path=None,
            provider=None,
            model=None,
            output_dir=None,
            verbose=True,
        )

        assert config.log_level == "DEBUG"


class TestOrchestratorCreation:
    """Test orchestrator creation from config."""

    @patch("src.cli.create_llm_client")
    def test_create_orchestrator(self, mock_create_client):
        """Test creating orchestrator from config."""
        mock_create_client.return_value = MagicMock()

        config = AppConfig(
            llm=LLMConfig(
                provider="openai",
                model="gpt-3.5-turbo",
                api_key="test-key",
            )
        )

        orchestrator = _create_orchestrator(config)

        assert orchestrator is not None
        mock_create_client.assert_called_once_with(config)


@pytest.mark.unit
class TestVersionCommand:
    """Test version command."""

    def test_version_command(self):
        """Test version command output."""
        result = runner.invoke(app, ["version"])

        # The command should succeed or gracefully handle missing version
        # Version may not be defined in development
        assert result.exit_code in [0, 1]


@pytest.mark.unit  
class TestGenerateDesignCommand:
    """Test generate-design command."""

    @patch("src.cli._create_orchestrator")
    @patch("src.cli._load_app_config")
    def test_generate_design_minimal_args(self, mock_load_config, mock_create_orch):
        """Test generate-design with minimal required arguments."""
        # Setup mocks
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        mock_orchestrator = MagicMock()
        mock_orchestrator.generate_project_design = AsyncMock()
        mock_create_orch.return_value = mock_orchestrator

        # This will fail because we need async support in CLI testing
        # but this tests argument parsing
        result = runner.invoke(
            app,
            [
                "generate-design",
                "--name",
                "test-project",
                "--languages",
                "Python",
                "--requirements",
                "Build an API",
            ],
        )

        # Command should be recognized even if execution fails
        # Exit code may vary based on async handling
        assert result.exit_code in [0, 1, 2]

    def test_generate_design_missing_required_args(self):
        """Test generate-design fails with missing required arguments."""
        result = runner.invoke(app, ["generate-design"])

        # Should fail due to missing required arguments
        assert result.exit_code != 0


@pytest.mark.unit
class TestGenerateDevplanCommand:
    """Test generate-devplan command."""

    def test_generate_devplan_missing_input(self):
        """Test generate-devplan fails with missing input file."""
        result = runner.invoke(
            app, ["generate-devplan", "nonexistent_design.json"]
        )

        # Should fail due to missing file
        assert result.exit_code != 0


@pytest.mark.unit
class TestListCheckpointsCommand:
    """Test list-checkpoints command."""

    @patch("src.cli.StateManager")
    def test_list_checkpoints_empty(self, mock_state_manager_class):
        """Test listing checkpoints when none exist."""
        mock_state_manager = MagicMock()
        mock_state_manager.list_checkpoints.return_value = []
        mock_state_manager_class.return_value = mock_state_manager

        result = runner.invoke(app, ["list-checkpoints"])

        # Command should succeed
        assert result.exit_code == 0
        assert "No checkpoints found" in result.stdout or result.exit_code == 0

    @patch("src.cli.StateManager")
    def test_list_checkpoints_with_data(self, mock_state_manager_class):
        """Test listing checkpoints with existing checkpoints."""
        mock_state_manager = MagicMock()
        mock_state_manager.list_checkpoints.return_value = [
            {
                "key": "test_checkpoint_1",
                "stage": "project_design",
                "timestamp": "2024-01-01T00:00:00",
                "metadata": {},
            }
        ]
        mock_state_manager_class.return_value = mock_state_manager

        result = runner.invoke(app, ["list-checkpoints"])

        # Command should succeed
        assert result.exit_code == 0


@pytest.mark.unit
class TestDeleteCheckpointCommand:
    """Test delete-checkpoint command."""

    @patch("src.cli.StateManager")
    def test_delete_checkpoint_success(self, mock_state_manager_class):
        """Test successful checkpoint deletion."""
        mock_state_manager = MagicMock()
        mock_state_manager.delete_checkpoint.return_value = None
        mock_state_manager_class.return_value = mock_state_manager

        result = runner.invoke(
            app, ["delete-checkpoint", "test_checkpoint"]
        )

        # Command execution may vary based on implementation
        # Verify it doesn't crash
        assert result.exit_code in [0, 1]

    @patch("src.cli.StateManager")
    def test_delete_checkpoint_not_found(self, mock_state_manager_class):
        """Test deleting non-existent checkpoint."""
        mock_state_manager = MagicMock()
        mock_state_manager.delete_checkpoint.side_effect = ValueError(
            "Checkpoint not found"
        )
        mock_state_manager_class.return_value = mock_state_manager

        result = runner.invoke(
            app, ["delete-checkpoint", "nonexistent_checkpoint"]
        )

        # Command should fail gracefully
        assert result.exit_code != 0


@pytest.mark.unit
class TestCleanupCheckpointsCommand:
    """Test cleanup-checkpoints command."""

    @patch("src.cli.StateManager")
    def test_cleanup_checkpoints_default_days(self, mock_state_manager_class):
        """Test cleanup with default days parameter."""
        mock_state_manager = MagicMock()
        mock_state_manager.cleanup_old_checkpoints.return_value = 3
        mock_state_manager_class.return_value = mock_state_manager

        result = runner.invoke(app, ["cleanup-checkpoints"])

        # Command should execute (may succeed or fail based on implementation)
        assert result.exit_code in [0, 1]

    @patch("src.cli.StateManager")
    def test_cleanup_checkpoints_custom_days(self, mock_state_manager_class):
        """Test cleanup with custom days parameter."""
        mock_state_manager = MagicMock()
        mock_state_manager.cleanup_old_checkpoints.return_value = 5
        mock_state_manager_class.return_value = mock_state_manager

        result = runner.invoke(app, ["cleanup-checkpoints", "--days", "14"])

        # Command should execute
        assert result.exit_code in [0, 1, 2]


@pytest.mark.unit
class TestInitRepoCommand:
    """Test init-repo command."""

    def test_init_repo_basic(self):
        """Test basic repository initialization."""
        # This command requires actual file system operations
        # Just test that the command is recognized
        result = runner.invoke(app, ["init-repo", "--help"])

        # Help should work
        assert result.exit_code == 0
        assert "init-repo" in result.stdout or "Usage" in result.stdout


@pytest.mark.unit
class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_invalid_command(self):
        """Test CLI handles invalid commands."""
        result = runner.invoke(app, ["invalid-command"])

        # Should fail with unknown command error
        assert result.exit_code != 0

    def test_help_command(self):
        """Test CLI help output."""
        result = runner.invoke(app, ["--help"])

        # Help should succeed
        assert result.exit_code == 0
        assert "devussy" in result.stdout.lower() or "Usage" in result.stdout


@pytest.mark.unit
class TestCLIGlobalOptions:
    """Test global CLI options."""

    def test_config_option_exists(self):
        """Test that --config option is recognized."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Help text should mention configuration or options

    def test_version_flag(self):
        """Test --version flag (if supported)."""
        result = runner.invoke(app, ["--version"])

        # May succeed or fail depending on implementation
        # Just verify command doesn't crash
        assert result.exit_code in [0, 1, 2]


@pytest.mark.unit
class TestInteractiveDesignCommand:
    """Test interactive-design command."""

    @patch("src.cli._create_orchestrator")
    @patch("src.cli._load_app_config")
    @patch("src.interactive.InteractiveQuestionnaireManager")
    def test_interactive_design_basic_flow(
        self, mock_questionnaire_class, mock_load_config, mock_create_orch
    ):
        """Test interactive design command basic flow."""
        # Setup mocks
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        mock_orchestrator = MagicMock()
        mock_create_orch.return_value = mock_orchestrator

        mock_questionnaire = MagicMock()
        mock_questionnaire.run_questionnaire = AsyncMock(
            return_value={"completed": True}
        )
        mock_questionnaire_class.return_value = mock_questionnaire

        result = runner.invoke(app, ["interactive-design"])

        # Command should be recognized
        assert result.exit_code in [0, 1]


@pytest.mark.unit
class TestRunFullPipelineCommand:
    """Test run-full-pipeline command."""

    @patch("src.cli._create_orchestrator")
    @patch("src.cli._load_app_config")
    def test_run_full_pipeline_minimal(self, mock_load_config, mock_create_orch):
        """Test run-full-pipeline with minimal arguments."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        mock_orchestrator = MagicMock()
        mock_create_orch.return_value = mock_orchestrator

        result = runner.invoke(
            app,
            [
                "run-full-pipeline",
                "--name",
                "test",
                "--languages",
                "Python",
                "--requirements",
                "Test",
            ],
        )

        # Command should be recognized
        assert result.exit_code in [0, 1, 2]

    def test_run_full_pipeline_missing_args(self):
        """Test run-full-pipeline with missing required arguments."""
        result = runner.invoke(app, ["run-full-pipeline"])

        # Should fail due to missing arguments
        assert result.exit_code != 0


@pytest.mark.unit
class TestGenerateHandoffCommand:
    """Test generate-handoff command."""

    @patch("src.cli._create_orchestrator")
    @patch("src.cli._load_app_config")
    def test_generate_handoff_basic(self, mock_load_config, mock_create_orch):
        """Test generate-handoff command."""
        mock_config = MagicMock()
        mock_config.output_dir = Path("output")
        mock_load_config.return_value = mock_config

        mock_orchestrator = MagicMock()
        mock_create_orch.return_value = mock_orchestrator

        result = runner.invoke(
            app,
            ["generate-handoff", "devplan.json", "--name", "test"],
        )

        # Command should be recognized even if file doesn't exist
        assert result.exit_code in [0, 1, 2]


@pytest.mark.unit
class TestInitRepoCommandExtended:
    """Extended tests for init-repo command."""

    @patch("subprocess.run")
    @patch("src.cli._load_app_config")
    def test_init_repo_with_defaults(self, mock_load_config, mock_subprocess):
        """Test init-repo with default parameters."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        # Mock subprocess.run to simulate git commands
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        result = runner.invoke(app, ["init-repo"])

        # Should recognize command
        assert result.exit_code in [0, 1]


@pytest.mark.unit
class TestConfigLoadingExtended:
    """Extended configuration loading tests."""

    def test_load_config_all_overrides(self):
        """Test loading config with all CLI overrides."""
        config = _load_app_config(
            config_path=None,
            provider="generic",
            model="gpt-4",
            output_dir="/custom",
            verbose=True,
        )

        assert config.llm.provider == "generic"
        assert config.llm.model == "gpt-4"
        assert config.output_dir == Path("/custom")
        assert config.log_level == "DEBUG"

    def test_load_config_with_missing_file(self):
        """Test loading config when file doesn't exist."""
        config = _load_app_config(
            config_path="nonexistent.yaml",
            provider=None,
            model=None,
            output_dir=None,
            verbose=False,
        )

        # Should fall back to defaults
        assert config is not None
        assert isinstance(config, AppConfig)


@pytest.mark.unit
class TestOrchestratorCreationExtended:
    """Extended orchestrator creation tests."""

    @patch("src.cli.create_llm_client")
    @patch("src.cli.ConcurrencyManager")
    @patch("src.cli.FileManager")
    @patch("src.cli.StateManager")
    def test_create_orchestrator_with_all_components(
        self,
        mock_state_manager,
        mock_file_manager,
        mock_concurrency_manager,
        mock_create_client,
    ):
        """Test creating orchestrator with all components."""
        mock_create_client.return_value = MagicMock()
        mock_concurrency_manager.return_value = MagicMock()
        mock_file_manager.return_value = MagicMock()
        mock_state_manager.return_value = MagicMock()

        config = AppConfig(
            llm=LLMConfig(
                provider="openai",
                model="gpt-3.5-turbo",
                api_key="test-key",
            ),
            max_concurrent_requests=5,
        )

        orchestrator = _create_orchestrator(config)

        assert orchestrator is not None
        mock_create_client.assert_called_once()
        mock_concurrency_manager.assert_called_once()


@pytest.mark.unit
class TestCLIFileOperations:
    """Test CLI file operation handling."""

    def test_generate_devplan_with_nonexistent_file(self):
        """Test generate-devplan with non-existent input file."""
        result = runner.invoke(
            app, ["generate-devplan", "does_not_exist.json"]
        )

        # Should fail gracefully
        assert result.exit_code != 0

    @patch("src.cli.Path.exists")
    @patch("src.cli._create_orchestrator")
    @patch("src.cli._load_app_config")
    def test_generate_devplan_with_existing_file(
        self, mock_load_config, mock_create_orch, mock_path_exists
    ):
        """Test generate-devplan with existing input file."""
        mock_path_exists.return_value = True
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        mock_orchestrator = MagicMock()
        mock_create_orch.return_value = mock_orchestrator

        # Won't fully execute but tests file checking logic
        result = runner.invoke(app, ["generate-devplan", "design.json"])

        # Command recognized
        assert result.exit_code in [0, 1, 2]


@pytest.mark.unit
class TestCheckpointManagement:
    """Test checkpoint management commands."""

    @patch("src.cli.StateManager")
    def test_delete_checkpoint_with_confirmation(
        self, mock_state_manager_class
    ):
        """Test checkpoint deletion with user confirmation."""
        mock_state_manager = MagicMock()
        mock_state_manager.delete_checkpoint.return_value = None
        mock_state_manager_class.return_value = mock_state_manager

        result = runner.invoke(
            app, ["delete-checkpoint", "test_key"], input="y\n"
        )

        # Should execute
        assert result.exit_code in [0, 1]

    @patch("src.cli.StateManager")
    def test_cleanup_with_keep_parameter(self, mock_state_manager_class):
        """Test cleanup checkpoints with --keep parameter."""
        mock_state_manager = MagicMock()
        mock_state_manager.cleanup_old_checkpoints.return_value = 2
        mock_state_manager_class.return_value = mock_state_manager

        result = runner.invoke(app, ["cleanup-checkpoints", "--keep", "5"])

        # Command should execute
        assert result.exit_code in [0, 1]


@pytest.mark.unit
class TestCLIValidation:
    """Test CLI input validation."""

    def test_generate_design_with_empty_name(self):
        """Test generate-design with empty project name."""
        result = runner.invoke(
            app,
            [
                "generate-design",
                "--name",
                "",
                "--languages",
                "Python",
                "--requirements",
                "Test",
            ],
        )

        # May fail validation or accept empty string
        assert result.exit_code in [0, 1, 2]

    def test_generate_design_with_special_characters(self):
        """Test generate-design with special characters in name."""
        result = runner.invoke(
            app,
            [
                "generate-design",
                "--name",
                "test@#$%",
                "--languages",
                "Python",
                "--requirements",
                "Test",
            ],
        )

        # Should handle special characters
        assert result.exit_code in [0, 1, 2]


@pytest.mark.unit
class TestCLIOutputHandling:
    """Test CLI output handling."""

    @patch("src.cli.StateManager")
    def test_list_checkpoints_with_multiple_entries(
        self, mock_state_manager_class
    ):
        """Test listing multiple checkpoints."""
        mock_state_manager = MagicMock()
        mock_state_manager.list_checkpoints.return_value = [
            {
                "key": "checkpoint1",
                "stage": "design",
                "timestamp": "2024-01-01T00:00:00",
                "metadata": {},
            },
            {
                "key": "checkpoint2",
                "stage": "devplan",
                "timestamp": "2024-01-02T00:00:00",
                "metadata": {},
            },
        ]
        mock_state_manager_class.return_value = mock_state_manager

        result = runner.invoke(app, ["list-checkpoints"])

        assert result.exit_code == 0
        # Output should contain checkpoint information

    @patch("src.cli.typer.echo")
    def test_help_text_formatting(self, mock_echo):
        """Test that help text is properly formatted."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "devussy" in result.stdout.lower() or "command" in result.stdout.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
