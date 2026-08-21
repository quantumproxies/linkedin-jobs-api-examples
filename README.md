# LinkedIn jobs API — hiring signals as rows, not a browser session

The [`linkedin_jobs` collector](https://quanticdata.io/collectors/linkedin-jobs-api/) takes a
query and a location and returns the public job listings: title, company, company URL, location,
posted date (absolute **and** LinkedIn's relative label), salary line, benefits, job id, link and
logo. **$0.001 per job**, up to 300 per run.

Public listing pages only — no login, no session cookie, nothing behind an account.

```bash
pip install requests
export QUANTICDATA_API_KEY=qd_live_your_key_here

python3 jobs.py "data engineer" --location "United States" --remote --days 7 --out jobs.csv
python3 hiring_signal.py roles.json      # which companies are staffing up, by week
```

## Files

| File | What it does |
|---|---|
| [`client.py`](client.py) | collector runner (sync + async polling) |
| [`jobs.py`](jobs.py) | one search → CSV, with a company histogram |
| [`hiring_signal.py`](hiring_signal.py) | several roles + markets → posts-per-company-per-week, sorted by acceleration |
| [`salary_bands.py`](salary_bands.py) | parse the salary line into numbers and print the band per seniority |
| [`cross_board.py`](cross_board.py) | LinkedIn + Indeed + Google Jobs for the same role, de-duplicated |

## Input

| Field | Notes |
|---|---|
| `query` | role or keyword, e.g. `"data engineer"` |
| `location` | city, region or country — `"New York"`, `"Italy"`, `"United States"` |
| `remote_only` | only listings LinkedIn flags as remote |
| `posted_within_days` | 1–30 |
| `country` | ISO code for the exit geo |
| `max_results` | 1–300, default 25 |

## Output row

```jsonc
{ "rank": 1, "title": "Senior Data Engineer", "company": "Acme",
  "company_url": "https://www.linkedin.com/company/acme",
  "location": "New York, NY", "posted_at": "2026-08-14",
  "posted_label": "1 week ago", "salary": "$150,000 - $190,000/yr",
  "benefits": "401(k), Medical", "job_id": "3945…",
  "link": "https://www.linkedin.com/jobs/view/3945…", "logo": "https://…" }
```

`posted_at` is the parsed date — sort on it. `posted_label` is what the page said.

## Reading hiring data honestly

- **A reposted job is not a new job.** LinkedIn resurfaces listings; de-duplicate on `job_id`
  and treat `posted_at` as "first seen", which is what `hiring_signal.py` does.
- **Salary is present on a minority of listings**, and mostly in markets where disclosure is
  mandated (much of the US, increasingly the EU). Treat the band as a sample, not a census.
- **Counts are relative signals.** "Acme posted 14 engineering roles this month, up from 3" is a
  real signal. "Acme has exactly 14 open roles" is not — you are seeing the public surface.
- Cross-referencing boards catches roles that only exist on one of them; `cross_board.py`
  merges LinkedIn, [Indeed](https://quanticdata.io/collectors/indeed-jobs-api/) and
  [Google Jobs](https://quanticdata.io/collectors/google-jobs-api/) on company+title.

## Related

- [LinkedIn jobs API](https://quanticdata.io/collectors/linkedin-jobs-api/) · [Indeed jobs API](https://quanticdata.io/collectors/indeed-jobs-api/) · [Google Jobs API](https://quanticdata.io/collectors/google-jobs-api/)
- [Scrape job postings](https://quanticdata.io/scrape-job-postings/) · [LinkedIn company scraper](https://quanticdata.io/collectors/linkedin-company-scraper-api/)
- [Market research data](https://quanticdata.io/market-research-data/)

MIT licensed.
