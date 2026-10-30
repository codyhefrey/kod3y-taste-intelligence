"""End-to-end HTTP smoke tests; only local loopback, never external APIs."""
import json
import os
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import Handler


class HttpSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.server.daemon_threads = True
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join(timeout=3)

    def test_html_page_loads(self):
        with urlopen(self.base + "/", timeout=3) as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b"<html", response.read().lower())

    def test_health_returns_200(self):
        with urlopen(self.base + "/api/health", timeout=3) as response:
            self.assertEqual(json.load(response)["status"], "ok")

    def test_head_probe_supported(self):
        with urlopen(Request(self.base + "/", method="HEAD"), timeout=3) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b"")

    def test_json_post_no_external_provider_call(self):
        payload = "{\"interest\":\"Black Panther\",\"category\":\"movies\"}".encode("utf-8")
        request = Request(self.base + "/api/recommend", data=payload,
                          headers={"Content-Type": "application/json"}, method="POST")
        with patch.dict(os.environ, {"QLOO_API_KEY": ""}):
            with patch("app.qloo_get") as remote:
                with urlopen(request, timeout=4) as response:
                    result = json.load(response)
                remote.assert_not_called()
        self.assertEqual(result["status"], "needs_api_key")

    def test_bad_route_returns_404(self):
        with self.assertRaises(HTTPError) as cm:
            urlopen(self.base + "/definitely-not-an-endpoint", timeout=3)
        self.assertEqual(cm.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
