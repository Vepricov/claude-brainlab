---
name: paper-ingest
description: Ingest papers from AlphaXiv/arXiv into Zotero + Obsidian. Trigger when user provides an arXiv URL or AlphaXiv folder link and wants a full literature note created. Handles BibTeX from external APIs, PDF download, tex-source figure/table extraction, creation of a proper Zotero parent paper item with child PDF attachment, duplicate prevention, an especially detailed Obsidian note with 8-section AI Explanation written by a specialised multi-agent pass (recon router, section writers, adversarial verifier), the AlphaXiv mirror write, and a strict BibTeX audit at the end.
version: 2.0.0
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

## Title Sanitization (for filenames and frontmatter `title:`)

Paper titles on arXiv often contain LaTeX math like `$\ell_1$ regularization`, `$\mathcal{O}(n)$`, `$k$-NN`. Obsidian rejects filenames containing `$`, `\`, `/`, `:`, `*`, `?`, `"`, `<`, `>`, `|` and iCloud sync silently breaks such files. The Obsidian note filename, the frontmatter `title:` field, and the `--expect-title` audit argument **must use a sanitized title**, never the raw LaTeX one.

Sanitization rules (apply in order):

1. Drop surrounding `$...$` markers but keep the inner content in readable form.
2. Replace common LaTeX commands with their plain ASCII equivalent:
   - `\ell` → `ell`, `\mathcal{X}` → `X`, `\mathbb{R}` → `R`, `\mathbf{x}` → `x`, `\boldsymbol{...}` → strip braces
   - Greek: `\alpha` → `alpha`, `\beta` → `beta`, `\theta` → `theta`, etc. (spelled-out name)
   - `\sqrt{x}` → `sqrt(x)`, `\frac{a}{b}` → `a over b`
   - subscripts `_{ab}` → `_ab`, superscripts `^{ab}` → `^ab`
3. Drop any remaining backslashes.
4. Replace OS-forbidden characters `/ \ : * ? " < > |` with a single space.
5. Collapse multiple spaces, trim.

Example:
- Raw arXiv title: `$\ell_1$-Regularized SGD for $\mathcal{O}(1/\sqrt{T})$ Convergence`
- Sanitized: `ell_1-Regularized SGD for O(1 over sqrt(T)) Convergence`

The sanitized title is canonical for:
- the Obsidian `.md` filename
- the frontmatter `title:` field
- every `[[Literature/...]]` wikilink in `## Related Papers` and in the cards of the Operon Reading board (`Operon/Reading/*.md`)
- the final audit `--expect-title` argument

Keep the **raw LaTeX title** only inside the BibTeX `title = {...}` field. Never put a LaTeX-formula title into a filename.

## Trigger

Use when the user provides:
- An arXiv or AlphaXiv URL and a folder/collection name
- A `paperswithcode.co/papers/{arxiv_id}` URL (HuggingFace-revived Papers with Code) — extract the arXiv ID and fall through to the standard arXiv path; PwC.co uses the arXiv ID as its slug
- "Add this paper", "Ingest this paper", "Создай заметку для этой статьи"
- A batch of arXiv URLs for a collection

## Quality Bar

The note must be detailed enough that the user can understand the paper without opening the PDF. Treat that as a hard quality bar, not a nice-to-have.

High-quality local example for depth and structure:
- `/Users/andrey/Library/Mobile Documents/iCloud~md~obsidian/Documents/shkodnik1917/Literature/PEFT/lora_base/ShadowPEFT: Shadow Network for Parameter-Efficient Fine-Tuning.md`

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

## Zotero Lock Awareness

`paper-ingest` writes to `~/Zotero/zotero.sqlite` via several scripts (`zotero_check_dup.py`, `zotero_attach_pdf.py`, inline SQLite for collection membership). While Zotero desktop is running it holds an exclusive write-lock, and these scripts fail with `sqlite3.OperationalError: database is locked`.

Three execution modes:

1. **Solo invocation, Zotero is running**: the skill MAY quit Zotero itself via `osascript -e 'tell application "Zotero" to quit'`, do its work, and relaunch with `open -a Zotero` at the end. Inform the user.
2. **Batch invocation from a parent skill** (e.g. `want-2-read` fan-out): the parent skill is responsible for Zotero lifecycle. `paper-ingest` MUST NOT quit or relaunch Zotero itself inside the batch — that would race other parallel `paper-ingest` agents. Assume Zotero is already closed when the parent skill says so.
3. **Zotero already closed**: just proceed. Do not relaunch at the end, the parent skill (or the user) will.

Never `kill -9` Zotero. Always use the AppleScript graceful quit. Always verify with `pgrep -lf Zotero` (empty) and `fuser ~/Zotero/zotero.sqlite` (empty) before SQLite writes.

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
7. The paper is mirrored to the matching AlphaXiv folder (Step 7), or the reason it cannot be is stated.
8. The final audit passes.

If any one of these is false, the ingest is incomplete and must be repaired before the workflow is considered done.

## Canonical Happy Path

For arXiv papers, the default happy path is:

1. Extract `ARXIV_ID`.
2. Run duplicate checks in Zotero, SQLite, and Obsidian.
3. Fetch BibTeX and metadata via `bibtex_fetch.py`.
4. Download PDF to `~/Papers/Library/ARXIV_ID.pdf` and extract text; download the LaTeX source bundle for figures; detect the code-repo URL via `extract_repo_url.py` (Step 4c).
5. Create a proper Zotero **parent** item via `connector/saveItems` with `itemType: preprint`.
6. Verify the parent item is not `webpage` and has correct metadata.
7. Ensure the parent item belongs to the intended Zotero collection.
8. Close Zotero if needed and attach the local PDF to that parent via `zotero_attach_pdf.py`.
9. Re-open Zotero if needed and verify the PDF child attachment exists.
10. Write the Obsidian note through the **multi-agent pass** of Step 6, using the parent item key in frontmatter.
11. Enrich the note with Papers with Code metadata via `pwc_fetch.py --inject` (best-effort, skip on 404).
12. Mirror the paper into its AlphaXiv folder (Step 7).
13. Run final audit.

