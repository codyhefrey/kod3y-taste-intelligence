"""KOD3Y Taste Intelligence — Qloo-backed cultural discovery.

API credentials are read only from the server environment, never sent to browsers.
The live Qloo workflow has not been verified until an issued key is tested.
"""
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8787"))
QLOO_BASE = "https://hackathon.api.qloo.com"
CATEGORIES = {
    "dining": "urn:entity:place",
    "music": "urn:entity:artist",
    "movies": "urn:entity:movie",
}
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


class QlooError(Exception):
    def __init__(self, status):
        super().__init__(status)
        self.status = status


def qloo_get(path, params, key):
    """Server-side, bounded Qloo API GET. Do not log keys or upstream bodies."""
    query = urlencode(params)
    req = Request(
        QLOO_BASE + path + "?" + query,
        headers={"X-Api-Key": key, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(req, timeout=12) as response:
            return json.load(response)
    except HTTPError as exc:
        if exc.code == 401:
            raise QlooError("unauthorized") from None
        if exc.code == 403:
            raise QlooError("forbidden") from None
        if exc.code == 429:
            raise QlooError("rate_limited") from None
        raise QlooError("upstream_error") from None
    except (URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        raise QlooError("upstream_unavailable") from None


def entities_from(payload):
    if not isinstance(payload, dict):
        raise QlooError("invalid_response")
    results = payload.get("results", {})
    if isinstance(results, dict):
        entities = results.get("entities", [])
    elif isinstance(results, list):
        entities = results
    else:
        raise QlooError("invalid_response")
    if not isinstance(entities, list):
        raise QlooError("invalid_response")
    return [e for e in entities if isinstance(e, dict)]


def recommendations(interest, category):
    if not isinstance(interest, str) or not 1 <= len(interest.strip()) <= 100:
        raise ValueError("Enter an interest (1–100 characters).")
    if category not in CATEGORIES:
        raise ValueError("Choose dining, music, or movies.")
    key = os.environ.get("QLOO_API_KEY", "").strip()
    if not key:
        return {
            "status": "needs_api_key",
            "message": "Your Qloo API key is pending. Set QLOO_API_KEY on the server to test live recommendations.",
            "results": [],
        }

    # Step 1: Resolve a named favorite into a real Qloo entity ID.
    interest = interest.strip()
    search = qloo_get("/search", {"query": interest, "take": 8}, key)
    candidates = [e for e in entities_from(search) if
                  isinstance(e.get("entity_id"), str) and UUID_RE.fullmatch(e["entity_id"])]
    if not candidates:
        return {
            "status": "interest_not_found",
            "message": "Qloo could not match that interest. Try a specific movie, musician, or restaurant name.",
            "results": [],
        }
    # Prefer exact name, then a usable match. Never generate or guess entity IDs.
    seed = next((e for e in candidates if str(e.get("name", "")).casefold() == interest.casefold()), candidates[0])

    # Step 2: Use the matched ID as a taste signal to retrieve cross-category picks.
    insights = qloo_get("/v2/insights", {
        "filter.type": CATEGORIES[category],
        "signal.interests.entities": seed["entity_id"],
        "filter.exclude.entities": seed["entity_id"],
        "take": 6,
    }, key)
    results = []
    for entity in entities_from(insights):
        if entity.get("subtype") != CATEGORIES[category]:
            continue
        name, entity_id = entity.get("name"), entity.get("entity_id")
        if not isinstance(name, str) or not isinstance(entity_id, str):
            continue
        if not UUID_RE.fullmatch(entity_id) or entity_id.lower() == seed["entity_id"].lower():
            continue
        props = entity.get("properties")
        description = props.get("description", "") if isinstance(props, dict) else ""
        if not isinstance(description, str):
            description = ""
        results.append({
            "name": name[:150], "entity_id": entity_id,
            "description": description[:260], "source": "Qloo Insights API",
        })
        if len(results) == 6:
            break
    return {
        "status": "ok" if results else "no_results",
        "message": "Live Qloo API results." if results else "Qloo returned no matching recommendations for this interest.",
        "resolved_interest": {"name": str(seed.get("name", interest))[:150], "entity_id": seed["entity_id"]},
        "results": results,
    }


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
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
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object.")
            return self.respond(200, recommendations(payload.get("interest"), payload.get("category")))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self.respond(400, {"error": str(exc)})
        except QlooError as exc:
            messages = {
                "unauthorized": "Qloo rejected the API key (401). Check the issued key and hackathon host.",
                "forbidden": "The key lacks permission for this Qloo API request (403).",
                "rate_limited": "Qloo rate limit reached. Retry later.",
                "invalid_response": "Qloo returned an unexpected response format.",
                "upstream_unavailable": "Could not reach Qloo. Retry later.",
                "upstream_error": "Qloo could not complete this request.",
            }
            code = 429 if exc.status == "rate_limited" else 502
            return self.respond(code, {"status": exc.status, "message": messages.get(exc.status, "Qloo error."), "results": []})


if __name__ == "__main__":
    print(f"Open http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
