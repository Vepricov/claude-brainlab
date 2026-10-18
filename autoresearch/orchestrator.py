"""autoresearch-оркестратор: CLI + самоходный раунд. Проект-агностичный.

Корень проекта резолвится через --project | env AUTORESEARCH_PROJECT | обход вверх
от cwd (config.load). На серверах без research_cycle.py `round` делает все стадии,
кроме самого цикла derive/proof/code/critic, и печатает выбранные узлы — их прогоняет
сам оркестрирующий агент своими сабагентами.
"""
from __future__ import annotations

import argparse
from collections import deque
import inspect
import importlib.util
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from dataclasses import replace
from datetime import datetime
from typing import Any, Dict, List, Optional

from . import config as cfgmod
from .config import ARConfig
from . import graph_io as gio
from . import dedup_guard, selector, failure_taxonomy, autodraft, meta_review, evolution
from . import scoop_gate, reporter, paper, review_gate, supervisor, agent_worker, inbox, koi_ui
from . import graph_hygiene
from . import exp_spec

logger = logging.getLogger(__name__)


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _load_research_cycle(cfg: ARConfig):
    """Импортировать research_cycle.py по пути из конфига (если задан и существует).
    Пути проекта пробрасываются в env ДО импорта — research_cycle/agent_memory читают
    их оттуда (env-override), поэтому один и тот же код работает на любой машине/проекте."""
    p = cfg.research_cycle_path
    if not p or not os.path.exists(p):
        return None
    os.environ["AUTORESEARCH_GRAPH"] = cfg.graph
    os.environ["AUTORESEARCH_GDIR"] = cfg.gdir
    os.environ["AUTORESEARCH_WORKDIR"] = cfg.workdir
    os.environ["AUTORESEARCH_CLAUDE_MODEL"] = cfg.engines.claude_model
    if getattr(cfg, "store", "graph") == "koi":   # Phase 1.5: память слой-1 из koi-store
        os.environ["AUTORESEARCH_STORE"] = "koi"
        os.environ["AUTORESEARCH_KOI_DIR"] = cfg.koi_dir
    os.makedirs(cfg.workdir, exist_ok=True)
    spec = importlib.util.spec_from_file_location("research_cycle", p)
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["research_cycle"] = mod
    sys.path.insert(0, os.path.dirname(p))   # чтобы import agent_memory внутри сработал
    spec.loader.exec_module(mod)
    return mod


# ---------- отдельные операции ----------

def cmd_init(cfg_project: Optional[str], domain: str, name: str) -> None:
    """Создать per-project IdeaGraph/autoresearch.json (скаффолд)."""
    root = cfgmod.find_project_root(cfg_project)
    path = os.path.join(root, "IdeaGraph", cfgmod.CONFIG_BASENAME)
    if os.path.exists(path):
        print(f"уже существует: {path}"); return
    payload = {
        "project_name": name or os.path.basename(root),
        "domain": domain or cfgmod.DEFAULT_DOMAIN,
        "paths": {"workdir": ".research_loop", "paper": "paper"},
        "research_cycle_path": None,
        "engines": {},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"создан {path}\nотредактируй 'domain' и при наличии — 'research_cycle_path'.")


def cmd_migrate(cfg: ARConfig) -> None:
    data = gio.load_graph(cfg)
    nf = gio.ensure_fields(data)
    nc = failure_taxonomy.annotate(data)
    gio.save_graph(data, cfg, backup=True)
    gio.regen_canvas(cfg)
    print(f"migrate: +{nf} полей, classified {nc} мёртвых узлов. Бэкап graph.json.bak.")


def cmd_status(cfg: ARConfig) -> None:
    data = gio.load_graph(cfg)
    guard = dedup_guard.DedupGuard(data, cfg)
    print(f"проект: {cfg.project_name}  | дедуп-бэкенд: {guard.backend}  | корень: {cfg.project_root}")
    print(f"research_cycle: {'есть' if (cfg.research_cycle_path and os.path.exists(cfg.research_cycle_path)) else 'НЕТ (round без авто-цикла)'}")
    print("\n=== ФРОНТИР (selector #2) ===")
    for i, sc in enumerate(selector.score_nodes(data, cfg)[:10]):
        print(("→ " if i < cfg.selector.pick_k else "  ") + sc.explain())
    print("\n" + (failure_taxonomy.memory_block(data) or "провалов нет"))
    print(f"\nвыжило узлов (proven/confirmed/conditional): {len(autodraft.survived_nodes(data, cfg))}")