Do not reorder these steps casually. In particular, do not write the final Obsidian note before the Zotero parent item is known-good.

## Zotero MCP is available — prefer it for reads

The `zotero` MCP server (`zotero-mcp-server`, package name matters: **not** `zotero-mcp`) exposes the
library over MCP and is the preferred path for everything read-only, because it does not fight the
SQLite write-lock and does not need Zotero desktop closed:

| Need | MCP tool | Beats |
|---|---|---|
| find an existing item | `mcp__zotero__zotero_search_items`, `zotero_advanced_search` | raw `sqlite3` SELECT |
| find by citation key | `mcp__zotero__zotero_search_by_citation_key` | grep over notes |
| nearest papers in the library | `mcp__zotero__zotero_semantic_search` | folder-name guessing |
| collection tree / keys | `mcp__zotero__zotero_get_collections` | `curl localhost:23119/api/.../collections` |
| create a sub-collection | `mcp__zotero__zotero_create_collection` | manual SQLite insert |
| duplicates in the library | `mcp__zotero__zotero_find_duplicates` | three-way manual check |
| read specific PDF pages | `mcp__zotero__zotero_read_pdf_pages`, `zotero_get_pdf_outline` | full `pdftotext` dump |

The semantic index is passage-level (chunking enabled, cross-encoder reranker on) and refreshes
weekly. If `zotero_semantic_search` returns nothing sensible, check `zotero-mcp db-status` before
concluding the paper is absent.

Writes (creating the parent item, attaching the PDF, fixing collection membership) still go through
the connector API and the direct SQLite path, and those still require Zotero to be closed.

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
grep -rl "ARXIV_ID" "/Users/andrey/Library/Mobile Documents/iCloud~md~obsidian/Documents/shkodnik1917/Literature/" 2>/dev/null
```

If duplicate found anywhere:
- Report the existing item's key, collection, and Obsidian path
- Check whether the Zotero item has `deleted = true` or lives in trash
- If it is in trash, restore it instead of creating a new duplicate
- Ask user whether to skip, update, or force-add
- **NEVER create a duplicate without explicit confirmation**

### Step 2b: Ask the shared lab corpus first

Another member may have ingested this paper already. The shared corpus is checked before any
work is done:

```bash
python3 ~/.claude/skills/paper-ingest/scripts/sync_to_lab.py --arxiv {ARXIV_ID} --verify
```

If it prints a title and a section count, the paper is already in the lab base. That changes two
things.

**Reuse its `citation_key`.** Keys are generated deterministically, so they usually match anyway,
but if the corpus holds a different one, the corpus wins: a divergent key silently splits the same
paper across two `\cite{...}` entries in shared bibliographies.

**Your own vault still gets its own note.** The corpus is shared, the reading is personal, and
another member's note lives in their vault, not yours. Ingest locally as usual.

Duplicates in the corpus are impossible by construction: a paper is matched by `arxiv_id`, `doi`
and `zotero_key` separately, and a match reuses the existing row while accumulating identifiers.
What *is* possible is losing someone's work: sections are replaced wholesale, so pushing your
shorter reading over their fuller one erases theirs from the corpus. `sync_to_lab.py` refuses that
by itself and explains what it found; `--force` overrides it deliberately.

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

### Step 4b: Extract figures and tables (arXiv source preferred)

The note must **embed actual figures** (not text descriptions) and **render tables as native Markdown** (not paraphrase). The cleanest source is the arXiv LaTeX bundle. PDF extraction is the fallback.

Path A — arXiv source bundle (preferred):

```bash
ARXIV_ID="2509.07972"
SRC_DIR="$HOME/Papers/Library/${ARXIV_ID}_src"
mkdir -p "$SRC_DIR"
curl -L -o "${SRC_DIR}.tar.gz" "https://arxiv.org/e-print/${ARXIV_ID}"
# arXiv bundles are usually gzipped tarballs; sometimes a single gzipped .tex
if tar -tzf "${SRC_DIR}.tar.gz" >/dev/null 2>&1; then
  tar -xzf "${SRC_DIR}.tar.gz" -C "$SRC_DIR"
else
  gunzip -c "${SRC_DIR}.tar.gz" > "$SRC_DIR/main.tex"
fi
```

Then prepare the attachments directory in the vault:

```bash
ATTACH_DIR="{VAULT_ROOT}/Literature/{TopLevel}/{collection}/_attachments/${ARXIV_ID}"
mkdir -p "$ATTACH_DIR"
```

Extract pieces:

- **Figures**: parse the main `.tex` for `\includegraphics[...]{<path>}`; copy each referenced `*.pdf`, `*.png`, `*.jpg`, `*.jpeg`, `*.eps` from `$SRC_DIR` into `$ATTACH_DIR`. Preserve the basename so wikilinks stay stable.
- **Tables**: grep for `\begin{table}` ... `\end{table}` blocks in the `.tex`. For each, convert the inner `\begin{tabular}` block to a Markdown table:
  - column count from the `tabular` spec (e.g. `{lcc}` → 3 cols)
  - rows split on `\\`, cells split on `&`
  - strip `\hline`, `\toprule`, `\midrule`, `\bottomrule`
  - keep numeric content verbatim; convert simple `\textbf{x}` → `**x**`
  - capture `\caption{...}` as the line above the table
- **Algorithms**: if the paper has `\begin{algorithm}` blocks, copy them as fenced code blocks inside Section 4 (Математика и формулы) — do not paraphrase.

Path B — PDF fallback (no source bundle, or source disabled on arXiv):

```bash
python3 ~/.claude/skills/paper-ingest/scripts/extract_pdf_figures.py \
  --pdf "$HOME/Papers/Library/${ARXIV_ID}.pdf" \
  --out "$ATTACH_DIR" \
  --vector
