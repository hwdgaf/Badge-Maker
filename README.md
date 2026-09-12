# Exotherm badge designer

Design badges for Minecraft mod listings. Paste any public Modrinth mod link, style the badge, copy the markdown.

## Use it

- Hosted: `https://<you>.github.io/<repo>/badges/designer.html` once Pages is on
- Local: download `designer.html` and double-click it. No installs, no server.

## What it does

- Fills name, version, icon, and link from any public Modrinth project
- Samples colors from the icon, with clickable candidate swatches
- 2000+ open webfonts plus your own uploads, embedded on request
- Bar and card layouts, gradients, borders, per-line type controls, live preview
- Outputs a standalone SVG plus link-wrapped markdown

## Needs internet for

Modrinth autofill, webfont search, hotlinked icons. Everything else runs offline. The eyedropper needs Chrome or Edge.

## Files

- `designer.html` — the app, one file
- `make-badge.py` — command-line twin, Python 3 with stdlib only
- `designer-link.txt` — the whole app as one paste-in-address-bar link

## License

MIT, copyright hwdgaf 2026. The full text sits in the header of `designer.html`.
