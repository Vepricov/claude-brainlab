#!/usr/bin/env python3
"""Stop, start, or query the Zotero desktop application.

zotero_attach_pdf.py writes to zotero.sqlite directly and therefore needs
Zotero closed. The shell form of that step used `osascript` and `open -a`,
which exist only on macOS, and verified with `pgrep`/`fuser`, which do not
exist on Windows. This is the one place in the pipeline that genuinely needs a
per-platform branch; the macOS branch runs exactly the commands used before.

The close is always graceful. Zotero has to flush and release the database, so
nothing here ever sends SIGKILL or `taskkill /F`.

    python3 zotero_app.py status      -> prints RUNNING or STOPPED
    python3 zotero_app.py stop        -> graceful quit, waits for exit
    python3 zotero_app.py start       -> relaunch
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

MACOS = sys.platform == "darwin"
WINDOWS = sys.platform == "win32"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def is_running() -> bool:
    if WINDOWS:
        out = _run(["tasklist", "/FI", "IMAGENAME eq zotero.exe", "/NH"]).stdout
        return "zotero.exe" in out.lower()
    return _run(["pgrep", "-f", "[Zz]otero"]).returncode == 0


def windows_executable() -> Path | None:
    found = shutil.which("zotero") or shutil.which("zotero.exe")
    if found:
        return Path(found)
    roots = [
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", ""),
    ]
    for root in roots:
        if not root:
            continue
        candidate = Path(root) / "Zotero" / "zotero.exe"
        if candidate.is_file():
            return candidate
    return None


def stop(timeout: float = 30.0) -> None:
    if not is_running():
        print("STOPPED (was not running)")
        return

    if MACOS:
        _run(["osascript", "-e", 'tell application "Zotero" to quit'])
    elif WINDOWS:
        # Without /F this posts a close request, the same as clicking the X.
        _run(["taskkill", "/IM", "zotero.exe"])
    else:
        _run(["pkill", "-TERM", "-f", "zotero"])

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not is_running():
            print("STOPPED")
            return
        time.sleep(0.5)

    raise SystemExit(
        f"ERROR: Zotero still running {timeout:.0f}s after a graceful quit. "
        "Close it by hand; do not force-kill, the database must be released."
    )


def start() -> None:
    if is_running():
        print("RUNNING (already)")
        return

    if MACOS:
        _run(["open", "-a", "Zotero"])
    elif WINDOWS:
        exe = windows_executable()
        if exe is None:
            raise SystemExit(
                "ERROR: zotero.exe not found in PATH, Program Files or "
                "LOCALAPPDATA. Start Zotero manually."
            )
        subprocess.Popen([str(exe)])
    else:
        exe = shutil.which("zotero")
        if exe is None:
            raise SystemExit("ERROR: zotero not found on PATH. Start it manually.")
        subprocess.Popen([exe])
    print("STARTED")


def main():
    parser = argparse.ArgumentParser(description="Control the Zotero application")
    parser.add_argument("action", choices=["status", "stop", "start"])
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Seconds to wait for a graceful quit (default: 30)",
    )
    args = parser.parse_args()

    if args.action == "status":
        print("RUNNING" if is_running() else "STOPPED")
    elif args.action == "stop":
        stop(args.timeout)
    else:
        start()


if __name__ == "__main__":
    main()
