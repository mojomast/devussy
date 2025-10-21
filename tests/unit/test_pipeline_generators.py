"""Tests for pipeline generator modules.

Tests for project_design.py, basic_devplan.py, detailed_devplan.py, and handoff_prompt.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models import DevPlan, DevPlanPhase, DevPlanStep, ProjectDesign
from src.pipeline.basic_devplan import BasicDevPlanGenerator
from src.pipeline.detailed_devplan import DetailedDevPlanGenerator
from src.pipeline.handoff_prompt import HandoffPromptGenerator
from src.pipeline.project_design import ProjectDesignGenerator


# =====================================================================
# ProjectDesignGenerator Tests
# =====================================================================


class TestProjectDesignGenerator:
    """Tests for ProjectDesignGenerator class."""

    @pytest.mark.asyncio
    async def test_generate_basic_design(self, mock_llm_client):
        """Test generating a basic project design."""
        # Mock LLM response with structured markdown
        mock_response = """
# Objectives
- Create a web application
- Build RESTful API

# Technology Stack
- Python
- FastAPI
- PostgreSQL

# Architecture
Microservices architecture with API gateway

# Dependencies
- pydantic
- sqlalchemy

# Challenges
- Performance optimization
- Security concerns

# Mitigations
- Use caching
- Implement authentication
"""
        mock_llm_client.generate_completion = AsyncMock(return_value=mock_response)

        generator = ProjectDesignGenerator(mock_llm_client)
        design = await generator.generate(
            project_name="test-project",
            languages=["Python"],
            requirements="Build a web app",
        )

        # Verify LLM was called
        mock_llm_client.generate_completion.assert_called_once()

        # Verify design structure
        assert isinstance(design, ProjectDesign)
        assert design.project_name == "test-project"
        assert "Create a web application" in design.objectives
        assert "Build RESTful API" in design.objectives
        assert "Python" in design.tech_stack
        assert "FastAPI" in design.tech_stack
        assert "Microservices architecture" in design.architecture_overview
        assert "pydantic" in design.dependencies
        assert "Performance optimization" in design.challenges

    @pytest.mark.asyncio
    async def test_generate_with_optional_params(self, mock_llm_client):
        """Test generating design with frameworks and APIs."""
        mock_response = """
# Objectives
- Build application

# Technology Stack
- Python
"""
        mock_llm_client.generate_completion = AsyncMock(return_value=mock_response)

        generator = ProjectDesignGenerator(mock_llm_client)
        design = await generator.generate(
            project_name="test-project",
            languages=["Python", "JavaScript"],
            requirements="Build app",
            frameworks=["React", "FastAPI"],
            apis=["Stripe", "OpenAI"],
        )

        # Verify all parameters were used in template context
        call_args = mock_llm_client.generate_completion.call_args
        prompt = call_args[0][0]
        assert "React" in prompt or "FastAPI" in prompt

    @pytest.mark.asyncio
    async def test_parse_response_with_valid_markdown(self, mock_llm_client):
        """Test parsing a well-formatted markdown response."""
        mock_response = """
# Project Objectives
- Objective 1
- Objective 2

# Technology Stack
- Tech 1
- Tech 2

# Architecture Overview
This is the architecture description
spanning multiple lines.

# Project Dependencies
- Dependency 1
- Dependency 2

# Potential Challenges
- Challenge 1
- Mitigation: Solution 1
"""
        mock_llm_client.generate_completion = AsyncMock(return_value=mock_response)

        generator = ProjectDesignGenerator(mock_llm_client)
        design = await generator.generate(
            project_name="test-project",
            languages=["Python"],
            requirements="Test",
        )

        assert len(design.objectives) == 2
        assert "Objective 1" in design.objectives
        assert len(design.tech_stack) == 2
        assert "Tech 1" in design.tech_stack
        assert "architecture description" in design.architecture_overview
        assert len(design.dependencies) == 2

    @pytest.mark.asyncio
    async def test_parse_response_with_empty_sections(self, mock_llm_client):
        """Test parsing response with missing/empty sections."""
        mock_response = """
