---
name: want-2-read
description: Use when the user wants to process want_2_read.md. Parse raw paper entries, fully ingest them through Zotero and Obsidian, classify them into the current Literature folders, and update want_2_read.md with final wiki-links, Zotero links, and detailed descriptions.
version: 1.3.0
---

# Skill: want-2-read

## Trigger

Use when the user writes `/want-2-read` or asks to "обработай мой список статей", "process my reading list", "разбери want_2_read".

## Input File

`${OBSIDIAN_VAULT}/Literature/want_2_read.md`

Если файла еще нет, его нужно создать.

Файл содержит единый reading queue. Основной поддерживаемый формат это unchecked чекбоксы внутри тематических daily blocks. Простой bullet-список без checkbox не является canonical format и должен постепенно нормализоваться.

Canonical format:
- заголовок дня: `## Daily_papers_DD-MM-YYYY`
- тематическая секция внутри дня: `### <human-readable topic>`
- resolved article block:
  ```markdown
  - [ ] [[Literature/.../Paper Title]]
    **Тема**: Zero-order optimization
    **Предлагаемая папка**: `Literature/Applied/FL` и zero-order
    **arXiv**: https://arxiv.org/abs/XXXX.XXXXX
    **Zotero**: zotero://select/library/items/XXXXXXXX
    **Дата**: YYYY-MM-DD
    **Краткая идея**: Подробное описание статьи на русском, достаточное чтобы понять постановку, метод и результаты без открытия PDF.
  ```
- raw article block:
  ```markdown
  - [ ] Raw Paper Title
    **Тема**: Zero-order optimization
    **Предлагаемая папка**: `Literature/Applied/FL` и zero-order
    **arXiv**: https://arxiv.org/abs/XXXX.XXXXX
    **Zotero**:
    **Дата**: YYYY-MM-DD
    **Краткая идея**: raw paper
  ```
- completed article block:
  ```markdown
  - [x] [[Literature/.../Paper Title]]
    **Тема**: Zero-order optimization
    **Предлагаемая папка**: `Literature/Applied/FL` и zero-order
    **arXiv**: https://arxiv.org/abs/XXXX.XXXXX
    **Zotero**: zotero://select/library/items/XXXXXXXX
    **Дата**: YYYY-MM-DD
    **Краткая идея**: Подробное описание статьи на русском, достаточное чтобы понять постановку, метод и результаты без открытия PDF.
  ```
- если поле неизвестно, строку оставить, но без значения

Example:
```
## Daily_papers_27-04-2026
### PEFT / LoRA base
- [ ] Where Should LoRA Go? Component-Type Placement in Hybrid Language Models
  **Тема**: LoRA base
  **Предлагаемая папка**: `Literature/PEFT/LoRA base`
  **arXiv**: https://arxiv.org/abs/2604.22127
  **Zotero**:
  **Дата**: 2026-04-24
  **Краткая идея**: raw paper
- [ ] [[Literature/PEFT/LoRA base/Some Paper]]
  **Тема**: LoRA base
  **Предлагаемая папка**: `Literature/PEFT/LoRA base`
  **arXiv**: https://arxiv.org/abs/2604.19321
  **Zotero**: zotero://select/library/items/XXXXXXXX
  **Дата**: 2026-04-21
  **Краткая идея**: Подробное описание статьи на русском, достаточное чтобы понять постановку, метод и результаты без открытия PDF.
- [x] [[Literature/Optimization/muon/Already Read Paper]]
  **Тема**: Muon
  **Предлагаемая папка**: `Literature/Optimization/Muon`
  **arXiv**: https://arxiv.org/abs/2604.04891
  **Zotero**: zotero://select/library/items/XXXXXXXX
  **Дата**: 2026-04-06
  **Краткая идея**: Уже прочитано.
```

## Step 1: Parse the File

Read `want_2_read.md`. Preserve all headings such as `## Daily_papers_DD-MM-YYYY` and any thematic subheadings under them.

Primary processing target:
- only unchecked checkbox entries, i.e. lines starting with `- [ ]`

