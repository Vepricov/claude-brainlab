# Skills catalog

Detailed reference for every skill shipped in this config (`skills/`). For the mental
model of *what a skill is* and *how progressive disclosure works*, see the seminar
handbook (`docs/seminar/handbook/04-skills.md` in the Obsidian vault).

**How to read this:** a skill is a folder with a `SKILL.md`. Only its one-line
`description` sits in the model's context at all times; the body is loaded on demand
when the description matches the task. So the description's *triggers* decide whether a
skill fires. Each entry below gives **what it does** and **when it fires**.

**Legend:** ⭐ = flagship skill unique to this fork · ◇ = adapted/vendored from upstream
(`claude-scholar`, Anthropic document-skills, `kepano/obsidian-skills`, community). See
[Credits in the README](README.md#credits).

---

## A. Literature pipeline (arXiv → Zotero → Obsidian)

The core research loop: get a paper into your library with a real, audited note.

- **`paper-ingest`** ⭐ — End-to-end ingestion of a single paper. Give it an arXiv or
  AlphaXiv URL: it fetches BibTeX from an external API (never LLM-generated), downloads
  the PDF, extracts figures/tables from the TeX source, creates a Zotero parent item
  with a PDF child attachment, prevents duplicates, and writes an unusually detailed
  Obsidian note with an 8-section AI Explanation (including Prerequisites) authored by
  Haiku, ending with a strict BibTeX audit. *Fires on:* an arXiv/AlphaXiv link + "сделай
  заметку / ingest this paper".
- **`want-2-read`** ⭐ — Batch version. Processes a `want_2_read.md` reading queue: one
  fan-out agent per paper, each invoking `paper-ingest`, then a final review agent for
  quality control, and rewrites the queue with final wiki-links, Zotero links, and
  descriptions. *Fires on:* "process my reading list / want-2-read".
- **`paper-search`** ⭐ — Library-aware arXiv shortlist. Scans for fresh papers on your
  topics and writes a shortlist into the Obsidian literature inbox, skipping anything
  already ingested. *Fires on:* "найди свежие статьи по теме / scan for new papers".
- **`zotero-obsidian-bridge`** — Turns papers already in Zotero into detailed reading
  notes inside the bound Obsidian project, checks collection-wide note coverage, and
  builds a connected knowledge map. *Fires on:* "papers are in Zotero, write notes".
- **`obsidian-literature-workflow`** — Filesystem-first literature review when notes
  live inside an Obsidian project KB: agent-first Zotero ingestion, `Papers/` + `Knowledge/`
  synthesis, collection normalization, default literature canvas, no Obsidian MCP needed.
- **`citation-verification`** — Reference guidance (not an action skill): principles and
  common error patterns for verifying citations. Supports `ml-paper-writing`. *Fires on:*
  "how to verify references / citation best practices".
- **`pdf-reader`** ◇ — Extracts structured text from a PDF via PyMuPDF (pypdf fallback).
  *Fires on:* "read this PDF / what's in this PDF" + a path.
- **`kaggle-learner`** ◇ — Access to extracted knowledge from winning Kaggle solutions
  (NLP, CV, time series, tabular, multimodal). *Fires on:* "learn from Kaggle" + a URL.

## B. Paper writing & review

- **`ml-paper-writing`** ⭐ — Write publication-ready ML/AI papers for NeurIPS/ICML/ICLR/
  ACL/AAAI/COLM. Drafting from a research repo, literature review, related-work search,
  citation verification, and camera-ready prep. Ships LaTeX templates and citation
  workflows. *Fires on:* "draft a paper / write the related work / camera-ready".
- **`astar-paper-review`** ⭐ — Write a peer review at the standard of a strong reviewer
  at a top venue. Runs a thorough reviewer + a theoretician (appendix/proofs) + a
  literature-scout (related work, uncited papers) + an experiments-auditor (numbers,
  hyperparameter search, released code), extracts your own PDF annotations, surfaces a
  weakness skeleton in chat first, then writes one review file per paper in the
  Summary / Strengths-Weaknesses / Questions / Limitations format. Handles prompt
  injection inside PDFs safely. Venue-agnostic. *Fires on:* "напиши ревью / review this
  paper" or a handed PDF.
- **`paper-self-review`** — QA checklist for your own paper before submission:
  completeness, structure, quality. *Fires on:* "self-review before submission".
- **`review-response`** — Systematic rebuttal workflow: analyze reviewer comments →
  professional response. *Fires on:* "write rebuttal / respond to reviewers".
- **`research-ideation`** — Research startup: brainstorm ideas, 5W1H, gap analysis,
  question definition, method selection, planning. *Fires on:* "brainstorm research
  ideas / gap analysis / start a research project".
- **`latex-conference-template-organizer`** — Turn a messy conference template `.zip`
  into a clean Overleaf-ready structure. *Fires on:* "organize LaTeX template".

## C. Experiments & results

- **`obsidian-experiment-log`** ⭐ — Note structure *and* operational workflow for ML
  runs: design, ablations, baselines, metrics, failures, plus launching/monitoring/
  post-mortem of multi-hour runs on shared servers. *Fires on:* experiment design or
  result-interpretation discussion.
- **`results-analysis`** — Strict statistical analysis + real scientific figures:
  significance, model comparison, ablations. Produces analysis bundles, not prose.
  *Fires on:* "analyze experimental results / check significance".
- **`results-report`** — Turn completed experiment artifacts into a structured,
  decision-oriented report (assumes `results-analysis` ran first). *Fires on:* "write an
  experiment report / retrospection".

## D. Presentation & promotion

- **`presentation`** ⭐ — LaTeX Beamer slides for theory/maths/conference talks. Enforces
  one mathematical chain (each formula motivated by the previous slide), stable notation,
  Russian prose by default, and treats overflow/heavy shrink as errors. Ships a built-in
  **terminal style** (dark, monospace, bright-green accent). *Fires on:* "make slides /
  rewrite this deck / use terminal style".
- **`post-acceptance`** — Conference-prep workflow after acceptance: Beamer talk, poster,
  promo content; routes terminal-style requests to the same canonical example as
  `presentation`. *Fires on:* "prepare conference presentation / make a poster".
- **`paper-to-social`** ⭐ — Turn a paper into copy-paste-ready social posts (Telegram,
  Twitter/X, Habr), with figures pulled from the arXiv version, in your own voice (never
  AI-sounding). *Fires on:* "сделай пост по статье / тред по статье / promote this paper".

## E. Obsidian knowledge base & project setup

- **`new-paper`** ⭐ — Track a new idea/paper project in Obsidian (hub card + people
  cards) without creating a filesystem folder. *Fires on:* "new paper / new idea".
- **`create-project`** ⭐ — Full project setup: `~/Papers/<slug>/` with `.claude/CLAUDE.md`
  (SSH servers, code paths), Obsidian hub card, people cards, `obsidian-projects.json`
  registration. *Fires on:* "create project / new project".
- **`call-notes`** ⭐ — Log meeting/call notes into the project's `Задачи.md`: per-student
  task assignments, follow-ups, deadlines. *Fires on:* "запиши звонок / задачи после
  звонка".
- **`code-ingest`** ⭐ — One-time deep analysis of an external repo (GitHub URL or path)
  into a structured set of Obsidian Code-library notes mapping how it works (entrypoint,
  modules, where to change X) — citing `path:line`, never copying code. *Fires on:*
  "разбери этот репозиторий / add this repo to the code library".
- **`code-library`** ⭐ — Reference for the whole code workflow: which coding skills/rules
  apply, how the Code library works, how a project hub card records its repo and edits,
  how experiments are monitored. *Fires on:* "how do we work with code here" / onboarding
  to a project with code.
- **`obsidian-project-memory`** — Maintain a project KB without MCP: import a repo, keep
  memory/daily notes synced, summarize context into durable notes.
- **`obsidian-project-bootstrap`** — Bind the current repo to a compact research KB for
  future syncing.
- **`obsidian-project-lifecycle`** — Detach, archive, or purge a project KB.
- **`obsidian-research-log`** — Daily research notes, plans, standups, meetings,
  milestones reflected into daily notes + hub updates.
- **`obsidian-synthesis-map`** — Higher-level synthesis notes: literature reviews,
  comparison matrices, project summaries across notes.
- **`obsidian-link-graph`** — Repair/strengthen wikilinks among canonical project notes
  (papers, knowledge, experiments, results, writing).
- **`obsidian-markdown`** ◇ — Author Obsidian Flavored Markdown: wikilinks, embeds,
  callouts, properties, tags.
- **`obsidian-bases`** ◇ — Create/edit Obsidian Bases (`.base`): views, filters, formulas,
  summaries.
- **`obsidian-cli`** ◇ — Drive a vault from the Obsidian CLI: read/create/search notes,
  tasks, properties; also plugin/theme dev and debugging.
- **`json-canvas`** ◇ — Create/edit JSON Canvas (`.canvas`): nodes, edges, groups —
  mind maps, flowcharts.
- **`operon-obsidian-setup`** ⭐ — Reproduce the lab's Operon task-manager setup in a vault:
  flat `project` tags (no `parentTask` hierarchy), a "my tasks" table dashboard, service-link
  badges on project pages, emoji task icons, and day-boundary auto-archiving. Applies plugin
  settings (`data.json`), templates, a CSS snippet, optional `main.js` display patches, and an
  optional macOS launchd archiver — bundled scripts + assets do the work. *Fires on:* "set up
  Operon / настрой Operon как у тебя / воспроизведи таск-систему Obsidian".

## F. Coding — development

- **`daily-coding`** ◇ — Everyday read/modify source-code tasks. The default coding skill.
- **`tdd`** ◇ — Red-green-refactor loop, test-first, integration tests. *Fires on:* "use
  TDD / red-green-refactor".
- **`architecture-design`** — Factory/Registry patterns for new registrable ML components.
  *Fires on:* creating a new model/dataset that needs registry wiring.
- **`uv-package-manager`** ◇ — `uv` for fast dependency management, venvs, modern Python
  project workflows.
- **`git-workflow`** ◇ — Conventional Commits, branch strategy, merge conflicts, PR
  workflow guidance.
- **`setup-pre-commit`** ◇ — Husky + lint-staged (Prettier), type-check, tests as
  pre-commit hooks. *Fires on:* "set up pre-commit".
- **`git-guardrails-claude-code`** ◇ — Install Claude Code hooks that block dangerous git
  commands (push, `reset --hard`, `clean`, `branch -D`). *Fires on:* "block git push /
  add git safety hooks".

## G. Coding — debugging, quality, verification

- **`bug-detective`** ◇ — Systematic debugging workflow + common error patterns. *Fires
  on:* "debug this / why is this failing / something is broken".
- **`diagnose`** ◇ — Disciplined diagnosis loop for hard bugs and perf regressions:
  reproduce → minimise → hypothesise → instrument → fix → regression-test.
- **`code-review-excellence`** ◇ — Review a diff/PR, write review comments, audit quality,
  establish review standards.
- **`verification-loop`** — Full pre-PR verification: build, type-check, lint, tests,
  security scan, diff review. *Fires on:* "verify code / before a PR".
- **`improve-codebase-architecture`** ◇ — Find deepening/refactor opportunities informed
  by `CONTEXT.md` and ADRs; consolidate coupling, improve testability/AI-navigability.

## H. Frontend & UI

- **`frontend-design`** ◇ — Distinctive, production-grade frontend (components, pages,
  landing pages, dashboards, React/HTML-CSS) that avoids generic AI aesthetics.
- **`ui-ux-pro-max`** ◇ — Design/review UIs: color, typography, accessibility, a coherent
  design system.
- **`web-design-reviewer`** ◇ — Visually inspect a running site (local/remote), find
  responsive/accessibility/layout problems, fix at the source.
- **`webapp-testing`** ◇ — Drive/test local web apps with Playwright: verify behavior,
  capture screenshots, read browser logs.
- **`prototype`** ◇ — Throwaway prototype before committing to a design: a runnable
  terminal app for state/logic, or several toggleable UI variations. *Fires on:*
  "prototype this / try a few designs".

## I. Meta — building the agent itself

These let you extend the agent without memorising every format. The seminar workshop
uses them directly.

- **`skill-development`** ◇ — Create/repair a skill, improve trigger descriptions,
  restructure for reuse. *Fires on:* "create a skill / fix this skill".
- **`skill-quality-reviewer`** ◇ — Evaluate a skill (description, organization, style,
  structure) and emit a quality report.
- **`skill-improver`** ◇ — Apply the improvements from a `improvement-plan-{name}.md`
  produced by `skill-quality-reviewer`.
- **`agent-identifier`** ◇ — Author/configure subagent frontmatter.
- **`command-development`** ◇ — Build slash commands: frontmatter, `$ARGUMENTS`, bash
  execution, file refs, interactive patterns.
- **`hook-development`** ◇ — Build hooks for any event (PreToolUse, PostToolUse, Stop,
  SessionStart/End, UserPromptSubmit, PreCompact, ...), including blocking via exit-code 2.
- **`plugin-structure`** ◇ — Scaffold a plugin: `plugin.json`, component layout,
  auto-discovery, `${CLAUDE_PLUGIN_ROOT}`.
- **`mcp-integration`** ◇ — Add/configure MCP servers (stdio/SSE/HTTP) in a plugin or
  `.mcp.json`.

## J. Workflow, communication & utilities

- **`grill-me`** ◇ — The agent interviews you relentlessly about a plan/design until
  shared understanding, resolving each branch of the decision tree. *Fires on:* "grill me
  / stress-test this plan".
- **`grill-with-docs`** ◇ — Same, but challenges the plan against your project's domain
  model and updates `CONTEXT.md`/ADRs inline as decisions crystallise.
- **`doc-coauthoring`** ◇ — Co-author docs/specs/RFCs/decision-docs through iterative
  collaboration and reader testing.
- **`planning-with-files`** ◇ — Manus-style persistent markdown for planning, progress,
  and knowledge storage on complex multi-step tasks.
- **`handoff`** ◇ — Compact the current conversation into a handoff doc for another agent.
- **`restore-session`** ◇ — Recall a prior session: list saved conversations and load one
  as context. *Fires on:* "restore session / continue previous conversation".
- **`zoom-out`** ◇ — Ask the agent to step back and give higher-level context on a piece
  of code or the task.
- **`caveman`** ◇ — Ultra-compressed communication mode (~75% fewer tokens) while keeping
  technical accuracy. *Fires on:* "caveman mode / be brief / less tokens".
- **`writing-anti-ai`** ◇ — Remove AI writing tells (inflated symbolism, promo language,
  vague attributions, AI vocabulary, negative parallelisms) per Wikipedia's "Signs of AI
  writing". *Fires on:* "humanize this / make it sound natural".
- **`defuddle`** ◇ — Extract clean markdown from a web page via Defuddle CLI (use instead
  of WebFetch to save tokens). *Fires on:* a URL to read/analyze.
- **`google-workspace-mcp`** ⭐ — Read/edit Google Docs from Claude and fix the
  google-workspace MCP OAuth gotchas (Web vs Desktop client, restricted scope, browser
  cache, Test users). *Fires on:* "переавторизуй google / google docs не работает / fix
  google mcp".
