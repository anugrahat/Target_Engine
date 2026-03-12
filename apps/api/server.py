"""Minimal read-only HTTP server for PrioriTx registry fixtures."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from prioritx_data.http_api import handle_get


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


class RegistryRequestHandler(BaseHTTPRequestHandler):
    """Serve read-only registry routes as JSON."""

    server_version = "PrioriTxRegistryAPI/0.1"

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in CORS_HEADERS.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        status, payload = handle_get(parsed.path, parse_qs(parsed.query))
        self._send_json(status, payload)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        for key, value in CORS_HEADERS.items():
            self.send_header(key, value)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), RegistryRequestHandler)
    print("PrioriTx registry API listening on http://127.0.0.1:8000")
    print("Routes: /health, /benchmarks, /materialized/benchmark-dashboard-summary, /materialized/benchmark-health-summary, /materialized/benchmark-health-export, /materialized/benchmark-mode-comparison, /materialized/target-shortlist-explanations, /benchmark-health-summary, /benchmark-dashboard-summary, /benchmark-mode-comparison, /target-shortlist-explanations, /target-explanation, /target-evidence-graph, /knowledge-graph, /graph-feature-scores, /graph-augmented-target-evidence, /graph-augmented-benchmark-evaluation, /benchmark-health-export, /rl-benchmark-evaluation")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
