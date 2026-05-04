---
name: paper-ingest
description: Ingest papers from AlphaXiv/arXiv into Zotero + Obsidian. Trigger when user provides an arXiv URL or AlphaXiv folder link and wants a full literature note created. Handles BibTeX from external APIs, PDF download, creation of a proper Zotero parent paper item with child PDF attachment, duplicate prevention, and an especially detailed Obsidian note with 7-section AI Explanation written by haiku.
version: 1.4.0
---

# Paper Ingest Pipeline

End-to-end pipeline: AlphaXiv/arXiv link → PDF + BibTeX + Zotero + Obsidian note.

## Hard Rule

If the source paper is a **local PDF** in `~/Downloads/` or any other filesystem path and the user asks to read, explain, summarize, or create a note for it:
- **first create or find the Zotero parent item**
- **then attach the local PDF to that Zotero item**
- **only after that read the PDF and write the Obsidian note**

Never explain a local PDF without first ingesting that exact file into Zotero.
If the Zotero parent item already exists, attach the PDF as a child attachment instead of creating a duplicate top-level item.

If the same paper must appear in multiple Obsidian Literature folders:
- do **not** keep two independent `.md` copies
- do **not** use symlinks inside the Obsidian vault
- use a **hard link** so both paths point to the same file content and edits stay synchronized
- choose one canonical source file and link the secondary locations to it

If the same paper must appear in multiple Zotero collections:
- do **not** create duplicate Zotero items
- keep one canonical Zotero item
- add that same item to each required collection
- if the caller passes an ordered list of destination folders, treat the first destination as canonical for the Obsidian note path and use hard links for the remaining folders

## Trigger

Use when the user provides:
- An arXiv or AlphaXiv URL and a folder/collection name
- "Add this paper", "Ingest this paper", "Создай заметку для этой статьи"
- A batch of arXiv URLs for a collection

## Quality Bar

The note must be detailed enough that the user can understand the paper without opening the PDF. Treat that as a hard quality bar, not a nice-to-have.

High-quality local example for depth and structure:
- `${OBSIDIAN_VAULT}/Literature/PEFT/lora_base/ShadowPEFT: Shadow Network for Parameter-Efficient Fine-Tuning.md`

Use this example as a style and completeness reference, especially for:
- mechanism explained step by step
- formulas tied back to the mechanism
- concrete table numbers
- ablations and deployment modes
- non-handwavy critical assessment

The default target is:
- not a short summary
- not a marketing overview
- not a loose intuition-only explanation
- but a dense research note that lets the reader reconstruct the method, setup, and main claims from the note alone

At minimum, a good paper note must make it possible for the reader to answer all of these without reopening the paper:
- What exact problem is solved?
- What are the core objects, states, modules, or optimization variables?
- How does the method work step by step?
- Which equations define it?
- What are the training and inference modes?
- What data, models, and baselines were used?
- What exact numbers were reported in the main tables or figures?
- What do the ablations show?
- What are the real limitations of the paper?

## Pipeline Steps

## Canonical Successful Outcome

For a paper ingest to count as successful, **all** of the following must be true:

1. There is exactly one canonical Zotero **parent** paper item for the article.
2. That parent item is a real bibliographic type such as `preprint`, `journalArticle`, or `conferencePaper`, not `webpage`.
3. The parent item has the correct title, creators, year, URL, and intended collection membership.
4. The parent item has a child PDF attachment stored in Zotero.
5. The Obsidian note frontmatter uses:
   - `zotero_key` = the **parent paper item** key
   - `zotero_link` = `zotero://select/library/items/PARENT_KEY`
6. The PDF attachment key is **not** written into the Obsidian note as the main Zotero key or main Zotero link.
7. The final audit passes.

If any one of these is false, the ingest is incomplete and must be repaired before the workflow is considered done.

## Canonical Happy Path

For arXiv papers, the default happy path is:

