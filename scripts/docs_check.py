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
    r"claude mcp add": "служба MCP снята 05-10-2026, база читается git'ом",
    # Не ловить имена файлов вида `lab-knowledge-checkpoint.py`: это хук, а не служба.
    # Поэтому после имени не должно идти дефиса.
    r"\blab-knowledge(?!-)\b(?=[^\n]*\b(MCP|служб|сервер)\b)": "MCP снят, остался навык",
}
#: Слова, которыми объявляют отмену. Строка с ними говорит о прошлом, а не учит ему.
ABOUT_REMOVAL = ("больше нет", "уже нет", "снят", "снята", "удал", "переимен", "прежн",
                 "больше не", "заменён", "заменен", "вместо", "было", "раньше",
                 # 07-10-2026: раздел объявлял себя историей словами «перестал быть правдой»
                 # и «остановлена», которых в списке не было, и сторож краснел на самой
                 # записи об отмене. Список слов — часть правила, а не оформление.
                 "перестал", "останов", "выключ", "это раздел про прошлое", "история",
                 # `README.md` и `SKILLS.md` написаны по-английски, и объявление отмены в них
                 # тоже английское. Без этих слов сторож краснел на фразе «the MCP service
                 # was removed on 05-10-2026», то есть ровно на объявлении.
                 "was removed", "were removed", "no longer", "used to", "folded into",
                 "replaces the old", "retired", "renamed")
#: Что проверяем. Журнал и CHANGELOG — история, их здесь нет нарочно.
PAGES = [("brainlab/handbook", None),
         ("brainlab/gitlab-profile", "README.md"),
         ("people/gitlab-profile", "README.md"),
         ("ops/gitlab-profile", "README.md"),
         ("brainlab/tools", "README.md")]
SKIP = {"CHANGELOG.md", "canon.md"}
#: Страницы этого репозитория. 07-10-2026 выяснилось, зачем они здесь нужны: в
#: `docs/architecture.md` целый раздел описывал службу MCP как живую через два дня после её
#: снятия, и сторож этого не видел, потому что смотрел только GitLab. Журнал и история
#: переезда сюда не входят по той же причине, что и CHANGELOG: это рассказ о прошлом.
HERE = pathlib.Path(__file__).resolve().parent.parent
LOCAL_SKIP = {"gitlab-migration.md", "gitlab-structure-proposal.md", "gitlab-layout.md"}


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


def about_removal(lines: list[str], number: int) -> bool:
    """Говорит ли строка (или её абзац) о прошлом, а не учит ему.

    Границей абзаца считается пустая строка или заголовок: отмену объявляют абзацем, и
    слова «перестало быть правдой» часто стоят в его начале, а имя снятого — ниже.
    """
    start = number
    while start > 0 and lines[start - 1].strip() and not lines[start - 1].startswith("#"):
        start -= 1
    end = number
    while end < len(lines) - 1 and lines[end + 1].strip() and not lines[end + 1].startswith("#"):
        end += 1
    para = " ".join(lines[start:end + 1]).lower()
    if any(word in para for word in ABOUT_REMOVAL):
        return True
    # Раздел, объявивший себя историей в своей преамбуле, ей не учит. Преамбула — первый
    # абзац после заголовка, и только он: иначе одно слово «прежний» в середине длинного
    # раздела освободило бы от проверки всё остальное.
    head = start
    while head > 0 and not lines[head].startswith("## "):
        head -= 1
    if not lines[head].startswith("## ") or head == start:
        return False
    first = head + 1
    while first < len(lines) and not lines[first].strip():
        first += 1
    last = first
    while last < len(lines) - 1 and lines[last + 1].strip() and not lines[last + 1].startswith("#"):
        last += 1
    preamble = " ".join(lines[first:last + 1]).lower()
    return any(word in preamble for word in ABOUT_REMOVAL)


def remarks(where: str, text: str) -> int:
    """Назвать мёртвые упоминания в одном тексте. Возвращает, сколько нашлось."""
    found = 0
    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        if about_removal(lines, number - 1):
            continue
        for pattern, instead in DEAD.items():
            for hit in re.finditer(pattern, line):
                print(f"  {where}:{number}: {hit.group(0)!r} — {instead}")
                found += 1
    return found


def local_pages() -> list[pathlib.Path]:
    """Страницы этого репозитория, которые отвечают «как сейчас»."""
    docs = sorted(HERE.joinpath("docs").glob("*.md"))
    roots = [HERE / "README.md", HERE / "SKILLS.md", HERE / "CLAUDE.md"]
    return [page for page in docs + roots
            if page.is_file() and page.name not in SKIP | LOCAL_SKIP]


def main() -> int:
    url = CONF.joinpath("git-url").read_text(encoding="utf-8").strip()
    token = CONF.joinpath("git-token").read_text(encoding="utf-8").strip()
    found = 0
    looked = 0
    unread = 0
    for project, only in PAGES:
        if only:
            paths = [only]
        else:
            one = urllib.parse.quote(project, safe="")
            # База может быть недоступна: проброс порта упал, сервер перезапускается. Тогда
            # сторож должен сказать, чего не прочёл, и проверить локальные страницы, а не
            # падать трассировкой — 07-10-2026 он падал, то есть молчал именно тогда, когда
            # нужен.
            try:
                tree = call(url, token, f"projects/{one}/repository/tree"
                                         "?recursive=true&per_page=100")
            except (urllib.error.HTTPError, urllib.error.URLError, OSError) as beda:
                print(f"  {project}: дерево не прочитано ({beda}), страницы базы пропущены")
                unread += 1
                continue
            paths = [row["path"] for row in tree
                     if row["type"] == "blob" and row["path"].endswith(".md")
                     and row["path"] not in SKIP]
        for path in paths:
            try:
                text = text_of(url, token, project, path)
            except (urllib.error.HTTPError, urllib.error.URLError, OSError) as beda:
                print(f"  {project}/{path}: не прочитан ({beda})")
                unread += 1
                continue
            looked += 1
            found += remarks(f"{project}/{path}", text)
    for page in local_pages():
        looked += 1
        found += remarks(str(page.relative_to(HERE)), page.read_text(encoding="utf-8"))
    note = f", не прочитано: {unread}" if unread else ""
    print(f"страниц прочитано: {looked}, мёртвых упоминаний: {found}{note}")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
