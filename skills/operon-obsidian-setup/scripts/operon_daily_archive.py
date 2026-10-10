#!/usr/bin/env python3
"""Archive Operon file-tasks that were finished/cancelled a while ago.

Moves each matching `.md` file-task into <vault>/<archive_subdir>/, preserving
Obsidian wikilinks (they resolve by basename, independent of folder).
Only file-tasks (frontmatter has `operonId`) are touched; inline `- [x]` stay.

Two different retention windows, because the two kinds of "done" are not alike:

* **finished** (`Прочитано`, `Готово`, `Finished`) — archived the next day. The card
  has served its purpose, the reading journal is the archive.
* **cancelled** (`Reading._Trash`, `Dropped`, `Cancelled`) — kept on the board for
  `--cancelled-grace-days` days (default 1). A rejection is a decision you may want
  to revisit, and an accidental drag must be recoverable by looking at the column
  rather than by digging through the archive.

`archiveHold: true` in a card's frontmatter pins it in place regardless of dates.

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
#: Запуск из launchd обычно упирается в TCC на папке iCloud и работает по фолбэку —
#: держать его в актуальном виде обязательно.
FALLBACK_FINISHED_STATUSES = {"Project.Finished", "Personal.Готово", "Reading.Прочитано"}
FALLBACK_CANCELLED_STATUSES = {"Project.Dropped", "Project.Cancelled", "Reading._Trash"}
DEFAULT_CANCELLED_GRACE_DAYS = 1


def archive_statuses(vault: Path) -> tuple[set[str], set[str]]:
    """Финальные статусы всех конвейеров: (завершённые, отменённые)."""
    config = vault / ".obsidian/plugins/operon/data.json"
    try:
        data = json.loads(config.read_text(encoding="utf-8"))
        pipelines = data["taxonomy"]["pipelines"]["pipelines"]
    except (OSError, KeyError, json.JSONDecodeError) as error:
        logger.warning("cannot read Operon config (%s); using fallback statuses", error)
        return set(FALLBACK_FINISHED_STATUSES), set(FALLBACK_CANCELLED_STATUSES)
    finished, cancelled = set(), set()
    for pipeline in pipelines:
        for status in pipeline.get("statuses", []):
            name = f"{pipeline['name']}.{status['label']}"
            # isCancelled выигрывает: отменённое держим дольше, даже если помечено обоими.
            if status.get("isCancelled"):
                cancelled.add(name)
            elif status.get("isFinished"):
                finished.add(name)
    if not finished and not cancelled:
        return set(FALLBACK_FINISHED_STATUSES), set(FALLBACK_CANCELLED_STATUSES)
    return finished, cancelled
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
    for key in ("dateCancelled", "dateCompleted", "datetimeModified"):
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


def run(vault: Path, archive_subdir: str, today: dt.date, dry_run: bool,
        cancelled_grace_days: int = DEFAULT_CANCELLED_GRACE_DAYS) -> int:
    archive_dir = (vault / archive_subdir).resolve()
    finished, cancelled = archive_statuses(vault)
    logger.info("finished (archive next day): %s", ", ".join(sorted(finished)))
    logger.info("cancelled (archive after %d days): %s",
                cancelled_grace_days, ", ".join(sorted(cancelled)))
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
        if status in cancelled:
            cutoff = today - dt.timedelta(days=cancelled_grace_days)
        elif status in finished:
            cutoff = today
        else:
            continue
        if fm.get("archiveHold", "").lower() in ("true", "yes", "1"):
            logger.info("hold: %s (archiveHold set)", path.relative_to(vault))
            continue
        cdate = completion_date(fm, path)
        if cdate is None or cdate >= cutoff:
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
    ap.add_argument("--cancelled-grace-days", type=int, default=DEFAULT_CANCELLED_GRACE_DAYS,
                    help="сколько дней отменённые/выброшенные карточки остаются на доске "
                         f"(по умолчанию {DEFAULT_CANCELLED_GRACE_DAYS}); "
                         "завершённые всегда уходят на следующий день")
    ap.add_argument("--today", default=None, help="override today (YYYY-MM-DD), for testing")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    run(args.vault.resolve(), args.archive_subdir, today, args.dry_run,
        max(0, args.cancelled_grace_days))


if __name__ == "__main__":
    main()
