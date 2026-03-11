from __future__ import annotations

import unittest
from unittest.mock import patch

from prioritx_data.service import string_network_scores


class StringNetworkTests(unittest.TestCase):
    def test_scores_string_network_support(self) -> None:
        string_map = {
            "GENE1": {"string_id": "9606.ENSP1", "preferred_name": "GENE1"},
            "GENE2": {"string_id": "9606.ENSP2", "preferred_name": "GENE2"},
        }
        edges = [
            {
                "stringId_A": "9606.ENSP1",
                "stringId_B": "9606.ENSP2",
                "preferredName_A": "GENE1",
                "preferredName_B": "GENE2",
                "score": 0.92,
            },
            {
                "stringId_A": "9606.ENSP2",
                "stringId_B": "9606.ENSP1",
                "preferredName_A": "GENE2",
                "preferredName_B": "GENE1",
                "score": 0.92,
            },
        ]
        with patch("prioritx_data.service.load_string_id_map", return_value=string_map), patch(
            "prioritx_data.service.load_string_network_edges",
            return_value=edges,
        ):
            items = string_network_scores(
                benchmark_id="ipf_tnik",
                subset_id="ipf_lung_core",
                candidate_gene_map={"GENE1": "ENSG000001", "GENE2": "ENSG000002"},
                seed_symbols=["GENE1"],
            )

        self.assertEqual(2, len(items))
        self.assertEqual("string_network_support_score", items[0]["score_name"])
        self.assertGreater(items[0]["score"], 0.0)

    def test_uses_string_id_partner_mapping_when_preferred_name_differs(self) -> None:
        string_map = {
            "GENE1": {"string_id": "9606.ENSP1", "preferred_name": "GENE1"},
            "GENE2": {"string_id": "9606.ENSP2", "preferred_name": "ALIAS2"},
        }
        edges = [
            {
                "stringId_A": "9606.ENSP1",
                "stringId_B": "9606.ENSP2",
                "preferredName_A": "GENE1",
                "preferredName_B": "ALIAS2",
                "score": 0.81,
            }
        ]
        with patch("prioritx_data.service.load_string_id_map", return_value=string_map), patch(
            "prioritx_data.service.load_string_network_edges",
            return_value=edges,
        ):
            items = string_network_scores(
                benchmark_id="ipf_tnik",
                subset_id="ipf_lung_core",
                candidate_gene_map={"GENE1": "ENSG000001", "GENE2": "ENSG000002"},
                seed_symbols=["GENE1"],
            )

        gene1 = next(item for item in items if item["gene_symbol"] == "GENE1")
        self.assertEqual(1, gene1["partner_count"])
        self.assertEqual("GENE2", gene1["top_partners"][0]["partner_symbol"])


if __name__ == "__main__":
    unittest.main()
