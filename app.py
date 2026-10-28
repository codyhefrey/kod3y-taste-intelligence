"""KOD3Y Taste Intelligence — local Qloo discovery prototype."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).parent
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8787"))
QLOO_URL = "https://hackathon.api.qloo.com/v2/insights/"
CATEGORIES = {"dining": "urn:entity:place", "music": "urn:entity:artist", "movies": "urn:entity:movie"}

def recommendations(interest, category):
    if not isinstance(interest, str) or not 1 <= len(interest.strip()) <= 100:
        raise ValueError("Enter an interest (1–100 characters).")
    if category not in CATEGORIES:
        raise ValueError("Choose dining, music, or movies.")
    key = os.environ.get("QLOO_API_KEY", "").strip()
    if not key:
        return {"status": "needs_api_key", "message": "Set QLOO_API_KEY to enable live Qloo recommendations.", "results": []}
    # Qloo's live API requires valid entity identifiers rather than arbitrary free-text.
    # This prototype deliberately does not invent entity IDs or fabricated recommendations.
    return {"status": "needs_entity_resolution", "message": "API key detected. Qloo entity resolution and live insights are the next integration milestone.", "results": []}

class Handler(BaseHTTPRequestHandler):
    def respond(self, status, obj):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if urlparse(self.path).path != "/":
            return self.respond(404, {"error": "Not found"})
        data = (ROOT / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_POST(self):
        if urlparse(self.path).path != "/api/recommend":
            return self.respond(404, {"error": "Not found"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 4096:
                return self.respond(413, {"error": "Invalid request size"})
            payload = json.loads(self.rfile.read(size))
            return self.respond(200, recommendations(payload.get("interest"), payload.get("category")))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self.respond(400, {"error": str(exc)})

if __name__ == "__main__":
    print(f"Open http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
