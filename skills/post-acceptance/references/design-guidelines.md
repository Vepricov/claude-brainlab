# Design Guidelines

## Beamer-first rule

For research presentations, prefer LaTeX Beamer unless the user explicitly asks for another format. The default deck should be readable, easy to compile, and easy to maintain from paper assets.

## Terminal Style

When the user asks for `terminal style` or `терминальный стиль`, use `~/.claude/skills/presentation/examples/terminal-style-mini.tex` as the exact reference.

Implement the style with these concrete settings:

- document class: `\documentclass[aspectratio=169]{beamer}`
- theme: `\usetheme{metropolis}`
- progress bar: `\metroset{progressbar=frametitle, sectionpage=none, numbering=counter}`
- title font: `\ttfamily`, bold, compact
- frame title font: `\ttfamily`, bold, compact
- normal text: foreground `#E6EDF3`, background `#0D1117`
- frame title bar: background `#161B22`, foreground `#00FF88`
- title separator: `#00FF88`
- progress bar: foreground `#00FF88`, background `#161B22`
- alerted text: `#FF7B54`
- example text: `#3FB950`

### Box styles

Use `tcolorbox` with two recurring styles:

- theorem-style box:
  - dark blue-gray fill `#1C2A3A`
  - dark title background `#161B22`
  - orange frame and title `#FF7B54`
  - monospace bold small title
- idea-style box:
  - dark background `#0D1117`
  - green frame and title `#00FF88`
  - monospace bold small title

### Figure and text conventions

- figure captions should be short, muted, small, and usually monospace
- prefer two-column frames
- prefer one figure plus one text block over dense bullet walls
- use small highlighted takeaway boxes instead of long prose paragraphs
- keep titles compact, not oversized

## Layout rules

- One idea per frame
- Prefer 3 to 5 bullets, not 8 to 10
- Prefer short claims and visual evidence over prose
- If a frame contains a theorem, include only the statement or proof idea, not both in full unless the user explicitly wants that
- Put secondary details in backup slides rather than squeezing them into the main talk

## Figure usage

- Reuse paper figures directly when possible
- Crop or scale figures so that labels remain readable
- If a figure is too dense, isolate a subfigure or add a short callout instead of shrinking it excessively
- Use placeholders only when the user explicitly allows it or when the figure asset is unavailable

## What to avoid

- white background if terminal style was requested
- inconsistent fonts across title, body, and math blocks
- tiny equations just to keep content on one slide
- full paragraphs copied from the paper
- frames that look acceptable in source but produce overflow in compiled PDF
