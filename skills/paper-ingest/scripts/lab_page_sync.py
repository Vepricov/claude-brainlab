#!/usr/bin/env python3
"""Полная страница статьи в репозитории темы лаборатории.

Корпус хранит разборы, но страница `literature/<ключ>.md` печатает из них только
краткое изложение. Этот скрипт дописывает туда разделы и кладёт рядом рисунки,
на которые они ссылаются, переводя PDF-рисунки в PNG: Gitea их иначе не покажет.

    lab_page_sync.py --arxiv 2604.18264            одна статья
    lab_page_sync.py --theme zo-estimators         вся тема
    lab_page_sync.py --arxiv 2604.18264 --dry-run  показать, ничего не записывая
"""
import ssl
import argparse, base64, json, os, re, shlex, shutil, subprocess, sys, tempfile
from urllib.parse import quote
import urllib.request, urllib.error

# pdftoppm ставится из Homebrew и в PATH неинтерактивной оболочки его нет
os.environ["PATH"] = os.environ.get("PATH", "") + ":/opt/homebrew/bin:/usr/local/bin"

#: База переехала с Gitea на GitLab 01-10-2026. У темы теперь свой проект
#: `literature` внутри её группы, страницы лежат в КОРНЕ проекта, а не в
#: подпапке, и авторизация идёт заголовком `PRIVATE-TOKEN`.
URL_FILE = os.path.expanduser("~/.config/brainlab/git-url")
_CTX = ssl.create_default_context()      # сертификат самоподписанный
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
_ПРОЕКТЫ: dict = {}


def base():
    return open(URL_FILE).read().strip().rstrip("/")
TOKEN_FILE = os.path.expanduser("~/.config/brainlab/git-token")
def _vault():
    """Хранилище лежит по-разному: у владельца в iCloud, на сервере копией в корне.

    Зашитый путь под Мак на do-vpn не существует, и всё, что опирается на заметки,
    там молча не работает: 30-09-2026 из-за этого страница статьи не создавалась, а
    сообщение винило корпус.
    """
    for путь in (os.path.expanduser(
                     "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/shkodnik1917"),
                 "/root/shkodnik1917",
                 os.path.expanduser("~/shkodnik1917")):
        if os.path.isdir(os.path.join(путь, "Literature")):
            return путь
    return os.path.expanduser(
        "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/shkodnik1917")


VAULT = os.environ.get("BRAINLAB_VAULT") or _vault()
LIB = os.path.join(VAULT, "Literature")
CACHE = os.path.expanduser("~/.cache/brainlab/fig-png")
def lit_dir(repo):
    """Где внутри репозитория лежат страницы.

    В GitLab у темы отдельный проект `literature`, и страницы лежат в его корне:
    возвращаем пустую строку. Прежние имена (`literature`, `литература` внутри
    репозитория темы) поддерживаем, пока где-то остаются старые клоны.
    """
    for name in ("literature", "литература"):
        if os.path.isdir(os.path.join(repo, name)):
            return name
    return ""


FOOT = "[← вся литература темы](../README.md)"
IMG = (".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp")
MACROS = {r"\vtheta": r"\theta", r"\vx": r"\mathbf{x}", r"\vg": r"\mathbf{g}"}


def token():
    if not os.path.exists(TOKEN_FILE):
        sys.exit("нет токена агента: ~/.config/brainlab/git-token")
    return open(TOKEN_FILE).read().strip()


def gitea(path, tok):
    url = quote(f"{base()}{path}", safe=":/?=&")
    req = urllib.request.Request(url, headers={"PRIVATE-TOKEN": tok})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=90).read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def lab_call(name, args):
    """Корпус доступен с сервера; локально идём тем же путём, что и Гермес."""
    local = "/root/.hermes/scripts/labcall.py"
    payload = json.dumps(args, ensure_ascii=False)
    if os.path.exists(local):                       # мы уже на сервере лаборатории
        cmd = [local, name, payload]
    else:                                           # ssh склеивает аргументы, кавычим сами
        cmd = ["ssh", "do-vpn", " ".join(shlex.quote(x) for x in [local, name, payload])]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def fig_roots():
    """Вложения лежат по-разному: у владельца в хранилище, на сервере у конвейера."""
    env = os.environ.get("BRAINLAB_FIG_ROOTS")
    if env:
        return [x for x in env.split(":") if x]
    return [p for p in (LIB, "/root/paper-agent/state/_attachments") if os.path.isdir(p)]


