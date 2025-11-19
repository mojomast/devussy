from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import sys
import os
import importlib

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import handlers
# We import them inside the methods to avoid circular import issues if any,
# and to ensure fresh imports if we were reloading (though we aren't here).

class DevServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Route: /api/models
        if self.path.startswith('/api/models'):
            try:
                from api.models import handler
                handler.do_GET(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/models: {e}")
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        # Route: /api/design
        if self.path.startswith('/api/design'):
            try:
                from api.design import handler
                handler.do_POST(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/design: {e}")
        
        # Route: /api/plan/basic
        elif self.path.startswith('/api/plan/basic'):
            try:
                from api.plan.basic import handler
                handler.do_POST(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/plan/basic: {e}")

        # Route: /api/plan/detail
        elif self.path.startswith('/api/plan/detail'):
            try:
                from api.plan.detail import handler
                handler.do_POST(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/plan/detail: {e}")

        # Route: /api/handoff
        elif self.path.startswith('/api/handoff'):
            try:
                from api.handoff import handler
                handler.do_POST(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/handoff: {e}")

        # Route: /api/interview
        elif self.path.startswith('/api/interview'):
            try:
                from api.interview import handler
                handler.do_POST(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/interview: {e}")
        
        else:
            self.send_error(404, "Not Found")

    def do_OPTIONS(self):
        # Handle CORS preflight if needed, though Next.js rewrite handles it usually
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

def run(server_class=ThreadingHTTPServer, handler_class=DevServerHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting Python API server on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
