from http.server import BaseHTTPRequestHandler
import json
import asyncio
from .utils import setup_path

# Add project root to sys.path
setup_path()

from src.config import load_config
from src.clients.factory import create_llm_client
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
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b"Missing design or plan data")
            return

        try:
            # Parse models
            design = ProjectDesign(**design_data)
            plan = DevPlan(**plan_data)
            
            # Load config and create client
            config = load_config()
            llm_client = create_llm_client(config)
            
            # Generate handoff
            # Generate handoff
            # Generate handoff
            async def generate_handoff():
                generator = HandoffPromptGenerator()
                handoff = generator.generate(
                    devplan=plan,
                    project_name=design.project_name,
                    architecture_notes=design.architecture_overview or "",
                    dependencies_notes=str(design.tech_stack) if design.tech_stack else ""
                )
                return handoff
            
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                handoff = loop.run_until_complete(generate_handoff())
            finally:
                loop.close()
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(handoff.model_dump_json().encode('utf-8'))
            
        except Exception as e:
            print(f"Error generating handoff: {e}")
            import traceback
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
