#!/usr/bin/env python3
"""Run bounded RL replay checks and save a timestamped local report."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from prioritx_rl.service import evaluate_bandit_agents


ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "tmp" / "rl_benchmark_reports"


def _render_case(title: str, payload: dict[str, object]) -> list[str]:
    lines = [f"## {title}", ""]
    for agent in payload["agents"]:
        metrics = agent["metrics"]
        lines.append(
            f"- `{agent['agent_name']}`: hit_rate=`{metrics['hit_rate']}`, "
            f"MRR=`{metrics['mean_reciprocal_first_positive_step']}`, "
            f"coverage=`{metrics['candidate_pool_positive_coverage_rate']}`"
        )
    lines.extend(["", "```json", json.dumps(payload["provenance"], indent=2), "```", ""])
    return lines


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")

    strict = evaluate_bandit_agents(candidate_limit=250, horizon=25, episodes=1, modes=["strict"])
    ipf_exploratory = evaluate_bandit_agents(
        benchmark_ids=["ipf_tnik"],
        candidate_limit=2000,
        horizon=100,
        episodes=3,
        modes=["exploratory"],
    )
    hcc_exploratory = evaluate_bandit_agents(
        benchmark_ids=["hcc_cdk20"],
        candidate_limit=12000,
        horizon=100,
        episodes=1,
        modes=["exploratory"],
    )

    lines = [
        "# PrioriTx RL Benchmark Report",
        "",
        f"- timestamp_utc: `{timestamp}`",
        "- profile: `bounded_offline_contextual_bandit_replay`",
        "",
        *_render_case("Strict", strict),
        *_render_case("Exploratory IPF", ipf_exploratory),
        *_render_case("Exploratory HCC", hcc_exploratory),
    ]

    report_path = REPORTS_DIR / f"{timestamp}.md"
    latest_path = REPORTS_DIR / "latest.md"
    report_text = "\n".join(lines) + "\n"
    report_path.write_text(report_text)
    latest_path.write_text(report_text)
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
