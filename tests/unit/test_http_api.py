from __future__ import annotations

import unittest
from unittest.mock import patch

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

    def test_transcriptomics_real_scores_route(self) -> None:
        mocked_items = [{"ensembl_gene_id": "ENSG000001", "score_name": "real_transcriptomics_inferential_score"}]
        with patch("prioritx_data.http_api.transcriptomics_real_scores", return_value=mocked_items):
            status, payload = handle_get(
                "/transcriptomics-real-scores",
                {"contrast_id": ["ipf_lung_core_gse52463"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("real_transcriptomics_inferential_score", payload["items"][0]["score_name"])

    def test_transcriptomics_evidence_route(self) -> None:
        mocked_items = [{"ensembl_gene_id": "ENSG000001", "score_name": "cross_contrast_transcriptomics_evidence_score"}]
        with patch("prioritx_data.http_api.transcriptomics_indication_evidence", return_value=mocked_items):
            status, payload = handle_get(
                "/transcriptomics-evidence",
                {"subset_id": ["hcc_adult_core"], "min_support": ["2"]},
            )
        self.assertEqual(200, status)
        self.assertEqual("cross_contrast_transcriptomics_evidence_score", payload["items"][0]["score_name"])

    def test_transcriptomics_evidence_requires_scope(self) -> None:
        status, payload = handle_get("/transcriptomics-evidence", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_transcriptomics_evidence_validates_min_support(self) -> None:
        status, payload = handle_get("/transcriptomics-evidence", {"subset_id": ["hcc_adult_core"], "min_support": ["abc"]})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_transcriptomics_real_scores_requires_contrast_id(self) -> None:
        status, payload = handle_get("/transcriptomics-real-scores", {})
        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_unknown_route_returns_404(self) -> None:
        status, payload = handle_get("/does-not-exist", {})
        self.assertEqual(404, status)
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
