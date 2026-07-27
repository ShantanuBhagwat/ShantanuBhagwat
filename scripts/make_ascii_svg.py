"""
make_ascii_svg.py
Convert the prepped grayscale photo into a self-typing, monochrome ASCII
portrait SVG. Each row wipes in left-to-right with a small block cursor
riding the reveal edge, staggered top to bottom. Prints once and freezes.

Usage:
    python scripts/make_ascii_svg.py source-photo-prepped.png
Output:
    avi-ascii.svg   (renamed shantanu-ascii.svg for this profile)
"""
import sys
from PIL import Image

# bright (sparse) -> dark (dense); leading space clears the background to nothing
RAMP = " .`:-=+*cs#%@"

COLS = 90
CHAR_W = 8
CHAR_H = 15
FONT_SIZE = 14


def image_to_grid(path: str, cols: int):
    img = Image.open(path).convert("L")
    w, h = img.size
    char_aspect = CHAR_W / CHAR_H  # monospace cells are taller than wide
    rows = max(1, round(cols * (h / w) * char_aspect))
    small = img.resize((cols, rows), Image.LANCZOS)

    grid = []
    for y in range(rows):
        row_chars = []
        for x in range(cols):
            brightness = small.getpixel((x, y))  # 0=black .. 255=white
            idx = round((255 - brightness) / 255 * (len(RAMP) - 1))
            row_chars.append(RAMP[idx])
        grid.append("".join(row_chars))
    return grid


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_svg(grid) -> str:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    width = cols * CHAR_W
    height = rows * CHAR_H

    row_dur = 0.55
    row_stagger = 0.032  # seconds between each row starting

    defs = []
    groups = []

    for r, row_text in enumerate(grid):
        row_y = r * CHAR_H
        text_y = row_y + CHAR_H * 0.78
        delay = r * row_stagger
        clip_id = f"clip{r}"

        defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="0" y="{row_y}" width="0" height="{CHAR_H}">'
            f'<animate attributeName="width" from="0" to="{width}" '
            f'begin="{delay:.3f}s" dur="{row_dur}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1" keyTimes="0;1" />'
            f'</rect></clipPath>'
        )

        groups.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text class="ascii-row" x="0" y="{text_y:.1f}" '
            f'textLength="{width}" lengthAdjust="spacingAndGlyphs" '
            f'xml:space="preserve">{escape_xml(row_text)}</text>'
            f'</g>'
        )

        # block cursor riding the wipe edge, then fading out once the row finishes
        cursor_end = delay + row_dur
        groups.append(
            f'<rect class="cursor" y="{row_y + CHAR_H * 0.12:.1f}" '
            f'width="{CHAR_W * 0.7:.1f}" height="{CHAR_H * 0.8:.1f}">'
            f'<animate attributeName="x" from="0" to="{width - CHAR_W}" '
            f'begin="{delay:.3f}s" dur="{row_dur}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1" keyTimes="0;1" />'
            f'<animate attributeName="opacity" from="1" to="0" '
            f'begin="{cursor_end:.3f}s" dur="0.15s" fill="freeze" />'
            f'</rect>'
        )

    style = """
    <style>
      svg { background: transparent; }
      .ascii-row {
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace;
        font-size: %(font_size)spx;
        fill: #8b949e;
        white-space: pre;
      }
      .cursor { fill: #8b949e; }
      @media (prefers-color-scheme: light) {
        .ascii-row, .cursor { fill: #57606a; }
      }
    </style>
    """ % {"font_size": FONT_SIZE}

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
{style}
<defs>
{''.join(defs)}
</defs>
{''.join(groups)}
</svg>"""
    return svg


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "source-photo-prepped.png"
    grid = image_to_grid(src, COLS)
    svg = build_svg(grid)
    out_path = "shantanu-ascii.svg"
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"wrote {out_path} ({len(grid)} rows x {COLS} cols)")


if __name__ == "__main__":
    main()
