"""Project manager for web interface.

This module manages project lifecycle, integrating the existing CLI pipeline
with the web API. It handles project creation, execution, status tracking,
and WebSocket streaming.
"""

import asyncio
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from src.logger import get_logger
from src.web.models import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectStatus,
    PipelineStage,
    StreamMessage,
    FileInfo,
)
from src.config import load_config
from src.pipeline.compose import PipelineOrchestrator
# GenerateDesignInputs not needed - using direct method calls


# In-memory project storage (replace with database in production)
_projects: Dict[str, "Project"] = {}
logger = get_logger(__name__)


@dataclass
class Project:
    """Internal project representation."""
    id: str
    name: str
    status: ProjectStatus
    current_stage: Optional[PipelineStage]
    progress: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    # Project configuration
    request: ProjectCreateRequest
    
    # Output directory
    output_dir: str
    
    # Generated files (dict mapping type to filepath)
    files: Dict[str, Optional[str]]
    
    # Error information
    error: Optional[str] = None
    
    # Task handle for cancellation
    _task: Optional[asyncio.Task] = None
    
    # NEW: Iteration support
    current_iteration: int = 0
    awaiting_user_input: bool = False
    iteration_prompt: Optional[str] = None
    current_stage_output: Optional[str] = None
    iteration_history: List[dict] = None  # Will be initialized in __post_init__
    
    # NEW: Detour instrumentation support
    detour_instrumentation: bool = False
    detour_metadata_logging: bool = False
    detour_metrics: Dict[str, Any] = None  # Will be initialized in __post_init__
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.iteration_history is None:
            self.iteration_history = []
        if self.detour_metrics is None:
            self.detour_metrics = {}
    
    def to_response(self) -> ProjectResponse:
        """Convert to API response model."""
        return ProjectResponse(
            id=self.id,
            name=self.name,
            status=self.status,
            current_stage=self.current_stage,
            progress=self.progress,
            created_at=self.created_at,
            updated_at=self.updated_at,
            completed_at=self.completed_at,
            project_type=self.request.project_type,
            languages=self.request.languages,
            frameworks=self.request.frameworks,
            files=self.files,
            error=self.error,
            current_iteration=self.current_iteration,
            awaiting_user_input=self.awaiting_user_input,
            iteration_prompt=self.iteration_prompt,
            current_stage_output=self.current_stage_output,
        )


