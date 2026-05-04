# User Presentation Preferences

Use these as hard defaults for this user unless they explicitly ask otherwise.

## 1. Language

- Write human-facing slide text in Russian.
- Keep method names, code, commands, file names, and only standard technical terms in English.
- Do not leave unnecessary English filler in the slide body.

## 2. Mathematical Style

- Theory slides must form a connected chain.
- Every new object should be motivated by the previous slide.
- Do not introduce formulas "from nowhere".
- If a theorem uses a condition, make that condition visible in the theorem statement or derivation, not only in a side remark.
- Prefer equations over long prose on theory slides, but only if they remain readable.
- If a proof is needed, give a short proof idea on the main path and move detail to a separate frame when needed.

## 3. Notation

- Keep notation consistent across the whole deck.
- Do not rename core matrices, vectors, or factors casually.
- If the user rejects a notation choice once, preserve the preferred notation in later edits.
- Reuse notation from the paper or from earlier accepted slides whenever possible.

## 4. How To React To User Feedback

- If the user says a slide is unclear, rewrite the slide itself.
- Do not add meta-answer boxes like "why this is here" unless the mathematical role of the object truly belongs on the slide.
- If the user says slides should be merged, merge them.
- If the user asks for stronger theory, read the source paper and rebuild the slide from the source rather than paraphrasing notes.

## 5. Layout And Visual Structure

- Avoid raw fact lists when a framed summary, equation block, or two-column comparison communicates better.
- Use boxes to separate theorem, intuition, assumptions, comparison, or takeaway.
- Keep one visual center per slide.
- Prefer balanced columns over cramped dense text.
- If a slide becomes too dense, split it.

## 6. Overflow Policy

- `Overfull \hbox` and `Overfull \vbox` are errors to fix.
- `Frame text is shrunk` is usually also an error.
- Fix in this order:
  1. remove redundant text
  2. split the frame
  3. rebalance columns
  4. shorten captions or side notes
  5. move technical detail to a dedicated proof or backup slide
- Do not rely on heavy shrink as the default solution.

## 7. Typical Desired Output Shape

For mathematical presentations, the preferred shape is:

1. motivation
2. precise setup
3. derivation or approximation step
4. theorem / guarantee
5. algorithmic consequence
6. empirical or practical note

This user prefers slides that look compact, mathematically intentional, and visually clean rather than generic lecture bullets.
