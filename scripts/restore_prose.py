#!/usr/bin/env python3
"""Вернуть разборам прежний раздел «Про что работа» вместо переписанного «Коротко».

Владелец 07-10-2026: «теперь все разборы выглядят типа текст **жирное**, абзац, текст
**жирное**, абзац. А раньше мне больше нравилось, когда они выглядели вот так» — и привёл
сплошную прозу, которую пишет навык `paper-ingest`.

Замерено: в одиннадцати пройденных темах раздел «Про что работа» исчез у всех 267
разборов, а вместо него встал «Коротко», написанный агентами по шаблону (266 из 269
«Коротко» в базе начинают абзацы с жирного зачина). В тринадцати непройденных темах
«Про что работа» на месте у 399 разборов, и «Коротко» там нет. То есть это не стиль
`paper-ingest`, это подмена, сделанная проходом.

Прежний текст не потерян: он лежит в истории git, в коммите перед тем, который его убрал.
Проход достаёт его оттуда, ставит на место «Коротко» и «Коротко» убирает. Утверждения,
тело разбора и всё остальное не трогаются.

    restore_prose.py <клон литературы с полной историей>... [--fix]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SECTION = re.compile(r"(?ms)^## Про что работа\n(.*?)(?=^## |\Z)")
SHORT = re.compile(r"(?ms)^## Коротко\n.*?(?=^## |\Z)")
AFTER_BIB = re.compile(r"(## BibTeX.*?```\s*\n)", re.S)
#: Короче этого — огрызок, а не раздел: такой лучше не ставить, чем поставить пустым.
ENOUGH = 300


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True).stdout


def past_names(root: Path, name: str) -> list[str]:
    """Все имена, под которыми файл жил. Разборы переименовывались вместе с ключом
    цитирования, и `-S` по новому имени историю до переименования не видит."""
    seen = [name]
    for line in git(root, "log", "--follow", "--name-only", "--format=", "--", name).splitlines():
        line = line.strip()
        if line.endswith(".md") and line not in seen:
            seen.append(line)
    return seen


def old_prose(root: Path, name: str) -> str | None:
    """Текст «Про что работа» из коммита, предшествующего его удалению."""
    for past in past_names(root, name):
        for sha in git(root, "log", "--all", "--format=%H",
                       "-S", "## Про что работа", "--", past).split():
            for ref in (f"{sha}^:{past}", f"{sha}:{past}"):
                found = SECTION.search(git(root, "show", ref))
                if found and len(found.group(1).strip()) >= ENOUGH:
                    return found.group(1).strip()
    return None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("roots", type=Path, nargs="+")
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args(argv)

    total = back = kept = lost = 0
    for root in sorted(args.roots):
        for paper in sorted(root.glob("*.md")):
            if paper.name == "README.md":
                continue
            total += 1
            text = paper.read_text(encoding="utf-8")
            if SECTION.search(text):
                kept += 1
                continue
            if not SHORT.search(text):
                continue
            prose = old_prose(root, paper.name)
            if prose is None:
                lost += 1
                print(f"  {root.name}/{paper.stem}: прежнего текста в истории нет, "
                      f"«Коротко» оставлено")
                continue
            block = "## Про что работа\n\n" + prose + "\n"
            fresh = SHORT.sub("", text, count=1)
            bib = AFTER_BIB.search(fresh)
            if bib:
                fresh = (fresh[:bib.end()].rstrip() + "\n\n" + block + "\n"
                         + fresh[bib.end():].lstrip("\n"))
            else:
                fresh = block + "\n" + fresh
            fresh = re.sub(r"\n{4,}", "\n\n\n", fresh)
            back += 1
            if args.fix:
                paper.write_text(fresh, encoding="utf-8")
    tail = f", переписано: {back}" if args.fix else ""
    print(f"разборов: {total}; «Про что работа» уже на месте: {kept}; "
          f"возвращено: {back}; не нашлось в истории: {lost}{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
