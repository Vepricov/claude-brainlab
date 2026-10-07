#!/usr/bin/env python3
"""Ярлык на статью: разбор лежит в одной теме, показан в нескольких.

Статья редко принадлежит одной теме. `allaire2026zeroth` — безградиентная оптимизация и
предобуславливание сразу, и разбор завели в обеих темах. Копии разошлись: заголовки
утверждений переписали дважды и независимо. В хранилище же заметка одна, с жёсткой
ссылкой, и она не могла быть равна обеим копиям.

Поэтому вместо второй копии в гостевой теме лежит **ярлык** — файл `<ключ>.md` из одной
строки-ссылки на разбор в теме-хозяйке. Правка одна, расходиться нечему. Проходы, которые
читают литературу, ярлык видят и идут за содержимым в тему-хозяйку; сверка с хранилищем
его пропускает, потому что заметка в хранилище одна и ведётся по теме-хозяйке.

    paper_label.py список <клон литературы>...
    paper_label.py повесить <ключ> --хозяйка <клон> --гостья <клон>
    paper_label.py снять    <ключ> --гостья <клон>

Ярлык узнаётся по строке `> Разбор этой статьи ведётся в теме` в начале файла.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

MARK = "> Разбор этой статьи ведётся в теме"
LABEL = re.compile(r"^> Разбор этой статьи ведётся в теме \[([^\]]+)\]")


def is_label(text: str) -> str | None:
    """Если файл — ярлык, вернуть слаг темы-хозяйки."""
    for line in text.splitlines():
        found = LABEL.match(line)
        if found:
            return found.group(1)
        if line.strip() and not line.startswith(("---", "#")):
            return None
    return None


def home_url(home: Path) -> tuple[str, str]:
    """Слаг темы-хозяйки и адрес её репозитория литературы.

    Адрес берётся из `origin` клона, а не склеивается из слага: тема лежит внутри
    направления (`zero-order/zo-estimators`), и ссылка на `brainlab/<слаг>` ведёт в никуда.
    """
    out = subprocess.run(["git", "-C", str(home), "remote", "get-url", "origin"],
                         capture_output=True, text=True).stdout.strip()
    if not out.endswith("/literature.git"):
        sys.exit(f"«{home}» не похожа на клон репозитория литературы: origin = {out!r}")
    web = out[:-len(".git")]
    return home.name, web


def render(key: str, title: str, home: str, web: str) -> str:
    return (f"# {title}\n\n"
            f"{MARK} [{home}]({web}/-/blob/main/{key}.md).\n\n"
            "Здесь лежит ярлык, а не копия: статья относится и к этой теме, но разбор "
            "один, и правится он у хозяйки. Вторая копия неизбежно разойдётся с первой — "
            "так уже было.\n")


def title_of(text: str) -> str:
    found = re.search(r"(?m)^#\s+(.+)$", text)
    return found.group(1).strip() if found else "без заголовка"


def show(roots: list[Path]) -> int:
    found = 0
    for root in sorted(roots):
        for paper in sorted(root.glob("*.md")):
            if paper.name == "README.md":
                continue
            home = is_label(paper.read_text(encoding="utf-8"))
            if home:
                found += 1
                print(f"  {root.name}/{paper.stem} -> хозяйка «{home}»")
    print(f"ярлыков на статьи: {found}")
    return 0


def hang(key: str, home: Path, guest: Path) -> int:
    source = home / f"{key}.md"
    if not source.exists():
        sys.exit(f"в теме-хозяйке «{home.name}» разбора {key} нет")
    target = guest / f"{key}.md"
    if target.exists():
        text = target.read_text(encoding="utf-8")
        if is_label(text):
            print(f"в «{guest.name}» уже ярлык на {key}")
            return 0
        print(f"  в «{guest.name}» лежала копия на {len(text.encode())} б, заменяю ярлыком")
    slug, web = home_url(home)
    target.write_text(render(key, title_of(source.read_text(encoding="utf-8")),
                             slug, web), encoding="utf-8")
    print(f"ярлык повешен: {key} ведётся в «{home.name}», показан в «{guest.name}»")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="что", required=True)
    listing = sub.add_parser("список")
    listing.add_argument("roots", type=Path, nargs="+")
    put = sub.add_parser("повесить")
    put.add_argument("ключ")
    put.add_argument("--хозяйка", type=Path, required=True, dest="home")
    put.add_argument("--гостья", type=Path, required=True, dest="guest")
    off = sub.add_parser("снять")
    off.add_argument("ключ")
    off.add_argument("--гостья", type=Path, required=True, dest="guest")
    args = parser.parse_args(argv)

    if args.что == "список":
        return show(args.roots)
    if args.что == "снять":
        target = args.guest / f"{getattr(args, 'ключ')}.md"
        if not target.exists() or not is_label(target.read_text(encoding="utf-8")):
            sys.exit(f"в «{args.guest.name}» ярлыка на {getattr(args, 'ключ')} нет")
        target.unlink()
        print(f"ярлык снят: {getattr(args, 'ключ')} больше не показан в «{args.guest.name}»")
        return 0
    return hang(getattr(args, "ключ"), args.home, args.guest)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
