#!/usr/bin/env python3
"""Weekly PR activity report generator.

Pulls PRs authored by a given GitHub user that saw activity in a Mon-Sun
week window, groups by repo, and renders an HTML artifact matching the
style of the other reports in this repo.

Usage:
  python3 generate.py [--author bentonyetman] [--week-start YYYY-MM-DD]

Without --week-start, targets the most recently completed Mon-Sun week
(i.e. running this on any day resolves to "last week").
"""
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

OUT_DIR = Path(__file__).parent


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
    return json.loads(result.stdout)


def group_by_repo(prs: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for pr in prs:
        repo = pr["repository"]["nameWithOwner"]
        grouped.setdefault(repo, []).append(pr)
    return dict(sorted(grouped.items(), key=lambda kv: len(kv[1]), reverse=True))


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def render(author: str, start: datetime.date, end: datetime.date, grouped: dict[str, list[dict]]) -> str:
    total = sum(len(v) for v in grouped.values())
    merged = sum(1 for v in grouped.values() for pr in v if pr["state"] == "merged")
    closed_unmerged = sum(1 for v in grouped.values() for pr in v if pr["state"] == "closed")
    open_prs = sum(1 for v in grouped.values() for pr in v if pr["state"] == "open")
    comments = sum(pr["commentsCount"] for v in grouped.values() for pr in v)
    repo_count = len(grouped)

    max_repo = max((len(v) for v in grouped.values()), default=1)

    bars = []
    for repo, prs in grouped.items():
        pct = round(100 * len(prs) / max_repo)
        bars.append(f"""
<div class="repo-row">
  <div class="repo-name">{esc(repo)}</div>
  <div class="repo-bar-track"><div class="repo-bar-fill" style="width:{pct}%"></div></div>
  <div class="repo-count">{len(prs)}</div>
</div>""")

    rows = []
    for repo, prs in grouped.items():
        for pr in sorted(prs, key=lambda p: p["updatedAt"], reverse=True):
            badge_class = {"merged": "badge-merged", "closed": "badge-closed", "open": "badge-open"}[pr["state"]]
            badge_label = {"merged": "Merged", "closed": "Closed", "open": "Open"}[pr["state"]]
            rows.append(f"""
<tr>
  <td>{esc(repo)}</td>
  <td><a href="{pr['url']}">#{pr['number']} {esc(pr['title'])}</a></td>
  <td><span class="badge {badge_class}">{badge_label}</span></td>
  <td>{pr['updatedAt'][:10]}</td>
  <td>{pr['commentsCount']}</td>
</tr>""")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Weekly PR Activity - {esc(author)}</title>
<style>
  body {{ margin: 0; background: #f8fafc; color: #0f172a;
    font: 15px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }}
  .page {{ max-width: 920px; margin: 0 auto; background: white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06); padding: 48px 56px; }}
  h1 {{ font-size: 28px; margin: 0 0 4px; }}
  h2 {{ font-size: 18px; margin: 32px 0 8px; padding-bottom: 6px; border-bottom: 1px solid #e2e8f0; }}
  .sub {{ color: #64748b; font-size: 13px; }}
  .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 24px 0; }}
  .stat {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px 18px; }}
  .stat .label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: #64748b; }}
  .stat .value {{ font-size: 26px; font-weight: 600; line-height: 1.3; }}
  .repo-row {{ display: grid; grid-template-columns: 220px 1fr 32px; align-items: center; gap: 12px; margin: 8px 0; }}
  .repo-name {{ font-size: 13px; color: #334155; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .repo-bar-track {{ background: #e5e7eb; border-radius: 999px; height: 10px; overflow: hidden; }}
  .repo-bar-fill {{ background: #2563eb; height: 100%; border-radius: 999px; }}
  .repo-count {{ font-size: 13px; font-weight: 600; text-align: right; color: #334155; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }}
  th, td {{ padding: 8px 10px; border-bottom: 1px solid #e2e8f0; text-align: left; vertical-align: top; }}
  th {{ background: #f8fafc; font-size: 11px; text-transform: uppercase; letter-spacing: 0.4px; color: #64748b; }}
  td a {{ color: #0f172a; text-decoration: none; }}
  td a:hover {{ text-decoration: underline; }}
  .badge {{ color: white; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; letter-spacing: 0.3px; white-space: nowrap; }}
  .badge-merged {{ background: #7c3aed; }}
  .badge-closed {{ background: #64748b; }}
  .badge-open {{ background: #16a34a; }}
  .footer {{ color: #94a3b8; font-size: 11px; margin-top: 24px; text-align: center; }}
  @media print {{ body {{ background: white; }} .page {{ box-shadow: none; padding: 24px; }} }}
</style>
</head>
<body>
<div class="page">

<h1>Weekly PR Activity</h1>
<div class="sub">{esc(author)} &middot; week of {start.isoformat()} to {end.isoformat()} &middot; generated {datetime.date.today().isoformat()}</div>

<div class="stats">
  <div class="stat"><div class="label">Total PRs</div><div class="value">{total}</div></div>
  <div class="stat"><div class="label">Merged</div><div class="value">{merged}</div></div>
  <div class="stat"><div class="label">Closed (unmerged)</div><div class="value">{closed_unmerged}</div></div>
  <div class="stat"><div class="label">Repos touched</div><div class="value">{repo_count}</div></div>
</div>

<h2>By repo</h2>
{''.join(bars)}

<h2>All PRs</h2>
<table>
<thead><tr><th>Repo</th><th>PR</th><th>State</th><th>Last activity</th><th>Comments</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>

<div class="footer">{total} PRs &middot; {repo_count} repos &middot; {comments} total comments &middot; open PRs in window: {open_prs}</div>

</div>
</body>
</html>
"""


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
    grouped = group_by_repo(prs)
    html = render(args.author, start, end, grouped)

    out_path = OUT_DIR / f"{start.isoformat()}-pr-activity.html"
    out_path.write_text(html)
    print(f"Wrote {out_path} ({len(prs)} PRs across {len(grouped)} repos)", file=sys.stderr)


if __name__ == "__main__":
    main()
