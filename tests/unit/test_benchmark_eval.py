from __future__ import annotations

import unittest
from unittest.mock import patch

from prioritx_eval.service import evaluate_fused_benchmark


class BenchmarkEvalTests(unittest.TestCase):
    def test_evaluates_fused_ranking_against_source_backed_positive(self) -> None:
        ranked = [
            {
                "ensembl_gene_id": "ENSG000002",
                "gene_symbol": "OTHER",
                "score": 0.81,
                "components": {"transcriptomics_component": 0.4},
            },
            {
                "ensembl_gene_id": "ENSG000001",
                "gene_symbol": "TNIK",
                "score": 0.44,
                "components": {"transcriptomics_component": 0.2},
            },
        ]
        with patch("prioritx_eval.service.fused_target_evidence", return_value=ranked):
            result = evaluate_fused_benchmark("ipf_tnik")

        self.assertEqual("ipf_lung_core", result["subset_id"])
        self.assertEqual(1, result["positive_targets_found"])
        self.assertEqual(2, result["metrics"]["best_rank"])
        self.assertEqual(0.5, result["metrics"]["mean_reciprocal_rank"])
        self.assertTrue(result["items"][0]["found"])
        self.assertEqual("gene_symbol", result["items"][0]["matching_strategy"])

    def test_reports_missing_positive_target(self) -> None:
        with patch("prioritx_eval.service.fused_target_evidence", return_value=[]):
            result = evaluate_fused_benchmark("hcc_cdk20")

        self.assertEqual(0, result["positive_targets_found"])
        self.assertIsNone(result["metrics"]["best_rank"])
        self.assertFalse(result["items"][0]["found"])


if __name__ == "__main__":
    unittest.main()
