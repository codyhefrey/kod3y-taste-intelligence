"""KOD3Y Taste Intelligence: transparent, Qloo-grounded discovery workflow.

An agentic tool orchestration: interpret request -> resolve 1-3 named taste seeds
-> fetch category-specific recommendations -> attach auditable evidence.
No simulated recommendations appear as live results. All API calls are server-side.
"""
import json
import os
import re
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8787"))
QLOO_BASE = "https://hackathon.api.qloo.com"
CATEGORIES = {"dining": "urn:entity:place", "music": "urn:entity:artist",
              "movies": "urn:entity:movie"}
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
MIN_BODY, MAX_BODY = 1, 4096


class QlooError(Exception):
    def __init__(self, status):
        self.status = status
        super().__init__(status)


def qloo_get(path, params, key):
    """Bounded remote request: key only in upstream header, never client-side."""
    query = urlencode(params)
    req = Request(QLOO_BASE + path + "?" + query,
                  headers={"X-Api-Key": key, "Accept": "application/json"}, method="GET")
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
        if exc.code == 400:
            raise QlooError("invalid_query") from None
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


def seeds_from(interest):
    if not isinstance(interest, str) or not 1 <= len(interest.strip()) <= 120:
        raise ValueError("Enter one to three named favorites (1–120 characters).")
    seeds = [x.strip() for x in interest.split(",")]
    if not 1 <= len(seeds) <= 3 or any(not 1 <= len(x) <= 65 for x in seeds):
        raise ValueError("Enter 1–3 comma-separated named favorites, each 1–65 characters.")
    return list(dict.fromkeys(seeds))


def _score(entity):
    query = entity.get("query")
    score = query.get("affinity") if isinstance(query, dict) else None
    return round(score, 3) if isinstance(score, (int, float)) and 0 <= score <= 1 else None


def _result(entity, category, seeds):
    name, entity_id = entity.get("name"), entity.get("entity_id")
    if not isinstance(name, str) or not isinstance(entity_id, str) or not UUID_RE.fullmatch(entity_id):
        return None
    if any(entity_id.lower() == s["entity_id"].lower() for s in seeds):
        return None
    props = entity.get("properties", {})
    desc = props.get("description", "") if isinstance(props, dict) else ""
    if not isinstance(desc, str):
        desc = ""
    tags = entity.get("tags", [])
    selected = [t.get("name") for t in tags if isinstance(t, dict)
                and isinstance(t.get("name"), str)
                and t.get("type", "").startswith(("urn:tag:genre:", "urn:tag:keyword:", "urn:tag:category:"))][:3] if isinstance(tags, list) else []
    affinity = _score(entity)
    return {
        "name": name[:130], "entity_id": entity_id, "category": category,
        "description": desc[:360], "affinity": affinity, "tags": selected,
        "reason": "Qloo Insights ranked this using the verified interest signals"
                  + (" and returned descriptive tags." if selected else "."),
        "source": "Qloo Insights API (live)",
    }


def recommendations(interest, category, location=""):
    seeds = seeds_from(interest)
    if category not in (*CATEGORIES, "all"):
        raise ValueError("Choose dining, music, movies or all categories.")
    if not isinstance(location, str) or len(location) > 80:
        raise ValueError("Location must be 80 characters or fewer.")
    location = location.strip()
    key = os.environ.get("QLOO_API_KEY", "").strip()
    if not key:
        return {"status": "needs_api_key", "message": "Qloo API key request submitted; live access is still pending.",
                "results": [], "steps": [{"tool": "Qloo", "status": "waiting_for_key"}]}

    trace, resolved = [], []
    for name in seeds:
        candidates = entities_from(qloo_get("/search", {"query": name, "take": 10}, key))
        valid = [x for x in candidates if isinstance(x.get("entity_id"), str)
                 and UUID_RE.fullmatch(x["entity_id"])
                 and isinstance(x.get("name"), str)
                 and x.get("subtype") not in ("urn:entity:locality", "urn:entity:album")]
        if not valid:
            trace.append({"tool": "entity_search", "query": name, "status": "no_match"})
            continue
        match = next((e for e in valid if e["name"].casefold() == name.casefold()), valid[0])
        resolved.append({"name": match["name"][:100], "entity_id": match["entity_id"],
                         "subtype": str(match.get("subtype", ""))[:70]})
        trace.append({"tool": "entity_search", "query": name, "status": "resolved",
                      "matched": match["name"][:100]})
    if not resolved:
        return {"status": "interest_not_found", "message": "Qloo could not resolve your named favorites. Try a specific musician, movie or restaurant.",
                "resolved_interests": [], "results": [], "steps": trace}
    ids = ",".join(dict.fromkeys(x["entity_id"] for x in resolved))
    target_categories = list(CATEGORIES) if category == "all" else [category]
    output = []
    for target in target_categories:
        params = {"filter.type": CATEGORIES[target], "signal.interests.entities": ids,
                  "filter.exclude.entities": ids, "feature.explainability": "true", "take": 7}
        if location and target == "dining":
            params["filter.location.query"] = location
        items = entities_from(qloo_get("/v2/insights", params, key))
        count = 0
        for e in items:
            if e.get("subtype") != CATEGORIES[target]:
                continue
            item = _result(e, target, resolved)
            if item is not None and not any(x["entity_id"] == item["entity_id"] for x in output):
                output.append(item)
                count += 1
                if count >= 5:
                    break
        trace.append({"tool": "qloo_insights", "category": target, "status": "completed",
                      "recommendations": count})
    return {"status": "ok" if output else "no_results",
            "message": "Recommendations fetched live from Qloo." if output else "Qloo returned no matching recommendations. Try another favorite or location.",
            "resolved_interests": resolved, "results": output, "steps": trace,
            "disclaimer": "Qloo affinity values are cultural matching scores, not probabilities of liking or success."}


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        for k, v in [("Content-Type", "application/json; charset=utf-8"),
                     ("Content-Length", str(len(body))),
                     ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff")]:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/health":
            return self.reply(200, {"status": "ok", "qloo_configured": bool(os.getenv("QLOO_API_KEY"))})
        if path not in ("/", "/index.html"):
            return self.reply(404, {"error": "Not found"})
        data = (ROOT / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/recommend":
            return self.reply(404, {"error": "Not found"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not MIN_BODY <= size <= MAX_BODY:
                return self.reply(413, {"error": "Invalid request size."})
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object.")
            result = recommendations(payload.get("interest"), payload.get("category"),
                                     payload.get("location", ""))
            return self.reply(200, result)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            return self.reply(400, {"error": str(exc)})
        except QlooError as exc:
            messages = {"unauthorized": "Qloo rejected the API key. Check your issued key.",
                        "forbidden": "Qloo access not permitted for this key.",
                        "rate_limited": "Qloo rate limit reached. Retry later.",
                        "invalid_query": "Qloo rejected the request parameters. Check the name or location.",
                        "invalid_response": "Qloo returned an unexpected response format.",
                        "upstream_unavailable": "Qloo is unavailable. Retry later.",
                        "upstream_error": "The Qloo API could not complete the request."}
            return self.reply(429 if exc.status == "rate_limited" else 502,
                              {"status": exc.status, "message": messages.get(exc.status, "Qloo error."), "results": []})


if __name__ == "__main__":
    print(f"Visit http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
