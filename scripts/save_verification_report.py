#!/usr/bin/env python3
"""Run the core verification suite and save a timestamped local report."""

from __future__ import annotations

import datetime as dt
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "tmp" / "verification_reports"
COMMANDS = [
    "ruby scripts/validate_benchmark_packs.rb",
    "ruby scripts/validate_subset_configs.rb",
    "ruby scripts/validate_contract_examples.rb",
    "ruby scripts/validate_registry_artifacts.rb",
    "ruby scripts/validate_transcriptomics_fixtures.rb",
    "ruby scripts/validate_benchmark_assertions.rb",
    "PYTHONPATH=packages/py python3 -m unittest discover -s tests/unit -p 'test_*.py'",
    "PYTHONPATH=packages/py python3 -m prioritx_eval.cli --modes strict --integrity-only",
]


def _run(command: str) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        shell=True,
        text=True,
        capture_output=True,
    )
    output = completed.stdout
    if completed.stderr:
        output = f"{output}\n[stderr]\n{completed.stderr}".strip()
    return completed.returncode, output.strip()


def _git_value(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() or "unknown"


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    branch = _git_value(["rev-parse", "--abbrev-ref", "HEAD"])
    commit = _git_value(["rev-parse", "--short", "HEAD"])

    lines = [
        "# PrioriTx Verification Report",
        "",
        f"- timestamp_utc: `{timestamp}`",
        f"- branch: `{branch}`",
        f"- commit: `{commit}`",
        "",
    ]

    overall_ok = True
    for command in COMMANDS:
        code, output = _run(command)
        overall_ok = overall_ok and code == 0
        lines.extend(
            [
                f"## `{command}`",
                "",
                f"- exit_code: `{code}`",
                "",
                "```text",
                output or "(no output)",
                "```",
                "",
            ]
        )

    lines.insert(4, f"- overall_status: `{'pass' if overall_ok else 'fail'}`")
    report_text = "\n".join(lines)

    report_path = REPORTS_DIR / f"{timestamp}.md"
    latest_path = REPORTS_DIR / "latest.md"
    report_path.write_text(report_text)
    latest_path.write_text(report_text)

    print(report_path)
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