1. Extract `ARXIV_ID`.
2. Run duplicate checks in Zotero, SQLite, and Obsidian.
3. Fetch BibTeX and metadata via `bibtex_fetch.py`.
4. Download PDF to `~/Papers/Library/ARXIV_ID.pdf` and extract text.
5. Create a proper Zotero **parent** item via `connector/saveItems` with `itemType: preprint`.
6. Verify the parent item is not `webpage` and has correct metadata.
7. Ensure the parent item belongs to the intended Zotero collection.
8. Close Zotero if needed and attach the local PDF to that parent via `zotero_attach_pdf.py`.
9. Re-open Zotero if needed and verify the PDF child attachment exists.
10. Write the Obsidian note using the parent item key in frontmatter.
11. Run final audit.

Do not reorder these steps casually. In particular, do not write the final Obsidian note before the Zotero parent item is known-good.

### Step 0: Local PDF pre-ingest

If the source is a local PDF, not an arXiv/AlphaXiv URL:

1. Identify the paper from filename, DOI, first page, or existing Obsidian/Zotero context.
2. Check for an existing Zotero parent item by title/DOI.
3. If the parent item exists, attach the local PDF to it.
4. If the parent item does not exist, create the Zotero item first, then attach the PDF.
5. Only after successful attachment, continue with note generation.

Attachment script:

```bash
python3 ~/.claude/skills/paper-ingest/scripts/zotero_attach_pdf.py \
  --parent-key ZOTERO_KEY \
  --pdf ~/Downloads/"Paper Title.pdf" \
  --url PAPER_URL
```

This script must be run with Zotero closed because it edits the Zotero DB and storage directly.

When using this script, remember:
- `--parent-key` must be the Zotero **paper parent** item key
- the created attachment is a child PDF item
- the attachment key is not the canonical literature key for Obsidian frontmatter

### Step 1: Extract arXiv ID

From any of these formats:
- `https://arxiv.org/abs/2509.07972` → `2509.07972`
- `https://www.arxiv.org/abs/2509.07972v2` → `2509.07972`
- `https://alphaxiv.org/...` → extract the arXiv ID from the page or URL

### Step 2: Check for duplicates in Zotero

Before doing anything, check if the paper already exists:

```bash
python3 ~/.claude/skills/paper-ingest/scripts/zotero_check_dup.py --arxiv ARXIV_ID
```

If the Zotero API is unavailable (Zotero not running), also check the SQLite DB:

```bash
sqlite3 ~/Zotero/zotero.sqlite \
  "SELECT items.key, fieldValues.value FROM items
   JOIN itemData ON items.itemID = itemData.itemID
   JOIN fields ON itemData.fieldID = fields.fieldID
   JOIN itemDataValues fieldValues ON itemData.valueID = fieldValues.valueID
   WHERE fields.fieldName='url' AND fieldValues.value LIKE '%ARXIV_ID%';"
```

Also check the Obsidian Literature folder:
```bash
grep -rl "ARXIV_ID" "${OBSIDIAN_VAULT}/Literature/" 2>/dev/null
```

If duplicate found anywhere:
- Report the existing item's key, collection, and Obsidian path
- Check whether the Zotero item has `deleted = true` or lives in trash
- If it is in trash, restore it instead of creating a new duplicate
- Ask user whether to skip, update, or force-add
- **NEVER create a duplicate without explicit confirmation**

### Step 3: Fetch BibTeX (external, NOT LLM-generated)

**CRITICAL: All BibTeX content comes from external APIs. The LLM must NEVER invent, guess, or modify BibTeX fields.**

```bash
python3 ~/.claude/skills/paper-ingest/scripts/bibtex_fetch.py --arxiv ARXIV_ID
# For published papers with DOI:
python3 ~/.claude/skills/paper-ingest/scripts/bibtex_fetch.py --doi DOI_STRING
```

The script fetches from `arxiv.org/bibtex/{id}` or `doi.org/{doi}`, generates a Google Scholar key (`{lastname}{year}{firstword}`), and outputs JSON with `bibtex`, `citation_key`, `title`, `authors`, `year`.

If the script fails, report the error and do NOT fall back to LLM-generated BibTeX. Offer to retry or proceed with a placeholder `[BibTeX pending]`.

