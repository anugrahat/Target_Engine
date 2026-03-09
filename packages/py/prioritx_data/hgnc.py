"""HGNC-backed gene identifier mapping."""

from __future__ import annotations

import csv

from prioritx_data.remote_cache import load_text_with_cache

HGNC_COMPLETE_SET_URL = "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt"


def parse_hgnc_complete_set(text: str) -> dict[str, dict[str, str]]:
    """Parse approved HGNC rows keyed by Ensembl gene id."""
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    mapping: dict[str, dict[str, str]] = {}
    for row in reader:
        ensembl_gene_id = (row.get("ensembl_gene_id") or "").strip()
        symbol = (row.get("symbol") or "").strip()
        hgnc_id = (row.get("hgnc_id") or "").strip()
        status = (row.get("status") or "").strip()
        if not ensembl_gene_id or not symbol or not hgnc_id:
            continue
        if status != "Approved":
            continue
        mapping[ensembl_gene_id] = {
            "symbol": symbol,
            "hgnc_id": hgnc_id,
        }
    return mapping


def load_hgnc_symbol_map() -> dict[str, dict[str, str]]:
    """Load the HGNC complete-set symbol map with local caching."""
    text = load_text_with_cache(HGNC_COMPLETE_SET_URL, namespace="hgnc_cache")
    return parse_hgnc_complete_set(text)
