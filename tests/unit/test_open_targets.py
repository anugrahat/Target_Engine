from __future__ import annotations

import unittest
from unittest.mock import patch

from prioritx_data.open_targets import load_open_targets_genetics
from prioritx_features.genetics import derive_open_targets_genetics_features
from prioritx_rank.baseline import score_open_targets_genetics


class OpenTargetsTests(unittest.TestCase):
    def test_loads_open_targets_genetics_with_patched_response(self) -> None:
        payload = {
            "data": {
                "disease": {
                    "id": "EFO_0000768",
                    "name": "idiopathic pulmonary fibrosis",
                    "associatedTargets": {
                        "rows": [
                            {
                                "score": 0.82,
                                "target": {
                                    "id": "ENSG000001",
                                    "approvedSymbol": "GENE1",
                                    "approvedName": "Gene one",
                                },
                                "datatypeScores": [
                                    {"id": "genetic_association", "score": 0.91},
                                    {"id": "genetic_literature", "score": 0.4},
                                ],
                            }
                        ]
                    },
                }
            }
        }

        load_open_targets_genetics.cache_clear()
        with patch("prioritx_data.open_targets.load_json_post_with_cache", return_value=payload):
            records = load_open_targets_genetics("ipf_tnik", size=25)

        self.assertEqual(1, len(records))
        self.assertEqual("ENSG000001", records[0]["gene"]["ensembl_gene_id"])
        self.assertEqual(0.91, records[0]["statistics"]["genetic_association_score"])

    def test_scores_open_targets_genetics(self) -> None:
        record = {
            "benchmark_id": "ipf_tnik",
            "disease": {"id": "EFO_0000768"},
            "gene": {
                "ensembl_gene_id": "ENSG000001",
                "symbol": "GENE1",
                "approved_name": "Gene one",
            },
            "statistics": {
                "association_score": 0.82,
                "genetic_association_score": 0.91,
                "genetic_literature_score": 0.4,
                "literature_score": 0.1,
            },
            "evidence_kind": "open_targets_genetics",
        }
        scored = score_open_targets_genetics(derive_open_targets_genetics_features(record))
        self.assertEqual("open_targets_genetics_evidence_score", scored["score_name"])
        self.assertGreater(scored["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