def fig_index():
    """Все файлы, лежащие где угодно внутри `_attachments`.

    Прежняя проверка брала только один уровень вложенности и пропускала рисунки,
    разложенные автором по подпапкам (`_attachments/<id>/full_timings/x.pdf`). У
    таких статей все вставки превращались в заглушки «рисунок отсутствует»: у
    2608.11612 так потерялись семь рисунков, у 2512.04632 — двадцать пять.

    Ключ — две последние части пути, потому что ровно так рисунок и назван в
    разметке заметки. Дополнительно кладём ключ по одному имени файла: если в
    заметке путь короче, найдём и так.
    """
    idx = {}
    for base in fig_roots():
        for root, _, files in os.walk(base):
            части = os.path.normpath(root).split(os.sep)
            if "_attachments" not in части and os.path.basename(base) != "_attachments":
                continue
            for f in files:
                idx.setdefault(f"{os.path.basename(root)}/{f}", os.path.join(root, f))
                idx.setdefault(f, os.path.join(root, f))
    return idx


def to_png(src, tail):
    os.makedirs(CACHE, exist_ok=True)
    dst = os.path.join(CACHE, tail.replace("/", "_")[:-4] + ".png")
    if not os.path.exists(dst):
        r = subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile", src, dst[:-4]],
                           capture_output=True)
        if r.returncode or not os.path.exists(dst):
            return None
    return dst


# Управляющий символ вместо команды TeX: где-то по дороге \rho прочли как \r + "ho".
# Восстанавливаем по хвосту команды, но только внутри формулы, чтобы не тронуть прозу.
ESCAPED = [("\n", "ho", "\\rho"), ("\r", "ho", "\\rho"),
           ("\n", "u", "\\nu"), ("\t", "heta", "\\theta"),
           ("\t", "au", "\\tau"), ("\t", "imes", "\\times"),
           ("\x0b", "theta", "\\vtheta"), ("\f", "rac", "\\frac")]


def unescape_tex(s):
    for ch, tail, cmd in ESCAPED:
        s = re.sub(r"\$([^$\n]*)" + re.escape(ch) + re.escape(tail) + r"([^$\n]*)\$",
                   lambda m: f"${m.group(1)}{cmd}{m.group(2)}$", s)
    return s


def escape_currency(s):
    """$5090 и $0.306 — деньги, а не формула.

    Экранируем только доллар, который открывает что-то похожее на цену: закрывающий
    доллар формулы трогать нельзя, иначе рвётся `9$\\times$9`. Поэтому идём по строке
    и помним, внутри формулы мы сейчас или нет. Отличаем цену от формулы по тому, что
    стоит до следующего доллара: у формулы это короткий кусок без пробелов либо кусок
    с признаком TeX, у цены — обычные слова. Внутри огороженного кода не трогаем.
    """
    def money(line, i):
        j, n = i + 1, len(line)
        while j < n:
            if line[j] == "$" and line[j - 1] != "\\":
                break
            j += 1
        if j >= n:
            return True                              # закрывать нечем — это цена
        span = line[i + 1:j]
        if any(c in span for c in "\\^_{}=<>+()[]|/"):
            return False                             # оператор или признак TeX — формула
        # У цены между долларами стоят слова; у формулы — однобуквенные переменные.
        return bool(re.search(r"[^\W\d_]{3,}", span))

    out, fenced = [], False
    for line in s.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append(line)
            continue
        if fenced or "$" not in line:
            out.append(line)
            continue
        res, i, in_math, n = [], 0, False, len(line)
        while i < n:
            c = line[i]
            if c != "$" or (i and line[i - 1] == "\\"):
                res.append(c)
                i += 1
                continue
            if line[i:i + 2] == "$$":                # выключенная формула, не деньги
                res.append("$$")
                i += 2
                continue
            if in_math:                              # закрывающий доллар
                res.append("$")
                in_math = False
            elif line[i + 1:i + 2].isdigit() and money(line, i):
                res.append("\\$")
            else:
                res.append("$")
                in_math = True
            i += 1
        out.append("".join(res))
    return "\n".join(out)


