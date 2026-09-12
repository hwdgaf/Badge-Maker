# Exotherm badge designer

Design badges for Minecraft mod listings. Paste any public Modrinth mod link, style the badge, copy the markdown.

![The badge designer](screenshot.png)

## Use it

Open `https://hwdgaf.github.io/Badge-Maker/` and:

1. Paste a Modrinth mod link and wait a second while name, icon, and colors fill in.
2. Style it: layout, colors, fonts, borders, positions. The preview updates live.
3. Download the SVG and copy the markdown into the listing.

No installs, no account, no server. The page runs entirely in the browser.

## What it does

- Fills name, version, icon, and link from any public Modrinth project
- Samples colors from the icon, with clickable candidate swatches
- 2000+ open webfonts plus your own uploads, embedded on request
- Bar and card layouts, gradients, borders, per-line type controls, live preview
- Outputs a standalone SVG plus link-wrapped markdown
- Sends the badge straight to the Modrinth project gallery, no download needed

## Needs internet for

Modrinth autofill, webfont search, hotlinked icons. Everything else runs offline. The eyedropper needs Chrome or Edge.

## Files

- `designer.html` — the app, one file
- `make-badge.py` — command-line twin, Python 3 with stdlib only
- `designer-link.txt` — the whole app as one paste-in-address-bar link

## License

MIT, copyright hwdgaf 2026. The full text sits in the header of `designer.html`.
