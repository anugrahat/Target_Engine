from __future__ import annotations

import unittest
from unittest.mock import patch

from prioritx_data.pubmed import load_pubmed_gene_support, pubmed_query_for_gene
from prioritx_features.literature import derive_pubmed_literature_features
from prioritx_rank.baseline import score_pubmed_literature_support


class PubMedTests(unittest.TestCase):
    def test_builds_pubmed_query_with_aliases(self) -> None:
        with patch(
            "prioritx_data.pubmed._ensembl_symbol_terms",
            return_value={"ENSG00000156345": ("CCRK", "CDK20", "p42")},
        ):
            query = pubmed_query_for_gene("hcc_cdk20", gene_symbol="CDK20", ensembl_gene_id="ENSG00000156345")
        self.assertIn("CDK20[Title/Abstract]", query)
        self.assertIn("CCRK[Title/Abstract]", query)
        self.assertIn('"hepatocellular carcinoma"[Title/Abstract]', query)

    def test_loads_pubmed_gene_support_with_patched_responses(self) -> None:
        esearch = {"esearchresult": {"count": "7", "idlist": ["1", "2"]}}
        esummary = {
            "result": {
                "uids": ["1", "2"],
                "1": {"title": "Paper 1", "pubdate": "2024", "source": "Nature"},
                "2": {"title": "Paper 2", "pubdate": "2023", "source": "Cell"},
            }
        }
        load_pubmed_gene_support.cache_clear()
        with patch(
            "prioritx_data.pubmed.load_json_with_cache",
            side_effect=[esearch, esummary],
        ), patch(
            "prioritx_data.pubmed._ensembl_symbol_terms",
            return_value={"ENSG00000156345": ("CCRK", "CDK20")},
        ):
            record = load_pubmed_gene_support("hcc_cdk20", "CDK20", "ENSG00000156345")

        self.assertEqual(7, record["statistics"]["pubmed_count"])
        self.assertEqual(2, len(record["top_hits"]))
        self.assertEqual("pubmed_literature_support", record["evidence_kind"])

    def test_scores_pubmed_support(self) -> None:
        record = {
            "benchmark_id": "ipf_tnik",
            "gene": {"ensembl_gene_id": "ENSG00000154310", "symbol": "TNIK"},
            "statistics": {"pubmed_count": 7},
            "top_hits": [{"pmid": "1", "title": "Paper"}],
            "evidence_kind": "pubmed_literature_support",
        }
        scored = score_pubmed_literature_support(derive_pubmed_literature_features(record))
        self.assertEqual("pubmed_literature_support_score", scored["score_name"])
        self.assertGreater(scored["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
