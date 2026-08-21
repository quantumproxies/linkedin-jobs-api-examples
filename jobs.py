"""One LinkedIn job search → CSV, plus who is posting the most.

    python3 jobs.py "data engineer" --location "United States" --remote --days 7 --max 200
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter

from client import collect

FIELDS = ["rank", "title", "company", "location", "posted_at", "posted_label",
          "salary", "benefits", "job_id", "company_url", "link"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--location", default="United States")
    ap.add_argument("--country", default="us")
    ap.add_argument("--remote", action="store_true")
    ap.add_argument("--days", type=int, default=None, help="posted within N days (1-30)")
    ap.add_argument("--max", type=int, default=100)
    ap.add_argument("--out", default="jobs.csv")
    args = ap.parse_args()

    rows = collect("linkedin_jobs", query=args.query, location=args.location,
                   country=args.country, remote_only=args.remote,
                   posted_within_days=args.days, max_results=args.max)

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    with_salary = sum(1 for r in rows if r.get("salary"))
    print(f"{len(rows)} listings → {args.out}   ({with_salary} disclose a salary)\n")

    print("top employers")
    for company, n in Counter(r.get("company") for r in rows).most_common(12):
        print(f"  {n:>3}  {company}")

    print("\ntop locations")
    for loc, n in Counter(r.get("location") for r in rows).most_common(8):
        print(f"  {n:>3}  {loc}")


if __name__ == "__main__":
    main()
