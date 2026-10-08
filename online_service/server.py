"""Read-only API scaffold. Run behind an HTTPS reverse proxy on the VPS."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os


def response_for(path):
    if path=="/api/v1/health":return 200,{"api_version":1,"status":"ok","service":"starstruck-atelier"}
    if path=="/api/v1/capabilities":return 200,{"api_version":1,"features":[],"local_saves_authoritative":True}
    return 404,{"api_version":1,"error":"not_found"}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status,payload=response_for(self.path)
        body=json.dumps(payload,separators=(",",":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self,format,*args):
        # No player data is accepted or logged by this scaffold.
        pass

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def get_request(self):
        socket,address=super().get_request()
        socket.settimeout(5)
        return socket,address

def main():
    server=Server((os.environ.get("HOST","127.0.0.1"),int(os.environ.get("PORT","8080"))),Handler)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=="__main__":main()
