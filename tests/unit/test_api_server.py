from __future__ import annotations

import unittest

from apps.api.server import CORS_HEADERS


class ApiServerTests(unittest.TestCase):
    def test_cors_headers_allow_browser_access(self) -> None:
        self.assertEqual("*", CORS_HEADERS["Access-Control-Allow-Origin"])
        self.assertIn("GET", CORS_HEADERS["Access-Control-Allow-Methods"])
        self.assertIn("OPTIONS", CORS_HEADERS["Access-Control-Allow-Methods"])


if __name__ == "__main__":
    unittest.main()
