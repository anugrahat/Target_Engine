from __future__ import annotations

import unittest

from prioritx_data.transcriptomics import list_fixture_contrast_ids, load_transcriptomics_fixture


class TranscriptomicsLoaderTests(unittest.TestCase):
    def test_lists_fixture_contrasts(self) -> None:
        fixture_ids = list_fixture_contrast_ids()
        self.assertEqual({"hcc_adult_core_gse77314", "ipf_lung_core_gse92592"}, set(fixture_ids))

    def test_loads_fixture_records(self) -> None:
        records = load_transcriptomics_fixture("ipf_lung_core_gse92592")
        self.assertEqual(5, len(records))
        self.assertEqual("illustrative_fixture", records[0]["fixture_status"])


if __name__ == "__main__":
    unittest.main()
