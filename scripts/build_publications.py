#!/usr/bin/env python3
"""Merge curated public publications into the showcase without reading private data."""
import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit


DATA = Path(__file__).resolve().parents[1] / "docs" / "lab-showcase" / "data"
ORIGIN = "author-publication"
SECTION = "Публикации Андрея"
REFERENCE_ORIGIN = "related-publication"
REFERENCE_SECTION = "Другие исследования"


def read_snapshot(path, variable):
    return json.loads(path.read_text(encoding="utf-8").split(
        f"window.{variable}=", 1)[1].strip().removesuffix(";"))


def write_snapshot(path, variable, data):
    header = "/* Демонстрационные данные: открытые публикации и вымышленный учебный проект. */\n"
    path.write_text(header + f"window.{variable}=" + json.dumps(
        data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")


def validate(manifest):
    topics = {t["slug"] for t in manifest["topics"]}
    ids, sources = set(), set()
    author_ids = {p["id"] for p in manifest["papers"]}
    for paper in manifest["papers"] + manifest["references"]:
        assert paper["id"].startswith(("pub", "ref")) and len(paper["id"]) == 8
        assert paper["id"] not in ids
        assert paper["source_url"] not in sources
        ids.add(paper["id"])
        sources.add(paper["source_url"])
        assert paper["authors"]
        if paper["id"] in author_ids:
            assert any("Veprikov" in author for author in paper["authors"])
        assert paper["topic"] in topics
        assert paper["title"] and paper["summary"] and paper["claims"]
        urls = [paper["source_url"], paper["venue_url"]]
        if paper.get("code_url"):
            urls.append(paper["code_url"])
        for claim in paper["claims"]:
            assert claim["kind"] in {"method", "empirical", "theoretical", "definition"}
            assert claim["text"] and claim["locator"]
            urls.append(claim["source_url"])
        assert all(urlsplit(url).scheme == "https" and urlsplit(url).hostname for url in urls)
    for question in manifest["questions"]:
        assert question["paper"] in author_ids and question["text"]
        assert len(question["related"]) >= 2
        assert len(set(question["related"])) == len(question["related"])
        assert question["paper"] not in question["related"]
        assert all(pid in ids for pid in question["related"])


def build(data_dir=DATA):
    manifest = json.loads((data_dir / "publications.json").read_text(encoding="utf-8"))
    validate(manifest)
    library = read_snapshot(data_dir / "library-snapshot.js", "LAB_LIBRARY")
    tree = read_snapshot(data_dir / "atlas-tree.js", "LAB_TREE")
    demo = read_snapshot(data_dir / "demo-flag.js", "LAB_DEMO")
    existing = [p for p in library["papers"] if p.get("origin") not in {ORIGIN, REFERENCE_ORIGIN}]
    all_papers = manifest["papers"] + manifest["references"]
    author_ids = {p["id"] for p in manifest["papers"]}
    assert not {p["id"] for p in existing} & {p["id"] for p in all_papers}
    papers = []
    for paper in all_papers:
        own = paper["id"] in author_ids
        claims = [dict(k=c["kind"], s=c["text"], q="", v=False,
                       source_url=c["source_url"], locator=c["locator"])
                  for c in paper["claims"]]
        papers.append(dict(
            id=paper["id"], ax=paper["arxiv"], key=None, t=paper["title"],
            au=", ".join(paper["authors"]), y=paper["year"], v=paper["venue"],
            s=paper["summary"], sr=paper["summary"], ab=paper["summary"],
            f=manifest["folder"] if own else manifest["reference_folder"],
            th=None, nc=len(claims), ns=1, nm=0, c=claims,
            origin=ORIGIN if own else REFERENCE_ORIGIN,
            source_url=paper["source_url"], venue_url=paper["venue_url"],
            code_url=paper.get("code_url"),
            reading_scope="; ".join(dict.fromkeys(c["locator"] for c in claims))))
    library["papers"] = papers + existing
    counts = Counter(p["f"] for p in library["papers"])
    library["folders"] = [dict(f=f, n=n) for f, n in counts.items()]
    abstract = "Открытые статьи и препринты Андрея Веприкова и соавторов: методы, результаты и ссылки на оригиналы."
    tree["sections"] = [dict(name=SECTION, abstract=abstract, folders=[manifest["folder"]])] + [
        s for s in tree["sections"] if s["name"] != SECTION]
    tree["folders"] = [dict(f=manifest["folder"], a=abstract, rest=[], sub=[
        dict(slug=t["slug"], t=t["title"], a=t["summary"],
             p=[p["id"] for p in manifest["papers"] if p["topic"] == t["slug"]])
        for t in manifest["topics"]])] + [
        f for f in tree["folders"] if f["f"] != manifest["folder"]]
    reference_abstract = "Публичные статьи по темам демонстрационных вопросов: исходные методы и другие подходы."
    tree["sections"] = [s for s in tree["sections"] if s["name"] != REFERENCE_SECTION] + [
        dict(name=REFERENCE_SECTION, abstract=reference_abstract,
             folders=[manifest["reference_folder"]])]
    tree["folders"] = [f for f in tree["folders"] if f["f"] != manifest["reference_folder"]] + [
        dict(f=manifest["reference_folder"], a=reference_abstract, rest=[], sub=[
            dict(slug=t["slug"], t=t["title"],
                 a=" ".join(p["summary"] for p in manifest["references"] if p["topic"] == t["slug"]),
                 p=[p["id"] for p in manifest["references"] if p["topic"] == t["slug"]])
            for t in manifest["topics"]
            if any(p["topic"] == t["slug"] for p in manifest["references"])])]
    demo.update(
        label="Публикации · BRAIn Lab",
        note="Работы лаборатории и статьи других авторов — настоящие открытые публикации и препринты. "
             "Проект Демо-лаборатории, его прогоны, числа и учебные статьи вымышлены. "
             "Поиск работает в браузере; приватная база лаборатории не подключена.",
        publication_folder=manifest["folder"], publication_count=len(author_ids),
        scenarios=manifest["questions"],
        hints=[q["text"] for q in manifest["questions"]])
    write_snapshot(data_dir / "library-snapshot.js", "LAB_LIBRARY", library)
    write_snapshot(data_dir / "atlas-tree.js", "LAB_TREE", tree)
    write_snapshot(data_dir / "demo-flag.js", "LAB_DEMO", demo)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA)
    build(parser.parse_args().data_dir)
