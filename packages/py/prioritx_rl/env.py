"""Non-leaky offline benchmark environment for PrioriTx target selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TargetCandidate:
    """One target choice exposed to an offline policy."""

    benchmark_id: str
    mode: str
    subset_id: str
    rank: int
    gene_symbol: str
    ensembl_gene_id: str | None
    fused_score: float
    feature_vector: tuple[float, ...]
    transcriptomics_score: float
    genetics_score: float
    tractability_score: float
    pathway_score: float
    network_score: float
    transcriptomics_supporting_contrasts: int
    transcriptomics_available: bool
    genetics_available: bool
    tractability_available: bool
    pathway_available: bool
    network_available: bool
    transcriptomics_direction_conflict: bool


@dataclass(frozen=True)
class BenchmarkBanditContext:
    """Static benchmark slice shown to the policy in one episode."""

    benchmark_id: str
    indication_name: str
    mode: str
    subset_id: str
    positive_gene_symbols: tuple[str, ...]
    candidate_pool: tuple[TargetCandidate, ...]
    candidate_limit: int


@dataclass(frozen=True)
class EpisodeStep:
    """One action taken by a policy in the environment."""

    step_index: int
    gene_symbol: str
    reward: float
    is_positive: bool
    rank: int
    fused_score: float


def reward_for_gene(context: BenchmarkBanditContext, gene_symbol: str) -> float:
    """Return a discovery-time reward using only source-backed benchmark labels."""
    return 1.0 if gene_symbol in context.positive_gene_symbols else 0.0


def run_episode(context: BenchmarkBanditContext, agent: Any, *, horizon: int) -> dict[str, Any]:
    """Run one without-replacement episode over a fixed candidate pool."""
    remaining = list(context.candidate_pool)
    steps: list[EpisodeStep] = []
    positive_hits = 0

    for step_index in range(min(max(horizon, 0), len(remaining))):
        candidate = agent.select_candidate(context, remaining, step_index=step_index)
        reward = reward_for_gene(context, candidate.gene_symbol)
        is_positive = reward > 0.0
        if is_positive:
            positive_hits += 1
        steps.append(
            EpisodeStep(
                step_index=step_index + 1,
                gene_symbol=candidate.gene_symbol,
                reward=reward,
                is_positive=is_positive,
                rank=candidate.rank,
                fused_score=candidate.fused_score,
            )
        )
        agent.observe(context, candidate, reward=reward)
        remaining = [item for item in remaining if item.gene_symbol != candidate.gene_symbol]
        if positive_hits >= len(context.positive_gene_symbols):
            break

    first_positive_step = next((step.step_index for step in steps if step.is_positive), None)
    return {
        "benchmark_id": context.benchmark_id,
        "indication_name": context.indication_name,
        "mode": context.mode,
        "subset_id": context.subset_id,
        "candidate_limit": context.candidate_limit,
        "positive_gene_symbols": list(context.positive_gene_symbols),
        "positive_covered_in_candidate_pool": any(
            candidate.gene_symbol in context.positive_gene_symbols for candidate in context.candidate_pool
        ),
        "horizon": horizon,
        "steps": [
            {
                "step": step.step_index,
                "gene_symbol": step.gene_symbol,
                "reward": step.reward,
                "is_positive": step.is_positive,
                "rank": step.rank,
                "fused_score": step.fused_score,
            }
            for step in steps
        ],
        "metrics": {
            "total_reward": round(sum(step.reward for step in steps), 4),
            "positive_hits": positive_hits,
            "first_positive_step": first_positive_step,
            "hit_at_horizon": first_positive_step is not None,
            "reciprocal_first_positive_step": round(1.0 / first_positive_step, 4) if first_positive_step else 0.0,
        },
    }
