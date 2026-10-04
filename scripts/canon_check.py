#!/usr/bin/env python3
"""Сторож свода: правила одни на всех, и это проверяется, а не обещается.

Источник свода один и лежит в базе: `brainlab/handbook/canon.md`. У машины одна копия,
`~/.claude/rules/lab-canon.md`. Сторож смотрит четыре вещи, и каждая из них однажды уже
расходилась молча:

1. копия на машине совпадает с источником в справочнике — иначе агент работает по тому
   своду, который когда-то налили, и не знает об этом;
2. второй копии нет. Это главное: свод лежал пятью файлами, они совпадали ровно до первой
   правки, и ровно так расходятся навыки в трёх корнях;
3. те, кто должен на свод ссылаться — правило сессии, навыки, хуки, — ссылаются;
4. места, которые свод называет проверяющими (`sweep.py`, `проверить_числа`, проход), в
   коде существуют: иначе «проверяется» становится обещанием.

Пятым номером сторож печатает расхождение навыков между тремя корнями. Это не ошибка
(в репозитории лежит опубликованная копия, у Claude Code и у codex свои), но молчать о нём
нельзя: именно так появляются три навыка, делающие одно и то же.

    canon_check.py              сверить всё; код возврата 1, если есть расхождения
    canon_check.py --offline    не ходить в сеть, сверять по лежащей копии
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOME = pathlib.Path.home()
SYNC = ROOT / "scripts" / "canon_sync.py"

#: Единственная законная копия на машине.
MIRROR = HOME / ".claude" / "rules" / "lab-canon.md"

#: Кто обязан на свод ссылаться. Пересказывать его им нельзя, называть — нужно.
MUST_POINT = (HOME / ".claude" / "rules" / "lab.md",
              HOME / ".claude" / "skills" / "lab-knowledge" / "SKILL.md",
              HOME / ".agents" / "skills" / "lab-knowledge" / "SKILL.md",
              HOME / ".claude" / "scripts" / "mempalace-obsidian-hook.py",
              HOME / ".claude" / "scripts" / "jev_route.py",
              ROOT / "skills" / "lab-knowledge" / "SKILL.md")

#: Навыки, которые тоже пишут в базу: разбор созвона, завод проекта, статья, очередь чтения.
#: Они не про прогоны, но «три места» и «не мусорить» относятся и к ним.
ALSO_POINT = ("call-notes", "create-project", "paper-ingest", "want-2-read")
SKILL_ROOTS = (HOME / ".claude" / "skills", HOME / ".agents" / "skills", ROOT / "skills")

#: Где искать вторую копию свода. Корни, в которых агент читает инструкции, плюс репозиторий.
LOOK_FOR_COPIES = (HOME / ".claude", HOME / ".agents", ROOT / "skills", ROOT / "docs")

#: Где искать то, что свод называет проверяющим. Серверное лежит не в репозитории, поэтому
#: ищется по копии, которая в нём есть.
CODE = (ROOT / "services" / "lab-knowledge" / "scripts",
        ROOT / "services" / "lab-knowledge" / "src" / "lab_knowledge",
        ROOT / "scripts")

#: Признак свода, а не упоминания о нём: заголовок плюс имя правила в разделе.
FINGERPRINT = "# Свод правил базы"


def rules(text: str) -> list[tuple[str, str]]:
    found = []
    for block in re.split(r"\n### ", text)[1:]:
        name = re.match(r"`([a-z-]+)`", block)
        if name:
            found.append((name.group(1), block))
    return found


def mentioned_code(block: str) -> list[str]:
    """Имена из строки «проверяется»: `sweep.py`, `проверить_числа`, `gitlab_cards.py`."""
    line = next((row for row in block.splitlines() if row.startswith("*проверяется")), "")
    return re.findall(r"`([A-Za-zА-Яа-я_][\w.]*)`", line)


def stray_copies() -> list[pathlib.Path]:
    found = []
    for place in LOOK_FOR_COPIES:
        if not place.is_dir():
            continue
        for file in place.rglob("*.md"):
            if file == MIRROR or ".git" in file.parts:
                continue
            try:
                head = file.read_text(encoding="utf-8", errors="replace")[:400]
            except OSError:
                continue
            if FINGERPRINT in head:
                found.append(file)
    return found


def skill_drift() -> list[str]:
    """Один навык в трёх корнях: что разошлось. Не ошибка, но и не тишина."""
    lines = []
    for skill in ("lab-knowledge",) + ALSO_POINT:
        copies = [root / skill for root in SKILL_ROOTS if (root / skill).is_dir()]
        if len(copies) < 2:
            continue
        differs = [str(other) for other in copies[1:]
                   if subprocess.run(["diff", "-rq", "--exclude", "__pycache__",
                                      "--exclude", ".pytest_cache",
                                      str(copies[0]), str(other)],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL).returncode]
        if differs:
            lines.append(f"{skill}: {len(differs) + 1} копии расходятся "
                         f"({copies[0]} против {', '.join(differs)})")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true",
                        help="не ходить в справочник, сверять по лежащей копии")
    args = parser.parse_args()
    bad: list[str] = []

    if not MIRROR.is_file():
        print(f"копии свода на машине нет: {MIRROR}\n"
              f"налить: python3 {SYNC}")
        return 1
    text = MIRROR.read_text(encoding="utf-8")

    if args.offline:
        print("источник не сверялся: --offline")
    else:
        ran = subprocess.run([sys.executable, str(SYNC), "--check"],
                             capture_output=True, text=True, timeout=60)
        if ran.returncode == 1:
            bad.append(ran.stdout.strip() or "копия разошлась с источником")
        elif ran.returncode == 2:
            print("  источник не сверялся:", ran.stdout.strip())

    for copy in stray_copies():
        bad.append(f"вторая копия свода: {copy} — её надо удалить и сослаться на {MIRROR}")

    for pointer in MUST_POINT:
        if not pointer.is_file():
            bad.append(f"должен ссылаться на свод, но файла нет: {pointer}")
        elif "lab-canon.md" not in pointer.read_text(encoding="utf-8"):
            bad.append(f"не ссылается на свод: {pointer}")

    for skill in ALSO_POINT:
        for root in SKILL_ROOTS:
            page = root / skill / "SKILL.md"
            if page.is_file() and "lab-canon.md" not in page.read_text(encoding="utf-8"):
                bad.append(f"пишет в базу и не ссылается на свод: {page}")

    haystack = ""
    for place in CODE:
        for pattern in ("*.py", "*.sh"):
            for file in place.rglob(pattern):
                haystack += file.read_text(encoding="utf-8", errors="replace")

    all_rules = rules(text)
    unchecked = 0
    for name, block in all_rules:
        if "*не проверяется машиной" in block:
            unchecked += 1
            continue
        for thing in mentioned_code(block):
            if thing.endswith((".py", ".sh")):
                if not any((place / thing).exists() or list(place.rglob(thing))
                           for place in CODE):
                    bad.append(f"{name}: назван проверяющим `{thing}`, а такого файла нет")
            elif thing not in haystack:
                bad.append(f"{name}: назван проверяющим `{thing}`, а в коде его нет")

    print(f"правил в своде: {len(all_rules)}, из них держатся на прочтении: {unchecked}")
    for line in skill_drift():
        print("  ~", line)
    for line in bad:
        print("  ✘", line)
    print("расхождений:", len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