#: Знаки, которым математика не нужна: в тексте они и так печатаются.
ГОЛЫЕ_ЗНАКИ = "↑↓→←↔≈±×·∓≤≥≠∞"


def unwrap_trivial_math(s):
    """Снять $...$ со знака, который и без математики печатается.

    `$↓$38.12%` ломает таблицу целиком: закрывающий доллар стоит вплотную к цифре,
    разметка такую пару формулой не считает, ищет следующий доллар — и формула
    уезжает в соседнюю ячейку, съедая строку. Стрелке математика не нужна, поэтому
    просто снимаем обёртку.

    Общий случай «закрывающий доллар вплотную к цифре» регуляркой не чинится:
    отличить настоящую пару от ложной без разбора разметки нельзя, и попытка
    вставлять пробел испортила верное `$4.4$–$6.8\\%$`.
    """
    s = re.sub(r"\$\s*([" + ГОЛЫЕ_ЗНАКИ + r"])\s*\$", r"\1", s)
    # `\\[1.5pt]` — межстрочный отступ LaTeX, при переводе таблицы он утекает
    # в первую ячейку заголовка и читается как мусор.
    return re.sub(r"(?<=\|)\s*\[\d+(?:\.\d+)?pt\]\s*", " ", s)


def tex(s):
    s = unescape_tex(s)
    s = unwrap_trivial_math(s)
    s = escape_currency(s)
    for a, b in MACROS.items():
        s = s.replace(a, b)
    return s


def _bare(s):
    """Доллары, которые видит KaTeX: без экранированных и без строчного кода."""
    masked = re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), s)
    return [m.start() for m in re.finditer(r"(?<!\\)\$", masked)]


def _mathlike(span):
    """Между парой долларов должна стоять формула, а не предложение."""
    if not span or len(span) > 60 or "\n" in span:
        return False
    if re.search(r"[^\W\d_]{4,}", span) and not re.search(r"\\[a-zA-Z]", span):
        return False                                 # длинное слово без команды TeX
    return True


def balance_math(s):
    # Выключенная формула, у которой закрывающий $$ обрезан до одного знака.
    s = re.sub(r"(?m)^(\$\$[^\n$]+[^\n$])\$[ \t]*$", r"\1$$", s)
    pos = _bare(s)
    if len(pos) % 2 == 0:
        return s
    fixed = re.sub(r"\$([^$\n`]{1,60})`", lambda m: f"${m.group(1)}$", s, count=1)
    if len(_bare(fixed)) % 2 == 0:
        return fixed
    # Лишний доллар экранируем, а не выбрасываем: удаление молча теряет текст, а
    # непарный $ заставляет KaTeX съесть всё до следующего. Какой из них лишний,
    # выбираем примеркой: верным считаем тот вариант, где оставшиеся пары — формулы.
    singles = [i for i in pos if s[i:i + 2] != "$$" and (i == 0 or s[i - 1] != "$")]
    best, score = (singles[-1] if singles else pos[-1]), -1
    for cand in singles:
        rest = [i for i in singles if i != cand]
        good = sum(_mathlike(s[a + 1:b]) for a, b in zip(rest[::2], rest[1::2]))
        if good > score:
            best, score = cand, good
    return s[:best] + "\\$" + s[best + 1:]


def head_of(old):
    """Заголовок, метаданные, источник и «Про что работа» — всё до первого другого раздела."""
    lines = old.split("\n")
    start = next((i for i, l in enumerate(lines) if l.strip() == "## Про что работа"), None)
    cut = len(lines)
    for i, l in enumerate(lines):
        if not l.startswith("## ") or (start is not None and i <= start):
            continue
        if start is None and l.strip() == "## Про что работа":
            continue
        cut = i
        break
    head = "\n".join(lines[:cut]).rstrip()
    while head.endswith("---"):
        head = head[:-3].rstrip()
    return head


