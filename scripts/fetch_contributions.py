"""
fetch_contributions.py
Pull a real GitHub contribution calendar with no token and no GraphQL API.

GitHub serves the calendar as a public HTML fragment at:
    https://github.com/users/<username>/contributions
(the same fragment the profile page itself loads). We fetch it, parse the
day cells with BeautifulSoup, and write data/contributions.json with the raw
days plus a few derived stats (current streak, longest streak, best day,
total).

Usage:
    python scripts/fetch_contributions.py
Output:
    data/contributions.json
"""
import datetime
import json
import re
import sys

import requests
from bs4 import BeautifulSoup

USERNAME = "ShantanuBhagwat"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = "data/contributions.json"


def fetch_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"}, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_count(tooltip_text: str) -> int:
    if tooltip_text.lower().startswith("no contributions"):
        return 0
    m = re.match(r"(\d+)\s+contributions?", tooltip_text.strip())
    return int(m.group(1)) if m else 0


def parse_days(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # Map tool-tip "for" id -> contribution count text
    tooltip_by_id = {}
    for tip in soup.select("tool-tip"):
        target = tip.get("for")
        if target:
            tooltip_by_id[target] = tip.get_text(strip=True)

    cells = soup.select("td.ContributionCalendar-day[data-date]")
    days = []
    for cell in cells:
        date_str = cell["data-date"]
        cell_id = cell.get("id", "")
        tooltip_text = tooltip_by_id.get(cell_id, "")
        count = parse_count(tooltip_text) if tooltip_text else 0
        days.append({"date": date_str, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days):
    if not days:
        return {}

    total = sum(d["count"] for d in days)
    counts = [d["count"] for d in days]
    max_count = max(counts) if counts else 0

    # current streak: walk backwards from the most recent day
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # longest streak anywhere in the window
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"]) if max_count > 0 else None

    monthly_totals = {}
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + d["count"]

    return {
        "total": total,
        "max_count": max_count,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": monthly_totals,
    }


def build_grid(days):
    """Lay days out into a 7-row (Sun-Sat) x N-week grid, GitHub-style."""
    if not days:
        return []
    first_date = datetime.date.fromisoformat(days[0]["date"])
    # first_date from GitHub's fragment is always a Sunday-aligned window start
    grid = {}
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        weekday = (date.weekday() + 1) % 7  # Mon=0..Sun=6 -> Sun=0..Sat=6
        week_index = (date - first_date).days // 7
        grid.setdefault(week_index, {})[weekday] = d["count"]
    return grid


def levels_from_counts(days):
    """Re-bucket raw counts into 6 shading levels (0-5), the extra top tier
    being a 'neon' highlight reserved for the single best day, matching the
    six-color palette used by render_heatmap_svg.py."""
    nonzero = sorted(d["count"] for d in days if d["count"] > 0)
    if not nonzero:
        return {d["date"]: 0 for d in days}

    def quartile(p):
        idx = min(len(nonzero) - 1, int(len(nonzero) * p))
        return nonzero[idx]

    q1, q2, q3 = quartile(0.25), quartile(0.5), quartile(0.75)
    max_count = nonzero[-1]

    levels = {}
    for d in days:
        c = d["count"]
        if c == 0:
            levels[d["date"]] = 0
        elif c == max_count and max_count > q3:
            levels[d["date"]] = 5
        elif c >= q3:
            levels[d["date"]] = 4
        elif c >= q2:
            levels[d["date"]] = 3
        elif c >= q1:
            levels[d["date"]] = 2
        else:
            levels[d["date"]] = 1
    return levels


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    html = fetch_html(username)
    days = parse_days(html)
    if not days:
        print("No day cells found - GitHub markup may have changed.", file=sys.stderr)
        sys.exit(1)

    stats = compute_stats(days)
    levels = levels_from_counts(days)
    for d in days:
        d["level"] = levels[d["date"]]

    grid = build_grid(days)

    output = {
        "username": username,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
        "grid": grid,
    }
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"wrote {OUT_PATH} ({len(days)} days, {stats.get('total', 0)} contributions)")


if __name__ == "__main__":
    main()
