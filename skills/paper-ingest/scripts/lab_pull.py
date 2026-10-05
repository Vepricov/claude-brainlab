#!/usr/bin/env python3
"""Забрать статью из репозитория темы лаборатории в локальное хранилище.

Статьи появляются в базе и без владельца: их добавляют другие участники. Сами по себе
они локально не возникают — и не должны. Этот скрипт показывает, чего в хранилище нет,
и по отдельной команде кладёт выбранную статью в `Literature/_inbox`, откуда владелец
сам решает, переносить ли её в папку темы.

    lab_pull.py --list                        что есть в базе, но нет локально
    lab_pull.py --list --theme latent-reasoning
    lab_pull.py --pull zheng2025soft          положить страницу в _inbox
    lab_pull.py --pull zheng2025soft --into-theme   сразу в папку темы
    lab_pull.py --sync                        забрать в _inbox всё, чего нет
    lab_pull.py --accept                      принять всё из _inbox в предложенные темы
    lab_pull.py --accept zheng2025soft        принять одну

`--sync` — то же самое без выбора руками: всё, что появилось в базе и чего нет в
хранилище, приезжает в `_inbox` целиком, вместе с разбором и рисунками. Перед этим
он подметает `_trash`: статью, которую владелец туда перетащил, скрипт заносит в
журнал отказов и удаляет вместе с её вложениями, так что следующий проход её не
принесёт обратно. Из базы при этом ничего не удаляется — там она принадлежит тому,
кто её добавил.

У каждой привезённой статьи в шапке стоит `предложенная тема` — та, в которой её страница
лежит в базе, то есть не догадка. Принять предложение можно двумя способами, и оба ведут в
одно место: перетащить заметку в папку темы руками или сказать `--accept`. После приёмки
статья уезжает в `Literature/<тема>/` вместе с рисунками, добавляется в ту же тему на
AlphaXiv и заводится в коллекции `Literature/<тема>` в Zotero. Заметку, перенесённую
руками, следующий `--sync` доводит до того же состояния сам.
"""
import argparse, base64, json, os, re, shutil, ssl, subprocess, sys
from datetime import datetime as _dt
from urllib.parse import quote, unquote
import urllib.request, urllib.error

#: База знания переехала с Gitea на GitLab 01-10-2026. Отличий три, и каждое
#: ломает старый код молча: авторизация заголовком `PRIVATE-TOKEN`, а не
#: `Authorization: token`; у каждой темы теперь ОТДЕЛЬНЫЙ проект `literature`
#: внутри группы темы, а не папка `literature/` в репозитории темы; и страницы
#: лежат в корне проекта, без префикса. Адрес и ключ — рядом с токеном.
URL_FILE = os.path.expanduser("~/.config/brainlab/git-url")
TOKEN_FILE = os.path.expanduser("~/.config/brainlab/git-token")
#: У GitLab лаборатории самоподписанный сертификат на sslip.io: проверку цепочки
#: отключаем осознанно, адрес берётся из файла на диске, а не из сети.
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
_ПРОЕКТЫ: dict = {}


def base():
    if not os.path.exists(URL_FILE):
        sys.exit("нет адреса базы: ~/.config/brainlab/git-url")
    return open(URL_FILE).read().strip().rstrip("/")


def token():
    if not os.path.exists(TOKEN_FILE):
        sys.exit("нет токена агента: ~/.config/brainlab/git-token")
    return open(TOKEN_FILE).read().strip()


def api(путь, tok, raw=False, страницами=False):
    """Запрос к GitLab. `страницами` собирает все страницы ответа, а не первую."""
    собрано = []
    стр = 1
    while True:
        сшивка = "&" if "?" in путь else "?"
        адрес = f"{base()}{путь}{сшивка}per_page=100&page={стр}" if страницами else f"{base()}{путь}"
        req = urllib.request.Request(адрес, headers={"PRIVATE-TOKEN": tok})
        # База обрывает соединение, когда к ней идут сотнями подряд: один проход
        # это 650 запросов, и `Connection refused` на середине терял весь обход.
        # Три попытки с нарастающей паузой; 404 это ответ, а не сбой.
        данные = None
        for попытка in range(3):
            try:
                данные = urllib.request.urlopen(req, timeout=90, context=_CTX).read()
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                if e.code in (429, 500, 502, 503, 504) and попытка < 2:
                    time.sleep(2 ** попытка * 3)
                    continue
                raise
            except (urllib.error.URLError, OSError):
                if попытка == 2:
                    raise
                time.sleep(2 ** попытка * 3)
        if данные is None:
            return None
        if raw:
            return данные
        кусок = json.loads(данные.decode())
        if not страницами:
            return кусок
        собрано += кусок
        if len(кусок) < 100:
            return собрано
        стр += 1


