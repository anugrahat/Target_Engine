from __future__ import annotations

import unittest
from unittest.mock import patch

from prioritx_eval.service import (
    audit_target_evidence,
    compare_benchmark_modes,
    evaluate_fused_benchmark,
    export_benchmark_health_rows,
    explain_target_evidence,
    explain_target_shortlist,
    summarize_benchmark_health,
    summarize_benchmark_dashboard,
    target_evidence_graph,
)


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

    def test_builds_target_evidence_graph(self) -> None:
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
            "provenance": {"association_rank": 887, "disease_id": "EFO_0000001"},
        }]
        fused = [{
            "gene_symbol": "TNIK",
            "ensembl_gene_id": "ENSG000001",
            "score": 0.4,
            "components": {"genetics_component": 0.2},
            "network_provenance": {"top_partners": [{"partner_symbol": "MAPK1", "score": 0.91}]},
        }]
        pathway = [{
            "gene_symbol": "TNIK",
            "ensembl_gene_id": "ENSG000001",
            "score": 0.3,
            "overlap_count": 1,
            "top_overlap_pathways": [
                {
                    "st_id": "R-HSA-123",
                    "name": "Example pathway",
                    "fdr": 0.01,
                }
            ],
        }]
        tractability = [{
            "gene_symbol": "TNIK",
            "ensembl_gene_id": "ENSG000001",
            "score": 0.25,
            "positive_bucket_count": 1,
            "positive_modalities": ["SM"],
            "positive_buckets": [{"label": "SM", "value": True}],
        }]
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
        ), patch(
            "prioritx_eval.service.reactome_pathway_scores",
            return_value=pathway,
        ), patch(
            "prioritx_eval.service.open_targets_tractability_scores",
            return_value=tractability,
        ):
            result = target_evidence_graph("ipf_tnik", gene_symbol="TNIK")

        self.assertEqual("TNIK", result["gene_symbol"])
        self.assertTrue(result["evidence_summary"]["genetics_found"])
        self.assertTrue(result["evidence_summary"]["network_found"])
        node_ids = {item["id"] for item in result["graph"]["nodes"]}
        self.assertIn("gene:ENSG000001", node_ids)
        self.assertIn("pathway:R-HSA-123", node_ids)
        edge_types = {item["type"] for item in result["graph"]["edges"]}
        self.assertIn("transcriptomics_support", edge_types)
        self.assertIn("genetics_association", edge_types)
        self.assertIn("string_interaction", edge_types)

    def test_explains_target_evidence(self) -> None:
        graph_result = {
            "benchmark_id": "ipf_tnik",
            "indication_name": "Idiopathic Pulmonary Fibrosis",
            "mode": "strict",
            "subset_id": "ipf_lung_core",
            "gene_symbol": "TNIK",
            "ensembl_gene_id": "ENSG000001",
            "graph": {
                "nodes": [
                    {"id": "gene:ENSG000001", "type": "gene", "label": "TNIK", "attributes": {}},
                    {"id": "tractability:ENSG000001", "type": "tractability_profile", "label": "TNIK tractability", "attributes": {"positive_modalities": ["SM"]}},
                    {"id": "pathway:R-HSA-123", "type": "pathway", "label": "Example pathway", "attributes": {"fdr": 0.01}},
                    {"id": "gene:MAPK1", "type": "gene", "label": "MAPK1", "attributes": {"is_network_partner": True}},
                ],
                "edges": [
                    {"type": "fused_target_evidence", "attributes": {"components": {"genetics_component": 0.2}}},
                    {"type": "genetics_association", "attributes": {"association_rank": 887}},
                ],
            },
            "evidence_summary": {
                "fused_found": True,
                "fused_rank": 125,
                "fused_score": 0.4012,
                "transcriptomics_found_in_contrasts": 2,
                "transcriptomics_support_hits": 0,
                "genetics_found": True,
                "tractability_found": True,
                "pathway_found": True,
                "network_found": True,
            },
            "integrity_review": {
                "families": [{"family": "pubmed_literature", "risk_level": "high"}],
            },
        }
        with patch("prioritx_eval.service.target_evidence_graph", return_value=graph_result):
            result = explain_target_evidence("ipf_tnik", gene_symbol="TNIK")

        self.assertEqual("TNIK", result["gene_symbol"])
        self.assertIn("ranked #125", result["overview"])
        self.assertTrue(any("association rank 887" in item for item in result["rationale"]))
        self.assertTrue(any("low-ranked" in item for item in result["caveats"]))
        self.assertEqual({"genetics_component": 0.2}, result["fused_components"])

    def test_explains_target_shortlist(self) -> None:
        ranked = [
            {"gene_symbol": "MUC5B", "ensembl_gene_id": "ENSG1", "score": 0.9},
            {"gene_symbol": "TNIK", "ensembl_gene_id": "ENSG9", "score": 0.85},
            {"gene_symbol": "SFTPA2", "ensembl_gene_id": "ENSG2", "score": 0.8},
        ]
        explanation = {
            "overview": "summary",
            "rationale": ["real support"],
            "caveats": ["none"],
            "fused_components": {"transcriptomics_component": 0.4},
            "evidence_summary": {"fused_rank": 1},
        }
        with patch("prioritx_eval.service.fused_target_evidence", return_value=ranked), patch(
            "prioritx_eval.service.explain_target_evidence",
            return_value=explanation,
        ):
            result = explain_target_shortlist("ipf_tnik", top_n=2)

        self.assertEqual("ipf_tnik", result["benchmark_id"])
        self.assertEqual(2, len(result["items"]))
        self.assertEqual("MUC5B", result["items"][0]["gene_symbol"])
        self.assertEqual("summary", result["items"][0]["overview"])
        self.assertFalse(result["items"][0]["benchmark_positive_overlay"]["is_source_backed_positive"])
        self.assertTrue(result["items"][1]["benchmark_positive_overlay"]["is_source_backed_positive"])
        self.assertEqual(1, result["benchmark_positive_overlay"]["recovered_in_top_n_count"])
        self.assertEqual("TNIK", result["benchmark_positive_overlay"]["items"][0]["gene_symbol"])
        self.assertEqual(2, result["benchmark_positive_overlay"]["items"][0]["rank"])

    def test_compares_strict_and_exploratory_modes(self) -> None:
        strict = {
            "benchmark_id": "ipf_tnik",
            "indication_name": "idiopathic pulmonary fibrosis",
            "subset_id": "ipf_lung_core",
            "items": [{"rank": 1, "gene_symbol": "MUC5B", "score": 0.9}],
            "benchmark_positive_overlay": {
                "items": [
                    {
                        "gene_symbol": "TNIK",
                        "label_tier": "tier1_mechanistic_support",
                        "recovered_in_top_n": False,
                        "rank": 4633,
                        "source": {"title": "paper"},
                    }
                ]
            },
            "integrity_review": {"subset_id": "ipf_lung_core"},
        }
        exploratory = {
            "benchmark_id": "ipf_tnik",
            "indication_name": "idiopathic pulmonary fibrosis",
            "subset_id": "ipf_lung_extended",
            "items": [{"rank": 1, "gene_symbol": "MUC5B", "score": 0.92}],
            "benchmark_positive_overlay": {
                "items": [
                    {
                        "gene_symbol": "TNIK",
                        "label_tier": "tier1_mechanistic_support",
                        "recovered_in_top_n": True,
                        "rank": 640,
                        "source": {"title": "paper"},
                    }
                ]
            },
            "integrity_review": {"subset_id": "ipf_lung_extended"},
        }
        with patch("prioritx_eval.service.explain_target_shortlist", side_effect=[strict, exploratory]):
            result = compare_benchmark_modes("ipf_tnik", top_n=10)

        self.assertEqual("ipf_tnik", result["benchmark_id"])
        self.assertEqual("improved_in_exploratory", result["benchmark_positive_comparison"][0]["movement"])
        self.assertEqual(3993, result["benchmark_positive_comparison"][0]["rank_delta"])
        self.assertEqual("ipf_lung_core", result["strict"]["subset_id"])
        self.assertEqual("ipf_lung_extended", result["exploratory"]["subset_id"])

    def test_summarizes_benchmark_dashboard(self) -> None:
        comparison = {
            "benchmark_id": "ipf_tnik",
            "indication_name": "idiopathic pulmonary fibrosis",
            "strict": {"subset_id": "ipf_lung_core", "top_targets": [{"gene_symbol": "MUC5B", "rank": 1, "score": 0.9}]},
            "exploratory": {"subset_id": "ipf_lung_extended", "top_targets": [{"gene_symbol": "MUC5B", "rank": 1, "score": 0.92}]},
            "benchmark_positive_comparison": [{"gene_symbol": "TNIK", "movement": "improved_in_exploratory"}],
        }
        with patch("prioritx_eval.service.list_benchmark_assertion_ids", return_value=["ipf_tnik"]), patch(
            "prioritx_eval.service.compare_benchmark_modes",
            return_value=comparison,
        ):
            result = summarize_benchmark_dashboard(top_n=3)

        self.assertEqual(1, result["benchmark_count"])
        self.assertEqual(3, result["top_n"])
        self.assertEqual("ipf_tnik", result["items"][0]["benchmark_id"])
        self.assertEqual("ipf_lung_core", result["items"][0]["strict_subset_id"])

    def test_summarizes_benchmark_health(self) -> None:
        dashboard = {
            "benchmark_count": 1,
            "items": [
                {
                    "benchmark_id": "ipf_tnik",
                    "indication_name": "idiopathic pulmonary fibrosis",
                    "strict_top_targets": [{"gene_symbol": "MMP1", "rank": 1, "score": 0.6}],
                    "exploratory_top_targets": [{"gene_symbol": "MUC5B", "rank": 1, "score": 0.59}],
                    "benchmark_positive_comparison": [
                        {
                            "gene_symbol": "TNIK",
                            "strict_rank": 4633,
                            "exploratory_rank": 1176,
                            "strict_recovered_in_top_n": False,
                            "exploratory_recovered_in_top_n": False,
                            "movement": "improved_in_exploratory",
                        }
                    ],
                }
            ],
        }
        with patch("prioritx_eval.service.summarize_benchmark_dashboard", return_value=dashboard):
            result = summarize_benchmark_health(top_n=10)

        self.assertEqual(1, result["benchmark_count"])
        self.assertEqual(1, result["totals"]["positive_target_count"])
        self.assertEqual(1, result["totals"]["improved_in_exploratory_count"])
        self.assertEqual("positive_recovered_outside_top_n", result["items"][0]["readiness_flag"])

    def test_exports_benchmark_health_rows(self) -> None:
        health = {
            "top_n": 10,
            "items": [
                {
                    "benchmark_id": "ipf_tnik",
                    "indication_name": "idiopathic pulmonary fibrosis",
                    "readiness_flag": "positive_recovered_outside_top_n",
                    "positive_target_count": 1,
                    "strict_recovered_in_top_n_count": 0,
                    "exploratory_recovered_in_top_n_count": 0,
                    "recovered_anywhere_count": 1,
                    "improved_in_exploratory_count": 1,
                    "worsened_in_exploratory_count": 0,
                    "unchanged_count": 0,
                    "strict_leader": {"gene_symbol": "MMP1", "rank": 1, "score": 0.6},
                    "exploratory_leader": {"gene_symbol": "MUC5B", "rank": 1, "score": 0.59},
                }
            ],
        }
        dashboard = {
            "items": [
                {
                    "benchmark_id": "ipf_tnik",
                    "strict_subset_id": "ipf_lung_core",
                    "exploratory_subset_id": "ipf_lung_extended",
                    "benchmark_positive_comparison": [
                        {
                            "gene_symbol": "TNIK",
                            "label_tier": "tier1_mechanistic_support",
                            "strict_rank": 4633,
                            "exploratory_rank": 1176,
                            "rank_delta": 3457,
                            "movement": "improved_in_exploratory",
                            "strict_recovered_in_top_n": False,
                            "exploratory_recovered_in_top_n": False,
                        }
                    ],
                }
            ],
        }
        with patch("prioritx_eval.service.summarize_benchmark_health", return_value=health), patch(
            "prioritx_eval.service.summarize_benchmark_dashboard",
            return_value=dashboard,
        ):
            result = export_benchmark_health_rows(top_n=10)

        self.assertEqual(1, result["row_count"])
        self.assertEqual("ipf_tnik", result["rows"][0]["benchmark_id"])
        self.assertEqual("TNIK", result["rows"][0]["positive_gene_symbol"])
        self.assertEqual("MMP1", result["rows"][0]["strict_leader_gene_symbol"])


if __name__ == "__main__":
    unittest.main()
