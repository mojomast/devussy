from http.server import BaseHTTPRequestHandler
import json
import asyncio
from ..utils import setup_path

# Add project root to sys.path
setup_path()

from src.config import load_config
from src.clients.factory import create_llm_client
from src.pipeline.basic_devplan import BasicDevPlanGenerator
from src.models import ProjectDesign
from src.streaming import StreamingHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            design_data = data.get('design')
            
            if not design_data:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing design data")
                return

            # Parse design data into model
            design = ProjectDesign(**design_data)
            
            # Load config and client
            config = load_config()
            # Apply overrides if present in request
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
            generator = BasicDevPlanGenerator(llm_client)

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

                    async def on_token_async(self, token: str):
                        # Send keep-alive/progress chunks
                        # We don't necessarily need to send the content if the frontend doesn't display it,
                        # but sending it keeps the connection active.
                        try:
                            data = json.dumps({"content": token})
                            self.writer.write(f"data: {data}\n\n".encode('utf-8'))
                            self.writer.flush()
                        except Exception:
                            pass

                    async def on_completion_async(self, full_response: str):
                        pass

                streaming_handler = APIStreamingHandler(self.wfile)

                try:
                    # Create a task for generation
                    generation_task = asyncio.create_task(generator.generate(
                        project_design=design,
                        streaming_handler=streaming_handler
                    ))

                    # Loop until generation is done, sending keep-alives if needed
                    # (Though on_token_async should handle most of it)
                    while not generation_task.done():
                        await asyncio.sleep(0.5)
                        if not generation_task.done():
                            try:
                                self.wfile.write(b": keep-alive\n\n")
                                self.wfile.flush()
                            except Exception:
                                break

                    dev_plan = await generation_task
                    
                    # Debug: Log the parsed plan
                    print(f"DEBUG: Parsed {len(dev_plan.phases)} phases")
                    for phase in dev_plan.phases:
                        print(f"  Phase {phase.number}: {phase.title}")
                        print(f"    Description: {phase.description}")
                    
                    # Send completion event
                    final_data = json.dumps({"done": True, "plan": dev_plan.model_dump()})
                    self.wfile.write(f"data: {final_data}\n\n".encode('utf-8'))
                    
                except Exception as e:
                    print(f"Error generating plan: {e}")
                    error_data = json.dumps({"error": str(e)})
                    try:
                        self.wfile.write(f"data: {error_data}\n\n".encode('utf-8'))
                    except Exception:
                        pass

            # Create a new event loop for this thread to avoid conflicts
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(generate_stream())
            finally:
                loop.close()

        except Exception as e:
            print(f"Error in handler: {e}")
            # If headers haven't been sent, send 500
            # But we might have already sent headers for streaming
            try:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            except Exception:
                pass
