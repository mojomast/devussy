from http.server import BaseHTTPRequestHandler
import json
import asyncio
import os
import aiohttp
from .utils import setup_path

# Add project root to sys.path
setup_path()

from src.config import load_config

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Load config to get API key
        config = load_config()
        # Try to get key from config or env
        api_key = getattr(config.llm, "api_key", None) or os.getenv("REQUESTY_API_KEY")
        
        if not api_key:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Requesty API key not configured"}).encode('utf-8'))
            return

        base_url = getattr(config.llm, "base_url", None) or "https://router.requesty.ai/v1"
        endpoint = f"{base_url.rstrip('/')}/models"

        async def fetch_models():
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, headers=headers) as resp:
                        if resp.status >= 400:
                            error_text = await resp.text()
                            raise Exception(f"Requesty API error {resp.status}: {error_text}")
                        
                        data = await resp.json()
                        
                # Process and sanitize models
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
                
                return sanitized
            except Exception as e:
                raise e

        try:
            models = asyncio.run(fetch_models())
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"models": models}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
