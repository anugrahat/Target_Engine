from __future__ import annotations

import unittest

from prioritx_data.http_api import handle_get


class HttpApiTests(unittest.TestCase):
    def test_health_route(self) -> None:
        status, payload = handle_get("/health", {})
        self.assertEqual(200, status)
        self.assertEqual({"status": "ok"}, payload)

    def test_benchmarks_route(self) -> None:
        status, payload = handle_get("/benchmarks", {})
        self.assertEqual(200, status)
        self.assertEqual(2, len(payload["items"]))

    def test_subset_detail_route(self) -> None:
        status, payload = handle_get("/subsets/ipf_lung_core", {})
        self.assertEqual(200, status)
        self.assertEqual("ipf_lung_core", payload["subset_id"])

    def test_dataset_manifest_filter_route(self) -> None:
        status, payload = handle_get("/dataset-manifests", {"subset_id": ["hcc_adult_core"]})
        self.assertEqual(200, status)
        self.assertEqual(4, len(payload["items"]))

    def test_contrast_readiness_route(self) -> None:
        status, payload = handle_get("/contrast-readiness", {"subset_id": ["ipf_lung_core"]})
        self.assertEqual(200, status)
        self.assertEqual(5, len(payload["items"]))
        self.assertIn("score", payload["items"][0])

    def test_transcriptomics_fixture_scores_route(self) -> None:
        status, payload = handle_get(
            "/transcriptomics-fixture-scores",
            {"contrast_id": ["hcc_adult_core_gse77314"]},
        )
        self.assertEqual(200, status)
        self.assertEqual(5, len(payload["items"]))
        self.assertEqual("fixture_transcriptomics_gene_score", payload["items"][0]["score_name"])

    def test_transcriptomics_fixture_scores_requires_contrast_id(self) -> None:
        status, payload = handle_get("/transcriptomics-fixture-scores", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_unknown_route_returns_404(self) -> None:
        status, payload = handle_get("/does-not-exist", {})
        self.assertEqual(404, status)
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
