import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


REGISTER = Path(__file__).resolve().parents[2] / "install/register-lab-mcp.py"


class NativeMcpRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / "client"
        self.target.mkdir()
        self.config = self.target / ".claude.json"
        self.original = {"customFlag": True, "mcpServers": {"personal": {"command": "personal-server"}}}
        self.config.write_text(json.dumps(self.original))
        self.server = {"type": "http", "url": "https://example.test/mcp",
                       "headers": {"Authorization": "Bearer synthetic-test-secret"}}
        self.settings = self.target / "settings.json"
        self.settings.write_text(json.dumps({"mcpServers": {"lab-knowledge": self.server}}))
        self.cli = self.root / "claude"
        self.cli.write_text(f"#!{sys.executable}\n" + '''
import json, os, pathlib, sys
path = pathlib.Path(os.environ['CLAUDE_CONFIG_DIR']) / '.claude.json'
data = json.loads(path.read_text())
assert sys.argv[1:5] == ['mcp', 'add-json', '--scope', 'user']
data['mcpServers'][sys.argv[5]] = json.loads(sys.argv[6])
path.write_text(json.dumps(data))
print(sys.argv[6])
''')
        self.cli.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.root) + os.pathsep + os.environ.get("PATH", ""),
                        CLAUDE_HOME=str(self.target), CLAUDE_CONFIG_DIR=str(self.target))

    def run_registration(self):
        return subprocess.run([sys.executable, str(REGISTER), str(self.settings), str(self.root / "backup")],
                              env=self.env, capture_output=True, text=True)

    def test_native_registration_preserves_settings_and_hides_secrets(self):
        result = self.run_registration()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(self.config.read_text())
        self.assertEqual(data["mcpServers"]["lab-knowledge"], self.server)
        self.assertEqual(data["mcpServers"]["personal"], self.original["mcpServers"]["personal"])
        self.assertTrue(data["customFlag"])
        self.assertNotIn("synthetic-test-secret", result.stdout + result.stderr)
        self.assertEqual(json.loads((self.root / "backup/claude-user-config.json").read_text()), self.original)
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o600)

    def test_existing_lab_connection_is_not_replaced(self):
        self.original["mcpServers"]["lab-knowledge"] = {"command": "my-own-connection"}
        self.config.write_text(json.dumps(self.original))
        self.cli.write_text(f"#!{sys.executable}\nraise SystemExit(99)\n")
        result = self.run_registration()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(self.config.read_text()), self.original)

    def test_cli_failure_is_not_reported_as_installed(self):
        self.cli.write_text(f"#!{sys.executable}\nprint('synthetic-test-secret')\nraise SystemExit(1)\n")
        result = self.run_registration()
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("synthetic-test-secret", result.stdout + result.stderr)
        self.assertEqual(json.loads(self.config.read_text()), self.original)

    def test_timeout_does_not_expose_command_or_key(self):
        spec = importlib.util.spec_from_file_location("register_lab_mcp", REGISTER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        error = subprocess.TimeoutExpired(["claude", "synthetic-test-secret"], 30)
        output = io.StringIO()
        with patch.dict(os.environ, self.env), patch.object(module.subprocess, "run", side_effect=error), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = module.register(self.settings, self.root / "backup")
        self.assertEqual(result, 1)
        self.assertNotIn("synthetic-test-secret", output.getvalue())


if __name__ == "__main__":
    unittest.main()
