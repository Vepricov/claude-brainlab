"""Supervisor команды живых агентов (Фаза 3).

Держит пул агентов-членов: selector(#2) выбирает узлы фронтира → на каждый назначается
агент-воркер (своя ветка idea/<X>) → воркер делает узел, пушит в bare-repo гейта →
pre-receive ревью-гейт судит → store обновляется. Агенты переживают задачи; общаются
через inbox-очереди. Параллельность — ThreadPoolExecutor (воркеры IO-bound на Opus+git).

Назначение, а не спавн-каждый-раз: один пул воркеров берёт узлы по мере освобождения.
"""
from __future__ import annotations

import logging
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from .config import ARConfig
from . import (graph_hygiene, graph_io as gio, selector, failure_taxonomy, inbox,
               agent_worker, agents_status, node_memory, exp_spec, litreview)

logger = logging.getLogger(__name__)


def _edge_summary(edge: Any) -> str:
    if not isinstance(edge, dict):
        return str(edge)
    keys = ("mean", "CI", "excl0", "sign_stable")
    return ", ".join(f"{k}={edge[k]}" for k in keys if k in edge)


def _result_metric_summary(spec: Dict[str, Any], result: Any, limit: int) -> str:
    bits = []
    if isinstance(spec, dict):
        for k in ("kind", "model", "claim", "success_metric"):
            if spec.get(k):
                bits.append(f"{k}: {spec[k]}")
    if not isinstance(result, dict):
        bits.append(f"result: {str(result)[:600]}")
        return " | ".join(bits)[:limit]

    final = result.get("FINAL") if isinstance(result.get("FINAL"), dict) else result
    verdict = result.get("verdict") or final.get("verdict") or result.get("pass")
    if verdict is not None:
        bits.append(f"verdict/pass: {verdict}")

    c1 = final.get("C1")
    if isinstance(c1, dict):
        bits.append(f"C1: {_edge_summary(c1)}")
    matched = final.get("matched_target")
    if isinstance(matched, dict):
        if matched.get("core_cross_rate"):
            bits.append(f"matched_target.core_cross_rate={matched['core_cross_rate']}")
        if matched.get("target_tau") is not None:
            bits.append(f"matched_target.target_tau={matched['target_tau']}")
        if matched.get("edge") is not None:
            bits.append(f"matched_target.edge: {_edge_summary(matched['edge'])}")
    edges = final.get("edges") if isinstance(final.get("edges"), dict) else {}
    for key in ("target_edge", "wallclock_edge", "retention_edge"):
        edge = final.get(key) or edges.get(key)
        if edge is not None:
            bits.append(f"{key}: {_edge_summary(edge)}")

    for key in ("rho_mean", "rho_grad_weighted", "rho_median", "rho_range", "n_layers",
                "n_dim_ok", "n_matrices"):
        if final.get(key) is not None:
            bits.append(f"{key}={final[key]}")
    for key in ("primary_confirmed", "P_delta", "target_noninferior",
                "target_noninferiority_eps"):
        if final.get(key) is not None:
            bits.append(f"{key}={final[key]}")
    for key in ("Delta_C1", "target_edge_neg_gap"):
        edge = final.get(key)
        if edge is not None:
            bits.append(f"{key}: {_edge_summary(edge)}")
    module = final.get("rho_by_module_type")
    if isinstance(module, dict):
        for name, vals in module.items():
            if isinstance(vals, dict):
                parts = ", ".join(f"{k}={vals[k]}" for k in ("rho_mean", "rho_grad_weighted", "grad_energy_frac")
                                  if k in vals)
                if parts:
                    bits.append(f"{name}: {parts}")
    if final.get("limitations"):
        bits.append(f"limitations: {final['limitations']}")

    if not bits:
        bits.append(json.dumps(result, ensure_ascii=False, sort_keys=True)[:800])
    return " | ".join(bits)[:limit]


def _exp_confirmed_summary(f: Dict[str, Any], limit: int = 1200) -> str:
    """Compact result-first text for prompts after a typed experiment confirms."""
    raw = str(f.get("rj") or "")
    try:
        obj = json.loads(raw)
    except (TypeError, ValueError):
        return raw[:limit]
    spec = obj.get("exp_spec") or f.get("exp_spec") or {}
    result = obj.get("result", obj.get("result_text", obj))
    return _result_metric_summary(spec if isinstance(spec, dict) else {}, result, limit)


def _exp_evidence_label(spec: Dict[str, Any]) -> str:
    kind = str((spec or {}).get("kind") or "typed EXP_SPEC")
    rule = str((spec or {}).get("confirm_rule")
               or (spec or {}).get("success_metric")
               or "the typed experiment confirm rule")
    return f"typed EXP_SPEC `{kind}` passed its own confirm rule: {rule}"


def _prompt_safe_gate_feedback(node: Dict[str, Any]) -> str:
    text = str(node.get("last_gate") or "")
    spec = node.get("exp_spec") if isinstance(node.get("exp_spec"), dict) else {}
    if spec.get("kind") != "rho_predictor":
        return text
    # Old rho writeup failures used bootstrap/CI/endpoints wording from a generic
    # evidence template.  For rho_predictor that wording is false and contaminates
    # future prompts, even when phrased as a negative instruction.
    text = re.sub(r"bootstrap[_ -]?ci[_ -]?endpoints?", "extra_result_fields", text,
                  flags=re.IGNORECASE)
    text = re.sub(r"bootstrap[- _]?(?:ci|confidence[- ]?intervals?)?",
                  "typed confirm-rule", text, flags=re.IGNORECASE)
    text = re.sub(r"confidence[- ]?intervals?", "additional statistical artifacts",
                  text, flags=re.IGNORECASE)
    text = re.sub(r"\bendpoints?\b", "extra result fields", text,
                  flags=re.IGNORECASE)
    text = text.replace("CI∌0", "typed confirm-rule pass")
    return text


def _lineage_ids(data: Dict[str, Any], node: Dict[str, Any]) -> List[str]:
    by = gio.index(data)
    chain = list(reversed(gio.ancestors(node["id"], by)))
    ids = [a["id"] for a in chain if a.get("id")]
    ids.append(node["id"])
    return ids


def _latest_review_digest(cfg: ARConfig) -> str:
    try:
        from .reporter import _reports_dir
        rd = _reports_dir(cfg)
        paths = [os.path.join(rd, f) for f in os.listdir(rd) if f.endswith(".review.md")]
        if not paths:
            return ""
        path = max(paths, key=os.path.getmtime)
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""
    keep = []
    for line in text.splitlines():
        if re.match(r"\s*(SCORE|HEADLINE|WEAK_NODES|CORNERSTONE)\s*:", line, re.IGNORECASE):
            cm = re.match(r"\s*CORNERSTONE\s*:\s*(.+?)\s*$", line, re.IGNORECASE)
            if cm:
                kind, ids = _refuted_cornerstone_kind(cfg, cm.group(1).strip())
                if kind:
                    keep.append(f"CORNERSTONE: нет (already refuted kind {kind} by {', '.join(ids[:5])})")
                    continue
            keep.append(line.strip())
        elif "KILLER" in line:
            keep.append(line.strip()[:700])
    return "\n".join(keep[:8])


def _refuted_kind_ids(cfg: ARConfig) -> Dict[str, List[str]]:
    try:
        data = gio.load_graph(cfg)
    except Exception:
        return {}
    out: Dict[str, List[str]] = {}
    for n in data.get("nodes", []):
        spec = n.get("exp_spec") if isinstance(n.get("exp_spec"), dict) else {}
        kind = str(spec.get("kind") or "").strip()
        if not kind or not n.get("exp_refuted"):
            continue
        if not graph_hygiene.project_policy_eligible(n, cfg):
            continue
        out.setdefault(kind, []).append(str(n.get("id")))
    return out


def _refuted_cornerstone_kind(cfg: ARConfig, cornerstone: str) -> tuple[str, List[str]]:
    if not cornerstone or "нет" in cornerstone.lower()[:6]:
        return "", []
    try:
        kind = exp_spec.infer_kind(cornerstone)
    except Exception:
        return "", []
    ids = _refuted_kind_ids(cfg).get(kind) or []
    return (kind, ids) if ids else ("", [])


def _experiment_pressure_block(data: Dict[str, Any], cfg: Optional[ARConfig]) -> str:
    if cfg is None:
        return ""
    try:
        from . import empirical
        if empirical.pending_count(cfg) > 0:
            return ""
    except Exception:
        return ""
    try:
        if _pick_confirm_candidate(data, cfg) is not None:
            return ""
    except Exception:
        return ""
    try:
        score = _latest_score(cfg)
    except Exception:
        score = None
    if score is None:
        try:
            status = json.load(open(os.path.join(cfg.workdir, ".run", "agents-status.json"),
                                    encoding="utf-8"))
            if status.get("last_astar") is not None:
                score = int(status.get("last_astar"))
            elif status.get("scores"):
                score = int(status["scores"][-1].get("score"))
        except (OSError, ValueError, TypeError, KeyError):
            score = None
    if score is None or score >= int(getattr(cfg, "report_min_score", 8) or 8):
        return ""
    try:
        fresh_refuted = _fresh_refuted_ids(data, cfg)
    except Exception:
        fresh_refuted = []
    if fresh_refuted:
        return (
            "EXPERIMENT-PRESSURE PAUSED: a typed EXP_SPEC result is newer than "
            "the latest A*-report and must be folded into a fresh report before "
            "asking agents for another experiment. Fresh refuted/no_signal nodes: "
            f"{', '.join(fresh_refuted[:5])}. Do not request the same stale "
            "CORNERSTONE again; wait for the immediate report pivot or formulate a "
            "materially different typed EXP_SPEC only if your branch adds a new "
            "real-net claim."
        )
    digest = _latest_review_digest(cfg)
    duplicate_note = ""
    required_note = ""
    cornerstone = _latest_feedback_cornerstone(cfg)
    if cornerstone:
        try:
            kind = exp_spec.infer_kind(cornerstone)
        except Exception:
            kind = ""
        if kind:
            refuted = [
                str(n.get("id"))
                for n in data.get("nodes", [])
                if n.get("exp_refuted")
                and isinstance(n.get("exp_spec"), dict)
                and (n.get("exp_spec") or {}).get("kind") == kind
            ]
            if refuted:
                duplicate_note = (
                    "\nIMPORTANT: the latest CORNERSTONE maps to typed EXP_SPEC "
                    f"`{kind}`, but that audit is already refuted by node(s): "
                    f"{', '.join(refuted[:5])}. Do not request the same EXP_SPEC again. "
                    "Branches addressing this critique should pivot around the negative "
                    "result and may use NO_EXP_NEEDED when they only formalize/report the "
                    "settled refutation. Request a typed EXP_SPEC only for a materially "
                    "different, non-refuted real-net claim."
                )
            elif kind in exp_spec.LLAMA_AUDIT_KINDS:  # единый источник набора (было 3 дубля)
                required_note = (
                    "\nLATEST A*-CRITIC EXPERIMENT REQUIREMENT: this critique maps to "
                    f"typed EXP_SPEC `{kind}`. If your branch addresses this critique "
                    "or makes the corresponding real-net claim, `NO_EXP_NEEDED` is not "
                    "acceptable. End derive.md with `EXP_SPEC_REQUEST:{...}` for exactly "
                    f"kind `{kind}` and a claim/metric/confirm_rule matching the branch. "
                    "The experimenter will only run that typed spec after the gate returns "
                    "GATE_VERDICT: EXPERIMENT."
                )
    return (
        "EXPERIMENT-PRESSURE WARNING: current report is below A* threshold "
        f"(A*={score}/10), GPU lane is idle, and there is no eligible typed EXP_SPEC. "
        "Do not launch or request a random harness. However, if this branch makes any "
        "claim about real LLM behavior, optimizer ranking, retention/C1, wall-clock, "
        "checkpoint choice, datasets, or baselines, the branch must end with a precise "
        "typed EXP_SPEC_REQUEST using an allowlisted kind. Use NO_EXP_NEEDED only for a "
        "genuinely local algebraic/theoretical result, and explicitly say which named "
        "weak point it resolves without a new real-net experiment. Latest report context:\n"
        + (digest or "(no latest review digest available)")
        + required_note
        + duplicate_note
    )


