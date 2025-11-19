from http.server import BaseHTTPRequestHandler
import json
import asyncio
from .utils import setup_path

# Add project root to sys.path
setup_path()

from src.config import load_config
from src.clients.factory import create_llm_client
from src.pipeline.hivemind import HiveMindManager
from src.streaming import StreamingHandler
from src.templates import render_template

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        import threading
        thread_id = threading.current_thread().ident
        print(f"[design_hivemind.py] Thread {thread_id}: do_POST called")
        
        content_length = int(self.headers['Content-Length'])
        print(f"[design_hivemind.py] Thread {thread_id}: Reading {content_length} bytes")
        post_data = self.rfile.read(content_length)
        print(f"[design_hivemind.py] Thread {thread_id}: Data read, parsing JSON")
        data = json.loads(post_data.decode('utf-8'))

        project_name = data.get('projectName')
        requirements = data.get('requirements')
        languages = data.get('languages', [])
        
        print(f"[design_hivemind.py] Thread {thread_id}: Design HiveMind request for project: {project_name}")
        
        if not project_name or not requirements:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_msg = {
                "error": "Missing required data",
                "received": {
                    "has_projectName": bool(project_name),
                    "has_requirements": bool(requirements)
                }
            }
            self.wfile.write(json.dumps(error_msg).encode('utf-8'))
            print(f"ERROR: Missing required data. Received: {error_msg}")
            return

        # Load config and create client
        config = load_config()
        
        # Apply model config overrides if present
        if 'modelConfig' in data:
            model_config = data['modelConfig']
            if model_config.get('model'):
                config.llm.model = model_config['model']
            if model_config.get('temperature') is not None:
                config.llm.temperature = float(model_config['temperature'])

        # Force streaming enabled
        config.llm.streaming_enabled = True
        config.streaming_enabled = True

        llm_client = create_llm_client(config)

        # Send response headers for SSE
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        async def generate_stream():
            class DroneStreamHandler(StreamingHandler):
                """Stream handler for individual drone."""
                def __init__(self, drone_id: str, writer):
                    super().__init__(enable_console=False)
                    self.drone_id = drone_id
                    self.writer = writer
                    self.token_count = 0

                async def on_token_async(self, token: str):
                    try:
                        self.token_count += 1
                        if self.token_count % 50 == 0:
                            print(f"[design_hivemind.py] {self.drone_id}: Streamed {self.token_count} tokens")
                        data = json.dumps({"type": self.drone_id, "content": token})
                        self.writer.write(f"data: {data}\n\n".encode('utf-8'))
                        self.writer.flush()
                    except Exception as e:
                        print(f"[design_hivemind.py] Error writing {self.drone_id} token: {e}")

                async def on_completion_async(self, full_response: str):
                    print(f"[design_hivemind.py] {self.drone_id}: Complete, total tokens: {self.token_count}")
                    # Send completion signal
                    complete_data = json.dumps({"type": f"{self.drone_id}_complete"})
                    self.writer.write(f"data: {complete_data}\n\n".encode('utf-8'))
                    self.writer.flush()

            try:
                # Prepare prompt for design
                context = {
                    "project_name": project_name,
                    "languages": languages,
                    "frameworks": [],
                    "apis": [],
                    "requirements": requirements,
                }
                
                # Use the standard project design template
                prompt = render_template("project_design.jinja", context)
                print(f"[design_hivemind.py] Prepared design prompt")

                # Create stream handlers for each drone and arbiter
                drone1_handler = DroneStreamHandler("drone1", self.wfile)
                drone2_handler = DroneStreamHandler("drone2", self.wfile)
                drone3_handler = DroneStreamHandler("drone3", self.wfile)
                arbiter_handler = DroneStreamHandler("arbiter", self.wfile)
                
                # Create HiveMind manager
                hivemind = HiveMindManager(llm_client)
                
                # Run swarm with streaming callbacks
                print(f"[design_hivemind.py] Starting HiveMind swarm execution...")
                final_response = await hivemind.run_swarm(
                    prompt=prompt,
                    count=3,
                    temperature_jitter=True,
                    drone_callbacks=[drone1_handler, drone2_handler, drone3_handler],
                    arbiter_callback=arbiter_handler
                )
                
                print(f"[design_hivemind.py] HiveMind execution complete")
                
                # Send done signal with design data
                # We return the raw response as 'content' or 'raw_response' in the design object
                # The frontend expects { done: true, design: { ... } }
                
                # We can try to parse it if we want, but for now let's just return the raw content
                # The DesignView handles raw_response if parsing fails or isn't done here
                
                design_data = {
                    "project_name": project_name,
                    "raw_response": final_response,
                    # We could add parsed fields here if we used the parser from ProjectDesignGenerator
                }
                
                final_data = json.dumps({"done": True, "design": design_data})
                self.wfile.write(f"data: {final_data}\n\n".encode('utf-8'))
                self.wfile.flush()
                
            except Exception as e:
                print(f"[design_hivemind.py] Error generating HiveMind design: {e}")
                import traceback
                traceback.print_exc()
                error_data = json.dumps({"error": str(e)})
                try:
                    self.wfile.write(f"data: {error_data}\n\n".encode('utf-8'))
                    self.wfile.flush()
                except Exception:
                    pass

        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(generate_stream())
        finally:
            loop.close()
