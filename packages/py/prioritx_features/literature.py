"""Feature derivation for disease-gene literature support."""

from __future__ import annotations

import math
from typing import Any


def derive_pubmed_literature_features(record: dict[str, Any]) -> dict[str, Any]:
    """Derive transparent features from PubMed disease-gene support."""
    count = int(record["statistics"]["pubmed_count"])
    top_hits = record.get("top_hits") or []
    return {
        "benchmark_id": record["benchmark_id"],
        "ensembl_gene_id": record["gene"].get("ensembl_gene_id"),
        "gene_symbol": record["gene"].get("symbol"),
        "pubmed_count": count,
        "log_count": round(math.log10(count + 1), 6),
        "top_hit_count": len(top_hits),
        "top_hits": top_hits,
        "evidence_kind": record["evidence_kind"],
    }