# Some Random Header
Random content without proper structure
"""
        mock_llm_client.generate_completion = AsyncMock(return_value=mock_response)

        generator = ProjectDesignGenerator(mock_llm_client)
        design = await generator.generate(
            project_name="test-project",
            languages=["Python"],
            requirements="Test",
        )

        # Should have default values
        assert design.project_name == "test-project"
        assert design.objectives == ["No objectives parsed"]
        assert design.tech_stack == ["No tech stack parsed"]
        # Architecture should fallback to full response
        assert "Random content" in design.architecture_overview

    @pytest.mark.asyncio
    async def test_generate_with_llm_kwargs(self, mock_llm_client):
        """Test passing additional LLM kwargs."""
        mock_response = "# Objectives\n- Test"
        mock_llm_client.generate_completion = AsyncMock(return_value=mock_response)

        generator = ProjectDesignGenerator(mock_llm_client)
        await generator.generate(
            project_name="test",
            languages=["Python"],
            requirements="Test",
            temperature=0.7,
            max_tokens=500,
        )

        # Verify kwargs were passed to LLM
        call_args = mock_llm_client.generate_completion.call_args
        assert call_args[1]["temperature"] == 0.7
        assert call_args[1]["max_tokens"] == 500

    @pytest.mark.asyncio
    async def test_generate_handles_llm_error(self, mock_llm_client):
        """Test error handling when LLM fails."""
        mock_llm_client.generate_completion = AsyncMock(
            side_effect=Exception("LLM API error")
        )

        generator = ProjectDesignGenerator(mock_llm_client)

        with pytest.raises(Exception, match="LLM API error"):
            await generator.generate(
                project_name="test",
                languages=["Python"],
                requirements="Test",
            )


# =====================================================================
# BasicDevPlanGenerator Tests
# =====================================================================


class TestBasicDevPlanGenerator:
    """Tests for BasicDevPlanGenerator class."""

    @pytest.mark.asyncio
    async def test_generate_basic_devplan(
        self, mock_llm_client, sample_project_design
    ):
        """Test generating a basic devplan from project design."""
        mock_response = """
Phase 1: Setup Phase
- Set up repository
- Install dependencies

Phase 2: Development Phase
- Implement features
- Write tests

Phase 3: Deployment Phase
- Deploy application
- Monitor performance
"""
        mock_llm_client.generate_completion = AsyncMock(return_value=mock_response)

        generator = BasicDevPlanGenerator(mock_llm_client)
        devplan = await generator.generate(sample_project_design)

        # Verify structure
        assert isinstance(devplan, DevPlan)
        assert len(devplan.phases) == 3
        assert devplan.phases[0].number == 1
        assert devplan.phases[0].title == "Setup Phase"
        assert devplan.phases[1].number == 2
        assert devplan.phases[1].title == "Development Phase"
        assert devplan.phases[2].number == 3
        assert devplan.phases[2].title == "Deployment Phase"

    @pytest.mark.asyncio
    async def test_generate_with_feedback_manager(
        self, mock_llm_client, sample_project_design
    ):
        """Test generating devplan with feedback manager."""
        mock_response = "Phase 1: Test Phase"
        mock_llm_client.generate_completion = AsyncMock(return_value=mock_response)

        mock_feedback_manager = MagicMock()
        mock_feedback_manager.apply_corrections_to_prompt.return_value = (
            "Corrected prompt"
        )

        generator = BasicDevPlanGenerator(mock_llm_client)
        devplan = await generator.generate(
            sample_project_design, feedback_manager=mock_feedback_manager
        )

        # Verify feedback manager was used
        mock_feedback_manager.apply_corrections_to_prompt.assert_called_once()
        assert isinstance(devplan, DevPlan)

    @pytest.mark.asyncio
    async def test_parse_response_various_formats(self, mock_llm_client):
        """Test parsing phases in different formats."""
        # Test with asterisks
        mock_response1 = "**Phase 1: Setup**\n- Item 1"
        # Test without colon
        mock_response2 = "Phase 1 Setup\n- Item 1"
        # Test with extra whitespace
        mock_response3 = "  Phase 1:  Setup  \n- Item 1"

        for mock_response in [mock_response1, mock_response2, mock_response3]:
            mock_llm_client.generate_completion = AsyncMock(
                return_value=mock_response
            )
            generator = BasicDevPlanGenerator(mock_llm_client)

            # Use a minimal ProjectDesign for testing
            design = ProjectDesign(
                project_name="test",
                objectives=["Test"],
                tech_stack=["Python"],
                architecture_overview="Test",
            )

            devplan = await generator.generate(design)
            assert len(devplan.phases) >= 1

    @pytest.mark.asyncio
    async def test_parse_response_no_phases(
        self, mock_llm_client, sample_project_design
    ):
        """Test handling response with no recognizable phases."""
        mock_response = """