```

Two complementary modes inside the script:
- Embedded-image extraction (always on): pulls raster images stored inside the PDF via xref. Lossless, preserves original format. Catches photo-like figures and screenshots.
- `--vector` (recommended for arXiv preprints): finds `Figure N` / `Fig. N` / `Table N` captions and rasterizes the page region attached to each caption (above for figures, below for tables). Catches vector plots that have no embedded raster.

Output naming inside `$ATTACH_DIR`:
- `fig_p{NN}_i{IDX}.{ext}` — embedded raster image
- `fig_p{NN}_figure_{K}.png` — caption-driven figure region
- `tab_p{NN}_table_{K}.png` — caption-driven table region

If both modes return zero artefacts on a given PDF: fall back to textual figure descriptions for that paper and tell the user explicitly.

**Cleanup after Step 5 succeeds:**

```bash
rm -rf "$SRC_DIR" "${SRC_DIR}.tar.gz"
```

The vault `_attachments/${ARXIV_ID}/` stays permanently — it is the only canonical copy of figures used by the note.

### Step 4c: Detect the code-repository URL (script proposes, agent verifies)

The note frontmatter carries an optional `git:` field pointing to the paper's **own** code repository. The script only *proposes* candidates from text already on disk (zero LLM tokens); it never decides the final `git:` on its own. Run it before the `SRC_DIR` cleanup (it needs the LaTeX source):

```bash
python3 ~/.claude/skills/paper-ingest/scripts/extract_repo_url.py \
  --txt "/tmp/paper_${ARXIV_ID}.txt" \
  --src-dir "$SRC_DIR" \
  --json
```

Output: `{"git": "<url-or-empty>", "candidates": ["<url>", ...]}`. The `git` field is only the script's *confidence hint*; `candidates` is the full ranked list. **Treat both as proposals to be verified, not as a final answer.**

**Mandatory verification before writing `git:`.** Never paste a candidate URL into frontmatter unsubstantiated — a wrong repo (a cited baseline, a tokenizer, a dependency) is worse than no link. For the chosen candidate, confirm it is genuinely *this paper's* repository using evidence you already have plus a cheap check:

1. **From the paper text (free — you already read it for the 8 sections):** does the paper present this exact URL as the authors' own code/release (e.g. under the title, in the abstract footnote, in a "Code" / "Reproducibility" statement)? Cited baselines (`karpathy/nanoGPT`, `KellerJordan/Muon`, `Liuhong99/Sophia`, tokenizers, "based on …") are NOT the paper's repo — reject them.
2. **Confirm the repo matches the paper:** the owner/org or repo name should be consistent with the paper (author/lab/group name, paper title, or method name). If it is plausibly the authors' but you are not sure, do one lightweight `WebFetch` of the repo page and check the README/description names this paper (title, arXiv id, or method). Only accept on a match.

Decision after verification:
- Verified as the paper's own repo → write `git: "<url>"` verbatim (collapse to repo root, no `/tree/…`).
- `candidates` present but none verifies as the authors' own → **omit `git:`** (do not guess).
- Script returned empty `git` and empty `candidates` → the paper has no repo → **omit the `git:` line entirely.** Never write `git: ""`.

The LaTeX source is much cleaner than `pdftotext` for URLs (no footnote-number gluing); the script already prefers it when `--src-dir` is given.

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
- the `**Zotero**:` line inside `## Комментарии` of the Operon Reading card

Those fields must always point to the canonical paper parent item.

When the caller is `want-2-read`, the card write-back uses the canonical four-section schema
(`## Заметка`, `## arXiv`, `## Тема`, `## Комментарии`) documented in that skill. `paper-ingest`
supplies the material for it — the sanitized title for the wikilink, the parent Zotero key, the final
folder, and the condensed Russian description — but the parent skill owns the write.

If Zotero is not running: create the Obsidian note without `zotero_key`, leave `zotero_key: "PENDING"` and tell the user.

### Step 6: Write the Obsidian Note (multi-agent)

The note is written by a small crew, not one agent. The pattern follows what the current literature
pipelines converge on: a cheap **recon/routing** stage that decides how the paper can be read at all,
**specialised writers** per section family, and an **adversarial verifier** that checks claims against
the source instead of re-reading its own output.

Target path: `{VAULT_ROOT}/Literature/{TopLevel}/{collection}/{Sanitized Paper Title}.md`

Where `{TopLevel}` is one of: `Optimization`, `PEFT`, `LLM`, `RL`, `Applied`, `Reference`, `_inbox`.

**Vault root:** `/Users/andrey/Library/Mobile Documents/iCloud~md~obsidian/Documents/shkodnik1917/`

**IMPORTANT:** The output file name must be the **sanitized** paper title per the "Title Sanitization" section near the top of this SKILL — no `$`, no `\`, no LaTeX commands. Never shorten the title semantically; only the LaTeX-to-ASCII rewrite is allowed. The same sanitized title also goes into frontmatter `title:`.

#### Frontmatter template

```yaml
---
title: "Paper Title"
zotero_key: "ZOTERO_KEY"
zotero_link: "zotero://select/library/items/ZOTERO_KEY"
url: "https://arxiv.org/abs/ARXIV_ID"
git: "https://github.com/owner/repo"   # OPTIONAL — only if the paper has a code repo; omit the line entirely if none
publication: "VENUE (e.g. NeurIPS 2025, ICLR 2026 (A*)) or Unpublished (arXiv preprint)"
tags:
  - tag1
  - tag2
updated: "DD-MM-YYYY"
---
```

`ZOTERO_KEY` here means the parent paper item key, not the PDF attachment key.

The `git:` field is populated by Step 4c (below). Omit the line entirely when the paper has no code repository — never write an empty `git: ""`.

#### BibTeX section (verbatim from Step 3)

```markdown
## BibTeX

