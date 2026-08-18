#!/usr/bin/env python3
"""Archive Operon file-tasks that were finished/cancelled on a previous day.

Moves each matching `.md` file-task into <vault>/<archive_subdir>/, preserving
Obsidian wikilinks (they resolve by basename, independent of folder).
Only file-tasks (frontmatter has `operonId`) are touched; inline `- [x]` stay.
A task is archived only if its completion date is strictly before *today*.
Idempotent, collision-safe, supports --dry-run.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import re
import shutil
from pathlib import Path

logger = logging.getLogger("operon_archive")

#: Запасной список, если конфиг плагина недоступен. Настоящий берётся из самого Operon:
#: архивируется всё, что помечено там как завершённое или отменённое, поэтому новая
#: колонка вроде «Передал на проверку» не ломает архив и не требует правки скрипта.
FALLBACK_ARCHIVE_STATUSES = {"Project.Finished", "Project.Dropped", "Project.Cancelled",
                             "Personal.Готово", "Reading.Прочитано"}


def archive_statuses(vault: Path) -> set[str]:
    """Финальные статусы всех конвейеров, в виде «Конвейер.Статус»."""
    config = vault / ".obsidian/plugins/operon/data.json"
    try:
        data = json.loads(config.read_text(encoding="utf-8"))
        pipelines = data["taxonomy"]["pipelines"]["pipelines"]
    except (OSError, KeyError, json.JSONDecodeError) as error:
        logger.warning("cannot read Operon config (%s); using fallback statuses", error)
        return set(FALLBACK_ARCHIVE_STATUSES)
    found = {
        f"{pipeline['name']}.{status['label']}"
        for pipeline in pipelines
        for status in pipeline.get("statuses", [])
        if status.get("isFinished") or status.get("isCancelled")
    }
    return found or set(FALLBACK_ARCHIVE_STATUSES)
FM_RE = re.compile(r"^---\n(.*?)\n---", re.S)
SKIP_DIRS = {".obsidian", ".git", ".trash"}


def parse_frontmatter(text: str) -> dict[str, str]:
    m = FM_RE.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def completion_date(fm: dict[str, str], path: Path) -> dt.date | None:
    for key in ("dateCompleted", "datetimeModified"):
        raw = fm.get(key, "")
        if raw:
            try:
                return dt.date.fromisoformat(raw[:10])
            except ValueError:
                pass
    try:
        return dt.date.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return None


def unique_dest(dest_dir: Path, name: str) -> Path:
    dest = dest_dir / name
    if not dest_dir.exists():
        return dest
    if not dest.exists():
        return dest
    stem, suffix = Path(name).stem, Path(name).suffix
    i = 2
    while (dest_dir / f"{stem} ({i}){suffix}").exists():
        i += 1
    return dest_dir / f"{stem} ({i}){suffix}"


def iter_task_files(vault: Path, archive_dir: Path):
    for p in vault.rglob("*.md"):
        if archive_dir in p.parents or p == archive_dir:
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(vault).parts):
            continue
        yield p


def run(vault: Path, archive_subdir: str, today: dt.date, dry_run: bool) -> int:
    archive_dir = (vault / archive_subdir).resolve()
    statuses = archive_statuses(vault)
    logger.info("archiving statuses: %s", ", ".join(sorted(statuses)))
    moved = 0
    for path in iter_task_files(vault, archive_dir):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = parse_frontmatter(text)
        if "operonId" not in fm:
            continue
        status = fm.get("status", "")
        if status not in statuses:
            continue
        cdate = completion_date(fm, path)
        if cdate is None or cdate >= today:
            continue
        # Архив разложен по конвейеру и месяцу: иначе через полгода это одна папка на
        # тысячу файлов, в которой ничего не найти. Прочитанные статьи так сами собой
        # складываются в помесячный журнал чтения.
        bucket = archive_dir / status.split(".", 1)[0] / f"{cdate:%Y-%m}"
        dest = unique_dest(bucket, path.name)
        logger.info("archive: %s  ->  %s (done %s)",
                    path.relative_to(vault), dest.relative_to(vault), cdate)
        if not dry_run:
            bucket.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(dest))
        moved += 1
    logger.info("%s%d file-task(s) %s", "[dry-run] " if dry_run else "",
                moved, "would be archived" if dry_run else "archived")
    return moved


def main() -> None:
    ap = argparse.ArgumentParser(description="Daily Operon file-task archiver")
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--archive-subdir", default="Operon/Archives")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--today", default=None, help="override today (YYYY-MM-DD), for testing")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    run(args.vault.resolve(), args.archive_subdir, today, args.dry_run)


if __name__ == "__main__":
    main()
