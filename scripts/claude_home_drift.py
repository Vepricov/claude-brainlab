#!/usr/bin/env python3
"""Что в `~/.claude` разошлось с репозиторием, и наоборот.

Раздаёт файлы `install/setup.sh`: он копирует `hooks/`, `scripts/`, `rules/`, `skills/`,
`commands/`, `agents/` в `~/.claude` и подставляет в них значения из `.env`. Поэтому правка,
сделанная прямо в `~/.claude`, у остальных не появляется, а правка в репозитории не
действует на этой машине, пока её не перенесли. 08-10-2026 это стоило дня: три файла хука
разошлись на 150, 137 и 57 строк, и студент после установки получал версию, которая молчала
121 ход из 137. В тот же день, уже после починки, разошёлся четвёртый — я забыл одну
команду копирования, и хук напечатал текст, который был удалён получасом раньше.

Расхождение ничем не ловилось. Теперь ловится:

    python3 scripts/claude_home_drift.py            # показать расхождения
    python3 scripts/claude_home_drift.py --apply    # перенести из репозитория в ~/.claude

Подстановки учитываются: файл с `${OBSIDIAN_VAULT}` в репозитории и подставленным путём в
`~/.claude` расхождением не считается.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

ROOTS = ("hooks", "scripts", "rules", "skills", "commands", "agents")
HOME = Path.home() / ".claude"
PLACEHOLDER = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")
#: Файлы и папки, которые живут только на машине и в репозиторий не ходят: резервные копии,
#: кеши и навыки, которые присылает сам Claude Code. Без этого список «есть только в
#: ~/.claude» вырастал до 454 строк и в нём терялось главное.
SKIP = {".DS_Store", "__pycache__", "synced", "disabled"}


def ignored(relative: Path) -> bool:
    name = relative.name
    return (any(part in SKIP for part in relative.parts)
            or ".bak" in name or name.endswith("~") or name.startswith("."))


def env_of(repo: Path) -> dict[str, str]:
    """Значения подстановок: из `.env`, иначе из окружения."""
    found: dict[str, str] = {}
    place = repo / ".env"
    if place.is_file():
        for line in place.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, _, value = line.partition("=")
                found[key.strip()] = value.strip().strip('"').strip("'")
    return found


def expanded(text: str, values: dict[str, str]) -> str:
    return PLACEHOLDER.sub(lambda m: values.get(m.group(1), os.environ.get(m.group(1), m.group(0))),
                           text)


def same(repo_file: Path, home_file: Path, values: dict[str, str]) -> bool:
    try:
        mine = repo_file.read_text(encoding="utf-8")
        theirs = home_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        try:
            return repo_file.read_bytes() == home_file.read_bytes()
        except OSError:
            return False
    return expanded(mine, values) == theirs or mine == theirs


def walk(repo: Path):
    for root in ROOTS:
        base = repo / root
        if not base.is_dir():
            continue
        for item in base.rglob("*"):
            relative = item.relative_to(repo)
            if not item.is_file() or ignored(relative):
                continue
            yield relative


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="перенести расходящиеся файлы из репозитория в ~/.claude")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--verbose", action="store_true", help="перечислить отсутствующие")
    asked = parser.parse_args()
    repo = Path(asked.repo).resolve()
    values = env_of(repo)

    differs: list[Path] = []
    missing: list[Path] = []
    for relative in walk(repo):
        home_file = HOME / relative
        if not home_file.exists():
            missing.append(relative)
        elif not same(repo / relative, home_file, values):
            differs.append(relative)

    only_home: list[Path] = []
    for root in ROOTS:
        base = HOME / root
        if not base.is_dir():
            continue
        for item in base.rglob("*"):
            relative = item.relative_to(HOME)
            if not item.is_file() or ignored(relative):
                continue
            if not (repo / relative).exists():
                only_home.append(relative)

    # Расходящиеся печатаются поимённо: только они означают, что две копии живут своей
    # жизнью и одна из них неверна. Отсутствующие — чаще всего сборочные скрипты
    # репозитория, которые на этой машине просто не нужны, поэтому их только считаем:
    # 131 строка такого списка прятала семь настоящих расхождений.
    if differs:
        print(f"расходятся: {len(differs)}")
        for relative in sorted(differs):
            mine = (repo / relative).stat().st_mtime
            theirs = (HOME / relative).stat().st_mtime
            newer = "репозиторий" if mine > theirs else "~/.claude"
            print(f"  {relative}  (свежее: {newer})")
    if missing:
        print(f"нет в ~/.claude: {len(missing)} — это нормально для сборочных скриптов; "
              f"полный список по --verbose")
        if asked.verbose:
            for relative in sorted(missing):
                print(f"  {relative}")
    if only_home:
        print(f"есть только в ~/.claude, в репозиторий не попадёт: {len(only_home)}")
        for relative in sorted(only_home)[:40]:
            print(f"  {relative}")

    if asked.apply:
        for relative in differs + missing:
            target = HOME / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            text = (repo / relative).read_text(encoding="utf-8", errors="surrogateescape")
            target.write_text(expanded(text, values), encoding="utf-8",
                              errors="surrogateescape")
            shutil.copymode(repo / relative, target)
        print(f"перенесено: {len(differs) + len(missing)}")

    if not (differs or missing or only_home):
        print("расхождений нет")
    return 1 if differs and not asked.apply else 0


if __name__ == "__main__":
    sys.exit(main())
