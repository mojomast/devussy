from http.server import BaseHTTPRequestHandler
import json
import asyncio
from ..utils import setup_path

# Add project root to sys.path
setup_path()

from src.config import load_config
from src.clients.factory import create_llm_client
from src.pipeline.detailed_devplan import DetailedDevPlanGenerator
from src.models import DevPlan, DevPlanPhase
from src.streaming import StreamingHandler
from src.concurrency import ConcurrencyManager

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
        print(f"[detail.py] Thread {thread_id}: do_POST called")
        
        content_length = int(self.headers['Content-Length'])
        print(f"[detail.py] Thread {thread_id}: Reading {content_length} bytes")
        post_data = self.rfile.read(content_length)
        print(f"[detail.py] Thread {thread_id}: Data read, parsing JSON")
        data = json.loads(post_data.decode('utf-8'))

        # Accept both 'plan' and 'basicPlan' for compatibility
        plan_data = data.get('plan') or data.get('basicPlan')
        phase_number = data.get('phaseNumber')
        project_name = data.get('projectName')
        
        print(f"[detail.py] Thread {thread_id}: Received request for phase {phase_number}, project: {project_name}")
        print(f"[detail.py] Plan has {len(plan_data.get('phases', []))} phases" if plan_data else "[detail.py] No plan data")
        
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
            class APIStreamingHandler(StreamingHandler):
                def __init__(self, writer):
                    super().__init__(enable_console=False)
                    self.writer = writer
                    self.token_count = 0

                async def on_token_async(self, token: str):
                    try:
                        self.token_count += 1
                        if self.token_count % 50 == 0:
                            print(f"[detail.py] Streamed {self.token_count} tokens so far...")
                        data = json.dumps({"content": token})
                        self.writer.write(f"data: {data}\n\n".encode('utf-8'))
                        self.writer.flush()
                    except Exception as e:
                        print(f"[detail.py] Error writing token: {e}")
                        import traceback
                        traceback.print_exc()

                async def on_completion_async(self, full_response: str):
                    print(f"[detail.py] Streaming complete, total tokens: {self.token_count}")
                    pass

            streaming_handler = APIStreamingHandler(self.wfile)

            try:
                # Parse the plan object
                print(f"[detail.py] Parsing plan_data with {len(plan_data.get('phases', []))} phases")
                dev_plan = DevPlan(**plan_data)
                print(f"[detail.py] DevPlan created with {len(dev_plan.phases)} phases")
                
                # Debug: print all phases
                for p in dev_plan.phases:
                    print(f"  Phase {p.number}: {p.title}")
                    print(f"    Description: {p.description[:100] if p.description else 'None'}...")
                
                # Find the requested phase
                target_phase = None
                for phase in dev_plan.phases:
                    if phase.number == phase_number:
                        target_phase = phase
                        break
                
                if not target_phase:
                    print(f"[detail.py] ERROR: Phase {phase_number} not found!")
                    print(f"[detail.py] Available phases: {[p.number for p in dev_plan.phases]}")
                    raise ValueError(f"Phase {phase_number} not found in plan")

                # Create concurrency manager
                concurrency_manager = ConcurrencyManager(config)
                
                # Create the generator
                generator = DetailedDevPlanGenerator(llm_client, concurrency_manager)
                
                # Send start message
                print(f"[detail.py] Sending start message for phase {phase_number}")
                self.wfile.write(f"data: {json.dumps({'content': f'Starting phase {phase_number} generation...\\n\\n'})}\n\n".encode('utf-8'))
                self.wfile.flush()

                # Generate detailed steps for this phase
                print(f"[detail.py] Calling _generate_phase_details for phase {phase_number}")
                print(f"[detail.py] Target phase: {target_phase.title}")
                print(f"[detail.py] Target phase description length: {len(target_phase.description) if target_phase.description else 0}")
                
                detailed_phase = await generator._generate_phase_details(
                    phase=target_phase,
                    project_name=project_name,
                    tech_stack=[],  # Could extract from plan if available
                    task_group_size=3,
                    streaming_handler=streaming_handler
                )
                
                print(f"[detail.py] Phase {phase_number} generation complete, got {len(detailed_phase.phase.steps)} steps")
                
                # Send the steps as content
                self.wfile.write(f"data: {json.dumps({'content': f'\\n\\nGenerated {len(detailed_phase.phase.steps)} steps for Phase {phase_number}\\n'})}\n\n".encode('utf-8'))
                self.wfile.flush()

                # Send completion event - extract the phase from the result
                final_data = json.dumps({"done": True, "phase": detailed_phase.phase.model_dump()})
                self.wfile.write(f"data: {final_data}\n\n".encode('utf-8'))
                self.wfile.flush()
                
            except Exception as e:
                print(f"Error generating phase details: {e}")
                import traceback
                traceback.print_exc()
                error_data = json.dumps({"error": str(e)})
                try:
                    self.wfile.write(f"data: {error_data}\n\n".encode('utf-8'))
                    self.wfile.flush()
                except Exception:
                    pass

        # Create a new event loop for this thread to avoid conflicts
        # when multiple requests come in concurrently
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(generate_stream())
        finally:
            loop.close()
