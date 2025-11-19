from http.server import BaseHTTPRequestHandler
import json
import asyncio
from ..utils import setup_path

# Add project root to sys.path
setup_path()

from src.config import load_config
from src.clients.factory import create_llm_client
from src.pipeline.hivemind import HiveMindManager
from src.models import DevPlan, DevPlanPhase
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
        print(f"[hivemind.py] Thread {thread_id}: do_POST called")
        
        content_length = int(self.headers['Content-Length'])
        print(f"[hivemind.py] Thread {thread_id}: Reading {content_length} bytes")
        post_data = self.rfile.read(content_length)
        print(f"[hivemind.py] Thread {thread_id}: Data read, parsing JSON")
        data = json.loads(post_data.decode('utf-8'))

        plan_data = data.get('plan')
        phase_number = data.get('phaseNumber')
        project_name = data.get('projectName')
        
        print(f"[hivemind.py] Thread {thread_id}: HiveMind request for phase {phase_number}, project: {project_name}")
        print(f"[hivemind.py] Plan has {len(plan_data.get('phases', []))} phases" if plan_data else "[hivemind.py] No plan data")
        
        if not plan_data or phase_number is None or not project_name:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_msg = {
                "error": "Missing required data",
                "received": {
                    "has_plan": bool(plan_data),
                    "has_phaseNumber": phase_number is not None,
                    "has_projectName": bool(project_name)
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
                            print(f"[hivemind.py] {self.drone_id}: Streamed {self.token_count} tokens")
                        data = json.dumps({"type": self.drone_id, "content": token})
                        self.writer.write(f"data: {data}\\n\\n".encode('utf-8'))
                        self.writer.flush()
                    except Exception as e:
                        print(f"[hivemind.py] Error writing {self.drone_id} token: {e}")

                async def on_completion_async(self, full_response: str):
                    print(f"[hivemind.py] {self.drone_id}: Complete, total tokens: {self.token_count}")
                    # Send completion signal
                    complete_data = json.dumps({"type": f"{self.drone_id}_complete"})
                    self.writer.write(f"data: {complete_data}\\n\\n".encode('utf-8'))
                    self.writer.flush()

            try:
                # Parse the plan object
                print(f"[hivemind.py] Parsing plan_data with {len(plan_data.get('phases', []))} phases")
                dev_plan = DevPlan(**plan_data)
                print(f"[hivemind.py] DevPlan created with {len(dev_plan.phases)} phases")
                
                # Find the requested phase
                target_phase = None
                for phase in dev_plan.phases:
                    if phase.number == phase_number:
                        target_phase = phase
                        break
                
                if not target_phase:
                    print(f"[hivemind.py] ERROR: Phase {phase_number} not found!")
                    print(f"[hivemind.py] Available phases: {[p.number for p in dev_plan.phases]}")
                    raise ValueError(f"Phase {phase_number} not found in plan")

                # Prepare prompt for phase
                phase_context = {
                    "project_name": project_name,
                    "phase": target_phase.model_dump(),
                    "all_phases": [p.model_dump() for p in dev_plan.phases]
                }
                
                prompt = render_template("phase_detail.jinja", phase_context)
                print(f"[hivemind.py] Prepared prompt for phase {phase_number}")

                # Create stream handlers for each drone and arbiter
                drone1_handler = DroneStreamHandler("drone1", self.wfile)
                drone2_handler = DroneStreamHandler("drone2", self.wfile)
                drone3_handler = DroneStreamHandler("drone3", self.wfile)
                arbiter_handler = DroneStreamHandler("arbiter", self.wfile)
                
                # Create HiveMind manager
                hivemind = HiveMindManager(llm_client)
                
                # Run swarm with streaming callbacks
                print(f"[hivemind.py] Starting HiveMind swarm execution...")
                final_response = await hivemind.run_swarm(
                    prompt=prompt,
                    count=3,
                    temperature_jitter=True,
                    drone_callbacks=[drone1_handler, drone2_handler, drone3_handler],
                    arbiter_callback=arbiter_handler
                )
                
                print(f"[hivemind.py] HiveMind execution complete")
                
                # Build detailed phase from final response
                # For now, just use the arbiter's response as the detailed content
                detailed_phase = {
                    **target_phase.model_dump(),
                    "detailedContent": final_response,
                    "steps": []  # TODO: Parse steps from arbiter response if needed
                }
                
                # Send done signal with phase data
                final_data = json.dumps({"done": True, "phase": detailed_phase})
                self.wfile.write(f"data: {final_data}\\n\\n".encode('utf-8'))
                self.wfile.flush()
                
            except Exception as e:
                print(f"[hivemind.py] Error generating HiveMind phase: {e}")
                import traceback
                traceback.print_exc()
                error_data = json.dumps({"error": str(e)})
                try:
                    self.wfile.write(f"data: {error_data}\\n\\n".encode('utf-8'))
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
