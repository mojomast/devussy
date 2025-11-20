"""FastAPI streaming server wrapper using existing generator pipeline.

This file is a skeleton for a FastAPI app that accepts a POST to `/api/design/stream`
and streams events using Server-Sent Events (SSE). It uses the existing
`ProjectDesignGenerator` from `src.pipeline.project_design`. This file is a
starting point and will need additional validation and tests.
"""

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import json
import os
import asyncio

from src.config import load_config
from src.clients.factory import create_llm_client
from src.pipeline.project_design import ProjectDesignGenerator
from src.pipeline.basic_devplan import BasicDevPlanGenerator
from src.pipeline.detailed_devplan import DetailedDevPlanGenerator
from src.pipeline.handoff_prompt import HandoffPromptGenerator
from src.models import ProjectDesign, DevPlan
import os
import glob
import time
from pathlib import Path
import aiohttp
from src.clients.factory import create_llm_client
from src.pipeline.project_design import ProjectDesignGenerator

app = FastAPI()

STREAMING_SECRET = os.environ.get("STREAMING_SECRET")


def _validate_incoming_request(x_streaming_proxy_key: str | None) -> None:
    if STREAMING_SECRET and x_streaming_proxy_key != STREAMING_SECRET:
        raise HTTPException(status_code=403, detail="Invalid streaming proxy key")


@app.post("/api/design/stream")
async def design_stream(request: Request, x_streaming_proxy_key: str | None = Header(None)):
    """Stream an LLM response using SSE. Input is identical to the synchronous call.
    Expects a JSON body with projectName, languages, and requirements (like the existing API).
    """
    _validate_incoming_request(x_streaming_proxy_key)

    body = await request.json()
    project_name = body.get("projectName") or body.get("project_name") or "Unnamed"
    languages = body.get("languages", [])
    requirements = body.get("requirements") or body.get("description", "")

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
                    await generator.generate(
                        project_name=project_name,
                        languages=languages,
                        requirements=requirements,
                        streaming_handler=streaming_handler,
                    )
                finally:
                    # Ensure the queue gets termination signal if generator finishes with no completion handler
                    await queue.put(None)

            generation_task = asyncio.create_task(run_generation())

            # Yield tokens as SSE
            while True:
                token = await queue.get()
                if token is None:
                    break
                yield f"data: {json.dumps({'content': token})}\n\n"

        except asyncio.CancelledError:
            # client disconnected
            return

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/design")
async def design_stream_alias(request: Request, x_streaming_proxy_key: str | None = Header(None)):
    """Alias for `/api/design/stream` kept for backwards compatibility with the frontend which hits `/api/design` for SSE streaming."""
    return await design_stream(request, x_streaming_proxy_key)


@app.post("/api/interview")
async def interview_endpoint(request: Request):
    data = await request.json()
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
        manager = LLMInterviewManager(config, verbose=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize interview manager: {e}")

    if history:
        try:
            manager.conversation_history.extend(history)
        except Exception:
            pass

    loop = asyncio.get_running_loop()
    try:
        response_text = await loop.run_in_executor(None, manager._send_to_llm, user_input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    extracted = manager._extract_structured_data(response_text)
    is_complete = manager._validate_extracted_data(extracted) if extracted else False
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
        handoff = await loop.run_in_executor(None, generator.generate, plan, design.project_name, design.architecture_overview or "", str(design.tech_stack) if design.tech_stack else "")
        return JSONResponse(status_code=200, content=handoff.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/plan/basic")
async def plan_basic(request: Request):
    data = await request.json()
    design_data = data.get('design')
    if not design_data:
        raise HTTPException(status_code=400, detail="Missing design data")

    try:
        design = ProjectDesign(**design_data)
    except Exception as e:
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

    return StreamingResponse(event_generator(), media_type='text/event-stream')


@app.post("/api/plan/detail")
async def plan_detail(request: Request):
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

    async def event_generator():
        llm_client = create_llm_client(config)
        generator = DetailedDevPlanGenerator(llm_client)
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

    return StreamingResponse(event_generator(), media_type='text/event-stream')



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