After fetching BibTeX from any external source, normalize it before writing it into the Obsidian note:

```bash
python3 ~/.claude/skills/paper-ingest/scripts/normalize_markdown_bibtex_authors.py
```

Hard BibTeX rule:
- author names in the final card must be normalized to BibTeX-friendly `Surname, Firstname` form when applicable
- do not hand-edit author order ad hoc in the note
- if the fetched external BibTeX is correct semantically but uses `Firstname Lastname`, run the normalization script instead of rewriting by hand
- if the external source is OpenReview, DOI, DBLP, or another non-arXiv source, the same normalization rule still applies

### Step 4: Download PDF (temporary)

Download to `~/Papers/Library/` for reading. After Zotero imports the paper (Step 5),
the local copy is redundant — Zotero stores its own PDF in `~/Zotero/storage/`.

```bash
ARXIV_ID="2509.07972"
curl -L -o "$HOME/Papers/Library/${ARXIV_ID}.pdf" "https://arxiv.org/pdf/${ARXIV_ID}.pdf"
```

Read with:
```bash
python3 ~/.claude/skills/pdf-reader/scripts/extract_pdf.py "$HOME/Papers/Library/${ARXIV_ID}.pdf"
```

**After Zotero import succeeds, delete the local copy:**
```bash
rm "$HOME/Papers/Library/${ARXIV_ID}.pdf"
```

`~/Papers/Library/` is a staging area, not permanent storage. Zotero is the PDF archive.

PDF naming: `{arxiv_id}.pdf`. Extract text immediately for the AI step:

```bash
export PATH=/opt/homebrew/bin:$PATH
pdftotext "$HOME/Papers/Library/${ARXIV_ID}.pdf" /tmp/paper_${ARXIV_ID}.txt
```

### Step 5: Import to Zotero

**Prerequisite: Zotero must be running for API import.**

**Critical rule:** never use `connector/saveSnapshot` on an `arXiv` abstract URL as the primary ingest path. In this environment it can create a top-level `webpage` item instead of a real paper record. That is a broken ingest and must be treated as failure.

Get the collection key:
```bash
curl -s "http://localhost:23119/api/users/0/collections?format=json" | python3 -c "
import json, sys
colls = json.loads(sys.stdin.read())
for c in colls:
    print(f'{c[\"key\"]}: {c[\"data\"][\"name\"]}')"
```

Create a real paper parent item first. For arXiv papers the preferred parent item type is `preprint`.

Recommended local path:
```bash
curl -s -X POST "http://localhost:23119/connector/saveItems" \
  -H "Content-Type: application/json" \
  -d '{"items":[{"itemType":"preprint","title":"FULL PAPER TITLE","abstractNote":"Imported via paper-ingest skill","date":"YEAR","url":"https://arxiv.org/abs/ARXIV_ID","repository":"arXiv","creators":[...]}]}'
```

If collection assignment is not honored by the local connector, repair collection membership immediately after creation using the local SQLite workflow or a write-capable Zotero API path. Do not leave the parent item in root or in the wrong top-level collection.

Retrieve the assigned Zotero key after import:
```bash
curl -s "http://localhost:23119/api/users/0/items?q=ARXIV_ID&format=json&limit=5" | python3 -c "
import json, sys
items = json.loads(sys.stdin.read())
for i in items:
    d = i.get('data', {})
    if d.get('itemType') not in ('attachment', 'note'):
        print(i['key'], d.get('title','')[:60])"
```

Immediately validate the created parent item:
- `itemType` must be a real bibliographic type like `preprint`, `journalArticle`, `conferencePaper`, `book`, etc.
- `itemType` must **not** be `webpage`
- title must match the actual paper title, not the raw URL
- creators must be populated
- collection membership must point to the intended collection

If the created parent item is `webpage`, has the raw URL as title, has no creators, or lands in the wrong collection:
- treat this as failed ingest
- create a fresh proper paper item
- move the broken item to trash
- reattach or recreate the PDF under the fixed parent

Record the bibliographic parent key as `zotero_key` for Obsidian frontmatter.

