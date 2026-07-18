#!/usr/bin/env python3
"""Weekly PR activity report generator.

Pulls PRs authored by a given GitHub user that saw activity in a Mon-Sun
week window and appends the week to pr-activity/data.json. index.html
(checked in separately, rewritten each run to stay in sync with this
script) reads that JSON client-side and renders history + a
per-week filter driven by the ?week= URL param.

Usage:
  python3 generate.py [--author bentonyetman] [--week-start YYYY-MM-DD]
  python3 generate.py --since YYYY-MM-DD    # backfill every week from that date through today

Without --week-start/--since, targets the most recently completed Mon-Sun
week (i.e. running this on any day resolves to "last week"). Re-running
for a week already in data.json replaces that week's entry. --since does
one bulk fetch and buckets PRs into Mon-Sun weeks by their updatedAt date,
upserting each week found.
"""
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

OUT_DIR = Path(__file__).parent
DATA_PATH = OUT_DIR / "data.json"
SITE_BASE = "https://reports-rho-plum.vercel.app/pr-activity/index.html"


def last_full_week(today: datetime.date) -> tuple[datetime.date, datetime.date]:
    this_monday = today - datetime.timedelta(days=today.weekday())
    last_monday = this_monday - datetime.timedelta(days=7)
    last_sunday = last_monday + datetime.timedelta(days=6)
    return last_monday, last_sunday


def fetch_prs(author: str, start: datetime.date, end: datetime.date) -> list[dict]:
    cmd = [
        "gh", "search", "prs",
        f"--author={author}",
        f"--updated={start.isoformat()}..{end.isoformat()}",
        "--json", "repository,title,url,state,createdAt,updatedAt,closedAt,number,isDraft,commentsCount",
        "--limit", "1000",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    raw = json.loads(result.stdout)
    return [
        {
            "repo": pr["repository"]["nameWithOwner"],
            "number": pr["number"],
            "title": pr["title"],
            "url": pr["url"],
            "state": pr["state"],
            "updatedAt": pr["updatedAt"],
            "commentsCount": pr["commentsCount"],
        }
        for pr in raw
    ]


def load_data() -> list[dict]:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text())
    return []


def upsert_week(weeks: list[dict], entry: dict) -> list[dict]:
    weeks = [w for w in weeks if w["weekStart"] != entry["weekStart"]]
    weeks.append(entry)
    weeks.sort(key=lambda w: w["weekStart"])
    return weeks


def monday_of(d: datetime.date) -> datetime.date:
    return d - datetime.timedelta(days=d.weekday())


def bucket_by_week(prs: list[dict]) -> dict[datetime.date, list[dict]]:
    buckets: dict[datetime.date, list[dict]] = {}
    for pr in prs:
        updated = datetime.date.fromisoformat(pr["updatedAt"][:10])
        buckets.setdefault(monday_of(updated), []).append(pr)
    return buckets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--author", default="bentonyetman")
    parser.add_argument("--week-start", help="Monday of the target week, YYYY-MM-DD. Defaults to last full Mon-Sun week.")
    parser.add_argument("--since", help="Backfill every week from this date (YYYY-MM-DD) through today in one pass.")
    args = parser.parse_args()

    weeks = load_data()
    today = datetime.date.today()

    if args.since:
        since = datetime.date.fromisoformat(args.since)
        prs = fetch_prs(args.author, since, today)
        buckets = bucket_by_week(prs)
        for week_start in sorted(buckets):
            week_prs = buckets[week_start]
            entry = {
                "weekStart": week_start.isoformat(),
                "weekEnd": (week_start + datetime.timedelta(days=6)).isoformat(),
                "author": args.author,
                "generatedAt": today.isoformat(),
                "prs": week_prs,
            }
            weeks = upsert_week(weeks, entry)
        DATA_PATH.write_text(json.dumps(weeks, indent=2))
        print(f"data.json: backfilled {len(buckets)} weeks from {since.isoformat()} ({len(prs)} PRs total, {len(weeks)} weeks in file)", file=sys.stderr)
        print(f"Share: {SITE_BASE}?week=all", file=sys.stderr)
        return

    if args.week_start:
        start = datetime.date.fromisoformat(args.week_start)
        end = start + datetime.timedelta(days=6)
    else:
        start, end = last_full_week(today)

    prs = fetch_prs(args.author, start, end)
    entry = {
        "weekStart": start.isoformat(),
        "weekEnd": end.isoformat(),
        "author": args.author,
        "generatedAt": today.isoformat(),
        "prs": prs,
    }

    weeks = upsert_week(weeks, entry)
    DATA_PATH.write_text(json.dumps(weeks, indent=2))

    repos = {pr["repo"] for pr in prs}
    print(f"data.json: week {start.isoformat()} - {len(prs)} PRs across {len(repos)} repos ({len(weeks)} weeks total)", file=sys.stderr)
    print(f"Share: {SITE_BASE}?week={start.isoformat()}", file=sys.stderr)


if __name__ == "__main__":
    main()
