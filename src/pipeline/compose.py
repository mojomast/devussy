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
from ..progress_reporter import PipelineProgressReporter
from ..state_manager import StateManager
from .basic_devplan import BasicDevPlanGenerator
from .detailed_devplan import DetailedDevPlanGenerator
from .handoff_prompt import HandoffPromptGenerator
from .design_review import DesignReviewRefiner
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
        progress_reporter: Optional[PipelineProgressReporter] = None,
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
            progress_reporter: Optional progress reporter for visual feedback
        """
        self.llm_client = llm_client
        self.concurrency_manager = concurrency_manager
        self.file_manager = file_manager or FileManager()
        self.git_config = git_config or GitConfig()
        self.config = config  # Store config for stage-specific clients
        self.state_manager = state_manager or StateManager()
        self.progress_reporter = progress_reporter or PipelineProgressReporter()

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
            # Align design stage with devplan stage when no explicit design override is set
            if self.config.design_llm is None and self.config.devplan_llm is not None:
                logger.info(
                    f"No explicit design model configured; aligning design stage with devplan: {self.config.devplan_llm.provider}/{self.config.devplan_llm.model}"
                )
                design_config = self.config.get_llm_config_for_stage("devplan")
            else:
                design_config = self.config.get_llm_config_for_stage("design")

            # Only create a new client if the design config differs from the base config
            if design_config.provider != self.config.llm.provider or design_config.model != self.config.llm.model:
                logger.info(
                    f"Creating stage-specific client for design: {design_config.provider}/{design_config.model}"
                )
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
        # Use devplan client for project design generation unless a design-specific override exists.
        design_generation_client = self.design_client
        try:
            if self.config is not None and getattr(self.config, "design_llm", None) is None:
                # No explicit design override; align design generation with devplan phase
                design_generation_client = self.devplan_client
                logger.info("Using devplan client for project design generation (aligned with devplan phase)")
        except Exception:
            # If anything goes wrong, fall back to the design client
            pass

        self.project_design_gen = ProjectDesignGenerator(design_generation_client)
        self.basic_devplan_gen = BasicDevPlanGenerator(self.devplan_client)
        self.detailed_devplan_gen = DetailedDevPlanGenerator(
            self.devplan_client, self.concurrency_manager
        )
        self.handoff_gen = HandoffPromptGenerator()
        self.design_review_refiner = DesignReviewRefiner(self.devplan_client)

    def _write_rerun_command_file(
        self,
        project_name: str,
        languages: List[str],
        requirements: str,
        frameworks: Optional[List[str]],
        apis: Optional[List[str]],
        output_dir: str,
    ) -> None:
        """Write a small helper file with CLI commands to rerun without interview."""
        try:
            # Prepare flag values
            lang_csv = ",".join(languages or [])
            fw_csv = ",".join(frameworks or []) if frameworks else ""
            api_csv = ",".join(apis or []) if apis else ""
            # Normalize requirements to single line
            req = (requirements or "").replace("\n", " ").strip()

            # Build a full-args command (bypasses interview entirely)
            parts = [
                "devussy run-full-pipeline",
                f"--name \"{project_name}\"",
                f"--languages \"{lang_csv}\"",
                f"--requirements \"{req}\"",
            ]
            if fw_csv:
                parts.append(f"--frameworks \"{fw_csv}\"")
            if api_csv:
                parts.append(f"--apis \"{api_csv}\"")
            parts.append(f"--output-dir \"{output_dir}\"")
            parts.append("--verbose")
            full_cmd = " ".join(parts)

            # Also provide a resume-from command that continues after design
            resume_cmd = (
                f"devussy run-full-pipeline --resume-from \"{project_name}_pipeline\" "
                f"--output-dir \"{output_dir}\" --verbose"
            )

            content = (
                full_cmd
                + "\n"
                + resume_cmd
                + "\n"
            )
            self.file_manager.write_markdown(f"{output_dir}/rerun_commands.txt", content)
            logger.info("Wrote rerun_commands.txt with CLI shortcuts")
        except Exception as e:
            logger.warning(f"Failed to write rerun command file: {e}")

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
        pre_review: bool = False,
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
        
        # Show pipeline start
        self.progress_reporter.start_pipeline(project_name)
        # Start persistent status bar at bottom (model/tokens/stage)
        self.progress_reporter.start_status()

        # Handle provider switching if requested
        if provider_override:
            try:
                self.switch_provider(provider_override)
            except Exception as e:
                logger.error(f"Failed to switch to provider {provider_override}: {e}")
                self.progress_reporter.display_error(str(e))
                raise

        # Stage 1: Generate project design
        self.progress_reporter.start_stage("Project Design", 1)
        logger.info("Stage 1/4: Generating project design")
        # Live spinner while LLM works
        with self.progress_reporter.create_spinner_context("Generating project design..."):
            project_design = await self.project_design_gen.generate(
                project_name=project_name,
                languages=languages,
                requirements=requirements,
                frameworks=frameworks,
                apis=apis,
                **llm_kwargs,
            )
        
        # Update token usage if available
        self._update_progress_tokens(self.design_client)
        self.progress_reporter.end_stage("Project Design")

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
            self.progress_reporter.show_checkpoint_saved(
                f"{project_name}_pipeline", "project_design"
            )
        except Exception as e:
            logger.warning(f"Failed to save checkpoint after project design: {e}")

        if save_artifacts:
            design_content = project_design.architecture_overview or "No design generated"
            self.file_manager.write_markdown(
                f"{output_dir}/project_design.md",
                design_content,
            )
            logger.info("Saved project_design.md")
            self.progress_reporter.report_file_created(
                f"{output_dir}/project_design.md",
                "Project Design",
                len(design_content)
            )
            # Write helper commands to rerun without interview / resume from checkpoint
            try:
                self._write_rerun_command_file(
                    project_name=project_name,
                    languages=languages,
                    requirements=requirements,
                    frameworks=frameworks,
                    apis=apis,
                    output_dir=output_dir,
                )
            except Exception as e:
                logger.warning(f"Failed to write rerun_commands.txt: {e}")

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

        # Optional: Pre-review design with devplan model to catch issues early
        if pre_review:
            with self.progress_reporter.create_spinner_context(
                "Reviewing project design for compatibility/workflow/backend issues..."
            ):
                try:
                    updated_design, review_md, changed = await self.design_review_refiner.refine(
                        project_design, **llm_kwargs
                    )
                    if save_artifacts:
                        self.file_manager.write_markdown(f"{output_dir}/design_review.md", review_md)
                        self.progress_reporter.report_file_created(
                            f"{output_dir}/design_review.md", "Design Review", len(review_md)
                        )
                    if changed:
                        project_design = updated_design
                        logger.info("Applied design improvements from pre-review")
                        # Save checkpoint after review
                        try:
                            self.state_manager.save_checkpoint(
                                checkpoint_key=f"{project_name}_pipeline",
                                stage="design_review",
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
                            self.progress_reporter.show_checkpoint_saved(
                                f"{project_name}_pipeline", "design_review"
                            )
                        except Exception:
                            pass
                except Exception as e:
                    logger.warning(f"Design pre-review failed: {e}; continuing with original design")

        # Stage 2: Generate basic devplan
        self.progress_reporter.start_stage("Basic DevPlan", 2)
        logger.info("Stage 2/4: Generating basic devplan")
        with self.progress_reporter.create_spinner_context("Creating basic development plan..."):
            basic_devplan = await self.basic_devplan_gen.generate(
                project_design, feedback_manager=feedback_manager, **llm_kwargs
            )
        self._update_progress_tokens(self.devplan_client)
        self.progress_reporter.end_stage("Basic DevPlan")

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
            self.progress_reporter.show_checkpoint_saved(
                f"{project_name}_pipeline", "basic_devplan"
            )
        except Exception as e:
            logger.warning(f"Failed to save checkpoint after basic devplan: {e}")

        # Stage 3: Generate detailed devplan
        self.progress_reporter.start_stage("Detailed DevPlan", 3)
        logger.info("Stage 3/4: Generating detailed devplan")
        total_phases = len(basic_devplan.phases)
        self.progress_reporter.show_concurrent_phases(total_phases)
        # Start a progress bar for phases
        self.progress_reporter.start_phase_progress(total_phases, description="Generating detailed phases")
        with self.progress_reporter.create_spinner_context("Generating detailed phase plans..."):
            detailed_devplan = await self.detailed_devplan_gen.generate(
                basic_devplan,
                project_name,
                project_design.tech_stack,
                feedback_manager=feedback_manager,
                on_phase_complete=lambda ph: (
                    self.progress_reporter.advance_phase(),
                    self.progress_reporter.console.print(
                        f"  [green]✓[/green] Phase {ph.number} ready ({len(ph.steps)} steps)"
                    )
                ),
                **llm_kwargs,
            )
        # Ensure progress bar completes
        self.progress_reporter.stop_phase_progress()
        self._update_progress_tokens(self.devplan_client)
        self.progress_reporter.end_stage("Detailed DevPlan")

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
            self.progress_reporter.show_checkpoint_saved(
                f"{project_name}_pipeline", "detailed_devplan"
            )
        except Exception as e:
            logger.warning(f"Failed to save checkpoint after detailed devplan: {e}")

        if save_artifacts:
            devplan_md = self._devplan_to_markdown(detailed_devplan)
            ok, written_path = self.file_manager.safe_write_devplan(f"{output_dir}/devplan.md", devplan_md)
            if ok:
                logger.info("Saved devplan.md dashboard (validated)")
                self.progress_reporter.report_file_created(
                    written_path,
                    "DevPlan Dashboard",
                    len(devplan_md)
                )
            else:
                logger.warning("Devplan write redirected to tmp due to failed validation: %s", written_path)
                self.progress_reporter.report_file_created(
                    written_path,
                    "DevPlan Dashboard (tmp)",
                    len(devplan_md)
                )

            # Generate individual phase files
            phase_files = self._generate_phase_files(detailed_devplan, output_dir)
            logger.info(f"Generated {len(phase_files)} individual phase files")

            # Commit devplan and phase files if Git integration is enabled
            if self.git_manager and self.git_config.commit_after_devplan:
                try:
                    all_files = [f"{output_dir}/devplan.md"] + phase_files
                    self.git_manager.commit_changes(
                        "feat: generate devplan dashboard with individual phase files",
                        files=all_files,
                    )
                    logger.info("Committed devplan dashboard and phase files to Git")
                except Exception as e:
                    logger.warning(f"Failed to commit devplan files: {e}")

        # Stage 4: Generate handoff prompt
        self.progress_reporter.start_stage("Handoff Prompt", 4)
        logger.info("Stage 4/4: Generating handoff prompt")
        with self.progress_reporter.create_spinner_context("Composing handoff prompt..."):
            handoff = self.handoff_gen.generate(
                devplan=detailed_devplan,
                project_name=project_name,
                project_summary=detailed_devplan.summary or "",
                architecture_notes=project_design.architecture_overview or "",
            )
        self.progress_reporter.end_stage("Handoff Prompt")

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
            self.progress_reporter.show_checkpoint_saved(
                f"{project_name}_pipeline", "handoff_prompt"
            )
        except Exception as e:
            logger.warning(f"Failed to save checkpoint after handoff prompt: {e}")

        if save_artifacts:
            self.file_manager.write_markdown(
                f"{output_dir}/handoff_prompt.md", handoff.content
            )
            logger.info("Saved handoff_prompt.md")
            self.progress_reporter.report_file_created(
                f"{output_dir}/handoff_prompt.md",
                "Handoff Prompt",
                len(handoff.content)
            )

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
        self.progress_reporter.display_summary()
        return project_design, detailed_devplan, handoff

    async def run_devplan_only(
        self,
        project_design: ProjectDesign,
        provider_override: Optional[str] = None,
        feedback_manager: Optional[Any] = None,
        pre_review: bool = False,
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

        # Optional: Pre-review design with devplan model to catch issues early
        if pre_review:
            with self.progress_reporter.create_spinner_context(
                "Reviewing project design for compatibility/workflow/backend issues..."
            ):
                try:
                    updated_design, review_md, changed = await self.design_review_refiner.refine(
                        project_design, **llm_kwargs
                    )
                    if changed:
                        project_design = updated_design
                        logger.info("Applied design improvements from pre-review")
                except Exception as e:
                    logger.warning(f"Design pre-review failed: {e}; continuing with original design")

        # Stage: Basic DevPlan
        self.progress_reporter.start_stage("Basic DevPlan", 2)
        with self.progress_reporter.create_spinner_context("Creating basic development plan..."):
            basic_devplan = await self.basic_devplan_gen.generate(
                project_design, feedback_manager=feedback_manager, **llm_kwargs
            )
        self._update_progress_tokens(self.devplan_client)
        self.progress_reporter.end_stage("Basic DevPlan")

        # Stage: Detailed DevPlan with per-phase progress
        total_phases = len(basic_devplan.phases)
        if total_phases > 0:
            self.progress_reporter.show_concurrent_phases(total_phases)
            self.progress_reporter.start_phase_progress(total_phases, description="Generating detailed phases")
        with self.progress_reporter.create_spinner_context("Generating detailed phase plans..."):
            detailed_devplan = await self.detailed_devplan_gen.generate(
                basic_devplan,
                project_design.project_name,
                project_design.tech_stack,
                feedback_manager=feedback_manager,
                on_phase_complete=lambda ph: (
                    self.progress_reporter.advance_phase(),
                    self.progress_reporter.console.print(
                        f"  [green]✓[/green] Phase {ph.number} ready ({len(ph.steps)} steps)"
                    )
                ),
                **llm_kwargs,
            )
        self.progress_reporter.stop_phase_progress()
        self._update_progress_tokens(self.devplan_client)
        self.progress_reporter.end_stage("Detailed DevPlan")

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
            ok, written_path = self.file_manager.safe_write_devplan(f"{output_dir}/devplan.md", devplan_md)
            if ok:
                logger.info("Saved devplan.md (validated)")
            else:
                logger.warning("Devplan write redirected to tmp due to failed validation: %s", written_path)

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
        # Stage: Handoff Prompt
        self.progress_reporter.start_stage("Handoff Prompt", 4)
        with self.progress_reporter.create_spinner_context("Composing handoff prompt..."):
            handoff = self.handoff_gen.generate(devplan, project_name, **kwargs)
        self.progress_reporter.end_stage("Handoff Prompt")
        return handoff

    def _devplan_to_markdown(self, devplan: DevPlan) -> str:
        """Convert a DevPlan to markdown index/dashboard format.

        Args:
            devplan: The development plan

        Returns:
            Markdown string for the main devplan index
        """
        lines = [
            "# Development Plan\n",
            "## Summary\n\n",
            f"{devplan.summary}\n\n",
            "---\n\n",
            "## 📋 Project Dashboard\n\n",
            "This document serves as the main index and dashboard for project development. ",
            "Each phase below has its own dedicated markdown file with detailed actionable steps.\n\n",
            "### 🚀 Phase Overview\n\n",
            "| Phase | Title | Status | Steps | File |\n",
            "|-------|-------|--------|-------|------|\n"
        ]

        for phase in devplan.phases:
            # Calculate completion percentage
            completed_steps = sum(1 for step in phase.steps if step.done)
            total_steps = len(phase.steps)
            completion_pct = (completed_steps / total_steps * 100) if total_steps > 0 else 0
            
            # Status emoji
            if completion_pct == 100:
                status = "✅ Complete"
            elif completion_pct > 0:
                status = f"🔄 {completion_pct:.0f}%"
            else:
                status = "⏳ Not Started"
            
            lines.append(
                f"| {phase.number} | {phase.title} | {status} | {total_steps} | [phase{phase.number}.md](phase{phase.number}.md) |\n"
            )

        lines.extend([
            "\n---\n\n",
            "## 📝 How to Use This Plan\n\n",
            "1. **Main Dashboard**: This file provides overview and progress tracking\n",
            "2. **Phase Files**: Click on phase links above to view detailed actionable steps\n",
            "3. **Coding Agents**: Each phase file contains specific steps for implementation agents\n",
            "4. **Progress Tracking**: Mark steps complete in individual phase files\n\n",
            "### 🔗 Quick Access\n\n"
        ])

        for phase in devplan.phases:
            lines.append(f"- **[Phase {phase.number}: {phase.title}](phase{phase.number}.md)**\n")

        # Automation hooks to allow agents to reliably update progress
        lines.extend([
            "\n---\n\n",
            "## 🔧 Automation Hooks (Do Not Remove)\n\n",
            "<!-- PROGRESS_LOG_START -->\n<!-- PROGRESS_LOG_END -->\n\n",
            "<!-- NEXT_TASK_GROUP_START -->\n<!-- NEXT_TASK_GROUP_END -->\n\n",
            "<!-- COMPLETION_SUMMARY_START -->\n<!-- COMPLETION_SUMMARY_END -->\n\n",
            "## 📊 Overall Progress\n\n",
            f"**Total Phases**: {len(devplan.phases)}\n",
            f"**Total Steps**: {sum(len(phase.steps) for phase in devplan.phases)}\n",
            f"**Completed Steps**: {sum(sum(1 for step in phase.steps if step.done) for phase in devplan.phases)}\n\n",
            "*Last updated: " + self._get_timestamp() + "*\n"
        ])

        # Expose per-phase status anchors so agents can update completion deterministically
        lines.extend([
            "\n---\n\n",
            "## 🔒 Phase Status Anchors (Do Not Remove)\n\n",
        ])
        for phase in devplan.phases:
            total_steps = len(phase.steps)
            completed_steps = sum(1 for s in phase.steps if s.done)
            lines.append(
                f"<!-- PHASE_{phase.number}_STATUS_START -->\n"
                f"phase: {phase.number}\nname: {phase.title}\ncompleted: {completed_steps}/{total_steps}\n"
                f"<!-- PHASE_{phase.number}_STATUS_END -->\n\n"
            )

        return "\n".join(lines)

    def _generate_phase_files(self, devplan: DevPlan, output_dir: str) -> List[str]:
        """Generate individual markdown files for each phase.

        Args:
            devplan: The development plan with detailed phases
            output_dir: Directory to write the phase files

        Returns:
            List of generated file paths
        """
        generated_files = []
        
        for phase in devplan.phases:
            phase_content = self._phase_to_markdown(phase, devplan)
            phase_filename = f"phase{phase.number}.md"
            phase_path = f"{output_dir}/{phase_filename}"
            
            self.file_manager.write_markdown(phase_path, phase_content)
            generated_files.append(phase_path)
            logger.info(f"Generated {phase_filename} with {len(phase.steps)} steps")
            
            # Report phase file creation
            self.progress_reporter.report_file_created(
                phase_path,
                f"Phase {phase.number}",
                len(phase_content)
            )
        
        return generated_files

    def _phase_to_markdown(self, phase: DevPlanPhase, devplan: DevPlan) -> str:
        """Convert a single phase to detailed markdown format.

        Args:
            phase: The phase to convert
            devplan: The overall devplan for context

        Returns:
            Markdown string for the phase file
        """
        lines = [
            f"# Phase {phase.number}: {phase.title}\n\n",
            f"**Project**: {devplan.summary.split('for')[1].strip() if 'for' in devplan.summary else 'Unknown Project'}\n",
            f"**Total Steps**: {len(phase.steps)}\n\n",
            "---\n\n",
            "## 📋 Phase Overview\n\n",
            "This phase contains detailed actionable steps for implementation agents. ",
            "Each step should be completed in order as they build upon each other.\n\n",
            "## 🚀 Implementation Steps\n\n"
        ]

        for step in phase.steps:
            status = "✅" if step.done else "⏳"
            lines.append(f"{status} **{step.number}**: {step.description}\n")
            # Render sub-bullets if present
            if getattr(step, "details", None):
                for d in step.details:
                    lines.append(f"- {d}\n")

        # Add agent-specific instructions
        lines.extend([
            "\n---\n\n",
            "## 🤖 For Implementation Agents\n\n",
            "### Instructions:\n",
            "1. **Complete steps in order** - Each step builds upon previous work\n",
            "2. **Mark complete** - Change ⏳ to ✅ when each step is finished\n",
            "3. **Add notes** - Document any important decisions or issues\n",
            "4. **Test thoroughly** - Ensure each step works before proceeding\n",
            "5. **Update main devplan** - Return to main devplan.md to update overall progress\n\n",
            "### Automation Hooks (Do Not Remove)\n\n",
            "<!-- PHASE_PROGRESS_START -->\n<!-- PHASE_PROGRESS_END -->\n\n",
            "### Dependencies:\n",
            "- Ensure previous phases are complete before starting this phase\n",
            "- Follow the project's established patterns and conventions\n",
            "- Coordinate with other agents working on related phases\n\n",
            "---\n\n",
            f"*Generated: {self._get_timestamp()}*\n",
            f"*Back to: [Main DevPlan](devplan.md)*\n"
        ])

        return "\n".join(lines)

    def _get_timestamp(self) -> str:
        """Get current timestamp for file generation."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def _update_progress_tokens(self, llm_client: LLMClient) -> None:
        """Update progress reporter with token usage from LLM client.
        
        Args:
            llm_client: The LLM client to get token usage from
        """
        try:
            usage = getattr(llm_client, "last_usage_metadata", None)
            if usage:
                self.progress_reporter.update_tokens(usage)
        except Exception as e:
            logger.debug(f"Could not update progress tokens: {e}")
