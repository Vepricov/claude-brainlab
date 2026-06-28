# LinkedIn post playbook

Language: **English** (unless the user says otherwise). Think of it as the Telegram post's content, rewritten as professional prose: connected sentences instead of emoji-header blocks, calmer, aimed at a mixed audience of researchers, engineers, and recruiters scrolling a feed.

Andrey's steer (refined 2026-06-24): make it **roughly Telegram length, not a thin summary** (LinkedIn allows ~3000 chars, a meaty ~250–400 words reads well). And **always include visuals** — a LinkedIn post with no image underperforms. Best options: one strong figure, or a **carousel/document (PDF) post** built from the same "Карточки" as Telegram (carousels get strong reach on LinkedIn). So it is the same substance as Telegram, fuller than a tweet, with images.

## Structure

1. **Hook line (1–2 sentences).** The problem or the result, stated so a non-specialist gets it. The first ~2 lines are all that show before "see more", so they must earn the click. Acceptance news is a strong opener ("Our paper on X was accepted at ICML 2026.").
2. **4–6 short paragraphs** (this is the "make it TG-length" part). Problem, the fix (the one mechanism in plain words), the matrix/second contribution, a sentence on the theory, and the numbers. One or two concrete results with exact figures. Connected prose, with one short bullet list of results allowed.
3. **Why it matters / who should care** — a line on the practical implication and the closing insight.
4. **Credit + links.** Thank coauthors (tag them with @ if you have confirmed accounts), link the paper and code.
5. **3–5 hashtags** at the very end (e.g. #MachineLearning #LLM #Optimization #ICML2026). Not more.

## Visuals (do not skip)

Every LinkedIn post gets at least one image. Pick one:
- a single strong figure (results plot or concept figure) with a one-line caption, or
- a **carousel/document post**: export the Telegram "Карточки" as a PDF and attach it. Carousels get the best reach on LinkedIn. In the deliverable, point to the card set and the figure files in the assets folder.

## Style notes

- Professional but human. First person. No corporate-influencer voice ("thrilled to share", "humbled", "🚀"). One emoji at most, and only if it genuinely helps.
- Short paragraphs (1–3 sentences). Whitespace between them. LinkedIn punishes walls of text.
- One figure attached (the results plot or the concept figure), with a one-line caption.
- Length: ~120–250 words.
- Same anti-AI rules as everywhere (no em dashes, no hype). Run `writing-anti-ai`.

## Personal angle (LinkedIn specifically)

LinkedIn is the right place to get personal, more than the other platforms. The user wants this here:
- **Tag coauthors** inline (verify handles first), and thank them.
- **Write professional feelings about the work**: what went well, what was hard, what surprised you, the frustration-then-breakthrough moment. This is what makes a LinkedIn post feel human instead of an abstract.
- A documented behind-the-scenes story is great material. Example: softsign has `Papers/softsign/llm_as_coauthor.md` — an honest account of how an LLM suggested the proximal/Fenchel-V framing that became the core theory (and confidently botched the algebra, `tanh(αx)=α·tanh(x)`, while the authors did the real work). Summarize such notes faithfully, do not embellish.

**Do not invent the personal parts.** If you don't know the feelings, the story, or the handles, ASK the user before writing them. Leave clear placeholders meanwhile.

## Relationship to the other platforms

- Start from the Telegram draft's substance, then de-emoji and connect the prose.
- Keep the same closing insight as Telegram/Twitter, phrased calmly.
- Tags here can be inline (LinkedIn norms differ from the Twitter "separate shout-out" rule). Still verify every handle.

See `examples/linkedin-template.md` for a worked example (softsign).
