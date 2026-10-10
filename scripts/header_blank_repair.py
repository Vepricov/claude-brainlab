#!/usr/bin/env python3
"""Вернуть пустые строки, съеденные прошлым проходом шапок.

`header_from_bib.py` заменял строку авторов и ссылку по регулярке с хвостом `\\s*$`. `\\s`
включает перевод строки, поэтому замена слизывала пустую строку после себя: «## BibTeX»
прилипал к абзацу, а ссылка на источник вставала вплотную к строке авторов. Смысл не
пострадал, но в сыром виде заметка читается хуже, а в хранилище владельца это видно глазами.

Правка узкая: только в первых десяти строках файла и только перед строкой авторов, ссылкой
на источник и первым «## ». Тело разбора не трогается.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

META = re.compile(r"^\*\*авторы\*\*")
LINK = re.compile(r"^\[Открыть источник\]\(")
HEAD = re.compile(r"^## ")
WINDOW = 10


def repair(text: str) -> str:
    # Делим по "\n", а не splitlines(): тот режет ещё и по \x0c, \x85, \u2028 и прочему,
    # что встречается в сырых выгрузках arXiv внутри разборов. Склейка через "\n" тогда
    # превращала такой символ в перевод строки и рвала формулу пополам.
    lines = text.split("\n")
    out: list[str] = []
    for i, line in enumerate(lines):
        if (i < WINDOW and i > 0 and out and out[-1].strip()
                and (META.match(line) or LINK.match(line) or HEAD.match(line))):
            out.append("")
        out.append(line)
    return "\n".join(out)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", type=Path, nargs="+")
    parser.add_argument("--fix", action="store_true", help="переписать файлы")
    args = parser.parse_args(argv)

    total = touched = 0
    for root in sorted(args.roots):
        for paper in sorted(root.glob("*.md")):
            if paper.name == "README.md":
                continue
            total += 1
            text = paper.read_text(encoding="utf-8")
            fixed = repair(text)
            if fixed == text:
                continue
            touched += 1
            print(f"  {root.name}/{paper.stem}")
            if args.fix:
                paper.write_text(fixed, encoding="utf-8")
    tail = f", переписано: {touched}" if args.fix else ""
    print(f"разборов: {total}, со съеденной пустой строкой: {touched}{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
