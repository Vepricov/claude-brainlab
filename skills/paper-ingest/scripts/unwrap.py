#!/usr/bin/env python3
"""Абзац разбора — одна строка, без ручных переносов.

Obsidian показывает одиночный перевод строки как разрыв, поэтому проза, свёрнутая на 80–100
знаках, рисуется рваными строками с висящими словами. Агент разбора сворачивал так текст,
потому что шаблон в промпте свёрнут сам. Владелец 25-10-2026 попросил убрать это везде.

Склеивается строка с предыдущей, если обе — проза одного абзаца (или одной цитаты `>`),
предыдущая шириной как свёрнутая (`MIN_WRAPPED`…`MAX_WRAPPED`) и либо обрывается не на конце
предложения, либо следующая начинается со строчной. Не трогаются шапка, код, `$$…$$`, таблицы, заголовки,
пункты списков как начало строки, заголовки выносок и строки с HTML-тегом.

    unwrap.py FILE...           поправить на месте, напечатать что поменялось
    unwrap.py --check FILE...   только сказать; код 1, если есть что править
"""
from __future__ import annotations

import pathlib
import re
import sys

#: Ширина свёрнутой строки: короче — нарочно короткая («**Год:** 2026»), длиннее — абзац,
#: уже записанный одной строкой, и следующая за ним строка начата нарочно.
MIN_WRAPPED, MAX_WRAPPED = 50, 110
#: Строка, которая сама начинает блок и к предыдущей не приклеивается.
НАЧАЛО = re.compile(r"(#{1,6}\s|[-*+]\s|\d+[.)]\s|\||\$\$|```|~~~|<(?!!--)|!\[|\[\^|---|\*\*\*|>|\[!)")
ЦИТАТА = re.compile(r"^((?:>\s?)+)(.*)$")


def _проза(строка: str) -> str | None:
    """Текст строки, если её можно склеивать, иначе None."""
    s = строка.strip()
    if not s or s.endswith(("  ", "\\")) or строка.endswith("  "):
        return None
    return s


def править(текст: str) -> tuple[str, int]:
    """Склеивать до неподвижной точки: склеенная строка может сама стать шириной как свёрнутая."""
    всего = 0
    while True:
        текст, склеек = _проход(текст)
        if not склеек:
            return текст, всего
        всего += склеек


def _проход(текст: str) -> tuple[str, int]:
    строки = текст.split("\n")
    out: list[str] = []
    склеек = 0
    в_коде = в_формуле = False
    начало = 0
    if строки and строки[0] == "---":                 # шапка YAML
        конец = next((i for i in range(1, len(строки)) if строки[i] == "---"), None)
        if конец is not None:
            out.extend(строки[: конец + 1])
            начало = конец + 1
    прежняя = ""
    for строка in строки[начало:]:
        s = строка.strip()
        if s.startswith(("```", "~~~")):
            в_коде = not в_коде
        elif not в_коде and s == "$$" or (not в_коде and s.startswith("$$") and s.count("$$") == 1):
            в_формуле = not в_формуле
        elif not (в_коде or в_формуле) and out and (хвост := склеить(прежняя, строка)):
            out[-1] = out[-1].rstrip() + " " + хвост
            склеек += 1
            прежняя = строка
            continue
        out.append(строка)
        прежняя = строка
    return "\n".join(out), склеек


def склеить(a: str, b: str) -> str | None:
    """Что приклеить от `b` к строке, начатой `a`, или None, если это разные строки."""
    qa, qb = ЦИТАТА.match(a), ЦИТАТА.match(b)
    if bool(qa) != bool(qb):
        return None
    if qa:
        if qa[1].replace(" ", "") != qb[1].replace(" ", ""):
            return None
        ta, tb = qa[2], qb[2]
    else:
        ta, tb = a, b
    pa, pb = _проза(ta), _проза(tb)
    if pa is None or pb is None or НАЧАЛО.match(pb) or pa.startswith(("|", "#", "[!", "$$", "![")) or re.match(r"<(?!!--)", pa):
        return None
    if re.match(r"\s{4,}|\t", tb) and not re.match(r"\s{2,}", ta):
        return None                                   # отступ кода под абзацем
    if not MIN_WRAPPED <= len(a.rstrip()) <= MAX_WRAPPED:
        return None
    if pa.endswith((".", "!", "?", ".*", ".)")) and not pb[0].islower():
        return None
    return pb


def main(argv: list[str]) -> int:
    check = "--check" in argv
    грязных = 0
    for p in (pathlib.Path(a) for a in argv if a != "--check"):
        t = p.read_text(encoding="utf-8")
        new, склеек = править(t)
        if склеек:
            грязных += 1
            print(f"{p}: склеено строк {склеек}")
            if not check:
                p.write_text(new, encoding="utf-8")
    return 1 if check and грязных else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
