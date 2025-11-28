"""FastAPI streaming server wrapper using existing generator pipeline.

This file is a skeleton for a FastAPI app that accepts a POST to `/api/design/stream`
and streams events using Server-Sent Events (SSE). It uses the existing
`ProjectDesignGenerator` from `src.pipeline.project_design`. This file is a
starting point and will need additional validation and tests.
"""

import time
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

# Handle both package and direct module execution
try:
    from .analytics import init_db, log_session, log_api_call, log_user_input, get_overview
except ImportError:
    from analytics import init_db, log_session, log_api_call, log_user_input, get_overview

from fastapi.responses import StreamingResponse, JSONResponse
import json
import tempfile
import shutil
import requests
from src.git_manager import GitManager
import os
import asyncio
from pathlib import Path
import aiohttp

from src.config import load_config
from src.clients.factory import create_llm_client
from src.pipeline.project_design import ProjectDesignGenerator
from src.pipeline.basic_devplan import BasicDevPlanGenerator
from src.pipeline.detailed_devplan import DetailedDevPlanGenerator
from src.pipeline.handoff_prompt import HandoffPromptGenerator
from src.pipeline.hivemind import HiveMindManager
from src.pipeline.design_validator import DesignValidator
from src.pipeline.design_correction_loop import DesignCorrectionLoop, LLMDesignCorrectionLoop
from src.pipeline.llm_sanity_reviewer import LLMSanityReviewer, LLMSanityReviewerWithLLM
from src.interview.complexity_analyzer import ComplexityAnalyzer, ComplexityProfile, LLMComplexityAnalyzer
from src.models import ProjectDesign, DevPlan
from src.concurrency import ConcurrencyManager
import os
import glob
import time

# Optional secret for proxy authentication
STREAMING_SECRET = os.getenv("STREAMING_SECRET")

# SSE headers to prevent proxy buffering (Next.js, nginx, etc.)
SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # nginx
}

def _validate_incoming_request(x_streaming_proxy_key: str | None) -> None:
    """Validate the proxy key if a secret is configured.
    In local Docker deployments the secret is often unset, so the check is skipped.
    """
    if STREAMING_SECRET and x_streaming_proxy_key != STREAMING_SECRET:
        raise HTTPException(status_code=403, detail="Invalid streaming proxy key")

app = FastAPI()

# Configure CORS origins based on environment
# In Docker/VPS, ALLOWED_ORIGINS env var can specify production origins
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    # Production: use env var (comma-separated list)
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # Local development: allow localhost
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analytics DB on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Middleware to log each request and response
class AnalyticsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        analytics_opt_out = request.cookies.get("devussy_analytics_optout")
        if analytics_opt_out and analytics_opt_out.lower() in ("1", "true", "yes"):
            return await call_next(request)
        # Session handling: use cookie or generate new
        session_id = request.cookies.get("devussy_session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
        # Attach session to request state so route handlers can reuse it
        request.state.session_id = session_id
        # Log session (IP hashing)
        client_ip = request.client.host if request.client else "0.0.0.0"
        user_agent = request.headers.get("user-agent")
        log_session(session_id, client_ip, user_agent)
        # Record request details
        start = time.time()
        # DON'T consume request body here - let the endpoint handler read it
        # This was causing ClientDisconnect errors
        request_size = 0  # We can't reliably get size without consuming body
        # Process request
        response = await call_next(request)
        # Record response details (duration until response object is ready)
        duration_ms = (time.time() - start) * 1000
        # Try to infer response size from Content-Length header if present
        content_length = response.headers.get("content-length")
        try:
            response_size = int(content_length) if content_length is not None else 0
        except ValueError:
            response_size = 0
        # Determine model used from response header if provided
        model_used = response.headers.get("x-model-used")
        # Log API call
        log_api_call(
            session_id=session_id,
            endpoint=str(request.url.path),
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_size=request_size,
            response_size=response_size,
            model_used=model_used,
        )
        # Set session cookie in response
        response.set_cookie(key="devussy_session_id", value=session_id, httponly=True, samesite="lax")
        return response

app.add_middleware(AnalyticsMiddleware)

@app.post("/api/design/stream")
async def design_stream(request: Request, x_streaming_proxy_key: str | None = Header(None)):
    _validate_incoming_request(x_streaming_proxy_key)

    body = await request.json()
    project_name = body.get("projectName") or body.get("project_name") or "Unnamed"
    languages = body.get("languages", [])
    requirements = body.get("requirements") or body.get("description", "")
    # Log user input for analytics
    analytics_opt_out = request.cookies.get("devussy_analytics_optout")
    if not (analytics_opt_out and analytics_opt_out.lower() in ("1", "true", "yes")):
        session_id = getattr(
            request.state,
            "session_id",
            request.cookies.get("devussy_session_id") or "unknown",
        )
        log_user_input(
            session_id=session_id,
            input_type="design_input",
            project_name=project_name,
            requirements=requirements,
            languages=languages,
        )

    # Load config
    config = load_config()
    incoming_api_key = (
        getattr(config.llm, "api_key", None)
        or os.environ.get("REQUESTY_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("GENERIC_API_KEY")
    )
    if incoming_api_key:
        config.llm.api_key = incoming_api_key
    else:
        raise HTTPException(status_code=400, detail="Missing LLM API key")

    config.llm.provider = "requesty"
    # Force streaming for this endpoint
    config.llm.streaming_enabled = True

    llm_client = create_llm_client(config)
    # Explicitly set streaming_enabled on the client instance to ensure it's picked up
    # This fixes the issue where LLMClient checks config.streaming_enabled but we set config.llm.streaming_enabled
    llm_client.streaming_enabled = True

    generator = ProjectDesignGenerator(llm_client)

    async def event_generator():
        try:
            # Create an async queue where the handler will push tokens.
            queue: asyncio.Queue[str | None] = asyncio.Queue()

            class QueueStreamingHandler:
                def __init__(self, queue: asyncio.Queue):
                    self._queue = queue
                    # Use the existing StreamingHandler's helpers if needed

                async def on_token_async(self, token: str) -> None:
                    await self._queue.put(token)

                async def on_completion_async(self, full_response: str) -> None:
                    # Signal completion
                    await self._queue.put(None)

                async def __aenter__(self):
                    return self

                async def __aexit__(self, exc_type, exc, tb):
                    return False

            streaming_handler = QueueStreamingHandler(queue)

            # Launch a task to run the generator with streaming handler
            async def run_generation():
                try:
                    # Generate returns the structured ProjectDesign object
                    design_result = await generator.generate(
                        project_name=project_name,
                        languages=languages,
                        requirements=requirements,
                        streaming_handler=streaming_handler,
                    )
                    # Send the structured design object as the final event
                    await queue.put({'done': True, 'design': design_result.model_dump()})
                except Exception as e:
                    # Log the error and push it to the queue so the client knows something went wrong
                    print(f"ERROR in run_generation: {e}")
                    import traceback
                    traceback.print_exc()
                    await queue.put({'error': str(e)})
                    await queue.put(None) # Signal end of stream on error
                finally:
                    # Ensure the queue gets termination signal if generator finishes
                    await queue.put(None)

            generation_task = asyncio.create_task(run_generation())

            # Yield tokens as SSE
            while True:
                item = await queue.get()
                if item is None:
                    break
                elif isinstance(item, dict):
                    # Handle done/error messages with full design object
                    yield f"data: {json.dumps(item)}\n\n"
                else:
                    # Regular token
                    yield f"data: {json.dumps({'content': item})}\n\n"
                # Yield a newline to flush the buffer immediately
                yield ":\n\n"

        except asyncio.CancelledError:
            # client disconnected
            return

    # Add headers to prevent proxy buffering (Next.js, nginx, etc.)
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # nginx
    }
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)


