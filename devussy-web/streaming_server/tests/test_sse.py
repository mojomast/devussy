import asyncio
import json
import os

import pytest
from httpx import AsyncClient

from streaming_server.app import app


@pytest.mark.asyncio
async def test_streaming_endpoint(monkeypatch):
    # Mock the generator to yield tokens without calling external services
    async def fake_generate(self, project_name, languages, requirements, streaming_handler=None):
        # Simulate stream tokens
        async with streaming_handler:
            await streaming_handler.on_token_async("Hello")
            await streaming_handler.on_token_async(" ")
            await streaming_handler.on_token_async("World")
            await streaming_handler.on_completion_async("Hello World")
        return "Hello World"

    monkeypatch.setattr("src.pipeline.project_design.ProjectDesignGenerator.generate", fake_generate)

    # Ensure secret is set for request
    os.environ["STREAMING_SECRET"] = "testsecret"

    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"X-Streaming-Proxy-Key": "testsecret"}
        resp = await client.post(
            "/api/design/stream",
            json={"projectName": "test-project", "languages": ["Python"], "requirements": "test"},
            headers=headers,
            timeout=10,
        )

        # Response is an event stream; we get plain text with data: ... lines
        text = resp.text
        assert "Hello" in text
        assert "World" in text
        assert resp.status_code == 200
