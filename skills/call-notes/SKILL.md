---
name: call-notes
description: Process research call or meeting notes when the user says "запиши звонок", "записать встречу", "call notes", "что сделать студентам", or "задачи после звонка". Keep the private narrative in Obsidian, publish approved hypotheses, experiments, evidence, and decisions to Lab Knowledge MCP, and create laboratory tasks only on the project's bound Yonote Kanban without duplicates.
---

# Call Notes

Turn one meeting into reviewed canonical records across three layers. Load `lab-knowledge` before
any shared knowledge write. Read [`references/analysis-contract.md`](references/analysis-contract.md)
before analyzing a transcript.

When changing or validating this skill, also use
[`references/evaluation-fixture.md`](references/evaluation-fixture.md).
When changing semantic reconstruction, human-correction handling, or preview revision, also run the
real-call regression in
[`references/hwo-preview-regression.md`](references/hwo-preview-regression.md).
For project terminology, unknown-term questions, and explicitly confirmed vocabulary learning, follow
[`references/asr-glossary.md`](references/asr-glossary.md).
Write every private meeting note with
[`references/obsidian-meeting-template.md`](references/obsidian-meeting-template.md).
Maintain the project's curated local hypothesis hub with
[`references/obsidian-hypothesis-template.md`](references/obsidian-hypothesis-template.md).

Do not analyze a full call with one monolithic prompt. Normalize it, hydrate project context, use
independent extraction lanes, adjudicate their output, and run a skeptical review.

## Mandatory execution topology

Every full call uses this topology. It is not an optional optimization:

1. **Context hydration:** use one bounded `ProjectDossier` containing Lab Knowledge, private/paper, and
   coordination sections. An interactive agent builds it with independent read-only workers. The local
   `brain-call` runner may instead consume the already curated, hash-verified project packet produced by
   `build_project_context`; it must block if any required section or confirmed roster is missing.
2. **Independent lanes:** a scientific lane, action lane, and chronology and privacy lane analyze the
   same normalized transcript and dossier without reading one another's conclusions.
3. **Integrator:** a distinct integrator merges candidates, preserves disagreements, and prepares one
   `CallBundle`; it does not write to any destination.
4. **Fresh independent skeptic:** a reviewer that did not participate in extraction or integration
   checks the complete bundle and may veto any item.
5. **Orchestrator:** after explicit approval, the call-notes orchestrator performs every Obsidian, Lab
   Knowledge MCP, and Yonote mutation itself and reads each destination back.

If this topology cannot be executed, stop before any canonical write and report
`blocked: mandatory_multi_agent_topology_unavailable`. Do not replace it with one large prompt or a
single-agent write path.

## Canonical routing

| Item | Canonical destination |
|---|---|
| Raw audio and transcript | Local private `~/BrainLab/Calls` storage only |
| Curated project minutes and relevant unfinished interpretation | Private Obsidian meeting note |
| Laboratory task, owner, issue date, deadline, dependency | Bound Yonote project Kanban plus a private Obsidian snapshot |
| Approved shared hypothesis | Lab Knowledge MCP hypothesis |
| Experiment protocol or run | Lab Knowledge MCP experiment |
| Observed result with provenance | Lab Knowledge MCP evidence |
| Proposed conclusion | Lab Knowledge MCP decision proposal |

Do not create a second writable task tracker in Obsidian. Record every meeting task in the private
meeting note as a detailed historical snapshot, then link it to the canonical Yonote item after
publication. A hypothesis and a task to test it are distinct objects linked by stable IDs.
Treat legacy project task files and checkboxes as read-only archives. Never update their status or add
new meeting tasks there; Yonote is the sole live task-status source.

## Destination-specific curation

- **Private Obsidian meeting note:** preserve the complete project-relevant narrative: hypotheses,
  tentative ideas, experiment discussions, intermediate observations, contradictions, corrections,
  decisions, open questions, and every task with its owner, issue date, due date, dependency, and
  scientific context. The task section is a historical snapshot; live status remains canonical in
  Yonote. Keep personal or unrelated material private and omit it from the research summary.
