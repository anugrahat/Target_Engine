"""CLI for source-backed benchmark target evaluation."""

from __future__ import annotations

from prioritx_eval.assertions import list_benchmark_assertion_ids
from prioritx_eval.service import evaluate_fused_benchmark


def main() -> int:
    print("Benchmark target evaluation:")
    for benchmark_id in list_benchmark_assertion_ids():
        result = evaluate_fused_benchmark(benchmark_id)
        metric = result["metrics"]
        print(
            f"- {benchmark_id}: found {result['positive_targets_found']}/{result['positive_target_count']} "
            f"positives, best_rank={metric['best_rank']}, hit@10={metric['hit_at_10']}, MRR={metric['mean_reciprocal_rank']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
