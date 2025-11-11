"""
Feedback Manager for DevPlan Orchestration Tool.

This module provides a mechanism for users to provide feedback on generated
devplans and integrate corrections into regeneration workflows.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.models import DevPlan

logger = logging.getLogger(__name__)


class FeedbackManager:
    """
    Manages user feedback integration for iterative devplan refinement.

    Supports loading feedback from YAML files, parsing corrections, and
    injecting them into devplan generation while preserving manual edits.
    """

    def __init__(self, feedback_file: Optional[Path] = None):
        """
        Initialize the FeedbackManager.

        Args:
            feedback_file: Optional path to YAML feedback file
        """
        self.feedback_file = feedback_file
        self.feedback_data: Dict[str, Any] = {}
        self.corrections: List[Dict[str, Any]] = []
        self.manual_edits: Dict[str, str] = {}

        if feedback_file and feedback_file.exists():
            self.load_feedback()

    def load_feedback(self) -> None:
        """
        Load feedback from YAML file.

        Raises:
            FileNotFoundError: If feedback file doesn't exist
            yaml.YAMLError: If feedback file is malformed
        """
        if not self.feedback_file:
            logger.warning("No feedback file specified")
            return

        if not self.feedback_file.exists():
            raise FileNotFoundError(f"Feedback file not found: {self.feedback_file}")

        logger.info(f"Loading feedback from {self.feedback_file}")
        try:
            with open(self.feedback_file, "r", encoding="utf-8") as f:
                self.feedback_data = yaml.safe_load(f) or {}

            # Parse corrections and manual edits
            self.corrections = self.feedback_data.get("corrections", [])
            self.manual_edits = self.feedback_data.get("manual_edits", {})

            logger.info(
                f"Loaded {len(self.corrections)} corrections and "
                f"{len(self.manual_edits)} manual edits"
            )
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse feedback YAML: {e}")
            raise

    def apply_corrections_to_prompt(self, prompt: str) -> str:
        """
        Apply feedback corrections to a generation prompt.

        Args:
            prompt: Original prompt text

        Returns:
            Modified prompt with feedback instructions injected
        """
        if not self.corrections:
            return prompt

        # Build feedback section
        feedback_section = "\n\n## User Feedback and Corrections\n\n"
        feedback_section += (
            "The following corrections should be applied to the output:\n\n"
        )

        for idx, correction in enumerate(self.corrections, 1):
            correction_type = correction.get("type", "general")
            description = correction.get("description", "")
            target = correction.get("target", "")

            if correction_type == "phase":
                feedback_section += f"{idx}. **Phase Correction** (Phase: {target})\n"
                feedback_section += f"   - {description}\n\n"
            elif correction_type == "step":
                feedback_section += f"{idx}. **Step Correction** (Step: {target})\n"
                feedback_section += f"   - {description}\n\n"
            elif correction_type == "general":
                feedback_section += f"{idx}. **General Correction**\n"
                feedback_section += f"   - {description}\n\n"
            else:
                feedback_section += f"{idx}. {description}\n\n"

        # Inject before the final instruction section
        modified_prompt = prompt + feedback_section
        logger.debug(f"Applied {len(self.corrections)} corrections to prompt")
        return modified_prompt

    def preserve_manual_edits(self, devplan: DevPlan) -> DevPlan:
        """
        Preserve manual edits when regenerating a devplan.

        Args:
            devplan: Generated DevPlan to modify

        Returns:
            DevPlan with manual edits preserved
        """
        if not self.manual_edits:
            return devplan

        logger.info(f"Preserving {len(self.manual_edits)} manual edits")

        # Manual edits are keyed by phase or step identifiers
        for edit_key, edit_content in self.manual_edits.items():
            # Parse edit key (e.g., "phase_3", "phase_2_step_4")
            parts = edit_key.split("_")

            if len(parts) == 2 and parts[0] == "phase":
                # Phase-level edit
                phase_num = int(parts[1])
                if 0 <= phase_num - 1 < len(devplan.phases):
                    phase = devplan.phases[phase_num - 1]
                    phase.description = edit_content
                    logger.debug(f"Applied edit to Phase {phase_num}")

            elif len(parts) == 4 and parts[0] == "phase" and parts[2] == "step":
                # Step-level edit
                phase_num = int(parts[1])
                step_num = int(parts[3])
                if 0 <= phase_num - 1 < len(devplan.phases):
                    phase = devplan.phases[phase_num - 1]
                    if 0 <= step_num - 1 < len(phase.steps):
                        step = phase.steps[step_num - 1]
                        step.description = edit_content
                        logger.debug(
                            f"Applied edit to Phase {phase_num}, Step {step_num}"
                        )

        return devplan

    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        Get a summary of loaded feedback.

        Returns:
            Dictionary with feedback statistics
        """
        return {
            "feedback_file": str(self.feedback_file) if self.feedback_file else None,
            "total_corrections": len(self.corrections),
            "total_manual_edits": len(self.manual_edits),
            "corrections_by_type": self._count_corrections_by_type(),
        }

    def _count_corrections_by_type(self) -> Dict[str, int]:
        """Count corrections by type."""
        counts: Dict[str, int] = {}
        for correction in self.corrections:
            correction_type = correction.get("type", "general")
            counts[correction_type] = counts.get(correction_type, 0) + 1
        return counts

    def create_feedback_template(self, output_path: Path) -> None:
        """
        Create a feedback template YAML file for users to fill out.

        Args:
            output_path: Path to write the template file
        """
        template = {
            "corrections": [
                {
                    "type": "phase",
                    "target": "Phase 1",
                    "description": "Add more detail about initialization steps",
                },
                {
                    "type": "step",
                    "target": "Phase 2, Step 3",
                    "description": "Clarify the API endpoint configuration",
                },
                {
                    "type": "general",
                    "target": "",
                    "description": "Include more error handling examples",
                },
            ],
            "manual_edits": {
                "phase_1": "Updated phase 1 description with more context",
                "phase_2_step_3": "Modified step 3 to include additional validation",
            },
            "metadata": {
                "created_by": "user",
                "purpose": "Iterative refinement of devplan",
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(template, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created feedback template at {output_path}")

    def merge_feedback_from_file(self, additional_feedback_file: Path) -> None:
        """
        Merge additional feedback from another file.

        Args:
            additional_feedback_file: Path to additional feedback YAML file
        """
        if not additional_feedback_file.exists():
            logger.warning(
                f"Additional feedback file not found: {additional_feedback_file}"
            )
            return

        with open(additional_feedback_file, "r", encoding="utf-8") as f:
            additional_data = yaml.safe_load(f) or {}

        # Merge corrections
        additional_corrections = additional_data.get("corrections", [])
        self.corrections.extend(additional_corrections)

        # Merge manual edits (later edits override earlier ones)
        additional_edits = additional_data.get("manual_edits", {})
        self.manual_edits.update(additional_edits)

        logger.info(
            f"Merged {len(additional_corrections)} corrections and "
            f"{len(additional_edits)} manual edits from {additional_feedback_file}"
        )
