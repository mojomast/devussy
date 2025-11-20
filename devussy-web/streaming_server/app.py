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
