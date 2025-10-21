"""File management routes for the web API."""

import os
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from src.web.models import FileInfo, ErrorResponse
from src.web.project_manager import ProjectManager


router = APIRouter()
project_manager = ProjectManager()


@router.get("/{project_id}", response_model=List[FileInfo])
async def list_project_files(project_id: str) -> List[FileInfo]:
    """List all files for a project.
    
    Args:
        project_id: Unique project ID
        
    Returns:
        List[FileInfo]: List of file information
        
    Raises:
        HTTPException: If project not found
    """
    project = await project_manager.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found"
        )
    
    files = await project_manager.list_files(project_id)
    return files


@router.get("/{project_id}/{filename}")
async def download_file(project_id: str, filename: str):
    """Download a specific file from a project.
    
    Args:
        project_id: Unique project ID
        filename: Name of the file to download
        
    Returns:
        FileResponse: File download response
        
    Raises:
        HTTPException: If project or file not found
    """
    project = await project_manager.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found"
        )
    
    file_path = await project_manager.get_file_path(project_id, filename)
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found in project '{project_id}'"
        )
    
    # Determine content type
    content_type = "text/markdown" if filename.endswith(".md") else "application/octet-stream"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=content_type
    )


@router.get("/{project_id}/{filename}/content")
async def get_file_content(project_id: str, filename: str) -> dict:
    """Get the text content of a file.
    
    Args:
        project_id: Unique project ID
        filename: Name of the file
        
    Returns:
        dict: File content as JSON
        
    Raises:
        HTTPException: If project or file not found
    """
    project = await project_manager.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found"
        )
    
    file_path = await project_manager.get_file_path(project_id, filename)
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found in project '{project_id}'"
        )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "filename": filename,
            "content": content,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file: {str(e)}"
        )
