"""
API endpoints for project template management.

Templates allow users to save successful project configurations
for quick reuse on future projects.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import uuid
import json
from datetime import datetime, timezone

from ..config_models import (
    ProjectTemplate,
    CreateTemplateRequest,
    UpdateTemplateRequest,
)
from ..config_storage import get_storage

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.post("", response_model=ProjectTemplate)
async def create_template(request: CreateTemplateRequest):
    """Create a new project template."""
    storage = get_storage()
    
    # Generate unique ID
    template_id = f"tpl_{uuid.uuid4().hex[:12]}"
    
    # Create template
    template = ProjectTemplate(
        id=template_id,
        name=request.name,
        description=request.description,
        llm_config=request.llm_config,
        stage_overrides=request.stage_overrides,
        tags=request.tags,
        created_at=datetime.now(timezone.utc),
        usage_count=0,
    )
    
    # Save template
    success = storage.save_template(template)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save template")
    
    return template


@router.get("", response_model=List[ProjectTemplate])
async def list_templates():
    """List all project templates."""
    storage = get_storage()
    templates = storage.load_all_templates()
    return templates


@router.get("/{template_id}", response_model=ProjectTemplate)
async def get_template(template_id: str):
    """Get a specific template by ID."""
    storage = get_storage()
    template = storage.load_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    
    return template


@router.put("/{template_id}", response_model=ProjectTemplate)
async def update_template(template_id: str, request: UpdateTemplateRequest):
    """Update an existing template."""
    storage = get_storage()
    
    # Load existing template
    template = storage.load_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    
    # Update fields
    if request.name is not None:
        template.name = request.name
    if request.description is not None:
        template.description = request.description
    if request.llm_config is not None:
        template.llm_config = request.llm_config
    if request.stage_overrides is not None:
        template.stage_overrides = request.stage_overrides
    if request.tags is not None:
        template.tags = request.tags
    
    # Save updated template
    success = storage.save_template(template)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update template")
    
    return template


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    """Delete a template."""
    storage = get_storage()
    
    success = storage.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    
    return {"message": f"Template {template_id} deleted successfully"}


@router.post("/{template_id}/use", response_model=ProjectTemplate)
async def use_template(template_id: str):
    """Mark a template as used (increments usage count)."""
    storage = get_storage()
    
    success = storage.increment_template_usage(template_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    
    # Return updated template
    template = storage.load_template(template_id)
    return template


@router.post("/from-project/{project_id}", response_model=ProjectTemplate)
async def create_template_from_project(
    project_id: str,
    request: CreateTemplateRequest
):
    """
    Create a template from an existing project's configuration.
    
    Extracts the LLM configuration from a completed project and saves it as a reusable template.
    """
    from ..project_manager import _projects
    
    # Get the project
    project = _projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    # Only allow creating templates from completed projects
    from ..models import ProjectStatus
    if project.status != ProjectStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Can only create templates from completed projects (current status: {project.status})"
        )
    
    storage = get_storage()
    
    # Generate unique ID
    template_id = f"tpl_{uuid.uuid4().hex[:12]}"
    
    # Extract configuration from project request
    project_request = project.request
    
    # Build stage overrides from project if they had custom models
    stage_overrides = {}
    
    # Create template with project configuration
    template = ProjectTemplate(
        id=template_id,
        name=request.name,
        description=request.description,
        llm_config=None,  # Will use global config by default
        stage_overrides=request.stage_overrides if request.stage_overrides else stage_overrides,
        tags=request.tags if request.tags else [],
        created_at=datetime.now(timezone.utc),
        created_from_project_id=project_id,
        usage_count=0,
    )
    
    # Save template
    success = storage.save_template(template)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save template")
    
    return template


@router.get("/{template_id}/export")
async def export_template(template_id: str):
    """Export a template as JSON file for sharing."""
    storage = get_storage()
    template = storage.load_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    
    # Convert to dict and make JSON serializable
    template_dict = template.model_dump(mode='json')
    
    # Create JSON response with download headers
    json_str = json.dumps(template_dict, indent=2)
    
    return JSONResponse(
        content=template_dict,
        headers={
            'Content-Disposition': f'attachment; filename="template_{template.name.replace(" ", "_")}.json"'
        }
    )


@router.post("/import", response_model=ProjectTemplate)
async def import_template(file: UploadFile = File(...)):
    """Import a template from a JSON file."""
    if not file.filename or not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a JSON file")
    
    try:
        # Read and parse JSON
        contents = await file.read()
        template_data = json.loads(contents)
        
        # Generate new ID to avoid conflicts
        old_id = template_data.get('id', '')
        new_id = f"tpl_{uuid.uuid4().hex[:12]}"
        template_data['id'] = new_id
        
        # Reset usage stats
        template_data['usage_count'] = 0
        template_data['last_used_at'] = None
        template_data['created_at'] = datetime.now(timezone.utc).isoformat()
        template_data['created_from_project_id'] = None
        
        # Create template from dict
        template = ProjectTemplate(**template_data)
        
        # Save template
        storage = get_storage()
        success = storage.save_template(template)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save imported template")
        
        return template
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to import template: {str(e)}")
