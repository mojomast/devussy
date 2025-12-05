"""Integration tests for adaptive pipeline orchestrator."""

from __future__ import annotations

import pytest
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from src.pipeline.compose import PipelineOrchestrator
from src.interview.complexity_analyzer import ComplexityProfile
from src.pipeline.design_validator import DesignValidationReport
from src.pipeline.design_correction_loop import DesignCorrectionResult
from src.concurrency import ConcurrencyManager


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create a mock LLM client."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="Mock generated content")
    client.last_usage_metadata = None
    return client


@pytest.fixture
def concurrency_manager() -> ConcurrencyManager:
    """Create a concurrency manager."""
    return ConcurrencyManager(max_concurrent=5)


@pytest.fixture
def orchestrator(mock_llm_client: MagicMock, concurrency_manager: ConcurrencyManager) -> PipelineOrchestrator:
    """Create a pipeline orchestrator with mocked dependencies."""
    return PipelineOrchestrator(
        llm_client=mock_llm_client,
        concurrency_manager=concurrency_manager,
    )


class TestComplexityAnalysis:
    """Tests for complexity analysis method."""

    def test_analyze_complexity_trivial_project(self, orchestrator: PipelineOrchestrator) -> None:
        """Test complexity analysis for a trivial CLI project."""
        interview_data = {
            "project_type": "cli_tool",
            "requirements": "Simple command-line utility",
            "apis": "",
            "team_size": "1",
        }
        
        profile = orchestrator.analyze_complexity(interview_data)
        
        assert isinstance(profile, ComplexityProfile)
        assert profile.project_type_bucket == "cli_tool"
        assert profile.depth_level == "minimal"
        assert profile.estimated_phase_count <= 5

    def test_analyze_complexity_complex_saas(self, orchestrator: PipelineOrchestrator) -> None:
        """Test complexity analysis for a complex SaaS project."""
        interview_data = {
            "project_type": "saas platform",
            "requirements": "Multi-region real-time collaboration",
            "apis": "Stripe, SendGrid, Twilio, AWS S3, Auth0",
            "team_size": "8",
        }
        
        profile = orchestrator.analyze_complexity(interview_data)
        
        assert isinstance(profile, ComplexityProfile)
        assert profile.depth_level == "detailed"
        assert profile.score >= 7
        assert profile.estimated_phase_count >= 5


class TestDesignValidation:
    """Tests for design validation method."""

    def test_validate_design_complete(self, orchestrator: PipelineOrchestrator) -> None:
        """Test validation of a complete design."""
        design_text = """
        # Project Architecture
        
        ## Architecture Overview
        This is a web application with REST API.
        
        ## Database
        PostgreSQL data model with users table.
        
        ## Testing
        Unit tests and integration tests required.
        """
        
        report = orchestrator.validate_design(design_text)
        
        assert isinstance(report, DesignValidationReport)
        assert report.checks["completeness"] is True

    def test_validate_design_incomplete(self, orchestrator: PipelineOrchestrator) -> None:
        """Test validation of an incomplete design."""
        design_text = """
        # Project
        
        This is just a simple description without proper sections.
        """
        
        report = orchestrator.validate_design(design_text)
        
        assert isinstance(report, DesignValidationReport)
        assert report.is_valid is False
        assert len(report.issues) > 0


class TestCorrectionLoop:
    """Tests for design correction loop method."""

    def test_run_correction_loop_valid_design(self, orchestrator: PipelineOrchestrator) -> None:
        """Test correction loop with already valid design."""
        design_text = """
        # Architecture Overview
        This is a standard web application.
        
        ## Database
        PostgreSQL data model.
        
        ## Testing
        Comprehensive test coverage.
        """
        
        result = orchestrator.run_correction_loop(design_text)
        
        assert isinstance(result, DesignCorrectionResult)
        assert result.validation.is_valid
        assert not result.requires_human_review
        assert not result.max_iterations_reached

    def test_run_correction_loop_with_complexity(self, orchestrator: PipelineOrchestrator) -> None:
        """Test correction loop with complexity profile."""
        design_text = """
        # Architecture
        Simple CRUD application.
        
        ## Database
        SQLite storage.
        
        ## Testing
        Basic tests.
        """
        
        profile = ComplexityProfile(
            project_type_bucket="cli_tool",
            technical_complexity_bucket="simple_crud",
            integration_bucket="standalone",
            team_size_bucket="solo",
            score=1.0,
            estimated_phase_count=3,
            depth_level="minimal",
            confidence=0.9,
        )
        
        result = orchestrator.run_correction_loop(design_text, complexity_profile=profile)
        
        assert isinstance(result, DesignCorrectionResult)