def _json_or_none(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _tail(path: str, n: int) -> List[str]:
    try:
        with open(os.path.expanduser(path), encoding="utf-8", errors="replace") as f:
            return list(deque(f, maxlen=max(1, n)))
    except OSError:
        return []


def _cards(status: Any) -> List[Dict[str, Any]]:
    if not isinstance(status, dict):
        return []
    agents = status.get("agents") or status.get("cards") or []
    if isinstance(agents, dict):
        return [v for v in agents.values() if isinstance(v, dict)]
    if isinstance(agents, list):
        return [v for v in agents if isinstance(v, dict)]
    return []


def _latest_review_fields(cfg: ARConfig) -> Dict[str, Any]:
    try:
        from .reporter import _reports_dir
        rd = _reports_dir(cfg)
        paths = [os.path.join(rd, f) for f in os.listdir(rd) if f.endswith(".review.md")]
        path = max(paths, key=os.path.getmtime) if paths else ""
        text = open(path, encoding="utf-8", errors="replace").read() if path else ""
    except OSError:
        return {}
    score = None
    sm = re.search(r"^\s*SCORE\s*:\s*(\d+)\s*$", text, flags=re.IGNORECASE | re.MULTILINE)
    if sm:
        try:
            score = int(sm.group(1))
        except ValueError:
            score = None
    weak: List[str] = []
    wm = re.search(r"^\s*WEAK_NODES\s*:\s*(.+?)\s*$", text,
                   flags=re.IGNORECASE | re.MULTILINE)
    if wm:
        raw = wm.group(1).strip()
        if raw and raw.lower() not in {"нет", "none", "-", "—"}:
            weak = [x.strip() for x in re.split(r"\s*,\s*", raw) if x.strip()]
    return {"path": path, "score": score, "weak_nodes": weak}


def _remote_path(path: Any) -> str:
    p = str(path or "").strip()
    if p.startswith("~/"):
        return p
    return shlex.quote(p)


def _ssh(server: str, command: str, timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", str(server), command],
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
    )


def _result_json_from_log(text: str) -> Optional[Dict[str, Any]]:
    for line in reversed((text or "").splitlines()):
        if line.startswith("RESULT_JSON:"):
            try:
                payload = json.loads(line.split(":", 1)[1].strip())
                return payload if isinstance(payload, dict) else None
            except ValueError:
                return None
    return None


def _emp_verdict_from_log(text: str) -> str:
    for line in reversed((text or "").splitlines()):
        if line.startswith("EMP_VERDICT:"):
            return line.split(":", 1)[1].strip().lower()
    return ""


def _decisive_result_for_kind(kind: str, payload: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(payload, dict):
        return False
    final = payload.get("FINAL")
    if kind == "rho_predictor":
        return isinstance(final, dict) and "rho_grad_weighted" in final and "per_layer" in final
    if kind == "llama_gnmuon_audit":
        return (
            isinstance(final, dict)
            and "primary_confirmed" in final
            and "Delta_C1" in final
            and "target_noninferior" in final
        )
    if kind == "llama_proxy_falsification_grid":
        return (
            isinstance(final, dict)
            and "proxy_primary_confirmed" in final
            and "proxy_lmo_delta_spearman" in final
            and "Delta_C1" in final
            and "wallclock_edge" in final
        )
    if kind == "llama_fixed_baseline_audit":
        return (
            isinstance(final, dict)
            and "fixed_baseline_primary_confirmed" in final
            and "fixed_baseline_summary" in final
            and "fixed_baseline_edges" in final
            and "Delta_C1" in final
            and "wallclock_edge" in final
        )
    if kind == "llama_checkpoint_pool_selector":
        return (
            isinstance(final, dict)
            and "primary_confirmed" in final
            and "Delta_C1_vs_controls" in final
            and "target_noninferior" in final
        )
    if kind == "llama_firewall_calibration_audit":
        return (
            isinstance(final, dict)
            and "calibration_primary_confirmed" in final
            and "calibration_false_accept_overall" in final
            and "Delta_C1_vs_controls" in final
            and "wallclock_edge_vs_controls" in final
            and "target_noninferior" in final
        )
    if kind == "llama_alignment_bridge_audit":
        return (
            isinstance(final, dict)
            and "alignment_primary_confirmed" in final
            and "alignment_Delta_C1" in final
            and "alignment_target_loss_gap" in final
            and "alignment_pairs" in final
        )
    if kind in {"gnmuon_wallclock", "gnmuon_matched_target"}:
        return bool(final or payload)
    return bool(final or payload)


def _proc_env(pid: int) -> Dict[str, str]:
    env_path = f"/proc/{pid}/environ"
    try:
        raw = open(env_path, "rb").read()
    except OSError:
        return {}
    out: Dict[str, str] = {}
    for chunk in raw.split(b"\0"):
        if not chunk or b"=" not in chunk:
            continue
        k, v = chunk.split(b"=", 1)
        try:
            out[k.decode("utf-8", "replace")] = v.decode("utf-8", "replace")
        except UnicodeDecodeError:
            continue
    return out


def _doctor_process_findings(
    cfg: ARConfig,
    log_file: str,
    expect_workers: int,
    expect_tmux: str = "",
) -> tuple[List[Dict[str, str]], Dict[str, Any]]:
    findings: List[Dict[str, str]] = []

    def add(severity: str, code: str, detail: str) -> None:
        findings.append({"severity": severity, "code": code, "detail": detail})

    try:
        ps = subprocess.run(
            ["ps", "-eo", "pid=,args="],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        add("error", "process_probe_failed", f"cannot run ps: {e}")
        return findings, {"error": str(e)}

    root = os.path.abspath(cfg.project_root)
    self_pid = os.getpid()
    team: List[Dict[str, Any]] = []
    orchestrators: List[Dict[str, Any]] = []
    claude_processes: List[Dict[str, Any]] = []
    for line in (ps.stdout or "").splitlines():
        m = re.match(r"\s*(\d+)\s+(.*)", line)
        if not m:
            continue
        pid = int(m.group(1))
        args = m.group(2)
        if pid == self_pid:
            continue
        # Ignore tmux/bash wrapper command lines that merely contain the python
        # launch string; the runtime/env checks must apply to the real Python
        # process that owns the loop.
        is_python_orchestrator = bool(re.match(r"\s*(?:\S*/)?python3?\s+-m\s+autoresearch\.orchestrator\b", args))
        if is_python_orchestrator and root in args and " doctor" not in args:
            rec = {"pid": pid, "args": args, "env": _proc_env(pid)}
            orchestrators.append(rec)
            if " team " in f" {args} ":
                team.append(rec)
        if re.search(r"(^|[\s/])(claude|claude-code)(\s|$)", args, re.IGNORECASE):
            if "autoresearch.orchestrator" not in args:
                claude_processes.append({"pid": pid, "args": args[:220]})

    if expect_workers > 0 and not team:
        add("error", "orchestrator_process_missing",
            f"no live autoresearch team process for project {root}")
    for rec in team:
        args = rec["args"]
        env = rec.get("env") or {}
        if expect_workers > 0:
            worker_ok = (
                f"--workers {expect_workers}" in args
                or f"--workers={expect_workers}" in args
            )
            if not worker_ok:
                add("error", "worker_count_mismatch",
                    f"team pid {rec['pid']} does not run with --workers {expect_workers}: {args[:240]}")
        if env.get("AUTORESEARCH_DISABLE_CLAUDE") != "1":
            add("error", "claude_not_disabled",
                f"team pid {rec['pid']} lacks AUTORESEARCH_DISABLE_CLAUDE=1")
    if claude_processes:
        sample = "; ".join(f"{p['pid']}:{p['args']}" for p in claude_processes[:3])
        add("error", "real_claude_process",
            f"real Claude process(es) present while Codex-only loop is expected: {sample}")

    tmux_name = expect_tmux.strip()
    if not tmux_name:
        base = os.path.basename(log_file or "")
        if base.endswith("-codex.log"):
            tmux_name = base[:-len("-codex.log")]
    tmux_alive: Optional[bool] = None
    if tmux_name:
        try:
            tmux = subprocess.run(
                ["tmux", "has-session", "-t", tmux_name],
                capture_output=True,
                text=True,
                timeout=10,
            )
            tmux_alive = tmux.returncode == 0
            if not tmux_alive:
                add("error", "tmux_session_missing",
                    f"expected tmux session {tmux_name!r} is not alive")
        except (subprocess.TimeoutExpired, OSError) as e:
            add("error", "tmux_probe_failed", f"cannot probe tmux session {tmux_name!r}: {e}")

    return findings, {
        "team_pids": [rec["pid"] for rec in team],
        "orchestrator_pids": [rec["pid"] for rec in orchestrators],
        "disable_claude": all((rec.get("env") or {}).get("AUTORESEARCH_DISABLE_CLAUDE") == "1"
                              for rec in team) if team else False,
        "tmux": tmux_name,
        "tmux_alive": tmux_alive,
        "claude_processes": claude_processes[:5],
    }


def _doctor_experiment_runtime_findings(
    cfg: ARConfig,
    data: Dict[str, Any],
    status: Dict[str, Any],
) -> tuple[List[Dict[str, str]], Dict[str, Any]]:
    findings: List[Dict[str, str]] = []

    def add(severity: str, code: str, detail: str) -> None:
        findings.append({"severity": severity, "code": code, "detail": detail})

    exp_dir = os.path.join(cfg.workdir, ".run", "experiments")
    records: List[Dict[str, Any]] = []
    unreadable = 0
    if os.path.isdir(exp_dir):
        for fn in sorted(os.listdir(exp_dir)):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(exp_dir, fn)
            try:
                rec = json.load(open(path, encoding="utf-8"))
                if isinstance(rec, dict):
                    rec["_doctor_file"] = fn
                    records.append(rec)
            except (OSError, ValueError) as e:
                unreadable += 1
                add("error", "experiment_pending_json", f"cannot read pending EXP_SPEC {fn}: {e}")
    by = gio.index(data)
    cards = _cards(status)
    exp_cards = [c for c in cards if "экспериментатор" in str(c.get("role") or "").lower()]
    generic_exp = [c for c in exp_cards if c.get("agent") == "agent-experimenter"]
    running_records = [r for r in records if r.get("status") == "running"]
    waiting_records = [r for r in records if r.get("status") == "waiting"]
    done_pending = 0
    stale_logs = 0
    mechanical_invalid = 0
    bad_no_signal = 0
    now = time.time()

    for rec in records:
        nid = str(rec.get("nid") or rec.get("_doctor_file") or "?")
        kind = str(rec.get("kind") or (rec.get("exp_spec") or {}).get("kind") or "")
        spec = rec.get("exp_spec") if isinstance(rec.get("exp_spec"), dict) else {}
        age = max(0.0, now - float(rec.get("started_at") or now))
        if not spec:
            add("error", "experiment_pending_spec", f"pending {nid} has no machine-readable exp_spec")
        else:
            try:
                exp_spec.canonicalize(
                    spec,
                    context=f"doctor pending {nid} idea={rec.get('idea','')}",
                    exp_kind=getattr(cfg, "exp_kind", ""),
                )
            except ValueError as e:
                add("error", "experiment_pending_spec", f"pending {nid} has invalid EXP_SPEC: {e}")
        node = by.get(nid) or {}
        if node and (node.get("exp_refuted") or node.get("exp_confirmed")):
            add("error", "experiment_pending_completed_node",
                f"pending file still exists for already finalized node {nid}")
        if rec.get("status") == "waiting" and age > 1800:
            add("warn", "experiment_waiting_gpu",
                f"pending {nid} has waited for GPU for {int(age/60)}m")
        if rec.get("status") != "running":
            continue
        server = str(rec.get("server") or "")
        log = str(rec.get("log") or "")
        done = str(rec.get("done") or "")
        tmux = str(rec.get("tmux") or "")
        if not (server and log and done and tmux):
            add("error", "experiment_running_record",
                f"running pending {nid} lacks server/log/done/tmux fields")
            continue
        try:
            tmux_probe = _ssh(
                server,
                f"tmux has-session -t {shlex.quote(tmux)} 2>/dev/null && echo TMUX_OK || echo TMUX_NO",
                timeout=20,
            )
            state_probe = _ssh(
                server,
                "now=$(date +%s); "
                f"if test -f {_remote_path(done)}; then echo DONE=1; echo DONE_AGE=$((now-$(stat -c %Y {_remote_path(done)}))); else echo DONE=0; fi; "
                f"if test -f {_remote_path(log)}; then echo LOG=1; echo LOG_AGE=$((now-$(stat -c %Y {_remote_path(log)}))); echo LOG_SIZE=$(stat -c %s {_remote_path(log)}); else echo LOG=0; fi",
                timeout=20,
            )
            tail_probe = _ssh(server, f"tail -120 {_remote_path(log)} 2>/dev/null", timeout=25)
        except (subprocess.TimeoutExpired, OSError) as e:
            add("error", "experiment_probe_failed", f"cannot probe running pending {nid} on {server}: {e}")
            continue
        meta: Dict[str, str] = {}
        for line in state_probe.stdout.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                meta[k.strip()] = v.strip()
        text = tail_probe.stdout or ""
        tmux_ok = "TMUX_OK" in (tmux_probe.stdout or "")
        done_exists = meta.get("DONE") == "1"
        log_exists = meta.get("LOG") == "1"
        try:
            done_age = int(meta.get("DONE_AGE") or "0")
        except ValueError:
            done_age = 0
        try:
            log_age = int(meta.get("LOG_AGE") or "0")
        except ValueError:
            log_age = 0
        try:
            log_size = int(meta.get("LOG_SIZE") or "0")
        except ValueError:
            log_size = 0
        if not tmux_ok and not done_exists and age > 60:
            add("error", "experiment_tmux_dead",
                f"pending {nid} is running but tmux {tmux} is absent on {server} and no done marker exists")
        if not log_exists or (log_size == 0 and age > 60):
            add("error", "experiment_log_missing", f"pending {nid} has no growing log on {server}: {log}")
        if log_age > 900 and not done_exists:
            stale_logs += 1
            add("error", "experiment_log_stale",
                f"pending {nid} log has not updated for {int(log_age/60)}m and EXP_DONE is absent")
        elif log_age > 300 and not done_exists:
            stale_logs += 1
            add("warn", "experiment_log_stale",
                f"pending {nid} log has not updated for {int(log_age/60)}m")
        bad_runtime = re.search(
            r"Traceback|RuntimeError|ImportError|ModuleNotFoundError|OSError|CUDA out of memory|"
            r"not a valid model identifier|numpy\.dtype size changed|binary incompatibility",
            text,
            re.IGNORECASE,
        )
        if bad_runtime and done_exists:
            mechanical_invalid += 1
            add("error", "experiment_mechanical_invalid",
                f"pending {nid} finished with mechanical runtime error in log")
        elif bad_runtime:
            add("warn", "experiment_runtime_warning",
                f"pending {nid} log contains runtime error text; watcher should fix or mark invalid")
        if str(getattr(cfg, "exp_kind", "") or "").strip().lower() == "llama":
            if re.search(r"EleutherAI/pythia-|\bpythia-|\bPythia\b", text):
                add("error", "experiment_policy_runtime",
                    f"pending {nid} log mentions legacy Pythia under exp_kind=llama")
        if done_exists:
            done_pending += 1
            if done_age > 240:
                add("error", "experiment_done_unprocessed",
                    f"pending {nid} has EXP_DONE marker for {int(done_age/60)}m but supervisor has not finalized it")
            for marker in ("RESULT_JSON:", "EMP_VERDICT:", "EXP_DONE"):
                if marker not in text:
                    add("error", "experiment_missing_marker",
                        f"pending {nid} done log lacks marker {marker}")
            verdict = _emp_verdict_from_log(text)
            payload = _result_json_from_log(text)
            if verdict == "no_signal" and not _decisive_result_for_kind(kind, payload):
                bad_no_signal += 1
                add("error", "experiment_no_signal_undecisive",
                    f"pending {nid} returned no_signal without decisive typed RESULT_JSON fields")
            if verdict == "invalid":
                mechanical_invalid += 1
                add("error", "experiment_invalid_done",
                    f"pending {nid} returned EMP_VERDICT=invalid; inspect log and mark mechanical_invalid_exp")

    if records:
        for c in generic_exp:
            detail = str(c.get("detail") or "")
            stage = str(c.get("stage") or "")
            if stage == "idle" and ("нет eligible" in detail or "GPU idle" in detail):
                add("error", "experimenter_card_stale",
                    "agent-experimenter says GPU idle while pending EXP_SPEC files exist")
    else:
        for c in generic_exp:
            detail = str(c.get("detail") or "")
            stage = str(c.get("stage") or "")
            if stage in {"experiment", "waiting_gpu"} or "GPU busy" in detail:
                add("error", "experimenter_card_stale",
                    "agent-experimenter says GPU busy/waiting while pending_count=0")
    for c in exp_cards:
        agent = str(c.get("agent") or "")
        if agent == "agent-experimenter":
            continue
        nid = str(c.get("node") or "").strip()
        stage = str(c.get("stage") or "")
        detail = str(c.get("detail") or "")
        if stage == "experiment" and not any(str(r.get("nid") or "") == nid for r in records):
            add("error", "experiment_card_stale",
                f"{agent} still shows stage=experiment but no pending record exists")
        if stage == "failed" and "no_signal" in detail:
            node = by.get(nid) or {}
            if not node.get("exp_refuted"):
                add("error", "experiment_card_graph_mismatch",
                    f"{agent} reports no_signal but graph node {nid} is not exp_refuted")
    report_path = os.path.join(cfg.workdir, ".run", "agents", "_report.json")
    legacy_report_path = os.path.join(cfg.workdir, ".run", "_report.json")
    status_report = status.get("report") if isinstance(status, dict) else {}
    actual_report = _json_or_none(report_path) or {}
    if isinstance(status_report, dict) and isinstance(actual_report, dict):
        if bool(status_report.get("active")) != bool(actual_report.get("active")):
            add("error", "dashboard_report_mismatch",
                "agents-status.json report banner disagrees with .run/agents/_report.json")
    legacy_report = _json_or_none(legacy_report_path) or {}
    if isinstance(legacy_report, dict) and legacy_report:
        try:
            legacy_newer = os.path.getmtime(legacy_report_path) > os.path.getmtime(report_path)
        except OSError:
            legacy_newer = False
        if legacy_newer and bool(legacy_report.get("active")) != bool(actual_report.get("active")):
            add("error", "report_legacy_shadow",
                ".run/_report.json is newer than .run/agents/_report.json and disagrees; "
                "some writer is using the wrong report path")
    report = actual_report if isinstance(actual_report, dict) else {}
    if isinstance(report, dict) and report.get("active"):
        try:
            report_age = int(now - os.path.getmtime(report_path))
        except OSError:
            report_age = 0
        if report_age > 2400:
            add("error", "report_banner_stale",
                f"report banner active for {int(report_age/60)}m; likely stale _report.json")
        elif report_age > 1200:
            add("warn", "report_banner_long",
                f"report banner active for {int(report_age/60)}m")

    summary = {
        "pending_count": len(records),
        "running": len(running_records),
        "waiting": len(waiting_records),
        "done_pending": done_pending,
        "stale_logs": stale_logs,
        "mechanical_invalid": mechanical_invalid,
        "bad_no_signal": bad_no_signal,
        "unreadable": unreadable,
        "counter": status.get("experiments") if isinstance(status, dict) else None,
        "status_report": status_report,
        "actual_report": actual_report,
        "legacy_report": legacy_report,
    }
    return findings, summary


def _doctor_experiment_pressure_findings(
    cfg: ARConfig,
    data: Dict[str, Any],
    status: Dict[str, Any],
    experiment_summary: Dict[str, Any],
) -> tuple[List[Dict[str, str]], Dict[str, Any]]:
    findings: List[Dict[str, str]] = []

    def add(severity: str, code: str, detail: str) -> None:
        findings.append({"severity": severity, "code": code, "detail": detail})

    pending = int(experiment_summary.get("pending_count") or 0)
    try:
        cand = supervisor._pick_confirm_candidate(data, cfg)
    except Exception:
        cand = None
    try:
        last_astar = status.get("last_astar")
        if last_astar is None and status.get("scores"):
            last_astar = status["scores"][-1].get("score")
        last_astar = int(last_astar) if last_astar is not None else None
    except (TypeError, ValueError, KeyError):
        last_astar = None
    cornerstone = ""
    cornerstone_kind = ""
    kind_refuted: List[str] = []
    kind_confirmed: List[str] = []
    try:
        cornerstone = supervisor._latest_feedback_cornerstone(cfg)
        cornerstone_kind = exp_spec.infer_kind(cornerstone) if cornerstone else ""
    except Exception:
        cornerstone_kind = ""
    if cornerstone_kind:
        for n in data.get("nodes", []):
            spec = n.get("exp_spec") if isinstance(n.get("exp_spec"), dict) else {}
            if spec.get("kind") != cornerstone_kind:
                continue
            nid = str(n.get("id") or "")
            if n.get("exp_refuted"):
                kind_refuted.append(nid)
            if n.get("exp_confirmed"):
                kind_confirmed.append(nid)
    try:
        pressure_block = supervisor._experiment_pressure_block(data, cfg)
    except Exception:
        pressure_block = ""
    if cornerstone_kind and kind_refuted and pressure_block:
        contradictory = (
            f"typed EXP_SPEC `{cornerstone_kind}`" in pressure_block
            and "`NO_EXP_NEEDED` is not acceptable" in pressure_block
            and f"kind `{cornerstone_kind}`" in pressure_block
        )
        if contradictory:
            add(
                "error",
                "experiment_pressure_duplicate_refuted_contradiction",
                "Pressure feedback tells agents to request an already-refuted "
                f"EXP_SPEC kind {cornerstone_kind}; it must instead force a negative "
                "writeup or a materially different typed claim."
            )
    actual_report = experiment_summary.get("actual_report")
    report_active = bool(isinstance(actual_report, dict) and actual_report.get("active"))
    latest_review = _latest_review_fields(cfg)
    critic_card = next((c for c in _cards(status) if c.get("agent") == "A*-критик-отчёта"), {})
    if latest_review and critic_card and not report_active:
        review_score = latest_review.get("score")
        card_astar = str(critic_card.get("astar") or "").strip()
        if review_score is not None and card_astar and card_astar != str(review_score):
            add(
                "warn",
                "report_critic_card_mismatch",
                f"Latest review score is {review_score}, but A*-critic dashboard card astar={card_astar}."
            )
        review_weak = list(latest_review.get("weak_nodes") or [])
        if review_weak:
            card_text = " ".join(str(critic_card.get(k) or "") for k in ("detail", "short", "node"))
            missing = [w for w in review_weak if w not in card_text]
            if missing:
                add(
                    "warn",
                    "report_critic_card_mismatch",
                    "Latest review WEAK_NODES are not reflected in the A*-critic dashboard card: "
                    + ", ".join(missing[:8])
                )
    try:
        fresh_refuted = supervisor._fresh_refuted_ids(data, cfg)
    except Exception:
        fresh_refuted = []
    if pending == 0 and cand is None and last_astar is not None and last_astar < 8:
        try:
            pressure_weak = selector.pressure_weak_nodes(cfg)
            pressure_prune = selector.pressure_prune_nodes(cfg)
            pressure_action = selector.pressure_action_targets(cfg)
            pressure_unresolved = selector.pressure_unresolved_targets(data, cfg)
            selected_now = [s.node_id for s in selector.score_nodes(data, cfg)[:cfg.selector.pick_k]]
            selected_norm = {
                nid[len("pressure_"):] if str(nid).startswith("pressure_") else nid
                for nid in selected_now
            }
            active_now = [str(nid) for nid in gio.load_active(cfg)]
            active_norm_by_id = {
                nid: (nid[len("pressure_"):] if nid.startswith("pressure_") else nid)
                for nid in active_now
            }
            active_norm = set(active_norm_by_id.values())
            unresolved_set = set(pressure_unresolved)
            active_off_pressure = [
                nid for nid, norm in active_norm_by_id.items()
                if unresolved_set and norm not in unresolved_set
            ]
        except Exception:
            pressure_weak = []
            pressure_prune = []
            pressure_action = []
            pressure_unresolved = []
            selected_now = []
            selected_norm = set()
            active_norm = set()
            active_now = []
            active_off_pressure = []
        if report_active:
            add(
                "warn",
                "experiment_pressure_report_active",
                "GPU lane is idle because a fresh A*-report is currently being generated; "
                "wait for that report/pivot before expecting another typed EXP_SPEC."
            )
        elif fresh_refuted:
            add(
                "warn",
                "experiment_pressure_waiting_report",
                "GPU lane is idle because fresh typed EXP_SPEC result(s) are newer than "
                "the latest report and must be folded into an A*-pivot first: "
                + ", ".join(fresh_refuted[:5])
            )
        else:
            detail = (
                f"A*={last_astar}/10, GPU lane idle, and confirm_candidate=null. "
                "This is not a random-harness bug, but active branches must either "
                "produce typed EXP_SPEC_REQUEST through the gate or explicitly justify NO_EXP_NEEDED."
            )
            if cornerstone_kind:
                detail += f" Latest reviewer experiment demand maps to {cornerstone_kind}."
                if kind_refuted:
                    detail += f" Existing refuted node(s): {', '.join(kind_refuted[:5])}."
                if kind_confirmed:
                    detail += f" Existing confirmed node(s): {', '.join(kind_confirmed[:5])}."
            add("warn", "experiment_pressure_idle", detail)
            unresolved_active = bool(
                pressure_unresolved
                and set(pressure_unresolved).issubset(active_norm)
            )
            if pressure_unresolved and pressure_action and not unresolved_active and not (set(pressure_action) & selected_norm):
                add(
                    "warn",
                    "experiment_pressure_weak_routing",
                    "Latest no-cornerstone A* feedback names weak nodes "
                    f"{', '.join(pressure_weak[:8])}, but selector top-k is "
                    f"{', '.join(selected_now[:8])}. Pressure routing should target "
                    f"{', '.join(pressure_action[:8])} before drifting to unrelated theory nodes."
                )
            if pressure_prune:
                bad_active = [
                    nid for nid in active_now
                    if str(nid).startswith("pressure_")
                    and str(nid)[len("pressure_"):] in set(pressure_prune)
                ]
                bad_selected = [
                    nid for nid in selected_now
                    if str(nid).startswith("pressure_")
                    and str(nid)[len("pressure_"):] in set(pressure_prune)
                ]
                if bad_active or bad_selected:
                    add(
                        "error",
                        "experiment_pressure_prune_misrouted",
                        "Latest A* review says to prune/drop weak nodes "
                        f"{', '.join(pressure_prune[:8])}, but pressure routing is still "
                        "sending workers to repair them. Route this feedback through "
                        f"{', '.join(pressure_action[:4]) or 'pressure_scope_pivot'} instead. "
                        f"active={', '.join(bad_active[:6]) or '-'}; "
                        f"topk={', '.join(bad_selected[:6]) or '-'}."
                    )
            if pressure_unresolved and active_off_pressure:
                add(
                    "error",
                    "experiment_pressure_active_mismatch",
                    "Unresolved pressure targets exist, but active workers include off-target nodes "
                    f"{', '.join(active_off_pressure[:8])}; active workers must converge to "
                    f"{', '.join(pressure_unresolved[:8])}. This usually means stale pressure active slots "
                    "survived a new A* prune/scope-pivot review."
                )
    else:
        pressure_weak = []
        pressure_prune = []
        pressure_action = []
        pressure_unresolved = []
        selected_now = []
        active_now = []
        active_off_pressure = []
    return findings, {
        "last_astar": last_astar,
        "pending_count": pending,
        "confirm_candidate": cand.get("id") if isinstance(cand, dict) else None,
        "confirm_kind": (cand.get("exp_spec") or {}).get("kind")
        if isinstance(cand, dict) and isinstance(cand.get("exp_spec"), dict) else None,
        "latest_cornerstone_kind": cornerstone_kind,
        "latest_cornerstone": cornerstone[:300],
        "latest_kind_refuted": kind_refuted[:10],
        "latest_kind_confirmed": kind_confirmed[:10],
        "fresh_refuted_since_report": fresh_refuted[:10],
        "report_active": report_active,
        "pressure_block": bool(pressure_block),
        "pressure_weak_nodes": pressure_weak[:10],
        "pressure_prune_nodes": pressure_prune[:10],
        "pressure_action_targets": pressure_action[:10],
        "pressure_unresolved_targets": pressure_unresolved[:10],
        "pressure_selector_topk": selected_now[:10],
        "pressure_active": active_now[:10],
        "pressure_active_offtarget": active_off_pressure[:10],
    }


def _doctor_node_attempt_findings(
    cfg: ARConfig,
    data: Dict[str, Any],
) -> tuple[List[Dict[str, str]], Dict[str, Any]]:
    findings: List[Dict[str, str]] = []

    def add(severity: str, code: str, detail: str) -> None:
        findings.append({"severity": severity, "code": code, "detail": detail})

    relevant = {str(nid) for nid in gio.load_active(cfg)}
    try:
        relevant.update(str(s.node_id) for s in selector.score_nodes(data, cfg)[:20])
    except Exception:
        pass
    try:
        for weak in selector.pressure_weak_nodes(cfg):
            relevant.add(str(weak))
            relevant.add(f"pressure_{weak}")
        for target in selector.pressure_action_targets(cfg):
            relevant.add(str(target))
            relevant.add(f"pressure_{target}")
    except Exception:
        pass

    checked: List[Dict[str, Any]] = []
    base = os.path.join(cfg.workdir, "memory", "nodes")
    gate_repo = cfg.gate_repo
    if not gate_repo and os.path.isdir("/root/research.git"):
        gate_repo = "/root/research.git"
    if not relevant or not os.path.isdir(base):
        return findings, {"checked": checked}

    for nid in sorted(relevant):
        attempts = os.path.join(base, re.sub(r"[^A-Za-z0-9_.-]+", "_", nid).strip("._-") or "node",
                                "attempts.jsonl")
        if not os.path.exists(attempts):
            continue
        rows: List[Dict[str, Any]] = []
        try:
            with open(attempts, encoding="utf-8") as f:
                for line in f:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue
        if not rows:
            continue
        last = rows[-1]
        if last.get("status") != "passed":
            checked.append({"node": nid, "status": last.get("status"), "ts": last.get("ts")})
            continue
        commit = str(last.get("commit") or "").strip()
        tree_branch = str(last.get("tree_branch") or "").strip()
        gate_summary = str(last.get("gate_summary") or "").strip()
        row = {"node": nid, "status": "passed", "ts": last.get("ts"),
               "commit": commit[:12], "tree_branch": tree_branch}
        checked.append(row)
        if not gate_summary:
            add("error", "node_attempt_false_pass",
                f"{nid} last attempt is passed but gate_summary is empty; PASS feedback was lost.")
        if not commit:
            add("error", "node_attempt_false_pass",
                f"{nid} last attempt is passed but has no commit.")
            continue
        if not tree_branch:
            add("error", "node_attempt_false_pass",
                f"{nid} last attempt is passed but has no tree_branch.")
            continue
        if gate_repo:
            ref = f"refs/heads/{tree_branch}"
            probe = subprocess.run(
                ["git", f"--git-dir={gate_repo}", "rev-parse", "--verify", ref],
                capture_output=True, text=True, errors="replace", timeout=20)
            if probe.returncode != 0:
                add("error", "node_attempt_false_pass",
                    f"{nid} last attempt is passed at {commit[:12]}, but {tree_branch} is missing in gate repo.")
            else:
                actual = (probe.stdout or "").strip()
                row["tree_commit"] = actual[:12]
                if actual != commit:
                    add("error", "node_attempt_false_pass",
                        f"{nid} last attempt is passed at {commit[:12]}, but {tree_branch} points to {actual[:12]}.")

    return findings, {"checked": checked[:30]}


def _doctor_prompt_smoke(cfg: ARConfig) -> Optional[str]:
    """Fast no-LLM smoke for prompt .format() bugs in agent_worker._produce.

    It intentionally forces the continuation path because long proofs often enter
    that branch, and it must preserve the experiment-contract requirement too.
    """
    calls: List[str] = []

    def fake_call(prompt: str) -> str:
        calls.append(prompt)
        if "ЗАДАЧА: напиши verify.py" in prompt:
            return '```python\nprint("ok")\n```'
        if "Это ПРОДОЛЖЕНИЕ" in prompt:
            return ("```markdown\nfinished. QED\n\n"
                    "NO_EXP_NEEDED: continuation smoke\n```")
        return "```markdown\n# Theorem\nProof starts but is truncated"

    try:
        agent_worker._produce(
            {"id": "doctor-smoke", "short": "smoke", "idea": "idea", "open": "", "plan": ""},
            "memory", cfg, fake_call)
    except Exception as e:
        return f"agent_worker._produce prompt smoke failed: {type(e).__name__}: {e}"
    try:
        worker_src = inspect.getsource(agent_worker.work_node)
    except OSError as e:
        return f"agent_worker.work_node source smoke failed: {e}"
    if "LOCAL_VERIFY_CHECK" not in worker_src or "review_gate._verify_sanity" not in worker_src:
        return "agent_worker.work_node lacks local verify.py preflight before git push"
    try:
        with tempfile.TemporaryDirectory() as td:
            gate_repo = os.path.join(td, "gate.git")
            subprocess.run(["git", "init", "--bare", gate_repo],
                           check=True, capture_output=True, text=True)
            smoke_cfg = replace(
                cfg,
                workdir=os.path.join(td, "work"),
                active=os.path.join(td, "active.json"),
            )
            os.makedirs(smoke_cfg.workdir, exist_ok=True)
            smoke_node = {
                "id": "doctor-local-verify-smoke",
                "short": "local verify smoke",
                "idea": "smoke",
                "open": "",
                "plan": "",
            }

            def bad_verify_call(prompt: str) -> str:
                if "ЗАДАЧА: напиши verify.py" in prompt:
                    return '```python\nprint(f"unterminated)\n```'
                return (
                    "```markdown\nTheorem. Smoke.\nProof. Trivial. QED\n\n"
                    "NO_EXP_NEEDED: smoke local verifier guard\n```"
                )

            smoke_res = agent_worker.work_node(
                smoke_node,
                "memory",
                smoke_cfg,
                gate_repo,
                max_rounds=1,
                call=bad_verify_call,
                lineage_ids=[smoke_node["id"]],
            )
            if not smoke_res.get("local_verify_failed") or smoke_res.get("pushed"):
                return (
                    "agent_worker local verify preflight smoke failed: "
                    f"expected local_verify_failed and pushed=false, got {smoke_res}"
                )
    except Exception as e:
        return f"agent_worker local verify preflight smoke crashed: {type(e).__name__}: {e}"
    if not calls or "EXP_SPEC_REQUEST: {...}" not in calls[0]:
        return "agent_worker._produce prompt smoke did not expose literal EXP_SPEC_REQUEST:{...}"
    if str(getattr(cfg, "exp_kind", "") or "").strip().lower() == "llama":
        contaminated = [i for i, p in enumerate(calls) if re.search(r"pythia", p, re.IGNORECASE)]
        if contaminated:
            return f"llama-policy writer prompt contains legacy checkpoint family text at calls={contaminated}"
    cont_prompts = [p for p in calls if "Это ПРОДОЛЖЕНИЕ" in p]
    if not cont_prompts:
        return "agent_worker._produce prompt smoke did not exercise continuation path"
    if "EXP_SPEC_REQUEST: {...}" not in cont_prompts[0] or "NO_EXP_NEEDED:" not in cont_prompts[0]:
        return "continuation prompt does not require EXP_SPEC_REQUEST/NO_EXP_NEEDED"
    long_derive = ("proof line\n" * 700) + "\nQED\n\nNO_EXP_NEEDED: long-tail contract smoke\n"
    prompt_diff = "=== derive.md ===\n" + long_derive[:6000]
    full_diff = "=== derive.md ===\n" + long_derive

    def gate_call(prompt: str) -> str:
        if (str(getattr(cfg, "exp_kind", "") or "").strip().lower() == "llama"
                and re.search(r"pythia", prompt, re.IGNORECASE)):
            return "FEEDBACK: llama-policy gate prompt contains legacy checkpoint family text\nGATE_VERDICT: FAIL"
        if ("[EXPERIMENT_CONTRACT_VISIBLE_TO_JUDGES" not in prompt
                or "NO_EXP_NEEDED: long-tail contract smoke" not in prompt
                or prompt.count("NO_EXP_NEEDED: long-tail contract smoke") != 1):
            return "FEEDBACK: long-tail contract is not visible to gate judge\nGATE_VERDICT: FAIL"
        if "=== derive.md ===\n[EXPERIMENT_CONTRACT_VISIBLE_TO_JUDGES" not in prompt:
            return "FEEDBACK: contract marker must be visible inside derive.md section\nGATE_VERDICT: FAIL"
        derive_part = ""
        if "=== derive.md ===" in prompt:
            derive_part = prompt.split("=== derive.md ===", 1)[1].split("\n=== ", 1)[0]
        if "omitted middle for gate prompt" in derive_part:
            return "FEEDBACK: derive.md was omitted inside gate prompt\nGATE_VERDICT: FAIL"
        if "СОСТЯЗАТЕЛЬНЫЙ КРИТИК" in prompt:
            return "A_STAR: 6\nFEEDBACK: ok\nGATE_VERDICT: PASS"
        return "FEEDBACK: ok\nGATE_VERDICT: PASS"

    status, fb = review_gate.review(prompt_diff, "", cfg, call=gate_call,
                                    node="doctor-smoke",
                                    contract_text=full_diff)
    if status != "pass":
        return f"review_gate long-tail contract smoke failed: {status}: {fb}"
    long_verify = (
        "print('verify-start')\n"
        + ("# filler keeps verifier valid while forcing prompt excerpting\n" * 2500)
        + "print('verify-end')\n"
    )
    derive_contract = "Theorem. Long verifier smoke.\n\nNO_EXP_NEEDED: long-tail contract smoke\n"
    excerpted_verify_diff = (
        "=== derive.md ===\n" + derive_contract + "\n\n"
        "=== verify.py ===\n" + review_gate._excerpt(long_verify, review_gate.OTHER_FILE_PROMPT_LIMIT)
    )
    status, fb = review_gate.review(
        excerpted_verify_diff,
        "# verify.py (exit 0)\nverify-start\nverify-end",
        cfg,
        call=gate_call,
        node="doctor-long-verify-excerpt",
        contract_text=derive_contract,
        verify_text=long_verify,
    )
    if status != "pass":
        return f"review_gate long-verify full-text sanity smoke failed: {status}: {fb}"
    transcript_verify = (
        "=== derive.md ===\n"
        "Theorem. A local smoke claim.\n\n"
        "NO_EXP_NEEDED: local smoke\n\n"
        "=== verify.py ===\n"
        "# result=PASS\n"
        "# This is only a transcript, not executable verification.\n"
    )
    status, fb = review_gate.review(
        transcript_verify,
        "# verify.py (exit 0)",
        cfg,
        call=lambda _prompt: "FEEDBACK: should not be called\nGATE_VERDICT: PASS",
        node="doctor-comment-only-verify",
        contract_text="Theorem.\n\nNO_EXP_NEEDED: local smoke\n",
    )
    if status != "fail" or "no module-level executable verification" not in fb:
        return f"review_gate comment-only verify smoke failed: {status}: {fb}"
    try:
        report_smoke = {
            "id": "doctor-report-protocol-smoke",
            "exp_refuted_summary": "Delta_C1: mean=-0.1, CI=[-0.2,-0.01]",
            "exp_spec": {
                "kind": "llama_gnmuon_audit",
                "script": "Results/scripts/exp_llama_gnmuon_audit.py",
                "model": "llama",
                "success_metric": "Delta_C1 bootstrap CI",
                "confirm_rule": "primary_confirmed true",
                "env": {
                    "PRE_STEPS": "600",
                    "FT_STEPS": "240",
                    "SEEDS": "0,1,2,3,4",
                    "METHODS": "gnmuon,muon,adamw,full_gn",
                    "LR_GRID_GNMUON": "0.01,0.02",
                    "N_LAYER": "4",
                    "N_HEAD": "4",
                    "N_EMBD": "256",
                },
                "required_markers": ["RESULT_JSON", "EMP_VERDICT", "EXP_DONE"],
            },
        }
        summary = paper._refuted_summary(report_smoke)
        required = [
            "protocol:", "FT_STEPS=240", "SEEDS=0,1,2,3,4",
            "METHODS=gnmuon,muon,adamw,full_gn", "LR_GRID_GNMUON=0.01,0.02",
            "N_LAYER=4", "required_markers",
        ]
        missing = [s for s in required if s not in summary]
        if missing:
            return (
                "paper refuted EXP_SPEC protocol summary smoke failed; "
                f"missing {missing} in {summary[:500]}"
            )
        if "compact protocol/baseline table" not in paper._WRITER_PROMPT:
            return "paper writer prompt does not require a protocol/baseline table"
    except Exception as e:
        return f"paper refuted EXP_SPEC protocol smoke crashed: {type(e).__name__}: {e}"
    return None


def _doctor_exp_policy_findings(cfg: ARConfig) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []

    def add(severity: str, code: str, detail: str) -> None:
        findings.append({"severity": severity, "code": code, "detail": detail})

    exp_kind = str(getattr(cfg, "exp_kind", "") or "").strip().lower()
    if exp_kind != "llama":
        return findings

    # Regression smoke for the gnmuon_c1_410m incident: a pythia-410m node must
    # not be allowed to launch a pythia-160m EXP_SPEC, and llama projects must
    # not launch Pythia typed runs at all.
    try:
        exp_spec.canonicalize(
            {"kind": "real_forgetting", "model": "EleutherAI/pythia-160m"},
            context="node=doctor_410m short=Pythia-410m plan pythia-410m",
            exp_kind=exp_kind,
        )
        add("error", "exp_policy_smoke",
            "pythia-160m EXP_SPEC inside pythia-410m context was accepted")
    except ValueError as e:
        # суть смока — «опасная 160m-в-410m спека ОТКЛОНЕНА»; точная строка ошибки не важна:
        # llama-политика отклоняет её раньше model-mismatch, и это тоже корректный исход
        # (проверка точной строки = хрупкий костыль, давала ложный error).
        if ("EXP_SPEC.model mismatch" not in str(e)
                and "exp_kind=llama forbids" not in str(e)):
            add("error", "exp_policy_smoke",
                f"160/410 mismatch smoke failed with wrong error: {e}")
    try:
        exp_spec.canonicalize(
            {"kind": "real_forgetting", "model": "EleutherAI/pythia-160m"},
            context="node=doctor_llama_policy",
            exp_kind=exp_kind,
        )
        add("error", "exp_policy_smoke",
            "Pythia EXP_SPEC was accepted under project exp_kind=llama")
    except ValueError as e:
        # суть — «Pythia-спека под exp_kind=llama ОТКЛОНЕНА»; generic-HF-отказ тоже валиден
        # (проверка точной строки = хрупкий костыль, ложный error).
        if ("exp_kind=llama forbids" not in str(e)
                and "generic HF/llm_exp_kit" not in str(e)):
            add("error", "exp_policy_smoke",
                f"llama-policy smoke failed with wrong error: {e}")
    try:
        exp_spec.canonicalize(
            {"kind": "real_forgetting", "model": "llama"},
            context="node=doctor_bare_llama_generic_hf",
            exp_kind=exp_kind,
        )
        add("error", "exp_policy_smoke",
            "generic HF real_forgetting accepted model='llama' under exp_kind=llama")
    except ValueError as e:
        if "generic HF/llm_exp_kit" not in str(e):
            add("error", "exp_policy_smoke",
                f"bare-llama generic-HF smoke failed with wrong error: {e}")
    try:
        exp_spec.canonicalize(
            {"kind": "gnmuon_wallclock", "claim": "Pythia-160m Pareto audit"},
            context="node=doctor_cornerstone raw CORNERSTONE Pythia-160m",
            exp_kind=exp_kind,
        )
        add("error", "exp_policy_smoke",
            "legacy checkpoint-specific claim with model default was accepted under exp_kind=llama")
    except ValueError as e:
        if "exp_kind=llama forbids legacy checkpoint-specific" not in str(e):
            add("error", "exp_policy_smoke",
                f"legacy-claim smoke failed with wrong error: {e}")
    try:
        legacy = exp_spec.canonicalize(
            {"kind": "legacy_llama_forgetting"},
            context="node=doctor_legacy_llama",
            exp_kind=exp_kind,
        )
        if legacy.get("model") != "llama":
            add("error", "exp_policy_smoke",
                f"legacy llama spec normalized to {legacy.get('model')!r}, expected 'llama'")
    except ValueError as e:
        add("error", "exp_policy_smoke", f"legacy llama spec was rejected: {e}")
    try:
        cornerstone = (
            "llama-style real-net finetune comparison: GN-Muon vs tuned Muon vs "
            "tuned Adam-like vs full three-factor GN variant under matched steps "
            "and matched wall-clock; require positive Delta_C1 with bootstrap 95% CI"
        )
        routed = exp_spec.canonicalize(
            {"kind": exp_spec.infer_kind(cornerstone), "claim": cornerstone},
            context=f"node=doctor_llama_cornerstone cornerstone={cornerstone}",
            exp_kind=exp_kind,
        )
        if routed.get("kind") != "llama_gnmuon_audit":
            add("error", "exp_policy_smoke",
                f"llama cornerstone routed to {routed.get('kind')!r}, expected 'llama_gnmuon_audit'")
        if routed.get("script") != "Results/scripts/exp_llama_gnmuon_audit.py":
            add("error", "exp_policy_smoke",
                f"llama cornerstone script is {routed.get('script')!r}, expected exp_llama_gnmuon_audit.py")
        if exp_spec.is_pythia_model(routed.get("model")):
            add("error", "exp_policy_smoke",
                f"llama cornerstone normalized to Pythia model {routed.get('model')!r}")
    except ValueError as e:
        add("error", "exp_policy_smoke", f"llama cornerstone typed route was rejected: {e}")

    try:
        proxy_cornerstone = (
            "llama-style proxy-falsification grid: GN-Muon/full-GN/AdamW/Muon "
            "under identical K, report held-out Delta_C1, target val, wall-clock, "
            "and Spearman CI between GN proxy/LMO score and Delta_C1"
        )
        routed = exp_spec.canonicalize(
            {"kind": exp_spec.infer_kind(proxy_cornerstone), "claim": proxy_cornerstone},
            context=f"node=doctor_llama_proxy_cornerstone cornerstone={proxy_cornerstone}",
            exp_kind=exp_kind,
        )
        if routed.get("kind") != "llama_proxy_falsification_grid":
            add("error", "exp_policy_smoke",
                f"llama proxy-falsification cornerstone routed to {routed.get('kind')!r}, "
                "expected 'llama_proxy_falsification_grid'")
        if routed.get("script") != "Results/scripts/exp_llama_gnmuon_audit.py":
            add("error", "exp_policy_smoke",
                f"llama proxy-falsification script is {routed.get('script')!r}, "
                "expected exp_llama_gnmuon_audit.py")
        if exp_spec.is_pythia_model(routed.get("model")):
            add("error", "exp_policy_smoke",
                f"llama proxy-falsification normalized to Pythia model {routed.get('model')!r}")
    except ValueError as e:
        add("error", "exp_policy_smoke", f"llama proxy-falsification typed route was rejected: {e}")

    try:
        fixed_cornerstone = (
            "llama-style fixed-baseline retention audit: GN-Muon vs заранее "
            "фиксированные AdamW/full-GN/Muon при одинаковом K, report held-out "
            "Delta_C1, target-loss, wall-clock, bootstrap 95% CI; pass only if "
            "firewall claim survives fixed-baseline reporting"
        )
        routed = exp_spec.canonicalize(
            {"kind": exp_spec.infer_kind(fixed_cornerstone), "claim": fixed_cornerstone},
            context=f"node=doctor_llama_fixed_cornerstone cornerstone={fixed_cornerstone}",
            exp_kind=exp_kind,
        )
        if routed.get("kind") != "llama_fixed_baseline_audit":
            add("error", "exp_policy_smoke",
                f"llama fixed-baseline cornerstone routed to {routed.get('kind')!r}, "
                "expected 'llama_fixed_baseline_audit'")
        if routed.get("script") != "Results/scripts/exp_llama_gnmuon_audit.py":
            add("error", "exp_policy_smoke",
                f"llama fixed-baseline script is {routed.get('script')!r}, "
                "expected exp_llama_gnmuon_audit.py")
        if exp_spec.is_pythia_model(routed.get("model")):
            add("error", "exp_policy_smoke",
                f"llama fixed-baseline normalized to Pythia model {routed.get('model')!r}")
    except ValueError as e:
        add("error", "exp_policy_smoke", f"llama fixed-baseline typed route was rejected: {e}")

    try:
        selector_cornerstone = (
            "llama-style checkpoint pool: compare C1-selector vs loss-selector vs "
            "time-selector vs GN-proxy under identical K-step finetune; report held-out "
            "Delta C1 bootstrap CI and pass only if C1-selector beats all baselines"
        )
        routed = exp_spec.canonicalize(
            {"kind": exp_spec.infer_kind(selector_cornerstone), "claim": selector_cornerstone},
            context=f"node=doctor_llama_selector_cornerstone cornerstone={selector_cornerstone}",
            exp_kind=exp_kind,
        )
        if routed.get("kind") != "llama_checkpoint_pool_selector":
            add("error", "exp_policy_smoke",
                f"llama selector cornerstone routed to {routed.get('kind')!r}, "
                "expected 'llama_checkpoint_pool_selector'")
        if routed.get("script") != "Results/scripts/exp_llama_checkpoint_pool_selector.py":
            add("error", "exp_policy_smoke",
                f"llama selector cornerstone script is {routed.get('script')!r}, "
                "expected exp_llama_checkpoint_pool_selector.py")
        if exp_spec.is_pythia_model(routed.get("model")):
            add("error", "exp_policy_smoke",
                f"llama selector cornerstone normalized to Pythia model {routed.get('model')!r}")
    except ValueError as e:
        add("error", "exp_policy_smoke", f"llama selector typed route was rejected: {e}")

    try:
        calibration_cornerstone = (
            "llama-style prospective firewall-calibration audit: preselect checkpoint "
            "pairs by C1 lower-CI rule vs loss/time/GN-proxy selectors, identical K "
            "and LR grid, report held-out Delta_C1, target loss, wall-clock, and "
            "false-accept bootstrap CI"
        )
        routed = exp_spec.canonicalize(
            {"kind": exp_spec.infer_kind(calibration_cornerstone), "claim": calibration_cornerstone},
            context=f"node=doctor_llama_calibration cornerstone={calibration_cornerstone}",
            exp_kind=exp_kind,
        )
        if routed.get("kind") != "llama_firewall_calibration_audit":
            add("error", "exp_policy_smoke",
                f"llama firewall-calibration cornerstone routed to {routed.get('kind')!r}, "
                "expected 'llama_firewall_calibration_audit'")
        if routed.get("script") != "Results/scripts/exp_llama_checkpoint_pool_selector.py":
            add("error", "exp_policy_smoke",
                f"llama firewall-calibration script is {routed.get('script')!r}, "
                "expected exp_llama_checkpoint_pool_selector.py")
        if exp_spec.is_pythia_model(routed.get("model")):
            add("error", "exp_policy_smoke",
                f"llama firewall-calibration normalized to Pythia model {routed.get('model')!r}")
    except ValueError as e:
        add("error", "exp_policy_smoke", f"llama firewall-calibration typed route was rejected: {e}")

    try:
        alignment_cornerstone = (
            "llama-style source-target alignment bridge audit: among target-loss-matched "
            "optimizer-checkpoint pairs, compare high vs low pre-finetune source-target "
            "alignment; report held-out Delta_C1 bucket gap with bootstrap 95% CI excluding 0"
        )
        routed = exp_spec.canonicalize(
            {"kind": exp_spec.infer_kind(alignment_cornerstone), "claim": alignment_cornerstone},
            context=f"node=doctor_llama_alignment cornerstone={alignment_cornerstone}",
            exp_kind=exp_kind,
        )
        if routed.get("kind") != "llama_alignment_bridge_audit":
            add("error", "exp_policy_smoke",
                f"llama alignment-bridge cornerstone routed to {routed.get('kind')!r}, "
                "expected 'llama_alignment_bridge_audit'")
        if routed.get("script") != "Results/scripts/exp_llama_checkpoint_pool_selector.py":
            add("error", "exp_policy_smoke",
                f"llama alignment-bridge script is {routed.get('script')!r}, "
                "expected exp_llama_checkpoint_pool_selector.py")
        if exp_spec.is_pythia_model(routed.get("model")):
            add("error", "exp_policy_smoke",
                f"llama alignment-bridge normalized to Pythia model {routed.get('model')!r}")
    except ValueError as e:
        add("error", "exp_policy_smoke", f"llama alignment-bridge typed route was rejected: {e}")

    try:
        from . import review_gate
        selector_noexp = (
            "The branch claims a llama-style proxy-falsification grid where GN/LMO proxy "
            "score predicts held-out Delta_C1 across GN-Muon/full-GN/AdamW/Muon.\n\n"
            "NO_EXP_NEEDED: local proof only\n"
        )
        status, fb = review_gate.review(
            "=== derive.md ===\n" + selector_noexp,
            "verify.py ok",
            cfg,
            call=lambda _prompt: "FEEDBACK: ok\nGATE_VERDICT: PASS",
            node="doctor_selector_noexp",
            contract_text=selector_noexp,
        )
        if status != "fail" or "NO_EXP_NEEDED is invalid" not in fb:
            add("error", "exp_policy_smoke",
                "review_gate accepted NO_EXP_NEEDED for llama proxy-falsification claim")
        negative_pivot_noexp = (
            "This branch mentions a llama-style proxy-falsification grid and checkpoint "
            "selector only to formalize the already negative result. It proves a local "
            "certificate limitation and makes not a new real-net claim.\n\n"
            "NO_EXP_NEEDED: чистая локальная/протокольная теорема; она formalize/report "
            "the settled refutation, без нового real-net claim.\n"
        )
        status, fb = review_gate.review(
            "=== derive.md ===\n" + negative_pivot_noexp,
            "verify.py ok",
            cfg,
            call=lambda _prompt: "FEEDBACK: ok\nGATE_VERDICT: PASS",
            node="doctor_negative_pivot_noexp",
            contract_text=negative_pivot_noexp,
        )
        if status == "fail" and "NO_EXP_NEEDED is invalid" in fb:
            add("error", "exp_policy_smoke",
                "review_gate rejected negative-pivot NO_EXP_NEEDED as a duplicate real-net EXP_SPEC")
        datapivot_noexp = (
            "The branch mentions a llama-style proxy-falsification grid and checkpoint "
            "selector only to prove target-only GN/LMO non-identifiability for source "
            "retention; it does not claim new held-out Delta_C1 wins without a real audit.\n\n"
            "NO_EXP_NEEDED: результат является локальной алгебраической и протокольной "
            "теоремой; он закрывает datapivot; новых real-net утверждений не добавлено.\n"
        )
        status, fb = review_gate.review(
            "=== derive.md ===\n" + datapivot_noexp,
            "verify.py ok",
            cfg,
            call=lambda _prompt: "FEEDBACK: ok\nGATE_VERDICT: PASS",
            node="doctor_datapivot_negative_noexp",
            contract_text=datapivot_noexp,
        )
        if status == "fail" and "NO_EXP_NEEDED is invalid" in fb:
            add("error", "exp_policy_smoke",
                "review_gate rejected datapivot local/protocol NO_EXP_NEEDED as a duplicate real-net EXP_SPEC")
        datapivot_analytic_noexp = (
            "The branch proves worst-case affine/source-linearized target-only "
            "GN/LMO non-identifiability and only states a sufficient source-aware "
            "CI audit rule; it does not claim new real-net behavior.\n\n"
            "NO_EXP_NEEDED: это локальная аналитическая теорема о worst-case "
            "affine/source-linearized non-identifiability и достаточности source-aware "
            "CI rule; она исправляет datapivot без нового real-net claim.\n"
        )
        status, fb = review_gate.review(
            "=== derive.md ===\n" + datapivot_analytic_noexp,
            "verify.py ok",
            cfg,
            call=lambda _prompt: "FEEDBACK: ok\nGATE_VERDICT: PASS",
            node="doctor_datapivot_analytic_noexp",
            contract_text=datapivot_analytic_noexp,
        )
        if status == "fail" and "NO_EXP_NEEDED is invalid" in fb:
            add("error", "exp_policy_smoke",
                "review_gate rejected datapivot analytic NO_EXP_NEEDED as a duplicate real-net EXP_SPEC")
        scope_pivot_noexp = (
            "The branch proves a source-free CE identifiability result: a target-only "
            "GN-Muon/LMO transcript can be valid target geometry but is not a "
            "source-retention certificate. It only states a held-out C1 gate protocol "
            "for the already negative story/scope pivot.\n\n"
            "NO_EXP_NEEDED: story/scope pivot; theorem is a source-free CE "
            "identifiability result and makes no new real-net optimizer/retention claim\n"
        )
        status, fb = review_gate.review(
            "=== derive.md ===\n" + scope_pivot_noexp,
            "verify.py ok",
            cfg,
            call=lambda _prompt: "FEEDBACK: ok\nGATE_VERDICT: PASS",
            node="doctor_scope_pivot_noexp",
            contract_text=scope_pivot_noexp,
        )
        if status == "fail" and "NO_EXP_NEEDED is invalid" in fb:
            add("error", "exp_policy_smoke",
                "review_gate rejected scope-pivot no-certificate NO_EXP_NEEDED as a duplicate real-net EXP_SPEC")
        with tempfile.TemporaryDirectory(prefix="doctor-prune-smoke-") as td:
            smoke_cfg = replace(cfg, workdir=td)
            os.makedirs(smoke_cfg.workdir, exist_ok=True)
            open(os.path.join(smoke_cfg.workdir, "astar_feedback.md"), "w", encoding="utf-8").write(
                "SCORE: 7\n"
                "CORNERSTONE: нет\n"
                "WEAK_NODES: schatten, risk, twophasedata, predalign, datapivot\n"
                "**Слабые/лишние узлы, которые выкинуть**\n"
                "- `schatten`: не нужен для negative GN-Muon story.\n"
                "DIRECTIVES: Выкинуть неподдерживающие ветки и оставить одну историю.\n"
            )
            prune = selector.pressure_prune_nodes(smoke_cfg)
            action = selector.pressure_action_targets(smoke_cfg)
            if set(prune) != {"schatten", "risk", "twophasedata", "predalign", "datapivot"} or action != ["scope_pivot"]:
                add("error", "exp_policy_smoke",
                    "prune-only weak-node smoke failed: "
                    f"prune={prune}, action={action}; expected scope_pivot routing")

        fixed_noexp = (
            "The branch claims a llama-style fixed-baseline retention audit: GN-Muon "
            "vs fixed AdamW/full_gn/Muon with Delta_C1, target loss, wall-clock, and CI.\n\n"
            "NO_EXP_NEEDED: local proof only\n"
        )
        status, fb = review_gate.review(
            "=== derive.md ===\n" + fixed_noexp,
            "verify.py ok",
            cfg,
            call=lambda _prompt: "FEEDBACK: ok\nGATE_VERDICT: PASS",
            node="doctor_fixed_noexp",
            contract_text=fixed_noexp,
        )
        if status != "fail" or "NO_EXP_NEEDED is invalid" not in fb:
            add("error", "exp_policy_smoke",
                "review_gate accepted NO_EXP_NEEDED for llama fixed-baseline claim")
        calibration_noexp = (
            "The branch claims a llama-style prospective firewall-calibration audit "
            "with held-out Delta_C1, target loss, wall-clock, and false-accept CI.\n\n"
            "NO_EXP_NEEDED: local proof only\n"
        )
        status, fb = review_gate.review(
            "=== derive.md ===\n" + calibration_noexp,
            "verify.py ok",
            cfg,
            call=lambda _prompt: "FEEDBACK: ok\nGATE_VERDICT: PASS",
            node="doctor_calibration_noexp",
            contract_text=calibration_noexp,
        )
        if status != "fail" or "NO_EXP_NEEDED is invalid" not in fb:
            add("error", "exp_policy_smoke",
                "review_gate accepted NO_EXP_NEEDED for llama firewall-calibration claim")
    except Exception as e:
        add("error", "exp_policy_smoke", f"selector NO_EXP_NEEDED gate smoke failed: {e}")

    try:
        data = gio.load_graph(cfg)
        gio.ensure_fields(data)
    except Exception as e:
        add("error", "exp_policy_graph", f"cannot load graph for exp policy check: {e}")
        return findings

    refuted_kinds: Dict[str, List[str]] = {}
    for node in data.get("nodes", []):
        spec = node.get("exp_spec") if isinstance(node.get("exp_spec"), dict) else {}
        kind = str(spec.get("kind") or "").strip()
        if kind and node.get("exp_refuted") and graph_hygiene.project_policy_eligible(node, cfg):
            refuted_kinds.setdefault(kind, []).append(str(node.get("id") or ""))
    if refuted_kinds:
        duplicate_cornerstone = (
            "llama-style multi-checkpoint/multi-task proxy-falsification benchmark: "
            "GN-proxy/LMO-score/target-loss/time selectors vs direct held-out "
            "\\(\\Delta C_1\\) audit under identical \\(K\\) and LR grids; report "
            "selector regret and Spearman bootstrap CIs, with the claim accepted "
            "only as negative safety if geometry proxies fail."
        )
        duplicate_kind = exp_spec.infer_kind(duplicate_cornerstone)
        if duplicate_kind in refuted_kinds:
            review = f"HEADLINE: gnmuon\nCORNERSTONE: {duplicate_cornerstone}\nSCORE: 5\n"
            suppressed = paper._suppress_refuted_cornerstone(review, refuted_kinds)
            if "DUPLICATE_REFUTED_CORNERSTONE" not in suppressed or "CORNERSTONE: нет" not in suppressed:
                add("error", "exp_policy_smoke",
                    "duplicate-refuted CORNERSTONE suppressor did not rewrite a refuted reviewer demand")
        live_corner = supervisor._latest_feedback_cornerstone(cfg)
        live_kind = exp_spec.infer_kind(live_corner) if live_corner else ""
        if live_kind in refuted_kinds:
            add("error", "exp_policy_cornerstone",
                f"latest feedback CORNERSTONE still exposes already-refuted kind {live_kind}: "
                + ", ".join(refuted_kinds[live_kind][:5]))
        astar_path = os.path.join(cfg.workdir, "astar_feedback.md")
        try:
            astar_text = open(astar_path, encoding="utf-8", errors="replace").read()
        except OSError:
            astar_text = ""
        if astar_text:
            for line in astar_text.splitlines():
                m = re.match(r"\s*CORNERSTONE\s*:\s*(.+?)\s*$", line, flags=re.IGNORECASE)
                if not m:
                    continue
                raw = m.group(1).strip()
                if raw in ("", "—", "-", "нет", "none", "None"):
                    break
                raw_kind = exp_spec.infer_kind(raw)
                if raw_kind in refuted_kinds and "DUPLICATE_REFUTED_CORNERSTONE" not in astar_text:
                    add("error", "exp_policy_feedback",
                        f"astar_feedback exposes already-refuted CORNERSTONE kind {raw_kind} without suppression note")
                break
        digest = supervisor._latest_review_digest(cfg)
        if "already refuted kind" not in digest:
            try:
                from .reporter import _reports_dir
                rd = _reports_dir(cfg)
                reviews = [os.path.join(rd, f) for f in os.listdir(rd) if f.endswith(".review.md")]
                latest = max(reviews, key=os.path.getmtime) if reviews else ""
                latest_text = open(latest, encoding="utf-8", errors="replace").read() if latest else ""
            except OSError:
                latest_text = ""
            m = re.search(r"^\s*CORNERSTONE\s*:\s*(.+?)\s*$", latest_text,
                          flags=re.IGNORECASE | re.MULTILINE)
            if m:
                raw = m.group(1).strip()
                if raw and raw.lower() not in {"нет", "none"}:
                    raw_kind = exp_spec.infer_kind(raw)
                    if raw_kind in refuted_kinds:
                        add("error", "exp_policy_cornerstone_digest",
                            f"latest review has already-refuted CORNERSTONE kind {raw_kind}, "
                            "but latest review digest did not mark it as already refuted")

    launchable_status = {"conditional", "proven", "open", "weak", "needs_writeup"}
    bad_nodes: List[str] = []
    bad_llama_alias_nodes: List[str] = []
    by = gio.index(data)
    for node in data.get("nodes", []):
        spec = node.get("exp_spec") if isinstance(node.get("exp_spec"), dict) else {}
        if not spec:
            continue
        if node.get("status") not in launchable_status:
            continue
        if node.get("policy_blocked_exp") or node.get("mechanical_invalid_exp"):
            continue
        if node.get("exp_refuted") or node.get("exp_confirmed"):
            continue
        if exp_spec.is_pythia_model(spec.get("model")):
            bad_nodes.append(str(node.get("id")))
        if exp_spec.is_bare_llama_generic_hf_spec(spec):
            bad_llama_alias_nodes.append(str(node.get("id")))
    if bad_nodes:
        add("error", "exp_policy_graph",
            "unblocked Pythia EXP_SPEC nodes under exp_kind=llama: " + ", ".join(bad_nodes[:12]))
    if bad_llama_alias_nodes:
        add("error", "exp_policy_graph",
            "generic HF EXP_SPEC nodes use non-loadable model='llama' under exp_kind=llama: "
            + ", ".join(bad_llama_alias_nodes[:12]))

    active_bad = []
    active_bad_llama_alias = []
    for nid in gio.load_active(cfg):
        node = by.get(nid) or {}
        spec = node.get("exp_spec") if isinstance(node.get("exp_spec"), dict) else {}
        if spec and exp_spec.is_pythia_model(spec.get("model")) and not node.get("policy_blocked_exp"):
            active_bad.append(str(nid))
        if spec and exp_spec.is_bare_llama_generic_hf_spec(spec):
            active_bad_llama_alias.append(str(nid))
    if active_bad:
        add("error", "exp_policy_active",
            "active Pythia EXP_SPEC nodes under exp_kind=llama: " + ", ".join(active_bad))
    if active_bad_llama_alias:
        add("error", "exp_policy_active",
            "active generic HF EXP_SPEC nodes use model='llama' under exp_kind=llama: "
            + ", ".join(active_bad_llama_alias))

    active_legacy = [
        str(nid) for nid in gio.load_active(cfg)
        if not graph_hygiene.project_policy_eligible(by.get(nid) or {}, cfg)
    ]
    if active_legacy:
        add("error", "exp_policy_active",
            "active nodes contain legacy checkpoint-size/model evidence under exp_kind=llama: "
            + ", ".join(active_legacy))

    astar_fb = os.path.join(cfg.workdir, "astar_feedback.md")
    try:
        with open(astar_fb, encoding="utf-8") as f:
            fb_text = f.read()
        if graph_hygiene.LEGACY_CHECKPOINT_TEXT_RE.search(fb_text):
            add("error", "exp_policy_feedback",
                f"{astar_fb} contains legacy checkpoint-size/model directives under exp_kind=llama")
    except OSError:
        pass

    try:
        from . import reports_index
        idx = reports_index._load(cfg)  # prompt-facing fields are scrubbed by loader.
        prompt_text = "\n".join(
            str(x.get("summary") or "") + "\n" + " ".join(str(t) for t in x.get("tags", []) or [])
            for x in idx
        )
        if graph_hygiene.LEGACY_CHECKPOINT_TEXT_RE.search(prompt_text):
            add("error", "exp_policy_report_index",
                "Reports/report_index.json prompt fields contain legacy checkpoint-size/model text under exp_kind=llama")
    except Exception as e:
        add("error", "exp_policy_report_index", f"report index policy check failed: {e}")

    try:
        cand = supervisor._pick_confirm_candidate(data, cfg)
        if cand:
            spec = cand.get("exp_spec") if isinstance(cand.get("exp_spec"), dict) else {}
            if spec and exp_spec.is_pythia_model(spec.get("model")):
                add("error", "exp_policy_confirm_candidate",
                    f"confirm picker returned Pythia candidate {cand.get('id')} under exp_kind=llama")
            if spec and exp_spec.is_bare_llama_generic_hf_spec(spec):
                add("error", "exp_policy_confirm_candidate",
                    f"confirm picker returned generic HF model='llama' candidate {cand.get('id')} under exp_kind=llama")
    except Exception as e:
        add("error", "exp_policy_confirm_candidate", f"confirm picker check failed: {e}")

    exp_dir = os.path.join(cfg.workdir, ".run", "experiments")
    try:
        for fn in os.listdir(exp_dir):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(exp_dir, fn)
            try:
                rec = json.load(open(path, encoding="utf-8"))
            except (OSError, ValueError) as e:
                add("error", "exp_policy_pending", f"cannot read pending EXP_SPEC {fn}: {e}")
                continue
            spec = rec.get("exp_spec") if isinstance(rec.get("exp_spec"), dict) else {}
            nid = rec.get("nid") or fn[:-5]
            if spec and exp_spec.is_bare_llama_generic_hf_spec(spec):
                add("error", "exp_policy_pending",
                    f"pending {nid} EXP_SPEC[{spec.get('kind')}] uses non-loadable model='llama' "
                    "with a generic HF/llm_exp_kit harness")
            if rec.get("status") == "running" and rec.get("server") and rec.get("done") and rec.get("log"):
                try:
                    done = subprocess.run(
                        ["ssh", str(rec["server"]), f"test -f {rec['done']} && echo DONE || echo WAIT"],
                        capture_output=True, text=True, timeout=20)
                    tail = subprocess.run(
                        ["ssh", str(rec["server"]), f"tail -40 {rec['log']} 2>/dev/null"],
                        capture_output=True, text=True, errors="replace", timeout=20)
                    text = tail.stdout or ""
                    if ("DONE" in done.stdout and "EMP_VERDICT: invalid" in text
                            and "not a valid model identifier" in text):
                        add("error", "exp_policy_pending",
                            f"pending {nid} already finished invalid because model id is not loadable")
                except (subprocess.TimeoutExpired, OSError) as e:
                    add("warn", "exp_policy_pending_probe",
                        f"could not probe pending {nid} on {rec.get('server')}: {e}")
    except OSError:
        pass

    try:
        corner = supervisor._latest_feedback_cornerstone(cfg)
        corner_kind = exp_spec.infer_kind(corner) if corner else ""
        if corner_kind in exp_spec.LLAMA_AUDIT_KINDS:  # единый источник набора (было 3 дубля)
            cand = supervisor._find_kind_candidate(data, cfg, corner_kind)
            completed = any(
                isinstance(n.get("exp_spec"), dict)
                and (n.get("exp_spec") or {}).get("kind") == corner_kind
                and (n.get("exp_refuted") or n.get("exp_confirmed"))
                and not n.get("policy_blocked_exp")
                and not n.get("mechanical_invalid_exp")
                for n in data.get("nodes", [])
            )
            pending = False
            exp_dir = os.path.join(cfg.workdir, ".run", "experiments")
            try:
                for fn in os.listdir(exp_dir):
                    if not fn.endswith(".json"):
                        continue
                    rec = json.load(open(os.path.join(exp_dir, fn), encoding="utf-8"))
                    spec = rec.get("exp_spec") if isinstance(rec.get("exp_spec"), dict) else {}
                    if spec.get("kind") == corner_kind:
                        pending = True
                        break
            except OSError:
                pass
            if cand is None and not pending and not completed:
                add("error", "exp_policy_cornerstone",
                    f"latest CORNERSTONE requires {corner_kind} but graph/pending has no launchable typed candidate")
    except Exception as e:
        add("error", "exp_policy_cornerstone", f"llama cornerstone liveness check failed: {e}")

    return findings


def cmd_doctor(cfg: ARConfig, log_file: str, tail: int, expect_workers: int,
               smoke_prompts: bool, expect_tmux: str = "") -> None:
    """Deterministic health checks for live autoresearch loops.

    This is intentionally stricter than `status`: it fails hard on worker crash
    loops even if the orchestrator process itself is still alive.
    """
    findings: List[Dict[str, str]] = []

    def issue(severity: str, code: str, detail: str) -> None:
        findings.append({"severity": severity, "code": code, "detail": detail})

    active_raw = _json_or_none(cfg.active)
    active = gio.load_active(cfg)
    if not (isinstance(active_raw, dict) and isinstance(active_raw.get("running"), list)):
        issue("error", "active_shape", f"{cfg.active} must be {{\"running\": [...]}}")

    status_path = os.path.join(cfg.workdir, ".run", "agents-status.json")
    status = _json_or_none(status_path) or {}
    agents = _cards(status)
    live_agents = [
        a for a in agents
        if str(a.get("agent", "")).startswith("agent-")
        and a.get("agent") != "agent-experimenter"
        and a.get("stage") in ("thinking", "writing", "gate", "experiment")
    ]
    pressure_limited_active = False
    if expect_workers > 0 and active and len(active) < expect_workers:
        try:
            d_active = gio.load_graph(cfg)
            unresolved = set(selector.pressure_unresolved_targets(d_active, cfg))
            active_norm = {
                nid[len("pressure_"):] if str(nid).startswith("pressure_") else nid
                for nid in active
            }
            pressure_limited_active = bool(unresolved and unresolved.issubset(active_norm))
        except Exception:
            pressure_limited_active = False
    if expect_workers > 0 and active and len(active) < expect_workers and not pressure_limited_active:
        issue("warn", "active_count", f"active={len(active)} expect_workers={expect_workers}")

    log_lines = _tail(log_file, tail) if log_file else []
    log_text = "".join(log_lines)
    live_markers = [
        log_text.rfind("НЕПРЕРЫВНЫЙ режим:"),
        log_text.rfind("пул идейных воркеров:"),
    ]
    live_start = max(live_markers)
    live_log_text = log_text[live_start:] if live_start >= 0 else log_text
    worker_crashes = re.findall(r"идейный воркер\s+\d+\s+упал:[^\n]*", log_text)
    prompt_format = re.findall(r"Replacement index \d+ out of range[^\n]*", log_text)
    tracebacks = re.findall(r"Traceback \(most recent call last\):", log_text)
    keyboard_interrupts = re.findall(
        r"Traceback \(most recent call last\):(?:(?!Traceback \(most recent call last\):).)*KeyboardInterrupt",
        log_text,
        flags=re.DOTALL,
    )
    traceback_count = max(0, len(tracebacks) - len(keyboard_interrupts))
    contract_rejects = re.findall(r"missing experiment contract[^\n]*", log_text)
    verify_preflight_regressions = re.findall(
        r"\[code\] verify\.py (?:is not valid Python|has no module-level executable verification)[^\n]*",
        live_log_text)
    subsystem_crashes = re.findall(
        r"(?:poll экспериментов|фаза подтверждения|планировщик|report-cycle)\s+упал:[^\n]*",
        log_text)

    if worker_crashes:
        sample = " | ".join(worker_crashes[-3:])
        issue("error", "worker_crash_loop", f"{len(worker_crashes)} worker crashes in last {tail} log lines: {sample}")
    if prompt_format:
        issue("error", "prompt_format_crash", "literal braces in a prompt probably need escaping: " + prompt_format[-1])
    if traceback_count:
        issue("error", "traceback", f"{traceback_count} traceback marker(s) in last {tail} log lines")
    if subsystem_crashes:
        issue("error", "subsystem_crash", " | ".join(subsystem_crashes[-3:]))
    if len(contract_rejects) >= 3:
        issue("warn", "contract_reject_loop",
              f"{len(contract_rejects)} missing-contract rejects in last {tail} log lines; check continuation prompt and agent compliance")
    if verify_preflight_regressions:
        issue("error", "verify_preflight_regression",
              "verify.py syntax/module-level reject reached git gate after latest team start; "
              "agent_worker local preflight should have caught it: " + verify_preflight_regressions[-1][:180])
    if not active and worker_crashes:
        issue("error", "empty_active_after_worker_crash", "active.running is empty while idea workers are crashing")
    if expect_workers > 0 and not active and not worker_crashes:
        issue("warn", "empty_active", "active.running is empty; ok only during startup or exhausted frontier")
    if expect_workers > 0 and not live_agents and active:
        issue("warn", "dashboard_no_live_agents", "active nodes exist but dashboard has no live writing/gate agent cards")

    process_summary: Dict[str, Any] = {}
    proc_findings, process_summary = _doctor_process_findings(
        cfg, log_file, expect_workers, expect_tmux)
    for finding in proc_findings:
        issue(finding["severity"], finding["code"], finding["detail"])

    if smoke_prompts:
        err = _doctor_prompt_smoke(cfg)
        if err:
            issue("error", "prompt_smoke", err)

    for finding in _doctor_exp_policy_findings(cfg):
        issue(finding["severity"], finding["code"], finding["detail"])

    experiment_summary: Dict[str, Any] = {}
    pressure_summary: Dict[str, Any] = {}
    node_attempt_summary: Dict[str, Any] = {}
    try:
        data = gio.load_graph(cfg)
        gio.ensure_fields(data)
        exp_findings, experiment_summary = _doctor_experiment_runtime_findings(cfg, data, status)
        for finding in exp_findings:
            issue(finding["severity"], finding["code"], finding["detail"])
        pressure_findings, pressure_summary = _doctor_experiment_pressure_findings(
            cfg, data, status, experiment_summary)
        for finding in pressure_findings:
            issue(finding["severity"], finding["code"], finding["detail"])
        attempt_findings, node_attempt_summary = _doctor_node_attempt_findings(cfg, data)
        for finding in attempt_findings:
            issue(finding["severity"], finding["code"], finding["detail"])
    except Exception as e:
        issue("error", "experiment_runtime_check", f"experiment runtime check failed: {e}")

    ok = not any(f["severity"] == "error" for f in findings)
    print(json.dumps({
        "ok": ok,
        "project": cfg.project_name,
        "active": active,
        "agents_status": status_path,
        "log": os.path.expanduser(log_file) if log_file else "",
        "tail_lines": tail if log_file else 0,
        "live_agent_cards": [a.get("agent") for a in live_agents],
        "process": process_summary,
        "experiment_runtime": experiment_summary,
        "experiment_pressure": pressure_summary,
        "node_attempt_integrity": node_attempt_summary,
        "findings": findings,
    }, ensure_ascii=False, indent=2))
    if not ok:
        raise SystemExit(2)


def cmd_dedup(cfg: ARConfig, text: str) -> None:
    data = gio.load_graph(cfg)
    print(dedup_guard.DedupGuard(data, cfg).check(text).message())


def cmd_select(cfg: ARConfig, k: int) -> None:
    data = gio.load_graph(cfg)
    print(" ".join(selector.select_next(data, cfg, k)))


def cmd_draft(cfg: ARConfig) -> None:
    data = gio.load_graph(cfg)
    print(autodraft.write_draft(data, _ts(), cfg))


def cmd_scoop(cfg: ARConfig, nid: str) -> None:
    data = gio.load_graph(cfg)
    by = gio.index(data)
    if nid not in by:
        print(f"нет узла {nid}"); return
    r = scoop_gate.check_node(by[nid], cfg)
    print(f"[{nid}] SCOOP={r.verdict}  REFS={r.refs}")


def cmd_meta(cfg: ARConfig) -> None:
    data = gio.load_graph(cfg)
    rules = meta_review.generate_rules(data, cfg)
    path = meta_review.write_overlay(rules, datetime.now().strftime("%Y-%m-%d %H:%M"), cfg)
    print(f"overlay -> {path}\n{rules}")


def cmd_report(cfg: ARConfig, no_llm: bool) -> None:
    data = gio.load_graph(cfg)
    r = reporter.generate(data, cfg, _ts(), live=not no_llm)
    print(f"report critic={r['critic']}\n  md:  {r['md']}\n  pdf: {r['pdf']}")
    if r["issues"] and r["issues"] != "нет":
        print(f"  issues: {r['issues']}")


def cmd_paper(cfg: ARConfig, branch: Optional[str], min_score: int) -> None:
    data = gio.load_graph(cfg)
    r = paper.generate_paper(data, cfg, _ts(), branch=branch, min_score=min_score)
    state = "ОПУБЛИКОВАНА" if r["published"] else "ЧЕРНОВИК (балл ниже порога)"
    print(f"финальная статья: A*={r['score']}/10 → {state}\n  pdf: {r['pdf']}\n  tex: {r['tex']}\n  review: {r['review']}")


def cmd_successes(cfg: ARConfig) -> None:
    data = gio.load_graph(cfg)
    r = paper.successes_report(data, cfg, _ts())
    print(f"отчёт по успешным кейсам:\n  pdf: {r['pdf']}")


def cmd_ui_sync(cfg: ARConfig, lit_dir: Optional[str]) -> None:
    """Наполнить кнопки UI: Knowledge (курируемые доки) + Related Work (library.csv)."""
    if cfg.store != "koi":
        print("ui-sync только для koi-store (единый стек)"); return
    data = gio.load_graph(cfg)
    docs = koi_ui.build_knowledge_docs(data, cfg)
    lib = koi_ui.library_from_obsidian(cfg, lit_dir or koi_ui.DEFAULT_LIT)
    print(f"Knowledge: {len(docs)} курируемых документов → {cfg.koi_dir}/knowledge/")
    print(f"Related Work: library.csv → {lib}")


def cmd_gate_init(cfg: ARConfig, repo: str, python: str) -> None:
    r = review_gate.gate_init(repo, cfg.project_root, python=python)
    print(f"bare-repo + pre-receive гейт: {r}\n"
          f"агенты пушат: git push {r} idea/<node>\n"
          f"на push idea/* просыпаются proof/code/critic → reject плохого")


def _gate_repo(cfg: ARConfig, arg: Optional[str]) -> Optional[str]:
    return arg or cfg.gate_repo


def cmd_team(cfg: ARConfig, gate_repo: Optional[str], k: int, rounds: int, workers: int,
             continuous: bool = False, max_iters: int = 1000) -> None:
    gr = _gate_repo(cfg, gate_repo)
    if not gr:
        print("нет gate-repo: задай --gate-repo <bare> или 'gate_repo' в autoresearch.json "
              "(сначала ar gate-init)"); return
    if continuous:
        print(f"НЕПРЕРЫВНЫЙ режим: без простоев, новая задача после каждой. "
              f"Останов: touch {os.path.join(cfg.workdir, 'STOP')}")
        out = supervisor.run_continuous(cfg, gr, k=k, max_workers=workers, max_iters=max_iters)
    else:
        out = supervisor.run(cfg, gr, k=k, rounds=rounds, max_workers=workers)
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_agent(cfg: ARConfig, node_id: str, gate_repo: Optional[str]) -> None:
    gr = _gate_repo(cfg, gate_repo)
    if not gr:
        print("нет gate-repo: --gate-repo или autoresearch.json"); return
    data = gio.load_graph(cfg)
    by = gio.index(data)
    if node_id not in by:
        print(f"нет узла {node_id}"); return
    mem = supervisor._memory(data, by[node_id], cfg)
    r = agent_worker.work_node(by[node_id], mem, cfg, gr)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    agent_worker.apply_result(data, r)
    gio.save_graph(data, cfg)


def cmd_gate(cfg: ARConfig, diff_file: str) -> None:
    diff = open(diff_file, encoding="utf-8").read()
    passed, fb = review_gate.review(diff, "", cfg)
    print(f"GATE: {'PASS' if passed else 'REJECT'} — {fb}")


def cmd_evolve(cfg: ARConfig, n: int) -> None:
    data = gio.load_graph(cfg)
    guard = dedup_guard.DedupGuard(data, cfg)
    added = evolution.evolve_into_graph(data, cfg, n,
                                        guard_check=lambda t: not guard.check(t).is_dup)
    if added:
        gio.save_graph(data, cfg); gio.regen_canvas(cfg)
    print("новые гибриды:", added or "нет")


# ---------- полный раунд ----------

def run_round(cfg: ARConfig, k: int = 0, do_evolve: bool = True, do_meta: bool = True,
              do_draft: bool = True, do_report: bool = True, dry: bool = False) -> Dict[str, Any]:
    data = gio.load_graph(cfg)
    gio.ensure_fields(data)
    failure_taxonomy.annotate(data)
    targets = selector.select_next(data, cfg, k)
    logger.info("ВЫБРАНЫ узлы (selector): %s", targets)
    summary: Dict[str, Any] = {"project": cfg.project_name, "targets": targets,
                               "ran": [], "deferred": [], "cycle_skipped": [],
                               "evolved": [], "draft": None, "overlay": None}
    by = gio.index(data)

    if dry:
        gio.regen_canvas(cfg)
        summary["dry"] = True
        return summary

    rc = _load_research_cycle(cfg)
    if rc is None:
        logger.warning("research_cycle.py не найден -> авто-цикл пропущен; "
                       "прогони стадии derive/proof/code/critic по выбранным узлам сам.")
        summary["cycle_skipped"] = targets
    else:
        fw = rc.FRAMEWORK
        overlay = meta_review.read_overlay(cfg)
        if overlay:
            fw = fw + "\n\n" + overlay
        gio.save_active(targets, cfg, detail="autoresearch round")
        gio.regen_canvas(cfg)
        try:
            for nid in targets:
                node = by[nid]
                scoop = scoop_gate.check_node(node, cfg)
                node["scoop"] = scoop.as_node_field(_ts())
                if scoop.verdict == "scooped":
                    node["status"] = "deferred"; summary["deferred"].append(nid)
                    logger.info("[%s] scooped -> defer (%s)", nid, scoop.refs); continue
                node["attempts"] = int(node.get("attempts", 0) or 0) + 1
                res = rc.run_node(node, fw, by, data.get("xref", []), data.get("root_idea", ""))
                node["verdict"] = ((node.get("verdict", "") + " | ") if node.get("verdict") else "") + \
                    f"R[{_ts()}] {res.get('theorem','')}".strip()
                if res.get("survived"):
                    if node.get("status") in ("open", "weak", "deferred"):
                        node["status"] = "conditional"
                elif res.get("critic") == "refuted" or res.get("code") == "fail":
                    node["status"] = "rejected"
                    node["failure_class"] = failure_taxonomy.classify(
                        str(res.get("critic")) + " " + str(res.get("code")))
                summary["ran"].append({"id": nid, "survived": res.get("survived"),
                                       "proof": res.get("proof"), "code": res.get("code"),
                                       "critic": res.get("critic")})
        finally:
            gio.save_active([], cfg)

    if do_meta:
        rules = meta_review.generate_rules(data, cfg)
        summary["overlay"] = meta_review.write_overlay(
            rules, datetime.now().strftime("%Y-%m-%d %H:%M"), cfg)
    if do_evolve:
        guard = dedup_guard.DedupGuard(data, cfg)
        summary["evolved"] = evolution.evolve_into_graph(
            data, cfg, 3, guard_check=lambda t: not guard.check(t).is_dup)
    if do_draft:
        summary["draft"] = autodraft.write_draft(data, _ts(), cfg)
    if do_report:
        rep = reporter.generate(data, cfg, _ts(), live=True)
        summary["report"] = {"pdf": rep["pdf"], "critic": rep["critic"]}

    gio.save_graph(data, cfg)
    gio.regen_canvas(cfg)
    return summary


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser(prog="autoresearch", description="autoresearch-оркестратор (проект-агностичный)")
    ap.add_argument("--project", help="корень проекта (где IdeaGraph/graph.json); иначе env/cwd")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_i = sub.add_parser("init", help="создать IdeaGraph/autoresearch.json")
    p_i.add_argument("--name", default=""); p_i.add_argument("--domain", default="")
    sub.add_parser("migrate", help="аддитивная миграция схемы графа")
    sub.add_parser("status", help="фронтир + таксономия + бэкенд дедупа")
    p_doc = sub.add_parser("doctor", help="жёсткая live-диагностика worker/log/dashboard состояния")
    p_doc.add_argument("--log", default=os.environ.get("AUTORESEARCH_LOG", ""),
                       help="лог живого loop, например /root/wsdteam-codex.log")
    p_doc.add_argument("--tail", type=int, default=400, help="сколько строк лога проверять")
    p_doc.add_argument("--expect-workers", type=int, default=0, help="ожидаемое число idea workers")
    p_doc.add_argument("--expect-tmux", default=os.environ.get("AUTORESEARCH_EXPECT_TMUX", ""),
                       help="ожидаемая tmux-сессия loop; если пусто, выводится из *-codex.log")
    p_doc.add_argument("--smoke-prompts", action="store_true",
                       help="no-LLM smoke для prompt .format() контрактов")
    p_d = sub.add_parser("dedup"); p_d.add_argument("text", nargs="+")
    p_s = sub.add_parser("select"); p_s.add_argument("-k", type=int, default=0)
    sub.add_parser("draft")
    p_sc = sub.add_parser("scoop"); p_sc.add_argument("node_id")
    sub.add_parser("meta")
    p_e = sub.add_parser("evolve"); p_e.add_argument("-n", type=int, default=3)
    p_rep = sub.add_parser("report", help="ОБЗОР состояния (уровень канбана) → критик-гейт → PDF")
    p_rep.add_argument("--no-llm", action="store_true", help="только детерминированный скелет")
    p_pap = sub.add_parser("paper", help="ФИНАЛЬНАЯ статья: Opus пишет → жёсткий A*-критик → ревайз до порога → PDF")
    p_pap.add_argument("--branch", default=None, help="узел-сюжет (col=1); иначе вся выжившая теория")
    p_pap.add_argument("--min-score", type=int, default=8, help="порог A*-балла для публикации")
    sub.add_parser("successes", help="отчёт по УСПЕШНЫМ кейсам (только победы) → PDF")
    p_gi = sub.add_parser("gate-init", help="создать bare-repo + pre-receive ревью-гейт")
    p_gi.add_argument("--repo", required=True, help="путь к bare-repo (напр. ~/research.git)")
    p_gi.add_argument("--python", default="python3")
    p_g = sub.add_parser("gate", help="прогнать ревью-гейт на diff-файле (ручной тест)")
    p_g.add_argument("diff_file")
    p_us = sub.add_parser("ui-sync", help="наполнить UI: Knowledge (курир. доки) + Related Work (library.csv из Obsidian)")
    p_us.add_argument("--lit-dir", default=None, help="папка literature темы или корень ~/brainlab (тогда все темы)")
    p_tm = sub.add_parser("team", help="Фаза 3: команда живых агентов ведёт узлы фронтира → гейт")
    p_tm.add_argument("-k", type=int, default=2, help="узлов за раунд")
    p_tm.add_argument("--rounds", type=int, default=1)
    p_tm.add_argument("--workers", type=int, default=2)
    p_tm.add_argument("--gate-repo", default=None)
    p_tm.add_argument("--continuous", action="store_true", help="без простоев: новая задача после каждой")
    p_tm.add_argument("--max-iters", type=int, default=1000)
    p_ag = sub.add_parser("agent", help="один агент-член ведёт узел (ветка idea/<X> → гейт)")
    p_ag.add_argument("node_id")
    p_ag.add_argument("--gate-repo", default=None)
    p_r = sub.add_parser("round")
    p_r.add_argument("-k", type=int, default=0)
    p_r.add_argument("--dry", action="store_true")
    p_r.add_argument("--no-evolve", action="store_true")
    p_r.add_argument("--no-meta", action="store_true")
    p_r.add_argument("--no-draft", action="store_true")
    p_r.add_argument("--no-report", action="store_true")
    a = ap.parse_args()

    if a.cmd == "init":
        cmd_init(a.project, a.domain, a.name); return
    cfg = cfgmod.load(a.project)
    if a.cmd == "migrate":
        cmd_migrate(cfg)
    elif a.cmd == "status":
        cmd_status(cfg)
    elif a.cmd == "doctor":
        cmd_doctor(cfg, a.log, a.tail, a.expect_workers, a.smoke_prompts, a.expect_tmux)
    elif a.cmd == "dedup":
        cmd_dedup(cfg, " ".join(a.text))
    elif a.cmd == "select":
        cmd_select(cfg, a.k)
    elif a.cmd == "draft":
        cmd_draft(cfg)
    elif a.cmd == "scoop":
        cmd_scoop(cfg, a.node_id)
    elif a.cmd == "meta":
        cmd_meta(cfg)
    elif a.cmd == "evolve":
        cmd_evolve(cfg, a.n)
    elif a.cmd == "report":
        cmd_report(cfg, a.no_llm)
    elif a.cmd == "paper":
        cmd_paper(cfg, a.branch, a.min_score)
    elif a.cmd == "successes":
        cmd_successes(cfg)
    elif a.cmd == "gate-init":
        cmd_gate_init(cfg, a.repo, a.python)
    elif a.cmd == "gate":
        cmd_gate(cfg, a.diff_file)
    elif a.cmd == "ui-sync":
        cmd_ui_sync(cfg, a.lit_dir)
    elif a.cmd == "team":
        cmd_team(cfg, a.gate_repo, a.k, a.rounds, a.workers, a.continuous, a.max_iters)
    elif a.cmd == "agent":
        cmd_agent(cfg, a.node_id, a.gate_repo)
    elif a.cmd == "round":
        print(json.dumps(run_round(cfg, a.k, not a.no_evolve, not a.no_meta,
                                   not a.no_draft, not a.no_report, a.dry), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
