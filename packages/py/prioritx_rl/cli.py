"""CLI for offline RL benchmark replay."""

from __future__ import annotations

import argparse
import json

from prioritx_rl.service import evaluate_bandit_agents


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-ids", nargs="+", help="Optional benchmark IDs to replay.")
    parser.add_argument("--candidate-limit", type=int, default=500, help="Maximum ranked candidates exposed to the agent.")
    parser.add_argument("--horizon", type=int, default=25, help="Maximum picks per episode.")
    parser.add_argument("--episodes", type=int, default=10, help="Repeated replay passes over the benchmark contexts.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for replay order and the random baseline.")
    parser.add_argument("--genetics-size", type=int, default=0, help="Open Targets genetics slice used when building bandit contexts.")
    parser.add_argument("--tractability-top-n", type=int, default=0, help="Tractability rerank slice used when building bandit contexts.")
    parser.add_argument("--pathway-top-n", type=int, default=0, help="Reactome rerank slice used when building bandit contexts.")
    parser.add_argument("--network-top-n", type=int, default=0, help="STRING rerank slice used when building bandit contexts.")
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=("strict", "exploratory"),
        default=["strict", "exploratory"],
        help="Benchmark modes to replay.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    payload = evaluate_bandit_agents(
        benchmark_ids=args.benchmark_ids,
        modes=args.modes,
        candidate_limit=args.candidate_limit,
        horizon=args.horizon,
        episodes=args.episodes,
        seed=args.seed,
        genetics_size=args.genetics_size,
        tractability_top_n=args.tractability_top_n,
        pathway_top_n=args.pathway_top_n,
        network_top_n=args.network_top_n,
    )
    print("PrioriTx offline RL benchmark replay:")
    for agent in payload["agents"]:
        metrics = agent["metrics"]
        print(
            f"- {agent['agent_name']}: hit_rate={metrics['hit_rate']}, "
            f"MRR={metrics['mean_reciprocal_first_positive_step']}, "
            f"coverage={metrics['candidate_pool_positive_coverage_rate']}"
        )
    print(json.dumps({"scientific_caveats": payload["scientific_caveats"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
