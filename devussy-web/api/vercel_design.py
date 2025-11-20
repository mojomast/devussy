import os
import json
import asyncio
from typing import Any

try:
    # Vercel's runtime provides a `VercelRequest`/`VercelResponse`, but in runtime
    # the `vercel` import may not be available at static analysis time. We'll
    # rely on returning a raw tuple or json string fallback for portability.
    from vercel import VercelResponse  # type: ignore
except Exception:
    VercelResponse = None  # type: ignore

from src.config import load_config
from src.clients.factory import create_llm_client
from src.pipeline.project_design import ProjectDesignGenerator


async def _generate_design_async(data: dict[str, Any]) -> dict:
    """Async logic for generating a design. Extracted so it can be awaited
    from both sync and async handlers."""
    project_name = data.get("projectName") or data.get("project_name") or "Unnamed"
    languages = data.get("languages", [])
    requirements = data.get("requirements") or data.get("description", "")
    model_config = data.get("modelConfig", {}) or {}

    # Load app config and apply overrides
    config = load_config()
    # Prefer stage/override keys from provided JSON, else fallback to env
    if model_config.get("model"):
        config.llm.model = model_config.get("model")
    if model_config.get("temperature") is not None:
        config.llm.temperature = float(model_config.get("temperature"))
    if model_config.get("reasoning_effort"):
        config.llm.reasoning_effort = model_config.get("reasoning_effort")

    # If there is no API key in config, read from environment (REQUESTY_API_KEY)
    incoming_api_key = (
        getattr(config.llm, "api_key", None)
        or os.environ.get("REQUESTY_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("GENERIC_API_KEY")
    )
    if incoming_api_key:
        config.llm.api_key = incoming_api_key
    else:
        # If there is no API key, return an explicit error rather than attempting to call the LLM.
        payload = {
            "ok": False,
            "error": "No LLM API key configured. Please add REQUESTY_API_KEY as a Vercel environment variable or configure the appropriate key in config.yml/.env.",
        }
        body = json.dumps(payload, default=str)
        if VercelResponse:
            return VercelResponse(body, status=400, headers={"Content-Type": "application/json"})
        return {"statusCode": 400, "headers": {"Content-Type": "application/json"}, "body": body}

    # Force provider to requesty by default for this endpoint (as present in codebase)
    config.llm.provider = "requesty"
    config.llm.streaming_enabled = False

    llm_client = create_llm_client(config)
    gen = ProjectDesignGenerator(llm_client)

    # `generate` is async; call it
    design_model = await gen.generate(project_name=project_name, languages=languages, requirements=requirements)
    # ProjectDesign uses pydantic; return serializable data
    return design_model.model_dump()


def handler(request):
    """Vercel entrypoint for the design API. Accepts JSON body and returns
    a JSON response. If the `vercel` package is installed, return
    VercelResponse for best compatibility."""
    try:
        # Attempt to read JSON body generically
        if hasattr(request, "json"):
            data = request.json()
        elif hasattr(request, "get_json"):
            data = request.get_json()
        else:
            body = getattr(request, "body", None)
            if body is None:
                try:
                    body = request.get_data()
                except Exception:
                    body = b""
            if isinstance(body, (bytes, bytearray)):
                try:
                    data = json.loads(body.decode("utf-8"))
                except Exception:
                    data = {}
            elif isinstance(body, str):
                try:
                    data = json.loads(body)
                except Exception:
                    data = {}
            else:
                data = {}

    except Exception:
        data = {}

    # Run the generation on a new event loop and await the async call
    try:
        design = asyncio.new_event_loop()
        asyncio.set_event_loop(design)
        result = design.run_until_complete(_generate_design_async(data))
    finally:
        try:
            design.close()
        except Exception:
            pass

    payload = {"ok": True, "design": result}
    body = json.dumps(payload, default=str)

    # Return using VercelResponse if available; else return a lambda-style dict body
    if VercelResponse:
        return VercelResponse(body, status=200, headers={"Content-Type": "application/json"})
    else:
        # Vercel can accept a tuple (status_code, headers, body) or a dict; choose dict to be safe
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": body,
        }
