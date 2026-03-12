"""Service layer for offline RL benchmark evaluation."""

from __future__ import annotations

import random
from typing import Any

from prioritx_data.service import fused_target_evidence
from prioritx_eval.assertions import list_benchmark_assertion_ids, load_benchmark_assertion
from prioritx_eval.policy import benchmark_mode_config
from prioritx_rl.agents import FusedGreedyAgent, LinearUCBAgent, RandomAgent
from prioritx_rl.env import BenchmarkBanditContext, TargetCandidate, run_episode


def _bounded_support(value: int) -> float:
    return min(max(value, 0) / 5.0, 1.0)


def _candidate_feature_vector(item: dict[str, Any]) -> tuple[float, ...]:
    return (
        float(item["score"]),
        float(item["components"]["transcriptomics_component"]),
        float(item["components"]["genetics_component"]),
        float(item["components"]["tractability_component"]),
        float(item["components"]["pathway_component"]),
        float(item["components"]["network_component"]),
        _bounded_support(int(item["transcriptomics_supporting_contrasts"])),
        1.0 if item["transcriptomics_available"] else 0.0,
        1.0 if item["genetics_available"] else 0.0,
        1.0 if item["tractability_available"] else 0.0,
        1.0 if item["pathway_available"] else 0.0,
        -1.0 if item["transcriptomics_direction_conflict"] else 0.0,
    )


def _build_candidate(item: dict[str, Any], *, benchmark_id: str, mode: str, subset_id: str, rank: int) -> TargetCandidate:
    return TargetCandidate(
        benchmark_id=benchmark_id,
        mode=mode,
        subset_id=subset_id,
        rank=rank,
        gene_symbol=item["gene_symbol"],
        ensembl_gene_id=item.get("ensembl_gene_id"),
        fused_score=float(item["score"]),
        feature_vector=_candidate_feature_vector(item),
        transcriptomics_score=float(item["components"]["transcriptomics_component"]),
        genetics_score=float(item["components"]["genetics_component"]),
        tractability_score=float(item["components"]["tractability_component"]),
        pathway_score=float(item["components"]["pathway_component"]),
        network_score=float(item["components"]["network_component"]),
        transcriptomics_supporting_contrasts=int(item["transcriptomics_supporting_contrasts"]),
        transcriptomics_available=bool(item["transcriptomics_available"]),
        genetics_available=bool(item["genetics_available"]),
        tractability_available=bool(item["tractability_available"]),
        pathway_available=bool(item["pathway_available"]),
        network_available=bool(item["network_available"]),
        transcriptomics_direction_conflict=bool(item["transcriptomics_direction_conflict"]),
    )


def build_bandit_contexts(
    *,
    benchmark_ids: list[str] | None = None,
    modes: list[str] | None = None,
    candidate_limit: int = 500,
    genetics_size: int = 0,
    tractability_top_n: int = 0,
    pathway_top_n: int = 0,
    network_top_n: int = 0,
) -> list[BenchmarkBanditContext]:
    """Build non-leaky benchmark contexts from the current fused evidence stack."""
    chosen_benchmarks = benchmark_ids or list_benchmark_assertion_ids()
    chosen_modes = modes or ["strict", "exploratory"]
    contexts: list[BenchmarkBanditContext] = []

    for benchmark_id in chosen_benchmarks:
        assertion = load_benchmark_assertion(benchmark_id)
        positive_symbols = tuple(
            sorted(
                target["gene_symbol"]
                for target in assertion["target_assertions"]
                if target["assertion_kind"] == "source_backed_positive_target"
            )
        )
        for mode in chosen_modes:
            mode_config = benchmark_mode_config(benchmark_id, mode=mode)
            ranked = fused_target_evidence(
                benchmark_id=benchmark_id,
                subset_id=mode_config["subset_id"],
                genetics_size=genetics_size,
                tractability_top_n=tractability_top_n,
                pathway_top_n=pathway_top_n,
                network_top_n=network_top_n,
            )
            limited = ranked[: max(candidate_limit, 0)]
            contexts.append(
                BenchmarkBanditContext(
                    benchmark_id=benchmark_id,
                    indication_name=assertion["indication_name"],
                    mode=mode,
                    subset_id=mode_config["subset_id"],
                    positive_gene_symbols=positive_symbols,
                    candidate_pool=tuple(
                        _build_candidate(
                            item,
                            benchmark_id=benchmark_id,
                            mode=mode,
                            subset_id=mode_config["subset_id"],
                            rank=index + 1,
                        )
                        for index, item in enumerate(limited)
                    ),
                    candidate_limit=candidate_limit,
                )
            )
    return contexts