def _memory(data: Dict[str, Any], node: Dict[str, Any], cfg: ARConfig = None) -> str:
    by = gio.index(data)
    proven = [n.get("short", "") for n in data["nodes"]
              if graph_hygiene.is_headline_win(n)
              and graph_hygiene.project_policy_eligible(n, cfg)][:10]
    chain = list(reversed(gio.ancestors(node["id"], by))) + [node]
    lineage = " -> ".join(a.get("short", a["id"]) for a in chain) or "корень"
    L = []
    if cfg is not None:
        try:
            from . import narrative as nar
            nstory = nar.ensure(cfg, data)
            if nstory:
                # 6000 chars ≈ 3k токенов — память узла всё равно ~1% контекста, запас огромный,
                # зато доходит и история этапов (напр. оценённый доклад transition-law-ru.pdf)
                L.append("ЕДИНАЯ ИСТОРИЯ ПРОЕКТА (работай В ЕЁ РУСЛЕ, строй кирпич в этот дом):\n"
                         + nstory[:6000])
        except Exception:
            pass
        try:
            from . import reports_index
            rep = reports_index.relevant(cfg, node["id"], by)
            if rep:
                L.append(reports_index.pointer(rep, node["id"]))
        except Exception:
            pass
    L += [f"КОРНЕВАЯ ИДЕЯ: {data.get('root_idea','')}",
          f"ОБЩИЙ ВЕРДИКТ: {data.get('overall_verdict','')}",
          "ДОКАЗАНО (строить ПОВЕРХ): " + ("; ".join(proven) or "—"),
          failure_taxonomy.memory_block(data) or "тупиков нет",
          f"ЛИНИЯ УЗЛА: {lineage}"]
    pressure = _experiment_pressure_block(data, cfg)
    if pressure:
        L.append(pressure)
    exp_confirmed = graph_hygiene.typed_exp_confirmed(node)
    if exp_confirmed:  # ЭТОТ узел уже гонял typed real experiment и он ПОДТВЕРДИЛ
        label = _exp_evidence_label(node.get("exp_spec") or {})
        L.append("ТВОЙ РЕАЛЬНЫЙ LLM-ЭКСПЕРИМЕНТ ПО ЭТОМУ УЗЛУ ПРОШЁЛ TYPED CONFIRM_RULE. "
                 f"{label}. Не обещай дополнительные артефакты или метрики, которых нет "
                 f"в RESULT_JSON. Реальные числа:\n{exp_confirmed}\nВпиши их в derive.md "
                 "(раздел Эксперименты) как эмпирическое подтверждение ровно в рамках "
                 "confirm_rule — это твой результат, не теряй его.")
    # ВСЕ per-seed exp-данные + пути к полным логам (в git-проекте) — идейный агент видит СЫРЫЕ
    # числа всех прогонов узла (не только вердикт), может построить multi-scale negative-таблицу /
    # per-seed сводку прямо в derive. Логи в Results/exp_logs/ (в дереве проекта, доступны агенту).
    _per_seed = node.get("exp_per_seed")
    _log_files = node.get("exp_log_files")
    if _per_seed or _log_files:
        _blk = "СЫРЫЕ ДАННЫЕ ТВОИХ ЭКСПЕРИМЕНТОВ (per-seed — реальные числа для таблиц/bootstrap-CI):\n"
        if _log_files:
            _lf = [_log_files] if isinstance(_log_files, str) else list(_log_files)
            _blk += "Полные логи в проекте: " + ", ".join(_lf[-6:]) + "\n"
        if _per_seed:
            _blk += "per-seed RESULT_JSON:\n" + str(_per_seed)[:6000]
        L.append(_blk)
    gate_feedback = _prompt_safe_gate_feedback(node)
    if gate_feedback:  # узел уже пробовали — продолжи с прошлых замечаний гейта
        L.append(f"ПРОШЛЫЕ ЗАМЕЧАНИЯ ГЕЙТА по этому узлу (попыток: {node.get('attempts',0)}) — "
                 f"устрани их, не начинай с нуля:\n{gate_feedback}")
    if cfg is not None:
        try:
            L.append(node_memory.prompt_block(cfg, node, _lineage_ids(data, node),
                                              f"idea/{node['id']}"))
        except Exception:
            pass
        fb = os.path.join(cfg.workdir, "astar_feedback.md")
        if os.path.exists(fb):
            try:
                fbtxt = graph_hygiene.scrub_project_policy_text(
                    open(fb, encoding="utf-8").read(), cfg)
                if not fbtxt.strip():
                    raise OSError("empty policy-scrubbed astar feedback")
                L.append("ДИРЕКТИВЫ A*-КРИТИКА (делай это, чтобы поднять балл):\n"
                         + fbtxt[:3000])
            except OSError:
                pass
        # СВЕЖИЕ ЧИСЛА ВСЕХ ЭКСПЕРИМЕНТОВ ПРОЕКТА (02-08): теор-агенты видят кросс-узловой дайджест
        # (вердикты + CI по масштабам + где полные логи) → гипотезы проверяются об реальные данные.
        _dig = os.path.join(cfg.workdir, ".run", "exp_results_digest.md")
        if os.path.exists(_dig):
            try:
                _dt = open(_dig, encoding="utf-8").read().strip()
                if _dt:
                    L.append("СВЕЖИЕ РЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТОВ ПРОЕКТА (все узлы; полные RESULT_JSON "
                             "в Results/exp_logs/ — читай их для чисел в derive):\n" + _dt[:4000])
            except OSError:
                pass
    return "\n".join(L)


def _ensure_pressure_repair_nodes(data: Dict[str, Any], cfg: ARConfig) -> List[str]:
    """Create clean work items for no-cornerstone report weak points.

    Historical weak nodes may be quarantined or contain legacy empirical text.
    Repair nodes give workers a clean target that is driven by the latest
    A*-feedback block, without reusing stale node evidence.
    """
    targets = selector.pressure_action_targets(cfg)
    if not targets:
        return []
    by = gio.index(data)
    digest = _latest_review_digest(cfg)[:1200]
    pruned = selector.pressure_prune_nodes(cfg)
    created_or_updated: List[str] = []
    for wid in targets:
        if wid == "scope_pivot":
            rid = "pressure_scope_pivot"
            short = "A*-pressure pivot: negative no-certificate story"
            idea = (
                "Implement the latest A* directives as a story/scope pivot, not as "
                "repairs to the listed weak side nodes. The review says to remove "
                f"these nodes from the core story: {', '.join(pruned) or 'n/a'}."
            )
            open_text = (
                "Use the latest A*-critic directives in memory. Produce a clean "
                "derive.md that rewrites the core as a negative GN-Muon no-certificate "
                "result, downgrades overbroad theory to a local identifiability lemma "
                "or a precise construction, narrows claims to the llama-style audit, "
                "and makes the held-out C1-gate protocol explicit. End with "
                "NO_EXP_NEEDED:<story/scope pivot; no new real-net claim> unless you "
                "introduce a materially different allowlisted typed EXP_SPEC claim."
            )
            plan = (
                "Do not strengthen or reuse the pruned side nodes. Remove loose "
                "bridges from the core paper package and state the defensive protocol "
                "around the already-settled negative evidence."
            )
            pressure_target = "scope_pivot"
        else:
            rid = f"pressure_{wid}"
            short = f"A*-pressure repair: {wid}"
            idea = (
                f"Close latest A* weak point `{wid}` from the current no-cornerstone "
                "review. This is paper/protocol/theory repair, not permission to "
                "reuse old quarantined evidence."
            )
            open_text = (
                "Use the latest A*-critic directives in memory. Produce a clean derive.md "
                "that either ends with NO_EXP_NEEDED:<specific reason and weak point> "
                "for paper/protocol/local-theory repair, or with typed EXP_SPEC_REQUEST "
                "only if the branch makes a materially new real-net claim."
            )
            plan = (
                "Do not quote stale legacy experiment payloads from the old weak node. "
                "Repair the current report package: evidence table/protocol definitions, "
                "acceptance rules, or the no-free-lunch/theory bridge requested by A*."
            )
            pressure_target = wid
        node = by.get(rid)
        if node is None:
            data.setdefault("nodes", []).append({
                "id": rid,
                "short": short,
                "parent": "root",
                "col": 2,
                "status": "open",
                "idea": idea,
                "open": open_text,
                "plan": plan,
                "pressure_target": pressure_target,
                "pressure_digest": digest,
                "pressure_pruned_nodes": pruned,
                "attempts": 0,
            })
            created_or_updated.append(rid)
            continue
        changed = False
        for k, v in {
            "short": short,
            "idea": idea,
            "open": open_text,
            "plan": plan,
            "pressure_target": pressure_target,
            "pressure_digest": digest,
            "pressure_pruned_nodes": pruned,
        }.items():
            if node.get(k) != v:
                node[k] = v
                changed = True
        if node.get("status") in ("weak", "deferred", "rejected"):
            node["status"] = "open"
            changed = True
        if changed:
            created_or_updated.append(rid)
    return created_or_updated


# Бюджет авто-эскалаций мощности на no_signal (сколько раз усиливать дизайн и переприонять,
# прежде чем признать честный settled-null). Итого прогонов = 1 исходный + ESC_BUDGET.
ESC_BUDGET = 2


def _escalate_power_env(env: Dict[str, Any], level: int) -> Dict[str, str]:
    """no_signal часто = недомощность (мелкая модель, мало seeds/чекпоинтов), а не отсутствие эффекта.
    Поднимаем мощность эксперимента на ступень `level` (>=1): больше seeds → уже bootstrap-CI, крупнее
    модель, больше чекпоинтов и eval-батчей. Сохраняем head_dim=N_EMBD/N_HEAD=64. Все значения — строки."""
    out: Dict[str, str] = {str(k): str(v) for k, v in (env or {}).items()}

    def _gi(key: str, default: int) -> int:
        try:
            return int(str(out.get(key, default)))
        except (TypeError, ValueError):
            return default

    # ВАЖНО: эскалация ТОЛЬКО УВЕЛИЧИВАЕТ мощность — никогда не ужимает уже заданный вручную крупный
    # конфиг (напр. seeded scale-аудит 12L/768d). Берём max(текущее_из_env, ladder). Иначе баг:
    # ручной 12L/768d при no_signal перезаписывался лестницей обратно в 8L/512d (level2).
    # seeds: расширяем количество (главный рычаг сужения bootstrap-CI): level1→8, level2→12
    n_seeds = max(4 + 4 * level, 3, len(_env_csv_len("SEEDS", out)))
    out["SEEDS"] = ",".join(str(i) for i in range(n_seeds))
    # модель крупнее, head_dim фиксируем 64: level0 4h/256, level1 6h/384, level2 8h/512 — но НЕ ниже заданного
    n_head = max(4 + 2 * level, _gi("N_HEAD", 0))
    out["N_HEAD"] = str(n_head)
    out["N_EMBD"] = str(max(64 * n_head, _gi("N_EMBD", 0)))
    out["N_LAYER"] = str(max(4 + 2 * level, _gi("N_LAYER", 0)))
    # больше eval-батчей → меньше шума метрики
    out["EVAL_BATCHES"] = str(max(_gi("EVAL_BATCHES", 4) * (level + 1), _gi("EVAL_BATCHES", 0)))
    # больше pretrain и чекпоинтов (осмысленно разнесённые снапшоты)
    pre = max(_gi("PRE_STEPS", 600), 600) + 200 * level
    out["PRE_STEPS"] = str(pre)
    n_ckpt = 4 + 2 * level
    out["POOL_STEPS"] = ",".join(str(int(pre * (i + 1) / n_ckpt)) for i in range(n_ckpt))
    # чуть длиннее held-out FT (не ниже заданного)
    out["FT_STEPS"] = str(max(_gi("FT_STEPS", 240) + 60 * level, _gi("FT_STEPS", 0)))
    return out


def _env_csv_len(key: str, env: Dict[str, Any]) -> list:
    raw = str(env.get(key, "") or "")
    return [s for s in raw.replace(" ", "").split(",") if s]


def _pick_confirm_candidate(data: Dict[str, Any],
                            cfg: Optional[ARConfig] = None) -> Optional[Dict[str, Any]]:
    """Узел с typed EXP_SPEC, прошедший теорию, но ещё не подтверждённый на сети.

    Старый режим выбирал по ключевым словам ("muon", "forget", ...), из-за чего один и тот же
    forgetting harness мог подтверждать нерелевантные claims. Теперь confirm-фаза берёт только
    узлы, для которых gate/agent уже записал machine-readable node.exp_spec.
    """
    for n in data["nodes"]:
        # НИКОГДА не переотбираем заблокированный/сломанный узел: policy_blocked_exp (роутер отказал)
        # или mechanical_invalid_exp (скрипт падал invalid). Раньше эти guard'ы чтил только
        # _find_kind_candidate, а _pick_confirm_candidate — нет → сломанный custom_llama-узел
        # переотбирался и вечно перезапускался invalid (жёг GPU). Теперь блок соблюдается везде.
        if n.get("policy_blocked_exp") or n.get("mechanical_invalid_exp"):
            continue
        # АВТО-ПЕРЕПРИОН no_signal: узел, помеченный needs_exp_rerun (эскалация мощности после
        # недомощного no_signal), берётся В ОБХОД обычных гвардов — иначе verdict «...эксперимент...»
        # и status="open" заморозили бы его навсегда. Пока бежит (experiment_running) — не переотбираем.
        if (n.get("needs_exp_rerun") and isinstance(n.get("exp_spec"), dict)
                and n.get("col") not in (0, None)
                and n.get("status") != "experiment_running"
                and not graph_hygiene.typed_exp_confirmed(n)):
            return n
        if n.get("status") not in ("conditional", "proven"):
            continue
        if n.get("col") in (0, None):
            continue
        if graph_hygiene.typed_exp_confirmed(n):
            continue
        if n.get("exp_confirmed") or n.get("exp_refuted") or n.get("legacy_exp_confirmed"):
            continue  # уже гоняли (подтверждён или опровергнут) — СТРУКТУРНЫЕ флаги вместо подстроки
            # (старый чек `"эксперимент" in verdict` молча выкидывал из GPU-полосы ЛЮБОЙ узел,
            #  в чей verdict критик просто вписал слово «эксперимент»)
        spec = n.get("exp_spec")
        if spec:
            if (cfg is not None
                    and str(getattr(cfg, "exp_kind", "") or "").strip().lower() == "llama"
                    and exp_spec.is_pythia_model((spec or {}).get("model"))):
                continue
            return n
    return None


_AUTO_SEED_KINDS = {"rho_predictor"}
_RHO_DIRECT_MARKERS = (
    "cfisher", "c_fisher", "txdepth", "depthprofile", "depth profile",
    "профиль глубины", "rho_l", "rho predictor", "sigma_delta", "sigma delta",
    "фишер-чувствительность",
)


