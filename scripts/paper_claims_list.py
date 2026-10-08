#!/usr/bin/env python3
"""Все утверждения, вытащенные из чужих статей, одним списком.

Разделы «Что статья утверждает» лежат внутри разборов, по одному на статью, и порознь их не
охватить. Проход читает библиотеку из зеркала и печатает их подряд: тема, статья,
утверждение, и — главное — строка «наша оценка», то есть чего слова статьи стоят.

    paper_claims_list.py                 сколько и где
    paper_claims_list.py --theme <слаг>  все утверждения одной темы, целиком
    paper_claims_list.py --doubts        только те, чья оценка говорит «верить нельзя»
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys

#: Зеркало базы на сервере. Путь настраивается, а не вписан: репозиторий публичный,
#: и домашний каталог конкретного человека в него попадать не должен.
MIRROR = pathlib.Path(os.environ.get("LAB_KNOWLEDGE_MIRROR",
                                     "~/brainlab-stack/mirror-gitlab")).expanduser()
HEAD = re.compile(r"^### Утверждение \d+ — (.+)$", re.M)
#: Слова, которыми оценка говорит, что опираться на это нельзя.
DOUBT = re.compile(r"верить нельзя|не установлен|в пределах шума|меньше.{0,20}шум|"
                   r"одном? (?:семен|затравк)|не следует|не подтвержд|"
                   r"числа.{0,30}не дошли|нельзя опираться", re.I)


def git(repo: pathlib.Path, *args: str) -> str:
    ran = subprocess.run(["git", "--git-dir", str(repo), *args],
                         capture_output=True, text=True)
    return ran.stdout if ran.returncode == 0 else ""


def claims(repo: pathlib.Path):
    """(статья, заголовок утверждения, строка «наша оценка») по всей теме."""
    for name in git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines():
        if not name.endswith(".md") or "/" in name:
            continue
        text = git(repo, "show", f"HEAD:{name}")
        block = re.search(r"^## Что статья утверждает(.*?)(?=^## |\Z)", text, re.S | re.M)
        if not block:
            continue
        body = block.group(1)
        chunks = re.split(r"^### Утверждение \d+ — ", body, flags=re.M)[1:]
        for chunk in chunks:
            title = chunk.splitlines()[0].strip()
            said = re.search(r"\*\*наша оценка\.\*\*\s*(.+?)(?=\n\n|\Z)", chunk, re.S)
            yield name[:-3], title, (said.group(1).strip() if said else "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--theme")
    parser.add_argument("--doubts", action="store_true")
    args = parser.parse_args()
    if not MIRROR.is_dir():
        sys.exit(f"нет зеркала {MIRROR}: проход запускается на brain_lab")

    total, doubtful, papers = 0, 0, 0
    by_theme: dict[str, int] = {}
    for repo in sorted(MIRROR.glob("*/literature.git")):
        theme = repo.parent.name
        if args.theme and theme != args.theme:
            continue
        seen = set()
        for paper, title, said in claims(repo):
            total += 1
            seen.add(paper)
            doubt = bool(DOUBT.search(said))
            doubtful += doubt
            if args.doubts and not doubt:
                continue
            if args.theme or args.doubts:
                print(f"\n{theme}/{paper}")
                print(f"  {title}")
                if said:
                    print(f"  оценка: {said[:300]}")
        papers += len(seen)
        if seen:
            by_theme[theme] = by_theme.get(theme, 0) + sum(1 for _ in claims(repo))
    if not args.theme and not args.doubts:
        print(f"утверждений из статей: {total}, статей: {papers}")
        print(f"из них с оценкой «опираться нельзя»: {doubtful}")
        print("\nпо темам:")
        for theme, n in sorted(by_theme.items(), key=lambda kv: -kv[1]):
            print(f"  {theme:34} {n}")
    elif args.doubts:
        print(f"\nвсего сомнительных: {doubtful} из {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