Interpretation rules:
- `- [ ] Raw Paper Title` block → unresolved raw entry, process it
- `- [ ] [[Literature/...]]` block → already resolved note, keep it as-is unless user explicitly asks to reprocess
- `- [x] ...` block → already read/completed, never process and never rewrite except when user explicitly asks
- plain headings `#`, `##`, `###` must be preserved
- plain non-checkbox text should be left untouched unless the user explicitly asks to normalize legacy content

For each unresolved unchecked checkbox entry:
- Parse the whole article block first
- Extract the first line after `- [ ]` as the article header
- If the header is a wiki-link `[[...]]`, treat it as resolved note
- Otherwise treat the header as a raw title
- Extract values from `**Тема**:`, `**Предлагаемая папка**:`, `**arXiv**:`, `**Zotero**:`, `**Дата**:`, `**Краткая идея**:`
- `**Тема**:` must be a human-readable topic label, not a slug and not a raw folder tail like `lora_base`
- Never invent underscore-based topic labels. Use normal names like `LoRA base`, `Zero-order optimization`, `Muon`, `Continual learning`
- Parse the folder field as one or more destinations. Separator can be `,` or textual `и`
- If `arXiv:` contains arxiv.org or alphaxiv.org, extract arXiv ID from it
- If only title is useful, search arXiv by title → find arXiv ID
- Skip completed checkboxes and already-resolved WikiLinks

Hard interpretation rule:
- a raw URL or raw paper title in `want_2_read.md` is **not** a finished entry
- adding only a description under a raw URL/title is **not** sufficient
- the entry is only considered processed after full `paper-ingest`, with a real Zotero parent paper item, a PDF attachment, and a final Obsidian note

## Step 2: Infer Current Library Structure

Do not use a hardcoded ontology.

Before suggesting any permanent destination, inspect the current library:
```bash
VAULT="${OBSIDIAN_VAULT}/Literature"
find "$VAULT" -mindepth 2 -maxdepth 2 -type d | sort
find "$VAULT" -name "*.md" | xargs grep -h "^tags:" -A 20 | grep "  - " | sed 's/^  - //' | sort | uniq -c | sort -rn
```

Also collect all seen arXiv IDs so you do not re-suggest already ingested or already rejected papers:
```bash
find "$VAULT" -name "*.md" | xargs grep -h "arxiv.org/abs/" | grep -oE "[0-9]{4}\.[0-9]{4,5}" | sort -u > /tmp/existing_arxiv_ids.txt
find "$VAULT" -path "*/_trash/*" -o -path "*/_inbox/*" | xargs grep -h "arxiv.org/abs/" 2>/dev/null | grep -oE "[0-9]{4}\.[0-9]{4,5}" | sort -u > /tmp/previously_seen_arxiv_ids.txt
cat /tmp/existing_arxiv_ids.txt /tmp/previously_seen_arxiv_ids.txt | sort -u > /tmp/all_seen_arxiv_ids.txt
```

Infer relevance from:
- existing Literature folder names
- note titles
- note tags
- project cards under `Papers/`, `Projects/`, `Staff/`

## Step 3: Resolve And Ingest Each Paper

Agent orchestration rule:
- first collect the full set of unresolved raw entries from `want_2_read.md`
- then launch **one separate agent per paper**
- each per-paper agent must resolve exactly one paper and then explicitly invoke the `paper-ingest` skill for that paper
- do not process the whole batch inside a single agent
- do not mix several papers into one ingest agent

Recommended execution order:
1. parse all raw entries
2. build the list of papers to process
3. launch one agent per paper
4. wait for all paper-level agents to finish
5. merge their results back into `want_2_read.md`
6. launch one final review agent over the updated `want_2_read.md` and all newly created/updated cards

Final review agent rule:
- after all paper-level agents finish, `want-2-read` must launch one additional agent whose only job is quality control
- this review agent must read the updated `want_2_read.md`
- it must then open every newly created or updated Obsidian paper note from this batch
- it must check that each card is complete, readable, properly linked, and detailed enough
- if any card is weak, shallow, inconsistent, or partially written, the review agent must strengthen it immediately instead of merely reporting the issue
- the batch is not complete until this review agent finishes

