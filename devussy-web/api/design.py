from http.server import BaseHTTPRequestHandler
import json
import asyncio
import os
from .utils import setup_path

# Add project root to sys.path
setup_path()

from src.config import load_config
from src.clients.factory import create_llm_client
from src.pipeline.project_design import ProjectDesignGenerator
from src.streaming import StreamingHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        project_name = data.get('projectName')
        languages = data.get('languages', [])
        requirements = data.get('requirements')
        
        # Extract model configuration overrides
        model_config = data.get('modelConfig', {})
        model_override = model_config.get('model')
        temperature_override = model_config.get('temperature')
        reasoning_effort_override = model_config.get('reasoning_effort')

        # Load config and initialize LLM client
        config = load_config()
        
        # Apply overrides to config if present
        if model_override:
            config.llm.model = model_override
        if temperature_override is not None:
            config.llm.temperature = float(temperature_override)
        if reasoning_effort_override:
            config.llm.reasoning_effort = reasoning_effort_override

        # Force streaming enabled for this endpoint (both global and llm-specific)
        config.llm.streaming_enabled = True
        config.streaming_enabled = True
        # Force Requesty provider as per user instruction
        config.llm.provider = "requesty"
        print(f"DEBUG: Configured streaming - Global: {config.streaming_enabled}, LLM: {config.llm.streaming_enabled}, Provider: {config.llm.provider}")

        llm_client = create_llm_client(config)
        print(f"DEBUG: Created LLM client type: {type(llm_client)}")
        generator = ProjectDesignGenerator(llm_client)

        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')  # Enable CORS for direct access
        self.end_headers()

        async def generate_stream():
            print("DEBUG: Starting generate_stream...")
            class APIStreamingHandler(StreamingHandler):
                def __init__(self, writer):
                    super().__init__(enable_console=False)
                    self.writer = writer
                    print("DEBUG: APIStreamingHandler initialized")

                async def on_token_async(self, token: str):
                    # Format as SSE data
                    print(f"DEBUG: Handler received token: {token[:5]}...")
                    data = json.dumps({"content": token})
                    self.writer.write(f"data: {data}\n\n".encode('utf-8'))
                    self.writer.flush()

                async def on_completion_async(self, full_response: str):
                    print("DEBUG: Handler on_completion_async called")
                    pass # Handled by the generator return

            streaming_handler = APIStreamingHandler(self.wfile)

            try:
                print("DEBUG: Creating generation task...")
                # Create a task for generation
                generation_task = asyncio.create_task(generator.generate(
                    project_name=project_name,
                    languages=languages,
                    requirements=requirements,
                    streaming_handler=streaming_handler
                ))

                # Loop until generation is done, sending keep-alives
                while not generation_task.done():
                    # Wait for a short period or until task is done
                    done, _ = await asyncio.wait([generation_task], timeout=2.0)
                    if done:
                        print("DEBUG: Generation task done.")
                        break
                    
                    # Send keep-alive comment to keep connection open
                    try:
                        print("DEBUG: Sending keep-alive...")
                        self.wfile.write(b": keep-alive\n\n")
                        self.wfile.flush()
                    except Exception as e:
                        print(f"DEBUG: Keep-alive failed: {e}")
                        # If writing fails, the connection is likely dead, so cancel generation
                        generation_task.cancel()
                        raise

                # Get the result (or raise exception if failed)
                design = await generation_task
                
                # Send completion event
                final_data = json.dumps({"done": True, "design": design.model_dump()})
                self.wfile.write(f"data: {final_data}\n\n".encode('utf-8'))
                
            except ConnectionAbortedError:
                print("Client disconnected during design generation.")
            except asyncio.CancelledError:
                print("Design generation cancelled.")
            except Exception as e:
                print(f"Error during design generation: {e}")
                error_data = json.dumps({"error": str(e)})
                try:
                    self.wfile.write(f"data: {error_data}\n\n".encode('utf-8'))
                except Exception:
                    pass

        print(f"Received design request for project: {project_name}")
        
        # Run the async generator with a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(generate_stream())
        finally:
            loop.close()
        print("Design request handler finished.")
