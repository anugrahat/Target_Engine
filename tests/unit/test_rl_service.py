from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from prioritx_rl import cli
from prioritx_rl.agents import FusedGreedyAgent, LinearUCBAgent, RandomAgent
from prioritx_rl.env import BenchmarkBanditContext, TargetCandidate, reward_for_gene, run_episode
from prioritx_rl.service import evaluate_bandit_agents


def _candidate(gene_symbol: str, *, fused_score: float, rank: int, positive_bias: float = 0.0) -> TargetCandidate:
    return TargetCandidate(
        benchmark_id="ipf_tnik",
        mode="strict",
        subset_id="ipf_lung_core",
        rank=rank,
        gene_symbol=gene_symbol,
        ensembl_gene_id=f"ENSG{rank:06d}",
        fused_score=fused_score,
        feature_vector=(fused_score, positive_bias, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        transcriptomics_score=fused_score,
        genetics_score=0.0,
        tractability_score=0.0,
        pathway_score=0.0,
        network_score=0.0,
        transcriptomics_supporting_contrasts=1,
        transcriptomics_available=True,
        genetics_available=False,
        tractability_available=False,
        pathway_available=False,
        network_available=False,
        transcriptomics_direction_conflict=False,
    )


def _context() -> BenchmarkBanditContext:
    return BenchmarkBanditContext(
        benchmark_id="ipf_tnik",
        indication_name="idiopathic pulmonary fibrosis",
        mode="strict",
        subset_id="ipf_lung_core",
        positive_gene_symbols=("TNIK",),
        candidate_pool=(
            _candidate("GENE_A", fused_score=0.8, rank=1, positive_bias=0.1),
            _candidate("TNIK", fused_score=0.2, rank=2, positive_bias=1.0),
            _candidate("GENE_B", fused_score=0.1, rank=3, positive_bias=0.0),
        ),
        candidate_limit=3,
    )


class RlServiceTests(unittest.TestCase):
    def test_reward_for_gene_is_binary(self) -> None:
        context = _context()
        self.assertEqual(1.0, reward_for_gene(context, "TNIK"))
        self.assertEqual(0.0, reward_for_gene(context, "GENE_A"))

    def test_fused_greedy_follows_existing_rank(self) -> None:
        result = run_episode(_context(), FusedGreedyAgent(), horizon=1)
        self.assertEqual("GENE_A", result["steps"][0]["gene_symbol"])
        self.assertFalse(result["metrics"]["hit_at_horizon"])

    def test_random_agent_produces_valid_episode(self) -> None:
        result = run_episode(_context(), RandomAgent(seed=1), horizon=2)
        self.assertEqual(2, len(result["steps"]))
        self.assertIn(result["steps"][0]["gene_symbol"], {"GENE_A", "TNIK", "GENE_B"})

    def test_linear_ucb_can_learn_positive_feature_bias(self) -> None:
        agent = LinearUCBAgent(alpha=0.4)
        positive = next(candidate for candidate in _context().candidate_pool if candidate.gene_symbol == "TNIK")
        agent.observe(_context(), positive, reward=1.0)
        chosen = agent.select_candidate(_context(), list(_context().candidate_pool), step_index=0)
        self.assertEqual("TNIK", chosen.gene_symbol)

    def test_evaluate_bandit_agents_aggregates_metrics(self) -> None:
        context = _context()
        with patch("prioritx_rl.service.build_bandit_contexts", return_value=[context]):
            payload = evaluate_bandit_agents(episodes=2, candidate_limit=3, horizon=1, seed=0)
        self.assertEqual("offline_contextual_bandit_replay", payload["evaluation_kind"])
        self.assertEqual(3, len(payload["agents"]))
        fused = next(item for item in payload["agents"] if item["agent_name"] == "fused_greedy")
        self.assertEqual(0.0, fused["metrics"]["hit_rate"])

    def test_rl_cli_prints_agent_summary(self) -> None:
        mocked_payload = {
            "agents": [
                {
                    "agent_name": "fused_greedy",
                    "metrics": {
                        "hit_rate": 0.0,
                        "mean_reciprocal_first_positive_step": 0.0,
                        "candidate_pool_positive_coverage_rate": 1.0,
                    },
                }
            ],
            "scientific_caveats": ["small benchmark"],
        }
        with patch("prioritx_rl.cli.evaluate_bandit_agents", return_value=mocked_payload):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = cli.main(["--episodes", "2"])
        self.assertEqual(0, exit_code)
        self.assertIn("fused_greedy", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
