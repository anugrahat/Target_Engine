from __future__ import annotations

import unittest
from unittest.mock import patch

from prioritx_data.proteophospho import load_benchmark_proteophospho_statistics
from prioritx_graph.service import proteophospho_program_activity_scores


PROTEIN_TUMOR = "idx\tT1\tT2\tT3\nENSGCTNNB1.1\t3.0\t3.2\t3.1\nENSGSTAT3.1\t4.0\t4.2\t4.1\n"
PROTEIN_NORMAL = "idx\tN1\tN2\tN3\nENSGCTNNB1.1\t2.0\t2.1\t2.2\nENSGSTAT3.1\t3.2\t3.1\t3.3\n"
PHOSPHO_TUMOR = "idx\tT1\tT2\tT3\nENSGCTNNB1.1|ENSP1|S675|PEPTIDE|1\t2.5\t2.6\t2.4\nENSGSTAT3.1|ENSP2|Y705|PEPTIDE|1\t3.5\t3.4\t3.6\n"
PHOSPHO_NORMAL = "idx\tN1\tN2\tN3\nENSGCTNNB1.1|ENSP1|S675|PEPTIDE|1\t1.0\t1.1\t1.2\nENSGSTAT3.1|ENSP2|Y705|PEPTIDE|1\t2.8\t2.7\t2.9\n"

PROGRAMS = [
    {
        "ref": "beta_catenin_signaling",
        "label": "Beta-catenin signaling",
        "linked_targets": ["CDK20"],
        "protein_markers": [{"gene_symbol": "CTNNB1", "expected_direction": "up"}],
        "phosphosite_markers": [{"gene_symbol": "CTNNB1", "site": "S675", "expected_direction": "up"}],
        "sources": [],
    },
    {
        "ref": "il6_pmn_mdsc_program",
        "label": "IL-6 / STAT3",
        "linked_targets": ["CDK20"],
        "protein_markers": [{"gene_symbol": "STAT3", "expected_direction": "up"}],
        "phosphosite_markers": [{"gene_symbol": "STAT3", "site": "Y705", "expected_direction": "up"}],
        "sources": [],
    },
]

REVERSE_MAP = {
    "CTNNB1": {"symbol": "CTNNB1", "ensembl_gene_id": "ENSGCTNNB1"},
    "STAT3": {"symbol": "STAT3", "ensembl_gene_id": "ENSGSTAT3"},
}


class ProteophosphoTests(unittest.TestCase):
    def setUp(self) -> None:
        load_benchmark_proteophospho_statistics.cache_clear()

    def tearDown(self) -> None:
        load_benchmark_proteophospho_statistics.cache_clear()

    def test_loads_selected_marker_statistics(self) -> None:
        member_texts = {
            "copheemap_hcc/HCC_proteomics_gene_abundance_log2_reference_intensity_normalized_Tumor.txt": PROTEIN_TUMOR,
            "copheemap_hcc/HCC_proteomics_gene_abundance_log2_reference_intensity_normalized_Normal.txt": PROTEIN_NORMAL,
            "copheemap_hcc/HCC_phospho_site_abundance_log2_reference_intensity_normalized_Tumor.txt": PHOSPHO_TUMOR,
            "copheemap_hcc/HCC_phospho_site_abundance_log2_reference_intensity_normalized_Normal.txt": PHOSPHO_NORMAL,
        }
        with patch("prioritx_data.proteophospho.load_proteophospho_programs", return_value=PROGRAMS), patch(
            "prioritx_data.proteophospho.load_hgnc_symbol_reverse_map",
            return_value=REVERSE_MAP,
        ), patch(
            "prioritx_data.proteophospho._extract_member_text",
            side_effect=lambda name: member_texts[name],
        ):
            payload = load_benchmark_proteophospho_statistics("hcc_cdk20")

        self.assertIn("CTNNB1", payload["protein_markers"])
        self.assertIn("CTNNB1:S675", payload["phosphosite_markers"])
        self.assertTrue(payload["protein_markers"]["CTNNB1"]["directionally_supported"])

    def test_scores_program_activity_from_supported_markers(self) -> None:
        mocked_stats = {
            "protein_markers": {
                "CTNNB1": {
                    "marker_kind": "protein",
                    "marker_ref": "CTNNB1",
                    "gene_symbol": "CTNNB1",
                    "score": 0.8,
                    "mean_difference": 1.0,
                    "statistics": {"adjusted_p_value": 0.001},
                    "directionally_supported": True,
                }
            },
            "phosphosite_markers": {
                "CTNNB1:S675": {
                    "marker_kind": "phosphosite",
                    "marker_ref": "CTNNB1:S675",
                    "gene_symbol": "CTNNB1",
                    "site": "S675",
                    "score": 0.9,
                    "mean_difference": 1.2,
                    "statistics": {"adjusted_p_value": 0.0001},
                    "directionally_supported": True,
                }
            },
        }
        with patch("prioritx_graph.service.load_proteophospho_programs", return_value=[PROGRAMS[0]]), patch(
            "prioritx_graph.service.load_benchmark_proteophospho_statistics",
            return_value=mocked_stats,
        ):
            items = proteophospho_program_activity_scores("hcc_cdk20", subset_id="hcc_adult_extended")

        self.assertEqual(1, len(items))
        self.assertEqual("proteophospho_program_activity_score", items[0]["score_name"])
        self.assertGreater(items[0]["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