- **Private Obsidian hypothesis hub:** maintain one `Гипотезы.md` per project for durable, useful
  hypotheses. Mirror the same compact scientific claim shown in Yonote, add the richer local context
  needed by personal agents, and link bidirectionally to call files, experiments, Lab Knowledge IDs,
  and Yonote. Tentative call-only ideas stay in their call file until they are curated.
- **Lab Knowledge MCP:** publish approved project knowledge as typed objects. Preserve hypotheses,
  experiments, evidence, and decision proposals separately. Intermediate results may be evidence when
  their provenance and limitations are explicit; otherwise keep them as unresolved private notes.
- **Yonote project view:** create laboratory actions only on the bound project Kanban. The human-facing
  project page may show a small curated set of high-level hypotheses that help a reader understand the
  project. Do not project raw transcripts, run-by-run intermediate results, private commentary, local
  paths, or MCP implementation details into Yonote.

Every accepted task has a confirmed non-null `assignee` and `issued_date`, normally the call date. If
either field cannot be resolved, keep the candidate blocked until the user confirms it.
Set `due_date` only when a deadline is explicitly stated and not later withdrawn. If the live Yonote
schema has no dedicated native `Исполнитель` or `Выдана` property, block the Yonote mutation. Never
fall back to the document body and never copy `issued_date` into `due_date`.
Task titles contain only the atomic action. Never add the project code, assignee, issue date, due date,
or status to the title; store them in their dedicated fields. Store each call in
`Звонки/<CODE> DD-MM-YYYY.md`; its H1 must not contain the project code.

For every experimental execution task, resolve the concrete `method_variant`, `model_scale`,
`initialization`, whether RL is enabled, and the expected artifact. Resolve the dataset and evaluation
protocol whenever changing either could alter the command, config, data split, metric, or acceptance
result; otherwise mark it `not_material` with an explicit reason. Phrases such as “current line”,
“canonical run config”, “matched setup”, or “same experiment” do not substitute for these fields unless
the destination contains a direct, accessible link to an immutable config that resolves every required
value.

If a required execution field is unresolved, block that task before shared mutation with
`missing_execution_parameters`. Put every missing key in `missing` and add focused, candidate-linked
questions to the single batch `questions_for_user`; their union must cover all missing keys. Do not
silently infer the method or run variant. Do not create `write_payload` or publish the task until the
user answers.

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

Drop voice-assistant prompts, subtitle credits, repeated recording watermarks, and unrelated dictation
as `out_of_scope_personal`. They remain only in the untouched local raw transcript when the user keeps
it. Do not copy them into candidates, summaries, Obsidian call notes, or even private project minutes;
private project minutes still contain only meeting material relevant to the selected project.

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
call_notes_skill_dir="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}/call-notes"
trap 'rm -f "$normalized"; rmdir "$call_notes_dir"' EXIT
python3 "$call_notes_skill_dir/scripts/normalize_transcript.py" /path/to/call.txt \
  --speaker "Confirmed Name" > "$normalized"
