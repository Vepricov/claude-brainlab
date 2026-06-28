---
name: obsidian-experiment-log
description: Use this skill when the user discusses experiment design, ablations, training runs, evaluation, baselines, metrics, failures, or result interpretation that should be logged into Obsidian experiment and result notes. Covers both the note structure and the operational workflow for launching, monitoring, and post-mortem of multi-hour ML runs on shared servers.
---

# Obsidian Experiment Log

Use this skill whenever project work changes the experimental state — either because a new run is being designed, launched, monitored, or completed, or because results need to be promoted into stable findings.

## Role in the workflow

Supporting skill under `obsidian-project-memory`. Covers two layers:
1. **Operations** — how to launch, monitor, and chain real training runs on remote servers
2. **Notes** — how to record the run's intent, progress, finals, and decisions into Obsidian

Both layers must be applied together. A finished experiment with no notes is invisible to future agents; a beautifully written note with no actual run is fiction.

---

## Layer 1 — Operations (running the experiments)

### Two execution modes — pick by user intent

| Mode | When to use | Reference |
|---|---|---|
| **Live monitor with /loop** | Multi-hour runs needing post-finish actions (kill tmux, refresh plot, launch next from queue, write final into table). User says "следи / поставь N ранов / запусти когда освободится". | [[general/Knowledge/autonomous-experiment-loop]] |
| **Push queue (per-GPU lane)** | Set-and-forget N items, no trigger logic, no chained actions. User says "поставь очередь на ночь". | [[general/Knowledge/server-run-queue]] |

The live-monitor mode is the default for warmup-style hypothesis studies. The push queue is for compute-burning ablations where order matters but events don't.

### Launch primitive (tmux + pipe-pane)

Every training run = one tmux session whose pane is piped to a log file. Survives ssh drop, log stays parseable.

```bash
ssh SERVER "tmux new-session -d -s SESSION_NAME && \
  tmux pipe-pane -t SESSION_NAME:0 'cat >> /abs/path/logs/RUN.txt' && \
  tmux send-keys -t SESSION_NAME 'source ~/venv/bin/activate' Enter && sleep 1 && \
  tmux send-keys -t SESSION_NAME 'cd ~/repo' Enter && \
  tmux send-keys -t SESSION_NAME 'GPU=N WS=X LR=Y SEED=Z bash scripts/param_run.sh' Enter"
```

Critical ordering:
- `tmux new-session -d -s NAME` first, **then** `pipe-pane`, **then** `send-keys`. Collapsing them (`tmux new -d -s NAME 'cmd'`) races the pane setup → empty log.
- Verify within 60–90 s: `tmux capture-pane -t NAME:0 -p | tail -10` should show `Iter=` lines. If only optimizer-init lines after 60 s, the run is stuck — kill and investigate before scheduling the next tick.

### Parametrized launcher (one script per experiment family)

Don't write one bash script per run. One parametrized script per family, env-var-controlled:

```bash
ITERS=${ITERS:-32000}
GPU=${GPU:-0}
LR=${LR:-1e-3}
WS=${WS:-10}
SEED=${SEED:-0}
# ... --lr $LR --warmup_steps $WS --seed $SEED ...
```

Adding `SEED=42` for reproducibility reruns becomes a one-line edit (`SEED=${SEED:-0}` + `--seed $SEED`). No fork. Default unchanged so prior runs unaffected.

### The /loop prompt (state lives in the prompt, not the agent)

```
AUTONOMOUS <study> on <server>.

CURRENT active runs (N):
- `session_1` (GPU X, ~Ys/iter, last iter, last val)

DONE so far: <seed=0 finals>

PLANNED queue: <ordered list of configs>

GPU plan: <which finish → which launch>

Each tick: ssh SERVER 'grep ">Eval" logs/<files>; nvidia-smi'

TRIGGERS:
(a) GPU >50GB free AND <30% util AND next item not running → launch
(b) running session hits target iter → record final, kill tmux, refresh plot, launch next
(c) ALL queue done → write final results section, STOP loop

Launch template: <one-line tmux+pipe-pane command>

CONSTRAINTS: paper-canonical hypers only. 30-min cadence. NO other launches.
```

The agent re-receives this verbatim every 30 min via `ScheduleWakeup(1800, /loop ...)`. Nothing in the model's head; state lives entirely in server logs + the prompt itself.

### Trigger semantics

| Trigger | Action | Don't forget |
|---|---|---|
| `last_eval_iter == target_iter` | record final, `tmux kill-session -t NAME`, refresh plot | check pane shows `wandb` sync + shell prompt — confirms clean exit, not OOM |
| GPU `>50GB free AND <30% util` | launch next queued config | re-check 60 s after launch that `Iter=` appears in log |
| **Same iter for two consecutive ticks** | **investigate stall before next tick** | check pane (`tmux capture-pane`) for traceback; check `df -h /data` for disk-full |
| All queue items finished | write final summary section + STOP loop (no ScheduleWakeup) | refresh plot one last time, add MemPalace drawer |

### GPU contention on shared servers

Other users grab freed GPUs in seconds. Two rules:

1. **Don't assume the GPU you freed is the GPU you'll reclaim.** After `kill-session`, log GPU map immediately. If now-owned by someone else, find a different free GPU.
2. **Safe envelope on H200 (141GB):** `>50GB free AND <30% util` for ~24GB models. Tighten or loosen per server class.

