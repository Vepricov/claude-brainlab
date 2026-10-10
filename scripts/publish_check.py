#!/usr/bin/env python3
"""Что уедет наружу при следующей отправке, и можно ли это публиковать.

Репозиторий публичный, поэтому отправка — это публикация, и отменить её нельзя. 08-10-2026
проверка перед отправкой уже была, но она ПЕЧАТАЛА число совпадений и не останавливала:
`grep -c … || echo 0` возвращает ноль, когда совпадения есть, и отправка прошла. В
публичную историю ушла личная почта третьего человека, ранее не публиковавшаяся. Сторож
должен выходить с ненулевым кодом, а не выводить строку.

    python3 scripts/publish_check.py              # сравнить с origin и lab
    python3 scripts/publish_check.py --remote lab

Ключи ищутся по форме, личные данные — по форме адреса почты и по домашним путям. Своя
почта владельца и уже опубликованное не считаются находкой: сравнение идёт с тем, что на
удалённом УЖЕ лежит, иначе сторож краснел бы на каждой отправке и его бы перестали звать.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

#: Секреты: форма, а не список. Совпадение здесь останавливает отправку всегда.
SECRETS = (
    ("ключ OpenRouter", re.compile(r"sk-or-v1-[A-Za-z0-9]{16,}")),
    ("ключ GitLab", re.compile(r"glpat-[A-Za-z0-9_\-]{16,}")),
    ("ключ GitHub", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("ключ OpenAI", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("закрытый ключ", re.compile(r"BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY")),
    ("ключ Zotero/Plane в коде", re.compile(r"(?:ZOTERO|PLANE)_API_KEY\s*=\s*[\"'][^\"'$]{8,}")),
)

#: Личные данные: чужая почта и домашние пути. Почта владельца исключена: она и так стоит
#: автором в каждом коммите, и считать её утечкой бессмысленно.
OWN_MAIL = ("andrei.veprikov@mbzuai.ac.ae", "veprikov.ad@phystech.edu", "Zeyka666@gmail.com")
PERSONAL = (
    ("чужая почта", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b")),
    ("домашний путь человека", re.compile(r"/(?:Users|home)/(?!\$|<)[A-Za-z][\w.-]*/")),
)


def changed(remote: str, branch: str) -> str:
    """Добавляемые строки относительно того, что на удалённом уже лежит."""
    try:
        subprocess.run(["git", "fetch", "-q", remote], check=False, timeout=60)
        span = f"{remote}/{branch}..HEAD"
        out = subprocess.run(["git", "diff", span], capture_output=True, text=True,
                             timeout=120).stdout
    except (OSError, subprocess.SubprocessError) as failure:
        print(f"не сравнить с {remote}: {failure}", file=sys.stderr)
        return ""
    return "\n".join(line[1:] for line in out.splitlines()
                     if line.startswith("+") and not line.startswith("+++"))


def already(remote: str, branch: str, needle: str) -> bool:
    """Это уже лежит на удалённом? Тогда отправка ничего не публикует заново."""
    done = subprocess.run(["git", "grep", "-q", needle, f"{remote}/{branch}"],
                          capture_output=True, timeout=60)
    return done.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", action="append", default=None)
    parser.add_argument("--branch", default=None)
    asked = parser.parse_args()
    branch = asked.branch or subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    remotes = asked.remote or subprocess.run(
        ["git", "remote"], capture_output=True, text=True).stdout.split()

    found: list[str] = []
    for remote in remotes:
        text = changed(remote, branch)
        if not text:
            continue
        for name, shape in SECRETS:
            for hit in set(shape.findall(text)):
                found.append(f"{remote}: {name} — {hit[:12]}…")
        for name, shape in PERSONAL:
            for hit in set(shape.findall(text)):
                if any(mine in hit for mine in OWN_MAIL):
                    continue
                if already(remote, branch, hit):
                    continue
                found.append(f"{remote}: {name} — {hit}")

    if not found:
        print(f"публиковать можно: новых ключей и чужих личных данных в {branch} нет")
        return 0
    print(f"ОТПРАВЛЯТЬ НЕЛЬЗЯ: {len(found)} находок", file=sys.stderr)
    for line in sorted(set(found)):
        print(f"  {line}", file=sys.stderr)
    print("Публикация необратима. Убери находки и повтори.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
