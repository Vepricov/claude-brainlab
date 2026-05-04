# SSH Server Configuration

## Overview
The user's code and experiments live on remote SSH servers. When working with code, always check whether the task requires accessing a remote server. Prefer running code and experiments on the appropriate server rather than locally.

## Available Servers

Full server reference with GPU specs, CUDA mapping, and monitoring info:
`${OBSIDIAN_VAULT}/general/Knowledge/servers.md`

Quick summary (example template — replace with your own hosts):
- **<host_a>** — 8×A100-80GB (PCIe + SXM4 mix). CUDA indices ≠ physical indices — see your servers.md for canonical mapping.
- **<host_b>** — 4×A100-80GB SXM4
- **<host_c>** — H200 server, internal network only
- **<host_d>** — 2×A100

Replace these stubs with the hosts from your `~/.ssh/config`. Maintain a single canonical reference at `${OBSIDIAN_VAULT}/general/servers.md` and link to it from this rule.

## Usage Instructions

### Connecting and running commands
```bash
ssh <host> "command"          # run single command
ssh <host> "cd ~/project && python train.py"
```

### Syncing code to server
```bash
rsync -avz --exclude='.git' --exclude='__pycache__' \
    /local/path/ user@host:/remote/path/
```

### Checking GPU status before running
```bash
ssh <host> "nvidia-smi"
ssh <host> "nvidia-smi --query-gpu=name,memory.used,memory.free --format=csv"
```

### Long-running jobs
Use `tmux` or `screen` to keep processes alive after disconnect:
```bash
ssh <host> "tmux new-session -d -s train 'cd ~/project && python train.py'"
ssh <host> "tmux attach -t train"   # reattach later
```

## Default Behavior

- When the user says "run this" or "train" — ask which server to use if not specified
- When editing code locally and syncing — use rsync pattern above
- When reading experiment results — prefer `ssh host "cat results/..."` or rsync back
- Never hardcode server addresses in committed code — use config files or environment variables

## Project-Specific Server Config

Research projects live in `~/Papers/<project>/` and have a `.claude/CLAUDE.md` with a list of servers relevant to that project.

**When working inside a project (`~/Papers/<project>/`):**
1. Check `.claude/CLAUDE.md` for `## SSH Servers` section
2. If servers are listed there — use only those servers (subset of global `~/.ssh/config`)
3. Do NOT ask which server if it is already recorded in `.claude/CLAUDE.md`
4. If no server is specified by user and multiple are listed → show GPU load for all listed servers, then ask

**Code path convention:**
- Local code: `~/Papers/<project>/<code_name>/`
- Remote code: `~/<code_name>/` (same folder name, cloned to home on server)
- Run pattern: `ssh <host> "cd <code_name> && <command>"`

**Checking GPU load across project servers:**
```bash
# For each server listed in .claude/CLAUDE.md:
ssh <host> "nvidia-smi --query-gpu=index,memory.used,memory.free,utilization.gpu --format=csv,noheader"
```

**Available servers** are read from `~/.ssh/config` (Host entries). Do not hardcode them here.
