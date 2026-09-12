#!/usr/bin/env python3
"""Command-line twin of designer.html. Same geometry, no browser needed.

Icons stay hotlinked URLs and widths are estimated (the designer measures
for real), everything else matches: layouts, fills, borders, per-line type,
trimming, contrast text. Icon color sampling needs a canvas, so use the
designer for that or pass --bg yourself.

Usage:
    python badges/make-badge.py --label TEXT --message TEXT [options]

Common options:
    --icon URL --link URL --slug SLUG [--field version|downloads|followers]
    --mc 26.2 --loader fabric --layout bar|card --out badges --name NAME
    --bg HEX [--gradient FROM,TO] [--grad-dir vertical|horizontal]
    --border WIDTH,COLOR --radius N --height N (0=auto) --width N (0=auto)
    --maxw N (0=off) --icon-size N (0=auto)
    --m-font F --m-size N --m-color HEX [--m-bold] [--m-italic]
    --l-font F --l-size N --l-color HEX [--l-bold] [--l-italic]
    --stroke COLOR,WIDTH
"""

import json
import math
import re
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


def lum(hexv):
    return 0.2126 * hexv[0] + 0.7152 * hexv[1] + 0.0722 * hexv[2]


def shade(hexv, t):
    out = []
    for c in hexv:
        n = c + (255 - c) * t if t >= 0 else c * (1 + t)
        out.append(max(0, min(255, round(n))))
    return out


def tohex(rgb):
    return "#" + "".join(f"{c:02x}" for c in rgb)


def parsehex(s):
    s = s.strip().lstrip("#")
    return [int(s[i:i + 2], 16) for i in (0, 2, 4)]


def clamp_fill(hexv):
    L = lum(hexv)
    if 32 <= L <= 224:
        return hexv
    if L <= 0:
        return [32, 32, 32]
    f = 32 / L if L < 32 else 224 / L
    return [round(min(255, c * f)) for c in hexv]


