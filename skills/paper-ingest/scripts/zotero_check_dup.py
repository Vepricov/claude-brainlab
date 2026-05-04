#!/usr/bin/env python3
"""
Check paper duplicates before import, and audit Zotero/Obsidian consistency after import.

Modes:
1. Pre-import duplicate check:
   python3 zotero_check_dup.py --arxiv 1901.06053
   python3 zotero_check_dup.py --title "A Tail-Index Analysis"
   python3 zotero_check_dup.py --doi 10.1073/pnas.2015617118

2. Final collection audit:
   python3 zotero_check_dup.py --collection scale_inv --final-audit
   python3 zotero_check_dup.py --collection scale_inv --final-audit \
       --expect-title "Paper Title" --expect-zotero-key ABCD1234
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path


ZOTERO_API_BASE = "http://localhost:23119/api/users/0"
VAULT_LITERATURE = Path(
    "${OBSIDIAN_VAULT}/Literature"
)
DB_PATH = Path("~/Zotero/zotero.sqlite").expanduser()


def safe_json_loads(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


def api_get(url: str):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (paper-ingest)")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return safe_json_loads(resp.read())


def sqlite_copy_path() -> Path | None:
    if not DB_PATH.exists():
        return None
    fd, tmp_name = tempfile.mkstemp(prefix="zotero_check_", suffix=".sqlite")
    os.close(fd)
    tmp_db = Path(tmp_name)
    try:
        shutil.copy2(DB_PATH, tmp_db)
    except Exception:
        try:
            tmp_db.unlink()
        except Exception:
            pass
        return None
    return tmp_db


def title_slug(title: str) -> str:
    value = title.lower().strip()
    value = re.sub(r"\s+", " ", value)
    return value


def check_via_api(title=None, arxiv_id=None, doi=None):
    results = []

    if title:
        url = f"{ZOTERO_API_BASE}/items?q={urllib.parse.quote(title)}&format=json&limit=20"
        items = api_get(url)
        for item in items:
            data = item.get("data", {})
            if data.get("itemType") in ("attachment", "note"):
                continue
            results.append({
                "key": item.get("key"),
                "title": data.get("title", ""),
                "itemType": data.get("itemType", ""),
                "collections": data.get("collections", []),
                "deleted": data.get("deleted", False),
                "url": data.get("url", ""),
                "doi": data.get("DOI", ""),
            })

    if arxiv_id:
        url = f"{ZOTERO_API_BASE}/items?q={urllib.parse.quote(arxiv_id)}&format=json&limit=20"
        items = api_get(url)
        for item in items:
            data = item.get("data", {})
            if data.get("itemType") in ("attachment", "note"):
                continue
            item_url = data.get("url", "")
            extra = str(data.get("extra", ""))
            if arxiv_id in item_url or arxiv_id in extra:
                results.append({
                    "key": item.get("key"),
                    "title": data.get("title", ""),
                    "itemType": data.get("itemType", ""),
                    "collections": data.get("collections", []),
                    "deleted": data.get("deleted", False),
                    "url": item_url,
                    "doi": data.get("DOI", ""),
                })

    if doi:
        url = f"{ZOTERO_API_BASE}/items?q={urllib.parse.quote(doi)}&format=json&limit=20"
        items = api_get(url)
        for item in items:
            data = item.get("data", {})
            if data.get("itemType") in ("attachment", "note"):
                continue
            if doi.lower() in str(data.get("DOI", "")).lower() or doi.lower() in str(data.get("url", "")).lower():
                results.append({
                    "key": item.get("key"),
                    "title": data.get("title", ""),
                    "itemType": data.get("itemType", ""),
                    "collections": data.get("collections", []),
                    "deleted": data.get("deleted", False),
                    "url": data.get("url", ""),
                    "doi": data.get("DOI", ""),
                })

    dedup = {}
    for row in results:
        dedup[row["key"]] = row
    return list(dedup.values())


def check_via_sqlite(title=None, arxiv_id=None, doi=None):
    tmp_db = sqlite_copy_path()
    if not tmp_db:
        return None

    conn = sqlite3.connect(tmp_db)
    cur = conn.cursor()
    results = []

    def append_rows(query, params):
        cur.execute(query, params)
        for row in cur.fetchall():
            results.append({
                "key": row[0],
                "title": row[1] or "",
                "collections": row[2].split(", ") if row[2] else [],
                "deleted": bool(row[3]),
            })

    if title:
        append_rows(
            """
            SELECT i.key, idv.value, GROUP_CONCAT(c2.collectionName, ', '),
                   EXISTS(SELECT 1 FROM deletedItems di WHERE di.itemID=i.itemID)
            FROM items i
            JOIN itemData id ON i.itemID = id.itemID
            JOIN itemDataValues idv ON id.valueID = idv.valueID
            JOIN fields f ON id.fieldID = f.fieldID AND f.fieldName = 'title'
            LEFT JOIN collectionItems ci ON i.itemID = ci.itemID
            LEFT JOIN collections c2 ON ci.collectionID = c2.collectionID
            WHERE idv.value LIKE ?
            GROUP BY i.key
            """,
            (f"%{title[:120]}%",),
        )

    if arxiv_id:
        append_rows(
            """
            SELECT i.key, MAX(idv.value), GROUP_CONCAT(DISTINCT c2.collectionName),
                   EXISTS(SELECT 1 FROM deletedItems di WHERE di.itemID=i.itemID)
            FROM items i
            JOIN itemData id ON i.itemID = id.itemID
            JOIN itemDataValues idv ON id.valueID = idv.valueID
            JOIN fields f ON id.fieldID = f.fieldID
            LEFT JOIN collectionItems ci ON i.itemID = ci.itemID
            LEFT JOIN collections c2 ON ci.collectionID = c2.collectionID
            WHERE (f.fieldName = 'url' AND idv.value LIKE ?)
               OR (f.fieldName = 'extra' AND idv.value LIKE ?)
            GROUP BY i.key
            """,
            (f"%{arxiv_id}%", f"%{arxiv_id}%"),
        )

    if doi:
        append_rows(
            """
            SELECT i.key, MAX(idv.value), GROUP_CONCAT(DISTINCT c2.collectionName),
                   EXISTS(SELECT 1 FROM deletedItems di WHERE di.itemID=i.itemID)
            FROM items i
            JOIN itemData id ON i.itemID = id.itemID
            JOIN itemDataValues idv ON id.valueID = idv.valueID
            JOIN fields f ON id.fieldID = f.fieldID
            LEFT JOIN collectionItems ci ON i.itemID = ci.itemID
            LEFT JOIN collections c2 ON ci.collectionID = c2.collectionID
            WHERE (f.fieldName = 'DOI' AND LOWER(idv.value) LIKE LOWER(?))
               OR (f.fieldName = 'url' AND LOWER(idv.value) LIKE LOWER(?))
            GROUP BY i.key
            """,
            (f"%{doi}%", f"%{doi}%"),
        )

    conn.close()
    try:
        tmp_db.unlink()
    except Exception:
        pass

    dedup = {}
    for row in results:
        dedup[row["key"]] = row
    return list(dedup.values())


def obsidian_matches(title=None, arxiv_id=None, doi=None):
    matches = []
    if not VAULT_LITERATURE.exists():
        return matches

    for path in VAULT_LITERATURE.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        frontmatter_title = re.search(r'^title:\s*"(.+?)"\s*$', text, re.MULTILINE)
        note_title = frontmatter_title.group(1) if frontmatter_title else path.stem
        if title and title_slug(title) == title_slug(note_title):
            matches.append(str(path))
            continue
        if arxiv_id and arxiv_id in text:
            matches.append(str(path))
            continue
        if doi and doi.lower() in text.lower():
            matches.append(str(path))
            continue
    return sorted(set(matches))


def list_collection_items_api(collection_key: str):
    items = api_get(f"{ZOTERO_API_BASE}/collections/{collection_key}/items/top?format=json&limit=100")
    rows = []
    for item in items:
        data = item.get("data", {})
        if data.get("itemType") in ("attachment", "note"):
            continue
        rows.append({
            "key": item.get("key"),
            "title": data.get("title", ""),
            "deleted": data.get("deleted", False),
        })
    return rows


def list_collection_items_sqlite(collection_name: str):
    tmp_db = sqlite_copy_path()
    if not tmp_db:
        return None
    conn = sqlite3.connect(tmp_db)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT i.key,
               COALESCE(MAX(CASE WHEN f.fieldName='title' THEN idv.value END), ''),
               EXISTS(SELECT 1 FROM deletedItems di WHERE di.itemID=i.itemID)
        FROM collections c
        JOIN collectionItems ci ON c.collectionID = ci.collectionID
        JOIN items i ON ci.itemID = i.itemID
        LEFT JOIN itemData id ON i.itemID = id.itemID
        LEFT JOIN fields f ON id.fieldID = f.fieldID
        LEFT JOIN itemDataValues idv ON id.valueID = idv.valueID
        WHERE c.collectionName = ?
        GROUP BY i.key
        """,
        (collection_name,),
    )
    rows = [{"key": r[0], "title": r[1] or "", "deleted": bool(r[2])} for r in cur.fetchall()]
    conn.close()
    try:
        tmp_db.unlink()
    except Exception:
        pass
    return rows