def convert_figs(text, repo_dir, idx, stats):
    text = re.sub(r"!\[\[\s*\]\]\s*", "", text)
    def sub(m):
        target = m.group(1).strip()
        tail = "/".join(target.split("/")[-2:])
        src = idx.get(tail)
        if not src:
            stats["не нашлось"] += 1
            if not idx:                      # машина без вложений: оставить как есть
                return m.group(0)
            return f"*(рисунок отсутствует: `{os.path.basename(target)}`)*"
        sub_dir, name = tail.split("/", 1)
        if name.lower().endswith(".pdf"):
            png = to_png(src, tail)
            if not png:
                stats["не нашлось"] += 1
                return f"*(рисунок отсутствует: `{name}`)*"
            src, name = png, name[:-4] + ".png"
            stats["pdf->png"] += 1
        dst = os.path.join(repo_dir, lit_dir(repo_dir), "_attachments", sub_dir, name)
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        stats["рисунков"] += 1
        return f"![{name}](_attachments/{sub_dir}/{name})"
    return re.sub(r"!\[\[([^\]]+)\]\]", sub, text)


#: Каркас проверки литературной правки живёт в репозитории службы, а не в скилле:
#: правило там одно на всех и меняется вместе со службой.
CHECKS_PATHS = (
    os.path.expanduser("~/Staff/BRAIn Lab/claude-brainlab/services/lab-knowledge/src"),
    "/srv/jarvis-local/Staff/BRAIn Lab/claude-brainlab/services/lab-knowledge/src",
)


def library_checks():
    """Модуль проверок или None, если репозитория службы на этой машине нет.

    Грузим файлом, а не пакетом: `lab_knowledge/__init__` тянет всю службу, а ей нужен
    Python 3.11, которого на машине может не быть. Модуль кладём в `sys.modules` до
    исполнения — иначе dataclass внутри не находит своего модуля.
    """
    import importlib.util
    for base in CHECKS_PATHS:
        f = os.path.join(base, "lab_knowledge", "library_checks.py")
        if not os.path.exists(f):
            continue
        spec = importlib.util.spec_from_file_location("_library_checks", f)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_library_checks"] = mod
        try:
            spec.loader.exec_module(mod)
            return mod
        except Exception:
            return None
    return None


def check_page(path, text=None):
    """Замечания к странице перед записью. Пустой список — можно писать.

    Проверку зовём ДО записи: отказать дешевле, чем потом искать, кто испортил страницу.
    Если каркас недоступен, молчим — проверка не обязана быть на каждой машине.
    """
    mod = library_checks()
    if mod is None:
        return []
    page = mod.Страница(__import__("pathlib").Path(path),
                        text if text is not None else open(path, encoding="utf-8").read())
    return mod.проверить_страницу(page)


def make_page(paper, theme_name, key):
    """Страницы ещё нет: служба её не выгрузила. Собираем шапку в том же виде, что и она."""
    au = ", ".join(paper.get("authors") or [])
    bits = [f"**авторы** {au}" if au else "",
            f"**год** {paper['year']}" if paper.get("year") else "",
            f"**где** {paper['venue']}" if paper.get("venue") else "",
            f"**ключ цитирования** `{key}`",
            f"**тема** {theme_name}" if theme_name else ""]
    meta = " · ".join(b for b in bits if b)
    head = [f"# {paper.get('title','')}", "", meta, ""]
    if paper.get("url"):
        head += [f"[Открыть источник]({paper['url']})", ""]
    head += ["## Про что работа", "", (paper.get("summary_ru") or "").strip()]
    return "\n".join(head).rstrip()


