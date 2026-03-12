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
        "overlap_count": 1,
        "top_overlap_pathways": [
            {"st_id": "R-HSA-1", "name": "Fibrosis pathway", "fdr": 1e-6},
        ],
        "provenance": {"source_kind": "reactome_analysis_service"},
    },
    {
        "ensembl_gene_id": "ENSG2",
        "gene_symbol": "MUC5B",
        "score": 0.1,
        "overlap_count": 1,
        "top_overlap_pathways": [
            {"st_id": "R-HSA-1", "name": "Fibrosis pathway", "fdr": 1e-6},
        ],
        "provenance": {"source_kind": "reactome_analysis_service"},
    },
]

MECHANISTIC_EDGES = [
    {
        "source": {"node_type": "disease", "ref": "ipf_tnik"},
        "target": {"ref": "myofibroblast_differentiation", "label": "Myofibroblast differentiation", "mechanism_kind": "cell_state_program"},
        "edge_type": "disease_mechanism_support",
        "weight": 0.95,
        "leakage_risk": "low",
        "sources": [{"title": "paper"}],
    },
    {
        "source": {"node_type": "gene", "ref": "TNIK"},
        "target": {"ref": "myofibroblast_differentiation", "label": "Myofibroblast differentiation", "mechanism_kind": "cell_state_program"},
        "edge_type": "gene_mechanism_support",
        "weight": 0.92,
        "leakage_risk": "medium",
        "sources": [{"title": "paper"}],
    },
]


