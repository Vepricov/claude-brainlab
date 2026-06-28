# Telegram post playbook

Language: **Russian**, conversational, like explaining your paper to a smart friend who is not in your subfield. This is the user's most-used format. Study the real examples before writing: `examples/telegram-wlora.md`, `examples/telegram-kawasaki.md`, `examples/telegram-markovian.md`.

## Structure (the shape all three examples share)

1. **Bold title** — the paper title (English is fine), sometimes with the catchy subtitle.
2. **Hook paragraph, no header.** Start from what the reader already does or assumes, in plain words, then puncture it. Patterns that work:
   - "Когда делаешь X, обычно делаешь так… Но есть нюанс." (wlora)
   - "Обучаешь модель на куче устройств и упираешься не в …, а в …" (kawasaki)
   - "Большая часть теории живёт в комфортном мире: … Но в реальных задачах всё иначе." (markovian)
3. **A second plain paragraph** that sharpens the problem and makes the reader feel the pain. Often ends on a small human aside ("Жалко.", "Зачем тогда держать их в памяти?").
4. **Emoji-header sections.** One idea each. Reuse this vocabulary of headers:
   - **💡 Идея / Что мы предлагаем?** — the method in plain words. Name it, give the one mechanism. End with "Всё. Никакой сложной архитектуры." energy when true.
   - **⚙️ Куда вставлять / Как это работает** — where it plugs in, that it needs no new architecture.
   - **📐 Теория** — one tight paragraph: what is proven, in which settings (non-convex, PL, strongly convex…), what is novel about it. Keep it readable.
   - **📊 Цифры:** — a bullet list (use `·`) of concrete results: named dataset/model then the number. Bold the single best headline number.
   - **✨ Почему это важно?** — optional, a short "why it matters" list with `·`.
5. **A closing insight line** (no header). The sharp, slightly contrarian takeaway the experiments earned. e.g. "чем невыпуклее задача, тем заметнее: мягкое накопление истории бьёт жёсткий бан." This is the signature move. Always include one.
6. **Acceptance line:** "Принято в <Venue> 2026." if accepted.
7. **Links:**
   ```
   🔗 Статья https://arxiv.org/pdf/<id>
   💻 Код: github.com/<org>/<repo>
   ```
   Verify both. If the repo is private/404, drop the code line rather than printing a dead link.

## Style notes

- Bold (`**…**`) for the title, section headers, and the occasional key phrase ("Часть из них почти ничего не делает").
- Bullets use the middle dot `·`, not `-`.
- Numbers are exact and attached to a named benchmark. Bold the headline one.
- Math: light. `$\omega_i$`, `$\ell_0$` render in Obsidian but **not in native Telegram** — keep formulas minimal and phrase them in words where possible. Note in the deliverable that LaTeX needs a plain-text fallback when pasted into Telegram.
- Length: ~300–500 words of body. Tight, no filler.
- Tone: confident, warm, a bit playful ("Жалко.", "Всё."). Never markety.

## Carousel "Карточки" — ALWAYS include them

Every Telegram post ships with a `## Карточки` carousel spec. This is not optional (the user insisted). Each card = a design spec, in BRAIn Lab style: white background, lavender/purple accent circles, brain logo top-right, Telegram-style chat bubbles, ✓ checklists, conference logo, QR codes (paper + code) on the title card. Use `telegram-wlora.md` as the canonical card set to mirror:
1. Титульная (title + QR paper/code), 2. Проблема, 3. «Раньше было так» (chat bubbles), 4. Наша идея (✓ checklist), 5. Метод, 6. Второй вклад (e.g. the matrix/spectral version), 7. Результаты (bold headline number), 8. Паттерн/инсайт, 9. TL;DR.
Adapt the count to the paper, but always produce a real card set.

## Theory screenshots go in the comments

If the paper has interesting theory, do NOT cram it into the post body. Instead:
- Put **screenshots of the actual theorems/key equations** (cropped from the arXiv PDF, see `images.md`) into the **channel comments** under the post.
- Give each screenshot a **one-line description** in the comment.
- **Reference them from the main text** ("Формулировки и доказательство — скрины в комментариях 👇", or "теорема о сходимости — в комментах").
Deliverable layout: a `## Комментарии (скрины теории)` section listing each image + its one-line caption, in the order to post them. The main `📐 Теория` block stays short and points to the comments.