@app.post("/api/design")
async def design_stream_alias(request: Request, x_streaming_proxy_key: str | None = Header(None)):
    """Alias for `/api/design/stream` kept for backwards compatibility with the frontend which hits `/api/design` for SSE streaming."""
    _validate_incoming_request(x_streaming_proxy_key)
    return await design_stream(request, x_streaming_proxy_key)

# Analytics overview endpoint
@app.get("/api/analytics/overview")
async def analytics_overview():
    return get_overview()

@app.post("/api/design/hivemind")
async def design_hivemind(request: Request):
    _validate_incoming_request(request.headers.get('x-streaming-proxy-key'))
    data = await request.json()
    project_name = data.get('projectName')
    requirements = data.get('requirements')
    languages = data.get('languages', [])
    if not project_name or not requirements:
        raise HTTPException(status_code=400, detail='Missing required data')

    model_config = data.get('modelConfig', {})
    config = load_config()
    if model_config.get('model'):
        config.llm.model = model_config.get('model')
    if model_config.get('temperature') is not None:
        config.llm.temperature = float(model_config.get('temperature'))

    async def event_generator():
        llm_client = create_llm_client(config)
        hivemind = HiveMindManager(llm_client)
        queue: asyncio.Queue = asyncio.Queue()

        class DroneHandler:
            def __init__(self, drone_id: str):
                self.drone_id = drone_id
            async def on_token_async(self, token: str):
                await queue.put({'type': self.drone_id, 'content': token})
            async def on_completion_async(self, full_response: str):
                await queue.put({'type': f'{self.drone_id}_complete'})

        try:
            prompt_context = {
                'project_name': project_name,
                'languages': languages,
                'frameworks': [],
                'apis': [],
                'requirements': requirements,
            }
            from src.templates import render_template
            prompt = render_template('project_design.jinja', prompt_context)

            drone_handlers = [DroneHandler('drone1'), DroneHandler('drone2'), DroneHandler('drone3')]
            arbiter_handler = DroneHandler('arbiter')

            async def run_swarm():
                final_response = await hivemind.run_swarm(
                    prompt=prompt,
                    count=3,
                    temperature_jitter=True,
                    drone_callbacks=drone_handlers,
                    arbiter_callback=arbiter_handler,
                )
                await queue.put({'done': True, 'design': {'project_name': project_name, 'raw_response': final_response}})

            task = asyncio.create_task(run_swarm())

            while True:
                item = await queue.get()
                if item.get('content'):
                    # drone or arbiter token
                    yield f"data: {json.dumps({'type': item['type'], 'content': item['content']})}\n\n"
                elif item.get('type') and item['type'].endswith('_complete'):
                    yield f"data: {json.dumps({'type': item['type']})}\n\n"
                elif item.get('done'):
                    yield f"data: {json.dumps({'done': True, 'design': item.get('design')})}\n\n"
                    break
        except asyncio.CancelledError:
            return

    return StreamingResponse(event_generator(), media_type='text/event-stream', headers=SSE_HEADERS)


@app.post("/api/plan/hivemind")
async def plan_hivemind(request: Request):
    # Accept POST with a plan and optional model config
    _validate_incoming_request(request.headers.get('x-streaming-proxy-key'))
    data = await request.json()
    plan_data = data.get('plan') or data.get('basicPlan')
    project_name = data.get('projectName') or (plan_data and plan_data.get('name'))
    if not plan_data or not project_name:
        raise HTTPException(status_code=400, detail='Missing required data')

    model_config = data.get('modelConfig', {})
    config = load_config()
    if model_config.get('model'):
        config.llm.model = model_config.get('model')
    if model_config.get('temperature') is not None:
        config.llm.temperature = float(model_config.get('temperature'))

    async def event_generator():
        llm_client = create_llm_client(config)
        hivemind = HiveMindManager(llm_client)
        queue: asyncio.Queue = asyncio.Queue()

        class DroneHandler:
            def __init__(self, drone_id: str):
                self.drone_id = drone_id
            async def on_token_async(self, token: str):
                await queue.put({'type': self.drone_id, 'content': token})
            async def on_completion_async(self, full_response: str):
                await queue.put({'type': f'{self.drone_id}_complete'})

        try:
            # Build prompt from plan JSON by summarizing phases
            prompt = """Generate a design summary and improvements for this development plan:\n"""
            try:
                # Try to create a short summary from plan
                phases = plan_data.get('phases', [])
                prompt += f"Project: {project_name}\nPhases:\n"
                for p in phases:
                    prompt += f"- {p.get('number')}: {p.get('title')}\n"
            except Exception:
                prompt += json.dumps(plan_data)[:1000]

            drone_handlers = [DroneHandler('drone1'), DroneHandler('drone2'), DroneHandler('drone3')]
            arbiter_handler = DroneHandler('arbiter')

            async def run_swarm():
                final_response = await hivemind.run_swarm(
                    prompt=prompt,
                    count=3,
                    temperature_jitter=True,
                    drone_callbacks=drone_handlers,
                    arbiter_callback=arbiter_handler,
                )
                await queue.put({'done': True, 'design': {'project_name': project_name, 'raw_response': final_response}})

            task = asyncio.create_task(run_swarm())

            while True:
                item = await queue.get()
                if item.get('content'):
                    yield f"data: {json.dumps({'type': item['type'], 'content': item['content']})}\n\n"
                elif item.get('type') and item['type'].endswith('_complete'):
                    yield f"data: {json.dumps({'type': item['type']})}\n\n"
                elif item.get('done'):
                    yield f"data: {json.dumps({'done': True, 'design': item.get('design')})}\n\n"
                    break
        except asyncio.CancelledError:
            return

    return StreamingResponse(event_generator(), media_type='text/event-stream', headers=SSE_HEADERS)


