"""Exercise the real Stop hook with disposable state and no automatic ingestion.

The hook decides whether to interrupt by asking the classifier (`scripts/jev_route.py`),
and falls back to a turn counter when the classifier says nothing. These tests drive that
через a stub router on disk rather than a mock, so the subprocess path, the timeout and the
JSON contract are all real; only the verdict is canned.

Replaces an earlier suite written for the design that stood here until 03-10-2026: an
interrupt on every tenth human message, and lab instructions gated on a `lab-knowledge`
MCP server being configured. The classifier replaced the counter, and that server was
deleted on 07-10-2026 together with its database.
"""

import importlib.util
import io
import json
import os
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

#: Заглушка классификатора: печатает заранее положенный вердикт и ничего не решает сама.
#: Пустой файл вердикта означает молчание, то есть ровно то, что происходит без ключа или
#: без сети, — и тогда решать должен счётчик.
STUB_ROUTER = '''import json, os, sys
verdict = os.environ.get("JEV_STUB_VERDICT", "")
with open(sys.argv[1], encoding="utf-8") as payload:
    json.dump(json.load(payload), open(os.environ["JEV_STUB_SEEN"], "w", encoding="utf-8"),
              ensure_ascii=False)
sys.stdout.write(verdict)
'''


class StopHookTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.transcript = self.root / "transcript.jsonl"
        self.state = self.root / "state"
        self.router = self.root / "jev_stub.py"
        self.router.write_text(STUB_ROUTER, encoding="utf-8")
        self.seen = self.root / "seen.json"

        for target, name, value in ((hooks_cli, "STATE_DIR", self.state),
                                    (HOOK, "ROUTER", self.router)):
            replacement = patch.object(target, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)

        environment = patch.dict(os.environ, {"JEV_STUB_SEEN": str(self.seen),
                                              "JEV_STUB_VERDICT": ""})
        environment.start()
        self.addCleanup(environment.stop)

        ingestion = patch.object(hooks_cli, "_maybe_auto_ingest")
        self.ingest = ingestion.start()
        self.addCleanup(ingestion.stop)

    # ── фикстуры ──────────────────────────────────────────────────────────────

    def write_turns(self, count, answer="Готово: число измерено, правка применена."):
        """Стенограмма Claude Code: `count` сообщений человека и ответ после последнего."""
        rows = []
        for number in range(count):
            rows.append({"type": "user",
                         "message": {"role": "user", "content": f"Human message {number}"}})
        rows.append({"type": "assistant",
                     "message": {"role": "assistant",
                                 "content": [{"type": "text", "text": answer}]}})
        self.transcript.write_text("\n".join(json.dumps(row) for row in rows),
                                   encoding="utf-8")

    def write_codex_turns(self, count):
        rows = [{"type": "session_meta", "payload": {"id": "fixture"}}]
        for number in range(count):
            rows.extend([
                {"type": "event_msg", "payload": {"type": "user_message", "message": "copy"}},
                {"type": "response_item", "payload": {"type": "message", "role": "user",
                 "content": [{"type": "input_text", "text": f"Human request {number}"}]}},
            ])
        self.transcript.write_text("\n".join(json.dumps(row) for row in rows),
                                   encoding="utf-8")

    def says(self, **verdict):
        """Что ответит заглушка на следующем вызове."""
        os.environ["JEV_STUB_VERDICT"] = json.dumps(verdict, ensure_ascii=False)

    def invoke(self, active=False):
        payload = {"session_id": "lab-check-fixture", "transcript_path": str(self.transcript),
                   "cwd": str(self.root), "stop_hook_active": active}
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(payload))), redirect_stdout(output):
            HOOK.main()
        return json.loads(output.getvalue())

    def marker(self):
        return self.state / "lab-check-fixture_last_checkpoint_turns"

    # ── решает классификатор ──────────────────────────────────────────────────

    def test_classifier_interrupts_even_before_the_counter_would(self):
        self.write_turns(2)
        self.says(прерывать=True)
        self.assertEqual(self.invoke()["decision"], "block")
        self.ingest.assert_called_once_with()

    def test_classifier_silence_about_interrupting_leaves_it_to_the_counter(self):
        self.write_turns(2)
        self.says(прерывать=None, оценка=2.9)
        self.assertEqual(self.invoke(), {})
        self.ingest.assert_not_called()

    def test_classifier_holds_back_at_the_interval(self):
        """Счётчик больше не главный: он сработал, а классификатор сказал «нет»."""
        self.write_turns(HOOK.SAVE_INTERVAL)
        self.marker().parent.mkdir(parents=True, exist_ok=True)
        self.marker().write_text("0", encoding="utf-8")
        self.says(прерывать=False)
        self.assertEqual(self.invoke(), {})

    def test_mute_classifier_falls_back_to_the_counter(self):
        """Ни ключа, ни сети: вердикт пустой, и решает прежнее правило по счётчику."""
        self.write_turns(HOOK.SAVE_INTERVAL)
        self.marker().parent.mkdir(parents=True, exist_ok=True)
        self.marker().write_text("0", encoding="utf-8")
        self.assertEqual(self.invoke()["decision"], "block")

    def test_mute_classifier_below_the_interval_does_not_interrupt(self):
        self.write_turns(HOOK.SAVE_INTERVAL - 1)
        self.marker().parent.mkdir(parents=True, exist_ok=True)
        self.marker().write_text("0", encoding="utf-8")
        self.assertEqual(self.invoke(), {})

    def test_missing_router_falls_back_instead_of_failing(self):
        self.router.unlink()
        self.write_turns(HOOK.SAVE_INTERVAL)
        self.marker().parent.mkdir(parents=True, exist_ok=True)
        self.marker().write_text("0", encoding="utf-8")
        self.assertEqual(self.invoke()["decision"], "block")

    def test_router_sees_turn_text_cwd_and_what_was_already_recorded(self):
        self.write_turns(3, answer="Перенёс три файла хука в репозиторий.")
        self.says(прерывать=True)
        self.invoke()
        asked = json.loads(self.seen.read_text(encoding="utf-8"))
        self.assertIn("Перенёс три файла", asked["текст"])
        self.assertEqual(asked["каталог"], str(self.root))
        self.assertEqual(asked["записанное"], [])

        self.write_turns(4, answer="Второй ход про то же самое.")
        self.invoke()
        asked = json.loads(self.seen.read_text(encoding="utf-8"))
        self.assertEqual([" ".join("Перенёс три файла хука в репозиторий.".split())],
                         asked["записанное"])

    def test_turn_without_assistant_text_is_not_sent_to_the_router(self):
        self.transcript.write_text(json.dumps(
            {"type": "user", "message": {"role": "user", "content": "вопрос"}}),
            encoding="utf-8")
        self.says(прерывать=True)
        self.assertEqual(self.invoke(), {})

    # ── что печатается, когда прерываем ───────────────────────────────────────

    def test_lab_rules_are_always_printed(self):
        """База — это git-клоны, а не служба, поэтому правила не за чем прятать.

        До 08-10-2026 раздел печатался только при настроенной MCP-службе `lab-knowledge`,
        удалённой вместе со своей базой, и у установки без неё правил базы не было никогда.
        """
        self.write_turns(2)
        self.says(прерывать=True)
        reason = self.invoke()["reason"]
        self.assertIn(HOOK.LAB_ADDENDUM.strip(), reason)
        self.assertIn(HOOK.OBSIDIAN_ADDENDUM.strip(), reason)

    def test_hint_from_the_classifier_is_appended(self):
        self.write_turns(2)
        self.says(прерывать=True, подсказка="Запись отсюда идёт в `brainlab/journal`.")
        self.assertIn("brainlab/journal", self.invoke()["reason"])

    def test_absent_hint_leaves_the_reason_ending_on_the_lab_rules(self):
        self.write_turns(2)
        self.says(прерывать=True)
        reason = self.invoke()["reason"]
        self.assertTrue(reason.rstrip().endswith(HOOK.LAB_ADDENDUM.strip()))

    # ── метка и кадры ─────────────────────────────────────────────────────────

    def test_interrupt_writes_the_marker_and_the_next_turn_is_quiet(self):
        self.write_turns(2)
        self.says(прерывать=True)
        self.invoke()
        self.assertEqual(self.marker().read_text(encoding="utf-8"), "2")
        self.says(прерывать=False)
        self.assertEqual(self.invoke(), {})

    def test_active_stop_guard_neither_interrupts_nor_consumes_the_interval(self):
        self.write_turns(HOOK.SAVE_INTERVAL)
        self.says(прерывать=True)
        self.assertEqual(self.invoke(active=True), {})
        self.assertFalse(self.state.exists())
        self.ingest.assert_not_called()
        self.assertEqual(self.invoke()["decision"], "block")

    def test_a_marker_ahead_of_the_transcript_is_reset(self):
        """Сжатие контекста переписывает `.jsonl`, и метка оказывается больше числа ходов.

        Разность уходила в минус, страховка по счётчику отключалась навсегда, и 08-10-2026
        в живой сессии хук докладывал «созрело, но прошло только -1650 ходов».
        """
        self.write_turns(4)
        self.marker().parent.mkdir(parents=True, exist_ok=True)
        self.marker().write_text("1654", encoding="utf-8")
        self.says(прерывать=False)
        self.invoke()
        self.assertEqual(self.marker().read_text(encoding="utf-8"), "4")
        asked = json.loads(self.seen.read_text(encoding="utf-8"))
        self.assertEqual(asked["прошлое"], 4)
        self.assertFalse(asked["счётчик_сработал"])

    def test_a_fresh_session_starts_counting_from_now(self):
        """Стенограмма проекта живёт дольше сессии, и у новой сессии метки нет.

        Прежний ноль означал «1867 ходов без записи» на первом же ходе, и страховка
        срабатывала сразу, а потом каждый ход.
        """
        self.write_turns(1867)
        self.assertEqual(self.invoke(), {})
        self.assertEqual(self.marker().read_text(encoding="utf-8"), "1867")

    def test_legacy_marker_preserves_cadence_without_claiming_a_save(self):
        self.write_turns(HOOK.SAVE_INTERVAL)
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "lab-check-fixture_last_save_turns").write_text("10", encoding="utf-8")
        self.assertEqual(self.invoke(), {})

    # ── счёт настоящих сообщений человека ─────────────────────────────────────

    def test_only_human_messages_advance_the_counter(self):
        self.write_turns(2)
        other = [
            {"message": {"role": "assistant", "content": "answer"}},
            {"message": {"role": "user", "content": [{"type": "tool_result", "content": "r"}]}},
            {"message": {"role": "user", "content": "<command-message>status</command-message>"}},
            {"message": {"role": "user", "content": "AUTO-SAVE checkpoint"}},
            {"message": {"role": "user", "content": "Stop hook feedback"}},
        ]
        with self.transcript.open("a", encoding="utf-8") as stream:
            stream.write("\n" + "\n".join(json.dumps(row) for row in other) + "\nmalformed\n")
        self.assertEqual(HOOK.human_turns(str(self.transcript)), 2)

    def test_codex_transcripts_count_each_message_once(self):
        self.write_codex_turns(10)
        self.assertEqual(HOOK.human_turns(str(self.transcript)), 10)

    def test_codex_injected_instructions_are_not_human_turns(self):
        self.write_codex_turns(9)
        with self.transcript.open("a", encoding="utf-8") as stream:
            stream.write("\n" + json.dumps({"type": "response_item", "payload": {
                "type": "message", "role": "user", "content": [
                    {"type": "input_text",
                     "text": "<environment_context>setup</environment_context>"}]}}))
        self.assertEqual(HOOK.human_turns(str(self.transcript)), 9)

    def test_missing_transcript_does_not_interrupt(self):
        self.says(прерывать=True)
        self.assertEqual(self.invoke(), {})
        self.ingest.assert_not_called()

    def test_non_object_json_lines_are_ignored(self):
        self.transcript.write_text("null\n[]\n42\n", encoding="utf-8")
        self.assertEqual(self.invoke(), {})


if __name__ == "__main__":
    unittest.main()
