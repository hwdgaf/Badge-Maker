#!/usr/bin/env python3
"""Design a badge SVG like a tiny photo editor. No assets taken from anywhere.

The icon is hotlinked from a URL you paste, never downloaded or embedded
unless you pass --embed. Text values can be typed or pulled from any public
Modrinth slug with --slug (text only, its icon is never touched).

Usage:
    python badges/make-badge.py --icon URL --label TEXT --message TEXT --link URL
        [--slug SLUG] [--mc 26.2] [--loader fabric] [--field version|downloads|followers]
        [--bg COLOR] [--gradient FROM,TO] [--grad-dir vertical|horizontal]
        [--border WIDTH,COLOR] [--radius N] [--height N]
        [--font FAMILY] [--font-size N] [--font-color HEX]
        [--stroke COLOR,WIDTH] [--out badges] [--name NAME]

Colors are hex with or without '#'. Fonts render with the viewer's system
fonts (badges viewed as images can't load webfonts), so common stacks only.
"""

import base64
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

API = "https://api.modrinth.com/v2"
HERE = Path(__file__).resolve().parent


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "exotherm-lab-badge-maker"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read()


def human(n):
    for unit in ("", "k", "M"):
        if n < 1000:
            s = f"{n:.1f}".rstrip("0").rstrip(".")
            return f"{s}{unit}"
        n /= 1000
    return f"{n:.1f}B"


def opt(argv, name, default=None):
    return argv[name] if name in argv else default


def main(raw):
    argv = {}
    slug = icon = label = message = link = None
    it = iter(raw)
    for a in it:
        if a in ("-h", "--help"):
            print(__doc__.strip())
            return 0
        if a.startswith("--"):
            argv[a[2:]] = next(it, "")
    slug = opt(argv, "slug")
    icon = opt(argv, "icon")
    label = opt(argv, "label", "")
    message = opt(argv, "message", "")
    link = opt(argv, "link", "")

    if slug:  # text autofill from Modrinth; icon stays whatever --icon says
        try:
            proj = json.loads(get(f"{API}/project/{slug}"))
        except Exception:
            print(f"no public Modrinth project called '{slug}'")
            return 1
        field = opt(argv, "field", "version")
        if field == "downloads":
            message = message or human(proj["downloads"])
            label = label or "downloads"
        elif field == "followers":
            message = message or human(proj["followers"])
            label = label or "followers"
        else:
            label = label or proj["title"]
            q = {}
            if opt(argv, "loader"):
                q["loaders"] = json.dumps([argv["loader"]])
            if opt(argv, "mc"):
                q["game_versions"] = json.dumps([argv["mc"]])
            try:
                vs = json.loads(get(f"{API}/project/{slug}/version?" + urllib.parse.urlencode(q)))
                message = message or (vs[0]["version_number"] if vs else "?")
            except Exception:
                message = message or "?"
        link = link or f"https://modrinth.com/mod/{slug}"

    if not (label or message):
        print("give --label/--message or --slug")
        return 2

    bg = opt(argv, "bg", "3C8527").lstrip("#")
    grad = opt(argv, "gradient", "")
    gdir = opt(argv, "grad-dir", "horizontal")
    bw, bcol = (opt(argv, "border", "0,000000") + ",").split(",")[:2]
    bw, bcol = float(bw or 0), bcol.lstrip("#") or "000000"
    radius = float(opt(argv, "radius", 5))
    height = float(opt(argv, "height", 24))
    font = opt(argv, "font", "Verdana,DejaVu Sans,sans-serif")
    fsize = float(opt(argv, "font-size", 12))
    fcol = opt(argv, "font-color", "ffffff").lstrip("#")
    scol, sw = ((opt(argv, "stroke", ",0") + ",").split(",") + [""])[:2]
    scol, sw = scol.lstrip("#"), float(sw or 0)
    embed = "embed" in argv
    name = opt(argv, "name", slug or "badge")

    icon_href, icon_side = "", 0
    if icon:
        icon_side = height - 8
        if embed:  # your call: bakes the bytes in, file stands alone
            mime = "image/png" if ".png" in icon.lower() else "image/svg+xml" if ".svg" in icon.lower() else "image/jpeg"
            icon_href = f"data:{mime};base64," + base64.b64encode(get(icon)).decode()
        else:
            icon_href = icon

    # widths are estimates, padded kindly
    def w(t):
        return len(t) * fsize * 0.56 + 14

    pad, gap = 10, 10
    left, right = (w(label) if label else 0), (w(message) if message else 0)
    total = pad + icon_side + (gap if icon and (label or message) else 0) + left
    if label and message:
        total += gap + 1 + right  # 1px divider line
    elif message and not label:
        total += 0
    total = int(total + pad + bw * 2)

    x = pad + bw + icon_side + (gap if icon_side and (label or message) else 0)
    parts = []
    if grad and "," in grad:
        a, b = [c.strip().lstrip("#") for c in grad.split(",", 1)]
        x2, y2 = ("100%", "0") if gdir == "horizontal" else ("0", "100%")
        parts.append(f'<linearGradient id="g" x1="0" y1="0" x2="{x2}" y2="{y2}">'
                     f'<stop offset="0" stop-color="#{escape(a)}"/>'
                     f'<stop offset="1" stop-color="#{escape(b)}"/></linearGradient>')
        fill = "url(#g)"
    else:
        fill = f"#{escape(bg)}"

    body = [f'<rect x="{bw / 2}" y="{bw / 2}" width="{total - bw}" height="{height - bw}"'
            f' rx="{radius}" fill="{fill}"']
    body[-1] += f' stroke="#{escape(bcol)}" stroke-width="{bw}"/>' if bw > 0 else "/>"
    if icon_side:
        body.append(f'<image x="{pad + bw}" y="{(height - icon_side) / 2:.1f}"'
                    f' width="{icon_side:.0f}" height="{icon_side:.0f}"'
                    f" href={quoteattr(icon_href)}"
                    f" alt={quoteattr((label + ' ' + message).strip())}/>")
    ty = height / 2 + fsize * 0.35
    stroke = (f' paint-order="stroke" stroke="#{escape(scol)}" stroke-width="{sw}"' if scol and sw > 0 else "")
    if label:
        body.append(f'<text x="{x:.1f}" y="{ty:.1f}" font-weight="bold"{stroke}>{escape(label)}</text>')
        x += left + gap
    if label and message:
        body.append(f'<line x1="{x - gap + 1:.1f}" y1="5" x2="{x - gap + 1:.1f}"'
                    f' y2="{height - 5:.0f}" stroke="#{fcol}" stroke-opacity="0.4"/>')
    if message:
        body.append(f'<text x="{x:.1f}" y="{ty:.1f}"{stroke}>{escape(message)}</text>')

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="{height:.0f}"'
           f' role="img" aria-label={quoteattr((label + ": " + message).strip(": "))}>'
           + (f"<defs>{parts[0]}</defs>" if parts else "")
           + f"<g>{''.join(body)}</g>"
           + f'<style>text{{font-family:{escape(font)};font-size:{fsize:.0f}px;fill:#{escape(fcol)}}}</style></svg>')

    out = Path(opt(argv, "out", str(HERE)))
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{name}.svg"
    dest.write_text(svg, encoding="utf-8")
    print(f"wrote {dest} ({dest.stat().st_size} bytes)")
    print()
    md = f"![{label + ' ' + message}]".strip() + f"({dest.name})"
    print(f"[{md}]({link})" if link else md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
