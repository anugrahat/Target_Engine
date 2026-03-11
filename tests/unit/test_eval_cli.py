from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from prioritx_eval import cli


class EvalCliTests(unittest.TestCase):
    def test_parse_args_defaults_to_both_modes(self) -> None:
        args = cli._parse_args([])

        self.assertEqual(["strict", "exploratory"], args.modes)
        self.assertFalse(args.skip_audit)

    def test_main_can_skip_audit_for_bounded_runs(self) -> None:
        benchmark_result = {
            "positive_targets_found": 1,
            "positive_target_count": 1,
            "metrics": {"best_rank": 1, "hit_at_10": True, "mean_reciprocal_rank": 1.0},
            "items": [{"gene_symbol": "TNIK"}],
        }
        integrity_result = {
            "subset_id": "ipf_lung_core",
            "families": [{"family": "pubmed_literature", "risk_level": "high"}],
        }
        with patch("prioritx_eval.cli.list_benchmark_assertion_ids", return_value=["ipf_tnik"]), patch(
            "prioritx_eval.cli.evaluate_fused_benchmark",
            return_value=benchmark_result,
        ), patch(
            "prioritx_eval.cli.benchmark_integrity_review",
            return_value=integrity_result,
        ), patch("prioritx_eval.cli.audit_target_evidence") as audit_mock:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = cli.main(["--modes", "strict", "--skip-audit"])

        self.assertEqual(0, exit_code)
        audit_mock.assert_not_called()
        self.assertIn("ipf_tnik [strict]", buffer.getvalue())

    def test_main_can_run_integrity_only(self) -> None:
        integrity_result = {
            "subset_id": "ipf_lung_core",
            "families": [{"family": "pubmed_literature", "risk_level": "high"}],
        }
        with patch("prioritx_eval.cli.list_benchmark_assertion_ids", return_value=["ipf_tnik"]), patch(
            "prioritx_eval.cli.benchmark_integrity_review",
            return_value=integrity_result,
        ), patch("prioritx_eval.cli.evaluate_fused_benchmark") as eval_mock, patch(
            "prioritx_eval.cli.audit_target_evidence"
        ) as audit_mock:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = cli.main(["--modes", "strict", "--integrity-only"])

        self.assertEqual(0, exit_code)
        eval_mock.assert_not_called()
        audit_mock.assert_not_called()
        self.assertIn("integrity subset=ipf_lung_core", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