```

The source audio, raw transcript, and normalized transcript remain private. Do not upload them to
Lab Knowledge or Yonote.

Use only the shared global glossary plus the selected project's scoped glossary. If a material term is
unknown, keep the heard form in the private preview and ask one focused terminology question.
Never let the model add its own guess. After the user explicitly explains and confirms the mapping, update the
shared glossary through the deterministic `brain-call --learn-term ... --confirmed-by-user` command,
then regenerate the affected preview. A terminology correction is not approval for any other write.

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

Follow the mandatory topology, ownership rules, and candidate schema in the analysis contract. Do not
collapse a context worker, extraction lane, integrator, skeptic, or orchestrator into another role.

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

Build the semantic reconstruction before rendering task cards or shared candidates. Label which facts
came from the transcript, project context, and user correction. Keep unresolved human uncertainties in
a separate visible section instead of hiding them in fluent prose.

If a spoken correction is ambiguous, use the voice-restatement fallback from the HWO regression:
restate the interpreted changes and remaining uncertainties, then ask for explicit confirmation. Every
correction follows revision-before-write: revise the preview, retain the correction trail, rerun the
applicable gates and skeptical review, and request approval of the exact revised payload. A correction
alone never authorizes a write.

ASR quality gates automatic publication, not semantic recovery. For `degraded` and `unusable` transcripts,
run the independent science, actions, and privacy lanes over every recoverable fragment. Preserve planned
experiments as tasks or focused owner questions; never ask for a full retelling merely because speakers are
anonymous or coverage is low. Only a transcript with no meaningful recoverable content may use
`needs_restatement`.

When that empty-transcript gate stopped the original full-call analysis and the user then supplies an
authoritative restatement, do not rerun the entire empty transcript topology. Run a bounded revision
path: one read-only structurer creates the corrected preview and a separate fresh read-only verifier
checks it against the restatement, project dossier, and regression contract. The runner records both
successful invocations before marking the revision reviewed. This exception applies only to a
user-restatement revision; every transcript with recoverable content still uses the full mandatory topology.

Show one compact batch preview:

```text
Obsidian private: meeting summary and private context
Yonote tasks: title, project, assignee, issued date, due date, related Lab Knowledge ID
Lab Knowledge: type, claim/result, project, provenance, duplicate candidate
```

Mark unresolved fields, source spans, confidence, and suspected duplicates. Obtain explicit approval
before all shared mutations and before creating new participant cards. Let the user remove or edit
individual items without re-approving unchanged items.

The local orchestrator may also send a **Jarvis sanitized digest** after the complete `CallBundle` has
passed skeptical review. Jarvis is notification and correction UI only: it does not watch the call,
does not run extraction, and never receives the raw transcript, audio, source excerpts, local paths,
secrets, or destination credentials. The digest is derived from the reviewed bundle and is bounded to
the project, call date, three to five main theses, destination counts, blocked questions, and existing
Yonote/project links. Keep it under 1,200 characters and identify editable items by stable candidate ID.

Jarvis may return one optional correction comment that refers to those stable IDs. No comment means
“no correction requested”, not explicit approval. The local call-notes orchestrator applies a correction
to the preview and asks for explicit approval of the exact changed payload. Jarvis never performs
Obsidian, Lab Knowledge, or Yonote mutations and does not start a watcher or follow-up loop.

## Task examples embedded in the contract

These examples define the required human-facing quality and the execution gate. They are included here
directly so an agent does not need to infer the expected card shape from a link.

### Good example: 1B KronZO run

This example assumes the dossier contains a direct immutable config reference that resolves the
material dataset and evaluator. Without that reference, the same candidate is blocked.

```yaml
title: Запустить KronZO + ARC-ZO + RL на 1B с FO initialization
body: >-
  Проверить масштабирование KronZO + ARC-ZO + RL на модель 1B. FO initialization
  и RL должны быть включены; это отдельный запуск от layer-wise ветки без RL.
  Сохранить config, logs и checkpoint, а также learning и validation curves для
  сопоставления с текущим 360M запуском.
assignee: Трофимов Владислав
issued_date: 2026-08-06
due_date: null
execution_spec:
  method_variant: KronZO + ARC-ZO + RL
  model_scale: 1B
  initialization: FO initialization
  rl_enabled: true
  dataset: resolved by the immutable baseline config in context_refs
  evaluation: resolved by the immutable baseline config in context_refs
  expected_artifact: config, logs, checkpoint, learning curve, validation curve
```

### Good example: two-seed DyKAF reproduction

```yaml
title: Запустить ещё два seed для DyKAF + Shampoo
body: >-
  Проверить воспроизводимость результата DyKAF + Shampoo ещё на двух seed. Полностью
  переиспользовать immutable protocol E-DYC-017 и менять только seed. Для каждого запуска
  сохранить config, logs, checkpoint и validation result и связать их с E-DYC-017.
assignee: Иван Петров
issued_date: 2026-08-06
due_date: 2026-08-10
due_date_basis: "к следующему понедельнику, Europe/Moscow"
execution_spec:
  method_variant: DyKAF + Shampoo from E-DYC-017
  model_scale: from immutable E-DYC-017 protocol
  initialization: from immutable E-DYC-017 protocol
  rl_enabled: from immutable E-DYC-017 protocol
  dataset: from immutable E-DYC-017 protocol
  evaluation: evaluator and metric from immutable E-DYC-017 protocol
  expected_artifact: two configs, logs, checkpoints, and per-seed validation results
