from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        repo_name = data.get('repoName')
        token = data.get('token')
        
        # Mock GitHub creation
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "success",
            "data": {
                "repoUrl": f"https://github.com/user/{repo_name}",
                "message": "Repository created successfully"
            }
        }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
        return
