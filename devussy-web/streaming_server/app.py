"""FastAPI streaming server wrapper using existing generator pipeline.

This file is a skeleton for a FastAPI app that accepts a POST to `/api/design/stream`
and streams events using Server-Sent Events (SSE). It uses the existing
`ProjectDesignGenerator` from `src.pipeline.project_design`. This file is a
starting point and will need additional validation and tests.
"""

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import StreamingResponse
import json
import os
import asyncio

from src.config import load_config
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
