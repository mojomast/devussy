from http.server import BaseHTTPRequestHandler
import json
import os
import glob
import time
from datetime import datetime
from .utils import setup_path

# Add project root to sys.path
setup_path()

CHECKPOINT_DIR = ".checkpoints"

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """List checkpoints or get a specific one."""
        # Parse query params
        path = self.path
        query_params = {}
        if '?' in path:
            query_string = path.split('?')[1]
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=')
                    query_params[key] = value

        if not os.path.exists(CHECKPOINT_DIR):
            os.makedirs(CHECKPOINT_DIR)

        if 'id' in query_params:
            # Load specific checkpoint
            checkpoint_id = query_params['id']
            filepath = os.path.join(CHECKPOINT_DIR, f"{checkpoint_id}.json")
            
            if not os.path.exists(filepath):
                self.send_error(404, "Checkpoint not found")
                return

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
        else:
            # List checkpoints
            checkpoints = []
            try:
                files = glob.glob(os.path.join(CHECKPOINT_DIR, "*.json"))
                # Sort by modification time, newest first
                files.sort(key=os.path.getmtime, reverse=True)
                
                for filepath in files:
                    filename = os.path.basename(filepath)
                    checkpoint_id = filename.replace('.json', '')
                    
                    # Read metadata (first few lines or just stat)
                    # We'll just read the whole file for now as they shouldn't be huge, 
                    # or better, just rely on filename/stat if we don't need deep details yet.
                    # Let's peek at the content to get the name/timestamp from the JSON if available
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            checkpoints.append({
                                "id": checkpoint_id,
                                "name": data.get("name", checkpoint_id),
                                "timestamp": data.get("timestamp", os.path.getmtime(filepath)),
                                "projectName": data.get("projectName", "Unknown Project"),
                                "stage": data.get("stage", "unknown")
                            })
                    except:
                        continue

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"checkpoints": checkpoints}).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))

    def do_POST(self):
        """Save a new checkpoint."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            if not os.path.exists(CHECKPOINT_DIR):
                os.makedirs(CHECKPOINT_DIR)
            
            # Generate ID
            timestamp = int(time.time())
            name = data.get("name", "checkpoint").replace(" ", "_")
            checkpoint_id = f"{timestamp}_{name}"
            
            # Add metadata
            data["timestamp"] = timestamp
            data["id"] = checkpoint_id
            
            filepath = os.path.join(CHECKPOINT_DIR, f"{checkpoint_id}.json")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "id": checkpoint_id}).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
