from http.server import BaseHTTPRequestHandler
import json
import asyncio
from ..utils import setup_path

# Add project root to sys.path
setup_path()

from src.config import load_config
from src.llm_client import LLMClient
from src.concurrency import ConcurrencyManager
from src.pipeline.detailed_devplan import DetailedDevPlanGenerator
from src.models import DevPlan, DevPlanPhase

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        plan_data = data.get('plan')
        phase_number = data.get('phaseNumber')
        project_name = data.get('projectName')
        
        if not plan_data or phase_number is None or not project_name:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing required data"}).encode('utf-8'))
            return

        self.end_headers()

        async def generate_stream():
            try:
                # We need to stream the raw tokens or steps. 
                # The DetailedDevPlanGenerator doesn't expose a simple token callback for a single phase 
                # in the same way ProjectDesignGenerator does, but it uses LLMClient.
                # We can pass a custom streaming handler via llm_kwargs if the underlying LLMClient supports it.
                # However, DetailedDevPlanGenerator._generate_phase_details calls generate_completion, not generate_completion_streaming.
                # For now, we will simulate streaming by sending the final result, or we'd need to modify the generator to support streaming.
                # Given the constraints, we'll wait for the generation and then send the result.
                # Ideally, we would refactor the generator to support streaming, but that's out of scope for this integration task.
                
                # To provide *some* feedback, we can send a "start" message.
                self.wfile.write(f"data: {json.dumps({'content': 'Generating details...'})}\n\n".encode('utf-8'))
                self.wfile.flush()

                # Generate details for the single phase
                # We use the internal _generate_phase_details method to target just one phase
                # This is a bit of a hack to reuse the logic without running the full plan generation
                detailed_phase = await generator._generate_phase_details(
                    phase=target_phase,
                    project_name=project_name,
                    tech_stack=[], # We might need to pass this if available
                    task_group_size=3
                )
                
                # Send the steps as "content" to simulate the streaming log effect
                for step in detailed_phase.steps:
                    log_message = f"Generated Step {step.number}: {step.description}\n"
                    self.wfile.write(f"data: {json.dumps({'content': log_message})}\n\n".encode('utf-8'))
                    self.wfile.flush()

                # Send completion event
                final_data = json.dumps({"done": True, "phase": detailed_phase.model_dump()})
                self.wfile.write(f"data: {final_data}\n\n".encode('utf-8'))
                
            except Exception as e:
                error_data = json.dumps({"error": str(e)})
                self.wfile.write(f"data: {error_data}\n\n".encode('utf-8'))

        asyncio.run(generate_stream())
