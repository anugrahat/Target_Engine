"""Load source-backed PubMed disease-gene literature support."""

from __future__ import annotations

import functools
import urllib.parse
from typing import Any

from prioritx_data.hgnc import parse_hgnc_complete_set
from prioritx_data.remote_cache import load_json_with_cache, load_text_with_cache

PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
HGNC_COMPLETE_SET_URL = "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt"

BENCHMARK_DISEASE_TERMS: dict[str, tuple[str, ...]] = {
    "ipf_tnik": ("idiopathic pulmonary fibrosis", "IPF"),
    "hcc_cdk20": ("hepatocellular carcinoma", "HCC"),
    "als": ("amyotrophic lateral sclerosis", "ALS"),
    "ad_phase_separation": ("Alzheimer disease", "Alzheimer's disease", "AD"),
}


def _url(url: str, params: dict[str, object]) -> str:
    return f"{url}?{urllib.parse.urlencode(params)}"


def _quoted_or_term(terms: tuple[str, ...]) -> str:
    return " OR ".join(f'"{term}"[Title/Abstract]' for term in terms if term)


@functools.lru_cache(maxsize=1)
def _ensembl_symbol_terms() -> dict[str, tuple[str, ...]]:
    text = load_text_with_cache(HGNC_COMPLETE_SET_URL, namespace="hgnc_cache")
    maps = parse_hgnc_complete_set(text)
    grouped: dict[str, set[str]] = {}
    for gene in maps.symbol_to_gene.values():
        grouped.setdefault(gene["ensembl_gene_id"], set()).add(gene["matched_symbol"])
        grouped[gene["ensembl_gene_id"]].add(gene["symbol"])
    return {
        ensembl_gene_id: tuple(sorted(symbols))
        for ensembl_gene_id, symbols in grouped.items()
    }


def pubmed_query_for_gene(benchmark_id: str, *, gene_symbol: str, ensembl_gene_id: str | None = None) -> str:
    """Build the disease-gene PubMed query used for literature support."""
    disease_terms = BENCHMARK_DISEASE_TERMS.get(benchmark_id)
    if not disease_terms:
        raise ValueError(f"Unsupported benchmark for PubMed support: {benchmark_id}")
    symbol_terms = [gene_symbol]
    if ensembl_gene_id:
        symbol_terms = list(_ensembl_symbol_terms().get(ensembl_gene_id, (gene_symbol,)))
    gene_clause = "(" + " OR ".join(f"{term}[Title/Abstract]" for term in sorted(set(symbol_terms))) + ")"
    disease_clause = "(" + _quoted_or_term(disease_terms) + ")"
    return f"{gene_clause} AND {disease_clause}"


@functools.lru_cache(maxsize=1024)
def load_pubmed_gene_support(benchmark_id: str, gene_symbol: str, ensembl_gene_id: str | None = None) -> dict[str, Any]:
    """Load PubMed count plus top summaries for one disease-gene query."""
    query = pubmed_query_for_gene(benchmark_id, gene_symbol=gene_symbol, ensembl_gene_id=ensembl_gene_id)
    search = load_json_with_cache(
        _url(
            PUBMED_ESEARCH_URL,
            {
                "db": "pubmed",
                "retmode": "json",
                "retmax": 5,
                "sort": "relevance",
                "term": query,
            },
        ),
        namespace="pubmed_cache",
    )
    esearch = (search or {}).get("esearchresult") or {}
    ids = list(esearch.get("idlist") or [])
    count = int(esearch.get("count") or 0)
    summaries: list[dict[str, Any]] = []
    if ids:
        summary = load_json_with_cache(
            _url(
                PUBMED_ESUMMARY_URL,
                {
                    "db": "pubmed",
                    "retmode": "json",
                    "id": ",".join(ids),
                },
            ),
            namespace="pubmed_cache",
        )
        result = (summary or {}).get("result") or {}
        for pmid in ids:
            item = result.get(pmid) or {}
            summaries.append(
                {
                    "pmid": pmid,
                    "title": item.get("title"),
                    "pubdate": item.get("pubdate"),
                    "source": item.get("source"),
                }
            )
    return {
        "schema_version": "0.1.0",
        "evidence_kind": "pubmed_literature_support",
        "benchmark_id": benchmark_id,
        "gene": {
            "ensembl_gene_id": ensembl_gene_id,
            "symbol": gene_symbol,
        },
        "statistics": {
            "pubmed_count": count,
        },
        "top_hits": summaries,
        "provenance": {
            "source_kind": "ncbi_eutils",
            "query": query,
            "esearch_url": PUBMED_ESEARCH_URL,
            "esummary_url": PUBMED_ESUMMARY_URL,
            "query_gene_terms": sorted(set(_ensembl_symbol_terms().get(ensembl_gene_id or "", (gene_symbol,)))),
            "query_disease_terms": list(BENCHMARK_DISEASE_TERMS[benchmark_id]),
        },
    }
