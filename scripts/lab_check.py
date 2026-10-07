#!/usr/bin/env python3
"""Run the repository's existing offline checks and keep their evidence together."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class Check:
    name: str
    command: tuple[str, ...]
    files: tuple[str, ...] = ()
    modules: tuple[str, ...] = ()
    executables: tuple[str, ...] = ()


def check_environment(command: tuple[str, ...]) -> dict[str, str]:
    env = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "TMPDIR", "SYSTEMROOT")
           if key in os.environ}
    executable = shutil.which(command[0])
    if executable and Path(executable).name.startswith("python"):
        env["PATH"] = str(Path(executable).parent) + os.pathsep + env.get("PATH", os.defpath)
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    return env


def missing_prerequisites(check: Check, root: Path, env: dict[str, str]) -> str:
    missing = [path for path in check.files if not (root / path).exists()]
    if missing:
        return "Missing input: " + ", ".join(missing)
    missing = [name for name in (check.command[0], *check.executables)
               if not shutil.which(name, path=env.get("PATH"))]
    if missing:
        return "Missing executable: " + ", ".join(missing)
    if check.modules:
        probe = subprocess.run(
            [check.command[0], "-c", "import importlib.util,json,sys; "
             "print(json.dumps([m for m in sys.argv[1:] if importlib.util.find_spec(m) is None]))",
             *check.modules], cwd=root, env=env, capture_output=True, text=True, timeout=10,
        )
        if probe.returncode:
            raise RuntimeError(f"Dependency probe exited {probe.returncode}")
        missing = json.loads(probe.stdout)
        if missing:
            return f"Missing Python modules in {check.command[0]}: " + ", ".join(missing)
    return ""


def outcome(results: list[dict]) -> tuple[str, int]:
    if any(item["status"] == "FAIL" for item in results):
        return "FAIL", 1
    if not results or any(item["status"] == "SKIP" for item in results):
        return "INCOMPLETE", 2
    return "PASS", 0


def run_checks(
    checks: list[Check], root: Path, output: Path, timeout: float
) -> list[dict]:
    results = []
    for check in checks:
        started = time.monotonic()
        log = output / f"{check.name}.log"
        env = check_environment(check.command)
        code = None
        with log.open("w", encoding="utf-8") as stream:
            try:
                reason = missing_prerequisites(check, root, env)
                if reason:
                    status = "SKIP"
                    stream.write(reason + "\n")
                else:
                    with subprocess.Popen(
                        check.command, cwd=root, stdout=stream, stderr=subprocess.STDOUT,
                        start_new_session=os.name == "posix", env=env,
                    ) as process:
                        try:
                            code = process.wait(timeout=timeout)
                            status = "PASS" if code == 0 else "FAIL"
                            reason = f"exit {code}"
                        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
                            try:
                                if os.name == "posix":
                                    os.killpg(process.pid, signal.SIGKILL)
                                else:
                                    process.kill()
                            except ProcessLookupError:
                                pass
                            process.wait()
                            if isinstance(error, KeyboardInterrupt):
                                raise
                            status, reason = "FAIL", f"Timeout after {timeout:g}s"
                            stream.write(reason + "\n")
            except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
                status, reason = "FAIL", f"{type(error).__name__}: {error}"
                stream.write(reason + "\n")
        results.append({
            "name": check.name,
            "status": status,
            "reason": reason,
            "returncode": code,
            "duration_seconds": round(time.monotonic() - started, 3),
            "command": list(check.command),
            "log": str(log),
        })
    return results


def available_checks(python: str, hook_python: str) -> list[Check]:
    return [
        Check("runner", (python, "-m", "unittest", "discover", "-s", "tests", "-p", "test_lab_check.py"),
              ("scripts/lab_check.py", "tests/test_lab_check.py")),
        Check("settings", ("bash", "tests/install/test-settings-rendering.sh"),
              ("tests/install/test-settings-rendering.sh", "install/setup.sh", "scripts/setup.sh",
               "settings.json.template", "obsidian-projects.example.json"), executables=("rg", "python3")),
        Check("llm-routes", (python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_llm_routes.py"),
              ("tests/test_llm_routes.py", "scripts/lab_llm/route.py", "config/llm-routes.toml"),
              modules=("pytest", "tomllib")),
        Check("call-notes", (python, "-m", "unittest", "discover", "-s", "skills/call-notes/tests"),
              ("skills/call-notes/tests/test_skill_contract.py", "skills/call-notes/tests/test_normalize_transcript.py",
               "skills/call-notes/SKILL.md", "skills/call-notes/scripts/normalize_transcript.py")),
        Check("hook", (hook_python, "-m", "unittest", "discover", "-s", "tests", "-p", "test_mempalace_obsidian_hook.py"),
              ("scripts/mempalace-obsidian-hook.py", "tests/test_mempalace_obsidian_hook.py"),
              modules=("mempalace",)),
        Check("atlas", (python, "-m", "unittest", "discover", "-s", "docs/lab-atlas/tests", "-p", "test_manifest.py"),
              ("docs/lab-atlas/tests/test_manifest.py", "docs/lab-atlas/data/atlas-data.json"),
              executables=("node", "git")),
    ]


def repository_state(root: Path) -> dict:
    def git(*args: str) -> str | None:
        try:
            result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.stdout.strip() if result.returncode == 0 else None

    return {"commit": git("rev-parse", "HEAD"), "working_tree": git("status", "--short")}


def positive_timeout(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("timeout must be a finite positive number")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("offline",), default="offline")
    parser.add_argument("--python", default=sys.executable, help="Python used for ordinary tests")
    parser.add_argument("--hook-python", help="Python with the existing MemPalace installation")
    parser.add_argument("--check", action="append", choices=("runner", "settings", "llm-routes", "call-notes", "hook", "atlas"),
                        help="Run only these checks; repeat this option to select several")
    parser.add_argument("--include-atlas", action="store_true", help="Include private Atlas manifest tests (read-only)")
    parser.add_argument("--timeout", type=positive_timeout, default=120, help="Seconds per check")
    parser.add_argument("--output-dir", type=Path, help="New directory for report.json and logs (default: temporary directory)")
    parser.add_argument("--list", action="store_true", help="List selected checks without running them")
    args = parser.parse_args(argv)
    checks = available_checks(args.python, args.hook_python or args.python)
    names = set(args.check or [check.name for check in checks if check.name != "atlas"])
    if args.include_atlas:
        names.add("atlas")
    checks = [check for check in checks if check.name in names]
    if args.list:
        for check in checks:
            print(f"{check.name}: {json.dumps(check.command)}")
        return 0
    root = Path(__file__).resolve().parents[1]
    if args.output_dir:
        output = args.output_dir.expanduser().resolve()
        try:
            output.mkdir(mode=0o700, parents=True, exist_ok=False)
        except OSError as error:
            parser.error(f"Cannot create report directory: {error}")
    else:
        output = Path(tempfile.mkdtemp(prefix="lab-check-"))
    report = {
        "profile": args.profile,
        "scope": "selected checks only" if args.check else "offline checks only",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "repository": repository_state(root),
        "source_sha256": {path: hashlib.sha256((root / path).read_bytes()).hexdigest()
                          for check in checks for path in check.files if (root / path).is_file()},
        "not_covered": [
            "Live MCP and Yonote integration; waiting for the component owner's stable contract",
            "Actual Brain Call recording, analysis and publication",
            "Browser interaction and the published website",
            "Successful durable memory writes; hook tests stub automatic ingestion",
        ],
    }
    if "atlas" not in names:
        report["not_covered"].append("Private Atlas manifest; opt in with --include-atlas")
    else:
        report["atlas_repository"] = repository_state(root / "docs/lab-atlas")
    results = run_checks(checks, root, output, args.timeout)
    status, exit_code = outcome(results)
    report.update(status=status, exit_code=exit_code, checks=results)
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for result in results:
        print(f"{result['status']:4} {result['name']:12} {result['duration_seconds']:6.2f}s  {result['reason']}")
    print(f"{status}: {report['scope']}. Live integrations and browser checks are NOT verified.")
    print(f"Report: {output / 'report.json'}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
