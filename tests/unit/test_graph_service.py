from __future__ import annotations

import unittest
from unittest.mock import patch

from prioritx_graph.service import (
    build_benchmark_knowledge_graph,
    evaluate_graph_augmented_benchmark,
    graph_augmented_target_evidence,
    graph_feature_scores,
)


CORE_RANKED = [
    {
        "ensembl_gene_id": "ENSG1",
        "gene_symbol": "TNIK",
        "score": 0.2,
        "components": {
            "transcriptomics_component": 0.2,
            "genetics_component": 0.0,
            "tractability_component": 0.0,
            "pathway_component": 0.0,
            "network_component": 0.0,
        },
        "transcriptomics_available": True,
        "genetics_available": False,
        "tractability_available": False,
        "pathway_available": False,
        "network_available": False,
        "transcriptomics_supporting_contrasts": 1,
        "transcriptomics_direction_conflict": False,
        "transcriptomics_provenance": {"source_contrast_ids": ["ipf_lung_core_gse1"]},
        "genetics_provenance": None,
    },
    {
        "ensembl_gene_id": "ENSG2",
        "gene_symbol": "MUC5B",
        "score": 0.15,
        "components": {
            "transcriptomics_component": 0.15,
            "genetics_component": 0.0,
            "tractability_component": 0.0,
            "pathway_component": 0.0,
            "network_component": 0.0,
        },
        "transcriptomics_available": True,
        "genetics_available": False,
        "tractability_available": False,
        "pathway_available": False,
        "network_available": False,
        "transcriptomics_supporting_contrasts": 2,
        "transcriptomics_direction_conflict": False,
        "transcriptomics_provenance": {"source_contrast_ids": ["ipf_lung_core_gse1"]},
        "genetics_provenance": None,
    },
]

PATHWAY_SCORES = [
    {
        "ensembl_gene_id": "ENSG1",
        "gene_symbol": "TNIK",
        "score": 0.9,
        "top_overlap_pathways": [
            {"st_id": "R-HSA-1", "name": "Fibrosis pathway", "fdr": 1e-6},
        ],
        "provenance": {"source_kind": "reactome_analysis_service"},
    },
    {
        "ensembl_gene_id": "ENSG2",
        "gene_symbol": "MUC5B",
        "score": 0.1,
        "top_overlap_pathways": [
            {"st_id": "R-HSA-1", "name": "Fibrosis pathway", "fdr": 1e-6},
        ],
        "provenance": {"source_kind": "reactome_analysis_service"},
    },
]


class GraphServiceTests(unittest.TestCase):
    def test_builds_provenance_first_graph(self) -> None:
        with patch("prioritx_graph.service.fused_target_evidence", return_value=CORE_RANKED), patch(
            "prioritx_graph.service.reactome_pathway_scores",
            return_value=PATHWAY_SCORES,
        ):
            payload = build_benchmark_knowledge_graph("ipf_tnik", candidate_limit=2, genetics_size=0)

        node_ids = {node["id"] for node in payload["graph"]["nodes"]}
        self.assertIn("disease:ipf_tnik", node_ids)
        self.assertIn("gene:ENSG1", node_ids)
        self.assertIn("pathway:R-HSA-1", node_ids)
        edge_types = {edge["type"] for edge in payload["graph"]["edges"]}
        self.assertIn("disease_gene_transcriptomics", edge_types)
        self.assertIn("disease_pathway_enrichment", edge_types)
        self.assertIn("pathway_gene_membership", edge_types)
        self.assertIn("shared_pathway_neighbor", edge_types)

    def test_scores_graph_features(self) -> None:
        with patch("prioritx_graph.service.fused_target_evidence", return_value=CORE_RANKED), patch(
            "prioritx_graph.service.reactome_pathway_scores",
            return_value=PATHWAY_SCORES,
        ):
            scores = graph_feature_scores("ipf_tnik", candidate_limit=2, genetics_size=0)

        self.assertEqual("knowledge_graph_support_score", scores[0]["score_name"])
        by_symbol = {item["gene_symbol"]: item for item in scores}
        self.assertGreater(by_symbol["TNIK"]["score"], by_symbol["MUC5B"]["score"])

    def test_graph_augmented_ranking_can_reorder_candidates(self) -> None:
        with patch("prioritx_graph.service.fused_target_evidence", return_value=CORE_RANKED), patch(
            "prioritx_graph.service.reactome_pathway_scores",
            return_value=PATHWAY_SCORES,
        ):
            ranked = graph_augmented_target_evidence("ipf_tnik", candidate_limit=2, genetics_size=0)

        self.assertEqual("TNIK", ranked[0]["gene_symbol"])
        self.assertEqual("graph_augmented_target_evidence_score", ranked[0]["score_name"])

    def test_evaluates_graph_augmented_benchmark(self) -> None:
        with patch("prioritx_graph.service.fused_target_evidence", return_value=CORE_RANKED), patch(
            "prioritx_graph.service.reactome_pathway_scores",
            return_value=PATHWAY_SCORES,
        ):
            result = evaluate_graph_augmented_benchmark("ipf_tnik", candidate_limit=2, genetics_size=0)

        self.assertEqual(1, result["metrics"]["best_rank"])
        self.assertTrue(result["items"][0]["found"])


if __name__ == "__main__":
    unittest.main()
