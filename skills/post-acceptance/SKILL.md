---
name: post-acceptance
description: This skill should be used when the user asks to "prepare conference presentation", "create presentation slides", "make a Beamer talk", "use terminal style", "терминальный стиль", "design poster", "make academic poster", "write promotion content", or mentions post-acceptance conference preparation. Provides workflows for Beamer presentations, posters, and promotion content.
version: 0.2.0
---

# Post-Acceptance Conference Preparation

A post-acceptance conference preparation workflow that helps researchers efficiently complete presentations, posters, and promotional content.

## Core Features

### 1. Presentation Slide Creation

Guidance for creating conference presentation slides:

**Default format for research talks**
- Prefer LaTeX Beamer unless the user explicitly asks for PowerPoint or another format.
- Reuse figures, tables, and notation directly from the paper source whenever possible.
- Build slides around the paper's core story: problem -> idea -> theory -> algorithm -> results -> takeaway.
- Do not overload slides with derivations. Keep proofs to the main idea and move details to backup slides if needed.

**Default presentation contract for this user**
- Treat presentation requests as theory-first unless the user clearly wants a poster, promo post, or high-level summary.
- Default language for slide prose is Russian. Keep method names, code, commands, file names, and only truly standard technical terms in English.
- Read the source material before editing slides: local paper `.tex` if available, then local notes/library entries, then the paper PDF if needed.
- For theory slides, build one connected mathematical chain. New formulas must be motivated by previous slides and must not appear from nowhere.
- Keep notation stable. Do not rename core objects casually across slides.
- If the user asks to combine slides, combine them rather than keeping the old split structure.
- If the user says something is unclear, fix the slide content itself. Do not answer with side boxes like "why this is here" unless the slide genuinely needs that mathematical object.
- Prefer fewer words and more equations on theory slides, but only when the equations remain readable and motivated.
- Use framed blocks, columns, and visual hierarchy instead of plain fact lists when summarizing approximations, assumptions, or comparisons.

**Time Control**
- 15-minute talk: 10-15 slides
- 20-minute talk: 15-20 slides
- 30-minute talk: 20-30 slides
- Average 1-1.5 minutes per slide

**Content Structure**
- Title slide (1)
- Motivation/Problem (2-3)
- Method overview (3-5)
- Key results (3-5)
- Conclusion (1-2)
- Q&A/Thank you (1)

**Visual Design Principles**
- One key message per slide
- Use figures and diagrams over text
- Consistent color scheme and fonts
- Minimum font size: 24pt for body, 32pt for titles
- High-contrast colors for readability
- If content does not fit cleanly, split the slide instead of shrinking text below readability

**Terminal style**
- If the user asks for `terminal style` or `терминальный стиль`, use the canonical compact reference at `~/.claude/skills/presentation/examples/terminal-style-mini.tex`. The `presentation` skill owns this style — both skills share one source of truth.
- Interpret `terminal style` exactly as: `\usetheme{metropolis}`, `aspectratio=169`, dark background (`#0D1117`), dark title bar (`#161B22`), main text color (`#E6EDF3`), muted secondary text (`#8B949E`), primary accent (`#00FF88`), orange alert accent (`#FF7B54`), monospace bold title and frame title, progress bar in frame title, compact `tcolorbox` blocks for idea/theorem content, and small muted monospace figure captions.
- Keep this style name stable. Future requests for `terminal style` should map to this visual language even if the user does not mention the example file again.

**Presentation Tips**
- Practice timing with a stopwatch
- Prepare backup slides for anticipated questions
- Use animations sparingly and purposefully
- Include slide numbers for Q&A reference
- After every substantial slide edit, compile the deck and check that nothing overflows or collides.
- Treat `Overfull \\hbox`, `Overfull \\vbox`, clipped equations, and cropped figures as errors to fix, not as acceptable warnings.
- Prefer reducing text, widening columns, moving material to the next frame, or replacing prose with a figure over aggressive font shrinking.
- Treat `Frame text is shrunk` warnings as layout failures unless the resulting slide is still clearly readable and visually balanced.

