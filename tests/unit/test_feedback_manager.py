"""Unit tests for FeedbackManager."""

from pathlib import Path

import pytest
import yaml

from src.feedback_manager import FeedbackManager
from src.models import DevPlan, DevPlanPhase, DevPlanStep


class TestFeedbackManagerInitialization:
    """Tests for FeedbackManager initialization."""

    def test_init_without_file(self):
        """Test initialization without a feedback file."""
        manager = FeedbackManager()
        assert manager.feedback_file is None
        assert manager.feedback_data == {}
        assert manager.corrections == []
        assert manager.manual_edits == {}

    def test_init_with_nonexistent_file(self):
        """Test initialization with nonexistent file doesn't auto-load."""
        fake_path = Path("/nonexistent/feedback.yaml")
        manager = FeedbackManager(fake_path)
        assert manager.feedback_file == fake_path
        assert manager.feedback_data == {}
        assert manager.corrections == []

    def test_init_with_existing_file(self, tmp_path):
        """Test initialization with existing file auto-loads."""
        feedback_file = tmp_path / "feedback.yaml"
        feedback_data = {
            "corrections": [
                {"type": "phase", "target": "Phase 1", "description": "Add more detail"}
            ],
            "manual_edits": {"phase_1": "Updated description"},
        }

        with open(feedback_file, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data, f)

        manager = FeedbackManager(feedback_file)
        assert len(manager.corrections) == 1
        assert len(manager.manual_edits) == 1


