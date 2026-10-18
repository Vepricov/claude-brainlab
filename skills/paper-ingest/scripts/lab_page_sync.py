#!/usr/bin/env python3
"""Полная страница статьи в репозитории литературы темы лаборатории.

Источник — заметка в дереве `~/brainlab/<направление>/<тема>/literature/<Название>.md`.
Скрипт переносит её в GitLab целиком: чинит формулы, кладёт рядом рисунки, на которые
она ссылается, и переводит PDF-рисунки в PNG, иначе GitLab их не покажет. Страница в
репозитории ищется по ключу цитирования из блока BibTeX заметки (или `citation_key`
в шапке); ключа нет — статья пропускается с сообщением. Служба корпуса (`get_paper`,
`labcall.py`) удалена 07-10-2026, и скрипт к ней не обращается.

    lab_page_sync.py --arxiv 2604.18264            одна статья
    lab_page_sync.py --theme zo-estimators         вся тема
    lab_page_sync.py --arxiv 2604.18264 --dry-run  показать, ничего не записывая
"""
import ssl
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from urllib.parse import quote, unquote
import urllib.request, urllib.error
import pathlib

# Корень хранилища знает один модуль, см. `vault_paths`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from vault_paths import VAULT as _VAULT, temy, vse_papki  # noqa: E402

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
    """Корень хранилища. С 16-10-2026 он один и тот же везде: дерево лаборатории.

    Прежде путей было три (iCloud на маке, `/root/shkodnik1917` на do-vpn, домашняя
    копия), и выбирался тот, внутри которого лежала папка `Literature`. Такой папки
    больше нет: разборы лежат в репозитории своей темы, `<направление>/<тема>/literature`.
    """
    return str(_VAULT)


VAULT = os.environ.get("BRAINLAB_VAULT") or _vault()
#: Единой папки разборов нет: темы собирает `vault_paths.temy()`.
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


def gitlab(path, tok):
    url = quote(f"{base()}{path}", safe=":/?=&")
    req = urllib.request.Request(url, headers={"PRIVATE-TOKEN": tok})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=90).read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def fig_roots():
    """Вложения лежат по-разному: у владельца в хранилище, на сервере у конвейера."""
    env = os.environ.get("BRAINLAB_FIG_ROOTS")
    if env:
        return [x for x in env.split(":") if x]
    return [str(p) for p in (*vse_papki(), "/root/paper-agent/state/_attachments")
            if os.path.isdir(p)]


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
    """Вики-вставки `![[...]]` и относительные `![](_attachments/...)` — в файлы клона.

    Относительную вставку, файл которой в клоне уже есть, не трогаем; остальные
    находим среди вложений машины, копируем в клон и, если это PDF, переводим в PNG.
    """
    text = re.sub(r"!\[\[\s*\]\]\s*", "", text)
    def sub(m):
        target = (m.group(1) or unquote(m.group(2))).strip()
        if m.group(2) and not target.lower().endswith(".pdf") and os.path.exists(
                os.path.join(repo_dir, lit_dir(repo_dir), target)):
            stats["рисунков"] += 1
            return m.group(0)
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
    return re.sub(r"!\[\[([^\]]+)\]\]|!\[[^\]]*\]\((_attachments/[^)\s]+)\)", sub, text)


def note_key(text):
    """Ключ цитирования заметки: из блока BibTeX, иначе из `citation_key` в шапке."""
    m = re.search(r"```bibtex\s*@\w+\s*\{\s*([^,\s]+)\s*,", text)
    if m:
        return m.group(1)
    m = re.search(r"(?m)^citation_key:\s*[\"']?([^\"'\s]+)", text)
    return m.group(1) if m else None


def local_notes(theme, arxiv=None):
    """Заметки темы в дереве; с `arxiv` — только те, где стоит этот номер."""
    d = temy().get(theme)
    if not d:
        return []
    out = []
    for f in sorted(d.glob("*.md")):
        if f.name == "README.md":
            continue
        if arxiv:
            try:
                текст = f.read_text(encoding="utf-8")
            except OSError:
                continue
            if not re.search(r"(arxiv\.org/abs/|eprint\s*=\s*\{)" + re.escape(arxiv) + r"\b", текст):
                continue
        out.append(f)
    return out


def page_for(repo, key):
    """Страница клона с тем же ключом цитирования: имя файла — название, а не ключ."""
    root = os.path.join(repo, lit_dir(repo))
    for f in sorted(os.listdir(root)):
        if f.endswith(".md") and f != "README.md":
            with open(os.path.join(root, f), encoding="utf-8") as fh:
                if note_key(fh.read()) == key:
                    return os.path.join(root, f)
    return None


