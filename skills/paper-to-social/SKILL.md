---
name: paper-to-social
description: This skill should be used when the user wants to turn a research paper into social-media posts to promote it, on Telegram, Twitter/X, or Habr (LinkedIn is paused by user request). Trigger on "сделай пост по статье", "напиши пост в тг/твиттер/хабр", "post about this paper", "promote this paper", "оформи статью в пост", "тред по статье", or a request for any single one of those platforms. Produces copy-paste-ready posts in the project's Obsidian folder, with figures pulled from the arXiv version, in the user's voice (never AI-sounding).
---

# Paper → social posts (Telegram · Twitter/X · Habr)

Turn a paper into promo posts that real researchers want to read and share. One job, three active target platforms. The user may ask for one platform or all of them. Default output: one Obsidian markdown note per requested platform in the project's folder, copy-paste-ready, with figures, in the user's voice.

> **LinkedIn is paused** (user request, 2026-06-26). Do not generate LinkedIn posts unless the user explicitly asks again. The `references/linkedin.md` playbook and `examples/linkedin-template.md` are kept for when it is re-enabled.

## Hard rules (the user has said these many times — never make them repeat)

Read `references/voice-and-anti-ai.md` in full before writing anything. The non-negotiables:
- **Never look like AI.** Always run the `writing-anti-ai` skill over every post before finishing. No em dashes, no semicolons in the prose, no hype vocabulary, no "In this work we…", no negative parallelism, no empty windups.
- **Accessible but precise.** A smart reader should understand what the paper does and want to keep reading. Plain words first, then the name. Concrete exact numbers over adjectives.
- **Never invent** results, arXiv links, GitHub links, conference acceptances, or @handles. Verify each; leave a clear placeholder if you cannot.
- **Never invent personal content.** Professional feelings, what worked / what didn't, who to tag, behind-the-scenes story: if you don't know it, ASK the user, do not make it up. (This is a standing rule the user stated explicitly.) Documented process notes the user points you to (e.g. an "how we did it" note) are fair to summarize faithfully.
- **Use the BRAIn Lab brand for all visuals** — palette and logo in `references/brand.md` (berry/apricot/cream/blue + the real graph-node logo). Never the old purple/lavender scheme, never a placeholder logo.
- **Figures come from the arXiv/published version**, extracted cleanly. See `references/images.md`.
- **Route output** to the project's Obsidian folder via `~/.claude/obsidian-projects.json` (`Papers/<slug>/...`), never `Research/`.

## Workflow

1. **Get the paper.** `git pull` the Overleaf/local source if present and read `main.tex` (abstract, intro/contributions, method, experiments/tables, conclusion). Prefer `.tex` over PDF. Also note the arXiv id, code URL, and conference acceptance if any.
2. **Extract the core once** (reused across platforms): the one-sentence idea, the problem it fixes, the mechanism, the headline numbers (exact), the theory in one breath, the "free to adopt" angle, and the live debate it plugs into.
3. **Pull figures from the arXiv version** into `Papers/<slug>/<platform>-assets/` (or a shared `social-assets/`). See `references/images.md`. View every render before describing it.
4. **Write each requested platform** using its reference file. Match the user's voice from the examples, not a generic template.
   - Telegram → `references/telegram.md` (examples: `telegram-wlora.md`, `telegram-kawasaki.md`, `telegram-markovian.md`)
   - Twitter/X → `references/twitter.md` (example: `twitter-softsign-thread.md`)
   - Habr → `references/habr.md` (example: `habr-template.md`)
   - LinkedIn → **paused**. Skip unless explicitly asked. (`references/linkedin.md`, `examples/linkedin-template.md`)
5. **Run `writing-anti-ai`** over the result and fix every flagged pattern.
6. **Verify mechanics**: tweet char counts ≤280, every handle resolves, every image marker maps to a real file, links present (or placeholdered).
7. **Report** the file path(s) and flag every placeholder the user must fill (arXiv link, coauthor handles, unconfirmed handles).

## What changes per platform (one-line map)

- **Telegram** — conversational Russian, emoji section headers, concrete numbers, a closing insight, "Принято в <venue>", 🔗 Статья / 💻 Код. **Always ship a "Карточки" carousel.** Theory-heavy paper: theorem screenshots go in the **comments** (one-line caption each), referenced from the body.
- **Twitter/X** — English thread, dense tweets near 280, theory gets 2–3 tweets, marquee method in tweet 1, tags only in a separate shout-out post, an image on most tweets.
- **LinkedIn** — *paused (user request)*. When re-enabled: the Telegram post's substance as professional English prose, **roughly TG length** (4–6 short paragraphs), light on emoji, 3–5 hashtags, **always with a visual** (one figure or a carousel/document built from the TG cards).
- **Habr** — a real connected-prose article in Russian (not bullets), sections, **formulas in LaTeX** (Habr renders them), the place to **expand the theory** in depth, several figures, practical framing, the longest version.

## Boundaries

- This skill drafts. The user posts. Do not post anything.
- Do not overclaim beyond the paper. Keep numbers exact (no rounding away, no "≈").
- One post per platform per request unless asked for variants.

## Resources

- `references/voice-and-anti-ai.md` — shared voice + the full anti-AI checklist + accumulated user preferences. **Read first.**
- `references/telegram.md`, `references/twitter.md`, `references/linkedin.md`, `references/habr.md` — per-platform playbooks.
- `references/images.md` — pulling clean figures/cover/theorem images from the arXiv PDF and the arXiv abstract page, plus the carousel/document build recipe.
- `references/brand.md` — BRAIn Lab palette + logo (`assets/`), for all carousels and visuals.
- `examples/` — real posts (gold standard): three Telegram, one Twitter thread, plus LinkedIn and Habr templates.
