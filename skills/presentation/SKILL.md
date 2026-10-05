---
name: presentation
description: This skill should be used when the user asks to create presentation slides, rewrite or polish a Beamer deck, prepare a lecture or conference talk, fix slide layout, improve mathematical slides, use the lab style or terminal style, make slides clearer, combine or split slides, or otherwise work on a presentation in LaTeX Beamer.
version: 0.1.0
---

# Presentation Slides

Use this skill for slide decks, especially LaTeX Beamer presentations with mathematical or research content.

## Goal

Produce slides that are:
- mathematically connected,
- visually clean,
- readable without overflow,
- consistent in notation and language,
- shaped to this user's presentation preferences by default.

## What This Skill Does

- creates new Beamer talks,
- rewrites existing decks,
- improves mathematical exposition,
- repairs layout and overflow,
- merges or splits frames when needed,
- turns paper material into presentation form.

## What This Skill Does Not Do

- it does not leave mathematical gaps unexplained,
- it does not keep ugly overflow just because the PDF compiles,
- it does not answer user confusion with meta-commentary boxes when the slide itself should be rewritten,
- it does not casually rename notation across slides.

## Default Workflow

1. Read the source first.
2. Identify the deck's mathematical story.
3. Check whether current slides are too dense, disconnected, or notation-inconsistent.
4. Rewrite slide content before polishing layout.
5. Compile after substantial edits.
6. Treat overflow and heavy shrink as errors to fix.

## Core Rules

### 1. Read Before Editing

- Prefer local paper `.tex` sources if they exist.
- Otherwise use local notes/library entries.
- Read the paper PDF if the notes are not enough for strict slides.

### 2. Mathematical Chain

- New formulas must be motivated by previous slides.
- The deck should read as a chain, not as a bag of facts.
- Theorem conditions should appear in formulas when possible, not only in prose.
- If the user asks for stronger theory, rebuild the slide from the source paper rather than paraphrasing loosely.

### 3. Language

- Default slide prose is Russian.
- Keep method names, code, commands, file names, and only standard technical terms in English.
- Remove decorative or unnecessary English phrases from slide bodies.

### 4. Notation

- Keep notation stable across the whole deck.
- Reuse notation already accepted by the user.
- Do not rename core objects casually.
- If the user rejects a notation choice once, preserve the preferred one later.

### 5. Reacting To User Feedback

- If the user says something is unclear, rewrite the slide itself.
- Do not solve that by adding a side box that says, in effect, “here is why this is here”, unless that mathematical object genuinely belongs as part of the slide's logic.
- The answer should become obvious from the revised slide content itself.
- If the user asks to combine slides, combine them.
- If the user asks to remove a slide, remove it unless there is a clear dependency that must first be rebuilt elsewhere.

### 6. Layout Policy

- Prefer framed blocks, balanced columns, and visual hierarchy over plain fact lists.
- Keep one main idea per frame.
- If content does not fit, split the frame before shrinking aggressively.
- Use proof frames or backup frames for dense derivations.

### 7. Overflow Policy

- `Overfull \hbox` is an error.
- `Overfull \vbox` is an error.
- `Frame text is shrunk` is usually an error.
- **A clean log does not mean the deck is clean.** A `tcolorbox` inside `columns` that runs past the
  bottom of a frame is silently cut by the page edge: no warning, `latexmk` exits 0. Never report a
  deck as done without running `scripts/check_overflow.py` on the built PDF and getting
  `all pages fit`. It also catches tables running off the right edge.
- Fix in this order:
  1. cut redundant text
  2. drop the least load-bearing box
  3. shrink the figure
  4. rebalance columns
  5. split the frame
- Do not rely on heavy shrink as the default solution.
- Capacity on 16:9 at 10pt (frame body ~205 pt): a column holds a figure **or** three short boxes,
  not both; a full-width figure leaves room for at most two boxes under it; six boxes on one frame
  is a guaranteed cut.

### 8. Lab Style — The Default

Every deck for this lab uses the BRAIn Lab house style unless the user explicitly asks for
something else. Authoritative compact reference: `examples/lab-style-mini.tex`, with
`examples/lab-style-notes.md` for the mandatory traits.

- Palette comes from two sources: the poster template
  `~/Papers/finished papers/kawasaki/poster/brainposter.sty` and, decisive for slides, the lab deck
  `~/Projects/huawei_optimizers/Talk3_Efficient_Pretraining_30min.pptx`:
  `plum` `#854C65` (full-bleed background of title / section / closing frames, and heading colour on
  content frames), `cream` `#FAF8F1` (content background, and text on plum), `amber` `#FFD183`
  (headings on plum), `amberink` `#A9741A` (amber readable on cream), `ink` `#1F1B18`,
  `red` `#B0453F` (problems), `muted` `#8C8078`.
