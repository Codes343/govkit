#!/usr/bin/env python3
"""Weekly revenue and traction report, posted to a GitHub issue by CI.

The only KPI that matters is monthly profit, so this reports the numbers that
roll up to it: runs, unique users, records delivered, and the revenue those
records imply at our published pay-per-event prices.

Apify's exact settled earnings live in Console > Actors > Insights >
Monetization. This script estimates from delivered records instead, which is
what we control and what we can alert on. The two should agree closely; a
persistent gap is itself a finding worth investigating.
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from datetime import UTC, datetime, timedelta

import httpx

API = "https://api.apify.com/v2"

# Must match the prices configured in the Apify Console. See PRICING.md.
PRICE_ACTOR_START = 0.005
PRICE_DATASET_ITEM = 0.003
DEVELOPER_SHARE = 0.80

WINDOW_DAYS = 7
GOAL_MONTHLY_NET = 20.00


def _fetch(client: httpx.Client, path: str, **params) -> dict:
    response = client.get(f"{API}{path}", params=params)
    response.raise_for_status()
    return response.json().get("data", {})


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def main() -> int:
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print("APIFY_TOKEN is not set; cannot report.", file=sys.stderr)
        return 1

    since = datetime.now(UTC) - timedelta(days=WINDOW_DAYS)

    with httpx.Client(timeout=60, headers={"Authorization": f"Bearer {token}"}) as client:
        actors = _fetch(client, "/acts", limit=100).get("items", [])

        rows = []
        totals = defaultdict(float)

        for actor in actors:
            actor_id = actor["id"]
            name = actor.get("name", actor_id)

            runs = _fetch(client, f"/acts/{actor_id}/runs", limit=1000, desc="true").get(
                "items", []
            )
            recent = [
                r for r in runs if (_parse_ts(r.get("startedAt")) or since) >= since
            ]

            items = 0
            succeeded = 0
            failed = 0
            for run in recent:
                if run.get("status") == "SUCCEEDED":
                    succeeded += 1
                elif run.get("status") in {"FAILED", "TIMED-OUT", "ABORTED"}:
                    failed += 1
                stats = run.get("stats") or {}
                items += int(
                    stats.get("datasetItemCount")
                    or (run.get("defaultDatasetId") and 0)
                    or 0
                )

            gross = len(recent) * PRICE_ACTOR_START + items * PRICE_DATASET_ITEM
            net = gross * DEVELOPER_SHARE

            rows.append(
                {
                    "name": name,
                    "runs": len(recent),
                    "ok": succeeded,
                    "failed": failed,
                    "items": items,
                    "gross": gross,
                    "net": net,
                    "users": (actor.get("stats") or {}).get("totalUsers", 0),
                }
            )
            totals["runs"] += len(recent)
            totals["failed"] += failed
            totals["items"] += items
            totals["gross"] += gross
            totals["net"] += net

    projected_monthly = totals["net"] * (30 / WINDOW_DAYS)
    pct = (projected_monthly / GOAL_MONTHLY_NET * 100) if GOAL_MONTHLY_NET else 0

    print(f"## GovKit weekly report - last {WINDOW_DAYS} days\n")
    if not rows:
        print("No actors found on this account yet. See SETUP.md.")
        return 0

    print("| Actor | Runs | Failed | Records | Gross | Net (80%) | Total users |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for row in sorted(rows, key=lambda r: -r["net"]):
        print(
            f"| `{row['name']}` | {row['runs']} | {row['failed']} | {row['items']:,} "
            f"| ${row['gross']:.2f} | ${row['net']:.2f} | {row['users']} |"
        )
    print(
        f"| **Total** | **{int(totals['runs'])}** | **{int(totals['failed'])}** | "
        f"**{int(totals['items']):,}** | **${totals['gross']:.2f}** | "
        f"**${totals['net']:.2f}** | |"
    )

    print(
        f"\n**Projected monthly net: ${projected_monthly:.2f}** "
        f"({pct:.0f}% of the ${GOAL_MONTHLY_NET:.0f} goal)"
    )

    if totals["failed"]:
        print(
            f"\n{int(totals['failed'])} run(s) failed this week. Failed runs are "
            "lost customers - check the smoke test and recent Store issues."
        )
    if projected_monthly >= GOAL_MONTHLY_NET:
        print("\nGoal met. Evaluate reinvestment per BUSINESS_PLAN.md section 7.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
