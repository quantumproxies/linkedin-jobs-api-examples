"""Collector runner shared by the job examples."""
from __future__ import annotations

import os
import time
from typing import Any

import requests

BASE = "https://api.quanticdata.io/v1"
_s = requests.Session()


def _h() -> dict[str, str]:
    key = os.environ.get("QUANTICDATA_API_KEY")
    if not key:
        raise SystemExit("set QUANTICDATA_API_KEY — https://app.quanticdata.io/register")
    return {"Authorization": f"Bearer {key}"}


def collect(slug: str, **input_: Any) -> list[dict]:
    r = _s.post(f"{BASE}/scraper/collectors/{slug}/run",
                json={k: v for k, v in input_.items() if v not in (None, False, "")},
                headers=_h(), timeout=300)
    body = r.json()
    if body.get("type") == "error" or not r.ok:
        raise RuntimeError(f"{slug} ({r.status_code}): {body.get('message')}")

    run = body.get("payload", {})
    while run.get("status") in ("queued", "running"):
        time.sleep(3)
        run = _s.get(f"{BASE}/scraper/collectors/runs/{run['run_id']}",
                     headers=_h(), timeout=60).json().get("payload", {})
    return run.get("results") or []