```bash
# GPU state
ssh SERVER 'nvidia-smi --query-gpu=index,memory.used,memory.free,utilization.gpu --format=csv,noheader'

# Ownership (who runs what)
ssh SERVER 'nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory,process_name --format=csv,noheader'
```

Map UUID → index using `--query-gpu=index,gpu_uuid`.

### Two failure modes to design for

**Same iter as last tick — process is stuck or dead.** Don't blindly schedule another tick. Capture the pane (`tmux capture-pane -t NAME:0 -p | tail -20`), look for: Python traceback, wandb upload + shell prompt (= clean finish you didn't notice), or silence (= true hang).

**Disk full mid-checkpoint.** `torch.save` fails partial writes with `RuntimeError: [enforce fail at inline_container.cc:...] . unexpected pos N vs 0`. Check `df -h /data`. If >95% full, **do not restart** — it will crash again. Accept partial result, document, move on.

### Brutal honest reporting

If a run crashed, write "crashed at iter X with traceback Y", not "may not have completed". If a finding rests on a partial trajectory, say so explicitly — "Q3 didn't finish; trajectory at 84% (val 3.072) consistent with Q1 at same %; inferred final ~3.04". Reviewers see through hedge-words; agents shouldn't generate them.

### Constraints worth always restating in the /loop prompt

- Paper-canonical hyperparameters only (no off-paper "fixes" without explicit user approval)
- NO other launches without explicit user instruction
- Cadence 30 min (1800 s): under 5 min wastes prompt-cache, over 60 min misses contention windows

---

## Layer 2 — Notes (documenting the experiments)

### Default outputs

- the relevant canonical note in `Experiments/`
- the relevant canonical note in `Results/`, if a durable finding exists
- links from today's `Daily/` note
- relevant hub or plan references only when project state materially changes

### Main rules

- Prefer updating an existing experiment note over creating a sibling note for the same experiment line.
- Prefer updating an existing result note over creating a parallel result page for the same durable finding.
- Raw logs, metric dumps, and temporary analysis fragments stay in `Daily/` until interpreted.
- A result note should exist only when the outcome is stable enough to reference later.

### File roles — three files, three jobs

| File | Role | Cadence |
|---|---|---|
| `Experiments/<series>.md` | per-tick narrative: launches, mid-run progress, decisions, crashes | every meaningful tick / finish |
| `Results/<series>-table.md` | only finals, only paper-grade. Sectioned by hypothesis. Embeds plot PNG. | when a final lands |
| `tools/refresh_plot.sh` (project-side) | local script: rsyncs remote logs, calls plot script, swaps PNG path in Results md | each tick that materially changes plotted data |

The Experiments log is the **narrative**; the Results table is the **conclusion**. Don't mix.

### Minimum experiment sections

- Goal / hypothesis
- Code or config entrypoint
- Dataset / split
- Metrics
- Status (`planned`, `running`, `done`, `failed`)
- Findings / notes
- Next step

### Minimum result sections

- Linked experiment
- Main observation
- Key numbers
- Evidence (loss curve, table, plot embed)
- Interpretation
- Decision: keep / iterate / discard

### Linking rule

Link experiments and results directly to each other, and link both back to `00-Hub.md`, `01-Plan.md`, or `Daily/` only when those references improve the main working surface.

### Research path handoff

Treat experiment notes as the bridge between `Papers/` and `Results/`:
- paper-derived hypotheses, baselines, and ablations land here
- stable findings get promoted from here into `Results/`
- when a result becomes claim-worthy, update `Writing/` rather than leaving the chain unfinished

### Post-mortem ritual (after every meaningful event)

1. Append to `Experiments/<series>.md` with timestamp + brief reads
2. If a result (val_loss, perplexity, accuracy): write the number into `Results/<series>-table.md` and refresh plot
3. If a decision (restart? give up? accept partial?): write 2–3 lines of reasoning in Experiments
4. After 5–10 such events: `mempalace_add_drawer` summarizing what's stable knowledge now

---

## Skill activation

Trigger this skill on user phrases like:
- "запусти параллельно X, Y, Z и следи"
- "поставь раны на N часов и сделай Q когда добежит"
- "сделай seed reruns после того как закончится текущий sweep"
- "проверь как идёт <experiment>" / "как там дела"
- "запиши результаты эксперимента в таблицу"
- "у меня крашнулся ран — что делать"

Workflow when activated:
1. Identify mode (live-monitor vs push-queue) from user intent
2. Identify project paths (`Experiments/<series>.md`, `Results/<series>-table.md`) from project's `.claude/CLAUDE.md`
3. For live-monitor: build /loop prompt → launch first runs via tmux+pipe-pane primitive → `ScheduleWakeup(1800s)`
4. For push-queue: follow [[server-run-queue]]
5. On every tick: log to Experiments narrative; on every final: update Results table + refresh plot
6. Stop the loop only after writing the final summary section (no orphaned ScheduleWakeup calls)

Cross-references:
- [[general/Knowledge/autonomous-experiment-loop]] — full operations playbook
- [[general/Knowledge/server-run-queue]] — push-queue alternative
- [[general/Knowledge/warmup-loss-plot-tool]] — refresh_plot.sh patterns + iCloud gotchas
- [[general/Knowledge/claude-loop-stay-alive-on-mac]] — keeping local /loop session alive

Last revised 14-06-2026 based on the 583M Muon warmup study (loop ran for 3+ days, 13 finished runs, 1 disk-full crash handled).
