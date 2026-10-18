"""Интеграция нашего пайплайна с кнопками UI ResearchOS.

#1 split_into_projects — большой граф → маленькие деревья (проекты-соседи на тему).
#2 build_knowledge_docs — кнопка Knowledge: курируемые документы (не свалка инсайтов).
#3 library_from_obsidian — Related Work: library.csv из разборов тем ~/brainlab/*/*/literature.
#4 paper_to_koi — кнопка Статья: финальная статья в koi-structure/paper/.

Всё детерминированно (без LLM). Пишет ровно в контракты, которые читает koi-движок.
"""
from __future__ import annotations

import csv
import glob
import json
import logging
import os
import re
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .config import ARConfig
from . import graph_io as gio, failure_taxonomy as ftax

logger = logging.getLogger(__name__)

_WINS = ("proven", "confirmed_emp")
_SURV = ("proven", "confirmed_emp", "conditional")
# Корень хранилища: разборы лежат по темам в <направление>/<тема>/literature.
DEFAULT_LIT = os.path.expanduser("~/brainlab")


# ---------------- #4 Paper → koi (кнопка «Статья») ----------------

def paper_to_koi(tex_path: str, pdf_path: Optional[str], cfg: ARConfig,
                 engine: str = "opus", score: Optional[int] = None) -> str:
    d = os.path.join(cfg.koi_dir, "paper")
    os.makedirs(d, exist_ok=True)
    if tex_path and os.path.exists(tex_path):
        shutil.copy2(tex_path, os.path.join(d, "main.tex"))
    if pdf_path and os.path.exists(pdf_path):
        shutil.copy2(pdf_path, os.path.join(d, "paper.pdf"))
    status = {"state": "done", "engine": engine, "backend": "autoresearch", "mode": "agent",
              "started_at": None, "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "error": None, "score": score}
    json.dump(status, open(os.path.join(d, "status.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    logger.info("paper → koi UI: %s", d)
    return d


# ---------------- #2 Knowledge: курируемые документы ----------------

def _branch_of(nid: str, by: Dict[str, Dict[str, Any]]) -> Optional[str]:
    for a in gio.ancestors(nid, by):
        if a.get("col") == 1:
            return a["id"]
    return nid if by.get(nid, {}).get("col") == 1 else None


def build_knowledge_docs(data: Dict[str, Any], cfg: ARConfig) -> List[str]:
    """Курируемые knowledge/<NN>.md (H1 + сводка-абзац + содержимое) — чисто, не инсайты."""
    kdir = os.path.join(cfg.koi_dir, "knowledge")
    os.makedirs(kdir, exist_ok=True)
    by = gio.index(data)
    written: List[str] = []
    surv = [n for n in data["nodes"] if n.get("status") in _SURV and n.get("col") not in (0, None)]
    wins = [n for n in surv if n.get("status") in _WINS]

    # 00 — обзор проекта
    ov = [f"# Обзор проекта {cfg.project_name}", "",
          (data.get("overall_verdict") or data.get("root_idea") or "").strip(), "",
          f"Доказано/подтверждено: {len(wins)}; выжило всего: {len(surv)}; "
          f"узлов-результатов: {len([n for n in data['nodes'] if n.get('col') not in (0,None)])}.", "",
          "## Центральный вопрос", (data.get("root_idea") or "").strip()]
    _w(os.path.join(kdir, "00-overview.md"), "\n".join(ov)); written.append("00-overview.md")

    # по ветке-сюжету: результаты с честными вердиктами
    branches: Dict[str, List[Dict[str, Any]]] = {}
    for n in surv:
        branches.setdefault(_branch_of(n["id"], by) or "misc", []).append(n)
    for i, (b, nodes) in enumerate(branches.items(), 1):
        title = by.get(b, {}).get("short", b)
        L = [f"# Результаты: {title}", "",
             f"Сводка по сюжету «{title}»: {len(nodes)} выживших результатов "
             f"({sum(1 for n in nodes if n.get('status') in _WINS)} доказано/подтверждено).", ""]
        for n in nodes:
            L += [f"## {n.get('short', n['id'])} ({n.get('status')})",
                  (n.get("idea") or "").strip(),
                  ("Вердикт: " + n["verdict"].strip()) if n.get("verdict") else "",
                  ("Открыто: " + n["open"].strip()) if n.get("open") else "", ""]
        fn = f"{10*i:02d}-results-{re.sub(r'[^a-z0-9]+','-',b.lower())[:24]}.md"
        _w(os.path.join(kdir, fn), "\n".join(x for x in L if x is not None)); written.append(fn)

    # негативы — отдельный курируемый документ (а не инсайты)
    tax = ftax.taxonomy(data)
    if tax:
        L = ["# Негативные результаты и классы провалов", "",
             "Чему научились на тупиках: повторяющиеся классы ошибок, которые не воскрешаем.", ""]
        for cls, cnt, ids in tax:
            L.append(f"## {cls} ({cnt})")
            L.append("Узлы: " + ", ".join(ids[:10]))
            L.append("")
        _w(os.path.join(kdir, "90-negatives.md"), "\n".join(L)); written.append("90-negatives.md")
    logger.info("knowledge docs: %s", written)
    return written


def _w(path: str, text: str) -> None:
    open(path, "w", encoding="utf-8").write(text.rstrip() + "\n")


# ПРИМ.: проект ОДИН. Карту дробим ветками ВНУТРИ проекта (см. reorganize_branches),
# а не созданием проектов-соседей — иначе Knowledge/Related Work расходятся.


# ---------------- #3 Related Work: library.csv из Obsidian ----------------

_ARXIV = re.compile(r"arxiv\.org/abs/([0-9]{4}\.[0-9]{4,5})", re.I)
_SKIP_DIRS = {"_inbox", "_trash", "_templates"}


def _extract_paper(md: str, fname: str) -> Optional[Dict[str, str]]:
    if not md.strip():
        return None
    # title: первый H1 или имя файла
    m = re.search(r"^#\s+(.+)$", md, re.M)
    title = (m.group(1) if m else os.path.splitext(fname)[0]).strip()
    ax = _ARXIV.search(md)
    arxiv_url = f"https://arxiv.org/abs/{ax.group(1)}" if ax else ""
    # авторы: frontmatter authors: ... или строка **Авторы**
    au = re.search(r"^authors?:\s*(.+)$", md, re.M | re.I) or re.search(r"\*\*Авторы\*\*[:：]\s*(.+)", md)
    authors = (au.group(1).strip().strip("[]") if au else "")
    # abstract: блок «Краткая идея» / «Abstract» / первый содержательный абзац
    ab = re.search(r"(?:Кратк(?:ая|о)\s*идея|Abstract|Аннотация)\*?\*?[:：]?\s*(.+?)(?:\n#|\n\*\*|\Z)",
                   md, re.S | re.I)
    abstract = re.sub(r"\s+", " ", (ab.group(1) if ab else "")).strip()[:1200]
    if not abstract:
        for para in re.split(r"\n\s*\n", re.sub(r"^---.*?---", "", md, flags=re.S)):
            p = re.sub(r"\s+", " ", para).strip()
            if len(p) > 80 and not p.startswith(("#", "-", "|", "**Тема")):
                abstract = p[:1200]; break
    if not title or (not abstract and not arxiv_url):
        return None
    return {"title": title, "arxiv_url": arxiv_url, "authors": authors, "abstract": abstract}


def library_from_obsidian(cfg: ARConfig, lit_dir: str = DEFAULT_LIT, limit: int = 2000) -> str:
    rows: List[Dict[str, str]] = []
    seen = set()
    # Корень хранилища → все папки literature тем; конкретная папка → только она.
    tops = sorted(glob.glob(os.path.join(lit_dir, "*", "*", "literature"))) or [lit_dir]
    for root, dirs, files in (x for t in tops for x in os.walk(t)):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for fn in files:
            if not fn.endswith(".md") or fn.startswith(("want_2_read", "_")):
                continue
            try:
                md = open(os.path.join(root, fn), encoding="utf-8").read()
            except OSError:
                continue
            p = _extract_paper(md, fn)
            if not p:
                continue
            key = p["arxiv_url"] or p["title"].lower()
            if key in seen:
                continue
            seen.add(key)
            rows.append(p)
            if len(rows) >= limit:
                break
    outdir = os.path.join(cfg.koi_dir, "library")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "library.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=("no", "arxiv_url", "title", "authors", "abstract"))
        w.writeheader()
        for i, r in enumerate(rows, 1):
            w.writerow({"no": i, **r})
    logger.info("library.csv: %d статей из %s → %s", len(rows), lit_dir, out)
    return out
