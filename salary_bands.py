"""Turn the salary line into numbers, then print the band per seniority.

The line is free text — "$150,000 - $190,000/yr", "€55K–€70K", "£450/day".
This parser keeps annual ranges and ignores what it cannot read, which is the
honest thing to do with a field that is optional and unstructured.

    python3 salary_bands.py "backend engineer" --location "United States" --max 300
"""
from __future__ import annotations

import argparse
import re
import statistics
from collections import defaultdict

from client import collect

MONEY = re.compile(r"([€$£])\s?([\d.,]+)\s*([KkMm])?")
SENIORITY = [
    ("principal/staff", ("principal", "staff", "distinguished")),
    ("lead/manager", ("lead", "manager", "head of", "director")),
    ("senior", ("senior", "sr.", "sr ")),
    ("mid", ("mid", "ii", " 2")),
    ("junior", ("junior", "jr.", "graduate", "intern", "entry")),
]


def amounts(text: str) -> list[float]:
    out = []
    for _, raw, suffix in MONEY.findall(text or ""):
        try:
            value = float(raw.replace(",", "").rstrip("."))
        except ValueError:
            continue
        if suffix and suffix.lower() == "k":
            value *= 1_000
        elif suffix and suffix.lower() == "m":
            value *= 1_000_000
        out.append(value)
    # Ignore anything that is clearly not an annual figure (hourly, daily rates).
    return [v for v in out if v >= 10_000]


def bucket(title: str) -> str:
    low = (title or "").lower()
    for label, needles in SENIORITY:
        if any(n in low for n in needles):
            return label
    return "unspecified"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--location", default="United States")
    ap.add_argument("--country", default="us")
    ap.add_argument("--max", type=int, default=300)
    args = ap.parse_args()

    rows = collect("linkedin_jobs", query=args.query, location=args.location,
                   country=args.country, max_results=args.max)

    bands: dict[str, list[float]] = defaultdict(list)
    parsed = 0
    for row in rows:
        values = amounts(row.get("salary") or "")
        if not values:
            continue
        parsed += 1
        bands[bucket(row.get("title"))].append(statistics.fmean(values))

    print(f"{len(rows)} listings, {parsed} with a readable annual salary "
          f"({100 * parsed // max(len(rows), 1)}%)\n")
    print(f"{'seniority':<18}{'n':>5}{'p25':>12}{'median':>12}{'p75':>12}")
    for label in ("junior", "mid", "senior", "lead/manager", "principal/staff", "unspecified"):
        values = sorted(bands.get(label, []))
        if len(values) < 3:
            continue
        q = statistics.quantiles(values, n=4)
        print(f"{label:<18}{len(values):>5}{q[0]:>12,.0f}{q[1]:>12,.0f}{q[2]:>12,.0f}")


if __name__ == "__main__":
    main()
