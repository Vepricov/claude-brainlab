"""Public teaching data must remain navigable and separate from real research."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

SHOWCASE = Path(__file__).resolve().parents[1] / "docs" / "lab-showcase"


def snapshot(name, variable):
    text = (SHOWCASE / "data" / name).read_text(encoding="utf-8")
    return json.loads(text.split(f"window.{variable}=", 1)[1].strip().removesuffix(";"))


def test_demo_has_diverse_records_and_resolvable_links():
    base = snapshot("base-snapshot.js", "LAB_BASE")
    assert len(base["records"]) >= 70
    assert {r["k"] for r in base["records"]} == {
        "project", "hypothesis", "experiment", "evidence", "derivation",
        "decision", "journal", "term", "resource", "source",
    }
    ids = {(r["k"], r["id"]) for r in base["records"] if r["id"]}
    assert len(ids) == sum(bool(r["id"]) for r in base["records"])
    for record in base["records"]:
        assert record["pj"] in {"WBD", "DEMO-T"}
        assert record["id"] is None or record["id"].startswith("demo")
        assert record["code"], "Every demo record must open through its public code"
    for relation in base["relations"]:
        assert (relation["a"], relation["ai"]) in ids
        assert (relation["b"], relation["bi"]) in ids
        if relation["r"] == "measures":
            assert (relation["a"], relation["b"]) == ("evidence", "experiment")
        if relation["r"] == "tests":
            assert (relation["a"], relation["b"]) == ("experiment", "hypothesis")
    assert {r["st"] for r in base["records"] if r["k"] == "experiment"} >= {
        "completed", "running", "failed",
    }


def test_preliminary_numbers_do_not_close_the_claim():
    base = snapshot("base-snapshot.js", "LAB_BASE")
    claim = next(r for r in base["records"] if r["code"] == "H-WBD-011")
    assert claim["st"] == "testing"
    assert claim["sup"] == "numbers"
    assert "2 из 3" in str(claim["f"])
    assert "измерений пока нет" not in str(claim["f"])


def test_fictional_papers_have_no_external_citations_or_verified_quotes():
    library = snapshot("library-snapshot.js", "LAB_LIBRARY")
    assert len(library["papers"]) >= 20
    assert sum(len(p["c"]) for p in library["papers"]) >= 50
    assert len({p["id"] for p in library["papers"]}) == len(library["papers"])
    fictional = [p for p in library["papers"] if p["id"].startswith("demo")]
    assert len(fictional) == 20
    for paper in fictional:
        assert not paper["ax"]
        assert paper["nc"] == len(paper["c"])
        assert "Учебная статья" in paper["sr"]
        for claim in paper["c"]:
            assert not claim["q"]
            assert not claim["v"]


def test_public_papers_have_authors_sources_and_honest_reading_scope():
    manifest = json.loads((SHOWCASE / "data/publications.json").read_text())
    library = snapshot("library-snapshot.js", "LAB_LIBRARY")
    papers = [p for p in library["papers"] if p.get("origin") == "author-publication"]
    assert len(papers) >= 19
    assert {p["id"] for p in papers} == {p["id"] for p in manifest["papers"]}
    assert len({p["ax"] for p in papers if p["ax"]}) == 18
    for paper in papers:
        assert "Veprikov" in paper["au"]
        assert paper["source_url"].startswith("https://")
        assert paper["venue_url"].startswith("https://")
        assert paper["reading_scope"]
        assert paper["nc"] == len(paper["c"])
        assert len(paper["c"]) >= 3
        for claim in paper["c"]:
            assert claim["locator"] and claim["source_url"].startswith("https://")
            assert not claim["q"] and not claim["v"]
    flag = snapshot("demo-flag.js", "LAB_DEMO")
    assert flag["hints"] == [q["text"] for q in manifest["questions"]]
    assert flag["publication_count"] == len(papers)


def test_related_papers_and_curated_scenarios_have_public_sources():
    manifest = json.loads((SHOWCASE / "data/publications.json").read_text())
    library = snapshot("library-snapshot.js", "LAB_LIBRARY")
    references = [p for p in library["papers"] if p.get("origin") == "related-publication"]
    assert {p["id"] for p in references} == {p["id"] for p in manifest["references"]}
    assert len(references) >= 8
    for paper in references:
        assert paper["source_url"] == "https://arxiv.org/abs/" + paper["ax"]
        assert paper["au"] and paper["reading_scope"]
        assert paper["f"] == manifest["reference_folder"]
        for claim in paper["c"]:
            assert claim["locator"] and claim["source_url"] == paper["source_url"]
            assert not claim["q"] and not claim["v"]
    flag = snapshot("demo-flag.js", "LAB_DEMO")
    assert flag["scenarios"] == manifest["questions"]
    own = {p["id"] for p in manifest["papers"]}
    all_ids = {p["id"] for p in library["papers"]}
    for scenario in flag["scenarios"]:
        assert scenario["paper"] in own
        assert len(scenario["related"]) >= 2
        assert set(scenario["related"]) <= all_ids - {scenario["paper"]}


def test_publication_build_is_reproducible_and_preserves_teaching_records(tmp_path):
    data = tmp_path / "data"
    shutil.copytree(SHOWCASE / "data", data)
    names = ["library-snapshot.js", "atlas-tree.js", "demo-flag.js", "base-snapshot.js"]
    before = {name: (data / name).read_bytes() for name in names}
    script = SHOWCASE.parents[1] / "scripts/build_publications.py"
    for _ in range(2):
        subprocess.run([sys.executable, str(script), "--data-dir", str(data)], check=True)
        assert {name: (data / name).read_bytes() for name in names} == before


def test_library_tree_places_every_paper_once_in_its_folder():
    library = snapshot("library-snapshot.js", "LAB_LIBRARY")
    tree = snapshot("atlas-tree.js", "LAB_TREE")
    papers = {p["id"]: p for p in library["papers"]}
    placed = []
    for folder in tree["folders"]:
        ids = folder["rest"] + [pid for sub in folder["sub"] for pid in sub["p"]]
        assert len(ids) == len(set(ids))
        assert all(papers[pid]["f"] == folder["f"] for pid in ids)
        placed.extend(ids)
    assert sorted(placed) == sorted(papers)
    section_folders = [f for s in tree["sections"] for f in s["folders"]]
    assert sorted(section_folders) == sorted(f["f"] for f in tree["folders"])


def test_demo_discloses_fictional_content_and_has_no_live_links():
    flag = snapshot("demo-flag.js", "LAB_DEMO")
    assert "вымышлены" in flag["note"]
    for name in ("base-snapshot.js", "library-snapshot.js", "atlas-tree.js", "demo-flag.js"):
        text = (SHOWCASE / "data" / name).read_text(encoding="utf-8")
        assert "Демонстрационные данные" in text
        for private in ("/Users/", "brainlab-stack", "@brainlab-ai", "68-183-24-188", "t.me/+"):
            assert private not in text
