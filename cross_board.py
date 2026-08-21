"""The same role on LinkedIn, Indeed and Google Jobs, merged and de-duplicated.

Each board has listings the others do not. Merging on a normalized
company+title key shows you the union, and which board found what.

    python3 cross_board.py "data engineer" --location "New York" --max 150
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict

from client import collect


def key(company: str | None, title: str | None) -> str:
    norm = lambda s: re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()
    return f"{norm(company)}|{norm(title)}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--location", default="New York")
    ap.add_argument("--country", default="us")
    ap.add_argument("--max", type=int, default=100)
    ap.add_argument("--out", default="cross-board.csv")
    args = ap.parse_args()

    sources = {
        "linkedin": ("linkedin_jobs", {"query": args.query, "location": args.location,
                                       "country": args.country, "max_results": args.max}),
        "indeed": ("indeed_jobs", {"query": args.query, "location": args.location,
                                   "country": args.country, "max_results": args.max}),
        "google": ("google_jobs", {"query": args.query, "location": args.location,
                                   "country": args.country, "max_results": args.max}),
    }

    merged: dict[str, dict] = {}
    boards: dict[str, set] = defaultdict(set)

    for board, (slug, payload) in sources.items():
        try:
            rows = collect(slug, **payload)
        except RuntimeError as exc:
            print(f"{board:<10} !! {exc}")
            continue
        print(f"{board:<10} {len(rows):>4} listings")
        for row in rows:
            k = key(row.get("company"), row.get("title"))
            boards[k].add(board)
            merged.setdefault(k, {
                "title": row.get("title"),
                "company": row.get("company"),
                "location": row.get("location"),
                "salary": row.get("salary"),
                "link": row.get("link"),
            })

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["title", "company", "location", "salary", "boards", "link"])
        for k, row in merged.items():
            w.writerow([row["title"], row["company"], row["location"], row["salary"],
                        "+".join(sorted(boards[k])), row["link"]])

    only_one = sum(1 for k in merged if len(boards[k]) == 1)
    all_three = sum(1 for k in merged if len(boards[k]) == 3)
    print(f"\n{len(merged)} unique roles — {only_one} on a single board, "
          f"{all_three} on all three → {args.out}")


if __name__ == "__main__":
    main()
