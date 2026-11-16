#!/usr/bin/env python3
"""Verify the published EP26 numbers against the raw result files.

Checks (no big datasets needed):
  1. every metric in results/summary.json equals the value in results/metrics_<site>.csv
  2. count_ratio_pct is reproducible from features / truth_buildings
  3. no layer claims more matched buildings than it has polygons

Run:  python verify.py            -> exit 0 = all green
      python verify.py --verbose  -> print every checked value
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
TOL = 0.02  # published values are rounded to 2 decimals


def load_csv(site: str) -> dict[str, dict]:
    with open(RESULTS / f"metrics_{site}.csv", encoding="utf-8") as f:
        return {row["layer"]: row for row in csv.DictReader(f)}


def main() -> int:
    verbose = "--verbose" in sys.argv
    summary = json.load(open(RESULTS / "summary.json", encoding="utf-8"))
    failures: list[str] = []
    checks = 0

    for site, info in summary["sites"].items():
        truth = info["truth_buildings"]
        rows = load_csv(site)
        published = summary["metrics"][site]

        if set(rows) != set(published):
            failures.append(f"{site}: layer sets differ ({sorted(rows)} vs {sorted(published)})")
            continue

        for layer, metrics in published.items():
            row = rows[layer]
            for key, value in metrics.items():
                checks += 1
                try:
                    csv_value = float(row[key])
                except (KeyError, ValueError):
                    failures.append(f"{site}/{layer}: {key} missing from CSV")
                    continue
                if abs(csv_value - float(value)) > TOL:
                    failures.append(
                        f"{site}/{layer}: {key} summary={value} csv={csv_value}"
                    )
                elif verbose:
                    print(f"ok  {site}/{layer:9s} {key:26s} {value}")

            # 2. count ratio must be reproducible from raw counts
            checks += 1
            recomputed = float(row["features"]) / truth * 100
            if abs(recomputed - float(row["count_ratio_pct"])) > TOL:
                failures.append(
                    f"{site}/{layer}: count_ratio_pct={row['count_ratio_pct']} "
                    f"but features/truth={recomputed:.2f}"
                )

            # 3. sanity: matched buildings cannot exceed polygon count
            checks += 1
            if int(row["one2one_matched"]) > int(row["features"]):
                failures.append(
                    f"{site}/{layer}: one2one_matched={row['one2one_matched']} > features={row['features']}"
                )

    print(f"\nchecked {checks} values across {len(summary['sites'])} sites")
    if failures:
        print("FAIL")
        for f in failures:
            print("  -", f)
        return 1
    print("PASS — published numbers match the result files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
