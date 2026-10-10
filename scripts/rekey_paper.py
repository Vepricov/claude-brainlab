#!/usr/bin/env python3
"""Переименовать ключ цитирования, когда он у двух разных статей один.

Ключ собирается как `{фамилия}{год}{первое слово}`, и у разных статей он совпадает:
«Parametric Retrieval Augmented Generation» Weihang Su и «Parametric Retrieval-Augmented
Generation using Latent Routing of LoRA Adapters» Zhan Su оба дают `su2025parametric`.
Генератор столкновения не замечает, и в `.bib` уезжает то, что попало.

Правка меняет ключ в трёх местах сразу, иначе база и хранилище разойдутся:
имя файла разбора, ключ внутри его блока BibTeX, и ключ в блоке BibTeX заметки хранилища.
Ссылки `\\cite{}` в рукописях НЕ трогаются: проверять, какая из двух статей там имелась в
виду, машине нельзя. Перед переименованием проход сам ищет ключ в `.tex` и `.bib` и
отказывается работать, если нашёл.

    rekey_paper.py <старый> <новый> --разбор <файл.md> [--заметка <файл.md>] [--fix]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

LOOK = (Path.home() / "Papers", Path.home() / "Projects")


EPRINT = re.compile(r"eprint\s*=\s*\{?([\d.]+)")


def eprint_of(text: str) -> str:
    found = EPRINT.search(text)
    return found.group(1) if found else ""


def cited(key: str, mine: str) -> list[str]:
    """Где ключ стоит в рукописях ПРО ЭТУ ЖЕ статью.

    Сверять один ключ недостаточно: `pethick2025training` стоит в 23 файлах рукописей, но
    все они про «Training Deep Learning Models with Norm-Constrained LMOs» (2502.07529), а
    переименовать нужно «Training Neural Networks at Any Scale» с тем же ключом. Поэтому у
    найденной записи `.bib` сверяется `eprint`: если статья другая, переименование этой
    копии рукописям не мешает. Файл `.tex` без своего `.bib` рядом считается совпадением:
    по одному `\cite{}` понять, какая из двух статей имелась в виду, нельзя.
    """
    found: list[str] = []
    for root in LOOK:
        if not root.is_dir():
            continue
        out = subprocess.run(
            ["grep", "-rlE", r"\{" + re.escape(key) + r"[},]", str(root),
             "--include=*.tex", "--include=*.bib"],
            capture_output=True, text=True).stdout
        for line in out.splitlines():
            if not line.strip():
                continue
            path = Path(line)
            if path.suffix == ".bib":
                entry = re.search(r"@\w+\{" + re.escape(key) + r"\s*,(.*?)\n\}",
                                  path.read_text(encoding="utf-8", errors="replace"), re.S)
                if entry and mine and eprint_of(entry.group(1)) not in ("", mine):
                    continue
            elif not list(path.parent.glob("*.bib")):
                found.append(line)
                continue
            else:
                continue
            found.append(line)
    return found


def swap(path: Path, old: str, new: str, fix: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    fresh = re.sub(r"(@\w+\{)" + re.escape(old) + r"(\s*,)", r"\1" + new + r"\2", text)
    if fresh == text:
        print(f"  {path.name}: ключа {old} в блоке BibTeX нет")
        return False
    if fix:
        path.write_text(fresh, encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("old")
    parser.add_argument("new")
    parser.add_argument("--разбор", type=Path, required=True, dest="paper")
    parser.add_argument("--заметка", type=Path, dest="note")
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args(argv)

    mine = eprint_of(args.paper.read_text(encoding="utf-8"))
    where = cited(args.old, mine)
    if where:
        print(f"ключ {args.old} уже стоит в рукописях ПРО ЭТУ ЖЕ статью "
              f"(eprint {mine or 'не указан'}), переименование отменено:")
        for line in where:
            print("   ", line)
        return 1

    swap(args.paper, args.old, args.new, args.fix)
    if args.note:
        swap(args.note, args.old, args.new, args.fix)
    target = args.paper.with_name(f"{args.new}.md")
    if args.fix:
        subprocess.run(["git", "-C", str(args.paper.parent), "mv",
                        args.paper.name, target.name], check=True)
    print(f"{'переименовано' if args.fix else 'переименовало бы'}: "
          f"{args.old} -> {args.new} ({args.paper.name} -> {target.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
