from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from prioritx_data.hgnc import load_hgnc_symbol_map, parse_hgnc_complete_set


class HgncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "hgnc" / "hgnc_complete_set_minimal.txt"

    def test_parses_approved_hgnc_rows(self) -> None:
        mapping = parse_hgnc_complete_set(self.fixture_path.read_text())
        self.assertEqual("A1BG", mapping.ensembl_to_gene["ENSG00000121410"]["symbol"])
        self.assertEqual("HGNC:2", mapping.ensembl_to_gene["ENSG00000175899"]["hgnc_id"])
        self.assertNotIn("ENSG00000999999", mapping.ensembl_to_gene)
        self.assertEqual("ENSG00000121410", mapping.symbol_to_gene["A1BG"]["ensembl_gene_id"])

    def test_loads_hgnc_symbol_map_with_cache_loader(self) -> None:
        fixture_text = self.fixture_path.read_text()
        with patch("prioritx_data.hgnc.load_text_with_cache", return_value=fixture_text):
            mapping = load_hgnc_symbol_map()
        self.assertEqual("A1BG", mapping["ENSG00000121410"]["symbol"])


if __name__ == "__main__":
    unittest.main()
