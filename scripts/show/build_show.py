"""Страница «Показ» на GitHub Pages: тот же атлас и та же вёрстка, другой текст.

Владелец 27-10-2026: «Дизайн оставляй, только сам контент меняй». Поэтому код атласа
копируется как есть из ~/brainlab/ops/demo_day/lab-atlas, а подменяются только тексты: данные
карты, вкладка «Агенты и модели», окно работы (LoRA-TSD вместо dykaf) и точные строки в
index.html и hub.js. Каждая замена обязана найтись ровно один раз: если атлас поменялся,
сборка падает и называет строку.

На 9446 отсюда ничего не пишется: выход только в docs/show этого репозитория.

    python3 scripts/show/build_show.py
"""
import colorsys
import json
import pathlib
import re
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
ATLAS = pathlib.Path.home() / "brainlab/ops/demo_day/lab-atlas"
TREE = pathlib.Path.home() / "brainlab"
LORA = "low-rank/low-rank-step-geometry/lora-muon"
OUT = REPO / "docs/show"
sys.path[:0] = [str(HERE), str(ATLAS / "scripts")]

import show_content as C  # noqa: E402
import show_pages as P  # noqa: E402
import export_tree_hub as hub  # noqa: E402

CODE = ["app.js", "search-core.js", "app.css", "refinements.css", "map-shapes.css", "mcp-design.css",
        "front-design.css", "memory-map.css", "memory-map.js", "obsidian-setup.css", "obsidian-setup.js",
        "surface-pages.css", "surface-pages.js", "search-workspace.css", "setup.css", "setup.js",
        "hub.css", "fixes.css", "data/atlas-public.js", "data/system-examples.js"]
INTERNAL = re.compile(r"68-183-24-188|sslip\.io|/root/|@brainlab\.local|phystech\.edu|mbzuai")
# Слова, которых на видимых страницах «Показа» быть не должно (владелец: «убрать англицизмы»).
BANNED = re.compile(r"GitLab|Claude|Харнесс|харнесс|MemPalace|Obsidian|GitHub для идей|Гермес")