class TestFeedbackLoading:
    """Tests for loading feedback from files."""

    def test_load_feedback_success(self, tmp_path):
        """Test successfully loading feedback from a YAML file."""
        feedback_file = tmp_path / "feedback.yaml"
        feedback_data = {
            "corrections": [
                {
                    "type": "phase",
                    "target": "Phase 1",
                    "description": "Add more detail about initialization",
                },
                {
                    "type": "step",
                    "target": "Phase 2, Step 3",
                    "description": "Clarify API endpoint",
                },
                {"type": "general", "target": "", "description": "Add error handling"},
            ],
            "manual_edits": {
                "phase_1": "Updated phase 1 description",
                "phase_2_step_3": "Modified step 3 description",
            },
        }

        with open(feedback_file, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data, f)

        manager = FeedbackManager()
        manager.feedback_file = feedback_file
        manager.load_feedback()

        assert len(manager.corrections) == 3
        assert len(manager.manual_edits) == 2
        assert manager.corrections[0]["type"] == "phase"
        assert manager.manual_edits["phase_1"] == "Updated phase 1 description"

    def test_load_feedback_file_not_found(self):
        """Test loading feedback raises error when file not found."""
        manager = FeedbackManager()
        manager.feedback_file = Path("/nonexistent/feedback.yaml")

        with pytest.raises(FileNotFoundError):
            manager.load_feedback()

    def test_load_feedback_malformed_yaml(self, tmp_path):
        """Test loading feedback raises error for malformed YAML."""
        feedback_file = tmp_path / "bad_feedback.yaml"

        with open(feedback_file, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: {[}]")

        manager = FeedbackManager()
        manager.feedback_file = feedback_file

        with pytest.raises(yaml.YAMLError):
            manager.load_feedback()

    def test_load_feedback_empty_file(self, tmp_path):
        """Test loading feedback from empty file."""
        feedback_file = tmp_path / "empty_feedback.yaml"
        feedback_file.touch()

        manager = FeedbackManager()
        manager.feedback_file = feedback_file
        manager.load_feedback()

        assert manager.feedback_data == {}
        assert manager.corrections == []
        assert manager.manual_edits == {}

    def test_load_feedback_no_file_specified(self):
        """Test load_feedback warns when no file is specified."""
        manager = FeedbackManager()
        manager.load_feedback()  # Should not raise, just warn

        assert manager.corrections == []


class TestApplyCorrectionsToPrompt:
    """Tests for applying corrections to prompts."""

    def test_apply_no_corrections(self):
        """Test applying corrections when none are loaded."""
        manager = FeedbackManager()
        original_prompt = "Generate a devplan for this project."

        result = manager.apply_corrections_to_prompt(original_prompt)

        assert result == original_prompt

    def test_apply_phase_correction(self, tmp_path):
        """Test applying phase-specific correction."""
        feedback_file = tmp_path / "feedback.yaml"
        feedback_data = {
            "corrections": [
                {
                    "type": "phase",
                    "target": "Phase 1",
                    "description": "Add more initialization steps",
                }
            ]
        }

        with open(feedback_file, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data, f)

        manager = FeedbackManager(feedback_file)
        original_prompt = "Generate a devplan."
        result = manager.apply_corrections_to_prompt(original_prompt)

        assert "User Feedback and Corrections" in result
        assert "Phase Correction" in result
        assert "Add more initialization steps" in result

    def test_apply_step_correction(self, tmp_path):
        """Test applying step-specific correction."""
        feedback_file = tmp_path / "feedback.yaml"
        feedback_data = {
            "corrections": [
                {
                    "type": "step",
                    "target": "Phase 2, Step 3",
                    "description": "Clarify the endpoint configuration",
                }
            ]
        }

        with open(feedback_file, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data, f)

        manager = FeedbackManager(feedback_file)
        result = manager.apply_corrections_to_prompt("Generate a devplan.")

        assert "Step Correction" in result
        assert "Clarify the endpoint configuration" in result

    def test_apply_general_correction(self, tmp_path):
        """Test applying general correction."""
        feedback_file = tmp_path / "feedback.yaml"
        feedback_data = {
            "corrections": [
                {"type": "general", "target": "", "description": "Add error handling"}
            ]
        }

        with open(feedback_file, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data, f)

        manager = FeedbackManager(feedback_file)
        result = manager.apply_corrections_to_prompt("Generate a devplan.")

        assert "General Correction" in result
        assert "Add error handling" in result

    def test_apply_multiple_corrections(self, tmp_path):
        """Test applying multiple corrections of different types."""
        feedback_file = tmp_path / "feedback.yaml"
        feedback_data = {
            "corrections": [
                {"type": "phase", "target": "Phase 1", "description": "More detail"},
                {"type": "step", "target": "Phase 2, Step 1", "description": "Clarify"},
                {"type": "general", "target": "", "description": "Add tests"},
            ]
        }

        with open(feedback_file, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data, f)

        manager = FeedbackManager(feedback_file)
        result = manager.apply_corrections_to_prompt("Generate a devplan.")

        assert result.count("1.") == 1
        assert result.count("2.") == 1
        assert result.count("3.") == 1
        assert "More detail" in result
        assert "Clarify" in result
        assert "Add tests" in result


class TestPreserveManualEdits:
    """Tests for preserving manual edits in devplans."""

    def test_preserve_no_edits(self):
        """Test preserving when no manual edits exist."""
        manager = FeedbackManager()
        devplan = DevPlan(
            phases=[
                DevPlanPhase(
                    number=1,
                    title="Phase 1",
                    steps=[DevPlanStep(number="1.1", description="Step 1 description")],
                )
            ],
            summary="Test devplan",
        )

        result = manager.preserve_manual_edits(devplan)

        assert result == devplan

    def test_preserve_phase_edit(self, tmp_path):
        """Test preserving phase-level manual edit."""
        feedback_file = tmp_path / "feedback.yaml"
        feedback_data = {"manual_edits": {"phase_1": "Updated phase 1 description"}}

        with open(feedback_file, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data, f)

        manager = FeedbackManager(feedback_file)
        devplan = DevPlan(
            phases=[
                DevPlanPhase(
                    number=1,
                    title="Phase 1",
                    description="Original description",
                    steps=[],
                )
            ],
            summary="Test",
        )

        result = manager.preserve_manual_edits(devplan)

        assert result.phases[0].description == "Updated phase 1 description"

    def test_preserve_step_edit(self, tmp_path):
        """Test preserving step-level manual edit."""
        feedback_file = tmp_path / "feedback.yaml"
        feedback_data = {
            "manual_edits": {"phase_1_step_1": "Updated step 1 description"}
        }

        with open(feedback_file, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data, f)

        manager = FeedbackManager(feedback_file)
        devplan = DevPlan(
            phases=[
                DevPlanPhase(
                    number=1,
                    title="Phase 1",
                    steps=[
                        DevPlanStep(
                            number="1.1", description="Original step description"
                        )
                    ],
                )
            ],
            summary="Test",
        )

        result = manager.preserve_manual_edits(devplan)

        assert result.phases[0].steps[0].description == "Updated step 1 description"

    def test_preserve_multiple_edits(self, tmp_path):
        """Test preserving multiple manual edits."""
        feedback_file = tmp_path / "feedback.yaml"
        feedback_data = {
            "manual_edits": {
                "phase_1": "Updated phase 1",
                "phase_2": "Updated phase 2",
                "phase_1_step_1": "Updated step 1.1",
                "phase_2_step_2": "Updated step 2.2",
            }
        }

        with open(feedback_file, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data, f)

        manager = FeedbackManager(feedback_file)
        devplan = DevPlan(
            phases=[
                DevPlanPhase(
                    number=1,
                    title="Phase 1",
                    description="Original phase 1",
                    steps=[DevPlanStep(number="1.1", description="Original step 1.1")],
                ),
                DevPlanPhase(
                    number=2,
                    title="Phase 2",
                    description="Original phase 2",
                    steps=[
                        DevPlanStep(number="2.1", description="Original step 2.1"),
                        DevPlanStep(number="2.2", description="Original step 2.2"),
                    ],
                ),
            ],
            summary="Test",
        )

        result = manager.preserve_manual_edits(devplan)

        assert result.phases[0].description == "Updated phase 1"
        assert result.phases[1].description == "Updated phase 2"
        assert result.phases[0].steps[0].description == "Updated step 1.1"
        assert result.phases[1].steps[1].description == "Updated step 2.2"

    def test_preserve_edits_invalid_phase(self, tmp_path):
        """Test preserving edits for non-existent phase."""
        feedback_file = tmp_path / "feedback.yaml"
        feedback_data = {"manual_edits": {"phase_99": "Non-existent phase"}}

        with open(feedback_file, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data, f)

        manager = FeedbackManager(feedback_file)
        devplan = DevPlan(
            phases=[DevPlanPhase(number=1, title="Phase 1", steps=[])], summary="Test"
        )

        # Should not raise error, just skip invalid edits
        result = manager.preserve_manual_edits(devplan)
        assert len(result.phases) == 1


class TestFeedbackSummary:
    """Tests for feedback summary generation."""

    def test_get_feedback_summary_empty(self):
        """Test getting summary with no feedback."""
        manager = FeedbackManager()
        summary = manager.get_feedback_summary()

        assert summary["feedback_file"] is None
        assert summary["total_corrections"] == 0
        assert summary["total_manual_edits"] == 0
        assert summary["corrections_by_type"] == {}

    def test_get_feedback_summary_with_data(self, tmp_path):
        """Test getting summary with feedback data."""
        feedback_file = tmp_path / "feedback.yaml"
        feedback_data = {
            "corrections": [
                {"type": "phase", "target": "Phase 1", "description": "Detail"},
                {"type": "phase", "target": "Phase 2", "description": "More"},
                {"type": "step", "target": "Phase 1, Step 1", "description": "Clarify"},
                {"type": "general", "target": "", "description": "Add tests"},
            ],
            "manual_edits": {
                "phase_1": "Updated",
                "phase_2_step_1": "Modified",
            },
        }

        with open(feedback_file, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data, f)

        manager = FeedbackManager(feedback_file)
        summary = manager.get_feedback_summary()

        assert str(feedback_file) in summary["feedback_file"]
        assert summary["total_corrections"] == 4
        assert summary["total_manual_edits"] == 2
        assert summary["corrections_by_type"]["phase"] == 2
        assert summary["corrections_by_type"]["step"] == 1
        assert summary["corrections_by_type"]["general"] == 1


class TestCreateFeedbackTemplate:
    """Tests for creating feedback templates."""

    def test_create_feedback_template(self, tmp_path):
        """Test creating a feedback template file."""
        manager = FeedbackManager()
        template_file = tmp_path / "feedback_template.yaml"

        manager.create_feedback_template(template_file)

        assert template_file.exists()

        with open(template_file, "r", encoding="utf-8") as f:
            template_data = yaml.safe_load(f)

        assert "corrections" in template_data
        assert "manual_edits" in template_data
        assert "metadata" in template_data
        assert len(template_data["corrections"]) == 3
        assert len(template_data["manual_edits"]) == 2


class TestMergeFeedback:
    """Tests for merging feedback from multiple files."""

    def test_merge_feedback_from_file(self, tmp_path):
        """Test merging additional feedback from another file."""
        # Create initial feedback
        feedback_file1 = tmp_path / "feedback1.yaml"
        feedback_data1 = {
            "corrections": [
                {"type": "phase", "target": "Phase 1", "description": "First"}
            ],
            "manual_edits": {"phase_1": "First edit"},
        }

        with open(feedback_file1, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data1, f)

        # Create additional feedback
        feedback_file2 = tmp_path / "feedback2.yaml"
        feedback_data2 = {
            "corrections": [
                {"type": "step", "target": "Phase 2, Step 1", "description": "Second"}
            ],
            "manual_edits": {"phase_2": "Second edit"},
        }

        with open(feedback_file2, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data2, f)

        manager = FeedbackManager(feedback_file1)
        assert len(manager.corrections) == 1
        assert len(manager.manual_edits) == 1

        manager.merge_feedback_from_file(feedback_file2)

        assert len(manager.corrections) == 2
        assert len(manager.manual_edits) == 2
        assert manager.corrections[1]["type"] == "step"
        assert manager.manual_edits["phase_2"] == "Second edit"

    def test_merge_feedback_nonexistent_file(self, tmp_path):
        """Test merging from non-existent file doesn't raise error."""
        feedback_file1 = tmp_path / "feedback1.yaml"
        feedback_data1 = {"corrections": [], "manual_edits": {}}

        with open(feedback_file1, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data1, f)

        manager = FeedbackManager(feedback_file1)
        fake_file = tmp_path / "nonexistent.yaml"

        # Should not raise, just warn
        manager.merge_feedback_from_file(fake_file)

        assert len(manager.corrections) == 0

    def test_merge_feedback_overrides_edits(self, tmp_path):
        """Test that later merges override earlier manual edits."""
        feedback_file1 = tmp_path / "feedback1.yaml"
        feedback_data1 = {"manual_edits": {"phase_1": "First version"}}

        with open(feedback_file1, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data1, f)

        feedback_file2 = tmp_path / "feedback2.yaml"
        feedback_data2 = {"manual_edits": {"phase_1": "Second version"}}

        with open(feedback_file2, "w", encoding="utf-8") as f:
            yaml.dump(feedback_data2, f)

        manager = FeedbackManager(feedback_file1)
        assert manager.manual_edits["phase_1"] == "First version"

        manager.merge_feedback_from_file(feedback_file2)
        assert manager.manual_edits["phase_1"] == "Second version"
