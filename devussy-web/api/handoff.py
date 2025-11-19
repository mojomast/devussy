from http.server import BaseHTTPRequestHandler
import json
import asyncio
from ..utils import setup_path

# Add project root to sys.path
setup_path()

from src.config import load_config
from src.llm_client import LLMClient
from src.pipeline.handoff_prompt import HandoffPromptGenerator
from src.models import ProjectDesign, DevPlan

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        design_data = data.get('design')
        plan_data = data.get('plan')
        
        if not design_data or not plan_data:
            self.send_response(400)
            self.end_headers()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(handoff.model_dump_json().encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

        asyncio.run(generate_handoff())