def load(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return json.loads(text[text.index("=") + 1:].strip().rstrip(";"))


def dump(path: pathlib.Path, var: str, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"window.{var}=" + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")


def replace_once(text: str, pairs: list, where: str) -> str:
    for old, new in pairs:
        n = text.count(old)
        if n != 1:
            sys.exit(f"{where}: строка найдена {n} раз, ожидался 1:\n  {old[:120]}")
        text = text.replace(old, new)
    return text


def loop_data() -> dict:
    """Карта: те же этапы, цвета и номера; текст общий, без инструментов."""
    data = load(ATLAS / "data/research-loop-data.js")
    for p in data["processes"]:
        c = C.PROCESSES[p["id"]]
        p.update({k: c[k] for k in ("title", "verb", "result", "purpose", "when", "outcomes")})
        p["stages"] = [{"title": t, "summary": s, "result": r, "ref": f"s{i + 1}"} for i, (t, s, r) in enumerate(c["stages"])]
        p["destinations"] = [{"name": n, "what": w, "why": y, "ref": f"d{i + 1}"} for i, (n, w, y) in enumerate(c["destinations"])]
        p["outcomeRefs"] = [{"ref": f"o{i + 1}", "label": o} for i, o in enumerate(c["outcomes"])]
        p["example"] = c["how"][1]
        for k in ("tools", "toolClusters", "mapRelations", "controls", "mapFeatured"):
            p[k] = []
        for k in ("toMcp", "spotlight", "pipeline", "gallery", "implementation"):
            p.pop(k, None)
    data["shared"].update(C.SHARED)
    data["meta"].pop("toolkit", None)
    return data


def hub_data() -> dict:
    """Окно работы и цепочка «прогон → статья» на LoRA-TSD; без адресов GitLab."""
    data = load(ATLAS / "data/hub-data.js")
    hub.WINDOW = LORA
    detail = hub.showcase_detail(TREE)
    strip = lambda rows: [{k: ("" if k == "url" else v) for k, v in r.items()} for r in rows]
    for k in ("claims", "runs", "issues", "mrs"):
        detail[k] = strip(detail[k])
    claim = TREE / LORA / "claims/H-LMU-005"
    count = lambda d: len(list((claim / d).glob("*.md")))
    shutil.copyfile(claim / "figures/F-LMU-001.svg", OUT / "assets/showcase/F-LMU-001.svg")
    detail["chain"] = {"claim": hub.page(claim / "README.md")["title"], "runs": count("runs"), "series": count("series"),
                       "theory": count("theory"), "figure": "assets/showcase/F-LMU-001.svg", "urls": {}}
    work = next(w for w in data["works"] if w["path"] == LORA)
    work = {**work, "url": "", "last": None, "title": "LoRA-TSD: правильное обучение LoRA-адаптеров",
            "lead": "Риманова оптимизация на многообразии матриц низкого ранга: спектральный шаг в касательном пространстве повышает качество дообучения"}
    events = []
    for row in hub.git(TREE / LORA, "log", "origin/main", "-30", "--format=%H%x09%ct%x09%an%x09%ae%x09%s").splitlines():
        sha, ct, an, ae, s = row.split("\t", 4)
        name, agent = hub.human(an, ae)
        name = "Агент" if agent else name
        if s.startswith("Merge"):
            continue
        events.append({"t": int(ct), "repo": "lora-muon", "url": "", "who": name, "agent": agent, "merge": False, "s": s[:140]})
    return {"public": True, "gitlab": "", "cta": None, "showcase": work, "detail": detail,
            "totals": data["totals"], "works": [work], "events": events[:10]}


# Цвета МФТИ: синий, голубой, белый. Владелец 27-10-2026: «делаем в цветах МФТИ». Вёрстка
# атласа не трогается: каждый цвет в собранных файлах переводится в синюю гамму. Насыщенные
# оттенки сохраняют порядок (у этапов остаются разные цвета), серые и бежевые становятся
# холодными, тёмные — тёмно-синими.
COLOR = re.compile(r"(?<=[:,(\s\"'=])(#|%23)([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![\w-])|rgba?\((\d+),\s*(\d+),\s*(\d+)")


def to_mipt(r: int, g: int, b: int) -> tuple:
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if s < 0.3 or l > 0.97 or l < 0.02:
        h, s = 215 / 360, (0.38 if l < 0.2 else min(0.3, s + 0.1)) if 0.02 <= l <= 0.97 else s
    else:
        h = (185 + h * 60) / 360
    return tuple(round(c * 255) for c in colorsys.hls_to_rgb(h, l, s))


def recolor(text: str) -> str:
    def sub(m: re.Match) -> str:
        if m.group(3):
            r, g, b = to_mipt(*(int(m.group(i)) for i in (3, 4, 5)))
            return m.group(0).split("(")[0] + f"({r},{g},{b}"
        x = m.group(2)
        x = "".join(c * 2 for c in x) if len(x) == 3 else x
        return m.group(1) + "%02x%02x%02x" % to_mipt(int(x[:2], 16), int(x[2:4], 16), int(x[4:], 16))
    return COLOR.sub(sub, text)


ICONS = {
    "model": '<circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M4.9 19.1l2.8-2.8M16.3 7.7l2.8-2.8"/>',
    "tune": '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    "lock": '<rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8.5 10.5V7.5a3.5 3.5 0 0 1 7 0v3"/><circle cx="12" cy="15.5" r="1.3"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
}


def points_html() -> str:
    """Под заголовком главного экрана: четыре главных обещания (вместо прежних плашек)."""
    cards = "".join(f'<li><svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[i]}</svg><p><b>{k}</b><span>{t}</span></p></li>'
                    for i, k, t in C.POINTS["items"])
    return f'<ul class="show-pts" aria-label="{C.POINTS["title"]}">{cards}</ul>'


def index_html() -> str:
    html = (ATLAS / "index.html").read_text(encoding="utf-8")
    html = re.sub(r"\?v=[\w-]+", "", html)
    html = re.sub(r'\n\s*<(?:link rel="stylesheet" href|script src)="(?:assets/katex/[^"]+|search-demo\.(?:css|js)|data/search-demo\.js)">(?:</script>)?', "", html)
    old_intro = re.search(r'<p class="overview-intro">.*?</p>', html).group(0)
    old_chips = re.search(r'<div class="overview-chips">.*?</div>', html).group(0)
    old_show = re.search(r'<a class="show-link"[^>]*>Показ</a>', html).group(0)
    core, (s1, s2, s3), tabs = C.INDEX["core"], C.INDEX["surfaces"], C.INDEX["tabs"]
    return replace_once(html, [
        ('<span class="brand-sign"><i></i><i></i></span><span><b>BRAIn Lab</b><small>Research system</small></span>',
         '<span class="show-logos"><img class="lg-brain" src="assets/logos/brainlab.svg" alt="BRAIn Lab">'
         '<img class="lg-iii" src="assets/logos/iii-white.png" alt="Институт искусственного интеллекта МФТИ">'
         '<img class="lg-mipt" src="assets/logos/mipt.png" alt="МФТИ"></span>'),
        ("<title>BRAIn Lab · Research Loop</title>", f"<title>{C.INDEX['title']}</title>"),
        ('<p class="overline">Исследовательская система · <span id="verified-date"></span></p>', f'<p class="overline">{C.INDEX["overline"]}<span id="verified-date" hidden></span></p>'),
        ("<h1>Вопрос входит —<br> <span>знание</span> выходит</h1>", f"<h1>{C.INDEX['h1']}</h1>"),
        ('data-view="loop" type="button">Машина знаний</button>', f'data-view="loop" type="button">{tabs[0]}</button>'),
        ("Карта исследовательской работы BRAIn Lab: агенты, база знаний в GitLab, сетап",
         "Машина знаний BRAIn Lab: агенты, база знаний и проверка каждого шага. В науке и в любой компании."),
        (old_intro, f'<div class="overview-intro show-intro"><p>{C.INDEX["intro"]}</p>'
                    f'<a class="show-qr" href="{C.QR[0]}" target="_blank" rel="noopener"><img src="assets/qr-github.svg" alt="QR-код: {C.QR[1]}">'
                    f'<span><b>{C.QR[1]}</b>{C.QR[2]}</span></a></div>'),
        ('<a class="show-link"', '<button class="show-theme" id="show-theme" type="button" aria-pressed="false">Светлая тема</button><a class="show-link"'),
        (old_chips, points_html()),
        (old_show, '<a class="show-link" href="../lab-showcase/ru/index.html">Подробная карта</a>'),
        ('>GitHub для идей</button>', f'>{tabs[1]}</button>'),
        ('>Харнесс агентов</button>', f'>{tabs[2]}</button>'),
        ("<strong>GitLab</strong><p>база знаний лаборатории: утверждения · прогоны · литература · предложения</p><i>Открыть базу →</i>",
         f"<strong>{core[0]}</strong><p>{core[1]}</p><i>{core[2]}</i>"),
        ("<span>Сердце системы</span>", ""),
        ("<b>Obsidian</b><span>всё дерево в одном окне</span>", f"<b>{s1[0]}</b><span>{s1[1]}</span>"),
        ("<b>MemPalace</b><span>память агента</span>", f"<b>{s2[0]}</b><span>{s2[1]}</span>"),
        ("<b>Гермес</b><span>агент на сервере 24/7</span>", f"<b>{s3[0]}</b><span>{s3[1]}</span>"),
        ('<link rel="stylesheet" href="fixes.css">', '<link rel="stylesheet" href="fixes.css">\n  <link rel="stylesheet" href="show.css">'),
        ('  <script src="app.js"></script>', '  <script src="data/show-data.js"></script>\n  <script src="app.js"></script>\n  <script src="show.js"></script>'),
    ], "index.html")


def main() -> None:
    shutil.rmtree(OUT, ignore_errors=True)
    for f in CODE:
        (OUT / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ATLAS / f, OUT / f)
    shutil.copytree(ATLAS / "assets", OUT / "assets", ignore=shutil.ignore_patterns("katex", "F-DYC-*"))
    for f in ("show.css", "show.js"):
        shutil.copyfile(HERE / f, OUT / f)
    shutil.copyfile(HERE / "qr-github.svg", OUT / "assets/qr-github.svg")
    (OUT / "assets/logos").mkdir(parents=True, exist_ok=True)
    for f in ("iii-white.png", "mipt.png", "brainlab.svg"):
        shutil.copyfile(ATLAS.parent / "optimizer-demo/logos" / f, OUT / "assets/logos" / f)

    counts = load(ATLAS / "data/counts.js")
    counts.pop("last", None)
    dump(OUT / "data/counts.js", "LAB_COUNTS", counts)
    loop = loop_data()
    dump(OUT / "data/research-loop-data.js", "RESEARCH_LOOP", loop)
    reg = (OUT / "data/atlas-public.js").read_text(encoding="utf-8")
    (OUT / "data/atlas-public.js").write_text(reg.replace("Сертификат выписан на sslip.io и настоящий, но хук не имеет права падать из-за",
                                                          "Говорит агенту, в какой репозиторий базы писать отсюда и как отправлять"), encoding="utf-8")
    dump(OUT / "data/setup-data.js", "LAB_SETUP", P.SETUP)
    dump(OUT / "data/hub-data.js", "LAB_HUB", hub_data())
    dump(OUT / "data/show-data.js", "LAB_SHOW", {"stage": C.STAGE,
                                                  "ribbon": P.RIBBON, "cta": P.CTA, "setupIds": [s["id"] for s in P.SETUP["sections"]]})
    hub_js = (ATLAS / "hub.js").read_text(encoding="utf-8")
    cta = re.search(r'<section class="hub-cta"><h2>Посмотрите сами</h2><p>.*?</p>', hub_js).group(0)
    hub_js = replace_once(hub_js, P.HUB + [(cta, f'<section class="hub-cta"><h2>{P.CTA[0]}</h2><p>{P.CTA[1]}</p>')], "hub.js")
    (OUT / "hub.js").write_text(hub_js, encoding="utf-8")
    setup_js = replace_once((ATLAS / "setup.js").read_text(encoding="utf-8"), [
        ('<p class="overline">Хуки</p>', '<p class="overline">Модели</p>'),
        ("Сетап агента · сверено", "Агенты и модели · сверено"),
        ('aria-label="Разделы сетапа"', 'aria-label="Разделы"'),
    ], "setup.js")
    (OUT / "setup.js").write_text(setup_js, encoding="utf-8")
    (OUT / "index.html").write_text(index_html(), encoding="utf-8")

    for f in OUT.rglob("*"):
        if f.is_file() and f.suffix in (".js", ".html", ".css"):
            f.write_text(recolor(f.read_text(encoding="utf-8")), encoding="utf-8")

    bad = []
    for f in OUT.rglob("*"):
        if f.is_file() and f.suffix in (".js", ".html", ".json", ".css"):
            text = f.read_text(encoding="utf-8", errors="replace")
            bad += [f"{f.relative_to(OUT)}: {m.group(0)}" for m in INTERNAL.finditer(text)]
            if f.name in ("index.html", "setup-data.js", "show-data.js"):
                bad += [f"{f.relative_to(OUT)}: слово «{m.group(0)}»" for m in BANNED.finditer(text)]
    visible = json.dumps([loop["processes"], {k: loop["shared"][k] for k in C.SHARED}], ensure_ascii=False)
    bad += [f"карта: слово «{m.group(0)}»" for m in BANNED.finditer(visible)]
    if bad:
        sys.exit("в сборке «Показа» нашлось лишнее:\n" + "\n".join(sorted(set(bad))[:40]))
    print("собрано в", OUT)


if __name__ == "__main__":
    main()
