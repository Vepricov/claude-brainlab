"""Страница «Показ» на GitHub Pages: тот же атлас и та же вёрстка, другой текст.

Владелец 27-10-2026: «Дизайн оставляй, только сам контент меняй». Поэтому код атласа
копируется как есть из ~/brainlab/ops/demo_day/lab-atlas, а подменяются только тексты: данные
карты, вкладка «Агенты и модели», окно работы (LoRA-TSD вместо dykaf) и точные строки в
index.html и hub.js. Каждая замена обязана найтись ровно один раз: если атлас поменялся,
сборка падает и называет строку.

На 9446 отсюда ничего не пишется: выход только в docs/show этого репозитория.

    python3 scripts/show/build_show.py
"""
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
BANNED = re.compile(r"GitLab|Claude|Харнесс|харнесс|MemPalace|Obsidian|GitHub для идей")


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
        for k in ("toMcp", "spotlight", "pipeline", "gallery"):
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


def index_html() -> str:
    html = (ATLAS / "index.html").read_text(encoding="utf-8")
    html = re.sub(r"\?v=[\w-]+", "", html)
    html = re.sub(r'\n\s*<(?:link rel="stylesheet" href|script src)="(?:assets/katex/[^"]+|search-demo\.(?:css|js)|data/search-demo\.js)">(?:</script>)?', "", html)
    old_intro = re.search(r'<p class="overview-intro">.*?</p>', html).group(0)
    old_chips = re.search(r'<div class="overview-chips">.*?</div>', html).group(0)
    old_show = re.search(r'<a class="show-link"[^>]*>Показ</a>', html).group(0)
    chips = "".join(f'<span style="--c:{c}">{t}</span>' for c, t in C.INDEX["chips"])
    core, (s1, s2, s3), tabs = C.INDEX["core"], C.INDEX["surfaces"], C.INDEX["tabs"]
    return replace_once(html, [
        ("<small>Research system</small>", "<small>Машина знаний</small>"),
        ("<title>BRAIn Lab · Research Loop</title>", "<title>BRAIn Lab · Машина знаний</title>"),
        ("Карта исследовательской работы BRAIn Lab: агенты, база знаний в GitLab, сетап",
         "Машина знаний BRAIn Lab: агенты, база знаний и проверка каждого шага. В науке и в любой компании."),
        (old_intro, f'<p class="overview-intro">{C.INDEX["intro"]}</p>'),
        (old_chips, f'<div class="overview-chips">{chips}</div>'),
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
                                                  "ribbon": P.RIBBON, "cta": P.CTA})
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
