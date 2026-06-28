# Voice and anti-AI (shared across all platforms)

Read this before writing any post. It encodes what the user (Andrey, ML researcher, BRAIn Lab) has asked for repeatedly across softsign, wlora, and kawasaki. Do not make him say it again.

## The one rule above all: it must not read as AI

Always run the **`writing-anti-ai`** skill over the finished post and fix everything it flags. Hard bans:
- **No em dashes (—) in English prose.** Use a period or a colon. Standing rule for Andrey's English writing (Twitter, LinkedIn, English abstracts). NOTE: this is English-only. In **Russian** posts (Telegram, Habr) the тире (—) is correct, required punctuation and appears all over his own wlora/kawasaki posts. Do NOT strip тире from Russian text. The ban targets the English AI-style "X—Y" reveal, not Russian grammar.
- **No semicolons** in the post prose.
- **No hype vocabulary:** revolutionary, game-changing, groundbreaking, seamless, cutting-edge, unlock, unleash, harness, "delve", "leverage" as filler, "powerful", "robust" when you just mean "good".
- **No formulaic openers:** "In this work, we…", "In this paper…", "Imagine a world where…", "Ever wondered…".
- **No negative parallelism** ("not only… but also", "it's not X, it's Y" as a tic).
- **No empty windups:** "Let's dive in", "Here's the thing", "The results speak for themselves".
- **No rule-of-three padding** unless each item is literally true and load-bearing.
- **No emoji spray on Twitter/LinkedIn.** (Telegram uses emoji *section headers* deliberately — that is its style, not spray.)
- **No vague attributions:** "studies show", "experts agree", "it's well known".

Read-aloud test: if a sentence sounds like a press release or a LinkedIn-influencer post, rewrite it. If you can't picture a specific researcher saying it to a colleague over coffee, cut it.

## Voice (all platforms)

- **Plain first, name second.** Define the mechanism in everyday words, then give it its name ("swap the hard sign for a temperature-controlled tanh").
- **Conversational and confident**, a little opinionated. First person ("we found", "our fix", "best part").
- **Specific over vague.** Exact numbers (`16.216 vs 16.362`, `54.71% vs 51.25%`), named datasets, named baselines. Never "significant improvements" or "various tasks".
- **Lead with tension, not the title.** Open inside a problem or a debate the reader already cares about.
- **One idea per unit** (per tweet, per Telegram block, per paragraph).
- **A closing insight beats a summary.** The best posts end on a sharp, slightly contrarian observation the experiments earned (e.g. "the less convex the task, the more the smooth version wins").

## Accumulated preferences (cross-platform, learned the hard way)

- **Research the format first.** Before writing for a platform, look at how it is actually done (best-practice guides, examples the user points to). Do not wing it.
- **Match an example, not a template.** When the user gives an example post, mirror its rhythm and structure.
- **Never invent.** No fake numbers, no guessed arXiv ids, no invented GitHub repos, no made-up @handles, no claimed acceptances. Verify; otherwise leave an obvious placeholder and flag it in the report.
- **arXiv/GitHub links are often stale or private.** Verify the arXiv id resolves; the GitHub repo may be private (404) — say so rather than printing a dead link.
- **Acceptance line matters.** If accepted, say it ("Принято в UAI 2026", "accepted at @icmlconf 2026"). Tag the venue handle (ICML=@icmlconf, NeurIPS=@NeurIPSConf, ICLR=@iclr_conf) where the platform allows it.
- **Figures from the published/arXiv version**, not a local draft. See `images.md`.
- **Don't over-tag.** 4–6 genuinely-relevant handles max. Tag the authors of the work you build on and a few notable people who would reshare. Each external tag gets a short "(what they did)".
- **Output goes to Obsidian**, routed by project location via `~/.claude/obsidian-projects.json` (`Papers/<slug>/`), never `Research/`.
- **The user iterates.** Expect "make it denser / fix block N / add an image here". Keep the deliverable clean and easy to edit (numbered blocks, image markers, a checklist).

## Language per platform

- **Telegram, Habr → Russian.** **Twitter/X → English.** **LinkedIn → English** (unless the user says otherwise).
- Academic/technical terms, method names, dataset names stay in English everywhere.
- Math: LaTeX `$...$` is fine in Obsidian notes and renders on Habr; on Telegram keep math light and have a plain-text fallback (Telegram does not render LaTeX natively).