- **Never a white background** — cream `#FAF8F1`. Plain white looks flat and does not sit with the
  rest of the palette. Figures go in white cards on the cream ground, which then read as cards.
- The deck's rhythm is the alternation of full-bleed plum frames and cream content frames. That
  alternation is what makes it look designed. Use the `plumframe` environment for the plum ones.
- `\usetheme{metropolis}`, `aspectratio=169`, serif `lmodern` — **not** monospace.
- Frame title: plum text on cream plus a thin plum rule at **text** width. Turn the theme progress
  bar off (`progressbar=none`): it spans the whole page, looks coarser and breaks overflow checking.
- Title slide: **typography only** — no logo, no author line, no `$ run --...` lines. Large amber
  title, thin amber rule, cream subtitle, date bottom-left and `BRAIn Lab` bottom-right.
- Box convention: `mathbox` white card (equations, tables), `ideabox` faint plum (ideas, results),
  `thmbox` amber (theorems, stable facts, surprising findings), `probbox` faint red (problems).
  All four carry `fontupper=\small`; without it three boxes never fit a column.
- `\fcap{...}` for figure captions must contain `\par` inside the group, otherwise `\scriptsize`
  does not control the leading and the caption renders oversized.

### 9. Figures — Find Before You Draw

- **A figure from the paper always beats a hand-rolled schematic.** Before generating anything in
  matplotlib, pull the original: check `Literature/**/_attachments/<arxiv-id>/` first (the
  `paper-ingest` skill already extracted figures for some papers), then
  `curl -sL https://arxiv.org/e-print/<id>` and untar. `grep -rhoE 'includegraphics\[[^]]*\]\{[^}]*\}' *.tex`
  shows which figures the paper itself actually uses.
- Crop only with `pdfcrop --margins 3`. Do not set a CropBox by hand (pymupdf and pdfTeX disagree
  about CropBox vs MediaBox and the figure lands offset). To take one panel of a multi-panel figure,
  narrow the MediaBox first, then `pdfcrop`.
- Do not squeeze a portrait figure into a 16:9 frame whole: cut out the wide fragment that carries
  the idea.
- Own figures, when no source figure exists: matplotlib, white background, serif fonts,
  `mathtext.fontset=cm`, palette colours above — use `#5E8797` for lines, because `#9DE1FC` itself
  is unreadable on white.

### 10. Terminal Style — Only On Request

- Use it only when the user asks for `terminal style` or `терминальный стиль`. It is a slide theme,
  not the lab's identity: anything representing the lab uses the palette above.
- Authoritative reference: `examples/terminal-style-mini.tex`, traits in `examples/terminal-style-notes.md`.
- Interpret it as: `\usetheme{metropolis}`, `aspectratio=169`, dark background (`#0D1117`), dark
  card/title background (`#161B22`), green accent (`#00FF88`), blue secondary (`#58A6FF`), orange
  theorem accent (`#FF7B54`), red problem accent (`#FF6B6B`), monospace bold titles, section
  dividers in the same visual language, compact `tcolorbox` blocks, clean plain final slide.
- Title slide there is rich: top `// tag` line, thin rules, title, blue subtitle, coloured author and
  affiliation lines, one or two `$ run --...` / `$ git clone ...` lines, optional QR row.
- Figures on the dark canvas must sit in a **white** `figcard` panel, otherwise they look broken.

## Preferred Output Shape For Theory Decks

1. motivation
2. precise setup
3. derivation or approximation step
4. theorem or guarantee
5. algorithmic consequence
6. empirical or practical note

## Reference Files

Load only what is needed:
- `references/beamer-workflow.md` - compile-and-fix workflow for Beamer
- `references/user-presentation-preferences.md` - detailed user-specific rules for mathematical slides, feedback handling, notation, and layout
- `examples/lab-style-mini.tex` - **default** style anchor: BRAIn Lab house style
- `examples/lab-style-notes.md` - mandatory visual traits of the lab style, figure sourcing, frame capacity
- `scripts/check_overflow.py` - detects frames whose content is silently cut by the page edge; run it before calling a deck done
- `examples/terminal-style-mini.tex` - style anchor for the dark terminal theme, only when asked
- `examples/terminal-style-notes.md` - mandatory visual traits of terminal style in short form