Never put the child attachment key into:
- `zotero_key`
- `zotero_link`
- `want_2_read.md` `**Zotero**:` field

Those fields must always point to the canonical paper parent item.

If Zotero is not running: create the Obsidian note without `zotero_key`, leave `zotero_key: "PENDING"` and tell the user.

### Step 6: Create Obsidian Note (haiku agent)

**The AI Explanation is written by `claude-haiku-4-5-20251001`. Spawn it as a sub-agent.**

Target path: `{VAULT_ROOT}/Literature/{TopLevel}/{collection}/{Full Paper Title}.md`

Where `{TopLevel}` is one of: `Optimization`, `PEFT`, `LLM`, `RL`, `Applied`, `Reference`, `_inbox`.

**Vault root:** `${OBSIDIAN_VAULT}/`

**IMPORTANT:** The output file name must be the exact paper title. Never shorten or abbreviate it.

#### Frontmatter template

```yaml
---
title: "Paper Title"
zotero_key: "ZOTERO_KEY"
zotero_link: "zotero://select/library/items/ZOTERO_KEY"
url: "https://arxiv.org/abs/ARXIV_ID"
publication: "VENUE (e.g. NeurIPS 2025, ICLR 2026 (A*)) or Unpublished (arXiv preprint)"
tags:
  - tag1
  - tag2
updated: "DD-MM-YYYY"
---
```

`ZOTERO_KEY` here means the parent paper item key, not the PDF attachment key.

#### BibTeX section (verbatim from Step 3)

```markdown
## BibTeX

```bibtex
{BIBTEX_FROM_SCRIPT — pasted exactly, no edits}
```
```

#### AI Explanation (written by haiku, 7 sections, Russian + LaTeX)

Haiku agent prompt template:

