---
name: want-2-read
description: Use when the user wants to process the reading queue on the Operon Reading board. Sync the AlphaXiv "Want to read" folder into the board, take the cards in the «Очередь» column that have no library link yet, fully ingest them through paper-ingest into Zotero and Obsidian, classify them into the current Literature folders, mirror the placement to AlphaXiv, and write the final wiki-link, Zotero link, and a detailed description back into each card.
version: 2.1.0
---

# Skill: want-2-read

## Trigger

Use when the user writes `/want-2-read` or asks to "обработай мой список статей", "process my reading list", "разбери очередь чтения", "синхронизируй Want to read".

## Two sources, one queue

The reading queue has **two** entry points and they must be reconciled every run:

1. **Operon Reading board** (master) — `Operon/Reading/<Заголовок статьи>.md`, one file per card,
   columns are statuses: `_Trash` → `Инбокс` → `Жду публикацию` → `Очередь` → `Читаю` → `Прочитано`.
2. **AlphaXiv "Want to read"** folder (`folder_id` = `want_to_read_folder_id` in
   `~/.claude/alphaxiv-library-map.json`) — where the owner drops papers from the phone or the
   alphaxiv.org site without opening Obsidian.

Per `~/.claude/rules/alphaxiv-sync.md` rule 2, a paper sitting in AlphaXiv "Want to read" is a
**decision to read**, so it maps to the «Очередь» column, not to «Инбокс». Step 1 below imports
those papers into the board before anything else happens.

Column ownership:
- `Инбокс` — `paper-search` writes here. The owner decides and drags. **This skill never processes
  Инбокс** and never promotes a card out of it.
- `Жду публикацию` — интересная работа подтверждена, но надёжной публичной версии ещё нет. The
  skill rechecks availability, but never ingests a title-only record and never changes its status.
- `Очередь` — accepted papers. **This is the input of `/want-2-read`.**
- `Читаю`, `Прочитано` — reader columns, untouched. Operon auto-archives finished cards into
  `Operon/Archives` a day later via `~/.local/bin/operon_daily_archive.py`.
- `_Trash` — explicit rejection. It is terminal (`isCancelled`) and is archived by the same
  nightly script. A rejected arXiv ID must also be removed from AlphaXiv «Want to read».

The skill never changes a card's `status`. Moving a card between columns is the owner's action;
the skill only fills a card in until it is *resolved*.

## Canonical card schema

Every card carries these four sections. They are all preserved on every write. If a section is
missing, add it empty rather than skipping it; if a section already has owner-written text, extend
it, never overwrite it.

```markdown
---
operonId: <7 символов [a-z0-9], уникально по всей Operon/Reading/>
status: Reading.<_Trash|Инбокс|Жду публикацию|Очередь|Читаю|Прочитано>
priority: C
datetimeCreated: <ISO, локальное время>
datetimeModified: <ISO, локальное время>
---
# <Заголовок статьи>

## Заметка
[[Literature/<TopLevel>/<Subfolder>/<Sanitized Paper Title>]]

## arXiv
https://arxiv.org/abs/<ARXIV_ID>

## Тема
<человекочитаемая тема>

## Комментарии
<подробное описание статьи на русском, собранное из итоговой Obsidian-заметки>

**Zotero**: zotero://select/library/items/<PARENT_KEY>
**Папка**: `Literature/<TopLevel>/<Subfolder>`
```

Rules for the schema:

- Section **order is free**. Older cards have `## Тема` before `## Заметка`; do not reshuffle them.
- `## Заметка` **empty** normally means the paper has never been through `paper-ingest`. A second
  explicit selector is `paperIngestState: pending`, used when an earlier metadata-only note must be
  rebuilt after a public full text appears. Never put a placeholder in `## Заметка`.
- `## Тема` is a human-facing label: `LoRA base`, `Zero-order optimization`, `Muon`,
  `Continual learning`. Never an underscore slug like `lora_base` and never a raw folder tail.
- `## Комментарии` holds the substance: the detailed Russian description, plus the `**Zotero**:`
  and `**Папка**:` lines. It is also where the owner's own notes live — **their text is never
  deleted**. Append the generated description below whatever is already there.
