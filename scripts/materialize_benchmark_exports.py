#!/usr/bin/env python3
"""Write PrioriTx benchmark summaries to timestamped JSON and CSV artifacts."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import shutil
from pathlib import Path

from prioritx_eval.service import (
    export_benchmark_health_rows,
    summarize_benchmark_dashboard,
    summarize_benchmark_health,
)

ROOT = Path(__file__).resolve().parent.parent
EXPORTS_DIR = ROOT / "tmp" / "benchmark_exports"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-n", type=int, default=10, help="Top-N slice used for benchmark summaries.")
    return parser.parse_args(argv)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    export_dir = EXPORTS_DIR / timestamp
    latest_dir = EXPORTS_DIR / "latest"
    export_dir.mkdir(parents=True, exist_ok=True)

    dashboard = summarize_benchmark_dashboard(top_n=args.top_n)
    health = summarize_benchmark_health(top_n=args.top_n)
    rows_payload = export_benchmark_health_rows(top_n=args.top_n)

    _write_json(export_dir / "benchmark_dashboard.json", dashboard)
    _write_json(export_dir / "benchmark_health.json", health)
    _write_json(export_dir / "benchmark_health_rows.json", rows_payload)
    _write_csv(export_dir / "benchmark_health_rows.csv", rows_payload["rows"])

    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    shutil.copytree(export_dir, latest_dir)

    print(export_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