def _safe_id(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", text).strip("_")[:80] or "exp_probe"


def _unique_node_id(data: Dict[str, Any], base: str) -> str:
    used = {n.get("id") for n in data.get("nodes", [])}
    nid = _safe_id(base)
    if nid not in used:
        return nid
    i = 2
    while f"{nid}_{i}" in used:
        i += 1
    return f"{nid}_{i}"


def _audit_identity(spec: Dict[str, Any]) -> str:
    """Идентичность ЭКСПЕРИМЕНТА, а не полосы (фикс в.220, класс в.198).

    `custom_llama` — это ПОЛОСА (агент сам пишет скрипт, путь per-node
    `Results/scripts/exp_custom_<hash>.py`), а не один эксперимент: за этим ключом стоят ВСЕ
    директивные аудиты критика. Дедуп по `kind` поэтому склеивает материально разные аудиты
    (тот же класс, что в.198 для ключа пересева). Для типизированных kind'ов идентичность == kind.
    """
    if not isinstance(spec, dict):
        return ""
    kind = str(spec.get("kind") or "")
    if kind != "custom_llama":
        return kind
    # ПОРЯДОК ИСПРАВЛЕН В в.221 (саморегрессия в.220b за 4 минуты после доставки).
    # Было: сперва AUDIT_KIND, потом sha1(claim). Но AUDIT_KIND ВЫВОДИТСЯ (`exp_spec.infer_kind`)
    # и НЕ стабилен: тик 1 после рестарта посеял `gnmuon_custom_llama_2` с ТЕМ ЖЕ claim, тем же
    # success_metric/confirm_rule и ТЕМ ЖЕ скриптом `exp_custom_f693f17704.py`, что и уже живой
    # `gnmuon_custom_llama` — отличался ровно один ключ env (`AUDIT_KIND=gnmuon_wallclock` против
    # его отсутствия у узла, созданного до фикса), и дедуп пропустил ПОЛНЫЙ дубль: две одинаковые
    # многочасовые ветки CORNERSTONE-аудита на пул, где пригодна одна карта.
    # claim — единственная СТАБИЛЬНАЯ идентичность полосы: путь per-node скрипта уже равен
    # sha1(claim) (`exp_custom_<hash>.py`), то есть «разные аудиты» в.220 различаются по claim'у
    # без всякого AUDIT_KIND, а одинаковые claim'ы обязаны склеиваться.
    claim = str(spec.get("claim") or "").strip()
    if claim:
        import hashlib
        return "custom_llama:" + hashlib.sha1(claim.encode("utf-8")).hexdigest()[:12]
    env = spec.get("env") if isinstance(spec.get("env"), dict) else {}
    ident = str(spec.get("audit_kind") or env.get("AUDIT_KIND") or "").strip()
    if ident:
        return "custom_llama:" + ident
    return kind


def _has_kind_child(data: Dict[str, Any], parent_id: str, kind: str,
                    identity: str = "") -> bool:
    for n in data.get("nodes", []):
        if n.get("parent") != parent_id:
            continue
        spec = n.get("exp_spec") or {}
        if spec.get("kind") != kind:
            continue
        # в.220: у полосы `custom_llama` сравниваем ИДЕНТИЧНОСТЬ аудита, иначе первый же
        # директивный child навсегда закрывает полосу для всех остальных директив критика.
        if identity and _audit_identity(spec) != identity:
            continue
        return True
    return False


def _needs_writeup_ids(data: Dict[str, Any]) -> List[str]:
    return [
        str(n.get("id"))
        for n in data.get("nodes", [])
        if graph_hygiene.needs_writeup_priority(n)
    ]


def _latest_feedback_cornerstone(cfg: ARConfig) -> str:
    """Latest reviewer CORNERSTONE directive, if any.

    This is intentionally plain text: exp_spec.canonicalize decides whether it
    is launchable under the project policy.  The supervisor only turns a valid
    reviewer demand into a typed child node when the GPU lane is empty.
    """
    # ФИКС ВОЛНЫ 217 (тот же класс, что в.200): опубликованные `Reports/*.review.md` обновляются
    # ТОЛЬКО при публикации цикла, а чекпоинт в.195 пишет `astar_feedback.md` сразу после вердикта
    # раунда — то есть published-файл может отставать на часы. Прежний порядок ставил его ПЕРВЫМ,
    # и первый же CORNERSTONE из УСТАРЕВШЕЙ рецензии (`llama_firewall_calibration_audit`,
    # duplicate-refuted) давал `return ""` — свежий CORNERSTONE не читался ВООБЩЕ. Замер волны 217:
    # 138 строк «ignore duplicate-refuted CORNERSTONE» в логе при живом требовании критика
    # `llama_direct_source_five_gate_deployment_audit`, то есть единственный путь оси E к pass
    # физически не мог получить узел. Источники берём по РЕАЛЬНОЙ свежести (mtime).
    cands: List[str] = [os.path.join(cfg.workdir, "astar_feedback.md")]
    try:
        from .reporter import _reports_dir
        rd = _reports_dir(cfg)
        cands.extend(os.path.join(rd, f) for f in os.listdir(rd) if f.endswith(".review.md"))
    except OSError:
        pass
    def _mtime(p: str) -> float:
        try:
            return os.path.getmtime(p)
        except OSError:
            return 0.0
    paths: List[str] = sorted([p for p in cands if _mtime(p) > 0], key=_mtime, reverse=True)[:4]
    for path in paths:
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            continue
        for line in text.splitlines():
            m = re.match(r"\s*CORNERSTONE\s*:\s*(.+?)\s*$", line, flags=re.IGNORECASE)
            if not m:
                continue
            spec = m.group(1).strip()
            if spec in ("", "—", "-", "нет", "none", "None"):
                return ""
            kind, ids = _refuted_cornerstone_kind(cfg, spec)
            if kind:
                logger.info("ignore duplicate-refuted CORNERSTONE kind=%s nodes=%s", kind, ",".join(ids[:5]))
                return ""
            return spec
    return ""


def _headline_parent_id(data: Dict[str, Any], cfg: ARConfig) -> Optional[str]:
    by = gio.index(data)
    fb = os.path.join(cfg.workdir, "astar_feedback.md")
    try:
        text = open(fb, encoding="utf-8").read()
    except OSError:
        text = ""
    m = re.search(r"^\s*HEADLINE\s*:\s*([A-Za-z0-9_.:-]+)\s*$",
                  text, flags=re.IGNORECASE | re.MULTILINE)
    if m and m.group(1) in by:
        return m.group(1)
    for sc in selector.score_nodes(data, cfg, exclude_running=True)[:20]:
        node = by.get(sc.node_id) or {}
        if graph_hygiene.project_policy_eligible(node, cfg):
            return sc.node_id
    return None


def _find_kind_candidate(data: Dict[str, Any], cfg: ARConfig, kind: str,
                         identity: str = "") -> Optional[Dict[str, Any]]:
    for node in data.get("nodes", []):
        spec = node.get("exp_spec") if isinstance(node.get("exp_spec"), dict) else {}
        if spec.get("kind") != kind:
            continue
        if identity and _audit_identity(spec) != identity:   # в.220: полоса != эксперимент
            continue
        if node.get("status") not in ("conditional", "proven"):
            continue
        if graph_hygiene.typed_exp_confirmed(node) or node.get("exp_refuted"):
            continue
        if node.get("policy_blocked_exp") or node.get("mechanical_invalid_exp"):
            continue
        if not graph_hygiene.project_policy_eligible(node, cfg):
            continue
        return node
    return None


def _seed_cornerstone_candidate(data: Dict[str, Any], cfg: ARConfig,
                                cornerstone: str) -> Optional[Dict[str, Any]]:
    """Create a typed GPU child from a reviewer CORNERSTONE when no candidate exists."""
    if not cornerstone:
        return None
    # Чисто-теоретический cornerstone (impossibility-теорема, лемма, NO_EXP_NEEDED) НЕЛЬЗЯ
    # «подтвердить» эмпирическим GPU-прогоном — попытка порождает doomed custom_llama child,
    # который вечно падает invalid. Такой cornerstone не сеет эксперимент (несущая — сам proof).
    _cl = cornerstone.lower()
    if any(m in _cl for m in ("theorem", "impossib", "lemma", "no-free", "no_free",
                              "no_exp_needed", "теорем", "невозможн", "лемм")):
        return None
    try:
        kind = exp_spec.infer_kind(cornerstone)
        # в.220: имя аудита, которое РЕАЛЬНО потребовал критик, — идентичность эксперимента в
        # полосе custom_llama. Без него дедуп по имени полосы навсегда закрывает её для всех
        # последующих директив (измерено: CORNERSTONE `llama_direct_source_five_gate_deployment_
        # audit`, единственный путь оси E к pass, не мог получить узел, потому что у несущей уже
        # был ЧУЖОЙ custom_llama-child).
        requested_audit = kind if kind else ""
        # единый источник набора (exp_spec.LLAMA_AUDIT_KINDS, было 3 дубля);
        # custom_llama: НОВЫЙ cornerstone от re-query (материально другой эксп) → агент пишет скрипт сам
        if kind not in (exp_spec.LLAMA_AUDIT_KINDS | {"custom_llama"}):
            # Критик потребовал решающий cornerstone, но infer_kind свёл его к legacy/не-llama
            # типу (ce_mechanism/muon_decomp/...). Не роняем сев — любой затребованный решающий
            # эксперимент идёт в custom_llama-полосу (агент сам пишет скрипт + код-ревью, 60M).
            kind = "custom_llama"
        # ФИКС в.221 (вторая половина; класс в.193 «пара строк — единая сущность»): идентичность,
        # по которой ИЩЕМ уже посеянного ребёнка, обязана считаться ТЕМ ЖЕ правилом, что и
        # идентичность СОЗДАВАЕМОГО узла. Прежняя строка строила её из `requested_audit`, а
        # `_audit_identity` (после в.221) берёт sha1(claim) — ключи расходились, и сев переставал
        # быть идемпотентным: каждый цикл добавлял ещё один узел с тем же claim'ом и тем же
        # скриптом. Считаем идентичность по тому же спеку, что уйдёт в узел.
        ident = _audit_identity({"kind": kind, "claim": cornerstone,
                                 "env": {"AUDIT_KIND": requested_audit}})
        if ident == kind:
            ident = ""
        existing = _find_kind_candidate(data, cfg, kind, ident)
        if existing is not None:
            return existing
        parent_id = _headline_parent_id(data, cfg)
        by = gio.index(data)
        parent = by.get(parent_id or "")
        if not parent:
            return None
        if _has_kind_child(data, parent["id"], kind, ident):
            return _find_kind_candidate(data, cfg, kind, ident)
        if kind == "llama_checkpoint_pool_selector":
            raw_spec = {
                "kind": kind,
                "model": exp_spec.DEFAULT_MODEL,
                "claim": cornerstone,
                "success_metric": (
                    "held-out Delta_C1 edge of C1-selector versus loss-selector, "
                    "time-selector, and GN-proxy checkpoint selectors with bootstrap 95% CI"
                ),
                "confirm_rule": (
                    "EMP_VERDICT=confirmed iff FINAL.primary_confirmed is true: every "
                    "pairwise selector-edge bootstrap CI lower bound is above zero and "
                    "target non-inferiority holds"
                ),
                "env": {
                    "PRE_STEPS": "600",
                    "POOL_STEPS": "120,240,360,600",
                    "PROBE_FT_STEPS": "32",
                    "FT_STEPS": "240",
                    "SEEDS": "0,1,2,3,4",
                    "SELECTORS": "c1,loss,time,gn_proxy",
                    "N_LAYER": "4",
                    "N_HEAD": "4",
                    "N_EMBD": "256",
                    "SEQ": "192",
                    "BATCH": "8",
                    "EVAL_BATCHES": "4",
                },
            }
            child_short = "llama-style checkpoint selector audit"
            child_open = (
                "Does a C1-based checkpoint selector beat loss/time/GN-proxy selectors "
                "on held-out source-retention after identical finetune?"
            )
            child_plan = (
                "Run the typed llama_checkpoint_pool_selector GPU probe. Keep the result "
                "only if its RESULT_JSON satisfies the registered confirm_rule."
            )
        elif kind == "llama_firewall_calibration_audit":
            raw_spec = {
                "kind": kind,
                "model": exp_spec.DEFAULT_MODEL,
                "claim": cornerstone,
                "success_metric": (
                    "prospective C1-firewall calibration reports held-out Delta_C1, "
                    "target loss, wall-clock, and false-accept bootstrap CI against "
                    "loss/time/GN-proxy selectors"
                ),
                "confirm_rule": (
                    "EMP_VERDICT=confirmed iff FINAL.calibration_primary_confirmed "
                    "is true: C1 firewall beats selector controls and false-accept "
                    "bootstrap upper CI is <=0.2"
                ),
                "env": {
                    "AUDIT_KIND": "llama_firewall_calibration_audit",
                    "PRE_STEPS": "600",
                    "POOL_STEPS": "120,240,360,600",
                    "PROBE_FT_STEPS": "32",
                    "FT_STEPS": "240",
                    "SEEDS": "0,1,2,3,4",
                    "SELECTORS": "c1,loss,time,gn_proxy",
                    "N_LAYER": "4",
                    "N_HEAD": "4",
                    "N_EMBD": "256",
                    "SEQ": "192",
                    "BATCH": "8",
                    "EVAL_BATCHES": "4",
                },
            }
            child_short = "llama-style firewall calibration audit"
            child_open = (
                "Does a prospective C1 lower-CI firewall avoid false accepts "
                "against loss/time/GN-proxy checkpoint selectors?"
            )
            child_plan = (
                "Run the typed llama_firewall_calibration_audit GPU probe. Keep the "
                "result only if RESULT_JSON reports false-accept bootstrap fields."
            )
        elif kind == "llama_alignment_bridge_audit":
            raw_spec = {
                "kind": kind,
                "model": exp_spec.DEFAULT_MODEL,
                "claim": cornerstone,
                "success_metric": (
                    "target-loss-matched high-vs-low pre-finetune source-target "
                    "gradient-alignment bucket gap in held-out Delta_C1 with bootstrap CI"
                ),
                "confirm_rule": (
                    "EMP_VERDICT=confirmed iff FINAL.alignment_primary_confirmed is true: "
                    "high-alignment checkpoints forget less than target-loss-matched "
                    "low-alignment checkpoints with positive bootstrap lower CI"
                ),
                "env": {
                    "AUDIT_KIND": "llama_alignment_bridge_audit",
                    "PRE_STEPS": "600",
                    "POOL_STEPS": "120,240,360,600",
                    "PROBE_FT_STEPS": "32",
                    "FT_STEPS": "240",
                    "SEEDS": "0,1,2,3,4",
                    "SELECTORS": "c1,loss,time,gn_proxy",
                    "N_LAYER": "4",
                    "N_HEAD": "4",
                    "N_EMBD": "256",
                    "SEQ": "192",
                    "BATCH": "8",
                    "EVAL_BATCHES": "4",
                },
            }
            child_short = "llama-style alignment bridge audit"
            child_open = (
                "Does pre-finetune source-target gradient alignment predict held-out "
                "C1 retention after target-loss-matched llama-style finetunes?"
            )
            child_plan = (
                "Run the typed llama_alignment_bridge_audit GPU probe. Keep the result "
                "only if RESULT_JSON reports alignment_Delta_C1 and matched target-loss gaps."
            )
        elif kind == "llama_proxy_falsification_grid":
            raw_spec = {
                "kind": kind,
                "model": exp_spec.DEFAULT_MODEL,
                "claim": cornerstone,
                "success_metric": (
                    "llama-style method grid reports Delta_C1, target loss, wall-clock, "
                    "and bootstrap Spearman CI between GN/LMO proxy score and held-out Delta_C1"
                ),
                "confirm_rule": (
                    "EMP_VERDICT=confirmed iff FINAL.proxy_primary_confirmed is true: "
                    "proxy_lmo_delta_spearman has |rho|>=0.5 with bootstrap CI excluding zero"
                ),
                "env": {
                    "AUDIT_KIND": "llama_proxy_falsification_grid",
                    "PRE_STEPS": "600",
                    "FT_STEPS": "240",
                    "SEEDS": "0,1,2,3,4",
                    "METHODS": "gnmuon,muon,adamw,full_gn",
                    "LR_GRID_GNMUON": "0.01,0.02",
                    "LR_GRID_MUON": "0.01,0.02",
                    "LR_GRID_ADAMW": "0.0001,0.0003",
                    "LR_GRID_FULL_GN": "0.005,0.01",
                    "N_LAYER": "4",
                    "N_HEAD": "4",
                    "N_EMBD": "256",
                    "SEQ": "192",
                    "BATCH": "8",
                    "COV_BATCHES": "8",
                    "EVAL_BATCHES": "4",
                },
            }
            child_short = "llama-style proxy falsification grid"
            child_open = (
                "Does the GN/LMO proxy score predict held-out Delta_C1 across a "
                "GN-Muon/full-GN/AdamW/Muon llama-style grid?"
            )
            child_plan = (
                "Run the typed llama_proxy_falsification_grid GPU probe. Keep the result "
                "only if its RESULT_JSON satisfies the registered proxy confirm_rule."
            )
        elif kind == "llama_fixed_baseline_audit":
            raw_spec = {
                "kind": kind,
                "model": exp_spec.DEFAULT_MODEL,
                "claim": cornerstone,
                "success_metric": (
                    "llama-style fixed-baseline table reports Delta_C1, target gap, "
                    "and wall-clock separately for GN-Muon vs AdamW, full_gn, and Muon"
                ),
                "confirm_rule": (
                    "EMP_VERDICT=confirmed iff FINAL.fixed_baseline_primary_confirmed "
                    "is true: every fixed baseline has positive Delta_C1 bootstrap CI "
                    "and target non-inferiority"
                ),
                "env": {
                    "AUDIT_KIND": "llama_fixed_baseline_audit",
                    "PRE_STEPS": "600",
                    "FT_STEPS": "240",
                    "SEEDS": "0,1,2,3,4",
                    "METHODS": "gnmuon,muon,adamw,full_gn",
                    "LR_GRID_GNMUON": "0.01,0.02",
                    "LR_GRID_MUON": "0.01,0.02",
                    "LR_GRID_ADAMW": "0.0001,0.0003",
                    "LR_GRID_FULL_GN": "0.005,0.01",
                    "N_LAYER": "4",
                    "N_HEAD": "4",
                    "N_EMBD": "256",
                    "SEQ": "192",
                    "BATCH": "8",
                    "COV_BATCHES": "8",
                    "EVAL_BATCHES": "4",
                },
            }
            child_short = "llama-style fixed-baseline audit"
            child_open = (
                "Does GN-Muon survive a preregistered fixed-baseline audit against "
                "AdamW, full_gn, and Muon separately?"
            )
            child_plan = (
                "Run the typed llama_fixed_baseline_audit GPU probe. Keep the result "
                "only if RESULT_JSON reports per-fixed-baseline CI fields."
            )
        elif kind == "custom_llama":
            raw_spec = {
                "kind": "custom_llama",
                "model": exp_spec.DEFAULT_MODEL,
                "claim": cornerstone,
                "success_metric": (
                    "измеряет ИМЕННО cornerstone-claim на реальной llama-сети; ключевая метрика "
                    "с bootstrap 95% CI по нескольким сидам против контролей"
                ),
                "confirm_rule": (
                    "EMP_VERDICT=confirmed iff заявленный эффект держится на реальных числах "
                    "(bootstrap CI исключает 0 по сидам); иначе no_signal (честный негатив валиден отдельно)"
                ),
                # в.220: имя затребованного аудита едет в env — `exp_spec.canonicalize` оставляет
                # ФИКСИРОВАННУЮ схему (kind/script/model/claim/success_metric/confirm_rule/env/
                # required_markers), поэтому верхнеуровневое поле не выжило бы; env переносится
                # целиком, и через него идентичность полосы видит и дедуп, и сам скрипт. Так же
                # это сделано у типизированных аудитов (AUDIT_KIND в env).
                "env": ({"SEEDS": "0,1,2,3,4", "AUDIT_KIND": requested_audit}
                        if requested_audit and requested_audit != "custom_llama"
                        else {"SEEDS": "0,1,2,3,4"}),
            }
            child_short = "custom llama experiment (cornerstone)"
            child_open = "Держится ли cornerstone-эффект на реальной 60M llama-сети по сидам?"
            child_plan = (
                "Экспериментатор сам пишет llama-скрипт под claim (custom_llama, +код-ревью), "
                "запуск на 60M из exp_env; результат по confirm_rule."
            )
        else:
            raw_spec = {
                "kind": kind,
                "model": exp_spec.DEFAULT_MODEL,
                "claim": cornerstone,
                "success_metric": (
                    "llama-style audit reports Delta_C1, target non-inferiority, P_delta, "
                    "wall-clock, and bootstrap 95% CI against tuned Muon/AdamW/full-GN controls"
                ),
                "confirm_rule": (
                    "EMP_VERDICT=confirmed iff FINAL.primary_confirmed is true: positive "
                    "Delta_C1 bootstrap CI above zero, target non-inferiority, and P_delta>=0.67"
                ),
                "env": {
                    "PRE_STEPS": "600",
                    "FT_STEPS": "240",
                    "SEEDS": "0,1,2,3,4",
                    "METHODS": "gnmuon,muon,adamw,full_gn",
                    "LR_GRID_GNMUON": "0.01,0.02",
                    "LR_GRID_MUON": "0.01,0.02",
                    "LR_GRID_ADAMW": "0.0001,0.0003",
                    "LR_GRID_FULL_GN": "0.005,0.01",
                    "N_LAYER": "4",
                    "N_HEAD": "4",
                    "N_EMBD": "256",
                    "SEQ": "192",
                    "BATCH": "8",
                    "COV_BATCHES": "8",
                    "EVAL_BATCHES": "4",
                },
            }
            child_short = "llama-style GN-Muon retention audit"
            child_open = (
                "Does GN-Muon beat tuned Muon/AdamW/full-GN controls on llama-style "
                "source retention without losing target performance?"
            )
            child_plan = (
                "Run the typed llama_gnmuon_audit GPU probe. Keep the result only if "
                "its RESULT_JSON satisfies the registered confirm_rule."
            )
        spec = exp_spec.canonicalize(
            raw_spec,
            context=f"node={parent['id']} cornerstone={cornerstone}",
            exp_kind=getattr(cfg, "exp_kind", ""),
        )
    except ValueError as e:
        logger.warning("cornerstone EXP_SPEC rejected by policy: %s", e)
        return None
    child = {
        "id": _unique_node_id(data, f"{parent['id']}_{kind}"),
        "short": child_short,
        "parent": parent["id"],
        "col": int(parent.get("col") or 1) + 1,
        "status": "conditional",
        "idea": spec["claim"],
        "open": child_open,
        "plan": child_plan,
        "verdict": (
            "auto-seeded from A*-critic CORNERSTONE because the GPU lane was empty "
            "and no eligible typed EXP_SPEC existed"
        ),
        "elo": max(float(parent.get("elo") or 1900.0), 2200.0),
        "attempts": 0,
        "exp_spec": spec,
    }
    data.setdefault("nodes", []).append(child)
    return child


def _latest_report_mtime(cfg: ARConfig) -> float:
    try:
        from .reporter import _reports_dir
        rd = _reports_dir(cfg)
        paths = [os.path.join(rd, f) for f in os.listdir(rd) if f.endswith(".review.md")]
        return max((os.path.getmtime(p) for p in paths), default=0.0)
    except OSError:
        return 0.0


def _latest_score(cfg: ARConfig) -> Optional[int]:
    try:
        hist = json.load(open(os.path.join(cfg.workdir, ".run", "_scores.json"), encoding="utf-8"))
        if hist:
            return int(hist[-1].get("score"))
    except (OSError, ValueError, TypeError):
        pass
    return None


def _fresh_refuted_ids(data: Dict[str, Any], cfg: ARConfig) -> List[str]:
    latest = _latest_report_mtime(cfg)
    out: List[str] = []
    for n in data.get("nodes", []):
        if not n.get("exp_refuted") or not isinstance(n.get("exp_spec"), dict):
            continue
        if not graph_hygiene.report_eligible(n) or not graph_hygiene.project_policy_eligible(n, cfg):
            continue
        try:
            ts = float(n.get("exp_refuted_at") or 0.0)
        except (TypeError, ValueError):
            ts = 0.0
        if ts and ts >= latest:
            out.append(str(n.get("id")))
    return out


def _fresh_pressure_passed_ids(data: Dict[str, Any], cfg: ARConfig) -> List[str]:
    """Passed pressure-repair nodes for the current sub-A* feedback.

    These nodes are not typed EXP_SPEC writeups, so they are not covered by
    _needs_writeup_ids.  They still must be counted as fresh report material;
    otherwise a restart can keep reselecting the same already-passed
    pressure_<weak> nodes while the old WEAK_NODES line remains current.
    """
    targets = set(selector.pressure_action_targets(cfg))
    if not targets:
        return []
    out: List[str] = []
    for n in data.get("nodes", []):
        if not selector.pressure_node_satisfied(n, targets, cfg):
            continue
        if not graph_hygiene.report_eligible(n) or not graph_hygiene.project_policy_eligible(n, cfg):
            continue
        out.append(str(n.get("id")))
    return out


def _unwedge_phantom_experiment_nodes(data: Dict[str, Any], cfg: ARConfig) -> List[str]:
    """Вернуть в conditional узлы, застрявшие в транзитном status="experiment_running" БЕЗ живой записи.

    Из этого статуса узел выводит ТОЛЬКО финализация прогона, при этом перевыбор его исключает
    (_pick_confirm_candidate) и confirm-lane берёт лишь conditional/proven ⇒ узел без записи выпадает из
    ВСЕХ гейтов навсегда (фикс волны 179).  Запись может исчезнуть не только при рестарте: её уводит в
    сторону policy-блокировка матрёшек и гигиена Syncthing-дублей.  Сам фикс волны 179 был позже потерян
    при правках supervisor.py (в коде осталась только неиспользуемая empirical.record_nids) — восстановлен
    волной 183.  Инвариант вахты: число experiment_running == числу записей в .run/experiments/.
    """
    from . import empirical  # локальный импорт: модуль НЕ в module-level импортах этого файла
    try:
        live = empirical.record_nids(cfg)
    except Exception as e:  # нет доступа к .run/experiments — лучше не трогать статусы вообще
        logger.warning("гигиена фантомов: не смог прочитать записи прогонов (%s)", e)
        return []
    freed: List[str] = []
    for n in data.get("nodes", []):
        if n.get("status") != "experiment_running":
            continue
        if str(n.get("id")) in live:
            continue
        n["status"] = "conditional"
        freed.append(str(n.get("id")))
    return freed


def _seed_confirm_candidate(data: Dict[str, Any], cfg: ARConfig,
                            prefer_ids: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """Create one typed experiment child when the GPU lane is empty.

    The theory workers may keep producing derive.md/verify.py-only branches.  That is
    useful, but it leaves GPUs idle after a decisive experiment refutes the previous
    typed claim.  This lane only seeds allowlisted, project-script-backed experiments,
    so it does not reintroduce the old "random harness confirms everything" bug.
    """
    if str(getattr(cfg, "exp_kind", "") or "").strip().lower() == "llama":
        # LLAMA: когда эксп-агенты простаивают → берём ОСНОВНЫЕ (headline) proven-теоремы, что пойдут
        # в статью, и МАСШТАБИРУЕМ их эмпирическую проверку по scale-ladder (бОльшая модель + перенос
        # между доменами). Не «одна проверка на 60M и стоп»: A* требует подтверждения на нескольких
        # масштабах. Сеём СЛЕДУЮЩИЙ непокрытый масштаб под теорему (не дубль того же).
        # ВАЖНО: масштабируем только RUNNABLE-теоремы (achievability/предиктивные — source-probe
        # предсказывает retention held-out, custom_llama-скрипт строится и ПРОХОДИТ код-ревью). НЕ
        # impossibility: его эмп-проверка требует двух неразличимых миров, которые автоген честно не
        # строит → скрипт вечно бракуется, до GPU не доходит (юзер: «не вижу бегущих экспов»).
        # Impossibility-теорема остаётся ДОКАЗАННОЙ формально, эмпирику под неё не сеем.
        _thm_markers = ("theorem", "lemma", "achievab", "identifiab", "predict", "probe", "gate",
                        "теорем", "лемм", "достижим", "предсказ", "селектор", "selector")
        # firewall/no-go/matched-firewall = impossibility-семейство (эмп-проверка требует двух
        # неразличимых миров, автоген их не строит → router refused → churn + блок codex-генерацией).
        # Маркер часто в id, а не в short/idea → _txt(n) уже включает id (см. ниже).
        _skip_markers = ("impossib", "невозможн", "no-go", "no-free", "firewall", "no_go")
        # РЕДАКТОРСКИЕ/ТЕОРЕТИЧЕСКИЕ директивы (правка текста/определений/новизны) НЕ гоняются на GPU:
        # раньше «убрать фразу…»/«добавить symmetry qualifier» получали proven+маркер и спавнили
        # эмп-scale-up 124M/350M/760M, которые падали (нечего мерить) → холостой жёг циклы/токены.
        # Их место — у писателя/теоретика, не на GPU. Эмпирику мерим только у реально измеримых claim.
        _editorial_markers = ("убрать", "удалить", "переформул", "сформулир", "добавить", "определить",
                              "symmetry qualifier", "quantile", "related work", "переписать", "исправить",
                              "убери", "уточнить", "выписать", "инволюц", "abstract", "заключени")
        # лестница масштабов модели (эскалация до тех, что убедят A*-рецензента)
        SCALE_LADDER = [
            {"tag": "124M", "env": {"N_EMBD": "768", "N_LAYER": "12", "N_HEAD": "12", "BATCH": "16"}},
            {"tag": "350M", "env": {"N_EMBD": "1024", "N_LAYER": "24", "N_HEAD": "16", "BATCH": "8"}},
            {"tag": "760M", "env": {"N_EMBD": "1536", "N_LAYER": "24", "N_HEAD": "16", "BATCH": "4"}},
            # 1B (02-08, по слову юзера «карты не должны простаивать»): корона лестницы. env.SCALES
            # задан явно (полная 4-ступенчатая лестница в одном прогоне — протокол-полнота);
            # N_EMBD=2048 → placement резервирует 60GB (GPU3 или облако mlsub).
            {"tag": "1B", "env": {"N_EMBD": "2048", "N_LAYER": "24", "N_HEAD": "16", "BATCH": "2",
                                  "SCALES": "124M:768,12,12;350M:1024,24,16;760M:1536,24,16;1B:2048,24,16"}},
        ]
        # Кандидаты на масштаб: (a) proven-теоремы с runnable-маркером, (b) эмпирически ПОДТВЕРЖД�ённые
        # узлы (exp_confirmed) — их методичка уже прошла ревью и дала сигнал, масштаб гарантированно
        # runnable. Оба — БЕЗ impossibility-маркера. headline вперёд (сортировка по elo).
        def _txt(n):
            # ВКЛЮЧАЕМ id: impossibility-узлы часто держат маркер в id (gap_gn_firewall_impossibility_emp),
            # а short/idea сформулированы нейтрально → skip не срабатывал → scale-ladder сеял impossibility
            # scale-up → codex-генерация custom_llama (минуты) в главном потоке БЛОКИРОВАЛА report-блок
            # (тики ~6мин, отчёт не наступал) + churn. Проверяем id тоже.
            return (str(n.get("id", "")) + " " + str(n.get("short", "")) + " " + str(n.get("idea", ""))).lower()
        thms = sorted(
            [n for n in data["nodes"]
             if n.get("col") not in (0, None)
             # skip-маркеры (impossib и т.п.) НЕ выкидывают эмпирически ПОДТВЕРЖДЁННЫЙ узел (02-08):
             # его протокол прошёл ревью и дал сигнал — масштаб выше (1B) и есть нужный мост.
             and not (any(s in _txt(n) for s in _skip_markers) and not n.get("exp_confirmed"))
             and not n.get("policy_blocked_exp")
             # scale-ребёнок (id уже несёт тег масштаба) сам НЕ кандидат лестницы: иначе confirmed
             # 124M-ребёнок сеет себе 124M-ребёнка → рекурсивная матрёшка _emp_124M_emp_124M_…
             # (наблюдалась ×25 клонов, каждый жёг GPU). Лестницу ведёт РОДИТЕЛЬ по covered-тегам.
             and not re.search(r"_emp_(?:124M|350M|760M)", str(n.get("id", "")))
             and (
                 (n.get("status") == "proven"
                  and any(m in _txt(n) for m in _thm_markers)
                  # редакторскую/теоретическую директиву НЕ гоним на GPU (если у неё уже нет реального
                  # exp_spec) — это правка текста, а не измеримый claim
                  and not (any(e in _txt(n) for e in _editorial_markers) and not n.get("exp_spec")))
                 or bool(n.get("exp_confirmed"))  # подтверждённый эмп-узел → масштабируем его же проверку
             )],
            # ЭМП-ПОДТВЕРЖДЁННЫЕ вперёд elo-теорий: у них уже есть РАБОЧИЙ (прошедший ревью) скрипт,
            # scale-up гарантированно runnable. Proven-теории (часто impossibility-смежные, напр.
            # firewall) их эмп-тест ревью бракует → шли бы в холостую. Внутри группы — по elo.
            key=lambda n: (0 if n.get("exp_confirmed") else 1, -float(n.get("elo", 0) or 0)))
        for n in thms:
            kids = [c for c in data["nodes"] if c.get("parent") == n["id"]]
            covered = set()
            for c in kids:
                cid = str(c.get("id", ""))
                cenv = (c.get("exp_spec") or {}).get("env") or {}
                matched = False
                for sc in SCALE_LADDER:
                    if sc["tag"] in cid or str(cenv.get("N_EMBD", "")) == sc["env"]["N_EMBD"]:
                        covered.add(sc["tag"]); matched = True
                if not matched and (c.get("exp_spec") or c.get("exp_confirmed")):
                    covered.add("124M")  # старый эмп-child без тега = базовый масштаб
            # собственный confirmed-прогон узла мог покрыть несколько ступеней (полная лестница
            # в одном RESULT_JSON) — эти теги тоже покрыты, сеем только следующую НОВУЮ ступень.
            _own = str(n.get("exp_confirmed") or "")[:20000]
            for sc in SCALE_LADDER:
                if sc["tag"] in _own:
                    covered.add(sc["tag"])
            nxt = next((sc for sc in SCALE_LADDER if sc["tag"] not in covered), None)
            if nxt is None:
                continue  # все масштабы покрыты → эта теорема проверена достаточно, к следующей
            # ПРЕДПОЧТЕНИЕ: если у родителя (эмп-подтверждённого) уже есть ВАЛИДИРОВАННЫЙ allowlisted
            # kind-скрипт (напр. llama_alignment_bridge_audit → exp_llama_checkpoint_pool_selector.py,
            # читает N_EMBD/N_LAYER/BATCH из env) — ПЕРЕИСПОЛЬЗУЕМ его на бОльшем масштабе. Такой скрипт
            # УЖЕ существует на диске → _ensure_exp_script возвращает его без автогена и БЕЗ код-ревью
            # (line 342) → scale-up гарантированно доходит до GPU. custom_llama-автоген же почти всегда
            # бракуется строгим ревьюером (и impossibility, и achievability) — вот почему running=НЕТ.
            pspec = n.get("exp_spec") if isinstance(n.get("exp_spec"), dict) else {}
            pkind = str(pspec.get("kind") or "")
            reuse = (pkind and pkind != "custom_llama"
                     and exp_spec.KIND_SCRIPTS.get(pkind))  # есть постоянный скрипт под этот kind
            claim = (f"Scale-up {nxt['tag']} подтверждённой эмп-проверки [{n['id']}]: "
                     f"{str(n.get('short',''))[:180]}")  # для child.idea (обе ветки)
            try:
                if reuse:
                    spec = exp_spec.canonicalize({
                        "kind": pkind,
                        "claim": pspec.get("claim") or claim,
                        "success_metric": pspec.get("success_metric") or "held-out метрика с bootstrap-CI",
                        "confirm_rule": pspec.get("confirm_rule") or "EMP_VERDICT=confirmed iff CI подтверждает",
                        "model": pspec.get("model"),
                        "env": dict(pspec.get("env") or {}, **nxt["env"], SEEDS="0,1,2,3,4,5"),
                    }, context=(str(n.get("short", "")) + " " + str(n.get("idea", ""))).lower(), exp_kind="llama")
                else:
                    claim = (f"Эмпирически проверить на РЕАЛЬНОЙ llama-сети масштаба {nxt['tag']} предсказание "
                             f"[{n['id']}]: {str(n.get('short',''))[:200]}. Методичка ACHIEVABILITY/предиктивная "
                             "(runnable, БЕЗ конструкции двух неразличимых миров): вычислить дешёвый source-probe "
                             "(source-gradient alignment ИЛИ знак source-Hessian вдоль обновления) на РЕАЛЬНОЙ "
                             "finetune-траектории и показать, что он предсказывает знак/величину source-retention "
                             "held-out по чекпоинтам ВЫШЕ chance. Перенос между доменами (wikitext↔shakespeare); "
                             "bootstrap-CI по >=3 уникальным seeds.")
                    spec = exp_spec.canonicalize({
                        "kind": "custom_llama", "claim": claim,
                        "success_metric": "held-out метрика теоремы с bootstrap-CI, исключающим тривиальный уровень",
                        "confirm_rule": "EMP_VERDICT=confirmed iff bootstrap-CI подтверждает предсказание теоремы",
                        "env": dict(nxt["env"], SEEDS="0,1,2,3,4,5"),
                    }, context=(str(n.get("short", "")) + " " + str(n.get("idea", ""))).lower(), exp_kind="llama")
            except ValueError:
                continue
            child = {
                "id": _unique_node_id(data, f"{n['id']}_emp_{nxt['tag']}"),
                "short": f"{str(n.get('short', n['id']))[:55]}: эмп-проверка на {nxt['tag']}",
                "parent": n["id"], "col": int(n.get("col") or 2),
                "status": "conditional", "idea": claim,
                "open": f"Держится ли предсказание теоремы на масштабе {nxt['tag']} (held-out, CI)?",
                "plan": "custom_llama аудит по методичке; confirmed→числа в derive; no_signal→честный предел масштаба.",
                "verdict": f"auto-seeded scale-up ({nxt['tag']}) эмпирической проверки headline-теоремы (GPU был свободен)",
                "elo": float(n.get("elo") or 2000.0), "attempts": 0, "exp_spec": spec,
            }
            data.setdefault("nodes", []).append(child)
            return child
        return None
    by = gio.index(data)
    ordered_ids: List[str] = []
    for nid in sorted(prefer_ids or []):
        if nid in by and nid not in ordered_ids:
            ordered_ids.append(nid)
    for sc in selector.score_nodes(data, cfg, exclude_running=True)[:30]:
        if sc.node_id not in ordered_ids:
            ordered_ids.append(sc.node_id)
    for nid in ordered_ids:
        node = by.get(nid)
        if not node or node.get("exp_refuted") or node.get("exp_spec"):
            continue
        ctx = " ".join(str(node.get(k) or "") for k in ("id", "short", "idea", "open"))
        try:
            kind = exp_spec.infer_kind(ctx)
            if kind not in _AUTO_SEED_KINDS:
                continue
            direct_ctx = " ".join(str(node.get(k) or "") for k in ("id", "short", "open")).lower()
            if kind == "rho_predictor" and not any(m in direct_ctx for m in _RHO_DIRECT_MARKERS):
                continue
            if _has_kind_child(data, node["id"], kind):
                continue
            spec = exp_spec.canonicalize({
                "kind": kind,
                "model": exp_spec.DEFAULT_MODEL,
                "claim": (
                    "Typed empirical probe for the parent frontier node: measure the "
                    "source Sigma_delta low-spectrum rho profile of the initial target "
                    "gradient on the configured model, and use it to check "
                    "whether the Fisher/depth profile is non-degenerate enough to support "
                    "the proposed sensitivity story."
                ),
                "success_metric": (
                    "FINAL has valid dimensions for all measured matrices, n_layers>=8, "
                    "finite rho_grad_weighted, and rho_range>=0.02."
                ),
                "confirm_rule": (
                    "EMP_VERDICT=confirmed iff rho_predictor router validates dimensions "
                    "and a non-degenerate rho profile; otherwise no_signal."
                ),
                "env": {"COV_BATCHES": "24", "GRAD_BATCHES": "2", "SEQ": "96", "BATCH": "4"},
            }, context=ctx, exp_kind=getattr(cfg, "exp_kind", ""))
        except ValueError:
            continue
        child = {
            "id": _unique_node_id(data, f"{node['id']}_{kind}"),
            "short": f"{node.get('short', node['id'])}: typed rho-profile probe",
            "parent": node["id"],
            "col": int(node.get("col") or 1) + 1,
            "status": "conditional",
            "idea": spec["claim"],
            "open": "Does the real-network Sigma_delta low-spectrum rho profile have enough non-degenerate structure to support this Fisher/depth branch?",
            "plan": "Run the typed rho_predictor GPU probe; if confirmed, write the measured profile into the branch; if no_signal, do not keep theorizing on this empirical premise.",
            "verdict": "auto-seeded typed experiment because the GPU lane was empty and no eligible EXP_SPEC candidate existed",
            "elo": node.get("elo", 1900.0),
            "attempts": 0,
            "exp_spec": spec,
        }
        data.setdefault("nodes", []).append(child)
        return child
    return None


def run_round(cfg: ARConfig, gate_repo: str, k: int = 2, max_workers: int = 2,
              max_rounds_per_node: int = 2, iter_no: int = 1) -> Dict[str, Any]:
    """Один раунд команды: выбрать k узлов → воркеры ведут параллельно → обновить store."""
    data = gio.load_graph(cfg)
    gio.ensure_fields(data)
    targets = selector.select_next(data, cfg, k)
    if not targets:
        return {"targets": [], "results": [], "note": "фронтир пуст"}
    by = gio.index(data)
    logger.info("supervisor: команда берёт узлы %s (gate=%s)", targets, gate_repo)
    gio.save_active(targets, cfg, detail="team round")
    try:
        agents_status.set_round(cfg, iter_no, targets)
        agents_status.log_event(cfg, "supervisor", f"итерация {iter_no}: команда берёт {', '.join(targets)}")
        agents_status.write_snapshot(cfg)
    except Exception:
        pass

    def _do(nid: str) -> Dict[str, Any]:
        node = by[nid]
        return agent_worker.work_node(node, _memory(data, node, cfg), cfg, gate_repo,
                                      max_rounds=max_rounds_per_node,
                                      lineage_ids=_lineage_ids(data, node))

    results: List[Dict[str, Any]]
    try:
        if max_workers > 1 and len(targets) > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                results = list(ex.map(_do, targets))
        else:
            results = [_do(t) for t in targets]
    finally:
        gio.save_active([], cfg)

    for r in results:
        agent_worker.apply_result(data, r)
    gio.save_graph(data, cfg)
    gio.regen_canvas(cfg)
    pend = inbox.list_pending(cfg)
    return {"targets": targets, "results": results,
            "passed": [r["node"] for r in results if r.get("gate_passed")],
            "inbox_pending": pend}


def run(cfg: ARConfig, gate_repo: str, k: int = 2, rounds: int = 1,
        max_workers: int = 2) -> List[Dict[str, Any]]:
    out = []
    for i in range(rounds):
        logger.info("=== supervisor round %d/%d ===", i + 1, rounds)
        out.append(run_round(cfg, gate_repo, k, max_workers, iter_no=i + 1))
    return out


_DIRECTIVE_RESEARCH_MARKERS = ("теорем", "докаж", "bridge", "таблиц", "сравнен", "инстанц",
                               "bound", "lower", "характериз", "перенес", "comparison")


def _seed_directive_nodes(cfg: ARConfig, max_new: int = 2) -> List[str]:
    """Нумерованные DIRECTIVES A*-критика → рабочие узлы графа (вызывать под glock).

    WEAK_NODES рождают pressure-узлы, а research-директивы (bridge-теорема, theorem-comparison
    таблица, инстанцирование bounds) доходили только до писателя — идейные воркеры их не брали.
    Сеем детей под HEADLINE-узлом; id = стабильный хэш текста директивы → повторный цикл с той же
    директивой НЕ создаёт дубль (id уже в графе)."""
    import hashlib
    fbp = os.path.join(cfg.workdir, "astar_feedback.md")
    try:
        fbtxt = open(fbp, encoding="utf-8").read()
    except OSError:
        return []
    dm = re.search(r"DIRECTIVES:(.*?)(?=\nCORNERSTONE:|\nWEAK_NODES:|\nDEMOTE_NODE:|\nSCORE:|\Z)",
                   fbtxt, re.DOTALL)
    hm = re.search(r"HEADLINE:\s*([A-Za-z0-9_\-]+)", fbtxt)
    if not dm or not hm or "нет" in hm.group(1).lower():
        return []
    headline = hm.group(1)
    items = [it.strip() for it in re.split(r"\n?\s*\d+\.\s+", dm.group(1)) if len(it.strip()) > 60]
    data = gio.load_graph(cfg)
    gio.ensure_fields(data)
    by = gio.index(data)
    if headline not in by:
        return []
    seeded: List[str] = []
    for it in items:
        low = it.lower()
        if not any(mk in low for mk in _DIRECTIVE_RESEARCH_MARKERS):
            continue  # редакционные директивы («убери», «раздели язык») выполняет писатель
        nid = "directive_" + hashlib.sha1(it[:200].encode()).hexdigest()[:8]
        if nid in by:
            continue
        data["nodes"].append({
            "id": nid, "parent": headline, "col": 2, "status": "open",
            "short": ("ДИРЕКТИВА A*: " + it)[:120],
            "idea": it[:800],
            "open": "выполнить директиву A*-критика (несущая для балла)",
            "elo": 2100.0, "attempts": 0,
        })
        by[nid] = data["nodes"][-1]
        seeded.append(nid)
        if len(seeded) >= max_new:
            break
    if seeded:
        gio.save_graph(data, cfg)
        gio.regen_canvas(cfg)
        logger.info("[директива→узел] создано %d узлов под [%s]: %s",
                    len(seeded), headline, ", ".join(seeded))
    return seeded


def run_continuous(cfg: ARConfig, gate_repo: str, k: int = 1, max_workers: int = 1,
                   max_iters: int = 1000, report_every_passed: int = 4) -> List[Dict[str, Any]]:
    """ПУЛ непрерывных ИДЕЙНЫХ воркеров: каждый, освободившись, СРАЗУ берёт новую идею (без
    барьера раунда). Эксперименты (фаза подтверждения + poll) идут в ГЛАВНОМ потоке ОТДЕЛЬНО —
    они НЕ занимают идейный слот, поэтому идейных всегда ровно max_workers. Главный поток также
    подбирает завершённые эксперименты и запускает report-cycle. Останов: <workdir>/STOP / max_iters.
    """
    from . import evolution, paper, report_trigger, empirical
    import datetime
    import threading
    import time
    stop_file = os.path.join(cfg.workdir, "STOP")
    os.makedirs(cfg.workdir, exist_ok=True)
    glock = threading.Lock()       # сериализует read-modify-write graph.json (воркеры + главный)
    slock = threading.Lock()       # active set + new_passed + last_evolve + cornerstone
    # cornerstone: id узла идущего КРАЕУГОЛЬНОГО эксперимента (или None) — пока он бежит, мыслители
    # отдыхают, а confirm-фаза не плодит конкурирующие прогоны. last_evolve: троттлинг эволюции.
    S: Dict[str, Any] = {"active": set(), "new_passed": [], "stop": False,
                         "last_evolve": 0.0, "cornerstone": None,
                         # ДЕМПФЕР (02-08): рестарт орха не должен разрешать отчёт немедленно —
                         # серия рестартов давала циклы подряд («вечная сборка отчёта» у юзера).
                         # После старта первый плановый цикл не раньше чем через 1ч (форс-триггер
                         # свежего exp-вердикта работает как раньше, в обход).
                         "last_report": max(_latest_report_mtime(cfg), time.time() - 10800.0)}
    # ГИГИЕНА БАННЕРА (02-08): рестарт посреди report-цикла оставлял карточку
    # «СОСТАВИТЕЛЬ: writing» и флаг сборки залипшими → сайт вечно показывал
    # «идёт сборка отчёта». На старте принудительно гасим.
    try:
        agents_status.report_flag(cfg, False)
        for _ag in ("СОСТАВИТЕЛЬ-отчёта", "A*-критик-отчёта"):
            agents_status.update(cfg, _ag, node="ОТЧЁТ", short="отчёт по всем узлам",
                                 stage="idle", detail="рестарт орха: сборка отчёта не идёт")
        agents_status.write_snapshot(cfg)
    except Exception:
        pass
    try:
        # Raw confirmed typed experiments are valid report material even before
        # the post-exp branch writeup passes its own gate. Seed them on restart
        # so deploying/restarting the supervisor does not lose the report trigger.
        d_start = gio.load_graph(cfg)
        S["new_passed"] = (
            _needs_writeup_ids(d_start)
            + _fresh_refuted_ids(d_start, cfg)
            + _fresh_pressure_passed_ids(d_start, cfg)
        )
    except Exception:
        S["new_passed"] = []
    # A killed/restarted report-cycle can leave _report.json saying "active".
    # A fresh supervisor owns the dashboard state, so clear stale report banners
    # and stale active slots from workers that died with the old process.
    agents_status.report_flag(cfg, False, "startup")
    gio.save_active([], cfg, detail="startup clear stale active slots")
    EVOLVE_COOLDOWN = 180.0        # эволюцию (спекулятивные узлы) — не чаще раза в 3 мин
    REPORT_COOLDOWN = 14400.0      # отчёт A*-критику — не чаще раза в 4 ЧАСА (правка 31-07 по требованию
                                   # юзера: цикл писатель+критик гонялся каждые 30 мин от любого мелкого
                                   # gate-PASS, попытки стабильно проигрывали рэтчету → вечный баннер
                                   # «сборка отчёта» без прогресса. Свежий typed-эксп вердикт триггерит
                                   # отчёт НЕМЕДЛЕННО в обход кулдауна (raw_confirmed/refuted_new) —
                                   # реальный материал ждать 4ч не будет).
    STALE_REPORT = 7200.0          # только как диагностический порог; не форсим отчёт без новых результатов
    out: List[Dict[str, Any]] = []

    def _ancestor_running(nid, by):
        """Истинность узла висит на in-flight эксперименте предка → строить на нём ещё рано."""
        return any(a.get("status") == "experiment_running" for a in gio.ancestors(nid, by))

    def _claim():
        """Свободный идейный воркер берёт узел фронтира. НЕ берёт: дубль активных; узел, чей
        предок сейчас в эксперименте (ждём результат, не строим на неподтверждённом).
        ВО ВРЕМЯ cornerstone мыслители ПРОДОЛЖАЮТ работу на ДРУГИХ ветках (не вся команда стоит) —
        блокируется только поддерево самого cornerstone-узла (через _ancestor_running) и confirm-фаза."""
        with glock:
            data = gio.load_graph(cfg); gio.ensure_fields(data)
            pressure_nodes = _ensure_pressure_repair_nodes(data, cfg)
            if pressure_nodes:
                gio.save_graph(data, cfg); gio.regen_canvas(cfg)
                logger.info("pressure repair nodes ready: %s", ",".join(pressure_nodes[:8]))
        by = gio.index(data)
        with slock:
            # A fresh no-cornerstone review can collapse old pressure_<weak>
            # repair work into pressure_scope_pivot. Drop stale/off-target
            # pressure slots before selecting more work, otherwise active.json
            # can keep workers on nodes the critic just told us to prune.
            try:
                unresolved_pressure = set(selector.pressure_unresolved_targets(data, cfg))
            except Exception:
                unresolved_pressure = set()
            if unresolved_pressure:
                before_active = set(S["active"])

                def _active_pressure_target(nid: str) -> str:
                    node = by.get(nid) or {}
                    if not str(nid).startswith("pressure_"):
                        return ""
                    return str(node.get("pressure_target") or str(nid)[len("pressure_"):]).strip()

                S["active"] = {
                    nid for nid in S["active"]
                    if not (str(nid).startswith("pressure_")
                            and _active_pressure_target(str(nid)) not in unresolved_pressure)
                }
                if S["active"] != before_active:
                    gio.save_active(list(S["active"]), cfg, detail="drop off-target pressure active")
            # РАЗНООБРАЗИЕ: не больше cap воркеров в одной col-1 ветке → хотя бы один всегда
            # разведывает другую линию (иначе headline-буст вырождает команду в одну ветку).
            cap = max(1, max_workers - 1)
            active_branch: Dict[str, int] = {}
            for anid in S["active"]:
                b = paper._branch_of(anid, by) or anid
                active_branch[b] = active_branch.get(b, 0) + 1
            # РЕЗЕРВ РАЗВЕДКИ (проект-агностично): не больше (max_workers-1) воркеров на pressure-узлах
            # одновременно → хотя бы один всегда двигает свежий фронтир/пивот/эволюцию. Иначе
            # sub-threshold A*-отчёт плодит pressure без конца и монополизирует всю команду на
            # ремонте старой (возможно, тупиковой) истории, а новые идеи голодают.
            pressure_cap = max(1, max_workers - 1)
            active_pressure = sum(1 for anid in S["active"] if str(anid).startswith("pressure_"))
            # ДВА ПРОХОДА: сперва с резервом разнообразия (не >cap воркеров на одну col-1 ветку),
            # затем — БЕЗ него. Иначе, когда весь фронтир в ОДНОЙ ветке (напр. theme_core), второй
            # идейный воркер структурно голодает и отдыхает при непустом фронтире. Разнообразие =
            # предпочтение, а не повод простаивать: лучше копать ту же ветку, чем ничего.
            for relax_branch in (False, True):
                for nid in selector.select_next(data, cfg, max_workers + len(S["active"]) + 6):
                    if nid in S["active"]:
                        continue
                    node = by.get(nid)
                    if (str(nid).startswith("pressure_")
                            and active_pressure >= pressure_cap
                            and not graph_hygiene.needs_writeup_priority(node or {})):
                        continue  # резерв разведки исчерпан pressure-узлами → пропускаем, ищем свежий фронтир
                    if (node
                            and node.get("status") in ("conditional", "proven")
                            and isinstance(node.get("exp_spec"), dict)
                            and not graph_hygiene.typed_exp_confirmed(node)
                            and not node.get("exp_refuted")):
                        continue  # typed EXP_SPEC belongs to the GPU confirm lane, not idea workers
                    if _ancestor_running(nid, by):
                        continue  # правда ветки решается экспериментом предка → ждём, не дивергируем
                    b = paper._branch_of(nid, by) or nid
                    if (not relax_branch
                            and active_branch.get(b, 0) >= cap
                            and not graph_hygiene.needs_writeup_priority(node or {})):
                        continue  # 1-й проход: держим разнообразие; 2-й проход берёт и эту ветку (не простаивать)
                    S["active"].add(nid)
                    gio.save_active(list(S["active"]), cfg, detail="worker claimed node")
                    return data, node
        return data, None

    def _rest(wid: int, why: str):
        """Мыслитель ОТДЫХАЕТ (ничего не делает, не жжёт токены) — видно на дашборде."""
        try:
            agents_status.update(cfg, f"idea-rest-{wid}", node="—", short="отдых",
                                 stage="resting", detail=why,
                                 engine=cfg.engines.writer, role="идейный агент (отдых)")
            agents_status.write_snapshot(cfg)
        except Exception:
            pass

    def _worker(wid: int):
        while not S["stop"]:
            node = None
            try:
                data, node = _claim()
                if node is None:  # брать нечего
                    unresolved_pressure = selector.pressure_unresolved_targets(data, cfg)
                    if unresolved_pressure:
                        _rest(wid, "pressure repair идёт — жду свободный unresolved target: "
                              + ", ".join(unresolved_pressure[:4]))
                        time.sleep(45); continue
                    with slock:
                        corner = S["cornerstone"] is not None
                    if corner:
                        # только КРАЕУГОЛЬНЫЙ эксп блокирует (мысль зависит от его результата);
                        # обычные pending-экспы идейных НЕ усыпляют — держим >=2 идейных агента в работе
                        # (генерят новые идеи через evolve ниже), иначе команда простаивает во время экспов.
                        _rest(wid, "краеугольный эксп бежит — жду результат")
                        time.sleep(45); continue
                    # ждать нечего и фронтир пуст → эволюция, но троттл (не каждые 5с — токен-жор)
                    now = time.time()
                    with slock:
                        do_evolve = (now - S["last_evolve"]) > EVOLVE_COOLDOWN
                        if do_evolve:
                            S["last_evolve"] = now
                    if do_evolve:
                        with glock:
                            d = gio.load_graph(cfg); gio.ensure_fields(d)
                            guard = __import__("autoresearch.dedup_guard", fromlist=["DedupGuard"]).DedupGuard(d, cfg)
                            added = evolution.evolve_into_graph(
                                d, cfg, 3, guard_check=lambda t: not guard.check(t).is_dup)
                            if added:
                                gio.save_graph(d, cfg); gio.regen_canvas(cfg)
                    else:
                        _rest(wid, "фронтир пуст, эволюция на кулдауне")
                    time.sleep(15); continue
                res = agent_worker.work_node(node, _memory(data, node, cfg), cfg, gate_repo,
                                             max_rounds=2, lineage_ids=_lineage_ids(data, node))
                with slock:
                    S["active"].discard(node["id"])
                    gio.save_active(list(S["active"]), cfg, detail="worker finished node")
                    if res and res.get("gate_passed"):
                        S["new_passed"].append(res["node"])
                if res:
                    with glock:
                        d = gio.load_graph(cfg); gio.ensure_fields(d)
                        agent_worker.apply_result(d, res); gio.save_graph(d, cfg); gio.regen_canvas(cfg)
                    if isinstance(res, dict) and res.get("rw_append"):
                        with glock:
                            d = gio.load_graph(cfg); gio.ensure_fields(d)
                            n = gio.index(d).get(node["id"])
                            if n is not None:
                                litreview.append_rw(cfg, n, res["rw_append"])
                                gio.save_graph(d, cfg); gio.regen_canvas(cfg)
                                logger.info("[lit] агент-RW_SEARCH дополнил узел %s", node["id"])
            except Exception as e:
                logger.warning("идейный воркер %d упал: %s", wid, e)
                with slock:
                    S["active"].discard(node["id"]) if node else None
                    gio.save_active(list(S["active"]), cfg, detail="worker exception")
                time.sleep(3)

    LIB_COOLDOWN = 30.0  # библиотекарь: пауза, когда все узлы фронтира уже с RW

    def _librarian():
        """Фоновый БИБЛИОТЕКАРЬ: обогащает узлы фронтира Related Work (обязательно у каждого).
        Источники: локальный индекс <тема>/literature/_index.jsonl + живой веб-поиск (движок cfg.engines.librarian).
        Медленный (web+LLM) → по одному узлу с троттлом; пишет node.related_work под glock (без клоббера)."""
        idx = None
        while not S["stop"]:
            try:
                with glock:
                    data = gio.load_graph(cfg); gio.ensure_fields(data)
                by = gio.index(data)
                cand = None
                for sc in selector.score_nodes(data, cfg, exclude_running=False)[:40]:
                    n = by.get(sc.node_id)
                    if n and n.get("col") not in (0, None) and not litreview.has_rw(n):
                        cand = n; break
                if cand is None:
                    time.sleep(LIB_COOLDOWN); continue
                if idx is None:
                    idx = litreview.load_index(cfg)
                nid = cand["id"]
                agents_status.update(cfg, "librarian", node=nid, short=str(cand.get("short", ""))[:40],
                                     stage="lit_review", detail="ищу related work (библиотека+веб)",
                                     engine=cfg.engines.librarian, role="библиотекарь")
                agents_status.write_snapshot(cfg)
                rw = litreview.make_related_work(cfg, cand, idx)  # slow (web) — ВНЕ glock
                if rw and "RELATED_WORK" in rw:
                    with glock:
                        d = gio.load_graph(cfg); gio.ensure_fields(d)
                        n = gio.index(d).get(nid)
                        if n is not None and not litreview.has_rw(n):
                            litreview.set_rw(cfg, n, rw)
                            gio.save_graph(d, cfg); gio.regen_canvas(cfg)
                            logger.info("[lit] RW добавлен узлу %s", nid)
                time.sleep(5)
            except Exception as e:
                logger.warning("библиотекарь упал: %s", e); time.sleep(20)

    nworkers = max(1, max_workers)
    pool = [threading.Thread(target=_worker, args=(i,), daemon=True) for i in range(nworkers)]
    for w in pool:
        w.start()
    threading.Thread(target=_librarian, daemon=True).start()
    logger.info("пул идейных воркеров: %d непрерывных + библиотекарь (RW) — эксперименты отдельно", nworkers)

    last_score: Optional[int] = _latest_score(cfg)
    MIN_FOR_CHECK = 8              # (31-07) 3 мелких gate-PASS набирались за полчаса → цикл крутился впустую
    # ФИКС ВОЛНЫ 177, ВОССТАНОВЛЕН ВОЛНОЙ 184 (был потерян перезаписью supervisor.py с Мака —
    # тот же инцидент, что съел `_unwedge_phantom_experiment_nodes`): слив/запуск экспериментов
    # вынесен из тела главного цикла в НАЗЫВАЕМУЮ функцию, чтобы её можно было «прокачивать» и
    # ВО ВРЕМЯ долгого отчётного цикла. Пока paper.generate_paper() (писатель + median-of-3
    # критик, до 2 раундов = 30-60 мин) стоит синхронно в этом же цикле, завершившиеся на GPU
    # прогоны висят running весь отчёт, их вердикты не доезжают до графа, waiting-записи не
    # переразмещаются, гигиена фантомов не идёт, а слоты max_concurrent_exp остаются занятыми →
    # новые прогоны (в т.ч. пересеянные под требования рецензента) НЕ стартуют, GPU простаивает.
    dlock = threading.Lock()

    def _drain_exp(it):
        """poll вердиктов + фаза подтверждения. Реентерантность запрещена (главный цикл vs pump)."""
        if not dlock.acquire(blocking=False):
            return
        try:
            _drain_exp_body(it)
        finally:
            dlock.release()

    def _drain_exp_body(it):
        # 1) подобрать завершённые эксперименты, применить вердикт (ОТДЕЛЬНО от идейных воркеров)
        try:
            fin = empirical.poll(cfg)
            if fin:
                with glock:
                    d0 = gio.load_graph(cfg); gio.ensure_fields(d0); by0 = gio.index(d0)
                    for f in fin:
                        n = by0.get(f["nid"])
                        if not n:
                            continue
                        # ПОЛНЫЙ exp-лог + ВСЕ per-seed → на узел, для ЛЮБОГО вердикта (в т.ч. no_signal/
                        # refuted). Идейные агенты и reporter видят сырые числа (multi-scale таблица).
                        if f.get("exp_log_file"):
                            logs = n.get("exp_log_files")
                            n["exp_log_files"] = ([logs] if isinstance(logs, str) else list(logs or []))
                            if f["exp_log_file"] not in n["exp_log_files"]:
                                n["exp_log_files"].append(f["exp_log_file"])
                            n["exp_log_files"] = n["exp_log_files"][-6:]  # последние 6 прогонов узла
                        if f.get("per_seed"):
                            n["exp_per_seed"] = str(f["per_seed"])[:20000]  # сырьё per-seed для таблицы
                        if f["verdict"] == "confirmed" and not f.get("exp_spec"):
                            n.pop("needs_exp_rerun", None)
                            n["status"] = f.get("prev_status") or n.get("status") or "conditional"
                            n["last_gate"] = ("real experiment result ignored: missing typed EXP_SPEC; "
                                              "rerun through the typed router before using as evidence")
                        elif f["verdict"] == "confirmed":
                            # НЕ застываем: узел возвращается СВОЕМУ агенту (ветка idea/<nid> + память)
                            # дописать реальные числа в derive и пройти гейт уже с подтверждением.
                            exp_summary = _exp_confirmed_summary(f)
                            n["status"] = "needs_writeup"
                            if f.get("exp_spec"):
                                n["exp_spec"] = f["exp_spec"]
                            n["exp_confirmed"] = exp_summary
                            n["exp_result_json"] = str(f.get("rj") or "")[:20000]  # raw RESULT_JSON → provenance appendix (W1)
                            n.pop("needs_exp_rerun", None)
                            n["writeup_attempts"] = 0
                            label = _exp_evidence_label(n.get("exp_spec") or {})
                            n["last_gate"] = ("ТВОЙ реальный LLM-эксперимент ПРОШЁЛ typed confirm_rule: "
                                              f"{label}. {exp_summary[:360]}. Это про ЭТОТ узел. Впиши эти "
                                              "РЕАЛЬНЫЕ числа в derive.md как эмпирическое подтверждение "
                                              "ровно в рамках confirm_rule; не обещай дополнительные артефакты "
                                              "или метрики, которых нет в RESULT_JSON.")
                            with slock:
                                S["new_passed"].append(f["nid"])
                        elif f["verdict"] == "invalid":
                            n.pop("needs_exp_rerun", None)
                            n["status"] = f.get("prev_status") or n.get("status") or "open"
                            # научный статус не меняем (infra-fail, не no_signal), но помечаем
                            # mechanical_invalid_exp → guard'ы (их раньше никто не выставлял) исключат
                            # узел из повторного авто-запуска того же сломанного прогона.
                            n["mechanical_invalid_exp"] = True
                            n["last_gate"] = (f"реальный эксперимент НЕВАЛИДЕН/infra-fail: "
                                              f"{f['rj'][:240]}. Не считать no_signal и не менять научный статус.")
                        else:
                            exp_summary = _exp_confirmed_summary(f)
                            esc = int(n.get("exp_escalations", 0) or 0)
                            spec = n.get("exp_spec") if isinstance(n.get("exp_spec"), dict) else None
                            if f.get("exp_spec") and isinstance(f["exp_spec"], dict):
                                spec = f["exp_spec"]
                                n["exp_spec"] = spec
                            # no_signal часто = НЕДОМОЩНОСТЬ, не отсутствие эффекта. Не замораживаем узел:
                            # эскалируем дизайн (seeds/модель/чекпоинты/eval) и авто-переприоняем, до ESC_BUDGET.
                            if f["verdict"] == "no_signal" and esc < ESC_BUDGET and spec is not None:
                                lvl = esc + 1
                                spec["env"] = _escalate_power_env(spec.get("env") or {}, lvl)
                                n["exp_escalations"] = lvl
                                n["needs_exp_rerun"] = True
                                n.pop("exp_refuted", None)
                                n.pop("exp_refuted_at", None)
                                n.pop("mechanical_invalid_exp", None)
                                n["status"] = "conditional"  # confirm-lane берёт только conditional/proven
                                n["verdict"] = (f"no_signal на power-level {esc} — вероятно недомощность; "
                                                f"авто-эскалация дизайна до level {lvl} и переприон")
                                n["last_gate"] = (
                                    f"no_signal (level {esc}) — не заморозка: усиливаю мощность "
                                    f"(seeds/слои/ширина/чекпоинты/eval, level {lvl}) и перезапускаю GPU-прогон. "
                                    f"{exp_summary[:240]}")
                                logger.info("[эксп %s] no_signal → ЭСКАЛАЦИЯ мощности level %d, переприон",
                                            f["nid"], lvl)
                            else:
                                # бюджет исчерпан ИЛИ чистое refutation → честный терминальный результат
                                n.pop("needs_exp_rerun", None)
                                n["status"] = "open"
                                n["exp_refuted"] = exp_summary
                                n["exp_result_json"] = str(f.get("rj") or "")[:20000]  # raw RESULT_JSON → provenance appendix (W1)
                                n["exp_refuted_at"] = time.time()
                                settled = (f" (settled-null после {esc} эскалаций мощности)"
                                           if f["verdict"] == "no_signal" and esc else "")
                                n["verdict"] = (f"Typed real experiment did NOT confirm the claim "
                                                f"({f['verdict']}){settled}: {exp_summary[:900]}")
                                n["last_gate"] = (f"реальный эксперимент НЕ подтвердил ({f['verdict']}){settled}: "
                                                  f"{exp_summary[:360]}. Сузь формулировку до подтверждённого.")
                                if f.get("exp_spec"):
                                    with slock:
                                        S["new_passed"].append(f["nid"])
                        logger.info("[эксп %s] вердикт=%s → %s", f["nid"], f["verdict"], n["status"])
                        # ГЛОБАЛЬНЫЙ ДАЙДЖЕСТ ЭКСПЕРИМЕНТОВ (02-08): каждый вердикт — строка в
                        # .run/exp_results_digest.md; блок вклеивается в память ВСЕХ идейных агентов,
                        # чтобы теоретики видели свежие числа и быстро проверяли гипотезы об данные.
                        try:
                            import json as _j
                            _dig = os.path.join(cfg.workdir, ".run", "exp_results_digest.md")
                            _sc_line = ""
                            try:
                                _pj = _j.loads(f.get("rj") or "{}")
                                _parts = []
                                for _s in (_pj.get("scales") or []):
                                    if _s.get("oom"):
                                        _parts.append(str(_s.get("tag")) + ":OOM")
                                        continue
                                    _ci = ((_s.get("target_only_control") or {}).get("sign_accuracy") or {}).get("CI")
                                    _parts.append("%s:%s,ctrl_acc_CI=%s" % (_s.get("tag"), _s.get("confirmed_direction"), _ci))
                                _sc_line = " dirs=%s | %s" % (_pj.get("confirmed_directions"), "; ".join(_parts))
                            except Exception:
                                pass
                            _entry = "- %s [%s] вердикт=%s%s | полные логи: Results/exp_logs/\n" % (
                                time.strftime("%d-%m %H:%M"), f["nid"][:50], f["verdict"], _sc_line)
                            _old = open(_dig, encoding="utf-8").read() if os.path.exists(_dig) else ""
                            _lines = (_entry + _old).splitlines(keepends=True)[:30]
                            open(_dig, "w", encoding="utf-8").write("".join(_lines))
                        except Exception as _e:
                            logger.warning("exp-дайджест не записан: %s", _e)
                    gio.save_graph(d0, cfg); gio.regen_canvas(cfg)
                    with slock:
                        if S["cornerstone"] and any(f["nid"] == S["cornerstone"] for f in fin):
                            logger.info("[краеугольный] %s завершён → разблокирую команду", S["cornerstone"])
                            S["cornerstone"] = None
        except Exception as e:
            logger.warning("poll экспериментов упал: %s", e)
        # 1b) РАСКЛИНИТЬ ФАНТОМЫ: узел в experiment_running без живой записи прогона (фикс волны 179,
        # восстановлен волной 183 — вызов был потерян при позднейших правках файла).
        try:
            with glock:
                dph = gio.load_graph(cfg); gio.ensure_fields(dph)
                freed = _unwedge_phantom_experiment_nodes(dph, cfg)
                if freed:
                    gio.save_graph(dph, cfg); gio.regen_canvas(cfg)
            if freed:
                logger.info("[гигиена] расклинил фантомные experiment_running без записи: %s",
                            ", ".join(freed[:6]) + (" …" if len(freed) > 6 else ""))
        except Exception as e:
            logger.warning("расклинивание фантомов упало: %s", e)
        # 2) ФАЗА ПОДТВЕРЖДЕНИЯ — запускает эксперимент в главном потоке (идейные слоты не трогает)
        try:
            with slock:  # сейф: краеугольный помечен, но прогонов в полёте нет → флаг завис, снять
                if S["cornerstone"] and empirical.pending_count(cfg) == 0:
                    S["cornerstone"] = None
                corner_now = S["cornerstone"] is not None
            if getattr(cfg, "empirical_in_loop", False) and not corner_now:
                MAX_EXP = getattr(cfg, "max_concurrent_exp", 0) or max(1, len(empirical._servers(cfg)))
                if empirical.pending_count(cfg) < MAX_EXP:
                    with glock:
                        dc = gio.load_graph(cfg); gio.ensure_fields(dc)
                    cand = _pick_confirm_candidate(dc, cfg)
                    # НЕПРЕРЫВНЫЙ ПАРАЛЛЕЛЬНЫЙ ПОТОК: сеем новый эксп-узел, пока есть СВОБОДНЫЙ слот
                    # (pending < MAX_EXP), а не только при полном простое (==0). Иначе при 1 бегущем
                    # эксперименте и отсутствии готовых кандидатов слоты 2..MAX простаивали, а
                    # экспериментаторы стояли. Теперь GPU-слоты заполняются до отказа параллельно идеям.
                    if cand is None and empirical.pending_count(cfg) < MAX_EXP:
                        with slock:
                            active_now = list(S["active"])
                        cand = _seed_confirm_candidate(dc, cfg, active_now)
                        if cand is None:
                            cand = _seed_cornerstone_candidate(dc, cfg, _latest_feedback_cornerstone(cfg))
                        if cand is not None:
                            gio.save_graph(dc, cfg); gio.regen_canvas(cfg)
                            logger.info("[tick %d] auto-seeded EXP_SPEC[%s] child %s under %s",
                                        it + 1, (cand.get("exp_spec") or {}).get("kind"),
                                        cand.get("id"), cand.get("parent"))
                        else:
                            backlog = _needs_writeup_ids(dc)
                            fresh_refuted = _fresh_refuted_ids(dc, cfg)
                            if fresh_refuted:
                                detail = (
                                    "GPU idle; свежий typed EXP_SPEC уже дал no_signal/refuted — "
                                    "форсю свежий A*-отчёт/pivot: "
                                    + ", ".join(fresh_refuted[:4])
                                )
                                if len(fresh_refuted) > 4:
                                    detail += "…"
                            elif backlog:
                                detail = ("GPU idle; post-exp writeup идёт отдельно, отчёт не блокируется: "
                                          + ", ".join(backlog[:4]))
                                if len(backlog) > 4:
                                    detail += "…"
                            else:
                                detail = (
                                    "GPU idle; нет eligible typed EXP_SPEC — активные ветки должны "
                                    "сначала пройти proof/code gate или явно запросить EXP_SPEC"
                                )
                            agents_status.update(
                                cfg, "agent-experimenter", node="EXP_SPEC",
                                short="typed experiment lane",
                                stage="idle", detail=detail,
                                engine="codex→GPU",
                                role="экспериментатор (typed EXP_SPEC)",
                            )
                    if cand and cand["id"] not in S["active"]:
                        rec = empirical.launch(cand, cand.get("idea", ""), cfg)
                        if rec.get("status") in ("running", "waiting"):
                            with glock:
                                d2 = gio.load_graph(cfg); gio.ensure_fields(d2)
                                n2 = gio.index(d2).get(cand["id"])
                                if n2:
                                    n2["status"] = "experiment_running"
                                    if rec.get("exp_spec"):
                                        n2["exp_spec"] = rec["exp_spec"]
                                    gio.save_graph(d2, cfg)
                            logger.info("[tick %d] фаза подтверждения: %s → EXP_SPEC[%s]",
                                        it + 1, cand["id"], rec.get("kind"))
                        else:
                            with glock:
                                d2 = gio.load_graph(cfg); gio.ensure_fields(d2)
                                n2 = gio.index(d2).get(cand["id"])
                                if n2:
                                    n2["last_gate"] = f"typed EXP_SPEC router refused: {rec.get('error','unknown')}"[:400]
                                    # ПОМЕЧАЕМ заблокированным: guard'ы (_pick_confirm_candidate/selector)
                                    # читают policy_blocked_exp, но раньше его НИКТО не выставлял → узел
                                    # переотбирался и launch отказывал каждый тик (relaunch-петля).
                                    n2["policy_blocked_exp"] = True
                                    gio.save_graph(d2, cfg)
        except Exception as e:
            logger.warning("фаза подтверждения упала: %s", e)

    for it in range(max_iters):
        if os.path.exists(stop_file):
            logger.info("STOP-файл найден → останавливаю (тиков: %d)", it); break
        _drain_exp(it)
        # 3) отчёт: НЕ спамим. Раньше каждый подтверждённый эксп безусловно форсил полный opus-отчёт →
        # отчёты строчили постоянно (и до того, как числа попадали в материал). Теперь ворота:
        #   (a) прошёл cooldown 30 мин с прошлого отчёта;
        #   (b) накопилось >= MIN_FOR_CHECK новых прошедших результатов;
        #   (c) эксперименты ДОБЕЖАЛИ (pending==0) — не судим статью, пока раны в полёте; safety-клапан:
        #       если ждём уже 2×cooldown, отчитываемся даже при живых ранах (пул бывает занят всегда).
        # Только при всех воротах зовём codex-планировщика (он решает, достаточно ли связного материала).
        do_rep = False
        now_r = time.time()
        with slock:
            np_snapshot = list(S["new_passed"])
            since_report = now_r - S["last_report"]
        pend_now = empirical.pending_count(cfg)
        # ФИКС ВОЛНЫ 210 (ОТЧЁТНЫЙ ЦИКЛ БЫЛ ЗАПЕРТ НА 8 ЧАСОВ ПРИ ЗАЯВЛЕННЫХ 4). `quiescent` требовал
        # `pend_now == 0`, то есть НИ ОДНОЙ записи прогона в полосе GPU, а клапан стоял на 2×cooldown =
        # 8 ч. Но `pending_count` считает и `waiting`-записи со скриптом (docstring `_holds_gpu_slot`),
        # а три записи 760M ФИЗИЧЕСКИ неразмещаемы (нужна карта >=44 ГБ, которой нет ни на одном сервере
        # пула; одна из них ещё и в карантине по трейсбэку) ⇒ `pend_now >= 3` НАВСЕГДА ⇒ единственным
        # триггером отчёта оставался 8-часовой клапан. Замер волны 210: `pend_now = 5` при MAX_EXP = 4,
        # прошлые публикации 31-07 09:24 → 01-08 02:04 (разрыв 16,7 ч). Кулдаун 4 ч — ТРЕБОВАНИЕ ЮЗЕРА
        # (31-07) и он НЕ трогается; тормозом остаётся он, а не «раны в полёте»: пока 10-12-часовой
        # прогон идёт, теория (ось N — единственная независимо закрываемая) не доезжала до критика.
        quiescent = (pend_now == 0) or (since_report >= REPORT_COOLDOWN)
        stale = since_report >= STALE_REPORT
        with glock:
            d_report_state = gio.load_graph(cfg)
            writeup_backlog = _needs_writeup_ids(d_report_state)
            refuted_backlog = _fresh_refuted_ids(d_report_state, cfg)
        raw_confirmed_new = bool(set(np_snapshot) & set(writeup_backlog))
        raw_refuted_new = bool(set(np_snapshot) & set(refuted_backlog))
        # ГОТОВАЯ ЭМПИРИКА (writeup_exhausted: confirmed-эксп есть, но writeup не прошёл контракт-гейт
        # → узел conditional, НЕ needs_writeup и НЕ свежий gate-PASS). Раньше такой узел НЕ триггерил
        # отчёт → когда гейт занят трудными узлами (24/25 REJECT), confirmed-эмпирика висела неучтённой,
        # отчёт застревал на старом скоре. Теперь готовая эмпирика — валидный повод собрать отчёт.
        exhausted_ids = frozenset(str(n.get("id")) for n in d_report_state.get("nodes", [])
                                  if graph_hygiene.writeup_exhausted(n))
        # exhausted_emp ПЕРМАНЕНТНО истинен (achiev навсегда writeup_exhausted) → как триггер он
        # ОТКЛЮЧАЛ требование нового материала: отчёт собирался каждый cooldown back-to-back и жёг
        # codex на пере-суде того же текста (юзер видел «отчёт каждые 10 минут»). Триггерим только
        # когда НАБОР exhausted-узлов изменился с последнего отчёта, + страховка от голодания (2ч).
        with slock:
            exhausted_new = exhausted_ids != S.get("exhausted_reported")
        exhausted_emp = bool(exhausted_ids) and (exhausted_new or since_report >= STALE_REPORT)
        enough_new = (len(np_snapshot) >= MIN_FOR_CHECK or raw_confirmed_new or raw_refuted_new
                      or exhausted_emp)
        if writeup_backlog and since_report >= REPORT_COOLDOWN:
            agents_status.log_event(
                cfg, "планировщик-отчёта",
                "raw confirmed typed EXP_SPEC будет учтён в отчёте; writeup продолжает gate: "
                + ", ".join(writeup_backlog[:4])
                + ("…" if len(writeup_backlog) > 4 else ""),
            )
        # Не строим отчёт без новых прошедших результатов: это только перерендер старого материала
        # и выглядит как прогресс без экспериментов/теории. Typed EXP_SPEC result is different:
        # if a real run just confirmed/refuted a claim, the old report is stale and must pivot
        # immediately instead of showing "no eligible EXP_SPEC" for the whole cooldown window.
        # raw_confirmed/refuted_new = СВЕЖИЙ результат → отчёт сразу. exhausted_emp ПОСТОЯНЕН (achiev
        # навсегда writeup_exhausted) → триггерим не чаще COOLDOWN, иначе отчёт каждый тик (жжёт критик).
        # ФИКС ВОЛНЫ 210, вторая половина: СВЕЖИЙ вердикт прогона НЕ ЖДЁТ НИКОГО. Комментарий к
        # REPORT_COOLDOWN прямо обещает «свежий typed-эксп вердикт триггерит отчёт НЕМЕДЛЕННО в обход
        # кулдауна», а код конъюнктил его с `quiescent` — то есть вердикт прогона A не мог собрать
        # отчёт, пока идёт прогон B (при 10-12-часовых ранах это почти всегда). Оговорка «не судим
        # статью, пока раны в полёте» на этом пути бессмысленна по построению: новые числа УЖЕ на руках.
        typed_result_ready = (raw_confirmed_new or raw_refuted_new) or (
            exhausted_emp and quiescent and since_report >= REPORT_COOLDOWN)
        if (typed_result_ready
                or (since_report >= REPORT_COOLDOWN
                    and enough_new
                    and quiescent)):
            try:
                if raw_confirmed_new:
                    do_rep, astar_ready, reason = True, "no", (
                        "confirmed typed EXP_SPEC is fresh report material; "
                        "post-exp writeup continues separately"
                    )
                elif raw_refuted_new:
                    do_rep, astar_ready, reason = True, "no", (
                        "negative/no_signal typed EXP_SPEC is fresh report material; "
                        "A*-critic must pivot or scope-reduce instead of calling the audit missing"
                    )
                elif exhausted_emp:
                    # confirmed-эмпирика (writeup_exhausted: эксп подтвердил, но формальный writeup не
                    # прошёл контракт-гейт) — ВАЛИДНЫЙ материал отчёта. should_report её НЕ видит (смотрит
                    # только свежие gate-PASS в np_snapshot, пустые после рестарта) → вето «перерендер» →
                    # confirmed achievability/gn_gap НИКОГДА не попадали в отчёт, скор застревал. Строим
                    # отчёт напрямую: критик должен зачесть эти реальные числа как E=pass-свидетельство.
                    do_rep, astar_ready, reason = True, "no", (
                        "confirmed typed EXP_SPEC empirics (writeup-exhausted) are report material — "
                        "incorporate the real numbers as E-axis evidence, do not call the audit missing"
                    )
                else:
                    with glock:
                        dr = gio.load_graph(cfg)
                    do_rep, astar_ready, reason = report_trigger.should_report(cfg, dr, np_snapshot, last_score)
                agents_status.log_event(cfg, "планировщик-отчёта",
                                        f"{'ОТЧЁТ' if do_rep else 'ждём'} · {reason[:80]}")
            except Exception as e:
                logger.warning("планировщик упал: %s", e); do_rep = False
        elif (since_report >= REPORT_COOLDOWN
              and stale
              and not np_snapshot
              and it % 15 == 0):
            agents_status.log_event(
                cfg, "планировщик-отчёта",
                "ждём · нет новых прошедших gate/typed-writeup результатов; отчёт без нового материала запрещён",
            )
        if True:
            if do_rep:
                try:
                    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                    with glock:
                        dgen = gio.load_graph(cfg)
                    # ФИКС ВОЛНЫ 177 (восстановлен волной 184): отчёт считается в ФОНОВОМ потоке, а
                    # главный поток, пока ждёт, прокачивает слив экспериментов (_drain_exp) раз в
                    # минуту. Семантика ниже не меняется — rep получаем ровно там же и так же, просто
                    # за 30-60 мин ожидания завершённые прогоны финализируются, waiting-записи
                    # переразмещаются, а освободившиеся слоты сразу заполняются.
                    _rep_box: Dict[str, Any] = {}

                    def _gen_report():
                        try:
                            _rep_box["rep"] = paper.generate_paper(
                                dgen, cfg, ts, min_score=cfg.report_min_score, max_rounds=2)
                        except BaseException as ge:            # noqa: BLE001 — пробрасываем наружу
                            _rep_box["err"] = ge

                    _rth = threading.Thread(target=_gen_report, daemon=True)
                    _rth.start()
                    while _rth.is_alive():
                        _rth.join(timeout=60)
                        if _rth.is_alive():
                            _drain_exp(it)
                    if "err" in _rep_box:
                        raise _rep_box["err"]
                    rep = _rep_box.get("rep") or {}
                    last_score = rep.get("score")
                    agents_status.log_event(cfg, "A*-критик-отчёта",
                                            (f"отчёт A*={last_score}/10 → правки агентам" if last_score is not None
                                             else "отчёт не собран → повтор позже"))
                    # AIDE² FORK-ON-STALL: балл на плато K циклов → форсируем эволюцию ВНЕ расписания
                    # (сброс кулдауна) → воркеры плодят свежие кросс-веточные гибриды = НОВЫЙ угол
                    # штурма потолка. Как в AIDE²: застрявшая линия → форк в новую под другой стратегией.
                    if rep.get("plateau"):
                        with slock:
                            S["last_evolve"] = 0.0
                        logger.info("[fork-on-stall] балл на плато → форсирую evolve (новый угол) на след. idle-воркере")
                        agents_status.log_event(cfg, "fork-on-stall",
                                                "балл застрял → форк фронтира: эволюция новых гибридов (смена угла)")
                    # критик потребовал КРАЕУГОЛЬНЫЙ длинный эксперимент → ставим один на лучшего
                    # эмпирического кандидата; команда скоординируется вокруг него (мыслители отдыхают)
                    spec = rep.get("cornerstone")
                    with slock:
                        busy = S["cornerstone"] is not None
                    if spec and not busy:
                        # dgen устарел на минуты (загружен ДО долгого generate_paper). Работать и
                        # СОХРАНЯТЬ его — значит затереть всё, что воркеры записали в граф за это время
                        # (lost-update). Перечитываем свежий граф под glock и сидируем/сохраняем под ним.
                        with glock:
                            dseed = gio.load_graph(cfg); gio.ensure_fields(dseed)
                            cand = _pick_confirm_candidate(dseed, cfg)
                            if cand is None:
                                cand = _seed_cornerstone_candidate(dseed, cfg, spec)
                                if cand is not None:
                                    gio.save_graph(dseed, cfg); gio.regen_canvas(cfg)
                        if cand and cand["id"] not in S["active"]:
                            rec = empirical.launch_cornerstone(cand, spec, cfg)
                            if rec.get("status") in ("running", "waiting"):
                                with glock:
                                    dch = gio.load_graph(cfg); gio.ensure_fields(dch)
                                    nch = gio.index(dch).get(cand["id"])
                                    if nch:
                                        nch["status"] = "experiment_running"
                                        if rec.get("exp_spec"):
                                            nch["exp_spec"] = rec["exp_spec"]
                                        gio.save_graph(dch, cfg)
                                with slock:
                                    S["cornerstone"] = cand["id"]
                                logger.info("[краеугольный] критик потребовал → EXP_SPEC[%s] на %s: %s",
                                            rec.get("kind"), cand["id"], spec[:80])
                                agents_status.log_event(cfg, "A*-критик-отчёта",
                                                        f"требует КРАЕУГОЛЬНЫЙ EXP_SPEC[{rec.get('kind')}] → "
                                                        f"запущен на {cand['id']}: {spec[:80]}")
                    # DIRECTIVES → рабочие узлы: WEAK_NODES рождают pressure-узлы, а нумерованные
                    # research-директивы критика (докажи bridge-теорему, построй theorem-comparison
                    # таблицу, инстанцируй bounds) доходили ТОЛЬКО до писателя — идейные воркеры их
                    # не брали, требования висели без исполнителя и балл стоял. Сеем до 2 узлов/цикл.
                    if (rep.get("score") or 0) < cfg.report_min_score:
                        try:
                            with glock:
                                seeded = _seed_directive_nodes(cfg)
                            if seeded:
                                agents_status.log_event(cfg, "директива→узел",
                                                        "созданы рабочие узлы по DIRECTIVES критика: "
                                                        + ", ".join(seeded))
                        except Exception as e:
                            logger.warning("directive-seeding упал: %s", e)
                    with slock:
                        S["new_passed"] = []
                        S["last_report"] = now_r   # старт cooldown — следующий отчёт не раньше +30 мин
                        S["exhausted_reported"] = exhausted_ids  # этот набор отчитан → не пере-судим без изменений
                except Exception as e:
                    logger.warning("report-cycle упал: %s", e)
                    # BACKOFF: без сдвига last_report ворота do_rep остаются открытыми и персистентная
                    # ошибка молотит критика каждый 20с-тик (retry-шторм, жжёт токены). Один cooldown паузы.
                    with slock:
                        S["last_report"] = now_r
        # дашборд: показать активных идейных воркеров
        try:
            with slock:
                act = list(S["active"])
            gio.save_active(act, cfg)          # selector тоже видит занятые узлы
            agents_status.set_round(cfg, it + 1, act)
            agents_status.write_snapshot(cfg)
        except Exception:
            pass
        time.sleep(20)
    S["stop"] = True
    return out
