import json
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from chromemind.errors import SkillError

def scrape_tabs(remote_debug_port: int, limit: int) -> list[dict]:
    """
    Retrieves active tabs and Tab Groups via a local HTTP server that the 
    ChromeMind TabGroup Fetcher extension posts to.
    """
    received_data = []

    class ExtensionHandler(BaseHTTPRequestHandler):
        def do_OPTIONS(self):
            self.send_response(200, "ok")
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

        def do_POST(self):
            if self.path == '/submit_tabs':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                received_data.extend(json.loads(post_data.decode()))
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            else:
                self.send_response(404)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
        def log_message(self, format, *args):
            pass # Disable logging

    server = HTTPServer(('localhost', 9223), ExtensionHandler)
    server.timeout = 5.0 # Wait up to 5 seconds for the extension to connect
    
    try:
        server.handle_request() # Handles a single request
    except socket.timeout:
        raise SkillError("Timeout waiting for TabGroup Extension to submit data. Ensure the extension is loaded and running.")
    finally:
        server.server_close()
        
    return received_data[:limit]
