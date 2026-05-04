---
name: presentation
description: This skill should be used when the user asks to create presentation slides, rewrite or polish a Beamer deck, prepare a lecture or conference talk, fix slide layout, improve mathematical slides, use terminal style, make slides clearer, combine or split slides, or otherwise work on a presentation in LaTeX Beamer.
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
- Fix in this order:
  1. cut redundant text
  2. split the frame
  3. rebalance columns
  4. shorten captions or side notes
  5. move technical detail to a proof or backup frame
- Do not rely on heavy shrink as the default solution.

### 8. Terminal Style

- If the user asks for `terminal style` or `терминальный стиль`, use the local example deck `examples/terminal-style-mini.tex` as the authoritative compact reference.
- Interpret it as: `\usetheme{metropolis}`, `aspectratio=169`, dark background (`#0D1117`), dark card/title background (`#161B22`), green accent (`#00FF88`), blue secondary accent (`#58A6FF`), orange theorem/proof accent (`#FF7B54`), monospace bold title and frame title, section-divider slides in the same visual language, compact `tcolorbox` blocks, and a clean plain-style final slide.
- Follow the tone of that mini deck rather than copying exact slide text.

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
- `examples/terminal-style-mini.tex` - compact style anchor for terminal-style Beamer decks
- `examples/terminal-style-notes.md` - mandatory visual traits of terminal style in short form