def page_key(theme, arxiv, tok):
    """Ключ цитирования берём из README темы: там ссылки вида literature/<ключ>.md."""
    путь = проекты(tok).get(theme)
    if not путь:
        return None
    data = gitea(f"/api/v4/projects/{quote(путь, safe='')}/repository/files/README.md?ref=main", tok)
    if not data:
        return None
    txt = base64.b64decode(data["content"]).decode()
    # Ссылки в README теперь без префикса `literature/`: страницы в корне проекта.
    for m in re.finditer(r"\]\((?:literature/)?([^)/]+)\.md\)[^\n]*?\[источник\]\((https?://[^)]+)\)", txt):
        if arxiv and arxiv in m.group(2):
            return m.group(1)
    return None


def sync(themes, arxivs, dry, tok):
    idx = fig_index()
    stats = {"страниц": 0, "рисунков": 0, "pdf->png": 0, "не нашлось": 0}
    work = tempfile.mkdtemp(prefix="labpage-")
    try:
        for theme in themes:
            путь = проекты(tok).get(theme)
            if not путь:
                print(f"  {theme}: проекта литературы в базе нет"); continue
            адрес = base().replace("https://", f"https://oauth2:{tok}@")
            url = f"{адрес}/{путь}.git"
            d = os.path.join(work, theme)
            if subprocess.run(["git", "clone", "-q", "--depth", "1", url, d],
                              capture_output=True).returncode:
                print(f"  {theme}: клонировать не удалось"); continue
            subprocess.run(["git", "config", "core.quotepath", "false"], cwd=d)
            changed = 0
            for ax in (arxivs or [None]):
                key = page_key(theme, ax, tok) if ax else None
                if ax and not key:
                    meta = ((lab_call("get_paper", {"arxiv_id": ax}) or {}).get("paper") or {})
                    key = meta.get("citation_key") or None
                pages = ([key] if key else
                         [f[:-3] for f in os.listdir(os.path.join(d, lit_dir(d)))
                          if f.endswith(".md")] if not ax else [])
                if ax and not key:
                    print(f"  {theme}: ни страницы, ни ключа цитирования для {ax}"); continue
                for k in pages:
                    p = os.path.join(d, lit_dir(d), f"{k}.md")
                    paper = lab_call("get_paper", {"arxiv_id": ax} if ax else {"arxiv_id": k})
                    if not os.path.exists(p):
                        meta = (paper or {}).get("paper") or {}
                        if not meta:
                            print(f"  {theme}: страницы {k} нет и статьи в корпусе тоже"); continue
                        theme_name = ""
                        rd = os.path.join(d, "README.md")
                        if os.path.exists(rd):
                            theme_name = open(rd, encoding="utf-8").readline().lstrip("# ").strip()
                        os.makedirs(os.path.dirname(p), exist_ok=True)
                        open(p, "w", encoding="utf-8").write(make_page(meta, theme_name, k) + "\n")
                        print(f"  {theme}: страница {k} создана")
                    secs = [(c.get("section"), c.get("content") or "")
                            for c in ((paper or {}).get("chunks") or [])]
                    if not secs:
                        continue
                    old = open(p, encoding="utf-8").read()
                    head = convert_figs(balance_math(tex(head_of(old))), d, idx, stats)
                    body = "\n\n".join(
                        f"## {tex(n)}\n\n{convert_figs(balance_math(tex(t)).strip(), d, idx, stats)}"
                        for n, t in secs if t.strip())
                    new = f"{head}\n\n{body}\n\n---\n\n{FOOT}\n"
                    if new != old:
                        if not dry:
                            open(p, "w", encoding="utf-8").write(new)
                        changed += 1
                        stats["страниц"] += 1
            if changed and not dry:
                subprocess.run(["git", "add", "-A"], cwd=d)
                subprocess.run(["git", "-c", "user.name=lab-agent",
                                "-c", "user.email=lab-agent@brainlab", "commit", "-q", "-m",
                                "Литература: полный разбор и рисунки из корпуса"], cwd=d)
                r = subprocess.run(["git", "push", "-q", "origin", "HEAD"], cwd=d, capture_output=True)
                if not r.returncode:
                    print(f"  {theme}: страниц {changed}, залито")
                else:
                    # Какие файлы отвергнуты, по сообщению не видно, а защита ветки
                    # разрешает только literature/** и README. Печатаем список сами.
                    файлы = subprocess.run(["git", "show", "--pretty=", "--name-only", "HEAD"],
                                           cwd=d, capture_output=True, text=True).stdout.split()
                    чужие = [x for x in файлы
                             if not x.startswith("literature/") and x != "README.md"]
                    print(f"  {theme}: страниц {changed}, ПУШ НЕ УДАЛСЯ: "
                          + r.stderr.decode()[:120].replace(chr(10), " "))
                    print(f"      в коммите файлов {len(файлы)}, вне literature/ и README: "
                          + (", ".join(чужие[:5]) if чужие else "нет"))
            else:
                print(f"  {theme}: страниц {changed}" + (" (сухой прогон)" if dry else ", изменений нет"))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print(stats)


