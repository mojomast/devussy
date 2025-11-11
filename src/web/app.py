"""FastAPI application for DevPlan Orchestrator web interface.

This module provides a web-based interface for generating development plans,
allowing non-technical users to interact with the tool through a browser
instead of the command line.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.__version__ import __version__
from src.web.routes import projects, files, websocket_routes, config, templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    print(f"Starting DevPlan Orchestrator Web Interface v{__version__}")
    
    # Create necessary directories
    os.makedirs("web_projects", exist_ok=True)
    os.makedirs("web_projects/.config", exist_ok=True)
    os.makedirs("web_projects/.config/credentials", exist_ok=True)
    os.makedirs("web_projects/.config/presets", exist_ok=True)
    os.makedirs("web_projects/.config/projects", exist_ok=True)
    os.makedirs("web_projects/.config/templates", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    yield
    
    # Shutdown
    print("Shutting down DevPlan Orchestrator Web Interface")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="DevPlan Orchestrator",
        description="AI-powered development planning tool with web interface",
        version=__version__,
        lifespan=lifespan,
    )
    
    # CORS middleware for frontend access
    # In development, allow all localhost ports to make life easier
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # React dev server (default)
            "http://localhost:3001",  # Vite dev server (alternate port)
            "http://localhost:3002",  # Vite dev server (alternate port 2)
            "http://localhost:5173",  # Vite dev server (default)
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3002",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
    app.include_router(files.router, prefix="/api/files", tags=["files"])
    app.include_router(websocket_routes.router, prefix="/api/ws", tags=["websocket"])
    app.include_router(config.router, tags=["configuration"])
    app.include_router(templates.router, tags=["templates"])
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Check if the API is running."""
        return {"status": "healthy", "version": __version__}
    
    @app.get("/api/version")
    async def get_version():
        """Get the API version."""
        return {"version": __version__, "name": "DevPlan Orchestrator"}
    
    # Serve static files (frontend build) if they exist
    frontend_build_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_build_path.exists():
        app.mount("/assets", StaticFiles(directory=frontend_build_path / "assets"), name="assets")
        
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            """Serve the frontend application."""
            # Serve index.html for all routes (SPA)
            index_path = frontend_build_path / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return {"error": "Frontend not built"}
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "src.web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
