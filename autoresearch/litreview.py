"""Обзор литературы внутри лупа (agent-driven Related Work).

Идея (директива юзера): у КАЖДОГО узла графа есть related_work — связанные работы,
которые агенты видят ДО того, как думают над узлом. Библиотекарь-воркёр фоном обогащает
узлы фронтира RW; идейный агент может дополнить RW своего узла, если чувствует нехватку.
Источники: (1) локальная Obsidian-библиотека (сжатый индекс `_index.jsonl`), (2) интернет
(через web-движок claude -p --allowedTools WebSearch на сервере).

Модуль stdlib-only. LLM-вызовы идут через engines.engine_call (движок cfg.engines.librarian).
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------- расположение библиотеки и индекса ----------------

def lit_dir(cfg: Any) -> str:
    """Каталог разборов темы на машине лупа. Порядок: cfg.lit_dir → <root>/../literature."""
    d = str(getattr(cfg, "lit_dir", "") or "").strip()
    if d:
        return os.path.abspath(os.path.expanduser(d))
    # project_root = ~/brainlab/<направление>/<тема>/<работа>; разборы темы = <тема>/literature
    root = os.path.abspath(getattr(cfg, "project_root", "."))
    guess = os.path.abspath(os.path.join(root, "..", "literature"))
    return guess


def index_path(cfg: Any) -> str:
    return os.path.join(lit_dir(cfg), "_index.jsonl")


# ---------------- построение сжатого индекса ----------------

def _bibkey(text: str) -> str:
    m = re.search(r"@\w+\s*\{\s*([^,\s]+)\s*,", text)
    return m.group(1).strip() if m else ""


def _frontmatter_title(text: str) -> str:
    m = re.search(r'(?ms)\Atitle:\s*"?(.+?)"?\s*$', text)
    if m:
        return m.group(1).strip()
    m = re.search(r"(?m)^title:\s*\"?(.+?)\"?\s*$", text[:600])
    if m:
        return m.group(1).strip()
    m = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return m.group(1).strip() if m else ""


def _tags(text: str) -> List[str]:
    m = re.search(r"(?ms)^tags:\s*\n((?:\s*-\s*.+\n)+)", text[:800])
    if not m:
        return []
    return [x.strip("- ").strip() for x in m.group(1).splitlines() if x.strip().lstrip("- ").strip()]


def _tldr(text: str, limit: int = 420) -> str:
    """Короткое изложение идеи/результата из готового блока обзора (без LLM)."""
    # предпочитаем "### 1. Общий обзор" / "## AI Explanation" / "## Summary"
    for pat in (r"###\s*1\.\s*Общий обзор", r"##\s*AI Explanation", r"##\s*Summary", r"##\s*TL;DR"):
        m = re.search(pat, text)
        if not m:
            continue
        rest = text[m.end():]
        # первый непустой абзац после заголовка (пропускаем под-заголовки)
        for para in re.split(r"\n\s*\n", rest):
            p = para.strip()
            if not p or p.startswith("#"):
                continue
            p = re.sub(r"\s+", " ", p)
            return p[:limit]
    # фолбэк: первый содержательный абзац после фронтматтера/заголовка
    body = re.sub(r"(?s)\A---.*?---\s*", "", text)
    body = re.sub(r"(?m)^#.*$", "", body)
    body = re.sub(r"(?s)```.*?```", "", body)
    for para in re.split(r"\n\s*\n", body):
        p = re.sub(r"\s+", " ", para.strip())
        if len(p) > 60:
            return p[:limit]
    return ""


def build_index(cfg: Any) -> Dict[str, int]:
    """Сканирует <тема>/literature/*.md → пишет _index.jsonl (по строке на статью). Возвращает статистику."""
    root = lit_dir(cfg)
    if not os.path.isdir(root):
        logger.warning("[lit] нет каталога библиотеки: %s", root)
        return {"notes": 0, "indexed": 0}
    rows: List[Dict[str, Any]] = []
    skip_dirs = ("_attachments", "_trash", "_inbox")
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in skip_dirs]
        for f in fn:
            if not f.endswith(".md") or f.startswith("_"):
                continue
            path = os.path.join(dp, f)
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            tldr = _tldr(text)
            if not tldr:
                continue
            rows.append({
                "key": _bibkey(text),
                "title": _frontmatter_title(text) or os.path.splitext(f)[0],
                "path": os.path.relpath(path, root),
                "tags": _tags(text),
                "tldr": tldr,
            })
    tmp = index_path(cfg) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, index_path(cfg))
    logger.info("[lit] индекс построен: %d статей → %s", len(rows), index_path(cfg))
    return {"notes": len(rows), "indexed": len(rows)}


def load_index(cfg: Any) -> List[Dict[str, Any]]:
    p = index_path(cfg)
    out: List[Dict[str, Any]] = []
    try:
        for line in open(p, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return out


# ---------------- дешёвый поиск по индексу (без LLM) ----------------

_WORD_RE = re.compile(r"[a-zа-я0-9µ]+", re.IGNORECASE)


def _tokens(s: str) -> List[str]:
    return [w.lower() for w in _WORD_RE.findall(s or "") if len(w) > 2]


def search_index(index: List[Dict[str, Any]], query: str, k: int = 8) -> List[Dict[str, Any]]:
    """Keyword-overlap ранжирование по title+tldr+tags. Возвращает top-k статей."""
    q = set(_tokens(query))
    if not q:
        return []
    scored = []
    for r in index:
        hay = _tokens(r.get("title", "")) + _tokens(r.get("tldr", "")) + _tokens(" ".join(r.get("tags", [])))
        if not hay:
            continue
        hayset = set(hay)
        overlap = len(q & hayset)
        if overlap == 0:
            continue
        # лёгкий буст за совпадение в title
        title_hit = len(q & set(_tokens(r.get("title", ""))))
        scored.append((overlap + 0.5 * title_hit, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:k]]


# ---------------- генерация Related Work (библиотека + интернет) ----------------

_RW_PROMPT = """\
Ты БИБЛИОТЕКАРЬ-ресёрчер. Собери СЖАТЫЙ Related Work для узла исследования, чтобы другие агенты
видели связанные работы ДО того, как думают над узлом.
Домен: {domain}
Узел [{nid}]: {short}
Идея узла: {idea}
Открытые вопросы: {open}
УЖЕ НАЙДЕННОЕ В ЛОКАЛЬНОЙ БИБЛИОТЕКЕ (используй эти citation_key дословно, если релевантно):
{library}
ЗАДАЧА:
1) Через WebSearch найди 2-4 ключевые/свежие ВНЕШНИЕ работы по теме узла (не только из библиотеки).
2) Оцени НОВИЗНУ: не была ли идея узла уже исследована? Если да — прямо назови где (критично, чтобы не тратить усилия на дубль).
3) Выдай РОВНО такой компактный блок (без воды, каждый пункт 1 строка):
RELATED_WORK:
- <citation_key ИЛИ короткая ссылка/название> — что сделано и чем релевантно узлу
(5-8 пунктов, самые релевантные первыми; локальные по citation_key, внешние по ссылке/названию)
NOVELTY: <1-2 строки: идея нова / частично сделана в [ref] / уже сделана в [ref]>
GAPS: <1 строка: чего в литературе нет и что этот узел может дать нового>
Только этот формат."""


def _extract_rw_block(text: str) -> str:
    """Берём от RELATED_WORK: до конца (RELATED_WORK/NOVELTY/GAPS) — компактно для узла."""
    m = re.search(r"(?s)RELATED_WORK:.*", text or "")
    block = m.group(0).strip() if m else (text or "").strip()
    return block[:2000]


def extract_rw_search(text: str) -> str:
    """Маркер агента `RW_SEARCH: <запрос>` в derive → идейный агент сам просит доп-поиск литературы."""
    m = re.search(r"(?im)^\s*RW_SEARCH\s*:\s*(.+?)\s*$", text or "")
    return m.group(1).strip()[:300] if m else ""


def make_related_work(cfg: Any, node: Dict[str, Any], index: Optional[List[Dict[str, Any]]] = None,
                      engine: str = "", query: str = "") -> str:
    """Генерирует RW-отчёт для узла: локальные хиты индекса + веб-поиск через web-движок.
    query!="" → точечный доп-поиск по запросу агента (RW_SEARCH), а не общий по полям узла."""
    if index is None:
        index = load_index(cfg)
    search_q = query or " ".join(str(node.get(k, "")) for k in ("short", "idea", "open"))
    hits = search_index(index, search_q, k=8)
    library = "\n".join(
        f"- {(h.get('key') or h.get('title',''))}: {h.get('tldr','')[:200]}" for h in hits
    ) or "(в локальной библиотеке релевантного не найдено — опирайся на веб-поиск)"
    from .engines import engine_call  # lazy: избегаем циклического импорта
    eng = engine or getattr(cfg.engines, "librarian", "codex_web")
    idea = str(node.get("idea", ""))[:900]
    if query:
        idea = (idea + " | КОНКРЕТНЫЙ ДОП-ЗАПРОС АГЕНТА (ищи прежде всего это): " + query)[:1100]
    out = engine_call(eng, cfg)(_RW_PROMPT.format(
        domain=str(cfg.domain)[:500],
        nid=node.get("id", "?"), short=str(node.get("short", ""))[:200],
        idea=idea, open=str(node.get("open", ""))[:300],
        library=library))
    return _extract_rw_block(out)


def append_rw(cfg: Any, node: Dict[str, Any], text: str) -> None:
    """Дописывает результат агент-инициированного доп-поиска в related_work узла (компактно) + в файл."""
    add = (text or "").strip()
    if not add:
        return
    cur = str(node.get("related_work") or "").strip()
    merged = (cur + "\n\n[доп-поиск агента]\n" + add) if cur else add
    node["related_work"] = merged[-2600:]
    try:
        p = rw_report_path(cfg, node.get("id", "x"))
        with open(p, "a", encoding="utf-8") as fh:
            fh.write("\n\n## Доп-поиск (агент RW_SEARCH)\n" + add + "\n")
    except OSError:
        pass


# ---------------- интеграция с узлом графа ----------------

def has_rw(node: Dict[str, Any]) -> bool:
    return bool(str(node.get("related_work") or "").strip())


def rw_report_path(cfg: Any, nid: str) -> str:
    d = os.path.join(cfg.workdir, "memory", "nodes", str(nid))
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "related_work.md")


def set_rw(cfg: Any, node: Dict[str, Any], text: str) -> None:
    """Пишет related_work в узел (компактно, видно агентам) + полный файл-отчёт (виден другим)."""
    node["related_work"] = (text or "").strip()[:2000]
    try:
        p = rw_report_path(cfg, node.get("id", "x"))
        open(p, "w", encoding="utf-8").write(
            f"# Related Work: {node.get('id')} — {node.get('short','')}\n\n{text}\n")
    except OSError:
        pass


def rw_for_prompt(node: Dict[str, Any], limit: int = 1500) -> str:
    rw = str(node.get("related_work") or "").strip()
    if not rw:
        return ""
    return "СВЯЗАННЫЕ РАБОТЫ (собраны библиотекарем; учитывай при идее/доказательстве, не дублируй известное):\n" + rw[:limit]

