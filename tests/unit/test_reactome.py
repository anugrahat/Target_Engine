from __future__ import annotations

import unittest
from urllib.error import HTTPError
from unittest.mock import patch

from prioritx_data.reactome import load_reactome_gene_pathways, load_reactome_pathway_enrichment
from prioritx_features.pathway import derive_reactome_pathway_features
from prioritx_rank.baseline import score_reactome_pathway_support


class ReactomeTests(unittest.TestCase):
    def test_loads_pathway_enrichment_with_patched_response(self) -> None:
        payload = {
            "pathways": [
                {
                    "stId": "R-HSA-1",
                    "dbId": 1,
                    "name": "Cell Cycle",
                    "species": {"name": "Homo sapiens", "taxId": "9606"},
                    "entities": {
                        "found": 12,
                        "total": 100,
                        "ratio": 0.12,
                        "pValue": 1e-6,
                        "fdr": 1e-4,
                    },
                }
            ]
        }
        load_reactome_pathway_enrichment.cache_clear()
        with patch("prioritx_data.reactome.load_json_text_post_with_cache", return_value=payload):
            items = load_reactome_pathway_enrichment(("GENE1", "GENE2"))

        self.assertEqual(1, len(items))
        self.assertEqual("R-HSA-1", items[0]["pathway"]["st_id"])
        self.assertEqual("reactome_pathway_enrichment", items[0]["evidence_kind"])

    def test_loads_gene_pathways_with_patched_response(self) -> None:
        payload = {
            "pathways": [
                {
                    "stId": "R-HSA-2",
                    "dbId": 2,
                    "name": "Mitotic G1 phase",
                    "species": {"name": "Homo sapiens", "taxId": "9606"},
                    "entities": {
                        "found": 1,
                        "total": 33,
                        "ratio": 0.03,
                        "pValue": 0.01,
                        "fdr": 0.02,
                    },
                }
            ]
        }
        load_reactome_gene_pathways.cache_clear()
        with patch("prioritx_data.reactome.load_json_text_post_with_cache", return_value=payload):
            items = load_reactome_gene_pathways("CDK20")

        self.assertEqual(1, len(items))
        self.assertEqual("reactome_gene_membership", items[0]["evidence_kind"])

    def test_gene_pathway_lookup_gracefully_handles_http_error(self) -> None:
        load_reactome_gene_pathways.cache_clear()
        with patch(
            "prioritx_data.reactome.load_json_text_post_with_cache",
            side_effect=HTTPError("https://reactome.org", 500, "boom", hdrs=None, fp=None),
        ):
            items = load_reactome_gene_pathways("TNIK")
        self.assertEqual([], items)

    def test_scores_reactome_pathway_overlap(self) -> None:
        enriched = [
            {
                "pathway": {"st_id": "R-HSA-1", "name": "Cell Cycle"},
                "statistics": {"fdr": 1e-4},
            },
            {
                "pathway": {"st_id": "R-HSA-2", "name": "M Phase"},
                "statistics": {"fdr": 1e-3},
            },
        ]
        gene_pathways = [
            {
                "pathway": {"st_id": "R-HSA-2", "name": "M Phase"},
                "statistics": {"fdr": 0.02},
            },
            {
                "pathway": {"st_id": "R-HSA-9", "name": "Other"},
                "statistics": {"fdr": 0.5},
            },
        ]
        features = derive_reactome_pathway_features(
            benchmark_id="hcc_cdk20",
            subset_id="hcc_adult_extended",
            gene={"ensembl_gene_id": "ENSG00000156345", "gene_symbol": "CDK20"},
            enriched_pathways=enriched,
            gene_pathways=gene_pathways,
            enrichment_gene_count=120,
            enrichment_fdr_max=0.05,
        )
        scored = score_reactome_pathway_support(features)
        self.assertEqual("reactome_pathway_support_score", scored["score_name"])
        self.assertGreater(scored["score"], 0.0)
        self.assertEqual(1, scored["overlap_count"])


if __name__ == "__main__":
    unittest.main()
