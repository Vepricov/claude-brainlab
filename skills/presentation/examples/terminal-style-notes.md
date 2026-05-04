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
- Large central title.
- Short subtitle in secondary accent color.
- Author and affiliation in muted text.
- One short terminal-like line at the bottom, but not a long command dump.

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

## Things To Avoid

- Generic white academic slides.
- Heavy gradients, glossy effects, or decorative shapes.
- Dense paragraphs.
- Tiny equations.
- Layouts that require aggressive shrink.
- Explanatory meta-boxes that answer user complaints instead of rewriting the slide itself.
