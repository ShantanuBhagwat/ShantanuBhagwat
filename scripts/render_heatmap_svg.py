"""
render_heatmap_svg.py
Render data/contributions.json as a real 53-week x 7-day calendar of rounded
boxes, with a diagonal line-after-line slide-in reveal (plays once on load,
then freezes) and a Less -> More legend + stats footer.

Usage:
    python scripts/render_heatmap_svg.py
Output:
    contrib-heatmap.svg
"""
import json

IN_PATH = "data/contributions.json"
OUT_PATH = "contrib-heatmap.svg"

BOX = 11
GAP = 3
CELL = BOX + GAP
RADIUS = 2
LEFT_PAD = 28   # room for weekday labels
TOP_PAD = 22    # room for month labels
RIGHT_PAD = 8
FOOTER_H = 34
LEGEND_H = 20

# level -> (light-mode color, dark-mode color)
PALETTE_LIGHT = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39", "#3fff9e"]
PALETTE_DARK = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # row index -> label (Sun=0)


def load_data():
    with open(IN_PATH) as f:
        return json.load(f)


def month_label_columns(days):
    """Return {week_index: 'Jan'} for the first column where a new month starts."""
    import datetime
    first_date = datetime.date.fromisoformat(days[0]["date"])
    labels = {}
    last_month = None
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        week_index = (date - first_date).days // 7
        if date.month != last_month:
            labels.setdefault(week_index, MONTH_ABBR[date.month - 1])
            last_month = date.month
    return labels


def build_svg(data) -> str:
    days = data["days"]
    grid = {int(k): v for k, v in data["grid"].items()}
    stats = data["stats"]
    num_weeks = max(grid.keys()) + 1 if grid else 53

    width = LEFT_PAD + num_weeks * CELL + RIGHT_PAD
    height = TOP_PAD + 7 * CELL + LEGEND_H + FOOTER_H

    month_cols = month_label_columns(days)

    boxes = []
    order = []  # (week, weekday) in diagonal reveal order
    for week in range(num_weeks):
        for weekday in range(7):
            order.append((week, weekday))
    # diagonal wave: earlier weeks + earlier weekdays reveal first
    order.sort(key=lambda wd: wd[0] + wd[1])
    delay_index = {wd: i for i, wd in enumerate(order)}

    total_cells = len(order) or 1
    total_anim_time = 2.4  # seconds for the whole diagonal sweep
    step = total_anim_time / total_cells
    dur = 0.35

    for week in range(num_weeks):
        for weekday in range(7):
            x = LEFT_PAD + week * CELL
            y = TOP_PAD + weekday * CELL
            idx = delay_index[(week, weekday)]
            delay = idx * step
            boxes.append((week, weekday, x, y, delay))

    # map (week, weekday) -> level using the days list directly
    import datetime
    first_date = datetime.date.fromisoformat(days[0]["date"])
    level_by_cell = {}
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        wd = (date.weekday() + 1) % 7
        wk = (date - first_date).days // 7
        level_by_cell[(wk, wd)] = d["level"]

    rects = []
    for week, weekday, x, y, delay in boxes:
        level = level_by_cell.get((week, weekday), 0)
        rects.append(
            f'<rect class="cell L{level}" x="{x}" y="{y}" width="{BOX}" height="{BOX}" '
            f'rx="{RADIUS}" ry="{RADIUS}" style="animation-delay:{delay:.3f}s" />'
        )

    month_labels = []
    for week, label in month_cols.items():
        if week + 3 > num_weeks:  # skip a trailing label with no room
            continue
        x = LEFT_PAD + week * CELL
        month_labels.append(f'<text class="month-label" x="{x}" y="{TOP_PAD - 8}">{label}</text>')

    weekday_labels = []
    for row, label in WEEKDAY_LABELS.items():
        y = TOP_PAD + row * CELL + BOX - 1
        weekday_labels.append(f'<text class="weekday-label" x="{LEFT_PAD - 6}" y="{y}" text-anchor="end">{label}</text>')

    legend_y = TOP_PAD + 7 * CELL + 14
    legend_x_start = width - RIGHT_PAD - (6 * (BOX + 4) + 60)
    legend_boxes = []
    lx = legend_x_start + 34
    for lvl in range(6):
        legend_boxes.append(
            f'<rect class="cell L{lvl}" x="{lx}" y="{legend_y - BOX + 2}" width="{BOX}" height="{BOX}" rx="{RADIUS}" ry="{RADIUS}" />'
        )
        lx += BOX + 4
    legend = (
        f'<text class="legend-text" x="{legend_x_start}" y="{legend_y}">Less</text>'
        + "".join(legend_boxes)
        + f'<text class="legend-text" x="{lx + 4}" y="{legend_y}">More</text>'
    )

    total = stats.get("total", 0)
    streak = stats.get("longest_streak", 0)
    current = stats.get("current_streak", 0)
    footer_y1 = height - FOOTER_H + 14
    footer_y2 = height - 6
    footer = (
        f'<text class="footer-main" x="{LEFT_PAD}" y="{footer_y1}">{total} contributions in the last year</text>'
        f'<text class="footer-sub" x="{LEFT_PAD}" y="{footer_y2}">longest streak {streak} day{"s" if streak != 1 else ""} '
        f"&#183; current streak {current} day{'s' if current != 1 else ''}</text>"
    )

    style = f"""
    <style>
      svg {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace; }}
      :root {{
        --l0: {PALETTE_LIGHT[0]}; --l1: {PALETTE_LIGHT[1]}; --l2: {PALETTE_LIGHT[2]};
        --l3: {PALETTE_LIGHT[3]}; --l4: {PALETTE_LIGHT[4]}; --l5: {PALETTE_LIGHT[5]};
        --fg: #57606a; --fg-strong: #24292f;
      }}
      @media (prefers-color-scheme: dark) {{
        :root {{
          --l0: {PALETTE_DARK[0]}; --l1: {PALETTE_DARK[1]}; --l2: {PALETTE_DARK[2]};
          --l3: {PALETTE_DARK[3]}; --l4: {PALETTE_DARK[4]}; --l5: {PALETTE_DARK[5]};
          --fg: #8b949e; --fg-strong: #c9d1d9;
        }}
      }}
      .cell {{ opacity: 0; transform: translate(0px, -6px); animation: reveal {dur}s ease-out forwards; }}
      .L0 {{ fill: var(--l0); }}
      .L1 {{ fill: var(--l1); }}
      .L2 {{ fill: var(--l2); }}
      .L3 {{ fill: var(--l3); }}
      .L4 {{ fill: var(--l4); }}
      .L5 {{ fill: var(--l5); }}
      @keyframes reveal {{
        0%   {{ opacity: 0; transform: translate(0px, -6px); }}
        100% {{ opacity: 1; transform: translate(0px, 0px); }}
      }}
      .month-label, .weekday-label {{ font-size: 10px; fill: var(--fg); }}
      .legend-text {{ font-size: 10px; fill: var(--fg); }}
      .footer-main {{ font-size: 12px; fill: var(--fg-strong); }}
      .footer-sub {{ font-size: 10px; fill: var(--fg); }}
    </style>
    """

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
{style}
{''.join(month_labels)}
{''.join(weekday_labels)}
{''.join(rects)}
{legend}
{footer}
</svg>"""
    return svg


def main():
    data = load_data()
    svg = build_svg(data)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
