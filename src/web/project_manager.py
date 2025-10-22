"""Project manager for web interface.

This module manages project lifecycle, integrating the existing CLI pipeline
with the web API. It handles project creation, execution, status tracking,
and WebSocket streaming.
"""

import asyncio
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

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
    
    # Generated files
    files: List[str]
    
    # Error information
    error: Optional[str] = None
    
    # Task handle for cancellation
    _task: Optional[asyncio.Task] = None
    
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
            files=[],
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
    
    async def run_pipeline(self, project_id: str):
        """Run the pipeline for a project.
        
        This is the main integration point with the existing CLI pipeline.
        
        Args:
            project_id: Project ID
        """
        project = _projects.get(project_id)
        
        if not project:
            return
        
        try:
            # Update status
            project.status = ProjectStatus.RUNNING
            project.updated_at = datetime.utcnow()
            await self._save_metadata(project)
            await self._send_update(project_id, "status", {"status": "running"})
            
            # Load configuration
            config = load_config()
            
            # Override with request settings
            if project.request.provider:
                config.llm.llm_provider = project.request.provider
            if project.request.model:
                config.llm.model = project.request.model
            if project.request.design_model:
                config.llm.design_model = project.request.design_model
            if project.request.devplan_model:
                config.llm.devplan_model = project.request.devplan_model
            if project.request.handoff_model:
                config.llm.handoff_model = project.request.handoff_model
            
            # Create pipeline orchestrator
            from src.clients.factory import create_llm_client
            from src.concurrency import ConcurrencyManager
            
            app_config = config  # Use the config we already loaded
            llm_client = create_llm_client(app_config)
            concurrency_manager = ConcurrencyManager(app_config.concurrency.max_concurrent)
            
            orchestrator = PipelineOrchestrator(
                llm_client=llm_client,
                concurrency_manager=concurrency_manager,
                file_manager=None,
                git_config=None,
                repo_path=None,
                config=app_config,
                state_manager=None
            )
            
            # Stage 1: Design (25% progress)
            project.current_stage = PipelineStage.DESIGN
            project.progress = 0
            await self._send_update(project_id, "stage", {"stage": "design", "progress": 0})
            
            # Generate design
            # Use description or requirements
            requirements_text = project.request.description or project.request.requirements or ""
            design = await orchestrator.project_design_gen.generate(
                project_name=project.request.name,
                languages=project.request.languages,
                requirements=requirements_text.split('\n') if requirements_text else [],
                frameworks=project.request.frameworks,
                apis=project.request.apis,
            )
            
            # Convert design to markdown
            design_output = f"# Project Design: {project.request.name}\n\n"
            design_output += f"## Architecture Overview\n\n{design.architecture_overview}\n\n"
            if design.objectives:
                design_output += "## Objectives\n\n"
                for obj in design.objectives:
                    design_output += f"- {obj}\n"
                design_output += "\n"
            if design.tech_stack:
                design_output += f"## Tech Stack\n\n{', '.join(design.tech_stack)}\n\n"
            
            project.progress = 25
            await self._send_update(project_id, "progress", {"progress": 25})
            
            # Save design file
            design_file = Path(project.output_dir) / "project_design.md"
            design_file.write_text(design_output, encoding='utf-8')
            project.files.append("project_design.md")
            
            # Stage 2: DevPlan (50% progress)
            project.current_stage = PipelineStage.BASIC_DEVPLAN
            await self._send_update(project_id, "stage", {"stage": "devplan", "progress": 25})
            
            devplan_output = await self._run_with_streaming(
                project_id,
                orchestrator.generate_devplan,
                design_output,
                PipelineStage.BASIC_DEVPLAN
            )
            
            project.progress = 75
            await self._send_update(project_id, "progress", {"progress": 75})
            
            # Save devplan file
            devplan_file = Path(project.output_dir) / "devplan.md"
            devplan_file.write_text(devplan_output, encoding='utf-8')
            project.files.append("devplan.md")
            
            # Stage 3: Handoff (100% progress)
            project.current_stage = PipelineStage.HANDOFF
            await self._send_update(project_id, "stage", {"stage": "handoff", "progress": 75})
            
            handoff_output = await self._run_with_streaming(
                project_id,
                orchestrator.generate_handoff,
                (devplan_output, project.request.name),
                PipelineStage.HANDOFF
            )
            
            # Save handoff file
            handoff_file = Path(project.output_dir) / "handoff_prompt.md"
            handoff_file.write_text(handoff_output, encoding='utf-8')
            project.files.append("handoff_prompt.md")
            
            # Mark complete
            project.status = ProjectStatus.COMPLETED
            project.progress = 100
            project.completed_at = datetime.utcnow()
            project.updated_at = datetime.utcnow()
            
            await self._save_metadata(project)
            await self._send_update(project_id, "complete", {
                "message": "Pipeline completed successfully",
                "files": project.files
            })
            
        except asyncio.CancelledError:
            project.status = ProjectStatus.CANCELLED
            project.updated_at = datetime.utcnow()
            await self._save_metadata(project)
            await self._send_update(project_id, "cancelled", {"message": "Project cancelled"})
            
        except Exception as e:
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
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
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
