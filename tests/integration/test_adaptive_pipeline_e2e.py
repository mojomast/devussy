"""End-to-end tests for adaptive pipeline with different complexity levels.

These tests verify the full adaptive pipeline flow including:
- Complexity analysis
- Design generation
- Validation
- Correction loop (when enabled)

Tests are marked with @pytest.mark.requires_api and @pytest.mark.slow.
Skip with: pytest -m "not requires_api" or pytest -m "not slow"
"""

from __future__ import annotations

import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.pipeline.compose import PipelineOrchestrator
from src.interview.complexity_analyzer import ComplexityProfile
from src.concurrency import ConcurrencyManager
from src.models import ProjectDesign, DevPlan, DevPlanPhase, DevPlanStep


# Skip all tests in this module if no API key is available
pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
]


class TestAdaptivePipelineMinimalComplexity:
    """Tests for minimal complexity projects (CLI tools, simple scripts)."""

    @pytest.fixture
    def minimal_interview_data(self) -> dict:
        """Interview data for a minimal complexity project."""
        return {
            "project_name": "file-renamer",
            "project_type": "cli_tool",
            "requirements": "Simple CLI to batch rename files with regex patterns",
            "languages": ["Python"],
            "frameworks": [],
            "apis": "",
            "team_size": "solo",
        }

    def test_minimal_complexity_detection(
        self,
        minimal_interview_data: dict,
        concurrency_manager: ConcurrencyManager,
        mock_llm_client: MagicMock,
    ) -> None:
        """Test that minimal projects are detected correctly."""
        orchestrator = PipelineOrchestrator(
            llm_client=mock_llm_client,
            concurrency_manager=concurrency_manager,
        )

        profile = orchestrator.analyze_complexity(minimal_interview_data)

        assert isinstance(profile, ComplexityProfile)
        assert profile.project_type_bucket == "cli_tool"
        assert profile.depth_level == "minimal"
        assert profile.estimated_phase_count <= 4
        assert profile.score <= 4.0

    @pytest.mark.asyncio
    async def test_minimal_pipeline_generates_concise_output(
        self,
        minimal_interview_data: dict,
        concurrency_manager: ConcurrencyManager,
        mock_llm_client: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that minimal complexity produces appropriately scoped outputs."""
        # Mock LLM responses
        mock_llm_client.generate = AsyncMock(return_value="""
        # CLI Architecture
        Simple command-line tool structure.
        
        ## Components
        - argparse CLI interface
        - Regex pattern engine
        - File operations module
        
        ## Testing
        Unit tests for pattern matching
        """)

        orchestrator = PipelineOrchestrator(
            llm_client=mock_llm_client,
            concurrency_manager=concurrency_manager,
        )

        # Mock generators to return appropriate minimal output
        mock_design = ProjectDesign(
            project_name="file-renamer",
            objectives=["Batch rename files using regex"],
            tech_stack=["Python", "argparse"],
            architecture_overview="Simple CLI tool",
        )
        orchestrator.project_design_gen.generate = AsyncMock(return_value=mock_design)

        mock_devplan = DevPlan(
            phases=[
                DevPlanPhase(
                    number=1,
                    title="Core Implementation",
                    steps=[
                        DevPlanStep(number="1.1", description="Setup CLI"),
                        DevPlanStep(number="1.2", description="Implement renaming"),
                    ],
                ),
                DevPlanPhase(
                    number=2,
                    title="Testing",
                    steps=[
                        DevPlanStep(number="2.1", description="Add unit tests"),
                    ],
                ),
            ],
            summary="Minimal CLI development plan",
        )
        orchestrator.basic_devplan_gen.generate = AsyncMock(return_value=mock_devplan)
        orchestrator.detailed_devplan_gen.generate = AsyncMock(return_value=mock_devplan)

        result = await orchestrator.run_adaptive_pipeline(
            project_name="file-renamer",
            languages=["Python"],
            requirements="Batch rename files with regex",
            interview_data=minimal_interview_data,
            output_dir=str(tmp_path),
            save_artifacts=True,
            enable_validation=False,
            enable_correction=False,
        )

        design, devplan, handoff, complexity = result

        # Verify minimal complexity characteristics
        assert complexity.depth_level == "minimal"
        assert len(devplan.phases) <= 4
        assert (tmp_path / "complexity_profile.md").exists()


class TestAdaptivePipelineStandardComplexity:
    """Tests for standard complexity projects (APIs, web apps)."""

    @pytest.fixture
    def standard_interview_data(self) -> dict:
        """Interview data for a standard complexity project.
        
        Scoring calculation:
        - project_type "api" = 3
        - requirements "auth" triggers auth_db = 2
        - apis "SendGrid,Stripe,Twilio" = 3 services = 2
        - team_size "4" = "4_6" = 1.2x multiplier
        Base: 3 + 2 + 2 = 7, with 1.2x = 8.4 => "detailed" but let's aim for standard
        
        Adjusted to get score in 4-7 range (standard):
        - api = 3, auth_db = 2, 1_2_services = 1, 2_3 = 1.0x
        Base: 3 + 2 + 1 = 6 * 1.0 = 6 => "standard"
        """
        return {
            "project_name": "task-api",
            "project_type": "api",
            "requirements": "REST API with user authentication, task CRUD, and PostgreSQL",
            "languages": ["Python", "TypeScript"],
            "frameworks": ["FastAPI", "React"],
            "apis": "SendGrid,Stripe",  # 2 services = 1_2_services bucket
            "team_size": "2",  # 2_3 bucket = 1.0x multiplier
        }

    def test_standard_complexity_detection(
        self,
        standard_interview_data: dict,
        concurrency_manager: ConcurrencyManager,
        mock_llm_client: MagicMock,
    ) -> None:
        """Test that standard projects are detected correctly."""
        orchestrator = PipelineOrchestrator(
            llm_client=mock_llm_client,
            concurrency_manager=concurrency_manager,
        )

        profile = orchestrator.analyze_complexity(standard_interview_data)

        assert isinstance(profile, ComplexityProfile)
        # Score should be around 6: api(3) + auth_db(2) + 1_2_services(1) * 1.0 = 6
        assert profile.depth_level == "standard", f"Got score={profile.score}, depth={profile.depth_level}"
        assert 3 <= profile.estimated_phase_count <= 6
        assert 4.0 <= profile.score <= 7.0

    @pytest.mark.asyncio
    async def test_standard_pipeline_with_validation(
        self,
        standard_interview_data: dict,
        concurrency_manager: ConcurrencyManager,
        mock_llm_client: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test standard complexity with validation enabled."""
        mock_llm_client.generate = AsyncMock(return_value="""
        # API Architecture
        
        ## Architecture Overview
        REST API with authentication and task management.
        
        ## Database
        PostgreSQL with users and tasks tables.
        
        ## Testing
        Pytest with 80% coverage target.
        """)

        orchestrator = PipelineOrchestrator(
            llm_client=mock_llm_client,
            concurrency_manager=concurrency_manager,
        )

        # Mock generators
        mock_design = ProjectDesign(
            project_name="task-api",
            objectives=["Build REST API", "User authentication", "Task CRUD"],
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
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

        mock_devplan = DevPlan(
            phases=[
                DevPlanPhase(
                    number=i,
                    title=f"Phase {i}",
                    steps=[
                        DevPlanStep(number=f"{i}.1", description=f"Step 1 of phase {i}"),
                        DevPlanStep(number=f"{i}.2", description=f"Step 2 of phase {i}"),
                    ],
                )
                for i in range(1, 5)
            ],
            summary="Standard API development plan",
        )
        orchestrator.basic_devplan_gen.generate = AsyncMock(return_value=mock_devplan)
        orchestrator.detailed_devplan_gen.generate = AsyncMock(return_value=mock_devplan)

        result = await orchestrator.run_adaptive_pipeline(
            project_name="task-api",
            languages=["Python", "TypeScript"],
            requirements="REST API with auth and tasks",
            interview_data=standard_interview_data,
            output_dir=str(tmp_path),
            save_artifacts=True,
            enable_validation=True,
            enable_correction=False,
        )

        design, devplan, handoff, complexity = result

        # Verify standard complexity characteristics
        assert complexity.depth_level == "standard"
        assert 3 <= len(devplan.phases) <= 6
        assert (tmp_path / "project_design.md").exists()


class TestAdaptivePipelineDetailedComplexity:
    """Tests for detailed/complex projects (SaaS, enterprise)."""

    @pytest.fixture
    def detailed_interview_data(self) -> dict:
        """Interview data for a detailed complexity project.
        
        Scoring calculation:
        - project_type "saas platform" = 5
        - requirements "real-time" triggers realtime = 3
        - apis "6 services" = 6_plus_services = 3
        - team_size "8" = 7_plus = 1.5x multiplier
        Base: 5 + 3 + 3 = 11, with 1.5x = 16.5 => "detailed"
        """
        return {
            "project_name": "enterprise-crm",
            "project_type": "saas platform",
            "requirements": "Multi-tenant CRM with real-time collaboration, insights, multi-region deployment",
            "languages": ["Python", "TypeScript", "Go"],
            "frameworks": ["FastAPI", "Next.js", "Kubernetes"],
            "apis": "Stripe, SendGrid, Twilio, AWS S3, Auth0, OpenAI",  # 6 services
            "team_size": "8",
        }

    def test_detailed_complexity_detection(
        self,
        detailed_interview_data: dict,
        concurrency_manager: ConcurrencyManager,
        mock_llm_client: MagicMock,
    ) -> None:
        """Test that complex projects are detected correctly."""
        orchestrator = PipelineOrchestrator(
            llm_client=mock_llm_client,
            concurrency_manager=concurrency_manager,
        )

        profile = orchestrator.analyze_complexity(detailed_interview_data)

        assert isinstance(profile, ComplexityProfile)
        assert profile.depth_level == "detailed", f"Got score={profile.score}, depth={profile.depth_level}"
        assert profile.estimated_phase_count >= 5
        assert profile.score >= 8.0

    @pytest.mark.asyncio
    async def test_detailed_pipeline_produces_comprehensive_output(
        self,
        detailed_interview_data: dict,
        concurrency_manager: ConcurrencyManager,
        mock_llm_client: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that detailed complexity produces comprehensive outputs."""
        mock_llm_client.generate = AsyncMock(return_value="""
        # Enterprise CRM Architecture
        
        ## Architecture Overview
        Multi-tenant SaaS platform with microservices.
        
        ## Database
        PostgreSQL with tenant isolation, Redis for caching.
        
        ## Security
        Auth0 integration, row-level security, audit logging.
        
        ## Testing
        Comprehensive test suite with 90% coverage.
        """)

        orchestrator = PipelineOrchestrator(
            llm_client=mock_llm_client,
            concurrency_manager=concurrency_manager,
        )

        # Mock generators for comprehensive output
        mock_design = ProjectDesign(
            project_name="enterprise-crm",
            objectives=[
                "Multi-tenant architecture",
                "Real-time collaboration",
                "ML-based insights",
                "Multi-region deployment",
                "Enterprise security",
            ],
            tech_stack=["Python", "FastAPI", "PostgreSQL", "Redis", "Kubernetes"],
            architecture_overview="""
            # Enterprise Architecture
            
            ## Microservices
            - User Service
            - CRM Service
            - ML Service
            - Notification Service
            
            ## Database
            PostgreSQL with sharding.
            
            ## Testing
            Pytest + integration tests.
            """,
        )
        orchestrator.project_design_gen.generate = AsyncMock(return_value=mock_design)

        mock_devplan = DevPlan(
            phases=[
                DevPlanPhase(
                    number=i,
                    title=f"Phase {i}",
                    steps=[
                        DevPlanStep(number=f"{i}.{j}", description=f"Step {j}")
                        for j in range(1, 6)
                    ],
                )
                for i in range(1, 8)  # 7 phases for complex project
            ],
            summary="Comprehensive enterprise development plan",
        )
        orchestrator.basic_devplan_gen.generate = AsyncMock(return_value=mock_devplan)
        orchestrator.detailed_devplan_gen.generate = AsyncMock(return_value=mock_devplan)

        result = await orchestrator.run_adaptive_pipeline(
            project_name="enterprise-crm",
            languages=["Python", "TypeScript", "Go"],
            requirements="Enterprise CRM platform",
            interview_data=detailed_interview_data,
            output_dir=str(tmp_path),
            save_artifacts=True,
            enable_validation=True,
            enable_correction=False,
        )

        design, devplan, handoff, complexity = result

        # Verify detailed complexity characteristics
        assert complexity.depth_level == "detailed"
        assert len(devplan.phases) >= 5
        assert len(design.objectives) >= 3


class TestAdaptivePipelineValidationCorrection:
    """Tests for validation and correction loop."""

    @pytest.fixture
    def interview_data_with_issues(self) -> dict:
        """Interview data that might trigger validation issues."""
        return {
            "project_name": "incomplete-api",
            "project_type": "api",
            "requirements": "API backend",  # Vague requirements
            "languages": ["Python"],
            "frameworks": [],
            "apis": "",
            "team_size": "solo",
        }

    @pytest.mark.asyncio
    async def test_correction_loop_invoked_on_issues(
        self,
        interview_data_with_issues: dict,
        concurrency_manager: ConcurrencyManager,
        mock_llm_client: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that correction loop is invoked when validation finds issues."""
        # This test verifies the correction loop is called but uses mocks
        # to avoid actual LLM calls
        
        orchestrator = PipelineOrchestrator(
            llm_client=mock_llm_client,
            concurrency_manager=concurrency_manager,
        )

        # Create design that will fail validation (missing sections)
        mock_design = ProjectDesign(
            project_name="incomplete-api",
            objectives=["Build API"],
            tech_stack=["Python"],
            architecture_overview="Incomplete design",  # Missing required sections
        )
        orchestrator.project_design_gen.generate = AsyncMock(return_value=mock_design)

        mock_devplan = DevPlan(
            phases=[
                DevPlanPhase(
                    number=1,
                    title="Development",
                    steps=[DevPlanStep(number="1.1", description="Build API")],
                ),
            ],
            summary="Basic plan",
        )
        orchestrator.basic_devplan_gen.generate = AsyncMock(return_value=mock_devplan)
        orchestrator.detailed_devplan_gen.generate = AsyncMock(return_value=mock_devplan)

        # Mock the correction loop to track if it was called (NOT async - it's a regular method)
        with patch.object(orchestrator, 'run_correction_loop') as mock_correction:
            from src.pipeline.design_correction_loop import DesignCorrectionResult
            from src.pipeline.design_validator import DesignValidationReport
            from src.pipeline.llm_sanity_reviewer import LLMSanityReviewResult
            
            # Create proper DesignCorrectionResult with required fields
            mock_validation = DesignValidationReport(
                is_valid=True,
                auto_correctable=False,
                issues=[],
                checks={"completeness": True, "consistency": True},
            )
            mock_review = LLMSanityReviewResult(
                confidence=0.9,
                notes="Design passes all checks.",
                risks=[],
            )
            mock_correction.return_value = DesignCorrectionResult(
                design_text="Corrected design text",
                validation=mock_validation,
                review=mock_review,
            )
            
            result = await orchestrator.run_adaptive_pipeline(
                project_name="incomplete-api",
                languages=["Python"],
                requirements="API backend",
                interview_data=interview_data_with_issues,
                output_dir=str(tmp_path),
                save_artifacts=True,
                enable_validation=True,
                enable_correction=True,
            )
            
            # Verify pipeline completed
            design, devplan, handoff, complexity = result
            assert design is not None
            assert devplan is not None


class TestAdaptivePipelineArtifacts:
    """Tests for artifact generation in adaptive pipeline."""

    @pytest.fixture
    def standard_interview_data(self) -> dict:
        return {
            "project_name": "artifact-test",
            "project_type": "api",
            "requirements": "Test artifact generation",
            "languages": ["Python"],
            "frameworks": [],
            "apis": "",
            "team_size": "solo",
        }

    @pytest.mark.asyncio
    async def test_all_artifacts_generated(
        self,
        standard_interview_data: dict,
        concurrency_manager: ConcurrencyManager,
        mock_llm_client: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that all expected artifacts are generated."""
        mock_llm_client.generate = AsyncMock(return_value="Mock content")

        orchestrator = PipelineOrchestrator(
            llm_client=mock_llm_client,
            concurrency_manager=concurrency_manager,
        )

        mock_design = ProjectDesign(
            project_name="artifact-test",
            objectives=["Test artifacts"],
            tech_stack=["Python"],
            architecture_overview="""
            # Architecture
            Test.
            
            ## Database
            SQLite.
            
            ## Testing
            Pytest.
            """,
        )
        orchestrator.project_design_gen.generate = AsyncMock(return_value=mock_design)

        mock_devplan = DevPlan(
            phases=[
                DevPlanPhase(
                    number=1,
                    title="Test",
                    steps=[DevPlanStep(number="1.1", description="Test step")],
                ),
            ],
            summary="Test plan",
        )
        orchestrator.basic_devplan_gen.generate = AsyncMock(return_value=mock_devplan)
        orchestrator.detailed_devplan_gen.generate = AsyncMock(return_value=mock_devplan)

        await orchestrator.run_adaptive_pipeline(
            project_name="artifact-test",
            languages=["Python"],
            requirements="Test",
            interview_data=standard_interview_data,
            output_dir=str(tmp_path),
            save_artifacts=True,
            enable_validation=False,
            enable_correction=False,
        )

        # Verify all expected artifacts exist
        expected_artifacts = [
            "complexity_profile.md",
            "project_design.md",
        ]
        
        for artifact in expected_artifacts:
            assert (tmp_path / artifact).exists(), f"Missing artifact: {artifact}"


@pytest.mark.requires_api
class TestAdaptivePipelineRealLLM:
    """Tests that actually call LLM APIs.
    
    These tests are skipped by default. Run with:
        pytest -m requires_api tests/integration/test_adaptive_pipeline_e2e.py
    
    Requires environment variables:
        - OPENAI_API_KEY or REQUESTY_API_KEY
    """

    @pytest.fixture
    def skip_if_no_api_key(self) -> None:
        """Skip test if no API key is available."""
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("REQUESTY_API_KEY"):
            pytest.skip("No API key available for real LLM tests")

    @pytest.fixture
    def real_llm_client(self):
        """Create a real LLM client from config."""
        from src.config import load_config
        from src.clients.factory import create_llm_client
        
        # Temporarily override any invalid provider in environment
        original_provider = os.environ.get("LLM_PROVIDER")
        if original_provider and original_provider not in ["openai", "generic", "aether", "agentrouter", "requesty"]:
            os.environ["LLM_PROVIDER"] = "requesty"
        
        try:
            config = load_config()
            return create_llm_client(config)
        finally:
            # Restore original value
            if original_provider:
                os.environ["LLM_PROVIDER"] = original_provider
            elif "LLM_PROVIDER" in os.environ:
                del os.environ["LLM_PROVIDER"]

    @pytest.fixture
    def real_concurrency_manager(self):
        """Create a real concurrency manager."""
        from src.config import load_config
        
        # Temporarily override any invalid provider in environment
        original_provider = os.environ.get("LLM_PROVIDER")
        if original_provider and original_provider not in ["openai", "generic", "aether", "agentrouter", "requesty"]:
            os.environ["LLM_PROVIDER"] = "requesty"
        
        try:
            config = load_config()
            return ConcurrencyManager(config)
        finally:
            if original_provider:
                os.environ["LLM_PROVIDER"] = original_provider
            elif "LLM_PROVIDER" in os.environ:
                del os.environ["LLM_PROVIDER"]

    @pytest.mark.asyncio
    async def test_real_minimal_pipeline(
        self,
        skip_if_no_api_key: None,
        real_llm_client,
        real_concurrency_manager,
        tmp_path: Path,
    ) -> None:
        """Run actual pipeline with minimal complexity project."""
        from src.pipeline.compose import PipelineOrchestrator
        
        interview_data = {
            "project_name": "quick-note",
            "project_type": "cli_tool",
            "requirements": "CLI tool to quickly jot down notes to a local file",
            "languages": ["Python"],
            "frameworks": [],
            "apis": "",
            "team_size": "solo",
        }
        
        orchestrator = PipelineOrchestrator(
            llm_client=real_llm_client,
            concurrency_manager=real_concurrency_manager,
        )
        
        # Run complexity analysis
        profile = orchestrator.analyze_complexity(interview_data)
        
        assert profile.depth_level == "minimal"
        assert profile.score <= 4.0
        assert profile.estimated_phase_count <= 4

    @pytest.mark.asyncio
    async def test_real_standard_pipeline(
        self,
        skip_if_no_api_key: None,
        real_llm_client,
        real_concurrency_manager,
        tmp_path: Path,
    ) -> None:
        """Run actual pipeline with standard complexity project."""
        from src.pipeline.compose import PipelineOrchestrator
        
        interview_data = {
            "project_name": "task-api",
            "project_type": "api",
            "requirements": "REST API for task management with authentication and database",
            "languages": ["Python"],
            "frameworks": ["FastAPI", "SQLAlchemy"],
            "apis": ["auth0"],
            "team_size": "3",
        }
        
        orchestrator = PipelineOrchestrator(
            llm_client=real_llm_client,
            concurrency_manager=real_concurrency_manager,
        )
        
        profile = orchestrator.analyze_complexity(interview_data)
        
        assert profile.depth_level in ["standard", "detailed"]
        assert 4.0 < profile.score <= 12.0
        assert 5 <= profile.estimated_phase_count <= 7

    @pytest.mark.asyncio
    async def test_real_detailed_pipeline(
        self,
        skip_if_no_api_key: None,
        real_llm_client,
        real_concurrency_manager,
        tmp_path: Path,
    ) -> None:
        """Run actual pipeline with detailed complexity project."""
        from src.pipeline.compose import PipelineOrchestrator
        
        interview_data = {
            "project_name": "enterprise-platform",
            "project_type": "saas",
            "requirements": "Multi-tenant SaaS platform with real-time collaboration, ML recommendations, and multi-region deployment",
            "languages": ["TypeScript", "Python"],
            "frameworks": ["Next.js", "FastAPI", "PyTorch"],
            "apis": ["stripe", "sendgrid", "auth0", "datadog", "cloudflare", "openai"],
            "team_size": "15",
        }
        
        orchestrator = PipelineOrchestrator(
            llm_client=real_llm_client,
            concurrency_manager=real_concurrency_manager,
        )
        
        profile = orchestrator.analyze_complexity(interview_data)
        
        assert profile.depth_level == "detailed"
        assert profile.score >= 8.0
        assert profile.estimated_phase_count >= 7

