#!/bin/bash
# Weekly PR activity update — run by launchd every Sunday 9pm local time.
# Fetches last week's PRs, appends to data.json, commits + pushes if changed.
set -euo pipefail

REPO_DIR="/Users/byetman/_projects/reports"
cd "$REPO_DIR"

python3 pr-activity/generate.py

if git diff --quiet -- pr-activity/data.json; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') No change to data.json, skipping commit."
  exit 0
fi

WEEK_START=$(python3 -c "import json; d=json.load(open('pr-activity/data.json')); print(d[-1]['weekStart'])")

git add pr-activity/data.json
git commit -m "Add week ${WEEK_START} PR activity

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
git push

echo "$(date '+%Y-%m-%d %H:%M:%S') Pushed week ${WEEK_START}."
