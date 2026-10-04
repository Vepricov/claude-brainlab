---
name: call-notes
description: "Turn research meeting notes into a private project record and approved, separately routed scientific records and tasks."
---

# Call Notes

Turn one meeting into reviewed canonical records across three layers. Load `lab-knowledge` before
any shared knowledge write. Read [`references/analysis-contract.md`](references/analysis-contract.md)
before analyzing a transcript.

The rules every write into the lab base must satisfy are in one place and are not
restated anywhere: `~/.claude/rules/lab-canon.md`, mirrored from
`brainlab/handbook/canon.md`. Read it when the write goes into a work, the handbook
or the journal; it also says which of the three a given thing belongs in.

Before rendering a meeting note, read
[`references/gold-standard-note.md`](references/gold-standard-note.md) — a real approved call
note that sets the quality bar. A note that is thinner than that one is not finished.

When changing or validating this skill, also use
[`references/evaluation-fixture.md`](references/evaluation-fixture.md).

Do not analyze a full call with one monolithic prompt. Normalize it, hydrate project context, use
independent extraction lanes, adjudicate their output, and run a skeptical review.

## Canonical routing

| Item | Canonical destination |
|---|---|
| Raw transcript, personal context, unfinished interpretation | Private Obsidian meeting note |
| Laboratory task, owner, deadline, dependency | Bound Yonote project Kanban |
| Approved shared hypothesis | Lab Knowledge MCP hypothesis |
| Experiment protocol or run | Lab Knowledge MCP experiment |
| Observed result with provenance | Lab Knowledge MCP evidence |
| Proposed conclusion | Lab Knowledge MCP decision proposal |

Do not create project task checkboxes in Obsidian. Do not mirror a Yonote task as another task
file. A hypothesis and a task to test it are distinct objects linked by stable IDs.

## Accepted inputs and transcription

Prefer a platform-provided `.vtt` or `.txt`. The configured local live-capture path is `brain-call`,
which runs ownscribe with system audio plus microphone and writes private `transcript.json` files under
`~/BrainLab/Calls`. Accept that JSON directly and retain its segment timestamps. Ignore an ownscribe
summary as scientific evidence; the normalized transcript is the analysis source. For Zoom, prefer a
local recording with a separate audio file for every participant when it is available; use the track
name as speaker identity only after it matches the project roster. For Yandex Telemost, accept an
ownscribe transcript, the Alice Pro transcript, or the `_audio_only.webm` recording. A mixed audio file
may use anonymous speaker labels, but never inferred real names.

Treat an ownscribe `speaker` value only as an anonymous source label. It becomes a canonical person
only when it exactly matches a name explicitly supplied from the confirmed project roster.

For live local Apple Silicon transcription, prefer the configured isolated ownscribe/WhisperX tool.
For an existing audio file when ownscribe is unavailable, prefer an isolated MLX Whisper runtime.
Keep diarization optional: it adds operational complexity and cannot establish real identities by
itself. Never use a live dictation tool such as SuperDictate to capture the meeting.

After resolving the project roster, normalize supported text input in a private temporary directory.
Pass every confirmed TXT speaker with a repeated `--speaker` flag; an unconfirmed prefix remains text:

```bash
umask 077
call_notes_dir="$(mktemp -d)"
normalized="$call_notes_dir/normalized.json"
trap 'rm -f "$normalized"; rmdir "$call_notes_dir"' EXIT
python3 scripts/normalize_transcript.py /path/to/call.txt \
  --speaker "Confirmed Name" > "$normalized"
```

The source audio, raw transcript, and normalized transcript remain private. Do not upload them to
Lab Knowledge or Yonote.

## Workflow

### 1. Resolve the bound project

Resolve the current project through `~/.Codex/obsidian-projects.json` and the private hub card.
If the registry is absent, follow the active `AGENTS.md` filesystem-to-vault routing rules; do
not silently substitute a Claude registry as the source of truth.
Read its stable Lab Knowledge project reference and Yonote page/board links. Confirm that the
named board belongs to the same project. If the binding is absent, use `lab-project-onboarding`
before preparing shared writes.

