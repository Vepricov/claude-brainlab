"""The check runner must distinguish test failures from missing prerequisites."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "lab_check.py"
SPEC = importlib.util.spec_from_file_location("lab_check", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class LabCheckTest(unittest.TestCase):
    def test_broken_runtime_is_reported_without_aborting_the_suite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "bad-python"
            runtime.write_text("#!/bin/sh\nexit 17\n")
            runtime.chmod(0o700)
            checks = [
                MODULE.Check("bad-runtime", (str(runtime),), modules=("pytest",)),
                MODULE.Check("next", (sys.executable, "-c", "exit(0)")),
            ]
            results = MODULE.run_checks(checks, root, root, 5)
            self.assertEqual([x["status"] for x in results], ["FAIL", "PASS"])
            self.assertIn("17", results[0]["reason"])

    def test_cli_keeps_a_machine_readable_report_and_states_its_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / "scripts" / "lab_check.py"
            script.parent.mkdir()
            script.write_bytes(SCRIPT.read_bytes())
            fixture = root / "skills" / "call-notes"
            (fixture / "tests").mkdir(parents=True)
            (fixture / "scripts").mkdir()
            (fixture / "SKILL.md").write_text("Test fixture only\n")
            (fixture / "scripts" / "normalize_transcript.py").touch()
            (fixture / "tests" / "test_normalize_transcript.py").touch()
            (fixture / "tests" / "test_skill_contract.py").write_text(
                "import unittest\nclass Fixture(unittest.TestCase):\n"
                "    def test_healthy(self):\n        self.assertTrue(True)\n"
            )
            report_dir = root / "report"
            completed = subprocess.run(
                [sys.executable, str(script), "--profile", "offline", "--check", "call-notes",
                 "--output-dir", str(report_dir)], cwd=directory,
                text=True, capture_output=True, timeout=20,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            report = json.loads((report_dir / "report.json").read_text())
            self.assertEqual(report["profile"], "offline")
            self.assertEqual(report["scope"], "selected checks only")
            self.assertEqual(report["status"], "PASS")
            self.assertEqual([x["name"] for x in report["checks"]], ["call-notes"])
            self.assertTrue(report["not_covered"])
            self.assertIn("commit", report["repository"])

    def test_children_do_not_inherit_credentials_or_python_injection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = (
                sys.executable, "-c",
                "import os; assert 'LAB_MCP_TOKEN' not in os.environ; "
                "assert 'PYTHONPATH' not in os.environ; print('isolated')",
            )
            with patch.dict(os.environ, {"LAB_MCP_TOKEN": "fake-secret", "PYTHONPATH": directory}):
                results = MODULE.run_checks([MODULE.Check("environment", command)], root, root, 5)
            self.assertEqual(results[0]["status"], "PASS")

    def test_missing_dependency_is_an_explicit_skip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            check = MODULE.Check(
                "dependency", (sys.executable, "-c", "exit(99)"),
                modules=("lab_check_nonexistent_dependency",),
            )
            results = MODULE.run_checks([check], root, root, 5)
            self.assertEqual(results[0]["status"], "SKIP")
            self.assertIn("lab_check_nonexistent_dependency", results[0]["reason"])

    def test_timeout_is_a_failure_and_next_check_still_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checks = [
                MODULE.Check("slow", (sys.executable, "-c", "import time; time.sleep(20)")),
                MODULE.Check("next", (sys.executable, "-c", "exit(0)")),
            ]
            results = MODULE.run_checks(checks, root, root, timeout=0.15)
            self.assertEqual([x["status"] for x in results], ["FAIL", "PASS"])
            self.assertIn("Timeout", results[0]["reason"])

    def test_missing_inputs_are_skipped_and_never_count_as_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            check = MODULE.Check(
                "missing", (sys.executable, "-c", "exit(0)"),
                files=("missing-test.py",),
            )
            results = MODULE.run_checks([check], root, root, timeout=5)
            self.assertEqual(results[0]["status"], "SKIP")
            self.assertIn("missing-test.py", results[0]["reason"])
            self.assertEqual(MODULE.outcome(results), ("INCOMPLETE", 2))
            self.assertEqual(MODULE.outcome([]), ("INCOMPLETE", 2))

    def test_failure_does_not_hide_later_checks_and_logs_are_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checks = [
                MODULE.Check("broken", (sys.executable, "-c", "print('failure detail'); exit(3)")),
                MODULE.Check("healthy", (sys.executable, "-c", "print('success detail')")),
            ]
            results = MODULE.run_checks(checks, root, root, timeout=5)
            self.assertEqual([item["status"] for item in results], ["FAIL", "PASS"])
            self.assertEqual(MODULE.outcome(results), ("FAIL", 1))
            self.assertIn("failure detail", Path(results[0]["log"]).read_text())
            self.assertIn("success detail", Path(results[1]["log"]).read_text())


if __name__ == "__main__":
    unittest.main()