#: Что уже прочитано из базы: `тема/файл -> {sha, title, arxiv, url}`. Нужен
#: только ради скорости, удаление безопасно — следующий проход соберёт заново.
КЕШ_FILE = os.path.expanduser("~/.config/brainlab/pages-cache.json")
_КЕШ: dict = {}


def _кеш():
    global _КЕШ
    if not _КЕШ and os.path.exists(КЕШ_FILE):
        try:
            _КЕШ = json.load(open(КЕШ_FILE, encoding="utf-8"))
        except (OSError, ValueError):
            _КЕШ = {}
    return _КЕШ


def _сохранить_кеш(кеш):
    try:
        tmp = КЕШ_FILE + ".tmp"
        json.dump(кеш, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
        os.replace(tmp, КЕШ_FILE)
    except OSError:
        pass


def проекты(tok):
    """Тема -> числовой id её проекта `literature`.

    Тема это предпоследний сегмент пути: `brainlab/zero-order/zo-estimators/literature`.
    """
    if _ПРОЕКТЫ:
        return _ПРОЕКТЫ
    for пр in api("/api/v4/projects?simple=true", tok, страницами=True) or []:
        путь = пр.get("path_with_namespace", "")
        части = путь.split("/")
        if len(части) >= 2 and части[-1] == "literature":
            _ПРОЕКТЫ[части[-2]] = пр["id"]
    return _ПРОЕКТЫ


def файл(pid, путь, tok):
    """Содержимое файла из корня проекта темы."""
    return api(f"/api/v4/projects/{pid}/repository/files/{quote(путь, safe='')}/raw?ref=main",
               tok, raw=True)

VAULT = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/shkodnik1917")
LIB = os.path.join(VAULT, "Literature")
IMG = (".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp")
INBOX = "_inbox"
TRASH = "_trash"
REJECTED = "_trash/paper-search_rejected.md"
NOT_A_THEME = {"grants"}          # репозиторий лаборатории, но не тема литературы




def themes_local():
    return sorted(x for x in os.listdir(LIB)
                  if os.path.isdir(os.path.join(LIB, x)) and not x.startswith(("_", ".")))


def local_arxivs():
    """Все номера arXiv, уже лежащие в хранилище."""
    out = set()
    for root, dirs, files in os.walk(LIB):
        dirs[:] = [d for d in dirs if d != "_attachments"]
        for f in files:
            if not f.endswith(".md"):
                continue
            try:
                txt = open(os.path.join(root, f), encoding="utf-8").read(4000)
            except OSError:
                continue
            out |= set(re.findall(r"arxiv\.org/abs/([^\s\")\]]+)", txt))
    return out


def pages_in_git(theme, tok):
    """Страницы темы в базе: ключ цитирования, название и номер arXiv.

    В GitLab у темы свой проект `literature`, и страницы лежат в его КОРНЕ,
    а не в подпапке. Поэтому отбираем `*.md` нулевой глубины, кроме README.
    """
    pid = проекты(tok).get(theme)
    if pid is None:
        return []
    дерево = api(f"/api/v4/projects/{pid}/repository/tree?recursive=true&ref=main",
                 tok, страницами=True) or []
    кеш = _кеш()
    out = []
    for x in дерево:
        p = x.get("path", "")
        if x.get("type") != "blob" or not p.endswith(".md") or "/" in p or p == "README.md":
            continue
        # Хеш файла дерево отдаёт бесплатно. Перечитываем только то, что
        # изменилось: иначе каждый проход тянет 651 страницу по сети, и один
        # обход всех тем занимает полчаса вместо минуты.
        ключ_кеша = f"{theme}/{p}"
        запись = кеш.get(ключ_кеша)
        if запись and запись.get("sha") == x.get("id"):
            out.append({"theme": theme, "key": p[:-3], "title": запись["title"],
                        "arxiv": запись["arxiv"], "url": запись["url"], "text": None,
                        "pid": pid})
            continue
        сырое = файл(pid, p, tok)
        if not сырое:
            continue
        txt = сырое.decode()
        title = txt.split("\n", 1)[0].lstrip("# ").strip()
        m = re.search(r"\[Открыть источник\]\((https?://[^)]+)\)", txt)
        url = m.group(1) if m else ""
        ax = re.search(r"arxiv\.org/abs/([^)\s]+)", url)
        ax_id = ax.group(1) if ax else ""
        кеш[ключ_кеша] = {"sha": x.get("id"), "title": title, "arxiv": ax_id, "url": url}
        out.append({"theme": theme, "key": os.path.basename(p)[:-3], "title": title,
                    "arxiv": ax_id, "url": url, "text": txt, "pid": pid})
    _сохранить_кеш(кеш)
    return out


ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}$")


