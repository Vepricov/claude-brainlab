import importlib.util
import contextlib
import io
import json
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

spec = importlib.util.spec_from_file_location('board', Path(__file__).resolve().parents[1] / 'scripts/hermes_obsidian_board.py')
board = importlib.util.module_from_spec(spec)
spec.loader.exec_module(board)


def fixture():
    return {'captured_at': '2026-09-09T16:00:00+00:00', 'boards': [
        {'slug': 'project', 'tasks': [
            {'id': 't_active', 'title': 'Active task', 'status': 'running', 'body': 'Protocol', 'result': 'Partial result'},
            {'id': 't_done', 'title': 'Finished task', 'status': 'done', 'result': 'Actual result'},
        ]}]}


class BoardTests(unittest.TestCase):
    def test_fetch_reads_task_scoped_comments_blocker_and_agent_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'project/kanban.db'
            path.parent.mkdir()
            with sqlite3.connect(path) as db:
                db.executescript('''
                    CREATE TABLE tasks (id,title,body,status,priority,assignee,created_at,started_at,completed_at,result,block_kind);
                    INSERT INTO tasks VALUES ('t_1','Experiment','Protocol','blocked',0,NULL,1,NULL,NULL,NULL,'needs_input');
                    CREATE TABLE task_comments (id,task_id,author,body,created_at);
                    INSERT INTO task_comments VALUES (1,'t_1','status','GPU0 was stopped; need approval',2),(2,'foreign','status','Foreign GPU7',3);
                    CREATE TABLE task_runs (id,task_id,status,started_at,ended_at,last_heartbeat_at,summary,error);
                    INSERT INTO task_runs VALUES (1,'t_1','blocked',1,2,NULL,'Missing access',NULL);
                    CREATE TABLE task_events (id,task_id,kind,payload,created_at);
                    INSERT INTO task_events VALUES (3,'t_1','blocked','{"reason":"Need access"}',2);
                ''')
            before = path.read_bytes()
            def run_local(command, **kwargs):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    exec(kwargs['input'], {})
                return subprocess.CompletedProcess(command, 0, output.getvalue(), '')
            with patch.object(board.subprocess, 'run', side_effect=run_local):
                data = board.fetch('fixture', str(root), ['project'])
            task = data['boards'][0]['tasks'][0]
            self.assertEqual([c['id'] for c in task['comments']], [1])
            self.assertEqual(task['agent_run']['summary'], 'Missing access')
            self.assertEqual(json.loads(task['block_event']['payload'])['reason'], 'Need access')
            self.assertEqual(path.read_bytes(), before)

    def test_failed_fetch_keeps_last_successful_view(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.obsidian').mkdir()
            view = root / 'Private/Hermes'
            board.write_view(view, board.render(fixture(), 'Private/Hermes'))
            before = {p.name:p.read_bytes() for p in view.iterdir()}
            args = ['board', '--ssh-host', 'fixture', '--remote-root', '/fixture',
                    '--board', 'project', '--vault', str(root), '--folder', 'Private/Hermes']
            with patch('sys.argv', args), patch.object(board, 'fetch', side_effect=TimeoutError):
                with self.assertRaises(TimeoutError):
                    board.main()
            self.assertEqual({p.name:p.read_bytes() for p in view.iterdir()}, before)

    def test_active_cards_and_full_history_keep_original_ids(self):
        files = board.render(fixture(), 'Staff/fixture/Hermes')
        canvas = json.loads(files['Hermes.canvas'])
        cards = [n for n in canvas['nodes'] if n.get('hermes_task_id')]
        self.assertEqual([n['hermes_task_id'] for n in cards], ['t_active'])
        self.assertIn('t_done', files['project.md'])
        self.assertIn('Protocol', files['project.md'])
        self.assertIn('Partial result', files['project.md'])
        self.assertIn('Actual result', files['project.md'])
        self.assertNotIn('operonId', files['project.md'])
        self.assertNotIn('- [ ]', files['project.md'])
        self.assertEqual(len({n['id'] for n in canvas['nodes']}), len(canvas['nodes']))

    def test_status_transition_keeps_identity_and_unknown_status_visible(self):
        data = fixture()
        old = json.loads(board.render(data, 'Staff/fixture/Hermes')['Hermes.canvas'])
        data['boards'][0]['tasks'][0]['status'] = 'future-status'
        new = json.loads(board.render(data, 'Staff/fixture/Hermes')['Hermes.canvas'])
        pick = lambda c: next(n for n in c['nodes'] if n.get('hermes_task_id') == 't_active')
        self.assertEqual(pick(old)['id'], pick(new)['id'])
        self.assertIn('future-status', pick(new)['text'])

    def test_untrusted_text_cannot_add_canvas_nodes_or_executable_blocks(self):
        data = fixture()
        data['boards'][0]['tasks'][0]['body'] = '```\n```dataviewjs\nalert(1)\n```\n- [ ] injected'
        files = board.render(data, 'Staff/fixture/Hermes')
        self.assertIn('````text', files['project.md'])
        self.assertNotIn('- [ ]', files['project.md'])
        self.assertEqual(json.loads(files['snapshot.json']), data)
        data['boards'][0]['slug'] = '../escape'
        with self.assertRaises(ValueError):
            board.render(data, 'Staff/fixture/Hermes')

    def test_refresh_preserves_manual_notes_and_unchanged_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = board.render(fixture(), 'Staff/fixture/Hermes')
            board.write_view(root, files)
            manual = root / 'My notes.md'
            manual.write_text('Keep this')
            original = (root / 'project.md').stat().st_mtime_ns
            board.write_view(root, files)
            self.assertEqual((root / 'project.md').stat().st_mtime_ns, original)
            self.assertEqual(manual.read_text(), 'Keep this')
            (root / 'project.md').write_text('User edited the generated note')
            with self.assertRaises(RuntimeError):
                board.write_view(root, files)
            self.assertEqual((root / 'project.md').read_text(), 'User edited the generated note')

    def test_task_id_is_scoped_by_board(self):
        data = fixture()
        data['boards'].append({'slug': 'second', 'tasks': [dict(data['boards'][0]['tasks'][0])]})
        canvas = json.loads(board.render(data, 'Staff/fixture/Hermes')['Hermes.canvas'])
        cards = [n for n in canvas['nodes'] if n.get('hermes_task_id')]
        self.assertEqual(len({n['id'] for n in cards}), 2)


if __name__ == '__main__':
    unittest.main()