- `## Идея / комментарии` is a legacy alias for `## Комментарии`. Rename the heading, keep the body.
- The `**Zotero**:` link must point at the **parent paper item**, never at the PDF attachment.
- Titles in `[[Literature/...]]` use the sanitized title from `paper-ingest` (no `$`, no `\`).
- A card created manually from the Kanban may initially contain only Operon frontmatter and a title,
  and may physically land outside `Operon/Reading/`. On every run, normalize such a Reading card:
  preserve its status and owner text, add the four missing sections, and move the file into
  `Operon/Reading/` before processing it. Never require the owner to fill metadata by hand.
- The supported manual path is: column `Очередь` → `+` → `FI Create File Task` → title →
  `Pick a Template` → `Reading Paper` → `File`. Do not recommend `Minimal File Task — Reading`:
  Operon 3.0.1 resets that template to the pipeline's first status (`Reading.Инбокс`) even when the
  creator was opened from another column.

A card is **resolved** when `## Заметка` holds a real `[[Literature/...]]` wikilink and
`## Комментарии` holds the description plus the Zotero link. Resolved is not the same as read:
"read" is `status: Reading.Прочитано`, set by the owner in Operon.

## Step 0: Pre-flight — free the Zotero SQLite lock

**HARD RULE.** Before launching any per-paper agent, quit Zotero desktop. While Zotero runs it holds
an exclusive write-lock on `~/Zotero/zotero.sqlite`, which turns every parallel `paper-ingest` agent
into a retry loop (measured on a 5-paper batch: ~16 min/agent with Zotero open vs ~2-3 min/agent
with it closed).

```bash
osascript -e 'tell application "Zotero" to quit'
sleep 3
pgrep -lf "Zotero" | head -5    # должно быть пусто
fuser ~/Zotero/zotero.sqlite    # должно быть пусто
```

Never `kill -9` — a corrupted DB write tail is far worse than a slow batch. Tell the user one line:
"Закрыл Zotero на время батча, перезапущу в конце." Skip this step entirely if the user says
"не закрывай Zotero" or the batch is exactly one paper.

## Step 1: Sync AlphaXiv «Want to read» into the board

Run this **before** collecting work, every time, even when the user asks only to "process the queue".

```
mcp__claude_ai_alphaXiv__list_library(include_papers=true)
```

The response is large; read it from the saved tool-result file rather than into context, and extract
only the `Want to read` folder's papers:

```bash
python3 - <<'PY'
import json
p = "<PATH_TO_SAVED_TOOL_RESULT>"
d = json.load(open(p))
for f in d["folders"]:
    if f["name"] == "Want to read":
        for pp in f.get("papers", []):
            print(pp["universal_paper_id"], "|", pp.get("title", ""))
PY
```

Before importing, scan live Reading cards and `Operon/Archives/Reading/` for
`status: Reading._Trash`. For every rejected card with an arXiv ID that is present in AlphaXiv
«Want to read», call `remove_papers_from_folder` on the Want-to-read folder. This is queue cleanup,
not deletion from thematic AlphaXiv folders. It prevents a rejected paper from being resurrected.

For each paper in "Want to read":

1. Look for an existing live or archived card whose `## arXiv` holds that arXiv ID, or whose title
   matches. A rejected match is removed from AlphaXiv «Want to read» and never imported. Any other
   match is not duplicated. If it is not in `Очередь`, report the status conflict and leave the
   AlphaXiv queue item in place for the owner to decide.
2. If no card exists, create one in `Operon/Reading/` with `status: Reading.Очередь`, an empty
   `## Заметка`, the arXiv URL, a topic guess, and one line in `## Комментарии` recording where it
   came from and when. Filename is the sanitized paper title, never the arXiv ID: a human reads it.
3. `operonId` must be unique across `Operon/Reading/` **and** `Operon/Archives/` — check before writing.

Do **not** remove anything from "Want to read" at this step. Removal happens in Step 6, atomically
with filing the paper into its topic folder, so a crash mid-batch never loses a queue item.

Report the import in one line: "Импортировал N статей из Want to read в «Очередь»."

If the AlphaXiv MCP is not connected, do the local work anyway and tell the user the AlphaXiv side
was skipped and needs `/mcp` auth. Never silently drop it.

### Step 1b: Recheck «Жду публикацию»

For every live card with `status: Reading.Жду публикацию`, search the exact title in official
sources (arXiv, OpenReview, DOI/Crossref, DBLP, or the venue page). Record `paperLastChecked` in
frontmatter. If a reliable public version appears, fill `## arXiv` or add the canonical DOI/venue
URL and append a short availability note under `## Комментарии`; tell the owner that the card is
ready to drag to `Очередь`. Do not change the status and do not run `paper-ingest` while it remains
in `Жду публикацию`.

## Step 2: Collect the work

```bash
VAULT="${OBSIDIAN_VAULT:?set OBSIDIAN_VAULT to the vault root}"
rg -l '^status: Reading\.Очередь$' "$VAULT/Operon" -g '*.md' \
  | rg -v '/Operon/Archives/' \
  | while IFS= read -r card; do
      if ! rg -q '\[\[Literature/' "$card" || rg -q '^paperIngestState: pending$' "$card"; then
        printf '%s\n' "$card"
      fi
    done
```

This vault-wide scan is intentional: Operon's native `+` creator may save a new Reading card in
the global File Tasks folder. Before collecting work, normalize every live `status: Reading.*`
file outside `Operon/Reading/` and move it there with a collision-safe filename.

Interpretation:
- card in `Очередь` without `[[Literature/...]]` → **unresolved, process it**
- card in `Очередь` with the link → already resolved, unless `paperIngestState: pending`
- card in `Инбокс` → the owner has not decided, **do not process, do not comment, do not promote**
- card in `Жду публикацию` → only run the availability check from Step 1b
- card in `_Trash` → never ingest; use it only for dedup and AlphaXiv queue cleanup
- cards in `Читаю` / `Прочитано` → never processed, never overwritten

Hard interpretation rule: a bare URL or a lone title in a card is **not** a processed entry. Adding
only a description under a raw title is **not** sufficient. An entry counts as processed only after a
full `paper-ingest` run with a real Zotero parent paper item, a PDF child attachment, and a final
Obsidian note.

## Step 3: Infer the current library structure

Do not use a hardcoded ontology. Inspect the live tree every run:

```bash
LIB="$VAULT/Literature"
find "$LIB" -mindepth 2 -maxdepth 2 -type d | sort
find "$LIB" -name "*.md" | xargs grep -h "^tags:" -A 20 | grep "  - " | sed 's/^  - //' | sort | uniq -c | sort -rn
```

Collect every arXiv ID already seen so nothing gets re-ingested or re-suggested:

```bash
find "$LIB" -name "*.md" | xargs grep -h "arxiv.org/abs/" | grep -oE "[0-9]{4}\.[0-9]{4,5}" | sort -u > /tmp/all_seen_arxiv_ids.txt
```

Relevance signals: existing folder names, note titles, note tags, and the project cards under
`Papers/`, `Projects/`, `Staff/`.

When the Zotero MCP is available, `mcp__zotero__zotero_semantic_search` over the library is a better
classifier than folder-name matching — use it to find the nearest existing papers and place the new
one beside them.

## Step 4: Fan out — one agent per paper

Agent orchestration is not optional:

- first collect the **full** set of unresolved cards
- then launch **one separate agent per paper**
- each per-paper agent resolves exactly one paper and then explicitly invokes the `paper-ingest` skill
- never process the whole batch inside a single agent
- never mix several papers into one ingest agent

Each per-paper agent runs the full `paper-ingest` pipeline — the whole thing, not a metadata lookup:

1. duplicate check (Zotero API + SQLite + Obsidian grep)
2. BibTeX from external APIs (DOI → DBLP → arXiv)
3. PDF download, text extraction, LaTeX source bundle for figures and tables
4. Zotero parent item (`preprint`) + PDF child attachment
5. the full Obsidian note with all 8 explanation sections
6. Papers with Code enrichment, final audit

This is a hard workflow boundary:
- `want-2-read` **must** call the `paper-ingest` skill for every resolvable paper
- **the depth of the note is not negotiable.** Dropping the reading-queue file changed nothing about
  the pipeline: every paper still gets the complete `paper-ingest` treatment and a full Obsidian note.
- it is not acceptable to imitate `paper-ingest` loosely or to stop after metadata lookup
- if `paper-ingest` was not invoked, this workflow is incomplete
- if the final review agent was not run, this workflow is incomplete

If the paper is already in the library, link the existing note instead of re-ingesting.

Unlike `paper-search`, this workflow is not shortlist-first. Every card in «Очередь» without a
library link is ingested and filed into a permanent folder in the same run.

## Step 5: Classify into permanent folders

For each paper, pick a permanent collection from its tags and content:

- infer the current top-level and sub-collection structure from the live tree
- match title, abstract, and tags against current folder names and note tags
- pick the most relevant existing folder, or create a new one when nothing fits

Behaviour:
- a strong existing destination → move the paper there automatically after ingest
- no folder fits → create the best new permanent folder and place the paper there immediately
- never leave a successfully processed paper in `_inbox` because classification was imperfect
- several destinations → the first is canonical; the others get **hard links** in Obsidian (never
  symlinks) and the same Zotero item added to each collection

## Step 6: Mirror the placement to AlphaXiv

**Mandatory.** Local Obsidian is master, AlphaXiv mirrors it, and the two must not drift.
Read `~/.claude/alphaxiv-library-map.json` for the target `folder_id`.

- Paper came from "Want to read" (Step 1 imported it, or it was already there):
  ```
  mcp__claude_ai_alphaXiv__move_papers_between_folders(
      from_folder_id=<want_to_read_folder_id>,
      to_folder_id=<mapped topic folder_id>,
      paper_ids_or_urls=[<arxiv_id>])
  ```
  This adds to the topic folder and clears the queue entry in one call.
- Paper was not in "Want to read":
  ```
  mcp__claude_ai_alphaXiv__save_papers_to_folder(
      folder_id=<mapped topic folder_id>, paper_ids_or_urls=[<arxiv_id>])
  ```
- Multiple destinations → repeat `save_papers_to_folder` for each; a paper may live in several folders.
- New local folder created in Step 5 → `create_folder` nested under the mapped top-level parent,
  then **add its id to `~/.claude/alphaxiv-library-map.json`**.
- Stale `folder_id` (call errors) → refresh via `list_library` and update the map file.
- **Non-arXiv paper** (ICML-poster-only, book, blog digest): file it locally, skip the MCP call, and
  tell the user it can be uploaded manually as a Private Paper on alphaxiv.org. The MCP has no upload
  tool. Do not fake an arXiv ID.
- Never touch `My publications` or `Private Papers`.

At the end of the batch, verify the mirror: the arXiv IDs you filed this run must all report the
expected folder in `list_library(paper_ids_or_urls=[...])`.

## Step 6b: Push into the shared lab corpus

**Mandatory, and the step this skill used to be missing entirely.** A batch filed through this
board landed in Obsidian, Zotero and AlphaXiv but never reached the Lab Knowledge corpus: forty
papers were invisible to `search_lab`, to `related_by_terms` and to every question asked at the
level of a research theme. The board is not the library of record for the lab; the corpus is what
other members search.

For every paper filed in Step 5:

```bash
python3 ~/.claude/skills/paper-ingest/scripts/sync_to_lab.py --arxiv {ARXIV_ID} --verify
```

`--verify` asks the base afterwards and prints the title and the number of sections. A reading with
one section means only metadata arrived; a reading with none means nothing did. Both are failures,
not successes — the exit code alone is not evidence.

The whole batch can also go in one command, which is idempotent and matches papers by their natural
key:

```bash
python3 ~/.claude/skills/paper-ingest/scripts/sync_to_lab.py --all
```

The push refuses to overwrite a fuller reading someone else wrote, so repeating it is safe. If the
base is unreachable, finish the local work and say the corpus push was skipped — never drop it
silently. The theme of the paper is derived on the server from its `library_folder`, so nothing has
to be passed here; a folder that is new to the map falls back to the theme of its section, which is
coarser than it deserves (see `library_themes.py`).

## Step 7: Write the cards back

Fill in the card **in place**, preserving `operonId`, `status`, `priority`, the dates, the title, and
every line the owner wrote themselves:

- `## Заметка` → the permanent `[[Literature/<Top>/<Sub>/<Sanitized Title>]]` wikilink
- `## arXiv` → the canonical `https://arxiv.org/abs/<ID>` URL, if the section was empty
- `## Тема` → the human-readable topic, if the section was empty or held a slug
- `## Комментарии` → the detailed Russian description, then the `**Zotero**:` and `**Папка**:` lines

After a successful full ingest, remove `paperIngestState: pending` (or set it to `complete`).

The description must not be a one-line annotation. Condense it from the full `paper-ingest` note and
keep it detailed enough that the user understands the paper without opening the PDF: the problem, the
mechanism, the key formulas in words, the setup, and the headline numbers.

**HARD RULE — the skill never changes `status`.** No promoting a card to `Читаю`, no marking anything
`Прочитано`, no writing `dateCompleted`. Those are exclusively the owner's signals, set by dragging
the card in Operon. This applies to per-paper agents, the merge step, and the QA review agent alike.

If a paper cannot be resolved at all, leave the card in place, leave `## Заметка` empty, and write the
reason into `## Комментарии` — what you searched (arXiv, DBLP, OpenReview, Semantic Scholar, Crossref,
OpenAlex), what the nearest real papers are, and what the owner should supply (exact title or arXiv
ID). A card that names its own blocker is a useful card. Only give up when no reliable Zotero +
Obsidian record can be created; if the title resolves to a non-arXiv paper with a DOI or another
bibliographic source, ingest through that instead.

## Step 8: Batch quality review

After all cards are written, launch **one** final review agent over the whole batch. Its only job is
quality control, and it fixes rather than reports.

It must:
- read every updated card
- open every Obsidian note created or updated in this run
- verify each note has complete frontmatter, a valid `zotero_link` to the **parent** item, a BibTeX
  block, all 8 explanation sections, and `## Related Papers`
- verify the prose is strong Russian, without mixed Russian-English fragments or ugly literal calques
- verify explanations are specific: concrete mechanisms, formulas, and numbers where the paper supports them
- verify each card has all four sections, no duplicated links, no broken heading, and an intact `operonId`
- verify the AlphaXiv mirror actually landed for every arXiv-bearing paper in the batch
- **strengthen anything weak immediately** instead of listing problems

Minimum bar: if a card or note is noticeably weaker than the better ones in the same batch, rewrite or
expand it. If a note is metadata-only because no PDF was obtainable, that limitation must be stated
explicitly in both the note and the card.

The batch is not complete until this agent finishes.

## Step 9: Report, then relaunch Zotero

```text
Импортировано из Want to read: K статей.
Обработано: N статей.

Готовые ссылки:
- [[Literature/.../Paper A]]
- [[Literature/.../Paper B]]

AlphaXiv: перенесено в тематические папки N, очередь Want to read очищена.
```

List unresolved cards separately with their blocker.

```bash
open -a Zotero
```

Mandatory unless Step 0 was skipped, and mandatory **even if the batch failed midway**, so the user is
never left with a closed Zotero. Zotero autosyncs the new items, attachments, and collection
memberships on startup.

## Key Rules

- Both sources are read every run: the Operon board **and** the AlphaXiv "Want to read" folder
- AlphaXiv "Want to read" maps to «Очередь», not to «Инбокс»
- Manually created Reading cards are discovered vault-wide, normalized, and moved to `Operon/Reading/`
- `Жду публикацию` is rechecked but never ingested until the owner moves it to `Очередь`
- `_Trash` is terminal, deduplicated through the archives, and removed from AlphaXiv «Want to read»
- Processing targets are cards in «Очередь» with empty `## Заметка` or `paperIngestState: pending`
- The skill never changes `status` and never writes `dateCompleted`
- Owner-written text in `## Тема` and `## Комментарии` is never deleted, only extended
- All four card sections are always present; `## Идея / комментарии` is renamed, its body kept
- Every paper goes through the **full** `paper-ingest` pipeline and gets a complete Obsidian note.
  This is the point of the skill, not an optional depth setting
- Batch processing is fan-out by paper: one card → one agent → one `paper-ingest` run
- One additional review agent checks the whole batch and strengthens weak output
- Every arXiv-bearing paper is mirrored to AlphaXiv in Step 6; non-arXiv papers are reported, not faked
- New local folder → `create_folder` on AlphaXiv **and** a new entry in `alphaxiv-library-map.json`
- Never create duplicates — check Zotero, SQLite, and Obsidian first
- `**Zotero**:` always points at the parent paper item, never at the PDF attachment
- Do not assume a fixed Literature taxonomy; inspect the current tree every run
- Do not propose papers already present in the library, inbox, or trash
- ALWAYS quit Zotero at Step 0 and relaunch at Step 9. Use
  `osascript -e 'tell application "Zotero" to quit'`, never `kill -9`; verify with `pgrep -lf Zotero`