def norm_title(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def local_titles():
    """Названия заметок хранилища: по ним ловим статьи, у которых нет номера arXiv.

    В базе такие страницы опознаются слагом AlphaXiv вроде `2609.deepseek-v4-1-flash`,
    и сравнение по номеру их не находит — статья приезжала бы в _inbox каждый проход.
    """
    out = set()
    for root, dirs, files in os.walk(LIB):
        dirs[:] = [d for d in dirs if d != "_attachments"]
        for f in files:
            if f.endswith(".md") and f != "README.md":
                out.add(norm_title(f[:-3]))
    return out


def themes_git(tok):
    """Темы берём из базы, а не из локальных папок: тема могла появиться без владельца."""
    return sorted(т for т in проекты(tok) if т not in NOT_A_THEME)


def rejected_arxivs():
    """Номера, которые владелец уже отверг: обратно их не приносим."""
    p = os.path.join(LIB, REJECTED)
    if not os.path.exists(p):
        return set()
    return set(re.findall(r"arxiv\.org/abs/([^\s\")\]]+)", open(p, encoding="utf-8").read()))


def sweep_trash():
    """Статья, перетащенная в _trash, уходит в журнал отказов и удаляется с вложениями."""
    d = os.path.join(LIB, TRASH)
    if not os.path.isdir(d):
        return []
    swept = []
    try:
        файлы = sorted(os.listdir(d))
    except OSError as беда:
        # macOS отказывает службе из launchd в доступе к iCloud (TCC), и прежде это роняло
        # ВЕСЬ проход: `sweep_trash` зовётся в начале `main`, поэтому синхронизация не
        # начиналась вовсе. Пятнадцать отказов подряд в журнале. Корзина не настолько важна,
        # чтобы из-за неё не приезжали новые статьи, поэтому здесь только предупреждение.
        print(f"корзину прочитать не удалось ({беда}); остальное делаю", flush=True)
        return []
    for f in файлы:
        p = os.path.join(d, f)
        if not f.endswith(".md") or os.path.join(TRASH, f).replace(os.sep, "/") == REJECTED:
            continue
        txt = open(p, encoding="utf-8").read()
        ax = re.search(r"arxiv\.org/abs/([^\s\")\]]+)", txt)
        title = re.search(r'(?m)^title:\s*"?([^"\n]+)', txt)
        title = (title.group(1) if title else f[:-3]).strip()
        url = f"https://arxiv.org/abs/{ax.group(1)}" if ax else "—"
        line = (f"- {_dt.now().strftime('%d-%m-%Y')} — {title} — {url} — "
                f"выброшено из _inbox владельцем\n")
        led = os.path.join(LIB, REJECTED)
        os.makedirs(os.path.dirname(led), exist_ok=True)
        if not os.path.exists(led):
            open(led, "w", encoding="utf-8").write("# paper-search rejected\n\n")
        with open(led, "a", encoding="utf-8") as fh:
            fh.write(line)
        if ax:                                    # вложения этой статьи тоже лишние
            att = os.path.join(d, "_attachments", ax.group(1))
            if os.path.isdir(att):
                shutil.rmtree(att)
        os.remove(p)
        swept.append(title)
    return swept


def pull_one(found, tok, into_theme=False):
    target = os.path.join(LIB, found["theme"]) if into_theme else os.path.join(LIB, INBOX)
    os.makedirs(target, exist_ok=True)
    name = re.sub(r'[\\/:*?"<>|]', " ", found["title"]).strip() or found["key"]
    dst = os.path.join(target, f"{name}.md")
    текст = found.get("text")
    if текст is None:                      # страница пришла из кеша, тела нет
        текст = (файл(found["pid"], f"{found['key']}.md", tok) or b"").decode()
    body = to_obsidian(текст, found["theme"], found["key"], tok, target)
    front = (f"---\ntitle: \"{found['title']}\"\n"
             f"url: \"{found['url']}\"\ntags:\n  - {found['theme']}\n"
             f"предложенная тема: {found['theme']}\n"
             f"источник: база лаборатории, {found['theme']}/{found['key']}\n---\n\n")
    if not into_theme:
        front += (f"> [!note] Предложенная тема — `{found['theme']}`\n"
                  f"> В базе разбор лежит именно там. Согласен — перетащи заметку в "
                  f"`Literature/{found['theme']}/` или скажи `lab_pull.py --accept`: "
                  f"статья уедет туда вместе с рисунками и появится в этой же теме на "
                  f"AlphaXiv и в Zotero. Не нужна — перетащи в `Literature/_trash`.\n\n")
    open(dst, "w", encoding="utf-8").write(front + body)
    return dst


def to_obsidian(txt, theme, key, tok, target_dir):
    """Ссылки на файлы репозитория переводим в вики-ссылки, рисунки скачиваем рядом."""
    def img(m):
        alt, src = m.group(1), unquote(m.group(2))
        if src.startswith("http"):
            return m.group(0)
        rel = src[len("_attachments/"):] if src.startswith("_attachments/") else src
        pid = проекты(tok).get(theme)
        data = файл(pid, src, tok) if pid is not None else None
        if not data:
            return f"*(рисунок не скачался: `{os.path.basename(src)}`)*"
        dst = os.path.join(target_dir, "_attachments", rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(data)
        return f"![[Literature/{os.path.basename(target_dir)}/_attachments/{rel}]]"
    txt = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", img, txt)
    txt = txt.replace(f"[← вся литература темы](../README.md)",
                      f"[[Literature/{theme}/README|← вся литература темы]]")
    return txt


ПРЕДЛОЖЕНА = re.compile(r"(?m)^предложенная тема:\s*(\S+)\s*$")
ПРИНЯТА = re.compile(r"(?m)^принято:\s*\S+")
ВСТАВКА = re.compile(r"!\[\[Literature/([^/\]]+)/_attachments/([^\]]+)\]\]")


def карта_alphaxiv():
    p = os.path.expanduser("~/.claude/alphaxiv-library-map.json")
    try:
        return json.load(open(p, encoding="utf-8")).get("folders") or {}
    except (OSError, ValueError):
        return {}


def на_сервере(*команда):
    """Позвать скрипт на do-vpn: там живой токен AlphaXiv и ключ Web API Zotero.

    Локально сервер AlphaXiv в Claude Code просит вход в браузере и в неинтерактивном
    прогоне отвечает «Needs authentication», а Zotero на маке заперт приложением. Поэтому
    зеркалирование идёт с сервера — и молча не пропускается: отказ печатается.
    """
    try:
        готово = subprocess.run(("ssh", "do-vpn", " ".join(команда)),
                                capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as e:
        return False, str(e)[:160]
    if готово.returncode:
        return False, (готово.stderr or готово.stdout).strip().splitlines()[-1][:160] if (
            готово.stderr or готово.stdout).strip() else f"код {готово.returncode}"
    return True, готово.stdout.strip()[:160]


def зеркалировать(arxiv, тема):
    """Статья принята: она обязана появиться в этой же теме на AlphaXiv и в Zotero."""
    итоги = []
    fid = карта_alphaxiv().get(тема)
    if not arxiv:
        итоги.append("AlphaXiv пропущен: у статьи нет номера arXiv")
    elif not fid:
        итоги.append(f"AlphaXiv пропущен: темы «{тема}» нет в alphaxiv-library-map.json")
    else:
        ладно, что = на_сервере(
            "python3", "/root/paper-agent/ax_call.py", "save_papers_to_folder",
            f"'{json.dumps({'folder_id': fid, 'paper_ids_or_urls': [arxiv]})}'")
        итоги.append("AlphaXiv: добавлено" if ладно else f"AlphaXiv не вышло: {что}")
    if arxiv:
        ладно, что = на_сервере("/root/paper-agent/.venv/bin/python3",
                                "/root/paper-agent/zotero_web.py", "--arxiv", arxiv,
                                "--folder", тема)
        итоги.append("Zotero: есть" if ладно else f"Zotero не вышло: {что}")
    return итоги


def _перенести(путь, тема):
    """Заметку и её рисунки — из _inbox в папку темы, с правкой вики-вставок."""
    цель = os.path.join(LIB, тема)
    os.makedirs(цель, exist_ok=True)
    if os.path.exists(os.path.join(цель, os.path.basename(путь))):
        # Заметка с таким названием в теме уже есть: чужой разбор затирать нельзя.
        return ""
    txt = open(путь, encoding="utf-8").read()
    откуда = os.path.basename(os.path.dirname(путь))
    for где, хвост in set(ВСТАВКА.findall(txt)):
        if где != откуда:
            continue
        a = os.path.join(LIB, где, "_attachments", хвост)
        b = os.path.join(цель, "_attachments", хвост)
        if os.path.exists(a) and not os.path.exists(b):
            os.makedirs(os.path.dirname(b), exist_ok=True)
            shutil.move(a, b)
    txt = txt.replace(f"![[Literature/{откуда}/_attachments/",
                      f"![[Literature/{тема}/_attachments/")
    новый = os.path.join(цель, os.path.basename(путь))
    open(новый, "w", encoding="utf-8").write(txt)
    os.remove(путь)
    return новый


def _отметить(путь):
    txt = open(путь, encoding="utf-8").read()
    if ПРИНЯТА.search(txt):
        return
    строка = f"принято: {_dt.now().strftime('%d-%m-%Y')}\n"
    txt = re.sub(r"(?m)^(источник: .*)$", lambda m: строка + m.group(1), txt, count=1)
    # убрать подсказку про приёмку: решение принято
    txt = re.sub(r"(?m)^> \[!note\] Предложенная тема.*(?:\n^>.*)*\n\n", "", txt, count=1)
    open(путь, "w", encoding="utf-8").write(txt)


def принять(какие):
    """Разложить `_inbox` по предложенным темам и дозеркалить перенесённое руками."""
    d = os.path.join(LIB, INBOX)
    взято = 0
    for f in sorted(os.listdir(d) if os.path.isdir(d) else []):
        if not f.endswith(".md"):
            continue
        путь = os.path.join(d, f)
        txt = open(путь, encoding="utf-8").read()
        if "источник: база лаборатории" not in txt:
            continue          # журналы поиска и прочее чужое в _inbox — не наше дело
        m = ПРЕДЛОЖЕНА.search(txt)
        if not m:
            print(f"  {f[:58]:58s} предложенной темы в шапке нет, оставляю")
            continue
        тема = m.group(1)
        ключ = re.search(r"источник: база лаборатории, [^/]+/(\S+)", txt)
        if какие and not (какие in (ключ.group(1) if ключ else "") or какие in f):
            continue
        ax = re.search(r"arxiv\.org/abs/([^\s\")\]]+)", txt)
        новый = _перенести(путь, тема)
        if not новый:
            print(f"  {тема:28s} {f[:52]} — в теме уже есть заметка с таким именем, "
                  f"оставляю в _inbox")
            continue
        _отметить(новый)
        взято += 1
        print(f"  {тема:28s} {f[:52]}")
        for строка in зеркалировать(ax.group(1) if ax else "", тема):
            print(f"    {строка}")
    print(f"принято: {взято}")
    return взято


def дозеркалить():
    """Заметки, перенесённые из _inbox руками: довести до AlphaXiv и Zotero.

    Владелец таскает файлы в Obsidian, а не запускает скрипты, и это правильный порядок.
    Признак «перенесена руками» — строка `источник: база лаборатории` есть, `принято:`
    нет, а лежит заметка уже не в _inbox.
    """
    сделано = 0
    for тема in themes_local():
        d = os.path.join(LIB, тема)
        for f in sorted(os.listdir(d)):
            if not f.endswith(".md") or f == "README.md":
                continue
            путь = os.path.join(d, f)
            txt = open(путь, encoding="utf-8").read(6000)
            if "источник: база лаборатории" not in txt or ПРИНЯТА.search(txt):
                continue
            ax = re.search(r"arxiv\.org/abs/([^\s\")\]]+)", txt)
            print(f"  принято руками: {тема}/{f[:48]}")
            for строка in зеркалировать(ax.group(1) if ax else "", тема):
                print(f"    {строка}")
            _отметить(путь)
            сделано += 1
    return сделано


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="показать, чего нет локально")
    ap.add_argument("--pull", help="ключ цитирования или номер arXiv")
    ap.add_argument("--theme", action="append", help="ограничить темой")
    ap.add_argument("--sync", action="store_true",
                    help="забрать в _inbox всё, чего нет локально, и подмести _trash")
    ap.add_argument("--accept", nargs="?", const="", default=None,
                    help="принять из _inbox в предложенные темы (без имени — всё)")
    ap.add_argument("--into-theme", action="store_true",
                    help="положить сразу в папку темы, а не в _inbox")
    a = ap.parse_args()
    if not os.path.isdir(LIB):
        sys.exit("хранилища нет на этой машине: lab_pull сравнивает базу с локальной библиотекой, "
                 "запускать его надо у владельца")
    if a.accept is not None:
        принять(a.accept)
        дозеркалить()
        return
    tok = token()
    themes = a.theme or (themes_git(token()) if a.sync else themes_local())

    if a.sync:
        for title in sweep_trash():
            print(f"выброшено насовсем: {title}")
        have = local_arxivs() | rejected_arxivs()
        titles = local_titles()
        taken = 0
        for th in themes:
            for p in pages_in_git(th, tok):
                if not p["arxiv"] or p["arxiv"] in have:
                    continue
                # Страница без настоящего номера arXiv: сверяемся по названию,
                # иначе один и тот же разбор приезжает каждый проход.
                if not ARXIV_RE.match(p["arxiv"]):
                    nt = norm_title(p["title"])
                    if nt in titles or any(nt and (nt in x or x in nt) for x in titles):
                        continue
                dst = pull_one(p, tok)
                have.add(p["arxiv"])
                titles.add(norm_title(p["title"]))
                taken += 1
                print(f"  {th:28s} {p['title'][:56]}")
        сделано = дозеркалить()
        if сделано:
            print(f"дозеркалено принятых руками: {сделано}")
        print(f"привезено в _inbox: {taken}")
        if taken:
            print("что не нужно — перетащить в Literature/_trash, "
                  "следующий проход удалит насовсем и больше не принесёт")
        return

    if a.list or not a.pull:
        have = local_arxivs()
        missing = []
        for t in themes:
            for p in pages_in_git(t, tok):
                if p["arxiv"] and p["arxiv"] not in have:
                    missing.append(p)
        print(f"страниц в базе без локальной заметки: {len(missing)}")
        for p in missing:
            print(f"  {p['theme']:30s} {p['key']:28s} {p['title'][:60]}")
        if missing:
            print("\nзабрать: lab_pull.py --pull <ключ>")
        return

    found = None
    for t in themes:
        for p in pages_in_git(t, tok):
            if a.pull in (p["key"], p["arxiv"]):
                found = p
                break
        if found:
            break
    if not found:
        sys.exit(f"{a.pull}: такой страницы в базе нет")

    dst = pull_one(found, tok, into_theme=a.into_theme)
    print(f"записано: {os.path.relpath(dst, VAULT)}")
    if not a.into_theme:
        print("лежит в _inbox: перенести в папку темы решает владелец")


if __name__ == "__main__":
    main()
