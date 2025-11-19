"""Test phase description extraction in BasicDevPlanGenerator."""

import pytest
from src.pipeline.basic_devplan import BasicDevPlanGenerator
from src.models import ProjectDesign


class TestPhaseDescriptionExtraction:
    """Test that phase descriptions are correctly extracted from LLM responses."""

    def test_extract_single_line_description(self):
        """Test extraction of single-line phase descriptions."""
        generator = BasicDevPlanGenerator(llm_client=None)
        
        response = """
# Development Plan

## Phase 1: Setup and Configuration

This phase sets up the initial project structure.

- Initialize repository
- Configure dependencies
- Setup CI/CD

## Phase 2: Core Implementation

Build the main application features.

- Implement API endpoints
- Create database models
- Add authentication
"""
        
        devplan = generator._parse_response(response, "test-project")
        
        assert len(devplan.phases) == 2
        assert devplan.phases[0].title == "Setup and Configuration"
        assert devplan.phases[0].description == "This phase sets up the initial project structure."
        assert devplan.phases[1].title == "Core Implementation"
        assert devplan.phases[1].description == "Build the main application features."

    def test_extract_multi_line_description(self):
        """Test extraction of multi-line phase descriptions."""
        generator = BasicDevPlanGenerator(llm_client=None)
        
        response = """
## Phase 1: Foundation

This is the first line of description.
This is the second line that should be concatenated.

- Task 1
- Task 2
"""
        
        devplan = generator._parse_response(response, "test-project")
        
        assert len(devplan.phases) == 1
        assert devplan.phases[0].description == "This is the first line of description. This is the second line that should be concatenated."

    def test_no_description_returns_none(self):
        """Test that phases without descriptions have None."""
        generator = BasicDevPlanGenerator(llm_client=None)
        
        response = """
## Phase 1: Quick Phase

- Task 1
- Task 2
"""
        
        devplan = generator._parse_response(response, "test-project")
        
        assert len(devplan.phases) == 1
        assert devplan.phases[0].description is None

    def test_description_with_markdown_formatting(self):
        """Test that markdown formatting is stripped from descriptions."""
        generator = BasicDevPlanGenerator(llm_client=None)
        
        response = """
## Phase 1: Formatted Phase

**This description** has *some* markdown **formatting**.

- Task 1
"""
        
        devplan = generator._parse_response(response, "test-project")
        
        assert len(devplan.phases) == 1
        # Asterisks should be removed
        assert "**" not in devplan.phases[0].description
        assert "*" not in devplan.phases[0].description
        assert "This description has some markdown formatting." == devplan.phases[0].description

    def test_last_phase_description(self):
        """Test that the last phase description is correctly extracted."""
        generator = BasicDevPlanGenerator(llm_client=None)
        
        response = """
## Phase 1: First

First phase description.

- Task 1

## Phase 2: Last

Last phase description here.

- Task A
- Task B
"""
        
        devplan = generator._parse_response(response, "test-project")
        
        assert len(devplan.phases) == 2
        assert devplan.phases[1].description == "Last phase description here."