```bibtex
{BIBTEX_FROM_SCRIPT — pasted exactly, no edits}
```
```

#### Step 6a: Recon router (cheap, runs first)

One short agent inspects what is actually on disk before any writing starts, and returns a routing
verdict. This is the stage that prevents a confident-sounding note built on a broken extraction.

It reports:
- `source_mode`: `tex` (LaTeX bundle downloaded and parsed), `pdf_text` (clean `pdftotext` output, no
  source), or `pdf_vision` (text layer is garbage or absent — scanned/figure-only paper)
- `figures_found`, `tables_found`: counts from `$ATTACH_DIR` and from `\begin{table}` blocks
- `theory_weight`: `heavy` (theorems, lemmas, proofs, convergence rates) or `light` (algorithmic or
  empirical paper)
- `blockers`: anything missing — no PDF, no source bundle, zero extracted figures, truncated text

Routing consequences:
- `source_mode: pdf_vision` → tables must be transcribed by reading the rasterised page regions, and
  every number carries a higher error risk; the verifier in Step 6c checks tables cell by cell.
- `theory_weight: heavy` → Sections 3 and 4 go to a stronger model (see the crew table); a haiku pass
  on a theorem-dense paper reliably drops conditions and mis-transcribes bounds.
- `figures_found: 0` → Section 7 falls back to textual descriptions with `*(исходник недоступен)*`
  markers, and this limitation is stated to the user, not hidden.

#### Step 6b: The writing crew

Spawn these agents. Each receives the paper text, the recon verdict, the attachments directory, and
the shared writing rules below. They write **into the same file**, each owning its own sections, so
run them sequentially in this order to avoid write races, or have each return its Markdown block and
assemble once.

| Agent | Model | Owns | Why split out |
|---|---|---|---|
| **Обзорщик** | `claude-haiku-4-5-20251001` | 1. Общий обзор, 2. Посекционный разбор, 5. Новые архитектуры, 6. Методология и данные | narrative sections, cheap and high-volume |
| **Математик** | haiku if `theory_weight: light`, otherwise the session model | 3. Прериквизиты, 4. Математика и формулы | every formula, theorem, and per-variable glossary; the single most error-prone part of the note |
| **Экспериментатор** | `claude-haiku-4-5-20251001` | 7. Графики и таблицы | transcribes tables from the `tex` `tabular` blocks or the rasterised regions verbatim, embeds figures |
| **Критик** | session model | 8. Критическая оценка | must contradict the paper's own framing, so it is deliberately not the agent that wrote the summary |
| **Связист** | session model | `## Related Papers` | uses the library index, see Step 6c |

Model choice is a floor, not a ceiling: if the paper is long or dense, raise it. Never lower the
Математик below the Обзорщик.

#### Step 6c: Related Papers via the library index

Do not guess neighbours from folder names. Query the passage-level index:

```
mcp__zotero__zotero_semantic_search(query="<paper title> <method name> <core mechanism>", limit=10)
```

Keep 1-3 hits that are genuinely connected **methodologically or theoretically**, not merely by topic,
and that already exist as notes under `Literature/`. Format each as
`[[Literature/{TopLevel}/{collection}/{Exact Paper Title}]]` with one sentence naming the connection
(shared assumption, competing estimator, predecessor of the same bound, ablation of the same module).

Verify every wikilink resolves to a real file before writing it. A dangling `[[...]]` is worse than
one fewer related paper.

#### Step 6d: Adversarial verifier

After the crew finishes, one verifier agent runs against **the paper**, not against the note. Its
prompt frames it as trying to *refute* the note:

- pick every numeric claim in Sections 6 and 7 and find it in the source; flag anything that is not there
- pick every formula in Sections 3 and 4 and check the glossary defines each symbol, including indices
  and operators, and that stated conditions (smoothness, convexity, step-size ranges) were not dropped
- check each `![[...]]` embed resolves to a real file in `_attachments/{ARXIV_ID}/`
- check each `[[Literature/...]]` in Related Papers resolves to a real note
- check the note answers all nine questions from the Quality Bar above without reopening the PDF
- check the prose is strong Russian without mixed-language fragments

The verifier **fixes what it finds, inline**. It does not re-run the writers and it does not merely
report. If it cannot verify a number against the source, it removes the number rather than keeping an
unsupported one.

#### Shared writing rules (given to every writing agent)