### 2. Academic Poster Design

Guidance for creating conference posters:

**Standard Sizes**
- Portrait: 24x36 inches or A0 (841x1189mm)
- Landscape: 36x24 inches or A0 landscape
- Check conference requirements for specific size

**Layout Structure**
- Title bar (top): Title, authors, affiliations, logos
- Introduction (left): Problem statement, motivation
- Method (center): Key approach, architecture diagram
- Results (right): Main findings, tables, figures
- Conclusion (bottom): Summary, future work, QR code

**Design Guidelines**
- Readable from 4-6 feet distance
- Title font: 72-96pt
- Section headers: 36-48pt
- Body text: 24-32pt
- Use bullet points, not paragraphs
- Include QR code linking to paper/code

### 3. Promotion Content Creation

Guidance for creating promotional content after paper acceptance:

**Twitter/X Thread**
- Thread structure: Hook -> Problem -> Method -> Key Result -> Link
- First tweet: Attention-grabbing summary with emoji
- Include 1-2 key figures
- End with paper link and relevant hashtags
- Tag co-authors and relevant accounts

**LinkedIn Post**
- Professional tone, 3-5 paragraphs
- Highlight practical implications
- Include key figure or diagram
- Add relevant hashtags

**Blog Post**
- 800-1500 words
- Non-technical summary for broader audience
- Include figures with explanations
- Link to paper, code, and demo

## When to Use

Use this skill in the following scenarios:

- **After paper acceptance** - Prepare presentation materials for the conference
- **Poster session preparation** - Design and create academic poster
- **Research promotion** - Create social media and blog content
- **Conference talk preparation** - Structure and practice presentation

## Workflow

### Presentation Workflow
```
Paper accepted -> Identify key messages -> Create slide outline -> Build Beamer slides -> Compile and fix overflow -> Practice timing -> Prepare Q&A backup slides
```

### Poster Workflow
```
Paper accepted -> Choose layout template -> Extract key content -> Design poster -> Print test at reduced size -> Final print
```

### Promotion Workflow
```
Paper accepted -> Write Twitter thread -> Create LinkedIn post -> Draft blog post -> Schedule posts around conference dates
```

## Best Practices

### Presentation
- Start with the "so what" - why should the audience care
- Tell a story: problem -> insight -> solution -> impact
- Use concrete examples and demos when possible
- Anticipate questions and prepare answers
- Arrive early to test equipment
- For theory talks, present the proof idea before technical details
- Use paper figures directly when they communicate the point faster than text
- Keep each frame visually balanced; avoid dense text walls and tiny equations
- For this user, assume a high bar for mathematical strictness: theorem statements, conditions, and approximation steps should be written in formulas when possible, not left only in prose.
- For this user, avoid decorative English filler and generic slide tropes; make slides look intentional, compact, and mathematically connected.

### Poster
- Design for scanning, not reading
- Use visual hierarchy to guide the eye
- Include a "elevator pitch" summary
- Bring business cards or QR codes
- Practice a 2-minute and 5-minute explanation

### Promotion
- Post within 1-2 weeks of acceptance notification
- Coordinate timing with co-authors
- Engage with comments and questions
- Share across multiple platforms
- Include accessible descriptions for figures

## Summary

This skill provides a comprehensive post-acceptance workflow covering three key areas: presentation slides, academic posters, and promotional content. Following these guidelines helps researchers effectively communicate their work at conferences and to the broader community.

## Reference Files

Load only what is needed:
- `references/design-guidelines.md` - visual design guidance
- `references/beamer-workflow.md` - Beamer-first workflow, compile checks, and overflow handling
- `references/user-presentation-preferences.md` - user-specific defaults for mathematical slides, notation, language, and layout
- `references/deliverable-checklists.md` - slide/poster/promo-specific checklists
- `examples/post-acceptance-plan.md` - compact delivery plan example
