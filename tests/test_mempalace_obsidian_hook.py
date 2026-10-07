"""Exercise the real Stop hook with disposable state and no automatic ingestion."""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

try:
    import mempalace.hooks_cli as hooks_cli
except ModuleNotFoundError as error:
    if error.name != "mempalace":
        raise
    raise unittest.SkipTest("Run hook tests with a Python that has MemPalace installed")


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "mempalace-obsidian-hook.py"
SPEC = importlib.util.spec_from_file_location("lab_stop_hook", SCRIPT)
HOOK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOOK)


class StopHookTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.transcript = self.root / "transcript.jsonl"
        self.settings = self.root / "settings.json"
        self.codex_config = self.root / "config.toml"
        self.codex_config.write_text('', encoding="utf-8")
        self.state = self.root / "state"
        self.settings.write_text('{}', encoding="utf-8")
        for target, name, value in (
            (hooks_cli, "STATE_DIR", self.state),
            (HOOK, "SETTINGS", self.settings),
            (HOOK, "CODEX_CONFIG", self.codex_config),
        ):
            replacement = patch.object(target, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)
        ingestion = patch.object(hooks_cli, "_maybe_auto_ingest")
        self.ingest = ingestion.start()
        self.addCleanup(ingestion.stop)

    def write_turns(self, count):
        rows = [{"message": {"role": "user", "content": f"Human message {number}"}}
                for number in range(count)]
        self.transcript.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    def invoke(self, active=False):
        payload = {"session_id": "lab-check-fixture", "transcript_path": str(self.transcript),
                   "cwd": str(self.root), "stop_hook_active": active}
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(payload))), redirect_stdout(output):
            HOOK.main()
        return json.loads(output.getvalue())

    def test_only_human_messages_advance_the_counter(self):
        self.write_turns(2)
        other = [
            {"message": {"role": "assistant", "content": "answer"}},
            {"message": {"role": "user", "content": [{"type": "tool_result", "content": "result"}]}},
            {"message": {"role": "user", "content": "<command-message>status</command-message>"}},
            {"message": {"role": "user", "content": "AUTO-SAVE checkpoint"}},
            {"message": {"role": "user", "content": "Stop hook feedback"}},
        ]
        with self.transcript.open("a", encoding="utf-8") as stream:
            stream.write("\n" + "\n".join(json.dumps(row) for row in other) + "\nmalformed JSON\n")
        self.assertEqual(HOOK.human_turns(str(self.transcript)), 2)

    def test_below_interval_does_not_interrupt(self):
        self.write_turns(9)
        self.assertEqual(self.invoke(), {})
        self.ingest.assert_not_called()

    def test_tenth_message_requests_obsidian_without_unconfigured_lab(self):
        self.write_turns(10)
        result = self.invoke()
        self.assertEqual(result["decision"], "block")
        self.assertIn(HOOK.OBSIDIAN_ADDENDUM.strip(), result["reason"])
        self.assertNotIn(HOOK.LAB_ADDENDUM.strip(), result["reason"])
        self.ingest.assert_called_once_with()

    def test_repeated_event_does_not_repeat_the_checkpoint(self):
        self.write_turns(10)
        self.invoke()
        self.assertEqual(self.invoke(), {})
        self.ingest.assert_called_once()

    def test_next_interval_includes_configured_lab(self):
        self.settings.write_text('{"mcpServers":{"lab-knowledge":{}}}', encoding="utf-8")
        self.write_turns(10)
        self.invoke()
        self.write_turns(20)
        result = self.invoke()
        self.assertEqual(result["decision"], "block")
        self.assertIn(HOOK.LAB_ADDENDUM.strip(), result["reason"])
        self.assertEqual(self.ingest.call_count, 2)

    def test_active_stop_guard_neither_interrupts_nor_consumes_interval(self):
        self.write_turns(10)
        self.assertEqual(self.invoke(active=True), {})
        self.assertFalse(self.state.exists())
        self.ingest.assert_not_called()
        self.assertEqual(self.invoke()["decision"], "block")

    def test_missing_transcript_does_not_interrupt(self):
        self.assertEqual(self.invoke(), {})
        self.ingest.assert_not_called()

    def test_broken_settings_do_not_enable_lab(self):
        self.settings.write_text('not JSON', encoding="utf-8")
        self.write_turns(10)
        self.assertNotIn(HOOK.LAB_ADDENDUM.strip(), self.invoke()["reason"])

    def test_marker_records_request_before_any_confirmed_save(self):
        self.write_turns(10)
        self.invoke()
        self.assertEqual((self.state / "lab-check-fixture_last_checkpoint_turns").read_text(), "10")
        self.assertEqual(self.invoke(), {})

    def write_codex_turns(self, count):
        rows = [{"type": "session_meta", "payload": {"id": "fixture"}}]
        for number in range(count):
            rows.extend([
                {"type": "event_msg", "payload": {"type": "user_message", "message": "copy"}},
                {"type": "response_item", "payload": {"type": "message", "role": "user",
                 "content": [{"type": "input_text", "text": f"Human request {number}"}]}},
            ])
        self.transcript.write_text("\n".join(json.dumps(row) for row in rows))

    def test_codex_counts_messages_once_and_requests_a_checkpoint(self):
        self.write_codex_turns(10)
        self.assertEqual(HOOK.human_turns(str(self.transcript)), 10)
        self.assertEqual(self.invoke()["decision"], "block")

    def test_codex_does_not_inherit_claude_mcp_configuration(self):
        self.settings.write_text('{"mcpServers":{"lab-knowledge":{}}}')
        self.write_codex_turns(10)
        self.assertNotIn(HOOK.LAB_ADDENDUM.strip(), self.invoke()["reason"])

    def test_codex_uses_its_own_enabled_server(self):
        self.codex_config.write_text('[mcp_servers.lab-knowledge]\nurl = "http://localhost/mcp"\n')
        self.write_codex_turns(10)
        self.assertIn(HOOK.LAB_ADDENDUM.strip(), self.invoke()["reason"])

    def test_disabled_codex_server_is_not_available(self):
        self.codex_config.write_text('[mcp_servers.lab-knowledge]\nenabled = false\n')
        self.write_codex_turns(10)
        self.assertNotIn(HOOK.LAB_ADDENDUM.strip(), self.invoke()["reason"])

    def test_codex_injected_instructions_are_not_human_turns(self):
        self.write_codex_turns(9)
        with self.transcript.open('a') as stream:
            stream.write('\n' + json.dumps({"type": "response_item", "payload": {
                "type": "message", "role": "user", "content": [
                    {"type": "input_text", "text": "<environment_context>setup</environment_context>"}]}}))
        self.assertEqual(self.invoke(), {})

    def test_legacy_marker_preserves_cadence_without_claiming_a_save(self):
        self.write_turns(10)
        self.state.mkdir()
        (self.state / 'lab-check-fixture_last_save_turns').write_text('10')
        self.assertEqual(self.invoke(), {})

    def test_non_object_json_lines_are_ignored(self):
        self.transcript.write_text('null\n[]\n42\n')
        self.assertEqual(self.invoke(), {})


if __name__ == "__main__":
    unittest.main()