```
You are writing a paper analysis card for an Obsidian research library.
Read the full paper text provided below and write ALL 7 sections in Russian.

OUTPUT FILE: {ABSOLUTE_PATH_TO_MD_FILE}

HIGH-QUALITY LOCAL EXAMPLE:
${OBSIDIAN_VAULT}/Literature/PEFT/lora_base/ShadowPEFT: Shadow Network for Parameter-Efficient Fine-Tuning.md

WRITING RULES:
- Russian prose must be the default. Use English only in narrow cases:
- when introducing a technical term after its Russian explanation in parentheses
- for standard names of models, datasets, methods, modules, metrics, and item titles
- inside formulas, code, BibTeX, file paths, and Zotero/Obsidian identifiers
- if a direct Russian replacement would be misleading or clearly unnatural
- Do not switch into English sentence fragments when a normal Russian sentence is possible
- LaTeX for ALL formulas: inline $x$, display $$\mathcal{L} = \ldots$$
- Explain EVERY variable when first introduced (no exceptions)
- NO em dashes, NO semicolons, NO promotional language, NO AI filler
- Write with enough depth that the user can understand the paper without opening the PDF
- Do not compress the paper into a shallow summary. Prefer concrete mechanisms, assumptions, equations, ablations, failure modes, and exact claims
- If the paper has a nontrivial algorithm or pipeline, explain it step by step in plain Russian
- If the paper has important limitations or hidden assumptions, make them explicit rather than vague
- Section 3 MUST include EVERY formula and EVERY theorem/lemma/proposition from the paper — not just "major" ones. For each: write the full LaTeX, then a sentence defining each symbol.
- Section 6 must include key table numbers and exact result values
- Write as if the reader will rely on this note instead of reopening the PDF
- Prefer mechanism over slogans, concrete claims over vague praise, and exact numbers over adjectives
- If the paper introduces a pipeline or module interaction, explain the order of operations explicitly
- If the paper has multiple regimes, modes, variants, or deployment settings, explain each one separately
- If the paper contains ablations, include what they changed and what conclusion follows from them
- If the paper reports only modest gains, say that clearly instead of exaggerating

Language quality rule:
- if a paragraph can be written naturally in Russian, it must be written in Russian
- avoid mixed Russian-English prose like "paper shows strong trade-off" or "метод useful for training"
- acceptable pattern: `спектральное расстояние (Spectral Wasserstein distance)` on first mention, then Russian wording afterward when possible
- do not force awkward calques just to eliminate English
- if the normal technical usage is `embeddings`, `backbone`, `perplexity`, `goodput`, `checkpoint`, or a similar standard term, prefer that term over an ugly literal translation
- when unsure, prefer either the standard English term as-is or a readable Russian phrase with the English term in parentheses on first mention
- avoid artificial replacements that make the note harder to read

REQUIRED SECTIONS (use these exact headers):

## AI Explanation

### 1. Общий обзор
3-4 dense paragraphs. Explain the problem, the proposed mechanism, the main empirical or theoretical result, the assumptions that matter, and why the work is practically or conceptually important.

### 2. Посекционный разбор
Each paper section gets its own #### subsection. Do not skip appendices if they contain substantive method, theory, training, or experimental details needed for understanding. If the paper's real substance is concentrated in one method section plus appendices, reflect that explicitly instead of writing a shallow section-by-section paraphrase.

### 3. Математика и формулы
Every key formula with LaTeX. Define each variable on first appearance. If the paper's real contribution is algorithmic rather than theorem-heavy, explain how the equations drive the method step by step.

### 4. Новые архитектуры
Forward pass + loss function if applicable. If there is no new architecture, say so directly and explain what is new instead: optimizer, routing, system design, training policy, evaluation method, or theory.

### 5. Методология и данные
Datasets, models, training setup, evaluation metrics, baselines, important ablations, and implementation details that affect interpretation. If deployment settings or inference modes matter, include them here too.

### 6. Графики и таблицы
Key figures and tables with exact numbers and takeaways. Do not write "the figure shows improvement" without naming the compared methods, the metric, and at least the most important values.

### 7. Критическая оценка
Strengths. Numbered list of limitations (be specific, not generic). Distinguish between conceptual value, empirical strength, engineering complexity, and unresolved questions.

The final card must be useful as a standalone reading substitute for first-pass understanding. If a smart reader could not explain the paper's mechanism, setup, main numbers, and limitations after reading the note, the note is not detailed enough.

## Related Papers
1-3 papers from the same `Literature/{TopLevel}/{collection}/` folder that relate to this paper.
Format: `[[Literature/{TopLevel}/{collection}/{Exact Paper Title}]]` — one sentence explaining the connection.
Focus on methodological or theoretical connections, not just topic overlap.

PAPER TEXT:
{FULL_TEXT_FROM_PDF}
```

After haiku writes the file, the main model must:
1. Read the written file and verify all 7 sections are present
2. Verify `## Related Papers` section exists with at least 1 WikiLink
3. Verify frontmatter is complete (no `PENDING` fields left unresolved)
4. If any section is missing or malformed, fix it inline (do not re-run haiku)

### Step 7: Mandatory Final Audit

**This step is required. Do not finish the add-paper workflow without it.**

Run the Python checker again at the end of the pipeline:

```bash
python3 ~/.claude/skills/paper-ingest/scripts/zotero_check_dup.py \
  --collection COLLECTION_NAME \
  --final-audit \
  --expect-title "FULL PAPER TITLE" \
  --expect-zotero-key ZOTERO_KEY
```

This final audit must algorithmically verify:
- the article exists in Zotero in the expected collection
- the Zotero parent item is a real paper item, not `webpage`
- the Zotero parent item title matches the paper title, not the URL
- the Zotero parent item has authors/creators populated
- the article exists in Obsidian in `Literature/COLLECTION_NAME/`
- the Obsidian note `zotero_key` matches the Zotero item key
- the Obsidian note `zotero_link` points to the same parent key as `zotero_key`
- the Zotero item is not in trash
- no article exists only on one side
- the Zotero parent has a PDF child attachment

If the audit output has `"ok": false`:
- stop
- inspect the returned discrepancy fields
- explain to the user exactly what is wrong
- fix the state before declaring success

## Paths and Config

