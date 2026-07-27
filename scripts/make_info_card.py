"""
make_info_card.py
Hand-authored neofetch-style info panel: a terminal title bar, then colored
key/value rows. Each line fades + slides in on a short stagger so it looks
like it's printing next to the ASCII portrait. Plays once, then freezes.

Set STATIC=1 to emit a frozen (already-revealed) frame for local previews.

Usage:
    python scripts/make_info_card.py
Output:
    info-card.svg
"""
import os

WIDTH = 490
HEADER_H = 34
ROW_H = 34
PAD_X = 20
TITLE = "shantanu@github ~"

# (label, value) rows - the story numbers on the heatmap can't tell
ROWS = [
    ("Now", "B.Tech CSE @ VIT Vellore, class of 2027"),
    ("Prev", "SDE Intern @ NCDEX - AP Revamp project"),
    ("Stack", "Java, Python, React, Node, Spring Boot"),
    ("Highlights", "Patent published + AI anomaly detection"),
]

STATIC = os.environ.get("STATIC") == "1"


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_svg() -> str:
    height = HEADER_H + len(ROWS) * ROW_H + 18

    style = """
    <style>
      svg { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace; }
      :root {
        --panel-bg: #0d1117; --header-bg: #161b22; --border: #30363d;
        --title: #8b949e; --label: #79c0ff; --value: #c9d1d9;
      }
      @media (prefers-color-scheme: light) {
        :root {
          --panel-bg: #f6f8fa; --header-bg: #eaeef2; --border: #d0d7de;
          --title: #57606a; --label: #0969da; --value: #24292f;
        }
      }
      .panel { fill: var(--panel-bg); stroke: var(--border); stroke-width: 1; }
      .header { fill: var(--header-bg); }
      .dot-red { fill: #ff5f56; } .dot-yellow { fill: #ffbd2e; } .dot-green { fill: #27c93f; }
      .title { fill: var(--title); font-size: 12px; }
      .label { fill: var(--label); font-size: 13px; font-weight: 600; }
      .value { fill: var(--value); font-size: 13px; }
      .row { opacity: %(row_start_opacity)s; }
      @keyframes lineIn {
        0%%   { opacity: 0; transform: translateX(-6px); }
        100%% { opacity: 1; transform: translateX(0); }
      }
      .row { animation: lineIn 0.4s ease-out forwards; }
    </style>
    """ % {"row_start_opacity": "1" if STATIC else "0"}

    if STATIC:
        style = style.replace(".row { animation: lineIn 0.4s ease-out forwards; }", "")

    header = f"""
    <rect class="header" x="0" y="0" width="{WIDTH}" height="{HEADER_H}" rx="8" ry="8" />
    <rect class="header" x="0" y="{HEADER_H - 8}" width="{WIDTH}" height="8" />
    <circle class="dot-red" cx="18" cy="{HEADER_H/2}" r="5.5" />
    <circle class="dot-yellow" cx="36" cy="{HEADER_H/2}" r="5.5" />
    <circle class="dot-green" cx="54" cy="{HEADER_H/2}" r="5.5" />
    <text class="title" x="{WIDTH/2}" y="{HEADER_H/2 + 4}" text-anchor="middle">{escape_xml(TITLE)}</text>
    """

    rows_svg = []
    base_delay = 0.35
    stagger = 0.16
    for i, (label, value) in enumerate(ROWS):
        y = HEADER_H + 28 + i * ROW_H
        delay = base_delay + i * stagger
        style_attr = "" if STATIC else f'style="animation-delay:{delay:.2f}s"'
        rows_svg.append(
            f'<g class="row" {style_attr}>'
            f'<text class="label" x="{PAD_X}" y="{y}">{escape_xml(label)}</text>'
            f'<text class="value" x="{PAD_X + 108}" y="{y}">{escape_xml(value)}</text>'
            f'</g>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}">
{style}
<rect class="panel" x="0.5" y="0.5" width="{WIDTH-1}" height="{height-1}" rx="8" ry="8" />
{header}
{''.join(rows_svg)}
</svg>"""
    return svg


def main():
    svg = build_svg()
    out_path = "info-card.svg"
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"wrote {out_path}{' (static frame)' if STATIC else ''}")


if __name__ == "__main__":
    main()
