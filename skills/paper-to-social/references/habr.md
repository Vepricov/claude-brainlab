# Habr article playbook

Language: **Russian**. Unlike Telegram (emoji blocks) and Twitter (atomic tweets), Habr wants a **real connected-prose article**: paragraphs that flow, with section headers, intuition, one or two formulas or figures, and a practical framing. The user said: "тут надо связный текст" and "я вообще не знаю как туда что-то писать" — so this reference carries the load.

How Habr ML paper-writeups actually read (from Yandex/Sber/AIRI posts, e.g. the TabM writeup): accessible but technical, opens with the practical stakes, explains the method with intuition rather than proofs, backs claims with concrete numbers and a comparison, and closes with credibility (acceptances, citations, links). Reads in 3–10 minutes.

## Structure

1. **Title** — clear and a little catchy. Can be the method name plus what it does ("TabM — новая архитектура для табличных данных"). Not the raw paper title.
2. **Lead paragraph (the hook).** Either the practical stakes ("обучение больших моделей упирается в …") or a short institutional intro ("В нашей лаборатории мы …"). State what the paper is and why a practitioner should care, in 2–3 sentences.
3. **## Постановка задачи / В чём проблема.** Connected prose: what people do now, why it breaks or is suboptimal. Build the tension. This is where you earn the reader.
4. **## Идея / Что мы предложили.** The method, explained with intuition first. You may include the key equation (LaTeX renders on Habr) and one concept figure, but lead with words. Walk through *why* it works, not just *what* it is.
5. **## Теория** (if the paper has it). One readable section: the setting, the main guarantee in plain terms, what is new. Do not paste the proof. A single theorem image or the main bound is enough.
6. **## Эксперименты / Результаты.** Concrete numbers in prose plus a table or a plot. Name datasets and baselines. State exact figures and where the gain comes from.
7. **## Почему это важно / Выводы.** The takeaway and the honest scope. End on the sharp closing insight (same one as the other platforms), expanded to a sentence or two.
8. **Links and credits.** arXiv, GitHub, conference acceptance, coauthors. A line on the lab if relevant.

## Style notes

- **Connected paragraphs**, not bullet dumps. Bullets only for a genuine list (results, settings covered).
- Accessible: define jargon the first time. A practitioner outside your exact subfield should follow it.
- Formulas: **write them in LaTeX** — Habr renders math (inline `$...$`, display `$$...$$`). Use real LaTeX, not unicode, for anything beyond a single symbol. Still surround each formula with a sentence of intuition. More math is fine here than on other platforms, but never a wall of it.
- **Theory can go deep.** Habr is the place to actually expand the theory: state the framework, the assumptions in words, the main theorem, the conjugate interpretation, the spectral derivation. This is the long-form channel, so give the interesting theory real room (the user explicitly wants more theory here than in the TG/LinkedIn versions).
- Figures: 2–5 is normal. Concept figure, the framework/definition, the theorem, results plot, a regime plot. Caption each.
- Length: ~1200–3000 words. The longest, most narrative version. Longer is fine if the theory earns it.
- Tone: confident, curious, practical. Russian technical-blog register, not academic stiffness, not marketing.
- Same anti-AI rules. Run `writing-anti-ai`. The connected-prose format makes AI tells (uniform paragraph shapes, "Таким образом, …", windups) more visible, so watch for them.

## Process

- Reuse the Telegram draft as the skeleton of content, then *expand each block into real paragraphs* with intuition and transitions. Telegram is the compressed version; Habr is the full narrative.
- Put the article in `Papers/<slug>/habr-<slug>.md`, images in the shared assets folder.

See `examples/habr-template.md` for a worked example (softsign).
