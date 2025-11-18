"""Markdown output manager for saving interview and pipeline outputs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .logger import get_logger

logger = get_logger(__name__)


class MarkdownOutputManager:
    """Manages markdown file outputs for interviews and pipeline stages."""
    
    def __init__(self, base_output_dir: str | Path = "outputs"):
        """Initialize the markdown output manager.
        
        Args:
            base_output_dir: Base directory for all markdown outputs (default: outputs/)
        """
        self.base_output_dir = Path(base_output_dir)
        self.run_dir: Optional[Path] = None
        
    def create_run_directory(self, project_name: str) -> Path:
        """Create a timestamped directory for this run.
        
        Args:
            project_name: Name of the project being planned
            
        Returns:
            Path to the created run directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_project_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)
        run_name = f"{timestamp}_{safe_project_name}"
        
        self.run_dir = self.base_output_dir / run_name
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created run directory: {self.run_dir}")
        
        # Create a README for this run
        readme_content = f"""# DevUssY Run: {project_name}

**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This directory contains all outputs from the DevUssY planning session.

## Contents

- `interview/` - Interview conversation and responses
- `01_project_design.md` - Initial project design
- `02_design_review.md` - Design review (if enabled)
- `03_basic_devplan.md` - Basic development plan
- `04_detailed_devplan.md` - Detailed development plan with phases
- `05_handoff_prompt.md` - Final handoff prompt
- `phases/` - Individual phase files
- `run_metadata.json` - Metadata about this run
"""
        self._write_file("README.md", readme_content)
        
        return self.run_dir
    
    def rename_run_directory(self, new_project_name: str) -> Path:
        """Rename the run directory with the actual project name.
        
        Args:
            new_project_name: The actual project name to use
            
        Returns:
            Path to the renamed directory
        """
        if not self.run_dir or not self.run_dir.exists():
            logger.warning("No existing run directory to rename")
            return self.create_run_directory(new_project_name)
        
        # Extract the timestamp from the old directory name
        old_name = self.run_dir.name
        # Timestamp is the first part before underscore
        timestamp_part = old_name.split("_")[0] + "_" + old_name.split("_")[1] if "_" in old_name else datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create new name with timestamp and actual project name
        safe_project_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in new_project_name)
        new_name = f"{timestamp_part}_{safe_project_name}"
        new_dir = self.base_output_dir / new_name
        
        # Rename the directory
        try:
            self.run_dir.rename(new_dir)
            logger.info(f"Renamed run directory from {self.run_dir} to {new_dir}")
            self.run_dir = new_dir
            
            # Update README with actual project name
            readme_content = f"""# DevUssY Run: {new_project_name}

**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This directory contains all outputs from the DevUssY planning session.

## Contents

- `interview/` - Interview conversation and responses
- `01_project_design.md` - Initial project design
- `02_design_review.md` - Design review (if enabled)
- `03_basic_devplan.md` - Basic development plan
- `04_detailed_devplan.md` - Detailed development plan with phases
- `05_handoff_prompt.md` - Final handoff prompt
- `phases/` - Individual phase files
- `run_metadata.json` - Metadata about this run
"""
            self._write_file("README.md", readme_content)
            
        except Exception as e:
            logger.error(f"Failed to rename run directory: {e}")
            # Keep using the old directory
        
        return self.run_dir
    
    def save_run_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save metadata about the run.
        
        Args:
            metadata: Dictionary containing run metadata
        """
        if not self.run_dir:
            logger.warning("Run directory not created yet, cannot save metadata")
            return
            
        metadata_with_timestamp = {
            **metadata,
            "run_timestamp": datetime.now().isoformat(),
            "output_directory": str(self.run_dir)
        }
        
        metadata_file = self.run_dir / "run_metadata.json"
        metadata_file.write_text(json.dumps(metadata_with_timestamp, indent=2), encoding="utf-8")
        logger.info(f"Saved run metadata to {metadata_file}")
    
    def save_interview_response(
        self, 
        question_number: int, 
        user_input: str, 
        llm_response: str,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Save an interview question/response pair.
        
        Args:
            question_number: Sequential number of this Q&A
            user_input: What the user typed
            llm_response: The LLM's response
            timestamp: Optional timestamp (defaults to now)
        """
        if not self.run_dir:
            logger.warning("Run directory not created yet, cannot save interview response")
            return
        
        interview_dir = self.run_dir / "interview"
        interview_dir.mkdir(exist_ok=True)
        
        if timestamp is None:
            timestamp = datetime.now()
        
        content = f"""# Interview Q&A #{question_number}

**Timestamp:** {timestamp.strftime("%Y-%m-%d %H:%M:%S")}

## User Input

{user_input}

## Assistant Response

{llm_response}

---
"""
        
        filename = f"qa_{question_number:03d}.md"
        self._write_file(f"interview/{filename}", content)
        logger.debug(f"Saved interview Q&A #{question_number}")
    
    def save_interview_summary(
        self, 
        conversation_history: List[Dict[str, str]], 
        extracted_data: Dict[str, Any]
    ) -> None:
        """Save the complete interview summary after /done.
        
        Args:
            conversation_history: Full conversation history
            extracted_data: Extracted project data
        """
        if not self.run_dir:
            logger.warning("Run directory not created yet, cannot save interview summary")
            return
        
        interview_dir = self.run_dir / "interview"
        interview_dir.mkdir(exist_ok=True)
        
        # Build the complete conversation markdown
        conversation_md = "# Complete Interview Transcript\n\n"
        conversation_md += f"**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        conversation_md += "---\n\n"
        
        for idx, msg in enumerate(conversation_history, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                conversation_md += f"## [{idx}] User\n\n{content}\n\n"
            elif role == "assistant":
                conversation_md += f"## [{idx}] Assistant\n\n{content}\n\n"
            else:
                conversation_md += f"## [{idx}] {role.title()}\n\n{content}\n\n"
            
            conversation_md += "---\n\n"
        
        self._write_file("interview/complete_transcript.md", conversation_md)
        logger.info("Saved complete interview transcript")
        
        # Save extracted data as both JSON and markdown
        extracted_json_path = interview_dir / "extracted_data.json"
        extracted_json_path.write_text(
            json.dumps(extracted_data, indent=2), 
            encoding="utf-8"
        )
        logger.info("Saved extracted interview data (JSON)")
        
        # Create a readable markdown summary
        summary_md = "# Interview Summary\n\n"
        summary_md += f"**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        summary_md += "## Extracted Project Information\n\n"
        
        for key, value in extracted_data.items():
            formatted_key = key.replace("_", " ").title()
            if isinstance(value, list):
                summary_md += f"**{formatted_key}:**\n"
                for item in value:
                    summary_md += f"- {item}\n"
                summary_md += "\n"
            elif isinstance(value, bool):
                summary_md += f"**{formatted_key}:** {'Yes' if value else 'No'}\n\n"
            else:
                summary_md += f"**{formatted_key}:** {value}\n\n"
        
        self._write_file("interview/summary.md", summary_md)
        logger.info("Saved interview summary")
    
    def save_stage_output(
        self, 
        stage_name: str, 
        content: str, 
        filename: Optional[str] = None
    ) -> Path:
        """Save output from a pipeline stage.
        
        Args:
            stage_name: Name of the stage (e.g., "project_design", "basic_devplan")
            content: Markdown content to save
            filename: Optional custom filename (will be auto-generated if not provided)
            
        Returns:
            Path to the saved file
        """
        if not self.run_dir:
            logger.warning("Run directory not created yet, cannot save stage output")
            return Path()
        
        if filename is None:
            # Auto-generate filename with numbering
            stage_mapping = {
                "project_design": "01_project_design.md",
                "design_review": "02_design_review.md",
                "basic_devplan": "03_basic_devplan.md",
                "detailed_devplan": "04_detailed_devplan.md",
                "handoff_prompt": "05_handoff_prompt.md",
            }
            filename = stage_mapping.get(stage_name, f"{stage_name}.md")
        
        # Add stage header
        header = f"""# {stage_name.replace('_', ' ').title()}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
        full_content = header + content
        
        file_path = self._write_file(filename, full_content)
        logger.info(f"Saved {stage_name} output to {filename}")
        
        return file_path
    
    def save_phase_file(self, phase_number: int, phase_name: str, content: str) -> Path:
        """Save an individual phase file.
        
        Args:
            phase_number: Phase number
            phase_name: Phase name
            content: Markdown content
            
        Returns:
            Path to the saved file
        """
        if not self.run_dir:
            logger.warning("Run directory not created yet, cannot save phase file")
            return Path()
        
        phases_dir = self.run_dir / "phases"
        phases_dir.mkdir(exist_ok=True)
        
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in phase_name)
        filename = f"phases/phase_{phase_number:02d}_{safe_name}.md"
        
        file_path = self._write_file(filename, content)
        logger.debug(f"Saved phase {phase_number} file")
        
        return file_path
    
    def _write_file(self, relative_path: str, content: str) -> Path:
        """Write a file to the run directory.
        
        Args:
            relative_path: Path relative to run directory
            content: File content
            
        Returns:
            Absolute path to the written file
        """
        if not self.run_dir:
            raise ValueError("Run directory not initialized")
        
        file_path = self.run_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        
        return file_path
    
    def get_run_directory(self) -> Optional[Path]:
        """Get the current run directory.
        
        Returns:
            Path to run directory or None if not created yet
        """
        return self.run_dir
