"""Which companies are accelerating their hiring?

Reads a roles file, pulls each search, de-duplicates on job_id, buckets by ISO
week and reports companies whose recent weeks beat their own baseline. That
relative comparison is the honest one — absolute counts just rank big companies.

    python3 hiring_signal.py roles.json
    # roles.json: [{"query":"data engineer","location":"United States"}, …]
"""
from __future__ import annotations

import argparse
import json
import pathlib
from collections import Counter, defaultdict
from datetime import date

from client import collect


def iso_week(value: str | None) -> str | None:
    if not value or len(value) < 10:
        return None
    try:
        y, w, _ = date.fromisoformat(value[:10]).isocalendar()
    except ValueError:
        return None
    return f"{y}-W{w:02d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("roles", type=pathlib.Path)
    ap.add_argument("--max", type=int, default=200)
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args()

    roles = json.loads(args.roles.read_text(encoding="utf-8"))
    seen: dict[str, dict] = {}

    for role in roles:
        rows = collect("linkedin_jobs", query=role["query"],
                       location=role.get("location", "United States"),
                       country=role.get("country", "us"),
                       posted_within_days=args.days, max_results=args.max)
        fresh = 0
        for row in rows:
            key = row.get("job_id") or row.get("link")
            if key and key not in seen:
                seen[key] = row
                fresh += 1
        print(f"{role['query']:<28} {role.get('location', ''):<22} "
              f"{len(rows):>4} rows, {fresh:>4} new")

    by_company_week: dict[str, Counter] = defaultdict(Counter)
    for row in seen.values():
        week = iso_week(row.get("posted_at"))
        if week and row.get("company"):
            by_company_week[row["company"]][week] += 1

    weeks = sorted({w for c in by_company_week.values() for w in c})
    if len(weeks) < 2:
        print("\nnot enough weeks of data yet — widen --days")
        return
    recent, baseline = weeks[-2:], weeks[:-2]

    scored = []
    for company, counts in by_company_week.items():
        late = sum(counts[w] for w in recent)
        early = sum(counts[w] for w in baseline) / max(1, len(baseline)) * len(recent)
        if late >= 3:
            scored.append((company, late, early, late / max(early, 0.5)))

    scored.sort(key=lambda t: -t[3])
    print(f"\naccelerating (last 2 weeks vs. earlier average) — {len(seen)} unique listings\n")
    print(f"{'company':<34}{'recent':>8}{'expected':>10}{'ratio':>8}")
    for company, late, early, ratio in scored[:20]:
        print(f"{company[:33]:<34}{late:>8}{early:>10.1f}{ratio:>8.1f}x")


if __name__ == "__main__":
    main()