```
You are writing a paper analysis card for an Obsidian research library.
Read the full paper text provided below and write your assigned sections in Russian.

OUTPUT FILE: {ABSOLUTE_PATH_TO_MD_FILE}
ATTACHMENTS DIR (relative to vault root):
  Literature/{TopLevel}/{collection}/_attachments/{ARXIV_ID}/

HIGH-QUALITY LOCAL EXAMPLE:
/Users/andrey/Library/Mobile Documents/iCloud~md~obsidian/Documents/shkodnik1917/Literature/PEFT/lora_base/ShadowPEFT: Shadow Network for Parameter-Efficient Fine-Tuning.md

WRITING RULES:
- Russian prose must be the default. Use English only in narrow cases:
- when introducing a technical term after its Russian explanation in parentheses
- for standard names of models, datasets, methods, modules, metrics, and item titles
- inside formulas, code, BibTeX, file paths, and Zotero/Obsidian identifiers
- if a direct Russian replacement would be misleading or clearly unnatural
- Do not switch into English sentence fragments when a normal Russian sentence is possible
- LaTeX for ALL formulas: inline $x$, display $$\mathcal{L} = \ldots$$
- Explain EVERY variable on first appearance with a one-line definition. No exceptions. This includes indices ($i$, $t$, $k$), set notation ($\mathcal{D}$, $\mathcal{B}$), and operator symbols ($\nabla$, $\mathbb{E}$, $\|\cdot\|$). If a variable also appears with subscript/superscript variants, explain the variants too.
- For each major equation: write the formula, then a bulleted variable glossary directly under it. Do not dump 5 formulas in a row without glossaries.
- NO em dashes, NO semicolons, NO promotional language, NO AI filler
- Write with enough depth that the user can understand the paper without opening the PDF
- Do not compress the paper into a shallow summary. Prefer concrete mechanisms, assumptions, equations, ablations, failure modes, and exact claims
- If the paper has a nontrivial algorithm or pipeline, explain it step by step in plain Russian
- If the paper has important limitations or hidden assumptions, make them explicit rather than vague
- Section 3 (Прериквизиты) MUST cover the math background a reader with only ML+LLM basics needs to follow the paper. Reconstruct definitions even when the paper omits them. See section spec below.
- Section 4 MUST include EVERY formula and EVERY theorem/lemma/proposition from the paper — not just "major" ones. For each: write the full LaTeX, then a bulleted glossary for every symbol.
- Section 7 must embed actual figures from `_attachments/{ARXIV_ID}/` and render tables as native Markdown. Include exact numbers from the originals.
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

### 3. Прериквизиты
**Large section.** Strict mathematical background a reader who knows only ML and LLM-training basics (SGD, cross-entropy, transformer block, attention, LayerNorm, residual, basic backprop) needs to fully understand the paper. Everything beyond that base that the paper uses or assumes must be defined here, even if the paper itself skips the definition.

Mandatory coverage:
- **Math objects, operators, norms** actually used in the paper: $\ell_p$-norms, operator/spectral norm, Frobenius norm, kernel/image of a matrix, projectors, SVD, eigendecomposition, Schatten norms, trace/determinant — define formally with LaTeX and explain every symbol.
- **Algorithms / methods the paper builds on**: LoRA, Adam/AdamW, momentum, KL-divergence, REINFORCE, PPO, DPO, RLHF, sparse coding, mirror descent, proximal operators, etc. Give the formal update rule with LaTeX and a one-line per-variable glossary.
- **Theoretical concepts the paper invokes but does not define**: smoothness, $\mu$-strong convexity, Lipschitz continuity, stochastic approximation, supermartingale, concentration inequalities (Hoeffding, Bernstein), bias/variance of an estimator, mixing time, etc. Give the definition with conditions and the property the paper actually uses.
- **The paper's own notation conventions**: what $\theta$, $W$, $x$, $y$, $\nabla$, $\mathbb{E}$, $\mathbb{P}$, $\mathcal{D}$, $\mathcal{B}$ mean in this paper specifically (dimensions, batch index, parameter set, dataset, distribution, etc.).

Format: each item is its own `####` subsection with:
1. A formal LaTeX definition.
2. A bulleted per-variable glossary.
3. One sentence on why this object/method/concept matters in the paper.

These formulas are **not required to appear in the paper**. Reconstruct the minimal-but-complete background so that Section 4 (Математика и формулы) can be read without external lookups.

No filler intro like «прежде чем перейти к методу». Definitions directly. No water.

### 4. Математика и формулы
Every key formula and every theorem/lemma/proposition with LaTeX. Under each: a bulleted glossary defining every variable, including indices and operators. If the paper's contribution is algorithmic rather than theorem-heavy, explain step by step how the equations drive the method.

### 5. Новые архитектуры
Forward pass + loss function if applicable. If there is no new architecture, say so directly and explain what is new instead: optimizer, routing, system design, training policy, evaluation method, or theory.

### 6. Методология и данные
Datasets, models, training setup, evaluation metrics, baselines, important ablations, and implementation details that affect interpretation. If deployment settings or inference modes matter, include them here too.

### 7. Графики и таблицы
**Embed actual figures and render actual tables, not text descriptions.**

For each key figure:
```
![[Literature/{TopLevel}/{collection}/_attachments/{ARXIV_ID}/<figure_basename>.<ext>]]
*Figure N (caption from the paper).* 1–2 фразы: что сравнивается, какая метрика, тренд, числовой диапазон.
```

For each key table: render it as a native Markdown table with the same headers and the same numbers as in the paper (sourced from the `tex` `\begin{tabular}` block when available). Under the table: one-line takeaway naming the compared methods, the metric, and the strongest result. Bold the winning row/cell with `**...**`.

For training curves and ablation plots: embed the figure **and** describe the trend (which method dominates, by what numeric margin, at what step/epoch).

Never write «figure shows improvement» without naming the compared methods, the metric, and at least the most important numerical values.

If a figure's source is unavailable: keep a textual description and add `*(исходник недоступен)*` so the auditor can flag it.

Paths to embedded files must be vault-relative wikilinks `![[Literature/...]]`, never absolute filesystem paths.

### 8. Критическая оценка
Strengths. Numbered list of limitations (be specific, not generic). Distinguish between conceptual value, empirical strength, engineering complexity, and unresolved questions.

The final card must be useful as a standalone reading substitute for first-pass understanding. If a smart reader could not explain the paper's mechanism, setup, main numbers, and limitations after reading the note, the note is not detailed enough.

## Related Papers
Written by the Связист agent from the semantic-search hits of Step 6c, not guessed from folder contents.
Format: `[[Literature/{TopLevel}/{collection}/{Exact Paper Title}]]` — one sentence explaining the connection.
Focus on methodological or theoretical connections, not just topic overlap.