| Item | Path |
|------|------|
| PDF library | `~/Papers/Library/` |
| Obsidian vault | `${OBSIDIAN_VAULT}/` |
| Literature base | `{vault}/Literature/` |
| Zotero DB | `~/Zotero/zotero.sqlite` |
| Zotero local API | `http://localhost:23119` |
| BibTeX script | `~/.claude/skills/paper-ingest/scripts/bibtex_fetch.py` |
| Duplicate check | `~/.claude/skills/paper-ingest/scripts/zotero_check_dup.py` |
| PDF attach script | `~/.claude/skills/paper-ingest/scripts/zotero_attach_pdf.py` |
| PDF extraction | `export PATH=/opt/homebrew/bin:$PATH && pdftotext` |
| AI model | `claude-haiku-4-5-20251001` |

## Duplicate Prevention And Sync Audit (full checklist)

Run ALL three checks before importing:
1. `zotero_check_dup.py --arxiv ARXIV_ID` (Zotero API)
2. SQLite query on `~/Zotero/zotero.sqlite` (works even if Zotero is closed)
3. `grep -rl ARXIV_ID` on the Literature/ folder (Obsidian)
4. For any found Zotero item, verify it is not in `deletedItems`

Then run the final collection audit after writing the note:
5. `zotero_check_dup.py --collection COLLECTION_NAME --final-audit --expect-title ... --expect-zotero-key ...`

If any check finds a hit → stop and report. Never auto-create a duplicate.

## Library Hierarchy & Zotero Keys

The library has 2 levels: `Literature/{TopLevel}/{collection}/`.

### Top-level parents (Zotero) — USER MUST FILL IN

This table maps Obsidian top-level folders to Zotero parent collection keys. Fill it in once per machine after creating the matching Zotero collections.

| Top-level | Zotero parent key |
|-----------|-------------------|
| Optimization | `<FILL_IN_AFTER_INSTALL>` |
| PEFT | `<FILL_IN_AFTER_INSTALL>` |
| LLM | `<FILL_IN_AFTER_INSTALL>` |
| RL | `<FILL_IN_AFTER_INSTALL>` |
| Applied | `<FILL_IN_AFTER_INSTALL>` |
| Reference | `<FILL_IN_AFTER_INSTALL>` |

**How to find your own parent keys** (Zotero must be running):

```bash
curl -s "http://localhost:23119/api/users/0/collections?format=json" | python3 -c "
import json, sys
for c in json.loads(sys.stdin.read()):
    parent = c['data'].get('parentCollection') or 'ROOT'
    print(f\"{c['key']}  parent={parent}  name={c['data']['name']}\")"
```

Look for the rows where `parent=ROOT` — those are top-level collections. Copy their keys into the table above.

For sub-collections you can either keep an explicit table here or always look them up at runtime via the same API.

When creating a new sub-collection, always pass the matching `parent_key` from the table so it nests correctly:

```python
mcp__zotero__zotero_create_collection(name="my-new-subcollection", parent_key=PARENT_KEY)
```

For a completely new top-level category: create the Zotero parent collection first, then add the row to this table.

## Error Handling

| Error | Action |
|-------|--------|
| Zotero not running | Create Obsidian note with `zotero_key: "PENDING"`, tell user |
| `saveSnapshot` produced `webpage` item | Create a fresh proper paper item via `saveItems`, fix collection membership, trash the broken `webpage` item, and only then continue |
| Obsidian note points to attachment key | Rewrite `zotero_key` and `zotero_link` to the parent paper item key and keep the attachment only as child PDF |
| PDF download fails | Try `export.arxiv.org/pdf/`, then ask user |
| BibTeX fetch fails | Report error, do NOT use LLM-generated BibTeX, offer to retry |
| Local PDF not in Zotero yet | Stop, ingest the PDF into Zotero first |
| pdftotext not found | `export PATH=/opt/homebrew/bin:$PATH` then retry |
| Obsidian file exists | Read it, offer to update (overwrite only the AI Explanation) |
| haiku writes wrong filename | Read wrong file, Write content to correct path, delete wrong file |