class TestMarkdownGeneration:
    """Tests for markdown generation helpers."""

    def test_complexity_profile_to_markdown(self, orchestrator: PipelineOrchestrator) -> None:
        """Test complexity profile markdown generation."""
        profile = ComplexityProfile(
            project_type_bucket="web_app",
            technical_complexity_bucket="auth_db",
            integration_bucket="1_2_services",
            team_size_bucket="2_3",
            score=6.0,
            estimated_phase_count=5,
            depth_level="standard",
            confidence=0.85,
        )
        
        markdown = orchestrator._complexity_profile_to_markdown(profile)
        
        assert "# Complexity Profile" in markdown
        assert "6.0" in markdown
        assert "standard" in markdown
        assert "web_app" in markdown

    def test_validation_report_to_markdown_valid(self, orchestrator: PipelineOrchestrator) -> None:
        """Test validation report markdown for valid design."""
        report = DesignValidationReport(
            is_valid=True,
            auto_correctable=True,
            issues=[],
            checks={"completeness": True, "consistency": True},
        )
        
        markdown = orchestrator._validation_report_to_markdown(report)
        
        assert "# Design Validation Report" in markdown
        assert "Valid**: Yes" in markdown
        assert "[PASS]" in markdown

    def test_validation_report_to_markdown_invalid(self, orchestrator: PipelineOrchestrator) -> None:
        """Test validation report markdown for invalid design."""
        from src.pipeline.design_validator import DesignValidationIssue
        
        report = DesignValidationReport(
            is_valid=False,
            auto_correctable=True,
            issues=[
                DesignValidationIssue(
                    code="completeness.missing_sections",
                    message="Missing required sections",
                    auto_correctable=True,
                )
            ],
            checks={"completeness": False, "consistency": True},
        )
        
        markdown = orchestrator._validation_report_to_markdown(report)
        
        assert "Valid**: No" in markdown
        assert "[FAIL]" in markdown
        assert "## Issues" in markdown
        assert "completeness.missing_sections" in markdown


class TestAdaptivePipelineIntegration:
    """Integration tests for full adaptive pipeline."""

    @pytest.mark.asyncio
    async def test_adaptive_pipeline_basic_flow(
        self,
        mock_llm_client: MagicMock,
        concurrency_manager: ConcurrencyManager,
        tmp_path: Path,
    ) -> None:
        """Test basic adaptive pipeline flow with mocked LLM."""
        from src.models import ProjectDesign
        
        # Setup mock responses
        mock_llm_client.generate = AsyncMock(return_value="""
        # Architecture Overview
        A simple web application with REST API.
        
        ## Database
        PostgreSQL with users table.
        
        ## Testing
        Unit tests and integration tests.
        """)
        
        orchestrator = PipelineOrchestrator(
            llm_client=mock_llm_client,
            concurrency_manager=concurrency_manager,
        )
        
        # Mock the project design generator
        mock_design = ProjectDesign(
            project_name="TestProject",
            objectives=["Build simple app"],
            tech_stack=["Python", "FastAPI"],
            architecture_overview="""
            # Architecture
            REST API backend.
            
            ## Database
            PostgreSQL.
            
            ## Testing
            Pytest.
            """,
        )
        orchestrator.project_design_gen.generate = AsyncMock(return_value=mock_design)
        
        # Mock devplan generators
        from src.models import DevPlan, DevPlanPhase, DevPlanStep
        mock_devplan = DevPlan(
            phases=[
                DevPlanPhase(
                    number=1,
                    title="Setup",
                    steps=[DevPlanStep(number="1.1", description="Initialize project")],
                )
            ],
            summary="Test devplan",
        )
        orchestrator.basic_devplan_gen.generate = AsyncMock(return_value=mock_devplan)
        orchestrator.detailed_devplan_gen.generate = AsyncMock(return_value=mock_devplan)
        
        interview_data = {
            "project_type": "api",
            "requirements": "Simple REST API",
            "apis": "",
            "team_size": "1",
        }
        
        # Run adaptive pipeline
        result = await orchestrator.run_adaptive_pipeline(
            project_name="TestProject",
            languages=["Python"],
            requirements="Build a simple API",
            interview_data=interview_data,
            output_dir=str(tmp_path),
            save_artifacts=True,
            enable_validation=True,
            enable_correction=False,  # Skip correction for faster test
        )
        
        project_design, devplan, handoff, complexity_profile = result
        
        # Verify results
        assert project_design is not None
        assert devplan is not None
        assert handoff is not None
        assert complexity_profile is not None
        
        # Verify artifacts were saved
        assert (tmp_path / "complexity_profile.md").exists()
        assert (tmp_path / "project_design.md").exists()
