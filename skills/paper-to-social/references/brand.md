# BRAIn Lab brand (use this for all visuals)

The lab is **BRAIn** — "basic research of artificial intelligence". Use this palette and logo for every carousel, card, and figure framing. Do not invent colors or use the old purple/lavender scheme.

## Palette (from `assets/palette.jpg`)

| Hex | Name | Use |
|-----|------|-----|
| `#8D4865` | Vintage Berry | primary brand color: title/accent card backgrounds, headings on light, highlight blocks, body text on cream (dark plum `#3a2330` also ok for body) |
| `#F7C57C` | Apricot Cream | accent: logo letters, big display text fill, badges, icon chips, highlight numbers |
| `#FBEDD6` | Papaya Whip | soft block backgrounds, equation boxes, decorative blobs |
| `#FBF8F1` | Floral White | content card background |
| `#9EE1FC` | Frosted Blue | secondary accent: outlines/strokes (logo outline, text-stroke on display titles, QR borders, equation borders) |

Signature look: **apricot fill with a frosted-blue outline** (the logo's letters). Echo it on big display titles: `color:#F7C57C; -webkit-text-stroke:7px #9EE1FC; paint-order:stroke fill`. Body text berry on cream, white on berry.

## Logo (use the real one, never a placeholder)

- `assets/brain_logo.png` — full transparent logo (graph-node "B" mark + "BRAIn" wordmark + tagline). For title cards / large placements.
- `assets/brain_logo_notag.png` — transparent, no tagline. For card corners (top-right, ~50px tall).
- `assets/brain_logo_original.png` — source (logo on berry background), if you need to re-extract.

The mark is a graph of nodes/edges forming a "B" (neural-network motif). Apricot letters, frosted-blue outline.

## Optional decorative motif

The lab's slide decks use light decorative elements (transformer/letter shapes, node graphs). You may add subtle versions (faint outlined letters, node-graph lines, soft brand-colored blobs) for texture. Keep it subtle. Non-critical — only if it helps, never at the expense of readability.

## Carousel mapping (what worked on softsign)

- Title + TL;DR cards: berry background, apricot+blue-outline display text, white subtitles, real logo, QR (berry modules on cream, blue border).
- Content cards: floral-white background, berry headings, papaya/blue equation boxes, berry highlight blocks with white text, berry ✓ circles, papaya icon chips, real logo top-right.
- Blobs: soft apricot, frosted-blue, papaya circles (not lavender).

Build recipe and CSS gotchas: see `images.md`. Reference build script: `Papers/softsign/linkedin-carousel/build_carousel.py`.
