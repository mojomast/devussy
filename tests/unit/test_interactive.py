"""Tests for interactive questionnaire system."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from src.interactive import (
    InteractiveQuestionnaireManager,
    InteractiveSession,
    Question,
    QuestionType,
)


@pytest.fixture
def sample_questions_config(tmp_path):
    """Create a sample questions config file."""
    config = {
        "questions": [
            {
                "id": "project_name",
                "text": "What is your project name?",
                "type": "text",
                "required": True,
            },
            {
                "id": "project_type",
                "text": "What type of project?",
                "type": "choice",
                "options": ["Web App", "API", "CLI"],
                "required": True,
            },
            {
                "id": "frontend_framework",
                "text": "Which frontend framework?",
                "type": "choice",
                "options": ["React", "Vue", "Angular"],
                "depends_on": {"project_type": "Web App"},
                "required": False,
            },
        ]
    }

    config_path = tmp_path / "test_questions.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


@pytest.fixture
def minimal_questions_config(tmp_path):
    """Create a minimal questions config file for basic testing."""
    config = {
        "questions": [
            {
                "id": "project_name",
                "text": "Project name?",
                "type": "text",
                "required": True,
            },
            {
                "id": "primary_language",
                "text": "Primary language?",
                "type": "text",
                "required": True,
            },
            {
                "id": "requirements",
                "text": "Requirements?",
                "type": "text",
                "required": True,
            },
        ]
    }

    config_path = tmp_path / "minimal_questions.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


class TestQuestion:
    """Tests for Question model."""

    def test_question_creation(self):
        """Test creating a Question instance."""
        question = Question(
            id="test_q",
            text="Test question?",
            type=QuestionType.TEXT,
            required=True,
        )

        assert question.id == "test_q"
        assert question.text == "Test question?"
        assert question.type == QuestionType.TEXT
        assert question.required is True

    def test_question_with_options(self):
        """Test question with choice options."""
        question = Question(
            id="choice_q",
            text="Choose one?",
            type=QuestionType.CHOICE,
            options=["A", "B", "C"],
            default="A",
        )

        assert question.options == ["A", "B", "C"]
        assert question.default == "A"

    def test_should_ask_no_dependencies(self):
        """Test that questions without dependencies always return True."""
        question = Question(
            id="q1", text="Question 1?", type=QuestionType.TEXT, required=True
        )

        assert question.should_ask({}) is True
        assert question.should_ask({"other": "value"}) is True

    def test_should_ask_with_single_dependency(self):
        """Test conditional questions with single dependency."""
        question = Question(
            id="q2",
            text="Question 2?",
            type=QuestionType.TEXT,
            depends_on={"project_type": "Web App"},
        )

        # Should ask when dependency is met
        assert question.should_ask({"project_type": "Web App"}) is True

        # Should not ask when dependency is not met
        assert question.should_ask({"project_type": "API"}) is False

        # Should not ask when dependency key is missing
        assert question.should_ask({}) is False

    def test_should_ask_with_list_dependency(self):
        """Test conditional questions with list of acceptable values."""
        question = Question(
            id="q3",
            text="Question 3?",
            type=QuestionType.TEXT,
            depends_on={"project_type": ["Web App", "API"]},
        )

        # Should ask when value matches any in list
        assert question.should_ask({"project_type": "Web App"}) is True
        assert question.should_ask({"project_type": "API"}) is True

        # Should not ask when value doesn't match any in list
        assert question.should_ask({"project_type": "CLI"}) is False

    def test_should_ask_with_multiple_dependencies(self):
        """Test questions with multiple dependencies."""
        question = Question(
            id="q4",
            text="Question 4?",
            type=QuestionType.TEXT,
            depends_on={"project_type": "Web App", "has_backend": True},
        )

        # Should ask only when all dependencies are met
        assert question.should_ask({"project_type": "Web App", "has_backend": True}) is True

        # Should not ask if any dependency is not met
        assert question.should_ask({"project_type": "Web App", "has_backend": False}) is False
        assert question.should_ask({"project_type": "API", "has_backend": True}) is False
        assert question.should_ask({"project_type": "Web App"}) is False


class TestInteractiveQuestionnaireManager:
    """Tests for InteractiveQuestionnaireManager."""

    def test_load_questions(self, sample_questions_config):
        """Test loading questions from config."""
        manager = InteractiveQuestionnaireManager(sample_questions_config)

        assert len(manager.questions) == 3
        assert manager.questions[0].id == "project_name"
        assert manager.questions[0].type == QuestionType.TEXT
        assert manager.questions[1].id == "project_type"
        assert manager.questions[1].type == QuestionType.CHOICE

    def test_load_questions_file_not_found(self, tmp_path):
        """Test that loading non-existent config raises error."""
        non_existent_path = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            InteractiveQuestionnaireManager(non_existent_path)

    def test_load_questions_invalid_config(self, tmp_path):
        """Test that invalid config raises error."""
        invalid_config_path = tmp_path / "invalid.yaml"
        with open(invalid_config_path, "w") as f:
            yaml.dump({"not_questions": []}, f)

        with pytest.raises(ValueError, match="missing 'questions' key"):
            InteractiveQuestionnaireManager(invalid_config_path)

    def test_session_initialization(self, sample_questions_config):
        """Test that session is properly initialized."""
        manager = InteractiveQuestionnaireManager(sample_questions_config)

        assert manager.session is not None
        assert isinstance(manager.session, InteractiveSession)
        assert len(manager.session.session_id) > 0
        assert manager.session.answers == {}
        assert manager.session.current_question_index == 0

    def test_save_session(self, sample_questions_config, tmp_path):
        """Test saving session to file."""
        manager = InteractiveQuestionnaireManager(sample_questions_config)

        # Add some answers
        manager.session.answers = {
            "project_name": "Test Project",
            "project_type": "Web App",
        }

        # Save session
        session_path = tmp_path / "test_session.json"
        manager.save_session(session_path)

        # Verify file was created
        assert session_path.exists()

        # Verify content
        with open(session_path, "r") as f:
            data = json.load(f)

        assert data["answers"]["project_name"] == "Test Project"
        assert data["answers"]["project_type"] == "Web App"

    def test_load_session(self, sample_questions_config, tmp_path):
        """Test loading session from file."""
        manager = InteractiveQuestionnaireManager(sample_questions_config)

        # Add some answers and save
        manager.session.answers = {
            "project_name": "Test Project",
            "project_type": "Web App",
        }
        session_path = tmp_path / "test_session.json"
        manager.save_session(session_path)

        # Create new manager and load session
        manager2 = InteractiveQuestionnaireManager(sample_questions_config)
        manager2.load_session(session_path)

        assert manager2.session.answers == manager.session.answers

    def test_load_session_file_not_found(self, sample_questions_config, tmp_path):
        """Test that loading non-existent session raises error."""
        manager = InteractiveQuestionnaireManager(sample_questions_config)
        non_existent_path = tmp_path / "nonexistent_session.json"

        with pytest.raises(FileNotFoundError):
            manager.load_session(non_existent_path)

    def test_to_generate_design_inputs_basic(self, minimal_questions_config):
        """Test converting answers to generate_design inputs."""
        manager = InteractiveQuestionnaireManager(minimal_questions_config)

        manager.session.answers = {
            "project_name": "My App",
            "primary_language": "Python",
            "requirements": "Build an API",
        }

        inputs = manager.to_generate_design_inputs()

        assert inputs["name"] == "My App"
        assert inputs["languages"] == "Python"
        assert inputs["requirements"] == "Build an API"

    def test_to_generate_design_inputs_with_frameworks(self, minimal_questions_config):
        """Test converting answers with frameworks."""
        manager = InteractiveQuestionnaireManager(minimal_questions_config)

        manager.session.answers = {
            "project_name": "My App",
            "primary_language": "Python",
            "requirements": "Build an API",
            "backend_framework": "FastAPI",
            "database": "PostgreSQL",
        }

        inputs = manager.to_generate_design_inputs()

        assert inputs["name"] == "My App"
        assert "FastAPI" in inputs["frameworks"]
        assert "PostgreSQL" in inputs["frameworks"]

    def test_to_generate_design_inputs_with_apis(self, minimal_questions_config):
        """Test converting answers with external APIs."""
        manager = InteractiveQuestionnaireManager(minimal_questions_config)

        manager.session.answers = {
            "project_name": "My App",
            "primary_language": "Python",
            "requirements": "Build an API",
            "external_apis": "Stripe,SendGrid",
        }

        inputs = manager.to_generate_design_inputs()

        assert inputs["apis"] == "Stripe,SendGrid"

    def test_to_generate_design_inputs_with_additional_languages(
        self, minimal_questions_config
    ):
        """Test converting answers with additional languages."""
        manager = InteractiveQuestionnaireManager(minimal_questions_config)

        manager.session.answers = {
            "project_name": "My App",
            "primary_language": "Python",
            "additional_languages": "JavaScript,HTML",
            "requirements": "Build a web app",
        }

        inputs = manager.to_generate_design_inputs()

        assert "Python" in inputs["languages"]
        assert "JavaScript" in inputs["languages"]
        assert "HTML" in inputs["languages"]

    def test_to_generate_design_inputs_with_authentication(
        self, minimal_questions_config
    ):
        """Test that authentication requirement is added to requirements."""
        manager = InteractiveQuestionnaireManager(minimal_questions_config)

        manager.session.answers = {
            "project_name": "My App",
            "primary_language": "Python",
            "requirements": "Build an API",
            "authentication": True,
        }

        inputs = manager.to_generate_design_inputs()

        assert "authentication" in inputs["requirements"].lower()

    def test_to_generate_design_inputs_with_cicd(self, minimal_questions_config):
        """Test that CI/CD requirement is added to requirements."""
        manager = InteractiveQuestionnaireManager(minimal_questions_config)

        manager.session.answers = {
            "project_name": "My App",
            "primary_language": "Python",
            "requirements": "Build an API",
            "ci_cd": True,
        }

        inputs = manager.to_generate_design_inputs()

        assert "ci/cd" in inputs["requirements"].lower() or "ci-cd" in inputs["requirements"].lower()

    def test_to_generate_design_inputs_skips_none_values(
        self, minimal_questions_config
    ):
        """Test that 'None' string values are filtered out."""
        manager = InteractiveQuestionnaireManager(minimal_questions_config)

        manager.session.answers = {
            "project_name": "My App",
            "primary_language": "Python",
            "requirements": "Build an API",
            "frontend_framework": "None (backend only)",
            "database": "None",
        }

        inputs = manager.to_generate_design_inputs()

        # Should not include None values in frameworks
        frameworks = inputs.get("frameworks", "")
        assert "None" not in frameworks


class TestInteractiveFlow:
    """Integration tests for the full interactive flow."""

    @patch("src.interactive.Progress")
    @patch("src.interactive.Prompt.ask")
    @patch("src.interactive.Confirm.ask")
    def test_full_questionnaire_flow(
        self, mock_confirm, mock_prompt, mock_progress_class, minimal_questions_config
    ):
        """Test running through a complete questionnaire."""
        # Setup mock responses
        mock_prompt.side_effect = ["Test Project", "Python", "Build a CLI tool"]

        # Mock the Progress context manager
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress.add_task.return_value = mock_task
        mock_progress.__enter__.return_value = mock_progress
        mock_progress.__exit__.return_value = None
        mock_progress_class.return_value = mock_progress

        manager = InteractiveQuestionnaireManager(minimal_questions_config)

        # Mock console to avoid actual rendering
        manager.console = MagicMock()

        answers = manager.run()

        assert answers["project_name"] == "Test Project"
        assert answers["primary_language"] == "Python"
        assert answers["requirements"] == "Build a CLI tool"

    def test_conditional_questions_are_skipped(self, sample_questions_config):
        """Test that conditional questions are skipped when dependencies not met."""
        manager = InteractiveQuestionnaireManager(sample_questions_config)

        # Manually set answers
        manager.session.answers = {
            "project_name": "Test",
            "project_type": "API",  # Not "Web App"
        }

        # Check if frontend_framework should be asked
        frontend_q = manager.questions[2]  # frontend_framework question
        assert frontend_q.should_ask(manager.session.answers) is False


class TestQuestionTypes:
    """Tests for different question types."""

    def test_text_question_type(self):
        """Test TEXT question type."""
        q = Question(id="q", text="Q?", type=QuestionType.TEXT, required=True)
        assert q.type == QuestionType.TEXT

    def test_choice_question_type(self):
        """Test CHOICE question type."""
        q = Question(
            id="q",
            text="Q?",
            type=QuestionType.CHOICE,
            options=["A", "B"],
            required=True,
        )
        assert q.type == QuestionType.CHOICE
        assert q.options == ["A", "B"]

    def test_yesno_question_type(self):
        """Test YESNO question type."""
        q = Question(id="q", text="Q?", type=QuestionType.YESNO, default=True)
        assert q.type == QuestionType.YESNO
        assert q.default is True

    def test_multichoice_question_type(self):
        """Test MULTICHOICE question type."""
        q = Question(
            id="q",
            text="Q?",
            type=QuestionType.MULTICHOICE,
            options=["A", "B", "C"],
        )
        assert q.type == QuestionType.MULTICHOICE

    def test_number_question_type(self):
        """Test NUMBER question type."""
        q = Question(id="q", text="Q?", type=QuestionType.NUMBER, default=5)
        assert q.type == QuestionType.NUMBER
        assert q.default == 5
