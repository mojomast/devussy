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
        # Route: /api/checkpoints
        if self.path.startswith('/api/checkpoints'):
            try:
                from api.checkpoints import handler
                handler.do_GET(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/checkpoints: {e}")
                import traceback
                traceback.print_exc()
        
        # Route: /api/models
        elif self.path.startswith('/api/models'):
            try:
                from api.models import handler
                handler.do_GET(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/models: {e}")
                import traceback
                traceback.print_exc()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        import threading
        thread_id = threading.current_thread().ident
        print(f"[dev_server] Thread {thread_id}: Received POST request to {self.path}")
        
        # Route: /api/design/hivemind
        if self.path.startswith('/api/design/hivemind'):
            try:
                from api.design_hivemind import handler
                handler.do_POST(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/design/hivemind: {e}")
                import traceback
                traceback.print_exc()

        # Route: /api/design
        elif self.path.startswith('/api/design'):
            try:
                from api.design import handler
                handler.do_POST(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/design: {e}")
                import traceback
                traceback.print_exc()
        
        # Route: /api/plan/basic
        elif self.path.startswith('/api/plan/basic'):
            try:
                from api.plan.basic import handler
                handler.do_POST(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/plan/basic: {e}")
                import traceback
                traceback.print_exc()

        # Route: /api/plan/detail
        elif self.path.startswith('/api/plan/detail'):
            try:
                from api.plan.detail import handler
                handler.do_POST(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/plan/detail: {e}")
                import traceback
                traceback.print_exc()

        # Route: /api/plan/hivemind
        elif self.path.startswith('/api/plan/hivemind'):
            try:
                from api.plan.hivemind import handler
                handler.do_POST(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/plan/hivemind: {e}")
                import traceback
                traceback.print_exc()

        # Route: /api/handoff
        elif self.path.startswith('/api/handoff'):
            try:
                from api.handoff import handler
                handler.do_POST(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/handoff: {e}")
                import traceback
                traceback.print_exc()

        # Route: /api/interview
        elif self.path.startswith('/api/interview'):
            try:
                from api.interview import handler
                handler.do_POST(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/interview: {e}")
                import traceback
                traceback.print_exc()

        # Route: /api/checkpoints
        elif self.path.startswith('/api/checkpoints'):
            try:
                from api.checkpoints import handler
                if self.command == 'GET':
                    handler.do_GET(self)
                elif self.command == 'POST':
                    handler.do_POST(self)
                elif self.command == 'OPTIONS':
                    handler.do_OPTIONS(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/checkpoints: {e}")
                import traceback
                traceback.print_exc()

        # Route: /api/github/create
        elif self.path.startswith('/api/github/create'):
            try:
                from api.github.create import handler
                if self.command == 'POST':
                    handler.do_POST(self)
                elif self.command == 'OPTIONS':
                    handler.do_OPTIONS(self)
            except Exception as e:
                self.send_error(500, str(e))
                print(f"Error in /api/github/create: {e}")
                import traceback
                traceback.print_exc()
        
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
    print(f"Server will handle requests with threading support")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
