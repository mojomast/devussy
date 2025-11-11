"""WebSocket routes for real-time streaming."""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from src.web.models import StreamMessage
from src.web.project_manager import ProjectManager


router = APIRouter()
project_manager = ProjectManager()

# Track active WebSocket connections per project
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manage WebSocket connections for projects."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, project_id: str, websocket: WebSocket):
        """Connect a WebSocket to a project stream.
        
        Args:
            project_id: Project ID to stream
            websocket: WebSocket connection
        """
        await websocket.accept()
        
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        
        self.active_connections[project_id].add(websocket)
    
    def disconnect(self, project_id: str, websocket: WebSocket):
        """Disconnect a WebSocket from a project stream.
        
        Args:
            project_id: Project ID
            websocket: WebSocket connection
        """
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
    
    async def broadcast(self, project_id: str, message: StreamMessage):
        """Broadcast a message to all connections for a project.
        
        Args:
            project_id: Project ID
            message: Message to broadcast
        """
        if project_id not in self.active_connections:
            return
        
        # Create a copy to avoid modification during iteration
        connections = self.active_connections[project_id].copy()
        
        for connection in connections:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message.dict())
            except Exception:
                # Remove dead connections
                self.disconnect(project_id, connection)


manager = ConnectionManager()


@router.websocket("/{project_id}")
async def stream_project(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for streaming project updates.
    
    This endpoint provides real-time updates for a project's pipeline execution,
    including LLM token streaming, progress updates, stage changes, and errors.
    
    Args:
        websocket: WebSocket connection
        project_id: Project ID to stream
        
    Message Types:
        - token: LLM token output
        - progress: Progress percentage update
        - stage: Pipeline stage change
        - complete: Pipeline completion
        - error: Error occurred
    """
    await manager.connect(project_id, websocket)
    
    try:
        # Send initial connection message
        await websocket.send_json(
            StreamMessage(
                type="connected",
                data={"project_id": project_id, "message": "Connected to project stream"}
            ).dict()
        )
        
        # Get project status
        project = await project_manager.get_project(project_id)
        
        if not project:
            await websocket.send_json(
                StreamMessage(
                    type="error",
                    data={"error": f"Project '{project_id}' not found"}
                ).dict()
            )
            await websocket.close()
            return
        
        # Send current project status
        await websocket.send_json(
            StreamMessage(
                type="status",
                data={
                    "status": project.status.value,
                    "stage": project.current_stage.value if project.current_stage else None,
                    "progress": project.progress
                }
            ).dict()
        )
        
        # Keep connection alive and listen for messages
        while True:
            try:
                # Wait for client messages (e.g., ping, cancel request)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle client messages
                if message.get("type") == "ping":
                    await websocket.send_json(
                        StreamMessage(type="pong", data={}).dict()
                    )
                elif message.get("type") == "cancel":
                    # Request project cancellation
                    await project_manager.cancel_project(project_id)
                    await websocket.send_json(
                        StreamMessage(
                            type="cancelled",
                            data={"message": "Project cancellation requested"}
                        ).dict()
                    )
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                # Invalid JSON, ignore
                pass
            except Exception as e:
                # Other errors
                await websocket.send_json(
                    StreamMessage(
                        type="error",
                        data={"error": f"Error processing message: {str(e)}"}
                    ).dict()
                )
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        # Log error
        print(f"WebSocket error for project {project_id}: {e}")
    finally:
        manager.disconnect(project_id, websocket)


async def send_update(project_id: str, message: StreamMessage):
    """Send an update to all connected clients for a project.
    
    This function should be called by the project manager to broadcast updates.
    
    Args:
        project_id: Project ID
        message: Message to send
    """
    await manager.broadcast(project_id, message)