Some random text without phase headers.
Just unstructured content.
"""
        mock_llm_client.generate_completion = AsyncMock(return_value=mock_response)

        generator = BasicDevPlanGenerator(mock_llm_client)
        devplan = await generator.generate(sample_project_design)

        # Should create default phase
        assert len(devplan.phases) == 1
        assert devplan.phases[0].number == 1
        assert devplan.phases[0].title == "Implementation"

    @pytest.mark.asyncio
    async def test_generate_with_llm_kwargs(
        self, mock_llm_client, sample_project_design
    ):
        """Test passing LLM kwargs."""
        mock_response = "Phase 1: Test"
        mock_llm_client.generate_completion = AsyncMock(return_value=mock_response)

        generator = BasicDevPlanGenerator(mock_llm_client)
        await generator.generate(
            sample_project_design, temperature=0.5, max_tokens=1000
        )

        # Verify kwargs passed to LLM
        call_args = mock_llm_client.generate_completion.call_args
        assert call_args[1]["temperature"] == 0.5
        assert call_args[1]["max_tokens"] == 1000


# =====================================================================
# DetailedDevPlanGenerator Tests
# =====================================================================


class TestDetailedDevPlanGenerator:
    """Tests for DetailedDevPlanGenerator class."""

    @pytest.mark.asyncio
    async def test_generate_detailed_devplan(
        self, mock_llm_client, concurrency_manager, sample_devplan
    ):
        """Test generating detailed steps for devplan."""
        mock_response = """
1.1: Create project directory structure
1.2: Initialize git repository
1.3: Set up virtual environment
"""
        mock_llm_client.generate_completion = AsyncMock(return_value=mock_response)

        generator = DetailedDevPlanGenerator(mock_llm_client, concurrency_manager)
        detailed = await generator.generate(
            sample_devplan, project_name="test-project"
        )

        # Verify structure
        assert isinstance(detailed, DevPlan)
        assert len(detailed.phases) == 1
        assert len(detailed.phases[0].steps) == 3
        assert detailed.phases[0].steps[0].number == "1.1"
        assert "directory structure" in detailed.phases[0].steps[0].description

    @pytest.mark.asyncio
    async def test_generate_multiple_phases(
        self, mock_llm_client, concurrency_manager, sample_detailed_devplan
    ):
        """Test generating details for multiple phases concurrently."""

        async def mock_generate(prompt, **kwargs):
            # Extract phase number from prompt
            if "Phase 1" in prompt or "phase_number: 1" in prompt:
                return "1.1: Step one\n1.2: Step two"
            elif "Phase 2" in prompt or "phase_number: 2" in prompt:
                return "2.1: Step one\n2.2: Step two"
            else:
                return "3.1: Step one\n3.2: Step two"

        mock_llm_client.generate_completion = AsyncMock(side_effect=mock_generate)

        generator = DetailedDevPlanGenerator(mock_llm_client, concurrency_manager)
        detailed = await generator.generate(
            sample_detailed_devplan, project_name="test-project"
        )

        # All phases should have detailed steps
        assert len(detailed.phases) == 3
        for phase in detailed.phases:
            assert len(phase.steps) >= 2

    @pytest.mark.asyncio
    async def test_generate_with_tech_stack(
        self, mock_llm_client, concurrency_manager, sample_devplan
    ):
        """Test generating with tech stack context."""
        mock_response = "1.1: Install Python dependencies"
        mock_llm_client.generate_completion = AsyncMock(return_value=mock_response)

        generator = DetailedDevPlanGenerator(mock_llm_client, concurrency_manager)
        await generator.generate(
            sample_devplan,
            project_name="test-project",
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
        )

        # Verify tech stack was in prompt
        call_args = mock_llm_client.generate_completion.call_args
        prompt = call_args[0][0]
        assert "Python" in prompt or "tech_stack" in prompt.lower()

    @pytest.mark.asyncio
    async def test_generate_with_feedback_manager(
        self, mock_llm_client, concurrency_manager, sample_devplan
    ):
        """Test generating with feedback manager."""
        mock_response = "1.1: Test step"
        mock_llm_client.generate_completion = AsyncMock(return_value=mock_response)

        mock_feedback_manager = MagicMock()
        mock_feedback_manager.apply_corrections_to_prompt.return_value = (
            "Corrected prompt"
        )
        mock_feedback_manager.preserve_manual_edits.return_value = sample_devplan

        generator = DetailedDevPlanGenerator(mock_llm_client, concurrency_manager)
        detailed = await generator.generate(
            sample_devplan,
            project_name="test-project",
            feedback_manager=mock_feedback_manager,
        )

        # Verify feedback manager methods were called
        mock_feedback_manager.apply_corrections_to_prompt.assert_called()
        mock_feedback_manager.preserve_manual_edits.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_steps_various_formats(
        self, mock_llm_client, concurrency_manager, sample_devplan
    ):
        """Test parsing steps in various formats."""
        # Test different step formats
        responses = [
            "1.1: Step with colon",
            "1.2 Step without colon",
            "1.3:Step with no space",
            "  1.4:  Step with whitespace  ",
        ]

        for response in responses:
            mock_llm_client.generate_completion = AsyncMock(return_value=response)
            generator = DetailedDevPlanGenerator(mock_llm_client, concurrency_manager)
            detailed = await generator.generate(sample_devplan, project_name="test")

            # Should parse at least one step
            assert len(detailed.phases[0].steps) >= 1

    @pytest.mark.asyncio
    async def test_parse_steps_no_steps_found(
        self, mock_llm_client, concurrency_manager, sample_devplan
    ):
        """Test handling when no steps are parsed."""
        mock_response = """