```

### Blocked anti-example

```yaml
title: Запустить финальный training run для ablation
candidate_state: blocked
owner: Иван Петров
issued_date: 2026-08-06
execution_spec:
  method_variant: null
  model_scale: null
  initialization: null
  rl_enabled: null
  dataset: null
  evaluation: null
  expected_artifact: null
missing: [method_variant, model_scale, initialization, rl_enabled, dataset, evaluation, expected_artifact]
block_reason: missing_execution_parameters
operation: blocked
write_payload: absent
```

Never replace the missing fields in the anti-example with phrases such as “current run” or “use the
canonical config”. Ask one candidate-linked question batch and publish nothing until the answers or a
direct immutable config resolve every field.

### 7. Write each object once

Create or update the private per-call note at `Звонки/<CODE> DD-MM-YYYY.md` with the full structured
meeting snapshot and stable references to shared objects. Do not append new calls to one aggregate file.

Before any mutation, require the configured broker to advertise actual Yonote task CRUD for the bound
Kanban, including create/update, lookup or deduplication, and read-back. If it is absent, stop the write
phase and report `blocked: yonote_task_crud_unavailable` loudly. Do not emit a manual fallback, write a
partial batch, or claim that tasks were created. Never use a client-side shared token.

For Lab Knowledge, use the object-specific operation advertised by the live MCP schema:
`create_hypothesis`, `record_experiment`, `record_evidence`, or `propose_decision`. Preserve
source provenance and returned stable IDs. Do not automatically change a hypothesis status when
evidence is recorded.

For every Yonote task, keep the human-facing card clean:

- the title contains only the action, without a project code, date, owner, or generic `Задача` prefix;
- `Исполнитель` and `Выдана` are required native database properties, not lines duplicated in the
  document body;
- `Выдана` must also be configured as a visible native date property in the normal human-facing task,
  card, or board view. Merely storing a hidden property is insufficient. If visibility cannot be
  verified, block before mutation with `yonote_issued_date_not_visible`;
- `Срок` is a separate native property and stays empty unless a deadline was explicitly agreed;
- the body contains only a useful task description: the research or operational context, the exact
  action, and an observable completion artifact or acceptance criterion. Use two to four concise
  sentences when that context is available;
- internal source hashes, idempotency markers, MCP IDs, HTML comments, and other machine metadata
  must never appear in the title or body. Replay protection belongs to the Brain Lab service or another
  destination-native hidden mechanism that is guaranteed not to render to users.

After approval, the orchestrator creates or updates the approved Obsidian note and hypothesis hub,
typed Lab Knowledge records, and Yonote tasks. Extraction agents, the integrator, and the skeptic remain
read-only. The orchestrator then reads back the exact call file, every MCP object, and every Yonote item;
missing or mismatched read-back is a failed write, not success with a warning.
For Yonote, read-back verifies both the issued-date value and that the active human-facing view exposes
the `Выдана` property.

Call a shared create/update only when the destination can persist and query the normalized source hash
and candidate idempotency key, or exposes an equivalent server-side idempotency parameter. Otherwise
leave that mutation `blocked`; prompt-level deduplication is not a replay guarantee.

Use the transcript SHA-256 as the batch idempotency key. Reprocessing the same transcript updates the
preview; it must not create a second set of records.

### 8. Verify and report

Read back every created or updated record under the caller's own permissions. Report IDs/links,
duplicates reused or skipped, private files changed, and unresolved items. Success requires verified
read-back from Obsidian, Lab Knowledge MCP, and Yonote for every approved item.

## Safety

- Use the exact term `ZO`, never a translated or expanded substitute in project metadata.
- Never publish raw transcripts, private commentary, local paths, secrets, or credentials.
- Never broaden visibility beyond the access mode explicitly approved for that project. A
  workspace-visible board is allowed only when the user has explicitly selected that temporary
  mode; do not generate a public share link.
- Never invent an assignee, deadline, metric, result, source, or API response.
