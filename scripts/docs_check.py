#!/usr/bin/env python3
"""Сторож описаний: не учит ли справочник тому, чего больше нет.

Правило свода: справочник отвечает «как сейчас», журнал — «что и когда поменялось».
Устаревший ответ в справочнике это ошибка, устаревшая запись в журнале — история. Поэтому
сторож смотрит справочник и передние страницы, а журнал и `CHANGELOG.md` не трогает.

Строка, которая САМА сообщает об отмене («команды больше нет», «снята», «переименован»),
не считается мёртвой: иначе сторож краснел бы ровно на тех записях, которыми отмену и
объявили.

    docs_check.py            проверить; код возврата 1, если что-то найдено
"""
from __future__ import annotations

import json
import pathlib
import re
import ssl
import sys
import urllib.parse
import urllib.request

CONF = pathlib.Path.home() / ".config" / "brainlab"
#: Что умерло и чем стало. Ключ — как это пишут в тексте, значение — что сказать человеку.
DEAD = {
    r"\blab pr\b": "команды нет: `git push -o merge_request.create`",
    r"\blab clone\b": "команды нет: обычный `git clone`",
    r"\blab open\b": "команды нет",
    r"lab-work-to-repo": "навык сведён в `lab-knowledge`",
    r"lab-submission": "такого навыка нет",
    r"--задача\b": "флаг зовётся `--task`",
    r"gitlab_board\.py (оснастка|доски|ярлыки)": "подкоманды: equip, boards, labels",
    r"record_figure": "такого вызова нет",
    r"\bпроверить_(числа|ссылки|коды|удаления|исчезнувшее)\b": "ворота зовутся `check_*`",
    r"issue_templates/Задача\.md": "шаблон зовётся `Task.md`",
    r"\bGitea\b": "Gitea снята, база в GitLab",
}
#: Слова, которыми объявляют отмену. Строка с ними говорит о прошлом, а не учит ему.
ABOUT_REMOVAL = ("больше нет", "уже нет", "снят", "снята", "удал", "переимен", "прежн",
                 "больше не", "заменён", "заменен", "вместо", "было", "раньше")
#: Что проверяем. Журнал и CHANGELOG — история, их здесь нет нарочно.
PAGES = [("brainlab/handbook", None),
         ("brainlab/gitlab-profile", "README.md"),
         ("people/gitlab-profile", "README.md"),
         ("ops/gitlab-profile", "README.md"),
         ("brainlab/tools", "README.md")]
SKIP = {"CHANGELOG.md", "canon.md"}


def _ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def call(url: str, token: str, path: str):
    request = urllib.request.Request(f"{url}/api/v4/{path}",
                                     headers={"PRIVATE-TOKEN": token})
    with urllib.request.urlopen(request, timeout=60, context=_ctx()) as answer:
        return json.loads(answer.read().decode())


def text_of(url: str, token: str, project: str, path: str) -> str:
    one = urllib.parse.quote(project, safe="")
    two = urllib.parse.quote(path, safe="")
    request = urllib.request.Request(
        f"{url}/api/v4/projects/{one}/repository/files/{two}/raw?ref=main",
        headers={"PRIVATE-TOKEN": token})
    with urllib.request.urlopen(request, timeout=60, context=_ctx()) as answer:
        return answer.read().decode()


def main() -> int:
    url = CONF.joinpath("git-url").read_text(encoding="utf-8").strip()
    token = CONF.joinpath("git-token").read_text(encoding="utf-8").strip()
    found = 0
    looked = 0
    for project, only in PAGES:
        if only:
            paths = [only]
        else:
            one = urllib.parse.quote(project, safe="")
            tree = call(url, token, f"projects/{one}/repository/tree"
                                     "?recursive=true&per_page=100")
            paths = [row["path"] for row in tree
                     if row["type"] == "blob" and row["path"].endswith(".md")
                     and row["path"] not in SKIP]
        for path in paths:
            try:
                text = text_of(url, token, project, path)
            except (urllib.error.HTTPError, urllib.error.URLError, OSError) as beda:
                print(f"  {project}/{path}: не прочитан ({beda})")
                continue
            looked += 1
            lines = text.splitlines()
            for number, line in enumerate(lines, 1):
                low = line.lower()
                if any(word in low for word in ABOUT_REMOVAL):
                    continue
                for pattern, instead in DEAD.items():
                    for hit in re.finditer(pattern, line):
                        print(f"  {project}/{path}:{number}: {hit.group(0)!r} — {instead}")
                        found += 1
    print(f"страниц прочитано: {looked}, мёртвых упоминаний: {found}")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
