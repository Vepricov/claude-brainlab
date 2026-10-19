"""The public showcase shows one open work and nothing internal."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOWCASE = ROOT / "docs" / "lab-showcase"
INTERNAL = re.compile(r"68-183-24-188|sslip\.io:9445|/root/|@brainlab\.local|phystech\.edu|mbzuai")


def data(path, variable):
    text = (SHOWCASE / path).read_text(encoding="utf-8")
    return json.loads(re.split(rf"window\.{variable}\s*=", text, maxsplit=1)[1].strip().removesuffix(";"))


def test_no_internal_addresses():
    for f in SHOWCASE.rglob("*"):
        if f.is_file() and f.suffix in {".js", ".html", ".json", ".css", ".md"}:
            assert not INTERNAL.search(f.read_text(encoding="utf-8", errors="replace")), f


def test_only_dykaf_is_open():
    for prefix in ("", "en/"):
        hub = data(f"{prefix}data/hub-data.js", "LAB_HUB")
        assert hub["public"] and not hub["gitlab"]
        assert [w["slug"] for w in hub["works"]] == ["dykaf"] and hub["showcase"]["slug"] == "dykaf"
        assert {e["repo"] for e in hub["events"]} <= {"dykaf"}
        assert all(not r.get("url") for rows in (hub["detail"]["claims"], hub["detail"]["runs"]) for r in rows)


def test_no_base_snapshots_shipped():
    for name in ("base-snapshot.js", "library-snapshot.js", "atlas-tree.js", "project-workspaces.js"):
        assert not (SHOWCASE / "data" / name).exists() and not (SHOWCASE / "en" / "data" / name).exists()


def test_english_build_is_current():
    subprocess.run(["node", "scripts/build_showcase_locales.cjs", "--check"], cwd=ROOT, check=True)
