---
name: obsidian-experiment-log
description: "Keeps a monitored training run's live page in its own folder <work>/runs/<E-code>/ with progress snapshots and a convergence plot that Obsidian shows like a W&B run page. Use when the user launches, monitors, or finishes a training run, asks to log an experiment, update a results table, or promote a finished result into a stable finding."
---

# Obsidian Experiment Log

Use this skill whenever project work changes the experimental state — either because a new run is being designed, launched, monitored, or completed, or because results need to be promoted into stable findings.

## Role in the workflow

Covers two layers:
1. **Operations** — how to launch, monitor, and chain real training runs on remote servers
2. **Notes** — the run's live page with its convergence plot, inside the work in `~/brainlab`

Both layers must be applied together. A finished experiment with no notes is invisible to future agents; a beautifully written note with no actual run is fiction.

---

## Layer 1 — Operations (running the experiments)

### Two execution modes — pick by user intent

| Mode | When to use | Reference |
|---|---|---|
| **Live monitor with /loop** | Multi-hour runs needing post-finish actions (kill tmux, refresh plot, launch next from queue, write final into table). User says "следи / поставь N ранов / запусти когда освободится". | [[personal/Knowledge/autonomous-experiment-loop]] |
| **Push queue (per-GPU lane)** | Set-and-forget N items, no trigger logic, no chained actions. User says "поставь очередь на ночь". | [[personal/Knowledge/server-run-queue]] |

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

## Layer 2 — Notes: the run's own folder, with a live convergence plot

The vault is the lab tree `~/brainlab`, so a monitored run is watched in Obsidian like a W&B run page. Owner 26-10-2026: «удобно что логи рисуются в обсидиане… чтобы у рана если я попросил его мониторить прям в E- папке экспа рисовался бы какой то график сходимости в md файле».

### Where it lives

One folder per run, named by its E-code, in the work's local shelf (closed from git):

```
<работа>/runs/<E-код>/
  README.md                  # status, progress table, plot embed, decisions
  curves-<YYYYMMDD-HHMM>.png # current convergence plot, one file at a time
```

A series of runs watched together gets one folder for the series (`runs/<S-код>/`) with one plot, and each run's row in its table.

### README.md of the run folder

- one line: what is checked and what the result will mean (the recorder's `objective`);
- status (`running`, `done`, `failed`, `killed`), server, GPU, tmux session, log path;
- the plot embed `![[curves-<stamp>.png]]` right under the status;
- `## Progress snapshots` — timestamped table: step, train loss, val metric, s/iter, ETA;
- decisions and crashes, 2-3 lines each, with the time.

### The plot

- Refresh it on every tick and on every progress report to the owner, in the same turn. A number without the matching curve is half a report.
- Draw from what the code wrote: the recorder's `metrics.csv` or the server log. Never from numbers typed by hand.
- House style and the plotter: `personal/Knowledge/warmup-loss-plot-tool.md` (main panel + zoom on running tips, big fonts, narrow figure).
- Obsidian caches embeds by file name: write a new timestamped file, rewrite the embed, delete the previous file. Keep the note closed in Obsidian while the loop writes it.

### When the run is finished

The run enters the lab base through `lab-knowledge`: the recorder's page goes to `claims/<H>/runs/<E>.md`, and a figure that carries a conclusion goes to `claims/<H>/figures/F-….svg` (SVG only, data only from that series). The local folder stays as the run's diary; nothing from it is copied into the base by hand.

### Post-mortem ritual (after every meaningful event)

1. Append a snapshot row and refresh the plot.
2. If a decision (restart? give up? accept partial?): 2-3 lines of reasoning in the run's README.
3. When the run or series is done: carry it into the base via `lab-knowledge`, and a `mempalace_add_drawer` with the stable numbers.

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
2. Find the work in `~/brainlab` and the run's E-code; create `runs/<E-код>/README.md`
3. For live-monitor: build /loop prompt → launch first runs via tmux+pipe-pane primitive → `ScheduleWakeup(1800s)`
4. For push-queue: follow [[server-run-queue]]
5. On every tick: snapshot row + refreshed plot in `runs/<E-код>/`; on finish: final numbers, then `lab-knowledge`
6. Stop the loop only after writing the final summary section (no orphaned ScheduleWakeup calls)

Cross-references:
- [[personal/Knowledge/autonomous-experiment-loop]] — full operations playbook
- [[personal/Knowledge/server-run-queue]] — push-queue alternative
- [[personal/Knowledge/warmup-loss-plot-tool]] — refresh_plot.sh patterns + iCloud gotchas
- [[personal/Knowledge/claude-loop-stay-alive-on-mac]] — keeping local /loop session alive

Last revised 14-06-2026 based on the 583M Muon warmup study (loop ran for 3+ days, 13 finished runs, 1 disk-full crash handled).
