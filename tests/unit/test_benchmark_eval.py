from __future__ import annotations

import unittest
from unittest.mock import patch

from prioritx_eval.service import audit_target_evidence, evaluate_fused_benchmark


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
        self.assertEqual("strict", result["mode"])
        self.assertEqual("ipf_lung_core", result["integrity_review"]["subset_id"])

    def test_exploratory_mode_uses_extended_subset(self) -> None:
        ranked = [{"ensembl_gene_id": "ENSG000001", "gene_symbol": "CDK20", "score": 0.5, "components": {}}]
        with patch("prioritx_eval.service.fused_target_evidence", return_value=ranked):
            result = evaluate_fused_benchmark("hcc_cdk20", mode="exploratory")

        self.assertEqual("exploratory", result["mode"])
        self.assertEqual("hcc_adult_extended", result["subset_id"])

    def test_reports_missing_positive_target(self) -> None:
        with patch("prioritx_eval.service.fused_target_evidence", return_value=[]):
            result = evaluate_fused_benchmark("hcc_cdk20")

        self.assertEqual(0, result["positive_targets_found"])
        self.assertIsNone(result["metrics"]["best_rank"])
        self.assertFalse(result["items"][0]["found"])

    def test_audits_target_across_layers(self) -> None:
        transcriptomics = [
            {
                "gene_symbol": "TNIK",
                "ensembl_gene_id": "ENSG000001",
                "score": 0.22,
                "statistics": {"log2_fold_change": 0.4, "adjusted_p_value": 0.07},
            }
        ]
        genetics = [{
            "gene_symbol": "TNIK",
            "ensembl_gene_id": "ENSG000001",
            "score": 0.55,
            "provenance": {"association_rank": 887},
        }]
        fused = [{"gene_symbol": "TNIK", "ensembl_gene_id": "ENSG000001", "score": 0.4, "components": {"genetics_component": 0.2}}]
        contrasts = [{"contrast_id": "ipf_lung_core_gse52463"}]
        with patch("prioritx_eval.service.query_study_contrasts", return_value=contrasts), patch(
            "prioritx_eval.service.transcriptomics_real_scores",
            return_value=transcriptomics,
        ), patch(
            "prioritx_eval.service.open_targets_genetics_scores",
            return_value=genetics,
        ), patch(
            "prioritx_eval.service.fused_target_evidence",
            return_value=fused,
        ):
            result = audit_target_evidence("ipf_tnik", gene_symbol="TNIK")

        self.assertEqual("TNIK", result["gene_symbol"])
        self.assertTrue(result["transcriptomics"][0]["found"])
        self.assertFalse(result["transcriptomics"][0]["passes_support_rule"])
        self.assertTrue(result["open_targets_genetics"]["found"])
        self.assertEqual(887, result["open_targets_genetics"]["association_rank"])
        self.assertTrue(result["fused_target_evidence"]["found"])
        self.assertEqual("strict", result["mode"])


if __name__ == "__main__":
    unittest.main()