def sync(themes, arxivs, dry, tok):
    global CACHE
    idx = fig_index()
    stats = {"страниц": 0, "рисунков": 0, "pdf->png": 0, "не нашлось": 0}
    work = tempfile.mkdtemp(prefix="labpage-")
    if dry:                                  # сухой прогон не пишет и в кеш рисунков
        CACHE = os.path.join(work, "fig-png")
    try:
        for theme in themes:
            путь = проекты(tok).get(theme)
            if not путь:
                print(f"  {theme}: проекта литературы в базе нет"); continue
            if theme not in temy():
                print(f"  {theme}: темы нет в дереве ~/brainlab/*/*/literature"); continue
            адрес = base().replace("https://", f"https://oauth2:{tok}@")
            url = f"{адрес}/{путь}.git"
            d = os.path.join(work, theme)
            if subprocess.run(["git", "clone", "-q", "--depth", "1", url, d],
                              capture_output=True).returncode:
                print(f"  {theme}: клонировать не удалось"); continue
            subprocess.run(["git", "config", "core.quotepath", "false"], cwd=d)
            changed = 0
            for ax in (arxivs or [None]):
                notes = local_notes(theme, ax)
                if ax and not notes:
                    print(f"  {theme}: в {temy()[theme]} нет заметки с arXiv {ax}"); continue
                for src in notes:
                    txt = src.read_text(encoding="utf-8").rstrip()
                    key = note_key(txt)
                    if not key:
                        print(f"  {theme}: у заметки нет ключа цитирования (ни блока BibTeX, "
                              f"ни citation_key в шапке), пропускаю: {src}"); continue
                    p = page_for(d, key) or os.path.join(d, lit_dir(d), src.name)
                    old = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
                    if txt.endswith(FOOT):
                        txt = txt[:-len(FOOT)].rstrip()
                    while txt.endswith("---"):
                        txt = txt[:-3].rstrip()
                    head_raw = head_of(txt)
                    secs = re.findall(r"(?ms)^## (.+?)\n(.*?)(?=^## |\Z)", txt[len(head_raw):])
                    head = convert_figs(balance_math(tex(head_raw)), d, idx, stats)
                    body = "\n\n".join(
                        f"## {tex(n)}\n\n{convert_figs(balance_math(tex(t)).strip(), d, idx, stats)}"
                        for n, t in secs if t.strip().strip("-").strip())
                    new = f"{head}\n\n{body}\n\n---\n\n{FOOT}\n" if body else f"{head}\n\n---\n\n{FOOT}\n"
                    if old and len(new) < len(old) // 2:
                        print(f"  {theme}: страница {os.path.basename(p)} в базе вдвое полнее "
                              "заметки, не трогаю"); continue
                    if new != old:
                        if not dry:
                            open(p, "w", encoding="utf-8").write(new)
                        changed += 1
                        stats["страниц"] += 1
            if changed and not dry:
                subprocess.run(["git", "add", "-A"], cwd=d)
                subprocess.run(["git", "-c", "user.name=lab-agent",
                                "-c", "user.email=lab-agent@brainlab", "commit", "-q", "-m",
                                "Литература: полный разбор и рисунки из заметки"], cwd=d)
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
        кусок = gitlab(f"/api/v4/projects?simple=true&per_page=100&page={стр}", tok) or []
        for пр in кусок:
            путь = пр.get("path_with_namespace", "")
            части = путь.split("/")
            if len(части) >= 2 and части[-1] == "literature":
                _ПРОЕКТЫ[части[-2]] = путь
        if len(кусок) < 100:
            break
        стр += 1
    return _ПРОЕКТЫ


def theme_of(arxiv):
    """Тема статьи — папка дерева, в `literature/` которой лежит её заметка."""
    for тема in temy():
        if local_notes(тема, arxiv):
            return тема
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arxiv", action="append", help="номер arXiv статьи")
    ap.add_argument("--theme", action="append", help="слаг темы; без него тема ищется по заметке в дереве")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fill-thin", action="store_true",
                    help="пройти все темы и перенести в базу заметки дерева, где страница отстала")
    a = ap.parse_args()
    tok = token()
    themes = a.theme
    if a.fill_thin:
        sync(themes or sorted(temy()), None, a.dry_run, tok)
        return
    if not themes:
        if not a.arxiv:
            sys.exit("нужен --arxiv или --theme")
        themes = []
        for ax in a.arxiv:
            слаг = theme_of(ax)
            if not слаг:
                print(f"  {ax}: заметки с этим номером нет ни в одной ~/brainlab/*/*/literature"); continue
            themes.append(слаг)
        themes = sorted(set(themes))
    sync(themes, a.arxiv, a.dry_run, tok)


if __name__ == "__main__":
    main()