For each new entry, first resolve the paper, then **explicitly invoke the `paper-ingest` skill** and run the full `paper-ingest` pipeline immediately:
1. Duplicate check (3-check: Zotero API + SQLite + Obsidian grep)
2. Fetch BibTeX (DOI → DBLP → arXiv priority chain)
3. Download PDF → extract text
4. Import to Zotero under staging collection `w2r_DD-MM-YYYY`
5. Write the full Obsidian card through `paper-ingest` to `Literature/_inbox/w2r_DD-MM-YYYY/`
6. Read the resulting Obsidian note and reuse its final `zotero_link` and detailed explanation when updating `want_2_read.md`

This is a hard workflow boundary:
- `want-2-read` must call the `paper-ingest` skill for every resolvable new paper
- `want-2-read` must do this through one dedicated agent per paper
- it is not acceptable to imitate `paper-ingest` loosely or to stop after metadata lookup
- if `paper-ingest` was not invoked, the `want-2-read` workflow is incomplete
- if the final review agent was not run, the `want-2-read` workflow is incomplete

If paper is already in library: link to existing card instead of re-ingesting.

If the paper came from a `paper-search` shortlist and the user said it should be added to the library or to `want_2_read.md`, that is already an ingest decision. Do not just copy the shortlist text into `want_2_read.md`. Invoke `paper-ingest` first, then write the resolved entry from the final note.

The same rule applies to raw links or titles that the user manually appends to `want_2_read.md`.
If the user adds a paper there, the default behavior is:
1. resolve the paper
2. invoke the `paper-ingest` skill and run full `paper-ingest`
3. create or link the final Obsidian note
4. replace the raw line with the canonical resolved block

Do not stop at "found the paper" or "added a description".

Unlike `paper-search`, this workflow is not shortlist-first. The purpose of `want_2_read` is to process the user's explicit reading queue end-to-end, so all valid unresolved unchecked checkbox entries should be resolved, ingested, and placed into their permanent library folders right away.

## Step 4: Classify Into Permanent Folders

For each paper, choose a permanent collection based on its tags and content:
- Infer the current top-level and sub-collection structure from the live library tree
- Match paper title/abstract/tags against the current folder names and note tags
- Choose the most relevant current folder, or create a new folder if nothing fits

Default behavior for this skill:
- If a strong existing destination exists, move the paper there automatically after ingest
- If no existing folder fits well enough, create the best new permanent folder under the current Literature hierarchy and place the paper there immediately
- Do not leave successfully processed papers in `_inbox` just because classification was not perfect
- If `folders:` lists multiple destinations, treat the first as canonical and place the same paper into the remaining destinations too
- For multiple Obsidian destinations, use **hard links**, not symlinks
- For multiple Zotero destinations, attach the same paper item to multiple collections

## Step 5: Update want_2_read.md

Replace each processed unresolved checkbox entry with exactly this canonical resolved format:
```markdown
- [ ] [[Literature/<CurrentTopLevel>/<CurrentSubfolder>/Paper Title]]
  **Тема**: Human-readable topic name
  **Предлагаемая папка**: `Literature/<TopLevel>/<CurrentSubfolder>`
  **arXiv**: https://arxiv.org/abs/ARXIV_ID
  **Zotero**: zotero://select/library/items/ZOTERO_KEY
  **Дата**: YYYY-MM-DD
  **Краткая идея**: подробное русское описание, собранное из итоговой Obsidian note после `paper-ingest`, достаточное чтобы понять статью без открытия PDF
```