Some random content without step numbers.
Just plain text.
"""
        mock_llm_client.generate_completion = AsyncMock(return_value=mock_response)

        generator = DetailedDevPlanGenerator(mock_llm_client, concurrency_manager)
        detailed = await generator.generate(sample_devplan, project_name="test")

        # Should create placeholder step
        assert len(detailed.phases[0].steps) == 1
        assert "Implement phase requirements" in detailed.phases[0].steps[0].description

    @pytest.mark.asyncio
    async def test_concurrent_execution(
        self, mock_llm_client, concurrency_manager, sample_detailed_devplan
    ):
        """Test that phases are processed concurrently."""
        call_count = 0

        async def mock_generate(prompt, **kwargs):
            nonlocal call_count
            call_count += 1
            # Simulate different phases
            return f"{call_count}.1: Step for phase {call_count}"

        mock_llm_client.generate_completion = AsyncMock(side_effect=mock_generate)

        generator = DetailedDevPlanGenerator(mock_llm_client, concurrency_manager)
        await generator.generate(sample_detailed_devplan, project_name="test")

        # Should have called LLM once per phase
        assert call_count == len(sample_detailed_devplan.phases)


# =====================================================================
# HandoffPromptGenerator Tests
# =====================================================================


class TestHandoffPromptGenerator:
    """Tests for HandoffPromptGenerator class."""

    def test_generate_basic_handoff(self, sample_devplan):
        """Test generating basic handoff prompt."""
        generator = HandoffPromptGenerator()
        handoff = generator.generate(
            devplan=sample_devplan,
            project_name="test-project",
            project_summary="Test project summary",
        )

        # Verify structure
        assert handoff.content
        assert "test-project" in handoff.content
        assert len(handoff.next_steps) > 0

    def test_generate_with_completed_phases(self):
        """Test handoff with completed phases."""
        # Create devplan with completed steps
        completed_phase = DevPlanPhase(
            number=1,
            title="Setup Phase",
            steps=[
                DevPlanStep(number="1.1", description="Step 1", done=True),
                DevPlanStep(number="1.2", description="Step 2", done=True),
            ],
        )
        in_progress_phase = DevPlanPhase(
            number=2,
            title="Development Phase",
            steps=[
                DevPlanStep(number="2.1", description="Step 1", done=True),
                DevPlanStep(number="2.2", description="Step 2", done=False),
            ],
        )
        devplan = DevPlan(
            summary="Test plan", phases=[completed_phase, in_progress_phase]
        )

        generator = HandoffPromptGenerator()
        handoff = generator.generate(
            devplan=devplan,
            project_name="test-project",
        )

        assert handoff.content
        # Should identify completed and in-progress phases
        assert "Setup Phase" in handoff.content or "Phase 1" in handoff.content

    def test_generate_with_all_notes(self, sample_devplan):
        """Test generating with all optional notes."""
        generator = HandoffPromptGenerator()
        handoff = generator.generate(
            devplan=sample_devplan,
            project_name="test-project",
            project_summary="Test summary",
            architecture_notes="Microservices architecture",
            dependencies_notes="FastAPI, PostgreSQL",
            config_notes="Environment variables in .env",
        )

        assert "test-project" in handoff.content
        # Architecture notes should be in content
        assert "architecture" in handoff.content.lower()

    def test_get_next_steps_limit(self):
        """Test limiting number of next steps."""
        # Create devplan with many steps
        steps = [
            DevPlanStep(number=f"1.{i}", description=f"Step {i}", done=False)
            for i in range(1, 20)
        ]
        phase = DevPlanPhase(number=1, title="Phase 1", steps=steps)
        devplan = DevPlan(summary="Test", phases=[phase])

        generator = HandoffPromptGenerator()
        handoff = generator.generate(
            devplan=devplan,
            project_name="test-project",
        )

        # Should limit to 5 steps by default
        assert len(handoff.next_steps) == 5

    def test_is_phase_complete(self):
        """Test phase completion detection."""
        generator = HandoffPromptGenerator()

        # Complete phase
        complete_phase = DevPlanPhase(
            number=1,
            title="Phase",
            steps=[
                DevPlanStep(number="1.1", description="Step 1", done=True),
                DevPlanStep(number="1.2", description="Step 2", done=True),
            ],
        )
        assert generator._is_phase_complete(complete_phase) is True

        # Incomplete phase
        incomplete_phase = DevPlanPhase(
            number=1,
            title="Phase",
            steps=[
                DevPlanStep(number="1.1", description="Step 1", done=True),
                DevPlanStep(number="1.2", description="Step 2", done=False),
            ],
        )
        assert generator._is_phase_complete(incomplete_phase) is False

        # Phase with no steps
        empty_phase = DevPlanPhase(number=1, title="Phase", steps=[])
        assert generator._is_phase_complete(empty_phase) is False

    def test_get_in_progress_phase(self):
        """Test finding in-progress phase."""
        generator = HandoffPromptGenerator()

        phases = [
            DevPlanPhase(
                number=1,
                title="Complete Phase",
                steps=[
                    DevPlanStep(number="1.1", description="Step 1", done=True),
                ],
            ),
            DevPlanPhase(
                number=2,
                title="In Progress Phase",
                steps=[
                    DevPlanStep(number="2.1", description="Step 1", done=True),
                    DevPlanStep(number="2.2", description="Step 2", done=False),
                ],
            ),
            DevPlanPhase(
                number=3,
                title="Not Started Phase",
                steps=[
                    DevPlanStep(number="3.1", description="Step 1", done=False),
                ],
            ),
        ]

        in_progress = generator._get_in_progress_phase(phases)

        assert in_progress is not None
        assert in_progress["number"] == 2
        assert in_progress["title"] == "In Progress Phase"
        assert len(in_progress["completed_steps"]) == 1
        assert len(in_progress["remaining_steps"]) == 1

    def test_get_next_steps_across_phases(self):
        """Test getting next steps from multiple phases."""
        generator = HandoffPromptGenerator()

        phases = [
            DevPlanPhase(
                number=1,
                title="Phase 1",
                steps=[
                    DevPlanStep(number="1.1", description="Done step", done=True),
                    DevPlanStep(number="1.2", description="Next step 1", done=False),
                ],
            ),
            DevPlanPhase(
                number=2,
                title="Phase 2",
                steps=[
                    DevPlanStep(number="2.1", description="Next step 2", done=False),
                    DevPlanStep(number="2.2", description="Next step 3", done=False),
                ],
            ),
        ]

        next_steps = generator._get_next_steps(phases, limit=3)

        assert len(next_steps) == 3
        assert next_steps[0]["number"] == "1.2"
        assert next_steps[1]["number"] == "2.1"
        assert next_steps[2]["number"] == "2.2"

    def test_generate_with_no_incomplete_steps(self):
        """Test handoff when all steps are complete."""
        complete_phase = DevPlanPhase(
            number=1,
            title="Phase",
            steps=[
                DevPlanStep(number="1.1", description="Step 1", done=True),
                DevPlanStep(number="1.2", description="Step 2", done=True),
            ],
        )
        devplan = DevPlan(summary="Test", phases=[complete_phase])

        generator = HandoffPromptGenerator()
        handoff = generator.generate(
            devplan=devplan,
            project_name="test-project",
        )

        # Should still generate handoff even if all complete
        assert handoff.content
        assert len(handoff.next_steps) == 0  # No incomplete steps

    def test_next_step_truncation(self):
        """Test that long step descriptions are truncated."""
        generator = HandoffPromptGenerator()

        long_description = "A" * 150  # Very long description
        phase = DevPlanPhase(
            number=1,
            title="Phase",
            steps=[
                DevPlanStep(number="1.1", description=long_description, done=False),
            ],
        )

        next_steps = generator._get_next_steps([phase])

        # Title should be truncated to 80 chars
        assert len(next_steps[0]["title"]) == 80
        # But full description should be preserved
        assert len(next_steps[0]["description"]) == 150
