# Terminal Style Notes

Use `terminal-style-mini.tex` as the compact visual anchor.

## Mandatory Visual Traits

- Dark background: near-black main canvas.
- Slightly lighter dark cards/title areas.
- Bright green primary accent.
- Blue secondary accent for subtitles or secondary emphasis.
- Orange accent for theorem/proof-style emphasis.
- Main text in light gray or off-white, not pure white.
- Monospace bold titles and frame titles.
- Compact, code-like aesthetic without looking like an IDE screenshot.

## Title Slide

- Plain frame.
- Small monospace line at the top starting with `//`.
- Thin horizontal rules above and below the main title area.
- Large central title (monospace bold).
- Short subtitle in secondary accent (blue).
- Author line: presenting/first author in `accentorange` bold, co-authors in muted `textsub`, all `\texttt`.
- Affiliation line: home lab(s) in `accentorange`, the rest in muted `textsub`, all `\texttt`, separated by `$\cdot$`.
- One or two terminal command lines at the bottom: a green `$ run --...` line and optionally a blue `$ git clone github.com/...` line. Keep them short — no long command dumps.
- Optional: a row of QR codes (GitHub / Telegram / X) under the commands when links exist.

## Figures

- NEVER drop a raw figure straight onto the dark canvas — it looks broken.
- Wrap every figure in a white `figcard` panel (white background, thin `border` frame). Define a `\figcard{path}` helper and use it everywhere.
- A text-only deck reads as a wall of boxes. Break it up: use the paper's figures (pull/copy them into the deck's `figures/`), and if a needed figure does not exist, generate a clean one (matplotlib, white background, serif/cm fonts, line colors matching the deck accents — green/blue/orange).
- Typical figure slide: two columns, `\figcard` on one side, a short `ideabox` takeaway on the other. Add a one-line muted `textsub` caption under the figure.

## Section Divider Slides

- Plain frame.
- Same visual language as the title slide.
- Small `// <section id>` line.
- One large section title centered.
- Minimal content: just the section marker and title.

## Regular Content Slides

- Dark theme continues unchanged.
- Prefer balanced two-column layouts for comparisons.
- Use compact `tcolorbox` blocks for theorem, idea, or definition content.
- Keep one main idea per frame.
- Avoid long bullet walls.
- Equations should be readable and visually centered.

## Final Slide

- Plain frame.
- Same title-slide visual language.
- Large `Спасибо!` or equivalent closing line.
- Optional short `Вопросы?` subtitle.
- No clutter.

## Box Color Convention

- `mathbox` (gray border) — neutral equations and tables.
- `ideabox` (green) — key ideas, definitions, main results, takeaways.
- `thmbox` (orange) — theorems, lemmas, assumptions.
- `bluebox` (blue) — secondary notes, comparisons, side facts.
- `probbox` (red) — problems, pitfalls, failure modes.
- Use a small green `// proof` monospace lead-in for proofs; keep long proofs as plain text across dedicated slides rather than cramming one box.

## Things To Avoid

- Generic white academic slides.
- Heavy gradients, glossy effects, or decorative shapes.
- Dense paragraphs.
- Tiny equations.
- Layouts that require aggressive shrink.
- Raw figures on the dark canvas (always use a white `figcard`).
- A deck that is 100% text boxes with no figures.
- Explanatory meta-boxes that answer user complaints instead of rewriting the slide itself.