Leave unprocessable entries (couldn't find on arXiv) as-is with a note:
```markdown
- [ ] Some raw title
  **Тема**:
  **Предлагаемая папка**:
  **arXiv**:
  **Zotero**:
  **Дата**:
  **Краткая идея**: не найдено на arXiv, уточни название
```

If the title resolves to a non-arXiv paper but there is still enough metadata to ingest through DOI or other external bibliographic source, do that instead of leaving the entry raw.
Only leave an entry unresolved when you truly cannot create a reliable Zotero + Obsidian record.

## Step 6: Finalize Placement Automatically

For each successfully ingested paper:
- move the Obsidian note from the temporary ingest location into its final permanent folder
- move the Zotero item into the matching permanent collection
- if a new folder was needed, create the corresponding permanent destination and use it immediately

Update `want_2_read.md` in-place so each processed unresolved checkbox entry becomes a final unchecked checkbox with a permanent WikiLink.

The description in `want_2_read.md` must not be a short shortlist blurb. It must be copied or condensed from the full `paper-ingest` note and remain detailed enough that the user can understand the paper without opening the PDF.

The `**Zotero**:` field in `want_2_read.md` must point to the Zotero parent paper item, not to the PDF attachment. The parent item itself must already be a proper bibliographic record, not a `webpage` placeholder.

Do not flatten the document:
- preserve `## Daily_papers_DD-MM-YYYY`
- preserve thematic `### ...` subheadings inside daily blocks
- keep processed entries in their original section

## Step 7: Batch Quality Review

After all entries are merged back into `want_2_read.md`, run one final review agent over the whole batch.

This review agent must:
- read the updated `want_2_read.md`
- collect all wiki-links created or updated in this run
- open every corresponding Obsidian card
- verify that each card has complete frontmatter, valid Zotero link, BibTeX section, all 7 explanation sections, and Related Papers
- verify that the prose is in strong Russian, without awkward mixed Russian-English fragments or ugly literal calques
- verify that explanations are specific, not shallow, and contain concrete mechanisms, formulas, and numbers where the paper supports them
- strengthen any weak cards immediately instead of only listing problems
- check for duplicated status markers, malformed headings, or broken formatting in `want_2_read.md`

Minimum bar for the review agent:
- if a card feels weaker than the better cards in the same batch, it should be rewritten or expanded
- if a summary in `want_2_read.md` is noticeably weaker than the underlying card, it should be tightened
- if a card is metadata-only because no PDF was obtainable, that limitation must be stated explicitly and clearly

## Step 8: Report to User

After processing all entries, report only the finished results:
```text
Обработано N статей.

Готовые ссылки:
- [[Literature/.../Paper A]]
- [[Literature/.../Paper B]]
```

If some entries could not be resolved at all, list them separately as unresolved titles or URLs.

## Key Rules

- Never create duplicates — always check existing library first
- want_2_read.md is updated in-place
- only unresolved unchecked checkbox entries are processing targets by default
- completed checkboxes `- [x]` must be preserved and skipped
- Daily blocks created by `paper-search` under `## Daily_papers_DD-MM-YYYY` must be preserved
- thematic substructure inside daily blocks must be preserved
- final resolved entries should remain unchecked checkboxes with permanent WikiLinks so the user can later mark them as read
- canonical article fields are checkbox + article header, then `**Тема**`, `**Предлагаемая папка**`, `**arXiv**`, `**Zotero**`, `**Дата**`, `**Краткая идея**`
- `**Тема**` is a human-facing label and must not use underscore slugs like `lora_base`
- Haiku agent writes cards; sonnet verifies 7 sections + Related Papers
- Ingest uses the `paper-ingest` skill pipeline exactly, and `want-2-read` must explicitly invoke that skill
- Batch processing must be fan-out by paper: one unresolved entry → one agent → one `paper-ingest` run
- After the per-paper fan-out, one additional review agent must check the whole batch and strengthen weak outputs
- This skill does eager ingest for all valid entries in the reading list
- This skill auto-classifies and auto-moves papers into permanent folders without asking first
- Writing only a description for a raw title or URL without creating the Zotero + Obsidian pair is a failure, not a partial success
- If no current folder fits, create the best new permanent folder instead of leaving the paper in a temporary inbox
- If paper not findable: leave entry with strikethrough + explanation
- Do not assume a fixed Literature taxonomy; inspect the current tree every run
- Do not propose papers already present in the library, inbox, or trash
- Accepted papers from `paper-search` are not considered done until the Zotero parent paper item exists, its PDF attachment exists, the Obsidian note exists, and the `want_2_read.md` entry contains both the wiki-link and the parent-item `zotero://` link
