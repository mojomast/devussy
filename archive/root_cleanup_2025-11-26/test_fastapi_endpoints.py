#!/usr/bin/env python3
"""
Quick test script to verify FastAPI adaptive endpoints work.

This tests the SSE streaming endpoints directly via HTTP.
"""

import asyncio
import json
import aiohttp


BASE_URL = "http://127.0.0.1:8001"


async def test_complexity_endpoint():
    """Test /api/adaptive/complexity endpoint."""
    print("\n" + "="*60)
    print("TEST: /api/adaptive/complexity (SSE)")
    print("="*60)
    
    payload = {
        "interview_data": {
            "project_type": "Web API",
            "requirements": "REST API with authentication and database",
            "team_size": "3",
            "apis": ["Stripe"],
            "frameworks": "FastAPI",
        },
        "use_llm": True,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/api/adaptive/complexity",
            json=payload,
        ) as response:
            print(f"Status: {response.status}")
            async for line in response.content:
                line = line.decode().strip()
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    print(f"  Event: {data.get('type')}")
                    if data.get('type') == 'result':
                        profile = data.get('profile', {})
                        print(f"    Score: {profile.get('complexity_score')}")
                        print(f"    Depth: {profile.get('depth_level')}")
                        print(f"    LLM: {profile.get('llm_powered')}")
                    if data.get('type') == 'done':
                        print("  ✅ PASSED")
                        return True
    return False


async def test_validation_endpoint():
    """Test /api/adaptive/validate endpoint."""
    print("\n" + "="*60)
    print("TEST: /api/adaptive/validate (SSE)")
    print("="*60)
    
    payload = {
        "design_content": """
# Project Design: Task API

## Tech Stack
- Python
- FastAPI  
- PostgreSQL

## Architecture
REST API with JWT auth.
""",
        "complexity_profile": {
            "project_type_bucket": "api",
            "technical_complexity_bucket": "auth_db",
            "integration_bucket": "standalone",
            "team_size_bucket": "2_3",
            "complexity_score": 6.0,
            "estimated_phase_count": 5,
            "depth_level": "standard",
            "confidence": 0.8,
        },
        "use_llm": True,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/api/adaptive/validate",
            json=payload,
        ) as response:
            print(f"Status: {response.status}")
            async for line in response.content:
                line = line.decode().strip()
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    print(f"  Event: {data.get('type')}")
                    if data.get('type') == 'result':
                        print(f"    Valid: {data.get('is_valid')}")
                        review = data.get('review', {})
                        print(f"    Review Confidence: {review.get('confidence')}")
                        print(f"    LLM: {review.get('llm_powered')}")
                    if data.get('type') == 'done':
                        print("  ✅ PASSED")
                        return True
    return False


async def test_correction_endpoint():
    """Test /api/adaptive/correct endpoint."""
    print("\n" + "="*60)
    print("TEST: /api/adaptive/correct (SSE)")
    print("="*60)
    
    payload = {
        "design_content": """
# Simple App Design

Just a basic app.
""",
        "max_iterations": 2,
        "use_llm": True,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/api/adaptive/correct",
            json=payload,
        ) as response:
            print(f"Status: {response.status}")
            async for line in response.content:
                line = line.decode().strip()
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    print(f"  Event: {data.get('type')}")
                    if data.get('type') == 'result':
                        print(f"    Iterations: {data.get('iterations')}")
                        print(f"    Valid: {data.get('is_valid')}")
                        print(f"    Changes: {len(data.get('changes_made', []))}")
                        print(f"    LLM: {data.get('llm_powered')}")
                    if data.get('type') == 'done':
                        print("  ✅ PASSED")
                        return True
    return False


async def main():
    print("="*60)
    print("FASTAPI ADAPTIVE ENDPOINT TESTS")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    
    results = []
    
    try:
        results.append(("Complexity", await test_complexity_endpoint()))
        results.append(("Validation", await test_validation_endpoint()))
        results.append(("Correction", await test_correction_endpoint()))
    except aiohttp.ClientConnectorError:
        print("\n❌ ERROR: Cannot connect to server!")
        print("   Make sure the server is running:")
        print("   cd devussy-web/streaming_server && uvicorn app:app --port 8000")
        return
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(1 for _, r in results if r)
    for name, result in results:
        print(f"  {name}: {'✅' if result else '❌'}")
    print(f"\nTotal: {passed}/{len(results)} passed")


if __name__ == "__main__":
    asyncio.run(main())
