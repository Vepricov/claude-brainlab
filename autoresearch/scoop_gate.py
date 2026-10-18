"""#7 Prior-art / scoop-гейт перед derive (идея из claude-autoresearch DEEPRESEARCH.md).

До дорогого derive дешёвый агент проверяет, не переоткрываем ли известное: ему
вшивается claim узла + grep по локальным заметкам проекта (офлайн, без веба). Веб-скан
(если нужен) делает оркестратор-человек своими тулзами. Результат -> node['scoop'].
"""
from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .config import ARConfig
from .engines import engine_call, grep_tail

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScoopReport:
    verdict: str          # novel | partial | scooped | ?
    refs: str
    raw: str

    def as_node_field(self, ts: str) -> Dict[str, str]:
        return {"verdict": self.verdict, "refs": self.refs, "ts": ts}


def _grep_library(claim: str, cfg: ARConfig, max_hits: int = 12) -> str:
    """Локальный поиск по заметкам проекта (Knowledge, разборы темы ../literature + корень)."""
    roots = [os.path.join(cfg.project_root, d) for d in ("Knowledge", os.path.join("..", "literature"), "Reports")]
    roots.append(cfg.project_root)
    terms = [w for w in claim.replace(",", " ").split() if len(w) > 5][:6]
    hits: List[str] = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        for term in terms:
            try:
                r = subprocess.run(["grep", "-ril", "--include=*.md", term, root],
                                   capture_output=True, text=True, timeout=20)
            except (OSError, subprocess.SubprocessError):
                continue
            for line in r.stdout.splitlines():
                base = os.path.basename(line)
                if base not in hits:
                    hits.append(base)
                if len(hits) >= max_hits:
                    break
        if len(hits) >= max_hits:
            break
    return "\n".join(f"- {h}" for h in hits) or "(локальная библиотека: совпадений нет)"


_SCOOP_PROMPT = """\
Ты PRIOR-ART РЕЦЕНЗЕНТ проекта: {domain}
Проверь, не переоткрывает ли узел известное.
CLAIM узла [{nid}]: {idea}
ОТКРЫТЫЕ ВОПРОСЫ: {open}

Релевантные локальные заметки (имена файлов, можешь сослаться):
{lib}

Оцени новизну СТРОГО и честно. Если это прямое следствие известного или уже сделано
в проекте — это scooped/partial, не делай вид что ново.
В КОНЦЕ выведи РОВНО две строки:
REFS: <через ; источники/заметки или 'нет'>
SCOOP_VERDICT: novel|partial|scooped"""


def check_node(node: Dict[str, Any], cfg: ARConfig,
               call: Optional[Callable[[str], str]] = None) -> ScoopReport:
    call = call or engine_call(cfg.engines.scoop, cfg)
    lib = _grep_library(node.get("idea", "") + " " + node.get("short", ""), cfg)
    prompt = _SCOOP_PROMPT.format(domain=cfg.domain, nid=node["id"], idea=node.get("idea", ""),
                                  open=node.get("open", ""), lib=lib)
    out = call(prompt)
    return ScoopReport(verdict=grep_tail(out, "SCOOP_VERDICT:"),
                       refs=grep_tail(out, "REFS:"), raw=out)