PAPER TEXT:
{FULL_TEXT_FROM_PDF}
```

After the crew and the verifier finish, the main model must check the assembled file itself:
1. All 8 sections present (1. Общий обзор, 2. Посекционный разбор, 3. Прериквизиты, 4. Математика и формулы, 5. Новые архитектуры, 6. Методология и данные, 7. Графики и таблицы, 8. Критическая оценка)
2. Section 3 is substantial (not a stub) and covers at least 3 background items with formal definitions + glossaries
3. Section 7 contains at least one `![[Literature/.../_attachments/...]]` embed OR an explicit `*(исходник недоступен)*` marker per figure
4. Each major formula in Sections 3 and 4 is followed by a per-variable glossary (not just the formula alone)
5. `## Related Papers` exists with at least 1 WikiLink, and every WikiLink resolves to a real file
6. Frontmatter is complete (no `PENDING` fields left unresolved)
7. Filename and frontmatter `title:` match the sanitized title (no `$`, no `\`)
8. No section boundary was clobbered by a second agent writing over the same region
9. If anything is missing or malformed, fix it inline — do not re-run the crew for a formatting slip

### Step 6e: Enrich with Papers with Code (best-effort)

After the Obsidian note exists, enrich it with `paperswithcode.co` metadata via the JSON API. This is a **best-effort** step — PwC.co does not have every paper, the API is undocumented, so any failure is silently skipped and the pipeline continues.

```bash
python3 ~/.claude/skills/paper-ingest/scripts/pwc_fetch.py \
  --arxiv ARXIV_ID \
  --inject "{ABSOLUTE_PATH_TO_NOTE.md}"
```

What the injector does (two parts):

1. **Frontmatter patch** — appends/replaces these YAML keys in the note's frontmatter (next to `url`, `publication`, `tags`, etc.):
   - `pwc_url: "https://paperswithcode.co/papers/{arxiv_id}"`
   - `citations: <int>` (from Semantic Scholar)
   - `citations_updated: "YYYY-MM-DD"`
   - `pwc_tasks: [<task names>]` (only when PwC has tagged any tasks)
2. **Body callout** — places a single standalone Obsidian callout between `## BibTeX` and `## AI Explanation`, with **no `##` section header**:

   ```markdown
   > [!abstract] TL;DR (Papers with Code)
   > {tldr written by PwC}
   >
   > **Methods used**: Adam (2014); BERT (2018); BPE (2015); ...
   ```

Both operations are **idempotent**: re-running on the same note replaces the existing keys and callout in place, never duplicates. A legacy `## Papers with Code` section from older versions of this skill is detected and removed on first re-run.

Design rationale (do not regress):
- `pwc_url`, `citations`, `citations_updated`, `pwc_tasks` live in **frontmatter**, not body, so Obsidian's metadata pane / Dataview can use them and they sit next to `url:`/`publication:` where they belong.
- The PwC `published` date is **dropped** — `publication:` already encodes the venue/year and the BibTeX block carries the exact date.
- The body callout contains **only** TL;DR + Methods used, joined by a `>` blank line. Methods are plain text separated by `; ` (no links, no per-method wikilinks). The PwC-internal method-graph backlinks were tried earlier but resolved to wrong targets in practice, so they were dropped.

Hard rules for this step:
- This step **does NOT** replace `bibtex_fetch.py`. PwC is never the BibTeX source; the citation_key still comes from arXiv/Semantic Scholar via the existing flow, and the `citation-validator.py` hook still enforces it.
- This step **does NOT** modify any other section of the note. The `## AI Explanation`, `## BibTeX`, and `## Related Papers` blocks remain untouched.
- This step **does NOT** create a `## Papers with Code` heading. The body change is exactly one `[!abstract]` callout.
- If `pwc_fetch.py` reports `"found": false`, treat the paper as not in PwC and move on — do not retry forever, do not fall back to HTML scraping (the site is a SPA).
- The cache directory `~/.cache/pwc/` is the source of truth for repeated runs — clear it manually if you want a fresh fetch.

### Step 7: Mirror the paper to AlphaXiv

**Mandatory.** Local Obsidian is master, the AlphaXiv account mirrors it, and per
`~/.claude/rules/alphaxiv-sync.md` the mirror write happens in the **same run** as the local write.
Skipping it is how the two libraries drift.

Read `~/.claude/alphaxiv-library-map.json`, resolve `Literature/{TopLevel}/{collection}` to its
`folder_id`, then:

```
mcp__claude_ai_alphaXiv__save_papers_to_folder(
    folder_id=<mapped folder_id>, paper_ids_or_urls=[ARXIV_ID])
```

Variants:
- The paper is currently in the AlphaXiv **"Want to read"** folder (typical when the caller is
  `want-2-read`): use `move_papers_between_folders(from=<want_to_read_folder_id>, to=<folder_id>)`
  instead, so it lands in the topic folder and leaves the queue atomically.
- **Batch invocation from `want-2-read`**: the parent skill owns the mirror write and does it in its
  own Step 6. Do not call the MCP here as well — a double write is harmless but a double *move* is not.
- Several destination folders: repeat `save_papers_to_folder` for each. A paper may live in many folders.
- A folder that does not exist on AlphaXiv yet: `create_folder` nested under the mapped top-level
  parent, then **add its id to `~/.claude/alphaxiv-library-map.json`**. A missing map entry silently
  breaks every later sync.
- A stale `folder_id` (the call errors): refresh via `list_library` and update the map file.
- **No arXiv ID** (ICML-poster-only, book, blog digest, private PDF): the MCP can only add arXiv
  papers — there is no upload tool. File the paper locally, skip this step, and tell the user they can
  upload the PDF manually as a Private Paper on alphaxiv.org. Never invent an arXiv ID to satisfy this step.
- The AlphaXiv MCP is not connected: finish the local work, then tell the user the mirror was skipped
  and needs `/mcp` auth. Do not drop it silently.

Never touch the `My publications` or `Private Papers` system folders.

### Step 7b: Push the paper into the lab library corpus

The same note that lands in the vault also belongs in the shared `library` corpus of the Lab
Knowledge MCP, where it becomes searchable next to the laboratory's own hypotheses. Skipping this
leaves the corpus behind the vault, exactly the way the AlphaXiv mirror used to drift.

```bash
python3 ~/.claude/skills/paper-ingest/scripts/sync_to_lab.py --arxiv {ARXIV_ID} --verify
```

The wrapper exists because the two halves of the job live on different machines. Parsing needs the
vault and Zotero, which are here. Pushing needs the `mcp` package, which is installed in the
server's environment and absent from the Mac's system Python, so calling `push_library.py` here
fails with `ModuleNotFoundError`. The wrapper parses locally, copies the manifest and pushes there.

Do not filter the parser by arXiv id with its own `--only`: that flag matches the note **path**,
which never contains the id, so the filter selects nothing and the step silently pushes an empty
manifest. The wrapper filters on the parsed `arxiv_id` instead.

`--verify` asks the base afterwards whether the paper is really there, by title and section count.
The exit code of the push says only that the call went through, and this step is exactly where a
silent no-op used to hide.

The research theme of the paper is derived on the server from its `library_folder`, so a paper
filed into a known folder is immediately visible from the theme it belongs to, next to the
laboratory's own hypotheses on the same area. Nothing to pass here. When the paper goes into a
**new** folder, add that folder to `services/lab-knowledge/src/lab_knowledge/library_themes.py`,
otherwise the paper falls back to the theme of its top-level section, which is coarser than it
deserves. A folder that fits no existing theme is a signal to propose a new theme to the owner,
not to invent one.

Repeating this is safe: the paper is matched by its natural key and updated, and its sections are
replaced rather than appended. Sources already pointing at the same arXiv id get attached to it
automatically, so a hypothesis that cites this paper starts showing the link with no extra step.

If the Lab Knowledge MCP is unreachable, finish the local work and tell the user the library push
was skipped. Do not drop it silently.

The sync is one-way and strict: **everything in the personal library must exist in the shared
corpus**. The reverse does not hold — other members will add their own papers there, and those do
not belong in this vault. A full reconciliation is one command and is idempotent:

```bash
python3 ~/.claude/skills/paper-ingest/scripts/sync_to_lab.py --all
```

### Step 8: Mandatory Final Audit

**This step is required. Do not finish the add-paper workflow without it.**

The audit has three parts: **A. Zotero/Obsidian sync audit**, **B. Strict BibTeX audit** and **C. Lab corpus audit**. All three must pass.

#### A. Zotero/Obsidian sync audit

Run the Python checker again at the end of the pipeline:

```bash
python3 ~/.claude/skills/paper-ingest/scripts/zotero_check_dup.py \
  --collection COLLECTION_NAME \
  --final-audit \
  --expect-title "SANITIZED PAPER TITLE" \
  --expect-zotero-key ZOTERO_KEY
```

This final audit must algorithmically verify:
- the article exists in Zotero in the expected collection
- the Zotero parent item is a real paper item, not `webpage`
- the Zotero parent item title matches the paper title (raw title is fine here, Zotero is allowed to keep the original LaTeX-rich title)
- the Zotero parent item has authors/creators populated
- the article exists in Obsidian in `Literature/COLLECTION_NAME/` under the **sanitized** filename
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

#### B. Strict BibTeX audit (per note)

When ingesting **a batch of papers**, the verifier agent must give the BibTeX block extra-thorough scrutiny — it is the most error-prone artifact in the pipeline and one bad BibTeX entry quietly poisons every future `\cite{...}` that uses the citation key.

Run for each newly created Obsidian note:

```bash
python3 - <<'PY'
import re, sys, pathlib, datetime
try:
    import bibtexparser
except ImportError:
    sys.exit("install bibtexparser: pip install bibtexparser")

NOTE = pathlib.Path("ABSOLUTE_PATH_TO_NOTE.md")
ARXIV_ID = "ARXIV_ID_OR_EMPTY"
text = NOTE.read_text()

blocks = re.findall(r"```bibtex\s*\n(.*?)```", text, re.S)
assert len(blocks) == 1, f"expected exactly 1 bibtex block, got {len(blocks)}"
raw = blocks[0]

assert "[BibTeX pending]" not in raw and "TODO" not in raw and "???" not in raw and "<FILL" not in raw, \
    "placeholder string left inside bibtex"

db = bibtexparser.loads(raw)
assert len(db.entries) == 1, f"expected 1 entry, got {len(db.entries)}"
e = db.entries[0]

for f in ("title", "author", "year"):
    assert e.get(f, "").strip(), f"missing required field: {f}"

cy = datetime.date.today().year
year = int(re.findall(r"\d{4}", e["year"])[0])
assert 1990 <= year <= cy + 1, f"year out of plausible range: {year}"

ck = e.get("ID", "")
assert re.match(r"^[a-z]+\d{4}[a-z][a-z0-9]*$", ck), \
    f"citation_key '{ck}' does not match {{lastname}}{{year}}{{firstword}} pattern"

assert " and " in e["author"] or "," in e["author"], \
    "author field is not in BibTeX-canonical 'Surname, Firstname [and ...]' form"

itype = e.get("ENTRYTYPE", "")
if itype in ("article", "journalArticle"):
    assert e.get("journal"), "@article missing 'journal'"
elif itype == "inproceedings":
    assert e.get("booktitle"), "@inproceedings missing 'booktitle'"
elif itype == "misc" and ARXIV_ID:
    assert e.get("eprint") == ARXIV_ID, f"eprint mismatch: {e.get('eprint')} vs {ARXIV_ID}"
    assert "arxiv" in e.get("archivePrefix", "").lower() or "arxiv" in raw.lower(), \
        "arXiv preprint missing archivePrefix=arXiv"

for field, val in e.items():
    assert "\\%" not in val and "&amp;" not in val, f"URL-encoded artefact in '{field}': {val}"

print("BibTeX audit OK:", ck)
PY
```

The strict audit verifies, for each note:

1. Exactly one ` ```bibtex ... ``` ` block in the file (no leftover duplicates from earlier ingest attempts).
2. BibTeX is parseable by `bibtexparser`.
3. Required fields `title`, `author`, `year` are present and non-empty.
4. `year` is an integer in `[1990, currentYear+1]`.
5. `citation_key` matches `{lastname}{year}{firstword}` regex (e.g. `vaswani2017attention`).
6. `author` is BibTeX-canonical: `Surname, Firstname [and Surname, Firstname ...]`.
7. Required fields per entry type are present: `@article` → `journal`, `@inproceedings` → `booktitle`, `@misc` arXiv → `eprint` matching the arXiv ID + `archivePrefix=arXiv`.
8. No placeholder strings (`[BibTeX pending]`, `TODO`, `???`, `<FILL...`) remain anywhere in the block.
9. No URL-encoded artefacts (`\%`, `&amp;`) inside fields.
10. The sanitized note `title:` and the BibTeX `title = {...}` describe the same paper (string match modulo LaTeX-to-ASCII sanitization).

If any BibTeX check fails: **stop**, report the exact field and value, do not silently rewrite the BibTeX (the LLM-never-edits-BibTeX rule still holds). Try the normalization scripts first:

```bash
python3 ~/.claude/skills/paper-ingest/scripts/normalize_markdown_bibtex_authors.py
python3 ~/.claude/skills/paper-ingest/scripts/normalize_markdown_bibtex_structure.py
python3 ~/.claude/skills/paper-ingest/scripts/remove_editor_field_from_markdown_bibtex.py
```

If the structural problem persists, re-run `bibtex_fetch.py` from the original source.

#### C. Lab corpus audit

The paper must be present in the shared `library` corpus, not merely pushed to it:

```bash
python3 ~/.claude/skills/paper-ingest/scripts/sync_to_lab.py --arxiv {ARXIV_ID} --verify
```

The check must print the paper's title and a non-zero section count. Zero sections means the note
was parsed but its reading is empty, and an empty paper answers no question — treat it as a
failure, not as a pass.

A silent no-op is the failure mode this part exists for. The push reports success whenever the call
goes through, so without asking the base afterwards a paper filtered out by a wrong flag looks
exactly like a paper that was written.

The whole add-paper workflow is considered successful only when **A, B and C pass for every note
created in this batch**.

## Paths and Config

| Item | Path |
|------|------|
| PDF library | `~/Papers/Library/` |
| Obsidian vault | `/Users/andrey/Library/Mobile Documents/iCloud~md~obsidian/Documents/shkodnik1917/` |
| Literature base | `{vault}/Literature/` |
| Zotero DB | `~/Zotero/zotero.sqlite` |
| Zotero local API | `http://localhost:23119` |
| BibTeX script | `~/.claude/skills/paper-ingest/scripts/bibtex_fetch.py` |
| Duplicate check | `~/.claude/skills/paper-ingest/scripts/zotero_check_dup.py` |
| PDF attach script | `~/.claude/skills/paper-ingest/scripts/zotero_attach_pdf.py` |
| Papers with Code enrichment | `~/.claude/skills/paper-ingest/scripts/pwc_fetch.py` |
| PwC API cache | `~/.cache/pwc/{arxiv_id}.json` |
| PDF extraction | `export PATH=/opt/homebrew/bin:$PATH && pdftotext` |
| Writing crew | Обзорщик + Экспериментатор on `claude-haiku-4-5-20251001`; Математик and Критик on the session model (see Step 6b) |

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

The library now has 2 levels: `Literature/{TopLevel}/{collection}/`

### Top-level parents (Zotero)

| Top-level | Zotero parent key |
|-----------|-------------------|
| Optimization | `DXJ7V8BA` |
| PEFT | `FRFQF6NN` |
| LLM | `WMWGRSXT` |
| RL | `4M8Z9Z4J` |
| Applied | `F98XUP8X` |
| Reference | `DFJP62BT` |

### Sub-collections with known API keys

| Path | Zotero key |
|------|-----------|
| Optimization/warmup | `8936AUN8` |
| Optimization/sgn | `Z3GI6J4U` |
| PEFT/lora_style | `TB47AA4G` |
| LLM/token_reweighting_llm | `9257ABB9` |
| RL/fedback_loop | `QU37FGFG` |

For all other sub-collections: Zotero keys are local-only. Use Zotero local API (`http://localhost:23119`) to get the key, or create a new child collection via `mcp__zotero__zotero_create_collection(name=..., parent_key=PARENT_KEY)`.

When creating a new sub-collection, always pass the parent_key from the table above so it nests correctly.

For a completely new top-level category: propose to the user first, then create a new parent collection and add it to this table.

## Error Handling

| Error | Action |
|-------|--------|
| Zotero not running (batch mode) | Expected state during `want-2-read` batches; proceed with direct SQLite writes |
| Zotero not running (solo mode, by user) | Create Obsidian note with `zotero_key: "PENDING"`, tell user |
| `saveSnapshot` produced `webpage` item | Create a fresh proper paper item via `saveItems`, fix collection membership, trash the broken `webpage` item, and only then continue |
| Obsidian note points to attachment key | Rewrite `zotero_key` and `zotero_link` to the parent paper item key and keep the attachment only as child PDF |
| PDF download fails | Try `export.arxiv.org/pdf/`, then ask user |
| BibTeX fetch fails | Report error, do NOT use LLM-generated BibTeX, offer to retry |
| PwC enrichment 404 / network error | Skip Step 6e silently; the note is left untouched and the pipeline continues |
| Local PDF not in Zotero yet | Stop, ingest the PDF into Zotero first |
| pdftotext not found | `export PATH=/opt/homebrew/bin:$PATH` then retry |
| Obsidian file exists | Read it, offer to update (overwrite only the AI Explanation) |
| a writing agent writes the wrong filename | Read the wrong file, Write its content to the correct sanitized path, delete the wrong file |
