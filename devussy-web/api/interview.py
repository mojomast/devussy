from http.server import BaseHTTPRequestHandler
import json
import asyncio
from .utils import setup_path

# Add project root to sys.path
setup_path()

from src.config import load_config
from src.clients.factory import create_llm_client
from src.llm_interview import LLMInterviewManager

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        user_input = data.get('userInput')
        history = data.get('history', [])
        
        # Extract model configuration overrides
        model_config = data.get('modelConfig', {})
        model_override = model_config.get('model')
        temperature_override = model_config.get('temperature')
        reasoning_effort_override = model_config.get('reasoning_effort')

        # Load config
        config = load_config()
        
        # Apply overrides
        if model_override:
            config.llm.model = model_override
        if temperature_override is not None:
            config.llm.temperature = float(temperature_override)
        if reasoning_effort_override:
            config.llm.reasoning_effort = reasoning_effort_override

        # Initialize Interview Manager
        # We use a fresh instance for each request, so we need to rehydrate state
        manager = LLMInterviewManager(config, verbose=True)
        
        # Rehydrate history
        # manager.__init__ adds the system prompt. We append the passed history.
        # We assume 'history' from frontend contains {"role": "...", "content": "..."} objects
        # excluding the initial system prompt which the manager adds itself.
        if history:
            manager.conversation_history.extend(history)

        try:
            # Process input
            # _send_to_llm handles appending user input to history, calling LLM, 
            # appending assistant response, and returning the response text.
            response_text = manager._send_to_llm(user_input)
            
            # Check for structured data (completion)
            extracted_data = manager._extract_structured_data(response_text)
            is_complete = False
            
            if extracted_data and manager._validate_extracted_data(extracted_data):
                is_complete = True
            
            response_data = {
                "response": response_text,
                "extractedData": extracted_data,
                "isComplete": is_complete
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
