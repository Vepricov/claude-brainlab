# Unified Agent Rules

## Core
- The user is an LLM researcher who mostly works in existing repos, research code, and third-party libraries. Do not assume greenfield work.
- Be concise. No filler. If uncertain, say so. If a task is ambiguous, ask one focused question.
- Respond in the user's language unless asked otherwise. Use English for code, commands, file names, formulas, comments, and technical terms unless the user explicitly asks otherwise. Academic prose defaults to English.

## Memory And Tools
- On the first substantial turn, load context with `project_context` or MemPalace search.
- Before answering about past decisions, experiments, bugs, prior work, or project history, search MemPalace first.
- Prefer `project_context`, `memory_search`, `memory_save`, and `memory_diary` when available.
- For web search or URLs, use `web-search-prime_web_search_prime` and/or `web-reader_webReader`, not model memory.
- Save important findings, quotes, decisions, and durable code context to project memory. Write a diary entry after meaningful tasks.
- Load and use a matching skill whenever one clearly applies.
- Prefer a project wing when available. The legacy archive wing is `conversations`.

## Changes
- Read and understand relevant code first. Explain your understanding in 2 to 3 sentences before changing it.
- If a change touches more than 3 files or has architectural impact, outline the plan and wait for confirmation.
- Do not refactor outside scope or add new dependencies without asking.
- Match surrounding style exactly and preserve the existing architecture.
- After changes, say exactly what changed and why. State uncertainty explicitly.

## Writing
- Write formulas in LaTeX, using inline $x$ and display $$\mathcal{L} = \ldots$$ when appropriate.
- When the user asks to write, rewrite, edit, polish, or humanize prose, use `writing-anti-ai` when available. Apply the same constraints automatically to `.tex` writing.
- In new academic prose: no em dashes, no semicolons, no `\emph{}`, `\textbf{}`, or `\textit{}` unless requested, no promotional phrasing, and avoid AI filler, inflated AI vocabulary, and formulaic discourse linkers unless they are genuinely needed.
- When reading a paper or article, first look for local `.tex` sources before using PDFs or external extraction.

## Obsidian And Local Workflow
- Obsidian vault root: `${OBSIDIAN_VAULT}/`.
- **When the user says "create/make/write an md file" or "md файл", ALWAYS write it to Obsidian (correct vault path), not to the local filesystem — unless the user explicitly says otherwise.**
- Treat `.md` files as Obsidian project files by default unless the user explicitly says otherwise.
- Prefer filesystem-first workflows. Do not require Obsidian MCP when direct file work is enough.
- Maintain durable notes only when the task materially changes research state. Use `~/.claude/obsidian-projects.json` when you need project-to-vault routing.
- In human-facing Obsidian notes, use `DD-MM-YYYY` for dates by default.
- Check `${OBSIDIAN_VAULT}/general/servers.md` before choosing remote GPU indices, and update it when server configuration changes.

### HARD ROUTING RULE (applies to ALL agents, ALL sessions)
- When the user asks to create, make, write, or update a `.md` file, the default destination is Obsidian, not the local repository, unless the user explicitly says otherwise.
- Project notes MUST be routed by the project's filesystem location. NEVER write to `Research/`.
- Mapping (authoritative source: `~/.claude/obsidian-projects.json`):
  - Project in `~/Papers/<slug>/`  → vault `Papers/<slug>/`
  - Project in `~/Projects/<slug>/` → vault `Projects/<slug>/`
  - Project in `~/Staff/<slug>/`    → vault `Staff/<slug>/`
- Before writing a note, resolve the target path via `obsidian-projects.json` (look up the `fs` root matching the project's location, then use the mapped `obsidian` root + slug). Do not rely on per-project `.claude/CLAUDE.md` alone and do not guess.

## Shell And Completion
- If a command needs `brew` and Homebrew is not on `PATH`, use `export PATH=/opt/homebrew/bin:$PATH` first.
- End meaningful tasks with a short operational summary: what changed, which files changed, current status, and natural next steps.

## Literature & Citation Rules

### Finding citations (applies to all agents, all sessions)

Before citing any paper in Related Work, background, or inline references:
1. Search the current Obsidian library and the current project card.
2. If found: use the exact `citation_key` from that paper's `## BibTeX` block and the exact Obsidian link that already exists in the library.
3. If not found → follow the **Add & Classify** workflow below.

### Library structure

The literature hierarchy is not fixed. Agents must inspect the current `Literature/` directory tree and infer the active top-level and subfolder structure at run time.

### Add & Classify workflow (when paper not in library)

1. Search arXiv for the paper; get its arXiv ID.
2. Run `paper-ingest` skill → add to `_inbox/{temp_collection}` (create dated folder).
3. Report: "Добавил [[Literature/_inbox/.../Title]] → предлагаю переместить в `{dynamic-target-folder}`. Подтверди?"
4. Wait for user confirmation. After confirmation: move Obsidian file + Zotero item to target collection.
5. Only cite from the confirmed final location.

### Citation key format

Always take `citation_key` from the paper's `.md` BibTeX block. Never invent keys. Format: `{lastname}{year}{firstword}` (generated by `bibtex_fetch.py`).

### New collection creation

If found papers don't fit any existing current collection: propose a new collection name, explain why it does not fit current folders, then wait for user approval before creating it in both Obsidian and Zotero.

### Hard-link rule

If the same paper must exist in multiple Obsidian folders, create a hard link to the canonical note. Do not keep two independent copies and do not use symlinks.
