"""HGNC-backed gene identifier mapping."""

from __future__ import annotations

import csv
from dataclasses import dataclass

from prioritx_data.remote_cache import load_text_with_cache

HGNC_COMPLETE_SET_URL = "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt"


@dataclass(frozen=True)
class HgncMaps:
    """Approved HGNC mappings in both Ensembl- and symbol-keyed forms."""

    ensembl_to_gene: dict[str, dict[str, str]]
    symbol_to_gene: dict[str, dict[str, str]]


def parse_hgnc_complete_set(text: str) -> HgncMaps:
    """Parse approved HGNC rows into Ensembl- and symbol-keyed maps."""
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    ensembl_to_gene: dict[str, dict[str, str]] = {}
    symbol_to_gene: dict[str, dict[str, str]] = {}
    for row in reader:
        ensembl_gene_id = (row.get("ensembl_gene_id") or "").strip()
        symbol = (row.get("symbol") or "").strip()
        hgnc_id = (row.get("hgnc_id") or "").strip()
        status = (row.get("status") or "").strip()
        if not ensembl_gene_id or not symbol or not hgnc_id:
            continue
        if status != "Approved":
            continue
        gene = {
            "symbol": symbol,
            "hgnc_id": hgnc_id,
            "ensembl_gene_id": ensembl_gene_id,
        }
        ensembl_to_gene[ensembl_gene_id] = gene
        symbol_to_gene[symbol] = gene
    return HgncMaps(ensembl_to_gene=ensembl_to_gene, symbol_to_gene=symbol_to_gene)


def load_hgnc_symbol_map() -> dict[str, dict[str, str]]:
    """Load the HGNC complete-set symbol map with local caching."""
    text = load_text_with_cache(HGNC_COMPLETE_SET_URL, namespace="hgnc_cache")
    return parse_hgnc_complete_set(text).ensembl_to_gene


def load_hgnc_symbol_reverse_map() -> dict[str, dict[str, str]]:
    """Load the HGNC complete-set reverse map keyed by approved symbol."""
    text = load_text_with_cache(HGNC_COMPLETE_SET_URL, namespace="hgnc_cache")
    return parse_hgnc_complete_set(text).symbol_to_gene
