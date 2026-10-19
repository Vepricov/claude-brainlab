#!/usr/bin/env python3
"""Привести заметку статьи в вид, который GitLab показывает правильно. Правит файл на месте.

Заметка лежит в клоне литературы темы: `~/brainlab/<направление>/<тема>/literature/<Название>.md`.
Скрипт чинит формулы, копирует рядом в `_attachments/` рисунки, на которые она ссылается, и
переводит PDF-рисунки в PNG, иначе GitLab их не покажет. Больше он ничего не делает: отправка
это обычный git в том же клоне, `git add`, `git commit`, `git push`.

    fix_page.py --arxiv 2604.18264            одна статья
    fix_page.py --theme zo-estimators         вся тема
    fix_page.py --arxiv 2604.18264 --dry-run  показать, ничего не записывая

До 19-10-2026 здесь был `lab_page_sync.py`: он клонировал тему во временную папку и сам пушил
туда исправленную страницу. В дереве это лишнее и вредно: заметка уже лежит в том самом клоне,
а пуш мимо него оставлял локальный файл позади своей же страницы в GitLab.
"""
import argparse, os, re, shutil, subprocess, sys, tempfile
from urllib.parse import unquote
import pathlib

# Корень хранилища знает один модуль, см. `vault_paths`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from vault_paths import temy, vse_papki  # noqa: E402

# pdftoppm ставится из Homebrew и в PATH неинтерактивной оболочки его нет
os.environ["PATH"] = os.environ.get("PATH", "") + ":/opt/homebrew/bin:/usr/local/bin"

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


def fix(themes, arxivs, dry):
    """Каждую заметку — на место: формулы, рисунки рядом, подпись внизу. Без git."""
    global CACHE
    idx = fig_index()
    stats = {"страниц": 0, "рисунков": 0, "pdf->png": 0, "не нашлось": 0}
    if dry:                                  # сухой прогон не пишет и в кеш рисунков
        CACHE = os.path.join(tempfile.mkdtemp(prefix="fixpage-"), "fig-png")
    for theme in themes:
        d = str(temy()[theme])
        changed = 0
        for ax in (arxivs or [None]):
            notes = local_notes(theme, ax)
            if ax and not notes:
                print(f"  {theme}: в {d} нет заметки с arXiv {ax}"); continue
            for src in notes:
                old = src.read_text(encoding="utf-8")
                txt = old.rstrip()
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
                if new != old:
                    if not dry:
                        src.write_text(new, encoding="utf-8")
                    changed += 1
                    stats["страниц"] += 1
        print(f"  {theme}: исправлено страниц {changed}" + (" (сухой прогон)" if dry else ""))
    print(stats)
    if stats["страниц"] and not dry:
        print("дальше обычный git в клоне литературы: git add -A && git commit && git push")


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
    a = ap.parse_args()
    themes = a.theme
    if themes:
        for слаг in themes:
            if слаг not in temy():
                sys.exit(f"темы {слаг} нет в дереве ~/brainlab/*/*/literature")
    elif a.arxiv:
        themes = []
        for ax in a.arxiv:
            слаг = theme_of(ax)
            if not слаг:
                print(f"  {ax}: заметки с этим номером нет ни в одной ~/brainlab/*/*/literature"); continue
            themes.append(слаг)
        themes = sorted(set(themes))
    else:
        sys.exit("нужен --arxiv или --theme")
    fix(themes, a.arxiv, a.dry_run)


if __name__ == "__main__":
    main()
