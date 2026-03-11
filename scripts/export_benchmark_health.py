#!/usr/bin/env python3
"""Export PrioriTx benchmark health rows as JSON or CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys

from prioritx_eval.service import export_benchmark_health_rows


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-n", type=int, default=10, help="Top-N slice used for benchmark summaries.")
    parser.add_argument(
        "--format",
        choices=("json", "csv"),
        default="json",
        help="Output format.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    payload = export_benchmark_health_rows(top_n=args.top_n)
    if args.format == "json":
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    rows = payload["rows"]
    fieldnames = list(rows[0].keys()) if rows else []
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