def main(raw):
    o = {
        "label": "", "message": "Required", "icon": "", "link": "", "slug": "",
        "field": "version", "mc": "", "loader": "", "layout": "bar",
        "out": str(HERE), "name": "badge", "bg": "3C8527", "gradient": "",
        "grad-dir": "vertical", "border": "4,0E2F0E", "radius": "12",
        "height": "0", "width": "0", "maxw": "0", "icon-size": "0",
        "m-font": "Arial", "m-size": "18", "m-color": "", "l-font": "Arial",
        "l-size": "20", "l-color": "", "stroke": ",0",
    }
    flags = {"m-bold", "m-italic", "l-bold", "l-italic"}
    on = set()
    it = iter(raw)
    for a in it:
        k = a[2:] if a.startswith("--") else None
        if k in o:
            o[k] = next(it, "")
        elif k in flags:
            on.add(k)
    for k in ("m-bold", "m-italic", "l-bold", "l-italic"):
        o[k] = k in on
    if not o["label"] and not o["message"] and not o["slug"]:
        print("give --label/--message or --slug")
        return 2

    if o["slug"]:
        slug = o["slug"]
        m = re.search(r"modrinth\.com/mod/([^/?#]+)", slug)
        if m:
            slug = m.group(1)
        try:
            proj = json.loads(get(f"{API}/project/{slug}"))
        except Exception:
            print(f"no public Modrinth project called '{slug}'")
            return 1
        if o["field"] == "downloads":
            o["message"], o["label"] = human(proj["downloads"]), o["label"] or "downloads"
        elif o["field"] == "followers":
            o["message"], o["label"] = human(proj["followers"]), o["label"] or "followers"
        else:
            o["label"] = proj["title"]
            if o["mc"] or o["loader"]:
                q = {}
                if o["loader"]:
                    q["loaders"] = json.dumps([o["loader"]])
                if o["mc"]:
                    q["game_versions"] = json.dumps([o["mc"]])
                try:
                    vs = json.loads(get(f"{API}/project/{slug}/version?" + urllib.parse.urlencode(q)))
                    o["message"] = vs[0]["version_number"] if vs else "?"
                except Exception:
                    o["message"] = o["message"] or "?"
            else:
                o["message"] = "Required"
                if "--name" not in raw:
                    o["name"] = f"{slug}-required"
        o["link"] = o["link"] or f"https://modrinth.com/mod/{slug}"
        o["icon"] = o["icon"] or proj.get("icon_url", "")

    label, message = o["label"], o["message"]
    msize, lsize = float(o["m-size"]), float(o["l-size"])
    bw_raw, bcol_raw = (o["border"] + ",").split(",")[:2]
    bw, bcol = float(bw_raw or 0), (bcol_raw or "000000").lstrip("#")
    radius = float(o["radius"])
    card = o["layout"] == "card"
    pad, gap = 10, 10

    def w(t, s):
        return len(t) * s * 0.56 + 14

    wM = lambda t: w(t, msize)
    wL = lambda t: w(t, lsize)

    icon = o["icon"].strip()
    auto_h = float(o["height"]) <= 0
    maxsize = max(msize if message else 0, lsize if label else 0)
    text_h = math.ceil(maxsize * 1.3 + 8)
    if icon and int(o["icon-size"]) <= 0:
        side = 48 if card else max(text_h - 8, 12)
    else:
        side = float(o["icon-size"]) if icon else 0
    H = float(o["height"]) if not auto_h else None
    if auto_h and not card:
        H = max(text_h, side + 16 if side else 0, 16) + bw * 2

    def fa(f, s, c, b, i):
        a = f' font-family="{f},DejaVu Sans,sans-serif" font-size="{s:g}" fill="#{c}"'
        if b:
            a += ' font-weight="bold"'
        if i:
            a += ' font-style="italic"'
        return a

    lab, msg = label, message
    if card:
        def retotal():
            return math.ceil(max(side, wM(msg) if msg else 0, wL(lab) if lab else 0) + pad * 2 + bw * 2)
    else:
        def retotal():
            t = pad + side + (gap if icon and (lab or msg) else 0)
            if lab:
                t += wL(lab)
            if msg:
                t += wM(msg)
            if lab and msg:
                t += gap + 1
            return round(t + pad + bw * 2)
    total = retotal()
    maxw = float(o["maxw"])
    limit = float(o["width"]) if float(o["width"]) > 0 else (maxw if maxw > 0 else float("inf"))
    if total > limit:
        guard = 500
        while total > limit - 12 and guard > 0:
            guard -= 1
            wm = wM(msg) if msg else -1
            wl = wL(lab) if lab else -1
            if wm < 20 and wl < 20:
                break
            if wm >= wl and len(msg) > 1:
                msg = msg[:-1]
            elif len(lab) > 1:
                lab = lab[:-1]
            elif len(msg) > 1:
                msg = msg[:-1]
            else:
                break
            total = retotal()
        if msg != message:
            msg += "…"
        if lab != label:
            lab += "…"
        total = retotal()
    if float(o["width"]) > 0:
        total = max(total, float(o["width"]))
    if card:
        rows = (side + gap if side else 0) + (msize * 1.25 if msg else 0)
        rows += 4 if msg and lab else 0
        rows += lsize * 1.25 if lab else 0
        svg_h = math.ceil(rows + pad * 2 + bw * 2)
    else:
        svg_h = H

    bgc = tohex(clamp_fill(parsehex(o["bg"])))
    grad = [p.strip().lstrip("#") for p in o["gradient"].split(",") if p.strip()] if o["gradient"] else []
    gA = tohex(clamp_fill(parsehex(grad[0]))) if len(grad) > 0 else bgc
    gB = tohex(clamp_fill(parsehex(grad[1]))) if len(grad) > 1 else bgc
    horiz = o["grad-dir"] == "horizontal"
    defs = (f'<defs><linearGradient id="g" x1="0" y1="0" x2="{"100%" if horiz else "0"}"'
            f' y2="{"0" if horiz else "100%"}"><stop offset="0" stop-color="{gA}"/>'
            f'<stop offset="1" stop-color="{gB}"/></linearGradient></defs>') if grad else ""
    use_grad = bool(grad)

    # text follows the background: exact inverse when readable, else black/white
    def text_for(bg_hex, explicit):
        if explicit:
            return explicit.lstrip("#")
        v = parsehex(bg_hex)
        inv = [255 - c for c in v]

        def rl(c):
            s = []
            for x in c:
                x /= 255
                s.append(x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4)
            return 0.2126 * s[0] + 0.7152 * s[1] + 0.0722 * s[2]

        a, b = rl(v), rl(inv)
        ratio = (max(a, b) + 0.05) / (min(a, b) + 0.05)
        if ratio >= 3:
            return tohex(inv).lstrip("#")
        return "1a1a1a" if lum(v) > 150 else "ffffff"

    mCol = text_for(bgc, o["m-color"] if "--m-color" in raw else "")
    lCol = text_for(bgc, o["l-color"] if "--l-color" in raw else "")
    scol_raw, sw_raw = (o["stroke"] + ",").split(",")[:2]
    sw = float(sw_raw or 0)
    st = f' paint-order="stroke" stroke="#{scol_raw.lstrip("#")}" stroke-width="{sw:g}"' if sw > 0 else ""
    alt = escape(f"{label} {message}".strip())

    parts = [f'<rect x="{bw / 2:g}" y="{bw / 2:g}" width="{total - bw:g}" height="{svg_h - bw:g}"'
             f' rx="{radius:g}" fill="{"url(#g)" if use_grad else bgc}"']
    parts[-1] += f' stroke="#{bcol}" stroke-width="{bw:g}"/>' if bw > 0 else "/>"
    if card:
        y = pad + bw
        if side:
            parts.append(f'<image x="{(total - side) / 2:.1f}" y="{y:.1f}" width="{side:g}" height="{side:g}"'
                         f" href={quoteattr(icon)} alt={quoteattr(f'{lab} {msg}'.strip())}/>")
            y += side + gap
        if msg:
            parts.append(f'<text x="{total / 2:g}" y="{y + msize:.1f}" text-anchor="middle"'
                         f"{fa(o['m-font'], msize, mCol, o['m-bold'], o['m-italic'])}{st}>{escape(msg)}</text>")
            y += msize * 1.25 + 4
        if lab:
            parts.append(f'<text x="{total / 2:g}" y="{y + lsize:.1f}" text-anchor="middle"'
                         f"{fa(o['l-font'], lsize, lCol, o['l-bold'], o['l-italic'])}{st}>{escape(lab)}</text>")
    else:
        x = pad + bw + side + (gap if side and (lab or msg) else 0)
        if side:
            parts.append(f'<image x="{pad + bw:g}" y="{(H - side) / 2:.1f}" width="{side:g}" height="{side:g}"'
                         f" href={quoteattr(icon)} alt={quoteattr(f'{lab} {msg}'.strip())}/>")
        ty = H / 2
        if lab:
            parts.append(f'<text x="{x:.1f}" y="{ty + lsize * 0.35:.1f}"'
                         f"{fa(o['l-font'], lsize, lCol, o['l-bold'], o['l-italic'])}{st}>{escape(lab)}</text>")
            x += wL(lab) + gap
        if msg:
            parts.append(f'<text x="{x:.1f}" y="{ty + msize * 0.35:.1f}"'
                         f"{fa(o['m-font'], msize, mCol, o['m-bold'], o['m-italic'])}{st}>{escape(msg)}</text>")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{total:g}" height="{svg_h:g}" role="img"'
           f' aria-label="{escape(f"{label}: {message}".strip(": "))}">{defs}<g>{"".join(parts)}</g></svg>')

    out = Path(o["out"])
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{o['name']}.svg"
    dest.write_text(svg, encoding="utf-8")
    print(f"wrote {dest} ({dest.stat().st_size} bytes)")
    print()
    print(f"[![{label} {message}".strip() + f"]({dest.name})]({o['link']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
