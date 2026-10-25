"""Fact guards of the Stop hook against real git repositories and canned GitLab answers.

24-10-2026 most fact interruptions were false: a branch already pushed to its own branch
in GitLab was called unsent, files the session never touched were blamed on it, and a gate
that failed once and passed on rerun stayed red.
"""

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


WHERE = load("where_fixture", ROOT / "hooks" / "lab-where-am-i.py")
try:
    HOOK = load("stop_fixture", ROOT / "scripts" / "mempalace-obsidian-hook.py")
except ModuleNotFoundError as error:
    raise unittest.SkipTest(f"needs MemPalace: {error}")


def git(folder, *args):
    subprocess.run(["git", "-C", str(folder), *args], check=True, capture_output=True)


class UnsentTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.bare, self.clone = root / "origin.git", root / "clone"
        git(root, "init", "-q", "--bare", "-b", "main", str(self.bare))
        git(root, "clone", "-q", str(self.bare), str(self.clone))
        for key, value in (("user.name", "t"), ("user.email", "t@t"), ("commit.gpgsign", "false")):
            git(self.clone, "config", key, value)
        # The guard recognises a lab clone by the base host anywhere in its config.
        git(self.clone, "config", "remote.base.url", f"https://{WHERE.BASE_HOST}/x.git")
        (self.clone / "a.md").write_text("a\n")
        git(self.clone, "add", "a.md")
        git(self.clone, "commit", "-qm", "a")
        git(self.clone, "push", "-q", "origin", "main")
        self.transcript = root / "t.jsonl"
        self.transcript.write_text("")
        patcher = patch.object(HOOK, "_lab_hook", lambda: WHERE)
        patcher.start()
        self.addCleanup(patcher.stop)

    def touched(self, *paths):
        rows = [{"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Edit", "input": {"file_path": str(self.clone / p)}}]}}
            for p in paths]
        self.transcript.write_text("\n".join(json.dumps(r) for r in rows))

    def unsent(self):
        return HOOK.nesohranennoe(str(self.clone), str(self.transcript))

    def test_branch_pushed_to_its_own_branch_is_sent(self):
        git(self.clone, "checkout", "-qb", "claim/H-X-001")
        (self.clone / "b.md").write_text("b\n")
        git(self.clone, "add", "b.md")
        git(self.clone, "commit", "-qm", "b")
        self.assertEqual(len(self.unsent()), 1)
        git(self.clone, "push", "-q", "-u", "origin", "claim/H-X-001")
        self.assertEqual(self.unsent(), [])

    def test_file_the_session_never_touched_is_not_blamed_on_it(self):
        (self.clone / "manuscript.tex").write_text("someone else's\n")
        self.assertEqual(self.unsent(), [])

    def test_file_the_session_edited_is_reported(self):
        (self.clone / "a.md").write_text("changed\n")
        self.touched("a.md")
        self.assertIn("a.md", self.unsent()[0])


class GateVerdictTest(unittest.TestCase):
    def verdict(self, statuses):
        answers = iter([[{"iid": 7, "sha": "abc", "title": "t"}], statuses])

        class Answer:
            def __init__(self, body): self.body = json.dumps(body).encode()
            def read(self): return self.body
            def __enter__(self): return self
            def __exit__(self, *a): return False

        with patch.object(WHERE.urllib.request, "urlopen", lambda *a, **k: Answer(next(answers))):
            return WHERE._open_with_verdict("brainlab/x", "token")[0]

    def test_rerun_that_passed_is_green(self):
        row = self.verdict([{"id": 1, "name": "база", "status": "failed"},
                            {"id": 2, "name": "база", "status": "success"}])
        self.assertIn("зелено", row)

    def test_latest_failure_is_still_red(self):
        row = self.verdict([{"id": 1, "name": "база", "status": "success"},
                            {"id": 2, "name": "база", "status": "failed"}])
        self.assertIn("ЕСТЬ ЗАМЕЧАНИЯ", row)


if __name__ == "__main__":
    unittest.main()
