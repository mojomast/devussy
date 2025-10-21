# DevPlan Orchestrator - Web Interface Guide

## Overview

The web interface provides a user-friendly browser-based UI for DevPlan Orchestrator, allowing non-technical users to generate development plans without using the command line.

## Architecture

### Backend (FastAPI)
- **Framework:** FastAPI with async support
- **WebSocket:** Real-time streaming of LLM responses
- **API:** RESTful API for project management
- **Location:** `src/web/`

### Frontend (React + TypeScript)
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite (fast development server)
- **Styling:** Tailwind CSS
- **State:** Zustand for global state
- **Location:** `frontend/`

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+ and npm
- All requirements from main README

### Backend Setup

1. **Install Python dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Ensure your `.env` file has the required API keys:
   ```
   OPENAI_API_KEY=your_key_here
   ```

3. **Run the FastAPI server:**
   ```powershell
   # From project root
   python -m src.web.app
   
   # Or using uvicorn directly
   uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Verify the API is running:**
   - Open http://localhost:8000/docs for interactive API documentation
   - Visit http://localhost:8000/health for health check

### Frontend Setup

1. **Navigate to frontend directory:**
   ```powershell
   cd frontend
   ```

2. **Install dependencies:**
   ```powershell
   npm install
   ```

3. **Run the development server:**
   ```powershell
   npm run dev
   ```

4. **Access the web interface:**
   - Open http://localhost:3000 in your browser

### Building for Production

**Frontend:**
```powershell
cd frontend
npm run build
```

The built files will be in `frontend/dist/` and will be automatically served by the FastAPI app when it runs.

**Full deployment:**
```powershell
# Build frontend
cd frontend
npm run build
cd ..

# Run backend (serves frontend automatically)
uvicorn src.web.app:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Projects

