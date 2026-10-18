"""Проект-агностичная конфигурация autoresearch.

НЕТ привязки к конкретному проекту и к конкретной машине. Корень проекта ищется
по наличию IdeaGraph/graph.json (через --project, env AUTORESEARCH_PROJECT, или
обходом вверх от cwd). Доменное описание и переопределения берутся из per-project
файла IdeaGraph/autoresearch.json (пути в нём — ОТНОСИТЕЛЬНЫЕ корня проекта, поэтому
один и тот же конфиг работает и на Mac, и на личном сервере).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, replace
from typing import Dict, Optional, Tuple

CONFIG_BASENAME = "autoresearch.json"          # лежит в <project>/IdeaGraph/
ENV_PROJECT = "AUTORESEARCH_PROJECT"
DEFAULT_DOMAIN = ("научный проект: формальные гипотезы/теоремы, проверяемые "
                  "доказательством И кодом; честность важнее хайпа")


@dataclass(frozen=True)
class Engines:
    ideator: str = "claude"
    editor: str = "claude"
    judge: str = "claude"
    scoop: str = "claude"
    evolve: str = "claude"
    meta: str = "claude"
    derive: str = "codex"
    code: str = "codex"
    # роли команды (движок задаётся напрямую: codex | sonnet | opus):
    writer: str = "codex"           # идейные агенты: теория + эксперименты
    exp_writer: str = "codex"       # автор GPU-экспскрипта (codex; промпт требует короткий скрипт ≤180 строк поверх готовых хелперов → не обрезается)
    gate_proof: str = "sonnet"      # критик гейта: логика доказательства
    gate_code: str = "codex"        # критик гейта: numpy-проверка
    gate_critic: str = "codex"      # критик гейта: адверсариальная атака  (итого sonnet+2×codex)
    reporter: str = "opus"          # СОСТАВИТЕЛЬ отчёта по узлам (самый тяжёлый)
    report_critic: str = "opus"     # СУПЕР-ЖЁСТКИЙ A*-критик отчёта (1-10)
    librarian: str = "codex_web"    # обзор литературы (Related Work): codex + live web search + локальный индекс
    claude_model: str = "opus"      # дефолт для спецификатора "claude"
    codex_timeout: int = 1200
    claude_timeout: int = 1800      # Opus + длинные отчёты/доказательства
    reporter_timeout: int = 2400
    codex_reasoning_effort: str = ""  # "" = дефолт CLI; "low|medium|high" → -c model_reasoning_effort=<v> (codex «на максимум» = high)
    codex_model: str = ""             # "" = дефолт CLI; иначе -m <model> для codex exec


@dataclass(frozen=True)
class Dedup:
    block_threshold: float = 0.82
    warn_threshold: float = 0.68
    rejected_penalty: float = 0.05
    char_ngram: Tuple[int, int] = (3, 5)


@dataclass(frozen=True)
class Elo:
    start: float = 1500.0
    k_factor: float = 24.0
    rounds: int = 4
    keep_top: int = 12


@dataclass(frozen=True)
class Selector:
    w_elo: float = 1.0
    w_open: float = 0.6
    w_promise: float = 0.8
    w_attempts: float = 0.5
    open_token_norm: int = 30
    pick_k: int = 3
    max_attempts: int = 16  # узел с >= стольких попыток выбывает из рабочего фронтира (анти-застой; проект-агностично)
    terminal: Tuple[str, ...] = (
        "proven", "confirmed_emp", "rejected", "refuted_breadth", "background", "root",
        "experiment_running")
    status_promise: Dict[str, float] = field(default_factory=lambda: {
        "needs_writeup": 1.5,  # эксп ПОДТВЕРДИЛ — приоритетно вписать числа в derive и пройти гейт
        "proven": 1.0, "confirmed_emp": 1.0, "conditional": 0.7, "open": 0.5,
        "weak": 0.3, "deferred": 0.3, "rejected": 0.0, "refuted_breadth": 0.0,
        "background": 0.6, "root": 0.6})


@dataclass(frozen=True)
class ARConfig:
    project_root: str
    project_name: str
    domain: str
    gdir: str
    graph: str
    active: str
    canvas_script: str
    workdir: str
    paper: str
    framework_overlay: str
    store: str = "graph"             # "graph" (IdeaGraph/graph.json) | "koi" (koi-structure)
    koi_dir: str = ""                # <project>/koi-structure (когда store=="koi")
    koi_engine_path: Optional[str] = None
    gate_repo: Optional[str] = None  # bare-repo ревью-гейта (агенты пушат сюда)
    # реальные LLM-эксперименты на GPU-сервере (двухуровневая валидация)
    gpu_server: str = "brain_lab"            # ssh-хост с GPU (доступен по ssh) — фолбэк
    gpu_servers: Tuple[str, ...] = ()        # пул GPU-серверов (brain_lab, <gpu-host>, …)
    gpu_python: str = "~/anaconda3/envs/DFT/bin/python"  # env с torch+transformers (дефолт)
    gpu_python_map: Dict[str, str] = field(default_factory=dict)  # {сервер: путь к python} — пути разнятся
    gpu_kit: str = "~/llm_exp_kit.py"        # хелперы: finetune, NS, eval_loss
    gpu_protocol: str = "~/transfer_protocol.py"  # preflight, bootstrap-CI, full_report
    empirical_in_loop: bool = False          # НЕ гонять реальные эксперименты авто (дорого/часы)
    exp_kind: str = ""                       # project policy, e.g. "llama" requires llama-style typed runs
    report_min_score: int = 8                # порог публикации отчёта И порог pressure-петли (единый)
    exp_env: Dict[str, str] = field(default_factory=dict)  # проектные env-оверрайды экспа (размер модели/шаги/LR); имеют приоритет над дефолтами empirical
    max_concurrent_exp: int = 0  # 0 = дефолт (число GPU-серверов); иначе потолок параллельных экспов (реально ограничен свободными GPU)
    lit_dir: str = ""            # каталог разборов темы на машине лупа (для Related Work); "" → <работа>/../literature
    research_cycle_path: Optional[str] = None   # абс. путь к research_cycle.py (если есть)
    engines: Engines = field(default_factory=Engines)
    dedup: Dedup = field(default_factory=Dedup)
    elo: Elo = field(default_factory=Elo)
    selector: Selector = field(default_factory=Selector)
    survived_status: Tuple[str, ...] = ("proven", "confirmed_emp", "conditional")


def _is_project_root(d: str) -> bool:
    return (os.path.exists(os.path.join(d, "IdeaGraph", "graph.json"))
            or os.path.exists(os.path.join(d, "koi-structure", "project.md")))


def find_project_root(start: Optional[str] = None) -> str:
    """Найти корень проекта = директория с IdeaGraph/graph.json ИЛИ koi-structure/project.md.
    Приоритет: явный start -> env AUTORESEARCH_PROJECT -> обход вверх от cwd."""
    candidates = []
    if start:
        candidates.append(start)
    if os.environ.get(ENV_PROJECT):
        candidates.append(os.environ[ENV_PROJECT])
    candidates.append(os.getcwd())
    for c in candidates:
        c = os.path.abspath(os.path.expanduser(c))
        if os.path.basename(c) in ("IdeaGraph", "koi-structure"):
            c = os.path.dirname(c)
        cur = c
        while True:
            if _is_project_root(cur):
                return cur
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
    raise FileNotFoundError(
        "Не найден корень проекта (IdeaGraph/graph.json или koi-structure/project.md). "
        "Укажи --project <path> или env AUTORESEARCH_PROJECT, или запускай из папки проекта.")


def load(project: Optional[str] = None) -> ARConfig:
    """Собрать ARConfig: корень + per-project IdeaGraph/autoresearch.json (опционален)."""
    root = find_project_root(project)
    gdir = os.path.join(root, "IdeaGraph")
    raw: Dict = {}
    # конфиг проекта ищем в koi-structure/ (единый стек) или IdeaGraph/ (legacy)
    for cfgfile in (os.path.join(root, "koi-structure", CONFIG_BASENAME),
                    os.path.join(gdir, CONFIG_BASENAME)):
        if os.path.exists(cfgfile):
            with open(cfgfile, encoding="utf-8") as f:
                raw = json.load(f)
            break
    paths = raw.get("paths", {})
    workdir = os.path.join(root, paths.get("workdir", ".research_loop"))
    paper = os.path.join(root, paths.get("paper", "paper"))
    rc_path = raw.get("research_cycle_path")
    if rc_path:
        rc_path = os.path.abspath(os.path.expanduser(rc_path))
    # store-режим: koi-structure приоритетнее IdeaGraph (единый стек)
    koi_dir = os.path.join(root, "koi-structure")
    store = raw.get("store") or ("koi" if os.path.exists(os.path.join(koi_dir, "project.md")) else "graph")
    cfg = ARConfig(
        project_root=root,
        project_name=raw.get("project_name", os.path.basename(root)),
        domain=raw.get("domain", DEFAULT_DOMAIN),
        gdir=gdir,
        graph=os.path.join(gdir, "graph.json"),
        active=os.path.join(gdir, "active.json"),
        canvas_script=os.path.join(gdir, "idea_graph_canvas.py"),
        workdir=workdir,
        paper=paper,
        framework_overlay=os.path.join(workdir, "framework_overlay.md"),
        store=store,
        koi_dir=koi_dir,
        koi_engine_path=raw.get("koi_engine_path"),
        gate_repo=(os.path.abspath(os.path.expanduser(raw["gate_repo"])) if raw.get("gate_repo") else None),
        research_cycle_path=rc_path,
    )
    # top-level переопределения ARConfig (gpu/эмпирика)
    top = {k: raw[k] for k in ("gpu_server", "gpu_python", "gpu_kit", "gpu_protocol",
                               "empirical_in_loop", "gpu_servers", "gpu_python_map",
                               "exp_kind", "report_min_score", "exp_env",
                               "max_concurrent_exp", "lit_dir") if k in raw}
    if "gpu_servers" in top:
        top["gpu_servers"] = tuple(top["gpu_servers"])
    if "exp_env" in top:
        top["exp_env"] = {str(k): str(v) for k, v in dict(top["exp_env"]).items()}
    if top:
        cfg = replace(cfg, **top)
    # точечные переопределения движков из конфига
    if "engines" in raw:
        cfg = replace(cfg, engines=replace(cfg.engines, **{
            k: v for k, v in raw["engines"].items() if hasattr(cfg.engines, k)}))
    return cfg
