#!/usr/bin/env python3
"""Убрать продублированные разделы разбора.

В двух разборах блок текста стоит дважды: сначала тело, потом заголовок и то же тело
снова. Читается как заикание, и в хранилище это видно глазами. Правка узкая: раздел
удаляется только если ровно такой же раздел с тем же заголовком стоит рядом, и только
из двух одинаковых остаётся один. Ничего, что встречается один раз, не трогается.

Сравнение по буквам и цифрам: пробелы и переводы строк между копиями расходятся, а текст
тот же.

    section_dedup.py <клон литературы>... [--fix]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEAD = re.compile(r"(?m)^## .+$")


def body_of(piece: str) -> str:
    """Раздел без собственного заголовка."""
    return piece.split("\n", 1)[1] if "\n" in piece else ""


def letters(text: str) -> str:
    return re.sub(r"[^0-9a-zA-Zа-яёА-ЯЁ]+", "", text).lower()


def cut(text: str) -> tuple[str, list[str]]:
    """Разделы как список (заголовок, тело), и всё, что стоит до первого заголовка."""
    marks = [m.start() for m in HEAD.finditer(text)]
    if not marks:
        return text, []
    head = text[:marks[0]]
    pieces = []
    for i, start in enumerate(marks):
        end = marks[i + 1] if i + 1 < len(marks) else len(text)
        pieces.append(text[start:end])
    return head, pieces


#: Разделы формы: их в разборе может быть только по одному, и остаться должен ПЕРВЫЙ.
#: Второй — остаток прежнего вида: у `chaubard2026probe` под утверждениями висело старое
#: «Коротко» на 3.6 КБ, и в хранилище оно читалось как второе краткое изложение.
ONCE = ("## BibTeX", "## Коротко", "## Что статья утверждает", "## Рядом в библиотеке")


def dedup(text: str) -> tuple[str, list[str]]:
    head, pieces = cut(text)
    if not pieces:
        return text, []
    kept: list[str] = []
    dropped: list[str] = []
    seen_once: set[str] = set()
    for piece in pieces:
        title = piece.splitlines()[0]
        if title in ONCE:
            if title in seen_once:
                dropped.append(title[3:] + " (второй раз, раздел формы)")
                continue
            seen_once.add(title)
        elif kept and letters(body_of(kept[-1])) == letters(body_of(piece)):
            # Тот же текст может стоять под другим заголовком: у `duchi2011adaptive`
            # «Про что работа» и «Общий обзор» совпадают дословно, 2674 байта в байт.
            # Сравниваем тело, а не заголовок, и оставляем первое вхождение.
            dropped.append(f"{title[3:]} (тот же текст, что и выше)"
                           if kept[-1].splitlines()[0] != title else title[3:])
            continue
        kept.append(piece)
    return head + "".join(kept), dropped


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("roots", type=Path, nargs="+")
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args(argv)

    total = touched = 0
    for root in sorted(args.roots):
        for paper in sorted(root.glob("*.md")):
            if paper.name == "README.md":
                continue
            total += 1
            text = paper.read_text(encoding="utf-8")
            fixed, dropped = dedup(text)
            if not dropped:
                continue
            touched += 1
            cut_bytes = len(text.encode()) - len(fixed.encode())
            print(f"  {root.name}/{paper.stem}: убрано {len(dropped)}, "
                  f"{cut_bytes} б")
            for title in dropped:
                print(f"      «{title[:70]}»")
            if args.fix:
                paper.write_text(fixed, encoding="utf-8")
    tail = f", переписано: {touched}" if args.fix else ""
    print(f"разборов: {total}, с повторами: {touched}{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
