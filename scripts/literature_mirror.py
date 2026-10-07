#!/usr/bin/env python3
"""Сверить утверждения статей в базе и в хранилище Обсидиана, и при просьбе — выровнять.

Разбор статьи живёт в двух местах: файлом `<ключ цитирования>.md` в репозитории литературы
темы и заметкой `<Заголовок статьи>.md` в хранилище. Владелец требует, чтобы они совпадали,
и раздел «Что статья утверждает» — та часть, которая расходится первой: её пишут в базу, а в
заметку забывают.

**Сверять по ключу цитирования, а не по заголовку.** 07-10-2026 замерено на теме
`muon-sign-methods`: из семнадцати разборов три имеют разные заголовки в базе и в хранилище.
У `kornilov2025sign` в базе заголовок без подзаголовка, а заметка названа полностью. У
`tao2026when` в базе `$\\ell_1$-norm`, в заметке `ell_1-norm`. У `wang2026olion` в базе
`$\\ell_\\infty$`, в заметке `$\\ell_{\\infty}$`. Сверка по заголовку объявила бы их
отсутствующими, а блоки у всех трёх совпадали слово в слово.

Ключ есть с обеих сторон: в базе это имя файла, в заметке — ключ в блоке BibTeX. Проверено:
у всех семнадцати заметок он на месте.

    literature_mirror.py <клон литературы> <папка темы в хранилище>
    literature_mirror.py ... --apply      перенести блок из базы в заметку
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CLAIMS = re.compile(r"## Что статья утверждает(.*?)(?=\n## |\Z)", re.S)
BIBKEY = re.compile(r"@\w+\{([^,\s}]+)\s*,")
#: Куда вставлять блок, если его в заметке нет: перед первым из этих разделов. Порядок
#: важен — в хранилище тело разложено иначе, чем в базе, и «AI Explanation» встречается
#: раньше плоских разделов.
BEFORE = ("## AI Explanation", "## Посекционный разбор", "## 1. Общий обзор",
          "## Критическая оценка", "## Математика и формулы")


def claims(text: str) -> str | None:
    found = CLAIMS.search(text)
    return found.group(0).rstrip() if found else None


def same(one: str | None, two: str | None) -> bool:
    """Сравнение без оглядки на то, как расставлены пробелы и переводы строк."""
    flat = lambda text: re.sub(r"\s+", " ", text).strip() if text else text
    return flat(one) == flat(two)


def notes_by_key(folder: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for note in sorted(folder.glob("*.md")):
        if note.name == "README.md":
            continue
        key = BIBKEY.search(note.read_text(encoding="utf-8"))
        if key:
            found[key.group(1)] = note
    return found


def put(note: Path, block: str) -> str:
    """Вписать блок в заметку: заменить прежний или вставить перед разделом разбора."""
    text = note.read_text(encoding="utf-8")
    if CLAIMS.search(text):
        text = CLAIMS.sub(lambda _: block, text, count=1)
        how = "заменён"
    else:
        for head in BEFORE:
            if head in text:
                text = text.replace(head, block + "\n\n" + head, 1)
                how = f"вставлен перед «{head[3:]}»"
                break
        else:
            text = text.rstrip() + "\n\n" + block + "\n"
            how = "дописан в конец"
    note.write_text(text, encoding="utf-8")
    return how


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path, help="клон репозитория литературы темы")
    parser.add_argument("vault", type=Path, help="папка темы в хранилище Обсидиана")
    parser.add_argument("--apply", action="store_true",
                        help="перенести блок из базы в заметку")
    args = parser.parse_args(argv)

    notes = notes_by_key(args.vault)
    papers = [p for p in sorted(args.base.glob("*.md")) if p.name != "README.md"]
    if not papers:
        sys.exit(f"в {args.base} нет разборов")

    agree = fixed = 0
    trouble: list[str] = []
    for paper in papers:
        key = paper.stem
        block = claims(paper.read_text(encoding="utf-8"))
        if block is None:
            trouble.append(f"{key}: в базе нет раздела «Что статья утверждает»")
            continue
        note = notes.get(key)
        if note is None:
            trouble.append(f"{key}: заметки с таким ключом цитирования в хранилище нет")
            continue
        if same(block, claims(note.read_text(encoding="utf-8"))):
            agree += 1
            continue
        if args.apply:
            trouble.append(f"{key}: {put(note, block)} в «{note.name}»")
            fixed += 1
        else:
            trouble.append(f"{key}: блок в заметке «{note.name}» расходится с базой")

    for line in trouble:
        print(" ", line)
    tail = f", выровнено: {fixed}" if args.apply else ""
    print(f"разборов: {len(papers)}, совпадают: {agree}, расходятся или без пары: "
          f"{len(trouble) - fixed if args.apply else len(trouble)}{tail}")
    return 1 if (len(trouble) - fixed if args.apply else trouble) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
