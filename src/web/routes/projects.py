"""Project management routes for the web API."""

import uuid
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from src.web.models import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectListResponse,
    ProjectStatus,
    PipelineStage,
    ErrorResponse,
    IterationRequest,
    StageApproval,
)
from src.web.project_manager import ProjectManager


router = APIRouter()
project_manager = ProjectManager()


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    request: ProjectCreateRequest,
    background_tasks: BackgroundTasks
) -> ProjectResponse:
    """Create a new project and start the pipeline.
    
    Args:
        request: Project creation request
        background_tasks: FastAPI background tasks
        
    Returns:
        ProjectResponse: Created project details
        
    Raises:
        HTTPException: If project creation fails
    """
    try:
        # Generate unique project ID
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        
        # Create project
        project = await project_manager.create_project(project_id, request)
        
        # Start pipeline in background
        background_tasks.add_task(
            project_manager.run_pipeline,
            project_id
        )
        
        return project
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    status: Optional[ProjectStatus] = None,
    limit: int = 50,
    offset: int = 0
) -> ProjectListResponse:
    """List all projects with optional filtering.
    
    Args:
        status: Filter by project status
        limit: Maximum number of projects to return
        offset: Number of projects to skip
        
    Returns:
        ProjectListResponse: List of projects
    """
    projects = await project_manager.list_projects(
        status=status,
        limit=limit,
        offset=offset
    )
    
    total = await project_manager.count_projects(status=status)
    
    return ProjectListResponse(projects=projects, total=total)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str) -> ProjectResponse:
    """Get details for a specific project.
    
    Args:
        project_id: Unique project ID
        
    Returns:
        ProjectResponse: Project details
        
    Raises:
        HTTPException: If project not found
    """
    project = await project_manager.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found"
        )
    
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str):
    """Delete a project and its files.
    
    Args:
        project_id: Unique project ID
        
    Raises:
        HTTPException: If project not found
    """
    success = await project_manager.delete_project(project_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found"
        )
    
    return None


@router.post("/{project_id}/cancel", response_model=ProjectResponse)
async def cancel_project(project_id: str) -> ProjectResponse:
    """Cancel a running project.
    
    Args:
        project_id: Unique project ID
        
    Returns:
        ProjectResponse: Updated project details
        
    Raises:
        HTTPException: If project not found or not running
    """
    project = await project_manager.cancel_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found"
        )
    
    if project.status != ProjectStatus.CANCELLED:
        raise HTTPException(
            status_code=400,
            detail=f"Project cannot be cancelled (status: {project.status})"
        )
    
    return project


@router.get("/{project_id}/files/{filename}")
async def get_file_content(project_id: str, filename: str):
    """Get the content of a generated file.
    
    Args:
        project_id: Unique project ID
        filename: Name of the file to retrieve
        
    Returns:
        str: File content
        
    Raises:
        HTTPException: If project or file not found
    """
    project = await project_manager.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found"
        )
    
    # Get the file path from project.files
    file_path = None
    for key, path in project.files.items():
        if path and (path.endswith(filename) or Path(path).name == filename):
            file_path = Path(path)
            break
    
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found"
        )
    
    try:
        content = file_path.read_text(encoding='utf-8')
        return content
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file: {str(e)}"
        )


# ============================================================================
# NEW: Iteration Support Endpoints
# ============================================================================

@router.post("/{project_id}/iterate", response_model=ProjectResponse)
async def iterate_on_stage(
    project_id: str,
    iteration_request: IterationRequest,
    background_tasks: BackgroundTasks
) -> ProjectResponse:
    """Submit feedback to iterate on current stage.
    
    Args:
        project_id: Unique project ID
        iteration_request: User feedback and iteration settings
        background_tasks: FastAPI background tasks
        
    Returns:
        ProjectResponse: Updated project details
        
    Raises:
        HTTPException: If project not found or not awaiting input
    """
    project = await project_manager.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found"
        )
    
    if not project.awaiting_user_input:
        raise HTTPException(
            status_code=400,
            detail=f"Project is not awaiting user input (status: {project.status})"
        )
    
    # Process iteration
    try:
        updated_project = await project_manager.iterate_stage(
            project_id,
            iteration_request.feedback,
            iteration_request.regenerate
        )
        
        # If regenerate, start in background
        if iteration_request.regenerate:
            background_tasks.add_task(
                project_manager.regenerate_current_stage,
                project_id,
                iteration_request.feedback
            )
        
        return updated_project
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to iterate: {str(e)}"
        )


@router.post("/{project_id}/approve", response_model=ProjectResponse)
async def approve_stage(
    project_id: str,
    approval: StageApproval,
    background_tasks: BackgroundTasks
) -> ProjectResponse:
    """Approve current stage and move to next stage.
    
    Args:
        project_id: Unique project ID
        approval: Stage approval with optional notes
        background_tasks: FastAPI background tasks
        
    Returns:
        ProjectResponse: Updated project details
        
    Raises:
        HTTPException: If project not found or not awaiting input
    """
    project = await project_manager.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found"
        )
    
    if not project.awaiting_user_input:
        raise HTTPException(
            status_code=400,
            detail=f"Project is not awaiting user input (status: {project.status})"
        )
    
    try:
        # Mark stage as approved and move to next
        updated_project = await project_manager.approve_stage(
            project_id,
            approval.notes
        )
        
        # Continue pipeline in background
        background_tasks.add_task(
            project_manager.continue_pipeline,
            project_id
        )
        
        return updated_project
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve stage: {str(e)}"
        )