def parse_obsidian_note(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    title_match = re.search(r'^title:\s*"(.+?)"\s*$', text, re.MULTILINE)
    key_match = re.search(r'^zotero_key:\s*"(.+?)"\s*$', text, re.MULTILINE)
    return {
        "path": str(path),
        "title": title_match.group(1) if title_match else path.stem,
        "zotero_key": key_match.group(1) if key_match else None,
    }


def collection_note_paths(collection_name: str):
    direct = VAULT_LITERATURE / collection_name
    candidates = []
    if direct.exists() and direct.is_dir():
        candidates.append(direct)

    for top_level in VAULT_LITERATURE.iterdir():
        if not top_level.is_dir():
            continue
        nested = top_level / collection_name
        if nested.exists() and nested.is_dir():
            candidates.append(nested)

    seen = set()
    note_paths = []
    for folder in candidates:
        for path in sorted(folder.glob("*.md")):
            if path not in seen:
                seen.add(path)
                note_paths.append(path)
    return note_paths


def audit_collection(collection_name: str, expect_title=None, expect_zotero_key=None):
    obsidian_notes = []
    for path in collection_note_paths(collection_name):
        note = parse_obsidian_note(path)
        if note:
            obsidian_notes.append(note)

    try:
        zotero_items = list_collection_items_api(collection_name_to_key(collection_name))
        source = "api"
    except Exception:
        zotero_items = list_collection_items_sqlite(collection_name)
        source = "sqlite"

    zotero_by_key = {row["key"]: row for row in (zotero_items or [])}
    obsidian_by_key = {row["zotero_key"]: row for row in obsidian_notes if row["zotero_key"]}
    obsidian_titles = {title_slug(row["title"]): row for row in obsidian_notes}
    zotero_titles = {title_slug(row["title"]): row for row in (zotero_items or [])}

    missing_in_zotero = []
    missing_in_obsidian = []
    trashed_in_zotero = []
    mismatched_keys = []

    for note in obsidian_notes:
        if not note["zotero_key"]:
            missing_in_zotero.append({"path": note["path"], "reason": "missing zotero_key"})
            continue
        zotero_item = zotero_by_key.get(note["zotero_key"])
        if not zotero_item:
            missing_in_zotero.append({"path": note["path"], "zotero_key": note["zotero_key"]})
            continue
        if zotero_item.get("deleted"):
            trashed_in_zotero.append({"key": note["zotero_key"], "title": zotero_item.get("title", "")})
        if title_slug(note["title"]) != title_slug(zotero_item.get("title", "")):
            mismatched_keys.append({
                "path": note["path"],
                "zotero_key": note["zotero_key"],
                "obsidian_title": note["title"],
                "zotero_title": zotero_item.get("title", ""),
            })

    for item in (zotero_items or []):
        if item["key"] not in obsidian_by_key and title_slug(item["title"]) not in obsidian_titles:
            missing_in_obsidian.append({"key": item["key"], "title": item["title"]})

    expected_ok = True
    expected_errors = []
    if expect_title and title_slug(expect_title) not in obsidian_titles and title_slug(expect_title) not in zotero_titles:
        expected_ok = False
        expected_errors.append({"missing_expected_title": expect_title})
    if expect_zotero_key and expect_zotero_key not in zotero_by_key:
        expected_ok = False
        expected_errors.append({"missing_expected_zotero_key": expect_zotero_key})

    ok = not any([missing_in_zotero, missing_in_obsidian, trashed_in_zotero, mismatched_keys]) and expected_ok
    return {
        "mode": "final_audit",
        "collection": collection_name,
        "source": source,
        "ok": ok,
        "counts": {
            "zotero_items": len(zotero_items or []),
            "obsidian_notes": len(obsidian_notes),
        },
        "missing_in_zotero": missing_in_zotero,
        "missing_in_obsidian": missing_in_obsidian,
        "trashed_in_zotero": trashed_in_zotero,
        "mismatched_keys": mismatched_keys,
        "expected_errors": expected_errors,
    }


def collection_name_to_key(collection_name: str):
    colls = api_get(f"{ZOTERO_API_BASE}/collections?format=json")
    for c in colls:
        data = c.get("data", {})
        if data.get("name") == collection_name:
            return c.get("key")
    raise RuntimeError(f"Collection not found via API: {collection_name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arxiv", help="arXiv ID")
    parser.add_argument("--title", help="Paper title (partial match)")
    parser.add_argument("--doi", help="DOI")
    parser.add_argument("--collection", help="Collection/folder name under Literature/ and Zotero")
    parser.add_argument("--final-audit", action="store_true", help="Audit Zotero/Obsidian consistency for a collection")
    parser.add_argument("--expect-title", help="Expected paper title after add flow")
    parser.add_argument("--expect-zotero-key", help="Expected Zotero key after add flow")
    args = parser.parse_args()

    if args.final_audit:
        if not args.collection:
            print(json.dumps({"ok": False, "error": "--collection is required with --final-audit"}, indent=2, ensure_ascii=False))
            sys.exit(1)
        output = audit_collection(args.collection, expect_title=args.expect_title, expect_zotero_key=args.expect_zotero_key)
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    output = {
        "mode": "duplicate_check",
        "duplicate_found": False,
        "items": [],
        "source": None,
        "obsidian_matches": obsidian_matches(title=args.title, arxiv_id=args.arxiv, doi=args.doi),
    }

    try:
        results = check_via_api(title=args.title, arxiv_id=args.arxiv, doi=args.doi)
        output["source"] = "api"
    except Exception:
        results = check_via_sqlite(title=args.title, arxiv_id=args.arxiv, doi=args.doi)
        if results is not None:
            output["source"] = "sqlite"
        else:
            output["source"] = "unavailable"
            output["error"] = "Cannot access Zotero (neither API nor SQLite)"
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return

    if results:
        output["duplicate_found"] = True
        output["items"] = results

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
