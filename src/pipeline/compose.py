"""Pipeline orchestration - coordinates all generation stages."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Tuple

from ..clients.factory import create_llm_client
from ..concurrency import ConcurrencyManager
from ..config import GitConfig
from ..file_manager import FileManager
from ..git_manager import GitManager
from ..llm_client import LLMClient
from ..logger import get_logger
from ..models import DevPlan, HandoffPrompt, ProjectDesign
from ..state_manager import StateManager
from .basic_devplan import BasicDevPlanGenerator
from .detailed_devplan import DetailedDevPlanGenerator
from .handoff_prompt import HandoffPromptGenerator
from .project_design import ProjectDesignGenerator

logger = get_logger(__name__)


class PipelineOrchestrator:
    """Orchestrate the full pipeline from user inputs to handoff prompt."""

    def __init__(
        self,
        llm_client: LLMClient,
        concurrency_manager: ConcurrencyManager,
        file_manager: Optional[FileManager] = None,
        git_config: Optional[GitConfig] = None,
        repo_path: Optional[Path] = None,
        config: Optional[Any] = None,
        state_manager: Optional[StateManager] = None,
    ):
        """Initialize the orchestrator.

        Args:
            llm_client: LLM client for generation (default/fallback)
            concurrency_manager: Manager for concurrent operations
            file_manager: Optional file manager for saving artifacts
            git_config: Optional Git configuration
            repo_path: Optional path to Git repository
            config: Optional full configuration for stage-specific LLM clients
            state_manager: Optional state manager for checkpoints
        """
        self.llm_client = llm_client
        self.concurrency_manager = concurrency_manager
        self.file_manager = file_manager or FileManager()
        self.git_config = git_config or GitConfig()
        self.config = config  # Store config for stage-specific clients
        self.state_manager = state_manager or StateManager()

        # Initialize Git manager if Git is enabled
        self.git_manager = None
        if self.git_config.enabled:
            self.git_manager = GitManager(repo_path)
            if not self.git_manager.is_repo():
                logger.warning("Git integration enabled but not in a Git repository")
                self.git_manager = None

        # Initialize stage-specific LLM clients
        self._initialize_stage_clients()
        
        # Initialize generators
        self._initialize_generators()

    def _initialize_stage_clients(self) -> None:
        """Initialize stage-specific LLM clients from config."""
        self.design_client = self.llm_client
        self.devplan_client = self.llm_client
        self.handoff_client = self.llm_client
        
        if self.config is None:
            logger.info("No config provided; using default client for all stages")
            return
        
        # Create stage-specific clients if configured
        try:
            design_config = self.config.get_llm_config_for_stage("design")
            if design_config != self.config.llm:
                logger.info(f"Creating stage-specific client for design: {design_config.provider}/{design_config.model}")
                # Create a temporary config object with the stage-specific LLM config
                stage_config = self.config.model_copy()
                stage_config.llm = design_config
                self.design_client = create_llm_client(stage_config)
        except Exception as e:
            logger.warning(f"Failed to create design-specific client: {e}. Using default.")
        
        try:
            devplan_config = self.config.get_llm_config_for_stage("devplan")
            if devplan_config != self.config.llm:
                logger.info(f"Creating stage-specific client for devplan: {devplan_config.provider}/{devplan_config.model}")
                stage_config = self.config.model_copy()
                stage_config.llm = devplan_config
                self.devplan_client = create_llm_client(stage_config)
        except Exception as e:
            logger.warning(f"Failed to create devplan-specific client: {e}. Using default.")
        
        try:
            handoff_config = self.config.get_llm_config_for_stage("handoff")
            if handoff_config != self.config.llm:
                logger.info(f"Creating stage-specific client for handoff: {handoff_config.provider}/{handoff_config.model}")
                stage_config = self.config.model_copy()
                stage_config.llm = handoff_config
                self.handoff_client = create_llm_client(stage_config)
        except Exception as e:
            logger.warning(f"Failed to create handoff-specific client: {e}. Using default.")

    def _initialize_generators(self) -> None:
        """Initialize/reinitialize generators with stage-specific LLM clients."""
        self.project_design_gen = ProjectDesignGenerator(self.design_client)
        self.basic_devplan_gen = BasicDevPlanGenerator(self.devplan_client)
        self.detailed_devplan_gen = DetailedDevPlanGenerator(
            self.devplan_client, self.concurrency_manager
        )
        self.handoff_gen = HandoffPromptGenerator()

    def switch_provider(self, new_provider: str) -> None:
        """Switch to a different LLM provider dynamically.

        Args:
            new_provider: Name of the new provider ('openai', 'generic', 'requesty')

        Raises:
            ValueError: If provider switching is not supported (no config available)
            ValueError: If the new provider is unsupported
        """
        if self.config is None:
            raise ValueError(
                "Provider switching requires config to be passed during initialization"
            )

        current_provider = getattr(
            getattr(self.config, "llm", None), "provider", "unknown"
        )

        if current_provider.lower() == new_provider.lower():
            logger.info(f"Already using provider: {new_provider}")
            return

        logger.info(f"Switching from {current_provider} to {new_provider}")

        # Update config with new provider
        if hasattr(self.config, "llm") and hasattr(self.config.llm, "provider"):
            self.config.llm.provider = new_provider
        else:
            logger.warning("Could not update config provider field")

        # Create new client with updated config
        try:
            new_client = create_llm_client(self.config)
            self.llm_client = new_client

            # Reinitialize all generators with new client
            self._initialize_generators()

            logger.info(f"Successfully switched to provider: {new_provider}")
        except Exception as e:
            logger.error(f"Failed to switch to provider {new_provider}: {e}")
            raise

    def get_current_provider(self) -> str:
        """Get the name of the current LLM provider.

        Returns:
            Current provider name
        """
        if self.config is None:
            return "unknown"

        return getattr(getattr(self.config, "llm", None), "provider", "unknown")

    async def run_full_pipeline(
        self,
        project_name: str,
        languages: List[str],
        requirements: str,
        frameworks: Optional[List[str]] = None,
        apis: Optional[List[str]] = None,
        output_dir: str = ".",
        save_artifacts: bool = True,
        provider_override: Optional[str] = None,
        feedback_manager: Optional[Any] = None,
        **llm_kwargs: Any,
    ) -> Tuple[ProjectDesign, DevPlan, HandoffPrompt]:
        """Run the complete pipeline from inputs to handoff prompt.

        Args:
            project_name: Name of the project
            languages: Programming languages to use
            requirements: Project requirements
            frameworks: Optional frameworks
            apis: Optional external APIs
            output_dir: Directory to save artifacts
            save_artifacts: Whether to save intermediate files
            provider_override: Optional provider to switch to before running
            feedback_manager: Optional FeedbackManager for iterative refinement
            **llm_kwargs: Additional LLM parameters

        Returns:
            Tuple of (ProjectDesign, DevPlan, HandoffPrompt)
        """
        logger.info(f"Starting full pipeline for project: {project_name}")

        # Handle provider switching if requested
        if provider_override:
            try:
                self.switch_provider(provider_override)
            except Exception as e:
                logger.error(f"Failed to switch to provider {provider_override}: {e}")
                raise

        # Stage 1: Generate project design
        logger.info("Stage 1/4: Generating project design")
        project_design = await self.project_design_gen.generate(
            project_name=project_name,
            languages=languages,
            requirements=requirements,
            frameworks=frameworks,
            apis=apis,
            **llm_kwargs,
        )

        # Save checkpoint after project design
        try:
            self.state_manager.save_checkpoint(
                checkpoint_key=f"{project_name}_pipeline",
                stage="project_design",
                data={
                    "project_design": project_design.model_dump(),
                    "project_name": project_name,
                    "languages": languages,
                    "requirements": requirements,
                    "frameworks": frameworks,
                    "apis": apis,
                },
                metadata={
                    "provider": self.get_current_provider(),
                    "output_dir": output_dir,
                    "llm_kwargs": llm_kwargs,
                },
            )
            logger.info("Saved checkpoint after project design")
        except Exception as e:
            logger.warning(f"Failed to save checkpoint after project design: {e}")

        if save_artifacts:
            self.file_manager.write_markdown(
                f"{output_dir}/project_design.md",
                project_design.architecture_overview or "No design generated",
            )
            logger.info("Saved project_design.md")

            # Commit project design if Git integration is enabled
            if self.git_manager and self.git_config.commit_after_design:
                try:
                    self.git_manager.commit_changes(
                        "feat: generate project design",
                        files=[f"{output_dir}/project_design.md"],
                    )
                    logger.info("Committed project design to Git")
                except Exception as e:
                    logger.warning(f"Failed to commit project design: {e}")

        # Stage 2: Generate basic devplan
        logger.info("Stage 2/4: Generating basic devplan")
        basic_devplan = await self.basic_devplan_gen.generate(
            project_design, feedback_manager=feedback_manager, **llm_kwargs
        )

        # Save checkpoint after basic devplan
        try:
            self.state_manager.save_checkpoint(
                checkpoint_key=f"{project_name}_pipeline",
                stage="basic_devplan",
                data={
                    "project_design": project_design.model_dump(),
                    "basic_devplan": basic_devplan.model_dump(),
                    "project_name": project_name,
                    "languages": languages,
                    "requirements": requirements,
                    "frameworks": frameworks,
                    "apis": apis,
                },
                metadata={
                    "provider": self.get_current_provider(),
                    "output_dir": output_dir,
                    "llm_kwargs": llm_kwargs,
                    "feedback_manager": feedback_manager is not None,
                },
            )
            logger.info("Saved checkpoint after basic devplan")
        except Exception as e:
            logger.warning(f"Failed to save checkpoint after basic devplan: {e}")

        # Stage 3: Generate detailed devplan
        logger.info("Stage 3/4: Generating detailed devplan")
        detailed_devplan = await self.detailed_devplan_gen.generate(
            basic_devplan,
            project_name,
            project_design.tech_stack,
            feedback_manager=feedback_manager,
            **llm_kwargs,
        )

        # Save checkpoint after detailed devplan
        try:
            self.state_manager.save_checkpoint(
                checkpoint_key=f"{project_name}_pipeline",
                stage="detailed_devplan",
                data={
                    "project_design": project_design.model_dump(),
                    "basic_devplan": basic_devplan.model_dump(),
                    "detailed_devplan": detailed_devplan.model_dump(),
                    "project_name": project_name,
                    "languages": languages,
                    "requirements": requirements,
                    "frameworks": frameworks,
                    "apis": apis,
                },
                metadata={
                    "provider": self.get_current_provider(),
                    "output_dir": output_dir,
                    "llm_kwargs": llm_kwargs,
                    "feedback_manager": feedback_manager is not None,
                },
            )
            logger.info("Saved checkpoint after detailed devplan")
        except Exception as e:
            logger.warning(f"Failed to save checkpoint after detailed devplan: {e}")

        if save_artifacts:
            devplan_md = self._devplan_to_markdown(detailed_devplan)
            self.file_manager.write_markdown(f"{output_dir}/devplan.md", devplan_md)
            logger.info("Saved devplan.md")

            # Commit devplan if Git integration is enabled
            if self.git_manager and self.git_config.commit_after_devplan:
                try:
                    self.git_manager.commit_changes(
                        "feat: generate detailed devplan with numbered steps",
                        files=[f"{output_dir}/devplan.md"],
                    )
                    logger.info("Committed devplan to Git")
                except Exception as e:
                    logger.warning(f"Failed to commit devplan: {e}")

        # Stage 4: Generate handoff prompt
        logger.info("Stage 4/4: Generating handoff prompt")
        handoff = self.handoff_gen.generate(
            devplan=detailed_devplan,
            project_name=project_name,
            project_summary=detailed_devplan.summary or "",
            architecture_notes=project_design.architecture_overview or "",
        )

        # Save checkpoint after handoff prompt
        try:
            self.state_manager.save_checkpoint(
                checkpoint_key=f"{project_name}_pipeline",
                stage="handoff_prompt",
                data={
                    "project_design": project_design.model_dump(),
                    "basic_devplan": basic_devplan.model_dump(),
                    "detailed_devplan": detailed_devplan.model_dump(),
                    "handoff_prompt": handoff.model_dump(),
                    "project_name": project_name,
                    "languages": languages,
                    "requirements": requirements,
                    "frameworks": frameworks,
                    "apis": apis,
                },
                metadata={
                    "provider": self.get_current_provider(),
                    "output_dir": output_dir,
                    "llm_kwargs": llm_kwargs,
                    "feedback_manager": feedback_manager is not None,
                },
            )
            logger.info("Saved checkpoint after handoff prompt - pipeline complete")
        except Exception as e:
            logger.warning(f"Failed to save checkpoint after handoff prompt: {e}")

        if save_artifacts:
            self.file_manager.write_markdown(
                f"{output_dir}/handoff_prompt.md", handoff.content
            )
            logger.info("Saved handoff_prompt.md")

            # Commit handoff prompt if Git integration is enabled
            if self.git_manager and self.git_config.commit_after_handoff:
                try:
                    self.git_manager.commit_changes(
                        "docs: generate handoff prompt",
                        files=[f"{output_dir}/handoff_prompt.md"],
                    )
                    logger.info("Committed handoff prompt to Git")
                except Exception as e:
                    logger.warning(f"Failed to commit handoff prompt: {e}")

        logger.info("Pipeline complete!")
        return project_design, detailed_devplan, handoff

    async def run_devplan_only(
        self,
        project_design: ProjectDesign,
        provider_override: Optional[str] = None,
        feedback_manager: Optional[Any] = None,
        **llm_kwargs: Any,
    ) -> DevPlan:
        """Generate only the devplan from an existing project design.

        Args:
            project_design: Existing project design
            provider_override: Optional provider to switch to before running
            feedback_manager: Optional FeedbackManager for iterative refinement
            **llm_kwargs: LLM parameters

        Returns:
            Complete DevPlan
        """
        logger.info("Generating devplan from existing project design")

        # Handle provider switching if requested
        if provider_override:
            try:
                self.switch_provider(provider_override)
            except Exception as e:
                logger.error(f"Failed to switch to provider {provider_override}: {e}")
                raise

        basic_devplan = await self.basic_devplan_gen.generate(
            project_design, feedback_manager=feedback_manager, **llm_kwargs
        )

        detailed_devplan = await self.detailed_devplan_gen.generate(
            basic_devplan,
            project_design.project_name,
            project_design.tech_stack,
            feedback_manager=feedback_manager,
            **llm_kwargs,
        )

        return detailed_devplan

    async def resume_from_checkpoint(
        self,
        checkpoint_key: str,
        output_dir: str = ".",
        save_artifacts: bool = True,
        provider_override: Optional[str] = None,
        feedback_manager: Optional[Any] = None,
        **llm_kwargs: Any,
    ) -> Tuple[ProjectDesign, DevPlan, HandoffPrompt]:
        """Resume pipeline execution from a checkpoint.

        Args:
            checkpoint_key: Key of the checkpoint to resume from
            output_dir: Directory to save artifacts
            save_artifacts: Whether to save intermediate files
            provider_override: Optional provider to switch to before running
            feedback_manager: Optional FeedbackManager for iterative refinement
            **llm_kwargs: Additional LLM parameters

        Returns:
            Tuple of (ProjectDesign, DevPlan, HandoffPrompt)

        Raises:
            ValueError: If checkpoint is not found or invalid
        """
        logger.info(f"Resuming pipeline from checkpoint: {checkpoint_key}")

        # Load checkpoint
        checkpoint_data = self.state_manager.resume_pipeline(checkpoint_key)
        if checkpoint_data is None:
            raise ValueError(f"Checkpoint not found: {checkpoint_key}")

        stage = checkpoint_data["stage"]
        data = checkpoint_data["data"]
        metadata = checkpoint_data.get("metadata", {})

        # Handle provider switching if requested
        if provider_override:
            try:
                self.switch_provider(provider_override)
            except Exception as e:
                logger.error(f"Failed to switch to provider {provider_override}: {e}")
                raise

        # Apply stored LLM kwargs if not overridden
        stored_kwargs = metadata.get("llm_kwargs", {})
        combined_kwargs = {**stored_kwargs, **llm_kwargs}

        # Reconstruct objects from checkpoint data
        project_design = ProjectDesign.model_validate(data["project_design"])
        project_name = data["project_name"]

        logger.info(f"Resuming from stage: {stage}")

        if stage == "project_design":
            # Resume from after project design - run remaining stages
            return await self._resume_from_project_design(
                project_design,
                data,
                output_dir,
                save_artifacts,
                feedback_manager,
                **combined_kwargs,
            )
        elif stage == "basic_devplan":
            # Resume from after basic devplan
            basic_devplan = DevPlan.model_validate(data["basic_devplan"])
            return await self._resume_from_basic_devplan(
                project_design,
                basic_devplan,
                project_name,
                output_dir,
                save_artifacts,
                feedback_manager,
                **combined_kwargs,
            )
        elif stage == "detailed_devplan":
            # Resume from after detailed devplan
            detailed_devplan = DevPlan.model_validate(data["detailed_devplan"])
            return await self._resume_from_detailed_devplan(
                project_design,
                detailed_devplan,
                project_name,
                output_dir,
                save_artifacts,
                **combined_kwargs,
            )
        elif stage == "handoff_prompt":
            # Pipeline already complete
            logger.info("Pipeline already complete at this checkpoint")
            detailed_devplan = DevPlan.model_validate(data["detailed_devplan"])
            handoff = HandoffPrompt.model_validate(data["handoff_prompt"])
            return project_design, detailed_devplan, handoff
        else:
            raise ValueError(f"Unknown checkpoint stage: {stage}")

    async def _resume_from_project_design(
        self,
        project_design: ProjectDesign,
        data: dict,
        output_dir: str,
        save_artifacts: bool,
        feedback_manager: Optional[Any] = None,
        **llm_kwargs: Any,
    ) -> Tuple[ProjectDesign, DevPlan, HandoffPrompt]:
        """Resume pipeline from project design stage."""
        project_name = data["project_name"]

        # Continue with basic devplan generation
        logger.info("Stage 2/4: Generating basic devplan (resumed)")
        basic_devplan = await self.basic_devplan_gen.generate(
            project_design, feedback_manager=feedback_manager, **llm_kwargs
        )

        # Save checkpoint after basic devplan
        self._save_basic_devplan_checkpoint(
            project_design, basic_devplan, data, **llm_kwargs
        )

        # Continue with detailed devplan
        return await self._resume_from_basic_devplan(
            project_design,
            basic_devplan,
            project_name,
            output_dir,
            save_artifacts,
            feedback_manager,
            **llm_kwargs,
        )

    async def _resume_from_basic_devplan(
        self,
        project_design: ProjectDesign,
        basic_devplan: DevPlan,
        project_name: str,
        output_dir: str,
        save_artifacts: bool,
        feedback_manager: Optional[Any] = None,
        **llm_kwargs: Any,
    ) -> Tuple[ProjectDesign, DevPlan, HandoffPrompt]:
        """Resume pipeline from basic devplan stage."""
        logger.info("Stage 3/4: Generating detailed devplan (resumed)")
        detailed_devplan = await self.detailed_devplan_gen.generate(
            basic_devplan,
            project_name,
            project_design.tech_stack,
            feedback_manager=feedback_manager,
            **llm_kwargs,
        )

        # Save checkpoint after detailed devplan
        self._save_detailed_devplan_checkpoint(
            project_design, basic_devplan, detailed_devplan, project_name, **llm_kwargs
        )

        # Save devplan artifact if requested
        if save_artifacts:
            devplan_md = self._devplan_to_markdown(detailed_devplan)
            self.file_manager.write_markdown(f"{output_dir}/devplan.md", devplan_md)
            logger.info("Saved devplan.md")

            # Commit devplan if Git integration is enabled
            if self.git_manager and self.git_config.commit_after_devplan:
                try:
                    self.git_manager.commit_changes(
                        "feat: generate detailed devplan with numbered steps",
                        files=[f"{output_dir}/devplan.md"],
                    )
                    logger.info("Committed devplan to Git")
                except Exception as e:
                    logger.warning(f"Failed to commit devplan: {e}")

        # Continue with handoff prompt
        return await self._resume_from_detailed_devplan(
            project_design,
            detailed_devplan,
            project_name,
            output_dir,
            save_artifacts,
            **llm_kwargs,
        )

    async def _resume_from_detailed_devplan(
        self,
        project_design: ProjectDesign,
        detailed_devplan: DevPlan,
        project_name: str,
        output_dir: str,
        save_artifacts: bool,
        **llm_kwargs: Any,
    ) -> Tuple[ProjectDesign, DevPlan, HandoffPrompt]:
        """Resume pipeline from detailed devplan stage."""
        logger.info("Stage 4/4: Generating handoff prompt (resumed)")
        handoff = self.handoff_gen.generate(
            devplan=detailed_devplan,
            project_name=project_name,
            project_summary=detailed_devplan.summary or "",
            architecture_notes=project_design.architecture_overview or "",
        )

        # Save final checkpoint
        self._save_handoff_checkpoint(
            project_design, detailed_devplan, handoff, project_name, **llm_kwargs
        )

        # Save handoff artifact if requested
        if save_artifacts:
            self.file_manager.write_markdown(
                f"{output_dir}/handoff_prompt.md", handoff.content
            )
            logger.info("Saved handoff_prompt.md")

            # Commit handoff prompt if Git integration is enabled
            if self.git_manager and self.git_config.commit_after_handoff:
                try:
                    self.git_manager.commit_changes(
                        "docs: generate handoff prompt",
                        files=[f"{output_dir}/handoff_prompt.md"],
                    )
                    logger.info("Committed handoff prompt to Git")
                except Exception as e:
                    logger.warning(f"Failed to commit handoff prompt: {e}")

        logger.info("Pipeline complete (resumed)!")
        return project_design, detailed_devplan, handoff

    def _save_basic_devplan_checkpoint(
        self,
        project_design: ProjectDesign,
        basic_devplan: DevPlan,
        original_data: dict,
        **llm_kwargs: Any,
    ) -> None:
        """Save checkpoint after basic devplan generation."""
        try:
            self.state_manager.save_checkpoint(
                checkpoint_key=f"{original_data['project_name']}_pipeline",
                stage="basic_devplan",
                data={
                    **original_data,
                    "basic_devplan": basic_devplan.model_dump(),
                },
                metadata={
                    "provider": self.get_current_provider(),
                    "llm_kwargs": llm_kwargs,
                },
            )
            logger.info("Saved checkpoint after basic devplan (resumed)")
        except Exception as e:
            logger.warning(
                f"Failed to save checkpoint after basic devplan (resumed): {e}"
            )

    def _save_detailed_devplan_checkpoint(
        self,
        project_design: ProjectDesign,
        basic_devplan: DevPlan,
        detailed_devplan: DevPlan,
        project_name: str,
        **llm_kwargs: Any,
    ) -> None:
        """Save checkpoint after detailed devplan generation."""
        try:
            self.state_manager.save_checkpoint(
                checkpoint_key=f"{project_name}_pipeline",
                stage="detailed_devplan",
                data={
                    "project_design": project_design.model_dump(),
                    "basic_devplan": basic_devplan.model_dump(),
                    "detailed_devplan": detailed_devplan.model_dump(),
                    "project_name": project_name,
                },
                metadata={
                    "provider": self.get_current_provider(),
                    "llm_kwargs": llm_kwargs,
                },
            )
            logger.info("Saved checkpoint after detailed devplan (resumed)")
        except Exception as e:
            logger.warning(
                f"Failed to save checkpoint after detailed devplan (resumed): {e}"
            )

    def _save_handoff_checkpoint(
        self,
        project_design: ProjectDesign,
        detailed_devplan: DevPlan,
        handoff: HandoffPrompt,
        project_name: str,
        **llm_kwargs: Any,
    ) -> None:
        """Save checkpoint after handoff prompt generation."""
        try:
            self.state_manager.save_checkpoint(
                checkpoint_key=f"{project_name}_pipeline",
                stage="handoff_prompt",
                data={
                    "project_design": project_design.model_dump(),
                    "detailed_devplan": detailed_devplan.model_dump(),
                    "handoff_prompt": handoff.model_dump(),
                    "project_name": project_name,
                },
                metadata={
                    "provider": self.get_current_provider(),
                    "llm_kwargs": llm_kwargs,
                },
            )
            logger.info(
                "Saved checkpoint after handoff prompt (resumed) - pipeline complete"
            )
        except Exception as e:
            logger.warning(
                f"Failed to save checkpoint after handoff prompt (resumed): {e}"
            )

    async def run_handoff_only(
        self, devplan: DevPlan, project_name: str, **kwargs: Any
    ) -> HandoffPrompt:
        """Generate only a handoff prompt from an existing devplan.

        Args:
            devplan: Existing development plan
            project_name: Name of the project
            **kwargs: Additional context

        Returns:
            HandoffPrompt
        """
        logger.info("Generating handoff prompt from existing devplan")
        return self.handoff_gen.generate(devplan, project_name, **kwargs)

    def _devplan_to_markdown(self, devplan: DevPlan) -> str:
        """Convert a DevPlan to markdown format.

        Args:
            devplan: The development plan

        Returns:
            Markdown string
        """
        lines = ["# Development Plan\n"]

        if devplan.summary:
            lines.append(f"## Summary\n\n{devplan.summary}\n\n---\n")

        for phase in devplan.phases:
            lines.append(f"\n## Phase {phase.number}: {phase.title}\n")

            for step in phase.steps:
                status = "✅" if step.done else "⏳"
                lines.append(f"{status} **{step.number}**: {step.description}\n")

        return "\n".join(lines)
