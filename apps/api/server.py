"""Minimal read-only HTTP server for PrioriTx registry fixtures."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from prioritx_data.http_api import handle_get


class RegistryRequestHandler(BaseHTTPRequestHandler):
    """Serve read-only registry routes as JSON."""

    server_version = "PrioriTxRegistryAPI/0.1"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        status, payload = handle_get(parsed.path, parse_qs(parsed.query))
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), RegistryRequestHandler)
    print("PrioriTx registry API listening on http://127.0.0.1:8000")
    print("Routes: /health, /benchmarks, /subsets, /dataset-manifests, /study-contrasts, /contrast-readiness, /open-targets-genetics, /transcriptomics-evidence, /transcriptomics-real-scores, /transcriptomics-fixture-scores")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
