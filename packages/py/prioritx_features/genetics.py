"""Feature derivation for source-backed genetics evidence."""

from __future__ import annotations

from typing import Any


def derive_open_targets_genetics_features(record: dict[str, Any]) -> dict[str, Any]:
    """Derive transparent features from one Open Targets genetics record."""
    stats = record["statistics"]
    return {
        "benchmark_id": record["benchmark_id"],
        "disease_id": record["disease"]["id"],
        "ensembl_gene_id": record["gene"]["ensembl_gene_id"],
        "gene_symbol": record["gene"]["symbol"],
        "approved_name": record["gene"]["approved_name"],
        "association_score": float(stats["association_score"]),
        "genetic_association_score": float(stats["genetic_association_score"]),
        "genetic_literature_score": float(stats["genetic_literature_score"]),
        "literature_score": float(stats["literature_score"]),
        "evidence_kind": record["evidence_kind"],
    }