def _agent_factories(seed: int) -> dict[str, Any]:
    return {
        "random": lambda: RandomAgent(seed=seed),
        "fused_greedy": FusedGreedyAgent,
        "linear_ucb": LinearUCBAgent,
    }


def _aggregate_metrics(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    if not episodes:
        return {
            "episode_count": 0,
            "hit_rate": 0.0,
            "mean_total_reward": 0.0,
            "mean_reciprocal_first_positive_step": 0.0,
            "candidate_pool_positive_coverage_rate": 0.0,
        }
    episode_count = len(episodes)
    hit_count = sum(1 for item in episodes if item["metrics"]["hit_at_horizon"])
    total_reward = sum(item["metrics"]["total_reward"] for item in episodes)
    reciprocal = sum(item["metrics"]["reciprocal_first_positive_step"] for item in episodes)
    covered = sum(1 for item in episodes if item["positive_covered_in_candidate_pool"])
    return {
        "episode_count": episode_count,
        "hit_rate": round(hit_count / episode_count, 4),
        "mean_total_reward": round(total_reward / episode_count, 4),
        "mean_reciprocal_first_positive_step": round(reciprocal / episode_count, 4),
        "candidate_pool_positive_coverage_rate": round(covered / episode_count, 4),
    }


def evaluate_bandit_agents(
    *,
    benchmark_ids: list[str] | None = None,
    modes: list[str] | None = None,
    candidate_limit: int = 500,
    horizon: int = 25,
    episodes: int = 10,
    seed: int = 0,
    genetics_size: int = 0,
    tractability_top_n: int = 0,
    pathway_top_n: int = 0,
    network_top_n: int = 0,
) -> dict[str, Any]:
    """Evaluate simple agents on repeated benchmark replay."""
    contexts = build_bandit_contexts(
        benchmark_ids=benchmark_ids,
        modes=modes,
        candidate_limit=candidate_limit,
        genetics_size=genetics_size,
        tractability_top_n=tractability_top_n,
        pathway_top_n=pathway_top_n,
        network_top_n=network_top_n,
    )
    factories = _agent_factories(seed)
    rng = random.Random(seed)
    agent_results = []

    for agent_name, factory in factories.items():
        agent = factory()
        agent_episodes = []
        for episode_index in range(max(episodes, 0)):
            shuffled = list(contexts)
            rng.shuffle(shuffled)
            for context in shuffled:
                result = run_episode(context, agent, horizon=horizon)
                result["episode_index"] = episode_index + 1
                agent_episodes.append(result)
        agent_results.append(
            {
                "agent_name": agent_name,
                "metrics": _aggregate_metrics(agent_episodes),
                "episodes": agent_episodes,
            }
        )

    return {
        "evaluation_kind": "offline_contextual_bandit_replay",
        "benchmark_ids": [context.benchmark_id for context in contexts],
        "modes": sorted({context.mode for context in contexts}),
        "context_count": len(contexts),
        "candidate_limit": candidate_limit,
        "horizon": horizon,
        "episodes": episodes,
        "agents": agent_results,
        "scientific_caveats": [
            "This is repeated in-sample benchmark replay over a very small source-backed benchmark set.",
            "Rewards use source-backed benchmark-positive labels only and exclude downstream validation leakage.",
            "A strong result here would still not establish prospective value; a weak result honestly means the current evidence stack is not yet enough for RL to add value.",
        ],
        "provenance": {
            "reward_definition": "1.0 for source-backed positive target, 0.0 otherwise",
            "candidate_source": "fused_target_evidence",
            "fused_parameters": {
                "genetics_size": genetics_size,
                "tractability_top_n": tractability_top_n,
                "pathway_top_n": pathway_top_n,
                "network_top_n": network_top_n,
            },
        },
    }