class GraphServiceTests(unittest.TestCase):
    def test_builds_provenance_first_graph(self) -> None:
        with patch("prioritx_graph.service.fused_target_evidence", return_value=CORE_RANKED), patch(
            "prioritx_graph.service.load_reactome_membership_cache",
            return_value={"TNIK": [], "MUC5B": []},
        ), patch(
            "prioritx_graph.service.load_reactome_pathway_enrichment",
            return_value=[
                {
                    "pathway": {"st_id": "R-HSA-1", "name": "Fibrosis pathway", "species_name": "Homo sapiens"},
                    "statistics": {"fdr": 1e-6},
                }
            ],
        ), patch(
            "prioritx_graph.service._score_pathway_overlap",
            side_effect=PATHWAY_SCORES,
        ), patch(
            "prioritx_graph.service.load_mechanistic_edges",
            return_value=[],
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
            "prioritx_graph.service.load_reactome_membership_cache",
            return_value={"TNIK": [], "MUC5B": []},
        ), patch(
            "prioritx_graph.service.load_reactome_pathway_enrichment",
            return_value=[
                {
                    "pathway": {"st_id": "R-HSA-1", "name": "Fibrosis pathway", "species_name": "Homo sapiens"},
                    "statistics": {"fdr": 1e-6},
                }
            ],
        ), patch(
            "prioritx_graph.service._score_pathway_overlap",
            side_effect=PATHWAY_SCORES,
        ), patch(
            "prioritx_graph.service.load_mechanistic_edges",
            return_value=[],
        ):
            scores = graph_feature_scores("ipf_tnik", candidate_limit=2, genetics_size=0)

        self.assertEqual("knowledge_graph_support_score", scores[0]["score_name"])
        by_symbol = {item["gene_symbol"]: item for item in scores}
        self.assertGreater(by_symbol["TNIK"]["score"], by_symbol["MUC5B"]["score"])

    def test_graph_augmented_ranking_can_reorder_candidates(self) -> None:
        with patch("prioritx_graph.service.fused_target_evidence", return_value=CORE_RANKED), patch(
            "prioritx_graph.service.load_reactome_membership_cache",
            return_value={"TNIK": [], "MUC5B": []},
        ), patch(
            "prioritx_graph.service.load_reactome_pathway_enrichment",
            return_value=[
                {
                    "pathway": {"st_id": "R-HSA-1", "name": "Fibrosis pathway", "species_name": "Homo sapiens"},
                    "statistics": {"fdr": 1e-6},
                }
            ],
        ), patch(
            "prioritx_graph.service._score_pathway_overlap",
            side_effect=PATHWAY_SCORES,
        ), patch(
            "prioritx_graph.service.load_mechanistic_edges",
            return_value=[],
        ):
            ranked = graph_augmented_target_evidence("ipf_tnik", candidate_limit=2, genetics_size=0)

        self.assertEqual("TNIK", ranked[0]["gene_symbol"])
        self.assertEqual("graph_augmented_target_evidence_score", ranked[0]["score_name"])

    def test_evaluates_graph_augmented_benchmark(self) -> None:
        with patch("prioritx_graph.service.fused_target_evidence", return_value=CORE_RANKED), patch(
            "prioritx_graph.service.load_reactome_membership_cache",
            return_value={"TNIK": [], "MUC5B": []},
        ), patch(
            "prioritx_graph.service.load_reactome_pathway_enrichment",
            return_value=[
                {
                    "pathway": {"st_id": "R-HSA-1", "name": "Fibrosis pathway", "species_name": "Homo sapiens"},
                    "statistics": {"fdr": 1e-6},
                }
            ],
        ), patch(
            "prioritx_graph.service._score_pathway_overlap",
            side_effect=PATHWAY_SCORES,
        ), patch(
            "prioritx_graph.service.load_mechanistic_edges",
            return_value=[],
        ):
            result = evaluate_graph_augmented_benchmark("ipf_tnik", candidate_limit=2, genetics_size=0)

        self.assertEqual(1, result["metrics"]["best_rank"])
        self.assertTrue(result["items"][0]["found"])

    def test_uses_cache_for_gene_pathways_when_available(self) -> None:
        with patch("prioritx_graph.service.fused_target_evidence", return_value=CORE_RANKED), patch(
            "prioritx_graph.service.load_reactome_membership_cache",
            return_value={"TNIK": [{"pathway": {"st_id": "R-HSA-1"}}], "MUC5B": []},
        ), patch(
            "prioritx_graph.service.load_reactome_pathway_enrichment",
            return_value=[
                {
                    "pathway": {"st_id": "R-HSA-1", "name": "Fibrosis pathway", "species_name": "Homo sapiens"},
                    "statistics": {"fdr": 1e-6},
                }
            ],
        ), patch(
            "prioritx_graph.service._score_pathway_overlap",
            side_effect=PATHWAY_SCORES,
        ), patch(
            "prioritx_graph.service.load_mechanistic_edges",
            return_value=[],
        ), patch(
            "prioritx_graph.service.load_reactome_gene_pathways",
        ) as load_gene_pathways, patch(
            "prioritx_graph.service.save_reactome_membership_cache",
        ) as save_cache:
            build_benchmark_knowledge_graph("ipf_tnik", candidate_limit=1, genetics_size=0)

        load_gene_pathways.assert_not_called()
        save_cache.assert_not_called()

    def test_falls_back_to_live_gene_membership_and_persists_cache(self) -> None:
        with patch("prioritx_graph.service.fused_target_evidence", return_value=CORE_RANKED[:1]), patch(
            "prioritx_graph.service.load_reactome_membership_cache",
            return_value={},
        ), patch(
            "prioritx_graph.service.load_reactome_pathway_enrichment",
            return_value=[
                {
                    "pathway": {"st_id": "R-HSA-1", "name": "Fibrosis pathway", "species_name": "Homo sapiens"},
                    "statistics": {"fdr": 1e-6},
                }
            ],
        ), patch(
            "prioritx_graph.service._score_pathway_overlap",
            return_value=PATHWAY_SCORES[0],
        ), patch(
            "prioritx_graph.service.load_mechanistic_edges",
            return_value=[],
        ), patch(
            "prioritx_graph.service.load_reactome_gene_pathways",
            return_value=[{"pathway": {"st_id": "R-HSA-1"}}],
        ) as load_gene_pathways, patch(
            "prioritx_graph.service.save_reactome_membership_cache",
        ) as save_cache:
            build_benchmark_knowledge_graph("ipf_tnik", candidate_limit=1, genetics_size=0)

        load_gene_pathways.assert_called_once_with("TNIK")
        save_cache.assert_called_once()

    def test_exploratory_mechanistic_edges_can_raise_tnik(self) -> None:
        with patch("prioritx_graph.service.fused_target_evidence", return_value=CORE_RANKED), patch(
            "prioritx_graph.service.load_reactome_pathway_enrichment",
            return_value=[],
        ), patch(
            "prioritx_graph.service.load_reactome_membership_cache",
            return_value={},
        ), patch(
            "prioritx_graph.service.load_mechanistic_edges",
            return_value=MECHANISTIC_EDGES,
        ):
            ranked = graph_augmented_target_evidence("ipf_tnik", mode="exploratory", candidate_limit=2, genetics_size=0)

        self.assertEqual("TNIK", ranked[0]["gene_symbol"])
        self.assertGreater(ranked[0]["graph_score"], ranked[1]["graph_score"])


if __name__ == "__main__":
    unittest.main()