def проекты(tok):
    """Слаг темы -> полный путь её проекта литературы в GitLab."""
    if _ПРОЕКТЫ:
        return _ПРОЕКТЫ
    стр = 1
    while True:
        кусок = gitea(f"/api/v4/projects?simple=true&per_page=100&page={стр}", tok) or []
        for пр in кусок:
            путь = пр.get("path_with_namespace", "")
            части = путь.split("/")
            if len(части) >= 2 and части[-1] == "literature":
                _ПРОЕКТЫ[части[-2]] = путь
        if len(кусок) < 100:
            break
        стр += 1
    return _ПРОЕКТЫ


def repo_names(tok):
    """Слаги тем, как они называются в базе."""
    return set(проекты(tok))


def theme_slug(arxiv, поле, tok):
    """Слаг репозитория темы для статьи.

    Полю `library_folder` из корпуса верить нельзя: там встречается и слаг
    (`training-dynamics`), и человекочитаемое имя темы («Динамика обучения»), и
    прежний путь таксономии. По имени репозиторий не находится, и статья молча
    остаётся без страницы. Поэтому проверяем по списку репозиториев, а если не
    сошлось — смотрим, в какой папке хранилища заметка лежит на самом деле.
    """
    известные = repo_names(tok)
    if поле in известные:
        return поле
    if os.path.isdir(LIB):
        for тема in sorted(os.listdir(LIB)):
            d = os.path.join(LIB, тема)
            if not os.path.isdir(d) or тема not in известные:
                continue
            for f in os.listdir(d):
                if not f.endswith(".md") or f == "README.md":
                    continue
                try:
                    текст = open(os.path.join(d, f), encoding="utf-8").read(4000)
                except OSError:
                    continue
                if re.search(r"arxiv\.org/abs/" + re.escape(arxiv) + r"\b", текст):
                    return тема
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arxiv", action="append", help="номер arXiv статьи")
    ap.add_argument("--theme", action="append", help="слаг темы; без него тема ищется по статье")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fill-thin", action="store_true",
                    help="пройти все темы и дополнить страницы, где напечатано только краткое изложение")
    a = ap.parse_args()
    tok = token()
    themes = a.theme
    if a.fill_thin:
        sync(themes or [x for x in os.listdir(LIB)
                        if os.path.isdir(os.path.join(LIB, x)) and not x.startswith(("_", "."))],
             None, a.dry_run, tok)
        return
    if not themes:
        if not a.arxiv:
            sys.exit("нужен --arxiv или --theme")
        themes = []
        for ax in a.arxiv:
            paper = lab_call("get_paper", {"arxiv_id": ax})
            поле = ((paper or {}).get("paper") or {}).get("library_folder")
            if not поле:
                print(f"  {ax}: в корпусе не нашёлся"); continue
            слаг = theme_slug(ax, поле, tok)
            if not слаг:
                print(f"  {ax}: тема «{поле}» не отвечает ни одному репозиторию, "
                      "и заметки в хранилище нет"); continue
            themes.append(слаг)
        themes = sorted(set(themes))
    sync(themes, a.arxiv, a.dry_run, tok)


if __name__ == "__main__":
    main()
