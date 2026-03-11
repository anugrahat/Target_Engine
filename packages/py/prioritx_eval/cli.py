"""CLI for source-backed benchmark target evaluation."""

from __future__ import annotations

import argparse

from prioritx_eval.assertions import list_benchmark_assertion_ids
from prioritx_eval.policy import benchmark_integrity_review
from prioritx_eval.service import audit_target_evidence, evaluate_fused_benchmark


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=("strict", "exploratory"),
        default=["strict", "exploratory"],
        help="Benchmark policy modes to evaluate.",
    )
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="Skip live target-audit calls to keep verification runs bounded.",
    )
    parser.add_argument(
        "--integrity-only",
        action="store_true",
        help="Only print benchmark integrity review output without live fused evaluation.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    print("Benchmark target evaluation:")
    for benchmark_id in list_benchmark_assertion_ids():
        for mode in args.modes:
            integrity = benchmark_integrity_review(benchmark_id, mode=mode)
            high_risk = [item["family"] for item in integrity["families"] if item["risk_level"] == "high"]
            if args.integrity_only:
                print(
                    f"- {benchmark_id} [{mode}]: integrity subset={integrity['subset_id']}, "
                    f"high_risk={','.join(high_risk) or 'none'}"
                )
                continue
            result = evaluate_fused_benchmark(benchmark_id, mode=mode)
            metric = result["metrics"]
            print(
                f"- {benchmark_id} [{mode}]: found {result['positive_targets_found']}/{result['positive_target_count']} "
                f"positives, best_rank={metric['best_rank']}, hit@10={metric['hit_at_10']}, MRR={metric['mean_reciprocal_rank']}"
            )
            print(f"  integrity subset={integrity['subset_id']}: high_risk={','.join(high_risk) or 'none'}")
            if args.skip_audit:
                continue
            target = result["items"][0]["gene_symbol"]
            audit = audit_target_evidence(benchmark_id, gene_symbol=target, mode=mode)
            support_hits = sum(1 for item in audit["transcriptomics"] if item["passes_support_rule"])
            print(
                f"  target audit {target}: transcriptomics_support_hits={support_hits}, "
                f"genetics_found={audit['open_targets_genetics']['found']}, "
                f"genetics_rank={audit['open_targets_genetics']['association_rank']}, "
                f"fused_found={audit['fused_target_evidence']['found']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
