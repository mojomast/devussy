"""Pydantic models for API request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class ProjectType(str, Enum):
    """Type of project being created."""
    WEB_APP = "web_app"
    API = "api"
    CLI = "cli"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    LIBRARY = "library"
    OTHER = "other"


class ProjectStatus(str, Enum):
    """Current status of a project generation."""
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_USER_INPUT = "awaiting_user_input"  # NEW: Waiting for user iteration
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStage(str, Enum):
    """Current stage in the pipeline."""
    DESIGN = "design"
    BASIC_DEVPLAN = "basic_devplan"
    DETAILED_DEVPLAN = "detailed_devplan"
    REFINED_DEVPLAN = "refined_devplan"  # NEW: Handoff-ready devplan
    HANDOFF = "handoff"


class ProjectCreateRequest(BaseModel):
    """Request model for creating a new project."""
    
    # Required fields
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    
    # Description/Requirements (either field works)
    description: Optional[str] = Field(None, min_length=10, description="Project description")
    requirements: Optional[str] = Field(None, min_length=10, description="Project requirements")
    
    # Optional fields with defaults
    project_type: ProjectType = Field(ProjectType.WEB_APP, description="Type of project")
    languages: List[str] = Field(default_factory=lambda: ["Python"], description="Programming languages")
    frameworks: List[str] = Field(default_factory=list, description="Frameworks to use")
    apis: List[str] = Field(default_factory=list, description="External APIs to integrate")
    database: Optional[str] = Field(None, description="Database system")
    authentication: Optional[bool] = Field(False, description="Requires authentication")
    deployment_platform: Optional[str] = Field(None, description="Target deployment platform")
    testing_framework: Optional[str] = Field(None, description="Testing framework")
    ci_cd: Optional[bool] = Field(False, description="Include CI/CD")
    
    # Options (for backward compatibility with frontend)
    options: Optional[dict] = Field(None, description="Additional options")
    
    # LLM configuration overrides
    credential_id: Optional[str] = Field(None, description="Credential ID to use for this project")
    provider: Optional[str] = Field(None, description="LLM provider (openai, generic, requesty)")
    model: Optional[str] = Field(None, description="Model name")
    design_model: Optional[str] = Field(None, description="Model for design stage")
    devplan_model: Optional[str] = Field(None, description="Model for devplan stage")
    handoff_model: Optional[str] = Field(None, description="Model for handoff stage")
    
    @validator("description", "requirements", pre=True, always=True)
    def validate_description_or_requirements(cls, v, values):
        """Ensure either description or requirements is provided."""
        # If this field is empty, check the other one
        if not v:
            desc = values.get('description')
            req = values.get('requirements')
            if not desc and not req:
                # Neither is set, this will fail
                if 'name' in values:  # Only raise if name is already set (meaning we're past initial field)
                    return None
            # Copy from the other field if one is set
            return req if 'requirements' in values else desc
        return v
    
    @validator("name")
    def validate_name(cls, v):
        """Validate project name."""
        if not v or v.isspace():
            raise ValueError("Project name cannot be empty")
        # Remove invalid filename characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in v for char in invalid_chars):
            raise ValueError(f"Project name cannot contain: {invalid_chars}")
        return v.strip()
    
    @validator("languages")
    def validate_languages(cls, v):
        """Validate languages list."""
        if not v:
            raise ValueError("At least one language is required")
        return [lang.strip() for lang in v if lang.strip()]
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "name": "E-commerce Platform",
                "project_type": "web_app",
                "languages": ["Python", "TypeScript"],
                "requirements": "Build a scalable e-commerce platform with product catalog, shopping cart, and payment integration",
                "frameworks": ["FastAPI", "React", "PostgreSQL"],
                "apis": ["Stripe", "SendGrid"],
                "database": "PostgreSQL",
                "authentication": True,
                "deployment_platform": "AWS",
                "testing_framework": "pytest",
                "ci_cd": True
            }
        }


class ProjectResponse(BaseModel):
    """Response model for project details."""
    
    id: str = Field(..., description="Unique project ID")
    name: str = Field(..., description="Project name")
    status: ProjectStatus = Field(..., description="Current status")
    current_stage: Optional[PipelineStage] = Field(None, description="Current pipeline stage")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    # Project details
    project_type: ProjectType
    languages: List[str]
    frameworks: List[str]
    
    # Generated files (dict mapping type to filepath)
    files: Dict[str, Optional[str]] = Field(default_factory=dict, description="Generated files by type")
    
    # Error information (if failed)
    error: Optional[str] = Field(None, description="Error message if failed")
    
    # Iteration support (NEW)
    current_iteration: int = Field(0, description="Current iteration count for this stage")
    awaiting_user_input: bool = Field(False, description="Whether project is waiting for user feedback")
    iteration_prompt: Optional[str] = Field(None, description="Prompt/question for user feedback")
    current_stage_output: Optional[str] = Field(None, description="Current output for user to review")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": "proj_abc123",
                "name": "E-commerce Platform",
                "status": "running",
                "current_stage": "design",
                "progress": 25,
                "created_at": "2025-10-20T10:00:00Z",
                "updated_at": "2025-10-20T10:05:00Z",
                "completed_at": None,
                "project_type": "web_app",
                "languages": ["Python", "TypeScript"],
                "frameworks": ["FastAPI", "React"],
                "files": [],
                "error": None
            }
        }


class ProjectListResponse(BaseModel):
    """Response model for listing projects."""
    
    projects: List[ProjectResponse] = Field(..., description="List of projects")
    total: int = Field(..., description="Total number of projects")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "projects": [
                    {
                        "id": "proj_abc123",
                        "name": "E-commerce Platform",
                        "status": "completed",
                        "current_stage": "handoff",
                        "progress": 100,
                        "created_at": "2025-10-20T10:00:00Z",
                        "updated_at": "2025-10-20T10:30:00Z",
                        "completed_at": "2025-10-20T10:30:00Z",
                        "project_type": "web_app",
                        "languages": ["Python", "TypeScript"],
                        "frameworks": ["FastAPI", "React"],
                        "files": ["project_design.md", "devplan.md", "handoff_prompt.md"],
                        "error": None
                    }
                ],
                "total": 1
            }
        }


class StreamMessage(BaseModel):
    """WebSocket message for streaming updates."""
    
    type: str = Field(..., description="Message type (token, progress, stage, error, complete)")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "type": "token",
                "data": {"token": "# Project", "stage": "design"},
                "timestamp": "2025-10-20T10:00:00Z"
            }
        }


class FileInfo(BaseModel):
    """Information about a generated file."""
    
    name: str = Field(..., description="File name")
    path: str = Field(..., description="File path")
    size: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="Creation timestamp")
    content_type: str = Field("text/markdown", description="MIME type")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "name": "project_design.md",
                "path": "web_projects/proj_abc123/project_design.md",
                "size": 4567,
                "created_at": "2025-10-20T10:15:00Z",
                "content_type": "text/markdown"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "error": "Project not found",
                "detail": "Project with ID 'proj_abc123' does not exist",
                "code": "PROJECT_NOT_FOUND"
            }
        }


# ============================================================================
# NEW: Iteration Support Models
# ============================================================================

class IterationRequest(BaseModel):
    """Request to iterate on current stage with user feedback."""
    
    feedback: str = Field(..., min_length=1, description="User feedback for iteration")
    regenerate: bool = Field(True, description="Whether to regenerate with feedback")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "feedback": "Please add more details about the database schema and add Redis for caching",
                "regenerate": True
            }
        }


class StageApproval(BaseModel):
    """Approval to move to next pipeline stage."""
    
    approved: bool = Field(True, description="Whether the stage is approved")
    notes: Optional[str] = Field(None, description="Optional notes about approval")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "approved": True,
                "notes": "Design looks great, ready to proceed to basic devplan"
            }
        }


class IterationHistory(BaseModel):
    """Track iteration history for a stage."""
    
    stage: PipelineStage = Field(..., description="Pipeline stage")
    iteration: int = Field(..., description="Iteration number")
    timestamp: datetime = Field(..., description="When this iteration occurred")
    feedback: str = Field(..., description="User feedback provided")
    output: str = Field(..., description="Generated output for this iteration")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "stage": "design",
                "iteration": 2,
                "timestamp": "2025-10-22T10:15:00Z",
                "feedback": "Add more details about authentication flow",
                "output": "# Updated Project Design\n\n..."
            }
        }

