#!/usr/bin/env python3
"""Build a local Reactome gene-membership cache for the current benchmark candidate universe."""

from __future__ import annotations

import argparse

from prioritx_data.reactome import load_reactome_gene_pathways
from prioritx_data.service import fused_target_evidence
from prioritx_eval.assertions import list_benchmark_assertion_ids
from prioritx_eval.policy import benchmark_mode_config
from prioritx_graph.cache import load_reactome_membership_cache, save_reactome_membership_cache


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-limit", type=int, default=800, help="Top core candidates per benchmark-mode slice.")
    parser.add_argument(
        "--benchmark-id",
        action="append",
        dest="benchmark_ids",
        help="Benchmark assertion ID to warm. May be repeated. Defaults to all benchmarks.",
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=("strict", "exploratory"),
        default=["strict", "exploratory"],
        help="Benchmark modes to scan.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    benchmark_ids = sorted(set(args.benchmark_ids or list_benchmark_assertion_ids()))
    candidate_symbols: set[str] = set()
    for benchmark_id in benchmark_ids:
        for mode in args.modes:
            mode_config = benchmark_mode_config(benchmark_id, mode=mode)
            ranked = fused_target_evidence(
                benchmark_id=benchmark_id,
                subset_id=mode_config["subset_id"],
                genetics_size=0,
                tractability_top_n=0,
                pathway_top_n=0,
                network_top_n=0,
            )[: max(args.candidate_limit, 0)]
            candidate_symbols.update(
                item["gene_symbol"]
                for item in ranked
                if item.get("gene_symbol")
            )

    memberships = load_reactome_membership_cache()
    for gene_symbol in sorted(candidate_symbols):
        if gene_symbol not in memberships:
            memberships[gene_symbol] = load_reactome_gene_pathways(gene_symbol)
    path = save_reactome_membership_cache(memberships)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