**POST /api/projects/**
- Create a new project
- Body: `ProjectCreateRequest`
- Returns: `ProjectResponse`

**GET /api/projects/**
- List all projects
- Query params: `status`, `limit`, `offset`
- Returns: `ProjectListResponse`

**GET /api/projects/{project_id}**
- Get project details
- Returns: `ProjectResponse`

**DELETE /api/projects/{project_id}**
- Delete a project
- Returns: 204 No Content

**POST /api/projects/{project_id}/cancel**
- Cancel a running project
- Returns: `ProjectResponse`

### Files

**GET /api/files/{project_id}**
- List files for a project
- Returns: `List[FileInfo]`

**GET /api/files/{project_id}/{filename}**
- Download a file
- Returns: File content

**GET /api/files/{project_id}/{filename}/content**
- Get file content as JSON
- Returns: `{"filename": str, "content": str, "size": int}`

### WebSocket

**WS /api/ws/{project_id}**
- Stream real-time updates for a project
- Message types:
  - `connected`: Connection established
  - `status`: Project status update
  - `token`: LLM token streamed
  - `progress`: Progress percentage
  - `stage`: Pipeline stage changed
  - `complete`: Pipeline completed
  - `error`: Error occurred
  - `cancelled`: Project cancelled

## Usage Flow

### Creating a Project via Web UI

1. **Navigate to http://localhost:3000**
2. **Click "Create New Project"**
3. **Fill out the form:**
   - Project name
   - Project type (Web App, API, CLI, etc.)
   - Programming languages
   - Requirements (detailed description)
   - Frameworks (optional)
   - APIs (optional)
   - Other configuration
4. **Click "Generate Development Plan"**
5. **Watch real-time progress:**
   - See pipeline stages (Design → DevPlan → Handoff)
   - View streaming LLM responses
   - Track progress percentage
6. **View and download results:**
   - Browse generated files
   - Copy content to clipboard
   - Download as markdown files

### Using the API Directly

**Example: Create Project**
```python
import requests

response = requests.post('http://localhost:8000/api/projects/', json={
    "name": "E-commerce Platform",
    "project_type": "web_app",
    "languages": ["Python", "TypeScript"],
    "requirements": "Build a scalable e-commerce platform...",
    "frameworks": ["FastAPI", "React"],
    "apis": ["Stripe", "SendGrid"],
    "database": "PostgreSQL",
    "authentication": True
})

project = response.json()
project_id = project['id']
```

**Example: Stream Updates via WebSocket**
```python
import asyncio
import websockets
import json

async def stream_project(project_id):
    uri = f"ws://localhost:8000/api/ws/{project_id}"
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data['type'] == 'token':
                print(data['data']['token'], end='', flush=True)
            elif data['type'] == 'complete':
                print("\nProject completed!")
                break
            elif data['type'] == 'error':
                print(f"\nError: {data['data']['error']}")
                break

asyncio.run(stream_project('proj_abc123'))
```

## Development

### Project Structure

```
src/web/
├── __init__.py          # Package initialization
├── app.py               # FastAPI application
├── models.py            # Pydantic models for API
├── project_manager.py   # Project lifecycle management
└── routes/
    ├── __init__.py
    ├── projects.py      # Project CRUD endpoints
    ├── files.py         # File download endpoints
    └── websocket_routes.py  # WebSocket streaming

frontend/
├── src/
│   ├── main.tsx         # Entry point
│   ├── App.tsx          # Main app component
│   ├── components/      # Reusable components
│   ├── pages/           # Page components
│   ├── services/        # API client
│   └── stores/          # State management
├── public/              # Static assets
├── package.json         # NPM dependencies
├── vite.config.ts       # Vite configuration
└── tailwind.config.js   # Tailwind CSS config
```

### Adding New Features

**Backend (Add new API endpoint):**
1. Define Pydantic models in `models.py`
2. Create route handler in `routes/`
3. Register router in `app.py`
4. Add tests in `tests/web/`

**Frontend (Add new page):**
1. Create component in `src/pages/`
2. Add route in `src/App.tsx`
3. Create API service in `src/services/`
4. Update navigation

## Testing

### Backend Tests
```powershell
# Create tests/web/ directory
pytest tests/web/ -v
```

### Frontend Tests
```powershell
cd frontend
npm test
```

### End-to-End Tests
```powershell
# Using Playwright or Cypress
cd frontend
npm run test:e2e
```

## Deployment

### Docker Deployment (Recommended)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/
COPY templates/ ./templates/

# Copy frontend build
COPY frontend/dist/ ./frontend/dist/

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```powershell
docker build -t devplan-orchestrator .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key devplan-orchestrator
```

### Cloud Deployment

**Option 1: Railway**
1. Connect GitHub repository
2. Set environment variables (OPENAI_API_KEY)
3. Deploy automatically

**Option 2: Render**
1. Create new Web Service
2. Build command: `cd frontend && npm install && npm run build`
3. Start command: `uvicorn src.web.app:app --host 0.0.0.0 --port $PORT`

**Option 3: AWS EC2**
1. Launch Ubuntu instance
2. Install Python, Node.js, and dependencies
3. Set up nginx reverse proxy
4. Use PM2 or systemd for process management

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional - per-stage API keys
DESIGN_API_KEY=sk-design-...
DEVPLAN_API_KEY=sk-devplan-...
HANDOFF_API_KEY=sk-handoff-...

# Optional - API base URLs
GENERIC_API_BASE_URL=https://api.example.com/v1
```

### CORS Configuration

Edit `src/web/app.py` to allow additional origins:
```python
allow_origins=[
    "http://localhost:3000",
    "https://your-domain.com",
]
```

## Troubleshooting

### Backend Issues

**Issue: FastAPI not starting**
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <pid> /F
```

**Issue: Import errors**
```powershell
# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Issues

**Issue: Cannot connect to API**
- Verify backend is running on port 8000
- Check CORS configuration
- Ensure proxy is configured in `vite.config.ts`

**Issue: WebSocket connection fails**
- Verify WebSocket endpoint is accessible
- Check browser console for errors
- Ensure firewall allows WebSocket connections

## Security Considerations

1. **API Keys:** Never commit API keys to version control
2. **CORS:** Restrict allowed origins in production
3. **Authentication:** Add user authentication for production use
4. **Rate Limiting:** Implement rate limiting to prevent abuse
5. **Input Validation:** All inputs are validated with Pydantic
6. **File Access:** File downloads are restricted to project directories

## Next Steps

- [ ] Add user authentication (JWT)
- [ ] Implement project sharing
- [ ] Add export to PDF
- [ ] Create project templates
- [ ] Add team collaboration features
- [ ] Implement cost tracking
- [ ] Add analytics dashboard

## Support

For issues or questions:
- Open an issue on GitHub
- Check API documentation: http://localhost:8000/docs
- Review logs in `logs/` directory

---

**Last Updated:** October 20, 2025
**Version:** 0.2.2 (Phase 11 in progress)
