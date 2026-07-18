#!/usr/bin/env python3
"""Weekly PR activity report generator.

Pulls PRs authored by a given GitHub user that saw activity in a Mon-Sun
week window and appends the week to pr-activity/data.json. index.html
(checked in separately, rewritten each run to stay in sync with this
script) reads that JSON client-side and renders history + a
per-week filter driven by the ?week= URL param.

Usage:
  python3 generate.py [--author bentonyetman] [--week-start YYYY-MM-DD]

Without --week-start, targets the most recently completed Mon-Sun week
(i.e. running this on any day resolves to "last week"). Re-running for a
week that's already in data.json replaces that week's entry.
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
        "--limit", "200",
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--author", default="bentonyetman")
    parser.add_argument("--week-start", help="Monday of the target week, YYYY-MM-DD. Defaults to last full Mon-Sun week.")
    args = parser.parse_args()

    if args.week_start:
        start = datetime.date.fromisoformat(args.week_start)
        end = start + datetime.timedelta(days=6)
    else:
        start, end = last_full_week(datetime.date.today())

    prs = fetch_prs(args.author, start, end)
    entry = {
        "weekStart": start.isoformat(),
        "weekEnd": end.isoformat(),
        "author": args.author,
        "generatedAt": datetime.date.today().isoformat(),
        "prs": prs,
    }

    weeks = load_data()
    weeks = upsert_week(weeks, entry)
    DATA_PATH.write_text(json.dumps(weeks, indent=2))

    repos = {pr["repo"] for pr in prs}
    print(f"data.json: week {start.isoformat()} - {len(prs)} PRs across {len(repos)} repos ({len(weeks)} weeks total)", file=sys.stderr)
    print(f"Share: {SITE_BASE}?week={start.isoformat()}", file=sys.stderr)


if __name__ == "__main__":
    main()