@app.post("/api/interview")
async def interview_endpoint(request: Request):
    print("[DEBUG] /api/interview called")
    try:
        data = await request.json()
        print(f"[DEBUG] Interview data keys: {list(data.keys())}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    
    user_input = data.get("userInput")
    history = data.get("history", [])
    model_config = data.get("modelConfig", {})

    if not user_input:
        raise HTTPException(status_code=400, detail="Missing userInput")

    config = load_config()
    # Apply model overrides
    if model_config.get("model"):
        config.llm.model = model_config.get("model")
    if model_config.get("temperature") is not None:
        config.llm.temperature = float(model_config.get("temperature"))
    if model_config.get("reasoning_effort"):
        config.llm.reasoning_effort = model_config.get("reasoning_effort")

    # Use LLMInterviewManager but call in executor to avoid blocking
    manager = None
    try:
        from src.llm_interview import LLMInterviewManager
        print("[DEBUG] Importing LLMInterviewManager...")
        manager = LLMInterviewManager(config, verbose=False)
        print("[DEBUG] LLMInterviewManager initialized")
    except Exception as e:
        import traceback
        print(f"[ERROR] Failed to init manager: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize interview manager: {e}")

    # Important: conversation_history starts with system prompt
    # We need to append history AFTER system prompt but BEFORE user message
    if history:
        try:
            # Validate history format
            if not isinstance(history, list):
                raise ValueError("history must be a list")
            
            # Filter out system messages from frontend history
            user_history = [msg for msg in history if isinstance(msg, dict) and msg.get("role") != "system"]
            
            # Extend conversation history (after system prompt which is already added in __init__)
            manager.conversation_history.extend(user_history)
        except Exception as e:
            print(f"Warning: Failed to process history: {e}")
            # Continue without history rather than failing

    loop = asyncio.get_running_loop()
    max_retries = 2
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            print(f"[DEBUG] Calling LLM with input (attempt {attempt + 1}/{max_retries + 1}): {user_input[:100]}...")
            response_text = await loop.run_in_executor(None, manager._send_to_llm, user_input)
            print(f"[DEBUG] Got LLM response: {len(response_text)} chars")
            break  # Success, exit retry loop
        except Exception as e:
            import traceback
            last_error = e
            error_str = str(e).lower()
            print(f"[ERROR] LLM call failed (attempt {attempt + 1}): {traceback.format_exc()}")
            
            # Retry on transient errors (timeouts, connection issues)
            is_retryable = any(term in error_str for term in ['timeout', 'connection', 'temporarily', 'rate limit', 'overloaded'])
            
            if attempt < max_retries and is_retryable:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s
                print(f"[DEBUG] Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                # Re-initialize manager for fresh state on retry
                manager = LLMInterviewManager(config, verbose=False)
                if history:
                    user_history = [msg for msg in history if isinstance(msg, dict) and msg.get("role") != "system"]
                    manager.conversation_history.extend(user_history)
            else:
                raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

    extracted = manager._extract_structured_data(response_text)
    is_complete = manager._validate_extracted_data(extracted) if extracted else False
    print(f"[DEBUG] Interview complete={is_complete}, extracted={extracted is not None}")
    return JSONResponse(status_code=200, content={"response": response_text, "extractedData": extracted, "isComplete": is_complete})


@app.get("/api/checkpoints")
async def checkpoints_get(id: str | None = None):
    CHECKPOINT_DIR = ".checkpoints"
    if not os.path.exists(CHECKPOINT_DIR):
        os.makedirs(CHECKPOINT_DIR)

    if id:
        filepath = os.path.join(CHECKPOINT_DIR, f"{id}.json")
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Checkpoint not found")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return JSONResponse(status_code=200, content=data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        files = glob.glob(os.path.join(CHECKPOINT_DIR, "*.json"))
        files.sort(key=os.path.getmtime, reverse=True)
        checkpoints = []
        for filepath in files:
            filename = os.path.basename(filepath)
            checkpoint_id = filename.replace('.json', '')
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    checkpoints.append({
                        "id": checkpoint_id,
                        "name": data.get("name", checkpoint_id),
                        "timestamp": data.get("timestamp", os.path.getmtime(filepath)),
                        "projectName": data.get("projectName", "Unknown Project"),
                        "stage": data.get("stage", "unknown")
                    })
            except Exception:
                continue
        return JSONResponse(status_code=200, content={"checkpoints": checkpoints})


@app.post("/api/checkpoints")
async def checkpoints_post(request: Request):
    data = await request.json()
    CHECKPOINT_DIR = ".checkpoints"
    if not os.path.exists(CHECKPOINT_DIR):
        os.makedirs(CHECKPOINT_DIR)
    timestamp = int(time.time())
    name = data.get("name", "checkpoint").replace(' ', '_')
    checkpoint_id = f"{timestamp}_{name}"
    data["timestamp"] = timestamp
    data["id"] = checkpoint_id
    filepath = os.path.join(CHECKPOINT_DIR, f"{checkpoint_id}.json")
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return JSONResponse(status_code=200, content={"success": True, "id": checkpoint_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/handoff")
async def handoff_endpoint(request: Request):
    data = await request.json()
    design_data = data.get('design')
    plan_data = data.get('plan')
    if not design_data or not plan_data:
        raise HTTPException(status_code=400, detail="Missing design or plan data")

    try:
        design = ProjectDesign(**design_data)
        plan = DevPlan(**plan_data)
        generator = HandoffPromptGenerator()
        # Handoff generator may be synchronous; run in executor
        loop = asyncio.get_running_loop()
        # Call with correct parameter names
        handoff = await loop.run_in_executor(
            None, 
            generator.generate,
            plan,  # devplan parameter
            design.project_name,  # project_name parameter
            design.architecture_overview or "",  # project_summary parameter
            design.architecture_overview or "",  # architecture_notes parameter
            ", ".join(design.dependencies) if design.dependencies else "",  # dependencies_notes parameter
            "",  # config_notes parameter
            5  # task_group_size parameter (default)
        )
        return JSONResponse(status_code=200, content=handoff.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/github/create")
async def github_create(request: Request):
    data = await request.json()
    repo_name = data.get('repoName')
    token = data.get('token')
    design = data.get('design', {})
    plan = data.get('plan', {})
    handoff_content = data.get('handoffContent', '')

    if not repo_name or not token:
        raise HTTPException(status_code=400, detail="Missing repoName or token")

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    api_url = 'https://api.github.com/user/repos'
    payload = {
        'name': repo_name,
        'private': True,
        'description': f"Generated by Devussy: {design.get('project_name', 'Project')}"
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code not in [200, 201]:
            err_msg = response.json().get('message', 'Unknown error')
            raise HTTPException(status_code=400, detail=f"GitHub API Error: {err_msg}")
        repo_data = response.json()
        clone_url = repo_data['clone_url']
        auth_clone_url = clone_url.replace('https://', f'https://{token}@')

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Write README, design, plan, handoff
            with open(temp_path / 'README.md', 'w', encoding='utf-8') as f:
                f.write(f"# {design.get('project_name', 'Devussy Project')}\n\n")
                f.write(f"Generated by Devussy.\n\n")
                f.write(f"## Description\n{design.get('description', 'No description provided.')}\n")
            with open(temp_path / 'project_design.md', 'w', encoding='utf-8') as f:
                f.write(design.get('raw_response') or json.dumps(design, indent=2))
            with open(temp_path / 'development_plan.md', 'w', encoding='utf-8') as f:
                f.write(json.dumps(plan, indent=2))
            if handoff_content:
                with open(temp_path / 'handoff_instructions.md', 'w', encoding='utf-8') as f:
                    f.write(handoff_content)
            phases_dir = temp_path / 'phases'
            phases_dir.mkdir(exist_ok=True)
            if plan and 'phases' in plan:
                for phase in plan['phases']:
                    p_num = phase.get('number', 0)
                    p_title = phase.get('title', f'Phase {p_num}').replace(' ', '_').lower()
                    p_filename = f"phase_{p_num}_{p_title}.md"
                    content = f"# Phase {p_num}: {phase.get('title', 'Untitled')}\n\n"
                    content += f"## Description\n{phase.get('description', '')}\n\n"
                    if 'steps' in phase:
                        content += "## Steps\n"
                        for idx, step in enumerate(phase['steps']):
                            content += f"### {idx+1}. {step.get('title', 'Step')}\n"
                            content += f"{step.get('description', '')}\n\n"
                    with open(phases_dir / p_filename, 'w', encoding='utf-8') as f:
                        f.write(content)

            # Git operations
            try:
                git = GitManager(temp_path)
                git.init_repository()
                git.add_remote('origin', auth_clone_url)
                git.commit_changes('Initial commit by Devussy')
                try:
                    git.push('origin', 'master')
                except Exception:
                    git.push('origin', 'main')
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        return JSONResponse(status_code=200, content={'status': 'success', 'data': {'repoUrl': repo_data['html_url'], 'message': 'Repository created and code pushed successfully!'}})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/plan/basic")
async def plan_basic(request: Request):
    _validate_incoming_request(request.headers.get('x-streaming-proxy-key'))
    data = await request.json()
    design_data = data.get('design')
    if not design_data:
        raise HTTPException(status_code=400, detail="Missing design data")

    # Debug logging
    print(f"[plan_basic] Received design data with keys: {list(design_data.keys())}")
    print(f"[plan_basic] project_name: {design_data.get('project_name', 'MISSING')}")
    print(f"[plan_basic] objectives count: {len(design_data.get('objectives', []))}")
    print(f"[plan_basic] tech_stack count: {len(design_data.get('tech_stack', []))}")
    print(f"[plan_basic] Has architecture_overview: {bool(design_data.get('architecture_overview'))}")

    try:
        design = ProjectDesign(**design_data)
    except Exception as e:
        print(f"[plan_basic] ERROR parsing ProjectDesign: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # Optional overrides
    model_config = data.get('modelConfig', {})
    config = load_config()
    if model_config.get('model'):
        config.llm.model = model_config.get('model')
    if model_config.get('temperature') is not None:
        config.llm.temperature = float(model_config.get('temperature'))

    # Stream as SSE
    async def event_generator():
        llm_client = create_llm_client(config)
        generator = BasicDevPlanGenerator(llm_client)

        class StreamHandler:
            def __init__(self):
                pass

            async def on_token_async(self, token: str):
                yield_token = f"data: {json.dumps({'content': token})}\n\n"
                yield yield_token

            async def on_completion_async(self, full_response: str):
                return

        # Streaming via async call
        try:
            # We will emulate an async streaming handler by writing to queue
            queue: asyncio.Queue = asyncio.Queue()

            class APIHandler:
                async def on_token_async(self, token: str):
                    await queue.put({'content': token})

                async def on_completion_async(self, full_response: str):
                    await queue.put({'done': True, 'plan': full_response})

            api_handler = APIHandler()

            async def run_generation():
                result = await generator.generate(project_design=design, streaming_handler=api_handler)
                # Put final plan data
                await queue.put({'done': True, 'plan': result.model_dump()})

            task = asyncio.create_task(run_generation())

            while True:
                item = await queue.get()
                if 'content' in item:
                    yield f"data: {json.dumps({'content': item['content']})}\n\n"
                elif item.get('done'):
                    yield f"data: {json.dumps({'done': True, 'plan': item.get('plan')})}\n\n"
                    break
        except asyncio.CancelledError:
            return

    return StreamingResponse(event_generator(), media_type='text/event-stream', headers=SSE_HEADERS)


@app.post("/api/plan/detail")
async def plan_detail(request: Request):
    _validate_incoming_request(request.headers.get('x-streaming-proxy-key'))
    data = await request.json()
    plan_data = data.get('plan') or data.get('basicPlan')
    phase_number = data.get('phaseNumber')
    project_name = data.get('projectName')

    if not plan_data or phase_number is None or not project_name:
        raise HTTPException(status_code=400, detail="Missing required data")

    try:
        dev_plan = DevPlan(**plan_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Find phase
    target_phase = None
    for p in dev_plan.phases:
        if p.number == phase_number:
            target_phase = p
            break
    if not target_phase:
        raise HTTPException(status_code=400, detail=f"Phase {phase_number} not found")

    model_config = data.get('modelConfig', {})
    config = load_config()
    if model_config.get('model'):
        config.llm.model = model_config.get('model')
    if model_config.get('temperature') is not None:
        config.llm.temperature = float(model_config.get('temperature'))

    # Force streaming enabled for this endpoint
    config.llm.streaming_enabled = True

    async def event_generator():
        llm_client = create_llm_client(config)
        # Explicitly set streaming_enabled on the client instance
        llm_client.streaming_enabled = True

        concurrency_manager = ConcurrencyManager(config)
        generator = DetailedDevPlanGenerator(llm_client, concurrency_manager)
        queue: asyncio.Queue = asyncio.Queue()

        class APIHandler:
            async def on_token_async(self, token: str):
                await queue.put({'content': token})

            async def on_completion_async(self, full_response: str):
                await queue.put({'done': True, 'phase': full_response})

        api_handler = APIHandler()

        async def run_gen():
            detailed_phase = await generator._generate_phase_details(
                phase=target_phase,
                project_name=project_name,
                tech_stack=[],
                task_group_size=3,
                streaming_handler=api_handler,
            )
            await queue.put({'done': True, 'phase': detailed_phase.phase.model_dump()})

        task = asyncio.create_task(run_gen())

        try:
            while True:
                item = await queue.get()
                if 'content' in item:
                    yield f"data: {json.dumps({'content': item['content']})}\n\n"
                elif item.get('done'):
                    yield f"data: {json.dumps({'done': True, 'phase': item.get('phase')})}\n\n"
                    break
        except asyncio.CancelledError:
            return

    return StreamingResponse(event_generator(), media_type='text/event-stream', headers=SSE_HEADERS)



@app.get("/api/models")
async def get_models():
    """Fetch available models from the configured LLM provider (Requesty router by default).

    This mirrors the helper handler in the repository's dev_server and allows the
    frontend to query models in production via the streaming server.
    """
    # Load config and API key
    config = load_config()
    api_key = getattr(config.llm, "api_key", None) or os.environ.get("REQUESTY_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Requesty API key not configured")

    base_url = getattr(config.llm, "base_url", None) or "https://router.requesty.ai/v1"
    endpoint = f"{base_url.rstrip('/')}/models"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers) as resp:
                if resp.status >= 400:
                    error_text = await resp.text()
                    raise HTTPException(status_code=502, detail=f"Requesty API error {resp.status}: {error_text}")
                data = await resp.json()

        # Normalize model shapes into: id, name, description, context_window
        models = data.get("data", data.get("models", []))
        sanitized = []
        for raw in models:
            model_id = raw.get("id") or raw.get("name")
            if not model_id:
                continue
            sanitized.append({
                "id": model_id,
                "name": raw.get("name", model_id),
                "description": raw.get("description", ""),
                "context_window": raw.get("context_window", raw.get("max_tokens")),
            })

        return JSONResponse(status_code=200, content={"models": sanitized})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Design & Plan Refinement Endpoints (Interactive Iteration)
# =============================================================================

@app.post("/api/design/refine")
async def design_refine(request: Request):
    """Interactive design refinement via chat interface.
    
    Takes design + chat history and streams conversational responses
    to help users iterate on the design before generating phases.
    """
    _validate_incoming_request(request.headers.get('x-streaming-proxy-key'))
    data = await request.json()
    design_data = data.get('design')
    project_name = data.get('projectName', '')
    requirements = data.get('requirements', '')
    chat_history = data.get('chatHistory', [])
    user_message = data.get('userMessage', '')
    
    print(f"[design_refine] Received: design_data={bool(design_data)}, userMessage='{user_message[:50] if user_message else 'None'}...'")
    
    if not design_data:
        raise HTTPException(status_code=400, detail="Missing design data")
    if not user_message:
        raise HTTPException(status_code=400, detail="Missing user message")
    
    config = load_config()
    config.llm.streaming_enabled = True
    
    async def event_generator():
        try:
            llm_client = create_llm_client(config)
            
            # Build conversation context
            conversation = []
            for msg in chat_history:
                if msg['role'] != 'system':
                    conversation.append(f"{msg['role'].upper()}: {msg['content']}")
            conversation.append(f"USER: {user_message}")
            
            # Build prompt with design context
            design_summary = f"""
Project: {project_name}
Requirements: {requirements}

Current Design:
- Objectives: {', '.join(design_data.get('objectives', []))}
- Tech Stack: {', '.join(design_data.get('tech_stack', []))}
- Dependencies: {', '.join(design_data.get('dependencies', []))}
"""
            
            prompt = f"""You are helping refine a project design through conversation. 

{design_summary}

Chat History:
{chr(10).join(conversation)}

Provide helpful, concise responses to guide the user toward a better design. Focus on:
- Identifying potential issues
- Suggesting improvements
- Clarifying technical approaches
- Ensuring requirements are met

Respond conversationally and constructively."""
            
            queue: asyncio.Queue = asyncio.Queue()
            
            class StreamHandler:
                async def on_token_async(self, token: str):
                    await queue.put({'content': token})
                async def on_completion_async(self, full_response: str):
                    await queue.put({'done': True})
                async def __aenter__(self):
                    return self
                async def __aexit__(self, exc_type, exc, tb):
                    return False
            
            handler = StreamHandler()
            
            async def run_chat():
                try:
                    await llm_client.generate_completion_streaming(
                        prompt,
                        callback=lambda token: asyncio.create_task(handler.on_token_async(token)),
                        streaming_handler=handler
                    )
                finally:
                    # Always signal completion after streaming finishes
                    await queue.put({'done': True})
            
            task = asyncio.create_task(run_chat())
            
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=120.0)
                except asyncio.TimeoutError:
                    print("[design_refine] Queue timeout - forcing completion")
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    break
                if item.get('content'):
                    yield f"data: {json.dumps({'content': item['content']})}\n\n"
                elif item.get('done'):
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    break
                    
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"Error in design refinement: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type='text/event-stream', headers=SSE_HEADERS)


@app.post("/api/design/review")
async def design_automated_review(request: Request):
    """Run automated design review using design_review pipeline."""
    _validate_incoming_request(request.headers.get('x-streaming-proxy-key'))
    data = await request.json()
    design_data = data.get('design')
    project_name = data.get('projectName', '')
    
    print(f"[design_review] Received request for project: {project_name}")
    print(f"[design_review] Design data keys: {list(design_data.keys()) if design_data else 'None'}")
    
    if not design_data:
        raise HTTPException(status_code=400, detail="Missing design")
    
    try:
        design = ProjectDesign(**design_data)
        print(f"[design_review] Successfully parsed design with {len(design.objectives)} objectives")
    except Exception as e:
        print(f"[design_review] Failed to parse design: {e}")
        print(f"[design_review] Design data: {json.dumps(design_data, indent=2)[:500]}")
        raise HTTPException(status_code=400, detail=f"Invalid design: {e}")
    
    config = load_config()
    config.llm.streaming_enabled = True
    
    async def event_generator():
        try:
            from src.pipeline.design_review import DesignReviewRefiner
            
            llm_client = create_llm_client(config)
            reviewer = DesignReviewRefiner(llm_client)
            
            # Run review (returns updated design + report)
            updated_design, report, changed = await reviewer.refine(design)
            
            # Stream the report as response
            for char in report:
                yield f"data: {json.dumps({'content': char})}\n\n"
                await asyncio.sleep(0.001)  # Small delay for readability
            
            yield f"data: {json.dumps({'done': True, 'changed': changed})}\n\n"
            
        except Exception as e:
            print(f"Error in automated review: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type='text/event-stream', headers=SSE_HEADERS)


@app.post("/api/plan/refine")
async def plan_refine(request: Request):
    """Interactive plan refinement via chat interface.
    
    Takes plan + design + chat history and streams conversational responses
    to help users iterate on phases before execution.
    """
    _validate_incoming_request(request.headers.get('x-streaming-proxy-key'))
    data = await request.json()
    plan_data = data.get('plan')
    design_data = data.get('design')
    project_name = data.get('projectName', '')
    chat_history = data.get('chatHistory', [])
    user_message = data.get('userMessage', '')
    
    if not plan_data or not user_message:
        raise HTTPException(status_code=400, detail="Missing plan or user message")
    
    config = load_config()
    config.llm.streaming_enabled = True
    
    async def event_generator():
        try:
            llm_client = create_llm_client(config)
            
            # Build conversation context
            conversation = []
            for msg in chat_history:
                if msg['role'] != 'system':
                    conversation.append(f"{msg['role'].upper()}: {msg['content']}")
            conversation.append(f"USER: {user_message}")
            
            # Build prompt with plan context
            phases = plan_data.get('phases', [])
            phase_summary = '\n'.join([
                f"Phase {p.get('number', i+1)}: {p.get('title', 'Untitled')}"
                for i, p in enumerate(phases)
            ])
            
            plan_context = f"""
Project: {project_name}

Current Development Plan ({len(phases)} phases):
{phase_summary}
"""
            
            prompt = f"""You are helping refine a development plan through conversation.

{plan_context}

Chat History:
{chr(10).join(conversation)}

Provide helpful, concise responses to guide the user toward a better plan. Focus on:
- Phase ordering and dependencies
- Coverage of all design requirements
- Appropriate scope and granularity
- Missing or redundant phases

Respond conversationally and constructively."""
            
            queue: asyncio.Queue = asyncio.Queue()
            
            class StreamHandler:
                async def on_token_async(self, token: str):
                    await queue.put({'content': token})
                async def on_completion_async(self, full_response: str):
                    await queue.put({'done': True})
                async def __aenter__(self):
                    return self
                async def __aexit__(self, exc_type, exc, tb):
                    return False
            
            handler = StreamHandler()
            
            async def run_chat():
                try:
                    await llm_client.generate_completion_streaming(
                        prompt,
                        callback=lambda token: asyncio.create_task(handler.on_token_async(token)),
                        streaming_handler=handler
                    )
                finally:
                    # Always signal completion after streaming finishes
                    await queue.put({'done': True})
            
            task = asyncio.create_task(run_chat())
            
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=120.0)
                except asyncio.TimeoutError:
                    print("[plan_refine] Queue timeout - forcing completion")
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    break
                if item.get('content'):
                    yield f"data: {json.dumps({'content': item['content']})}\n\n"
                elif item.get('done'):
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    break
                    
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"Error in plan refinement: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type='text/event-stream', headers=SSE_HEADERS)


@app.post("/api/plan/apply-refinements")
async def plan_apply_refinements(request: Request):
    """Apply refinements from conversation to the plan.
    
    Analyzes the chat history to extract agreed-upon changes and produces
    an updated plan with those modifications applied.
    """
    _validate_incoming_request(request.headers.get('x-streaming-proxy-key'))
    data = await request.json()
    plan_data = data.get('plan')
    design_data = data.get('design')
    project_name = data.get('projectName', '')
    chat_history = data.get('chatHistory', [])
    
    if not plan_data:
        raise HTTPException(status_code=400, detail="Missing plan data")
    
    config = load_config()
    config.llm.streaming_enabled = True
    
    async def event_generator():
        try:
            llm_client = create_llm_client(config)
            
            # Build conversation summary for context
            conversation_text = []
            for msg in chat_history:
                if msg['role'] != 'system':
                    conversation_text.append(f"{msg['role'].upper()}: {msg['content']}")
            
            # Build current plan JSON
            phases = plan_data.get('phases', [])
            phases_json = json.dumps(phases, indent=2)
            
            prompt = f"""You are a development plan editor. Based on the conversation below, you must produce an UPDATED version of the development plan that incorporates any changes discussed.

PROJECT: {project_name}

CURRENT PLAN PHASES (JSON):
```json
{phases_json}
```

REFINEMENT CONVERSATION:
{chr(10).join(conversation_text)}

INSTRUCTIONS:
1. Analyze the conversation to identify any agreed-upon changes to the plan
2. Apply those changes to produce an updated plan
3. If no changes were discussed or agreed upon, return the original plan unchanged
4. Output ONLY valid JSON - no explanation, no markdown fences, just the JSON array of phases

Changes to look for:
- Phase reordering
- New phases to add
- Phases to remove or merge
- Title or description updates
- Scope adjustments
- Dependency clarifications

OUTPUT FORMAT - Return a JSON object with this exact structure:
{{"phases": [...], "changes_applied": ["description of change 1", "description of change 2"]}}

If no changes: {{"phases": [...original phases...], "changes_applied": []}}

OUTPUT ONLY THE JSON:"""

            queue: asyncio.Queue = asyncio.Queue()
            full_response = ""
            
            class StreamHandler:
                async def on_token_async(self, token: str):
                    nonlocal full_response
                    full_response += token
                    await queue.put({'content': token})
                async def on_completion_async(self, _: str):
                    await queue.put({'done': True})
                async def __aenter__(self):
                    return self
                async def __aexit__(self, exc_type, exc, tb):
                    return False
            
            handler = StreamHandler()
            
            async def run_extraction():
                try:
                    await llm_client.generate_completion_streaming(
                        prompt,
                        callback=lambda token: asyncio.create_task(handler.on_token_async(token)),
                        streaming_handler=handler
                    )
                finally:
                    await queue.put({'done': True})
            
            task = asyncio.create_task(run_extraction())
            
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=120.0)
                except asyncio.TimeoutError:
                    print("[plan_apply] Queue timeout")
                    break
                    
                if item.get('content'):
                    yield f"data: {json.dumps({'content': item['content']})}\n\n"
                elif item.get('done'):
                    # Parse the LLM response to extract the updated plan
                    try:
                        # Clean up potential markdown fences
                        clean_response = full_response.strip()
                        if clean_response.startswith('```'):
                            lines = clean_response.split('\n')
                            clean_response = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
                        
                        result = json.loads(clean_response)
                        updated_phases = result.get('phases', phases)
                        changes = result.get('changes_applied', [])
                        
                        # Build updated plan
                        updated_plan = {**plan_data, 'phases': updated_phases}
                        
                        yield f"data: {json.dumps({'done': True, 'updatedPlan': updated_plan, 'changesApplied': changes})}\n\n"
                    except json.JSONDecodeError as e:
                        print(f"[plan_apply] Failed to parse LLM response: {e}")
                        print(f"[plan_apply] Response was: {full_response[:500]}")
                        # Return original plan on parse failure
                        yield f"data: {json.dumps({'done': True, 'updatedPlan': plan_data, 'changesApplied': [], 'parseError': str(e)})}\n\n"
                    break
                    
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"Error applying refinements: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type='text/event-stream', headers=SSE_HEADERS)


@app.post("/api/plan/review")
async def plan_automated_review(request: Request):
    """Run automated plan review to identify issues before execution."""
    _validate_incoming_request(request.headers.get('x-streaming-proxy-key'))
    data = await request.json()
    plan_data = data.get('plan')
    design_data = data.get('design')
    project_name = data.get('projectName', '')
    
    if not plan_data:
        raise HTTPException(status_code=400, detail="Missing plan")
    
    config = load_config()
    config.llm.streaming_enabled = True
    
    async def event_generator():
        try:
            llm_client = create_llm_client(config)
            
            # Build review prompt
            phases = plan_data.get('phases', [])
            phase_list = '\n'.join([
                f"Phase {p.get('number', i+1)}: {p.get('title', 'Untitled')}\n  {p.get('description', '')[:100]}..."
                for i, p in enumerate(phases)
            ])
            
            design_summary = ""
            if design_data:
                design_summary = f"""
Design Context:
- Objectives: {', '.join(design_data.get('objectives', [])[:3])}
- Tech Stack: {', '.join(design_data.get('tech_stack', []))}
"""
            
            prompt = f"""Review this development plan for potential issues:

Project: {project_name}
{design_summary}

Development Plan ({len(phases)} phases):
{phase_list}

Analyze the plan and provide:
1. Any missing phases or functionality gaps
2. Phase ordering issues or dependency problems
3. Overly broad or narrow phases
4. Misalignment with design requirements
5. Overall assessment and recommendations

Format as a clear, structured review."""
            
            response = await llm_client.generate_completion(prompt)
            
            # Stream the response character by character
            for char in response:
                yield f"data: {json.dumps({'content': char})}\n\n"
                await asyncio.sleep(0.001)
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            print(f"Error in plan review: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type='text/event-stream', headers=SSE_HEADERS)


# =============================================================================
# Adaptive Pipeline Endpoints
# =============================================================================


def _create_llm_client_for_adaptive(model_config: dict = None):
    """Create LLM client configured for adaptive pipeline.
    
    Uses requesty provider with gpt-5-nano by default for testing.
    """
    config = load_config()
    # Override with requesty/gpt-5-nano for adaptive pipeline
    config.llm.provider = "requesty"
    config.llm.model = "openai/gpt-4.1-nano"  # Use gpt-4.1-nano as gpt-5-nano doesn't exist yet
    
    # Allow override from request
    if model_config:
        if model_config.get("provider"):
            config.llm.provider = model_config["provider"]
        if model_config.get("model"):
            config.llm.model = model_config["model"]
        if model_config.get("temperature") is not None:
            config.llm.temperature = float(model_config["temperature"])
    
    return create_llm_client(config)


@app.post("/api/adaptive/complexity")
async def complexity_analysis(request: Request):
    """
    Analyze project complexity from interview data using LLM.
    Returns SSE stream with complexity profile.
    
    Input:
    {
        "interview_data": {
            "project_type": "...",
            "requirements": "...",
            "team_size": "...",
            "apis": [...],
            "frameworks": "..."
        },
        "use_llm": true,  // Optional, defaults to true
        "model_config": {...}  // Optional model overrides
    }
    """
    data = await request.json()
    interview_data = data.get('interview_data', {})
    use_llm = data.get('use_llm', True)
    model_config = data.get('model_config', {})

    async def event_generator():
        try:
            # Send start event
            yield f"data: {json.dumps({'type': 'analyzing', 'message': 'Starting complexity analysis...'})}\n\n"

            if use_llm:
                yield f"data: {json.dumps({'type': 'progress', 'message': 'Using LLM for intelligent complexity analysis...'})}\n\n"
                
                # Create LLM client and analyzer
                llm_client = _create_llm_client_for_adaptive(model_config)
                analyzer = LLMComplexityAnalyzer(llm_client)
                
                # Run LLM-powered analysis
                profile = await analyzer.analyze_with_llm(interview_data)
                
                # Prepare result with LLM-specific fields
                # Convert ScoringRationale dataclass to dict for JSON serialization
                rationale_dict = {
                    "score_justification": profile.scoring_rationale.score_justification,
                    "phase_count_justification": profile.scoring_rationale.phase_count_justification,
                    "depth_justification": profile.scoring_rationale.depth_justification,
                    "key_complexity_drivers": profile.scoring_rationale.key_complexity_drivers,
                    "comparison_anchor": profile.scoring_rationale.comparison_anchor,
                }
                result = {
                    "complexity_score": profile.complexity_score,
                    "estimated_phase_count": profile.estimated_phase_count,
                    "depth_level": profile.depth_level,
                    "confidence": profile.confidence,
                    "scoring_rationale": rationale_dict,
                    "complexity_factors": dict(profile.complexity_factors),
                    "follow_up_questions": profile.follow_up_questions,
                    "hidden_risks": profile.hidden_risks,
                    "llm_powered": True,
                }
            else:
                # Fallback to static analysis
                analyzer = ComplexityAnalyzer()
                profile = analyzer.analyze(interview_data)

                yield f"data: {json.dumps({'type': 'progress', 'message': f'Computed score: {profile.score:.1f}, depth: {profile.depth_level}'})}\n\n"

                result = {
                    "project_type_bucket": profile.project_type_bucket,
                    "technical_complexity_bucket": profile.technical_complexity_bucket,
                    "integration_bucket": profile.integration_bucket,
                    "team_size_bucket": profile.team_size_bucket,
                    "complexity_score": profile.score,
                    "estimated_phase_count": profile.estimated_phase_count,
                    "depth_level": profile.depth_level,
                    "confidence": profile.confidence,
                    "llm_powered": False,
                }

                # Check if follow-up questions are needed (low confidence)
                if profile.confidence < 0.7:
                    result["follow_up_questions"] = _generate_follow_up_questions(profile, interview_data)

            result["needs_clarification"] = len(result.get("follow_up_questions", [])) > 0

            # Send final result
            yield f"data: {json.dumps({'type': 'result', 'profile': result})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'success': True})}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type='text/event-stream', headers=SSE_HEADERS)


def _generate_follow_up_questions(profile: ComplexityProfile, interview_data: dict) -> list:
    """Generate follow-up questions based on low-confidence areas."""
    questions = []

    if not interview_data.get('team_size'):
        questions.append("What is the expected team size for this project?")

    if not interview_data.get('apis') and profile.score > 5:
        questions.append("Will this project integrate with any external APIs or services?")

    if profile.technical_complexity_bucket == "simple_crud" and profile.score > 7:
        questions.append("Are there any advanced features like real-time updates, ML, or multi-region deployment?")

    if not interview_data.get('frameworks'):
        questions.append("What frameworks or libraries do you plan to use?")

    return questions[:3]


@app.post("/api/adaptive/validate")
async def design_validation(request: Request):
    """
    Validate a design document against complexity profile using LLM.
    Returns SSE stream with validation report.
    
    Input:
    {
        "design_content": "...",
        "complexity_profile": {...},
        "use_llm": true,  // Optional, defaults to true
        "model_config": {...}  // Optional model overrides
    }
    """
    data = await request.json()
    design_content = data.get('design_content', '')
    profile_data = data.get('complexity_profile') or {}
    use_llm = data.get('use_llm', True)
    model_config = data.get('model_config', {})

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'validating', 'message': 'Starting design validation...'})}\n\n"

            # Build complexity profile from data
            profile = ComplexityProfile(
                project_type_bucket=profile_data.get('project_type_bucket', 'web_app'),
                technical_complexity_bucket=profile_data.get('technical_complexity_bucket', 'simple_crud'),
                integration_bucket=profile_data.get('integration_bucket', 'standalone'),
                team_size_bucket=profile_data.get('team_size_bucket', 'solo'),
                score=profile_data.get('score', profile_data.get('complexity_score', 5.0)),
                estimated_phase_count=profile_data.get('estimated_phase_count', 5),
                depth_level=profile_data.get('depth_level', 'standard'),
                confidence=profile_data.get('confidence', 0.8)
            )

            # Run rule-based validation first
            validator = DesignValidator()
            report = validator.validate(design_content, complexity_profile=profile)

            # Send individual check results
            for check_name, passed in report.checks.items():
                yield f"data: {json.dumps({'type': 'check', 'check': check_name, 'passed': passed})}\n\n"

            # Build issues list
            issues = [
                {
                    "code": issue.code,
                    "message": issue.message,
                    "auto_correctable": issue.auto_correctable
                }
                for issue in report.issues
            ]

            result = {
                "is_valid": report.is_valid,
                "auto_correctable": report.auto_correctable,
                "checks": report.checks,
                "issues": issues
            }

            # Run LLM sanity review if enabled
            if use_llm:
                yield f"data: {json.dumps({'type': 'progress', 'message': 'Running LLM sanity review...'})}\n\n"
                try:
                    llm_client = _create_llm_client_for_adaptive(model_config)
                    llm_reviewer = LLMSanityReviewerWithLLM(llm_client)
                    review_result = await llm_reviewer.review_with_llm(design_content, report)
                    
                    result["review"] = {
                        "confidence": review_result.confidence,
                        "overall_assessment": review_result.overall_assessment,
                        "coherence_score": review_result.coherence_score,
                        "coherence_notes": review_result.coherence_notes,
                        "hallucination_passed": review_result.hallucination_passed,
                        "hallucination_issues": [
                            {"type": h.type, "text": h.text, "note": h.note}
                            for h in review_result.hallucination_issues
                        ],
                        "scope_alignment": {
                            "score": review_result.scope_alignment.score,
                            "missing_requirements": review_result.scope_alignment.missing_requirements,
                            "over_engineered": review_result.scope_alignment.over_engineered,
                            "under_engineered": review_result.scope_alignment.under_engineered,
                        } if review_result.scope_alignment else None,
                        "risks": [
                            {"severity": r.severity, "category": r.category, "description": r.description, "mitigation": r.mitigation}
                            for r in review_result.risks
                        ],
                        "suggestions": review_result.suggestions,
                        "summary": review_result.summary,
                        "llm_powered": True,
                    }
                except Exception as review_error:
                    print(f"LLM review failed: {review_error}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to simple review
                    simple_reviewer = LLMSanityReviewer()
                    simple_result = simple_reviewer.review(design_content, report)
                    result["review"] = {
                        "confidence": simple_result.confidence,
                        "risks": simple_result.risks,
                        "notes": simple_result.notes,
                        "llm_powered": False,
                    }
            else:
                # Use simple reviewer
                simple_reviewer = LLMSanityReviewer()
                simple_result = simple_reviewer.review(design_content, report)
                result["review"] = {
                    "confidence": simple_result.confidence,
                    "risks": simple_result.risks,
                    "notes": simple_result.notes,
                    "llm_powered": False,
                }

            yield f"data: {json.dumps({'type': 'result', **result})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'success': True})}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type='text/event-stream', headers=SSE_HEADERS)


@app.post("/api/adaptive/correct")
async def design_correction(request: Request):
    """
    Run the design correction loop using LLM.
    Returns SSE stream with corrected design.
    
    Input:
    {
        "design_content": "...",
        "max_iterations": 3,
        "complexity_profile": {...},  // Optional
        "use_llm": true,  // Optional, defaults to true
        "model_config": {...}  // Optional model overrides
    }
    """
    data = await request.json()
    design_content = data.get('design_content', '')
    max_iterations = data.get('max_iterations', 3)
    profile_data = data.get('complexity_profile') or {}
    use_llm = data.get('use_llm', True)
    model_config = data.get('model_config') or {}

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'correcting', 'message': 'Starting design correction loop...', 'max_iterations': max_iterations})}\n\n"

            # Build complexity profile if provided
            complexity_profile = None
            if profile_data:
                complexity_profile = ComplexityProfile(
                    project_type_bucket=profile_data.get('project_type_bucket', 'web_app'),
                    technical_complexity_bucket=profile_data.get('technical_complexity_bucket', 'simple_crud'),
                    integration_bucket=profile_data.get('integration_bucket', 'standalone'),
                    team_size_bucket=profile_data.get('team_size_bucket', 'solo'),
                    score=profile_data.get('score', profile_data.get('complexity_score', 5.0)),
                    estimated_phase_count=profile_data.get('estimated_phase_count', 5),
                    depth_level=profile_data.get('depth_level', 'standard'),
                    confidence=profile_data.get('confidence', 0.8)
                )

            if use_llm:
                yield f"data: {json.dumps({'type': 'progress', 'message': 'Using LLM for intelligent corrections...'})}\n\n"
                
                llm_client = _create_llm_client_for_adaptive(model_config)
                correction_loop = LLMDesignCorrectionLoop(llm_client)
                result = await correction_loop.run_with_llm(
                    design_content, 
                    complexity_profile=complexity_profile,
                    max_iterations=max_iterations
                )
            else:
                # Use simple correction loop
                correction_loop = DesignCorrectionLoop()
                result = correction_loop.run(design_content, complexity_profile=complexity_profile)

            # Build changes history
            changes_made = [
                {
                    "issue_code": change.issue_code,
                    "action": change.action,
                    "before": change.before,
                    "after": change.after,
                    "explanation": change.explanation,
                    "location": change.location,
                }
                for change in result.changes_made
            ]

            yield f"data: {json.dumps({
                'type': 'result', 
                'final_design': result.design_text, 
                'iterations': result.iterations_used,
                'max_iterations_reached': result.max_iterations_reached,
                'requires_human_review': result.requires_human_review,
                'is_valid': result.validation.is_valid,
                'changes_made': changes_made,
                'llm_powered': use_llm,
            })}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'success': True})}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type='text/event-stream', headers=SSE_HEADERS)


@app.get("/api/adaptive/profile")
async def get_complexity_profile(request: Request):
    """
    Synchronous endpoint to get complexity profile (non-streaming).
    Useful for quick lookups or when SSE is not needed.
    
    Query params: project_type, requirements, team_size, apis, frameworks
    """
    params = dict(request.query_params)
    
    interview_data = {
        "project_type": params.get("project_type", ""),
        "requirements": params.get("requirements", ""),
        "team_size": params.get("team_size", ""),
        "apis": params.get("apis", "").split(",") if params.get("apis") else [],
        "frameworks": params.get("frameworks", ""),
    }

    try:
        analyzer = ComplexityAnalyzer()
        profile = analyzer.analyze(interview_data)

        result = {
            "project_type_bucket": profile.project_type_bucket,
            "technical_complexity_bucket": profile.technical_complexity_bucket,
            "integration_bucket": profile.integration_bucket,
            "team_size_bucket": profile.team_size_bucket,
            "score": profile.score,
            "estimated_phase_count": profile.estimated_phase_count,
            "depth_level": profile.depth_level,
            "confidence": profile.confidence
        }

        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
