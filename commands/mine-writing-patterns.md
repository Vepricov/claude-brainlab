---
name: mine-writing-patterns
description: Read one or more papers and update the global paper-miner writing memory with reusable writing patterns, structure signals, reusable phrasing, venue-specific signals, and rebuttal-friendly language.
args:
  - name: source
    description: Paper source path, URL, arXiv link, or a short description of the target papers
    required: true
  - name: focus
    description: Optional focus area (general/introduction/method/results/rebuttal/venue)
    required: false
    default: general
tags: [Research, Writing, Paper Mining, Knowledge Extraction]
---

# /mine-writing-patterns - Global Writing Memory Mining

Read the paper source "$source" and update the **global paper-miner writing memory**.

## Default target

Always write mined knowledge into:

```text
~/.claude/skills/ml-paper-writing/references/knowledge/paper-miner-writing-memory.md
```

This command does **not** create project-specific writing memory.

## When to use

Use this command when you want to:
- learn reusable writing patterns from a strong paper,
- study how a venue frames introductions, methods, results, or rebuttals,
- mine phrasing and structure signals before drafting,
- enrich the global writing memory that powers `ml-paper-writing` and `review-response`.

## Usage

### Basic usage

```bash
/mine-writing-patterns path/to/paper.pdf
```

### Mine from an arXiv paper

```bash
/mine-writing-patterns https://arxiv.org/abs/2301.xxxxx
```

### Focus on rebuttal or venue signals

```bash
/mine-writing-patterns path/to/paper.pdf rebuttal
/mine-writing-patterns path/to/paper.pdf venue
```

## Workflow

### Step 1: Resolve the paper source

Acceptable inputs:
- local PDF
- local DOCX
- arXiv URL
- readable web URL
- short natural-language request that identifies the paper(s)

If the source is ambiguous, narrow it before mining.

### Step 2: Invoke `paper-miner`

Use the `paper-miner` agent to:
- extract paper content,
- identify reusable writing knowledge,
- merge it into the global writing memory,
- avoid duplicate entries,
- preserve source attribution.

### Step 3: Respect the focus mode

Interpret `$focus` as follows:

| Focus | Priority |
|------|----------|
| `general` | Mine balanced signals across all major sections |
| `introduction` | Emphasize framing, motivation, and contribution setup |
| `method` | Emphasize exposition style, technical sequencing, and clarity |
| `results` | Emphasize result narration, claim-evidence language, and interpretation |
| `rebuttal` | Emphasize clarification phrases, response structure, and reviewer-facing tone |
| `venue` | Emphasize venue-specific style and convention signals |

### Step 4: Update the canonical memory only

The canonical write target is:

```text
~/.claude/skills/ml-paper-writing/references/knowledge/paper-miner-writing-memory.md
```

Update one or more of these sections:
- `Writing patterns mined`
- `Structure signals`
- `Reusable phrasing`
- `Venue-specific signals`
- `How this helps our writing`
- `Source index`

Do not create project-local writing memory.
Do not scatter the mined result across multiple maintained knowledge files.

### Step 5: Return a standardized mining summary

The final response should follow the `paper-miner` standardized output format:
- metadata
- memory write summary
- new reusable patterns
- how we should reuse this
- blockers or limits

## Related integrations

- `ml-paper-writing` reads this global memory before drafting or revising sections.
- `review-response` reads this global memory when tone, phrasing, and rebuttal structure matter.
- `paper-miner` is the agent that performs the actual mining work.

## Success criteria

- the target paper is read successfully,
- reusable writing knowledge is merged into the canonical memory,
- source attribution is preserved,
- no project-specific writing memory is created,
- the user receives a standardized mining summary.