class ProjectManager:
    """Manage projects for the web interface."""
    
    def __init__(self, base_dir: str = "web_projects"):
        """Initialize project manager.
        
        Args:
            base_dir: Base directory for project outputs
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    async def create_project(
        self,
        project_id: str,
        request: ProjectCreateRequest
    ) -> ProjectResponse:
        """Create a new project.
        
        Args:
            project_id: Unique project ID
            request: Project creation request
            
        Returns:
            ProjectResponse: Created project
        """
        # Create project directory
        output_dir = self.base_dir / project_id
        output_dir.mkdir(exist_ok=True)
        
        # Create project object
        project = Project(
            id=project_id,
            name=request.name,
            status=ProjectStatus.PENDING,
            current_stage=None,
            progress=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=None,
            request=request,
            output_dir=str(output_dir),
            files={},  # Changed from [] to {}
            error=None,
        )
        
        # Store project
        _projects[project_id] = project
        
        # Save project metadata
        await self._save_metadata(project)
        
        return project.to_response()
    
    async def get_project(self, project_id: str) -> Optional[ProjectResponse]:
        """Get project by ID.
        
        Args:
            project_id: Project ID
            
        Returns:
            Optional[ProjectResponse]: Project if found
        """
        project = _projects.get(project_id)
        return project.to_response() if project else None
    
    async def list_projects(
        self,
        status: Optional[ProjectStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProjectResponse]:
        """List projects with optional filtering.
        
        Args:
            status: Filter by status
            limit: Maximum number of projects
            offset: Number to skip
            
        Returns:
            List[ProjectResponse]: List of projects
        """
        projects = list(_projects.values())
        
        # Filter by status
        if status:
            projects = [p for p in projects if p.status == status]
        
        # Sort by creation time (newest first)
        projects.sort(key=lambda p: p.created_at, reverse=True)
        
        # Apply pagination
        projects = projects[offset:offset + limit]
        
        return [p.to_response() for p in projects]
    
    async def count_projects(
        self,
        status: Optional[ProjectStatus] = None
    ) -> int:
        """Count projects.
        
        Args:
            status: Filter by status
            
        Returns:
            int: Number of projects
        """
        projects = _projects.values()
        
        if status:
            projects = [p for p in projects if p.status == status]
        
        return len(list(projects))
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project and its files.
        
        Args:
            project_id: Project ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        project = _projects.get(project_id)
        
        if not project:
            return False
        
        # Cancel if running
        if project.status == ProjectStatus.RUNNING and project._task:
            project._task.cancel()
        
        # Delete files
        output_dir = Path(project.output_dir)
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        # Remove from storage
        del _projects[project_id]
        
        return True
    
    async def cancel_project(self, project_id: str) -> Optional[ProjectResponse]:
        """Cancel a running project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Optional[ProjectResponse]: Updated project if found
        """
        project = _projects.get(project_id)
        
        if not project:
            return None
        
        if project.status == ProjectStatus.RUNNING and project._task:
            project._task.cancel()
            project.status = ProjectStatus.CANCELLED
            project.updated_at = datetime.utcnow()
            await self._save_metadata(project)
        
        return project.to_response()
    
    async def _run_current_stage(self, project_id: str):
        """Run the current pipeline stage for a project.
        
        This method runs whichever stage the project is currently on.
        After completion, it pauses for user review.
        
        Args:
            project_id: Project ID
        """
        project = _projects.get(project_id)
        
        if not project:
            return
        
        try:
            # Update status to running
            project.status = ProjectStatus.RUNNING
            project.awaiting_user_input = False
            project.updated_at = datetime.utcnow()
            await self._save_metadata(project)

            # Load config and create orchestrator
            config = load_config()

            # If a specific credential was requested, load and use it
            if project.request.credential_id:
                from src.web.config_storage import ConfigStorage
                from src.web.security import SecureKeyStorage
                import os
                
                storage = ConfigStorage()
                credential = storage.load_credential(project.request.credential_id)
                
                if credential:
                    # Decrypt the API key (or use plaintext in dev mode)
                    key_storage = SecureKeyStorage()
                    api_key = key_storage.decrypt(credential.api_key_encrypted)
                    
                    # Override config with credential settings
                    config.llm.provider = credential.provider.lower()
                    config.llm.api_key = api_key
                    
                    if credential.api_base:
                        config.llm.base_url = credential.api_base
                    
                    if credential.organization_id:
                        config.llm.org_id = credential.organization_id
            
            # Apply request overrides (these take precedence over credential)
            if project.request.provider:
                config.llm.provider = project.request.provider
            if project.request.model:
                config.llm.model = project.request.model
            
            # Handle per-stage model overrides (Phase 20 fix)
            if project.request.design_model:
                config.llm.design_model = project.request.design_model
            
            if project.request.devplan_model:
                config.llm.devplan_model = project.request.devplan_model
            
            if project.request.handoff_model:
                config.llm.handoff_model = project.request.handoff_model

            from src.clients.factory import create_llm_client
            from src.concurrency import ConcurrencyManager

            detour_config = getattr(config, "detour", None)
            detour_enabled = bool(detour_config and detour_config.enabled)
            instrumentation_active = bool(
                detour_enabled and getattr(detour_config, "instrumentation_enabled", False)
            )
            metadata_logging_active = bool(
                detour_enabled
                and (
                    getattr(detour_config, "metadata_logging_enabled", False)
                    or getattr(detour_config, "instrumentation_enabled", False)
                )
            )

            project.detour_instrumentation = instrumentation_active
            project.detour_metadata_logging = metadata_logging_active

            stage_handlers = {
                PipelineStage.DESIGN: self._run_design_stage,
                PipelineStage.BASIC_DEVPLAN: self._run_basic_devplan_stage,
                PipelineStage.DETAILED_DEVPLAN: self._run_detailed_devplan_stage,
                PipelineStage.REFINED_DEVPLAN: self._run_refined_devplan_stage,
                PipelineStage.HANDOFF: self._run_handoff_stage,
            }

            stage_callable = stage_handlers.get(project.current_stage)
            stage_name = project.current_stage.value if project.current_stage else "unknown"
            stage_stat: Optional[Dict[str, Any]] = None
            stage_run_index: Optional[int] = None

            if instrumentation_active and stage_callable and stage_name != "unknown":
                metrics = project.detour_metrics.setdefault("stage_runs", {})
                stage_stat = metrics.setdefault(
                    stage_name,
                    {"count": 0, "total_time": 0.0, "last_duration": 0.0},
                )
                stage_stat["count"] += 1
                stage_run_index = stage_stat["count"]
                logger.info(
                    "[Detour] Project %s entering stage %s (run #%d)",
                    project.id,
                    stage_name,
                    stage_run_index,
                )

            orchestration_timer = time.perf_counter() if instrumentation_active else None

            llm_client = create_llm_client(config)
            concurrency_manager = ConcurrencyManager(config.max_concurrent_requests)

            orchestrator = PipelineOrchestrator(
                llm_client=llm_client,
                concurrency_manager=concurrency_manager,
                file_manager=None,
                git_config=None,
                repo_path=None,
                config=config,
                state_manager=None
            )

            if instrumentation_active and orchestration_timer is not None:
                orch_duration = time.perf_counter() - orchestration_timer
                orch_stats = project.detour_metrics.setdefault("orchestrator_init", {})
                orch_entry = orch_stats.setdefault(
                    stage_name,
                    {"count": 0, "total_time": 0.0, "last_duration": 0.0},
                )
                orch_entry["count"] += 1
                orch_entry["total_time"] += orch_duration
                orch_entry["last_duration"] = orch_duration
                logger.info(
                    "[Detour] Project %s orchestrator ready for stage %s in %.3fs",
                    project.id,
                    stage_name,
                    orch_duration,
                )

            if not stage_callable:
                logger.warning(
                    "[Detour] Project %s has no handler for stage %s",
                    project.id,
                    project.current_stage,
                )
                return

            stage_start = time.perf_counter() if instrumentation_active else None
            stage_error: Optional[Exception] = None

            try:
                await stage_callable(project, orchestrator)
            except Exception as exc:
                stage_error = exc
                raise
            finally:
                if instrumentation_active and stage_start is not None:
                    duration = time.perf_counter() - stage_start
                    if stage_stat is not None:
                        stage_stat["total_time"] += duration
                        stage_stat["last_duration"] = duration
                    outcome = "failed" if stage_error else "completed"
                    logger.info(
                        "[Detour] Stage %s %s in %.3fs%s for project %s",
                        stage_name,
                        outcome,
                        duration,
                        f" (run #{stage_run_index})" if stage_run_index else "",
                        project.id,
                    )

        except Exception as e:
            project.status = ProjectStatus.FAILED
            project.error = str(e)
            project.updated_at = datetime.utcnow()
            await self._save_metadata(project)
            await self._send_update(project_id, "error", {"error": str(e)})
    
    async def _run_design_stage(self, project: Project, orchestrator):
        """Run the design stage."""
        project.progress = 0
        await self._send_update(project.id, "stage", {"stage": "design", "progress": 0})
        
        # Generate design
        requirements_text = project.request.description or project.request.requirements or ""
        design = await orchestrator.project_design_gen.generate(
            project_name=project.request.name,
            languages=project.request.languages,
            requirements=requirements_text.split('\n') if requirements_text else [],
            frameworks=project.request.frameworks,
            apis=project.request.apis,
        )
        
        # Convert to markdown
        design_output = f"# Project Design: {project.request.name}\n\n"
        design_output += f"## Architecture Overview\n\n{design.architecture_overview}\n\n"
        if design.objectives:
            design_output += "## Objectives\n\n"
            for obj in design.objectives:
                design_output += f"- {obj}\n"
            design_output += "\n"
        if design.tech_stack:
            design_output += f"## Tech Stack\n\n{', '.join(design.tech_stack)}\n\n"
        
        project.progress = 20
        await self._send_update(project.id, "progress", {"progress": 20})
        
        # Save file
        design_file = Path(project.output_dir) / "project_design.md"
        design_file.write_text(design_output, encoding='utf-8')
        project.files["design"] = str(design_file)
        
        # PAUSE for user review
        project.status = ProjectStatus.AWAITING_USER_INPUT
        project.awaiting_user_input = True
        project.current_stage_output = design_output[:500]  # First 500 chars for preview
        project.iteration_prompt = "Please review the project design. Approve to continue to Basic DevPlan, or provide feedback to iterate."
        project.updated_at = datetime.utcnow()
        await self._save_metadata(project)
        await self._send_update(project.id, "awaiting_input", {
            "stage": "design",
            "prompt": project.iteration_prompt
        })
    
    async def _run_basic_devplan_stage(self, project: Project, orchestrator):
        """Run the basic devplan stage (high-level phases)."""
        project.progress = 25
        await self._send_update(project.id, "stage", {"stage": "basic_devplan", "progress": 25})
        
        # Get design output to base devplan on
        design_file = Path(project.output_dir) / "project_design.md"
        design_output = design_file.read_text(encoding='utf-8') if design_file.exists() else ""
        
        # Generate basic devplan (4-8 phases)
        devplan_output = await self._run_with_streaming(
            project.id,
            orchestrator.generate_devplan,
            design_output,
            PipelineStage.BASIC_DEVPLAN
        )
        
        project.progress = 40
        await self._send_update(project.id, "progress", {"progress": 40})
        
        # Save file
        devplan_file = Path(project.output_dir) / "devplan_basic.md"
        devplan_file.write_text(devplan_output, encoding='utf-8')
        project.files["basic_devplan"] = str(devplan_file)
        
        # PAUSE for user review
        project.status = ProjectStatus.AWAITING_USER_INPUT
        project.awaiting_user_input = True
        project.current_stage_output = devplan_output[:500]
        project.iteration_prompt = "Please review the basic development plan (high-level phases). Approve to continue to Detailed DevPlan, or provide feedback to iterate."
        project.updated_at = datetime.utcnow()
        await self._save_metadata(project)
        await self._send_update(project.id, "awaiting_input", {
            "stage": "basic_devplan",
            "prompt": project.iteration_prompt
        })
    
    async def _run_detailed_devplan_stage(self, project: Project, orchestrator):
        """Run the detailed devplan stage (100-300 steps)."""
        project.progress = 45
        await self._send_update(project.id, "stage", {"stage": "detailed_devplan", "progress": 45})
        
        # Get basic devplan to expand on
        basic_file = Path(project.output_dir) / "devplan_basic.md"
        basic_output = basic_file.read_text(encoding='utf-8') if basic_file.exists() else ""
        
        # Generate detailed devplan
        detailed_output = await self._run_with_streaming(
            project.id,
            orchestrator.generate_devplan,
            basic_output,
            PipelineStage.DETAILED_DEVPLAN
        )
        
        project.progress = 60
        await self._send_update(project.id, "progress", {"progress": 60})
        
        # Save file
        detailed_file = Path(project.output_dir) / "devplan_detailed.md"
        detailed_file.write_text(detailed_output, encoding='utf-8')
        project.files["detailed_devplan"] = str(detailed_file)
        
        # PAUSE for user review
        project.status = ProjectStatus.AWAITING_USER_INPUT
        project.awaiting_user_input = True
        project.current_stage_output = detailed_output[:500]
        project.iteration_prompt = "Please review the detailed development plan (100-300 steps). Approve to continue to Refined DevPlan, or provide feedback to iterate."
        project.updated_at = datetime.utcnow()
        await self._save_metadata(project)
        await self._send_update(project.id, "awaiting_input", {
            "stage": "detailed_devplan",
            "prompt": project.iteration_prompt
        })
    
    async def _run_refined_devplan_stage(self, project: Project, orchestrator):
        """Run the refined devplan stage (agent-ready)."""
        project.progress = 65
        await self._send_update(project.id, "stage", {"stage": "refined_devplan", "progress": 65})
        
        # Get detailed devplan to refine
        detailed_file = Path(project.output_dir) / "devplan_detailed.md"
        detailed_output = detailed_file.read_text(encoding='utf-8') if detailed_file.exists() else ""
        
        # Generate refined devplan
        refined_output = await self._run_with_streaming(
            project.id,
            orchestrator.generate_devplan,
            detailed_output,
            PipelineStage.REFINED_DEVPLAN
        )
        
        project.progress = 80
        await self._send_update(project.id, "progress", {"progress": 80})
        
        # Save file
        refined_file = Path(project.output_dir) / "devplan_refined.md"
        refined_file.write_text(refined_output, encoding='utf-8')
        project.files["refined_devplan"] = str(refined_file)
        
        # PAUSE for user review
        project.status = ProjectStatus.AWAITING_USER_INPUT
        project.awaiting_user_input = True
        project.current_stage_output = refined_output[:500]
        project.iteration_prompt = "Please review the refined development plan (handoff-ready). Approve to continue to Handoff generation, or provide feedback to iterate."
        project.updated_at = datetime.utcnow()
        await self._save_metadata(project)
        await self._send_update(project.id, "awaiting_input", {
            "stage": "refined_devplan",
            "prompt": project.iteration_prompt
        })
    
    async def _run_handoff_stage(self, project: Project, orchestrator):
        """Run the handoff generation stage."""
        project.progress = 85
        await self._send_update(project.id, "stage", {"stage": "handoff", "progress": 85})
        
        # Get refined devplan for handoff
        refined_file = Path(project.output_dir) / "devplan_refined.md"
        refined_output = refined_file.read_text(encoding='utf-8') if refined_file.exists() else ""
        
        # Generate handoff
        handoff_output = await self._run_with_streaming(
            project.id,
            orchestrator.generate_handoff,
            (refined_output, project.request.name),
            PipelineStage.HANDOFF
        )
        
        project.progress = 100
        await self._send_update(project.id, "progress", {"progress": 100})
        
        # Save file
        handoff_file = Path(project.output_dir) / "handoff_prompt.md"
        handoff_file.write_text(handoff_output, encoding='utf-8')
        project.files["handoff"] = str(handoff_file)
        
        # Mark complete (no pause after handoff)
        project.status = ProjectStatus.COMPLETED
        project.completed_at = datetime.utcnow()
        project.updated_at = datetime.utcnow()
        await self._save_metadata(project)
        await self._send_update(project.id, "complete", {
            "message": "Pipeline completed successfully",
            "files": project.files
        })

    async def run_pipeline(self, project_id: str):
        """Run the pipeline for a project.
        
        This is the main integration point with the existing CLI pipeline.
        Starts from Design stage and proceeds through user-approved iterations.
        
        Args:
            project_id: Project ID
        """
        project = _projects.get(project_id)
        
        if not project:
            return
        
        try:
            # Set initial stage
            project.current_stage = PipelineStage.DESIGN
            project.updated_at = datetime.utcnow()
            await self._save_metadata(project)
            
            # Run the design stage (will pause for review)
            await self._run_current_stage(project_id)
            
        except Exception as e:
            # Handle errors in initial pipeline setup
            project.status = ProjectStatus.FAILED
            project.error = str(e)
            project.updated_at = datetime.utcnow()
            await self._save_metadata(project)
            await self._send_update(project_id, "error", {"error": str(e)})
    
    async def _run_with_streaming(
        self,
        project_id: str,
        func,
        inputs,
        stage: PipelineStage
    ) -> str:
        """Run a pipeline function with streaming support.
        
        Args:
            project_id: Project ID
            func: Function to run
            inputs: Function inputs
            stage: Current stage
            
        Returns:
            str: Function output
        """
        # For now, just run the function
        # TODO: Add streaming callback integration
        result = func(inputs) if not asyncio.iscoroutinefunction(func) else await func(inputs)
        return result
    
    async def _send_update(self, project_id: str, msg_type: str, data: dict):
        """Send WebSocket update.
        
        Args:
            project_id: Project ID
            msg_type: Message type
            data: Message data
        """
        # Import here to avoid circular dependency
        from src.web.routes.websocket_routes import send_update
        
        message = StreamMessage(type=msg_type, data=data)
        await send_update(project_id, message)
    
    async def _save_metadata(self, project: Project):
        """Save project metadata to disk.
        
        Args:
            project: Project to save
        """
        metadata_file = Path(project.output_dir) / "metadata.json"
        
        metadata = {
            "id": project.id,
            "name": project.name,
            "status": project.status.value,
            "current_stage": project.current_stage.value if project.current_stage else None,
            "progress": project.progress,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "completed_at": project.completed_at.isoformat() if project.completed_at else None,
            "request": {
                "name": project.request.name,
                "project_type": project.request.project_type.value,
                "languages": project.request.languages,
                "frameworks": project.request.frameworks,
                "apis": project.request.apis,
                "requirements": project.request.requirements,
            },
            "files": project.files,
            "error": project.error,
        }

        payload = json.dumps(metadata, indent=2)
        metadata_file.write_text(payload, encoding='utf-8')

        if project.detour_metadata_logging:
            bytes_written = len(payload.encode("utf-8"))
            write_stats = project.detour_metrics.setdefault(
                "metadata_writes",
                {"count": 0, "total_bytes": 0},
            )
            write_stats["count"] += 1
            write_stats["total_bytes"] += bytes_written
            logger.info(
                "[Detour] Metadata write #%d for project %s (%d bytes, total %d bytes)",
                write_stats["count"],
                project.id,
                bytes_written,
                write_stats["total_bytes"],
            )
    
    async def list_files(self, project_id: str) -> List[FileInfo]:
        """List all files for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List[FileInfo]: File information
        """
        project = _projects.get(project_id)
        
        if not project:
            return []
        
        output_dir = Path(project.output_dir)
        files = []
        
        for filename in project.files:
            file_path = output_dir / filename
            if file_path.exists():
                stat = file_path.stat()
                files.append(FileInfo(
                    name=filename,
                    path=str(file_path),
                    size=stat.st_size,
                    created_at=datetime.fromtimestamp(stat.st_ctime),
                    content_type="text/markdown"
                ))
        
        return files
    
    async def get_file_path(self, project_id: str, filename: str) -> Optional[str]:
        """Get the file path for a project file.
        
        Args:
            project_id: Project ID
            filename: File name
            
        Returns:
            Optional[str]: File path if exists
        """
        project = _projects.get(project_id)
        
        if not project or filename not in project.files:
            return None
        
        file_path = Path(project.output_dir) / filename
        return str(file_path) if file_path.exists() else None
    
    # ========================================================================
    # NEW: Iteration Support Methods
    # ========================================================================
    
    async def iterate_stage(
        self,
        project_id: str,
        feedback: str,
        regenerate: bool = True
    ) -> ProjectResponse:
        """Handle iteration request on current stage.
        
        Args:
            project_id: Project ID
            feedback: User feedback
            regenerate: Whether to regenerate content
            
        Returns:
            ProjectResponse: Updated project
        """
        project = _projects.get(project_id)
        
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Record iteration
        project.current_iteration += 1
        
        # Store feedback in history
        history_entry = {
            "stage": project.current_stage.value if project.current_stage else None,
            "iteration": project.current_iteration,
            "timestamp": datetime.utcnow().isoformat(),
            "feedback": feedback,
            "output": project.current_stage_output or ""
        }
        project.iteration_history.append(history_entry)
        
        if not regenerate:
            # Just store feedback, don't regenerate
            project.awaiting_user_input = True
            project.iteration_prompt = f"Iteration {project.current_iteration}: Review your feedback and approve or regenerate."
        else:
            # Will regenerate in background
            project.status = ProjectStatus.RUNNING
            project.awaiting_user_input = False
        
        project.updated_at = datetime.utcnow()
        await self._save_metadata(project)
        
        return project.to_response()
    
    async def approve_stage(
        self,
        project_id: str,
        notes: Optional[str] = None
    ) -> ProjectResponse:
        """Approve current stage and prepare to move to next.
        
        Args:
            project_id: Project ID
            notes: Optional approval notes
            
        Returns:
            ProjectResponse: Updated project
        """
        project = _projects.get(project_id)
        
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Reset iteration counter for next stage
        project.current_iteration = 0
        project.awaiting_user_input = False
        project.iteration_prompt = None
        project.status = ProjectStatus.RUNNING
        
        # Store approval in history if notes provided
        if notes:
            history_entry = {
                "stage": project.current_stage.value if project.current_stage else None,
                "iteration": "APPROVED",
                "timestamp": datetime.utcnow().isoformat(),
                "feedback": notes,
                "output": project.current_stage_output or ""
            }
            project.iteration_history.append(history_entry)
        
        project.updated_at = datetime.utcnow()
        await self._save_metadata(project)
        
        return project.to_response()
    
    async def regenerate_current_stage(
        self,
        project_id: str,
        feedback: str
    ):
        """Regenerate current stage with user feedback.
        
        Args:
            project_id: Project ID
            feedback: User feedback to incorporate
        """
        project = _projects.get(project_id)
        
        if not project:
            return
        
        try:
            # Load configuration
            config = load_config()
            
            # Create clients
            from src.clients.factory import create_llm_client
            from src.concurrency import ConcurrencyManager
            
            llm_client = create_llm_client(config)
            concurrency_manager = ConcurrencyManager(config.concurrency.max_concurrent)
            
            orchestrator = PipelineOrchestrator(
                llm_client=llm_client,
                concurrency_manager=concurrency_manager,
                file_manager=None,
                git_config=None,
                repo_path=None,
                config=config,
                state_manager=None
            )
            
            # Regenerate based on current stage
            if project.current_stage == PipelineStage.DESIGN:
                # Regenerate design with feedback
                requirements_text = project.request.description or project.request.requirements or ""
                requirements_list = requirements_text.split('\n') if requirements_text else []
                requirements_list.append(f"\nUSER FEEDBACK (Iteration {project.current_iteration}): {feedback}")
                
                design = await orchestrator.project_design_gen.generate(
                    project_name=project.request.name,
                    languages=project.request.languages,
                    requirements=requirements_list,
                    frameworks=project.request.frameworks,
                    apis=project.request.apis,
                )
                
                # Convert to markdown
                design_output = f"# Project Design: {project.request.name}\n\n"
                design_output += f"## Architecture Overview\n\n{design.architecture_overview}\n\n"
                if design.objectives:
                    design_output += "## Objectives\n\n"
                    for obj in design.objectives:
                        design_output += f"- {obj}\n"
                    design_output += "\n"
                if design.tech_stack:
                    design_output += f"## Tech Stack\n\n{', '.join(design.tech_stack)}\n\n"
                
                # Save and update
                design_file = Path(project.output_dir) / "project_design.md"
                design_file.write_text(design_output, encoding='utf-8')
                project.current_stage_output = design_output
            
            # After regeneration, pause for user review
            project.status = ProjectStatus.AWAITING_USER_INPUT
            project.awaiting_user_input = True
            project.iteration_prompt = f"Please review the updated {project.current_stage.value}. Approve to continue or provide more feedback."
            
            project.updated_at = datetime.utcnow()
            await self._save_metadata(project)
            await self._send_update(project_id, "regenerated", {
                "stage": project.current_stage.value,
                "iteration": project.current_iteration
            })
            
        except Exception as e:
            project.status = ProjectStatus.FAILED
            project.error = str(e)
            project.updated_at = datetime.utcnow()
            await self._save_metadata(project)
            await self._send_update(project_id, "error", {"error": str(e)})
    
    async def continue_pipeline(self, project_id: str):
        """Continue pipeline to next stage after approval.
        
        Args:
            project_id: Project ID
        """
        project = _projects.get(project_id)
        
        if not project:
            return
        
        # Determine next stage based on current
        next_stage = None
        if project.current_stage == PipelineStage.DESIGN:
            next_stage = PipelineStage.BASIC_DEVPLAN
        elif project.current_stage == PipelineStage.BASIC_DEVPLAN:
            next_stage = PipelineStage.DETAILED_DEVPLAN
        elif project.current_stage == PipelineStage.DETAILED_DEVPLAN:
            next_stage = PipelineStage.REFINED_DEVPLAN
        elif project.current_stage == PipelineStage.REFINED_DEVPLAN:
            next_stage = PipelineStage.HANDOFF
        else:
            # Already at handoff, complete
            project.status = ProjectStatus.COMPLETED
            project.completed_at = datetime.utcnow()
            project.updated_at = datetime.utcnow()
            await self._save_metadata(project)
            await self._send_update(project_id, "complete", {
                "message": "Pipeline completed successfully",
                "files": project.files
            })
            return
        
        # Move to next stage
        project.current_stage = next_stage
        project.updated_at = datetime.utcnow()
        await self._save_metadata(project)
        
        # Run the next stage
        await self._run_current_stage(project_id)
        # For now, just run the full pipeline
        # TODO: Make pipeline truly iterative
        await self.run_pipeline(project_id)