Resolve participants only against confirmed project members. Ask one focused question when a
project or person is ambiguous. Never search globally and guess.

### 2. Hydrate a bounded context packet

Read the current project context, hypotheses, related Lab Knowledge search results, confirmed roster,
and the relevant paper sections. Read Yonote task state only through an authorized integration. Give the
same bounded packet to every analysis lane. Do not expose unrelated private notes.

For long calls, segment at topic or project boundaries with a short overlap and retain global segment
IDs. Do not split blindly by token count or lose cross-segment decisions.

### 3. Extract with independent agents

Follow the required lanes and candidate schema in the analysis contract. Use three independent
subagents plus the integrator: scientific, action, and chronology/privacy. After all three finish, use a
fresh independent reviewer for the skeptical pass. If this topology is unavailable, stop before shared
publication and report the degraded mode.

### 4. Adjudicate without collapsing object types

Preserve distinct tasks, hypotheses, experiments, evidence, and decisions. A completed task is
not evidence. A reported metric is not a decision. Evidence must state what was observed and
where the supporting artifact can be found.

Keep raw text private by default. Merge by semantic identity and stable IDs, preserve contradictions,
and publish only the minimum project-relevant facts explicitly approved for laboratory reuse. Produce
one typed `CallBundle` with private minutes, shared candidates, blocked items, and questions.

### 5. Check duplicates and permissions

Use Lab Knowledge search and project context to find semantically related shared records before
creating any hypothesis, experiment, evidence, or decision. Use the configured server-side
Yonote broker to resolve existing board items. The client must never read or store a shared
Yonote API token.

Treat access denial as final. Do not infer hidden records from result counts, timing, IDs, or
different error messages.

### 6. Preview once and approve

Show one compact batch preview:

```text
Obsidian private: meeting summary and private context
Yonote tasks: title, project, assignee, due date, related Lab Knowledge ID
Lab Knowledge: type, claim/result, project, provenance, duplicate candidate
```

Mark unresolved fields, source spans, confidence, and suspected duplicates. Obtain explicit approval
before all shared mutations and before creating new participant cards. Let the user remove or edit
individual items without re-approving unchanged items.

### 7. Write each object once

Write a newest-first `DD-MM-YYYY` block to the private project meeting note. Store only concise
narrative and stable references to shared objects.

Create laboratory tasks only if the live MCP schema advertises a server-side Yonote task
operation for the bound Kanban. The current project provisioning operation creates bindings but
does not provide task CRUD. If task CRUD is absent, mark the task batch `blocked/manual`, give the
exact board link, and do not claim that tasks were created. Never use a client-side shared token.

For Lab Knowledge, do not call anything: the base is a git repository of the work, cloned
locally. A claim is the folder `claims/<CODE>/`; a series, a run, a derivation and a figure are
files inside it. Edit the files, then `lab pr` and `lab checks`; a person merges, and the merge
is the write. Direct MCP writes are refused by design. Preserve source provenance in the page
itself, and do not change a claim's status just because a number was added under it.

Call a shared create/update only when the destination can persist and query the normalized source hash
and candidate idempotency key, or exposes an equivalent server-side idempotency parameter. Otherwise
leave that mutation `blocked`; prompt-level deduplication is not a replay guarantee.

Use the transcript SHA-256 as the batch idempotency key. Reprocessing the same transcript updates the
preview; it must not create a second set of records.

### 8. Verify and report

Read back every created shared record under the caller's own permissions. Report IDs/links,
duplicates reused or skipped, private files changed, and unresolved items. If a destination was
unavailable, report the exact prepared item and binding needed; never claim it was created.

## Safety

- Use the exact term `ZO`, never a translated or expanded substitute in project metadata.
- Never publish raw transcripts, private commentary, local paths, secrets, or credentials.
- Never broaden visibility beyond the access mode explicitly approved for that project. A
  workspace-visible board is allowed only when the user has explicitly selected that temporary
  mode; do not generate a public share link.
- Never invent an assignee, deadline, metric, result, source, or API response.
