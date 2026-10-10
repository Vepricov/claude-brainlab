import json
from html.parser import HTMLParser
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from hermes_project_notes import display_time, render_project, write_project_notes


def snapshot():
    return {'captured_at': '2026-09-10T06:14:00+00:00', 'boards': [
        {'slug': slug, 'tasks': [
            {'id': 't_same', 'title': title, 'status': 'running', 'body': 'Protocol'},
            {'id': 't_done', 'title': 'Finished', 'status': 'done', 'result': 'Measurement'},
        ]} for slug, title in [('rl-muon', 'RL experiment'), ('dykaf-scale', 'DyKAF experiment')]]
    }


class ProjectNotesTests(unittest.TestCase):
    def test_dates_are_moscow_time_independent_of_machine_timezone(self):
        self.assertEqual(display_time(1788865451), '08-09-2026 14:04 МСК')
        self.assertEqual(display_time('1788880953'), '08-09-2026 18:22 МСК')
        self.assertEqual(display_time('2026-09-10T00:00:00Z'), '10-09-2026 03:00 МСК')
        self.assertEqual(display_time(None), '')
        self.assertIn('Некорректная', display_time('bad'))
        self.assertIn('Часовой пояс', display_time('2026-09-10T00:00:00'))

    def test_latest_comment_preserves_resources_and_corrections_not_old_blocker(self):
        data = snapshot()
        task = data['boards'][0]['tasks'][0]
        task.update(status='blocked', created_at=1788865451, started_at=1788880953,
                    comments=[{'id': 2, 'author': 'status', 'created_at': 1789024106,
                               'body': 'SSH vv_h200 работает. Этот опыт не запущен. Нужен выбор владельца. '
                                       'Соседний опыт на GPU0 к этой задаче не относится.'}],
                    block_event={'id': 1, 'created_at': 1788865451,
                                 'payload': '{"reason": "SSH недоступен"}'})
        note = render_project(data, data['boards'][0], 'Papers/RL/Knowledge/Hermes')['Доска.md']
        self.assertIn(task['comments'][0]['body'], note)
        self.assertLess(note.index('SSH vv_h200 работает'), note.index('Предыдущие сообщения Hermes'))
        self.assertGreater(note.index('SSH недоступен'), note.index('Предыдущие сообщения Hermes'))
        self.assertIn('08-09-2026 18:22 МСК', note)
        self.assertNotIn('Создано: 1788865451', note)
        self.assertIn('Последнее сообщение Hermes', note)
        self.assertNotIn('Причина блокировки · запись Hermes', note)

    def test_block_reason_without_comment_and_missing_information(self):
        data = snapshot()
        task = data['boards'][0]['tasks'][0]
        task.update(status='blocked', block_kind='needs_input')
        note = render_project(data, data['boards'][0], 'Papers/RL/Knowledge/Hermes')['Доска.md']
        self.assertIn('Причина и необходимая помощь в Hermes не описаны', note)
        self.assertIn('Сервер и занятые GPU не указаны', note)
        task['block_event'] = {'id': 5, 'created_at': 1789024106,
                               'payload': '{"reason": "Need dataset access <script>"}'}
        note = render_project(data, data['boards'][0], 'Papers/RL/Knowledge/Hermes')['Доска.md']
        self.assertIn('Need dataset access &lt;script&gt;', note)
        self.assertIn('Причина блокировки · запись Hermes', note)
        self.assertNotIn('Причина и необходимая помощь в Hermes не описаны', note)

    def test_agent_session_is_not_reported_as_a_gpu_run(self):
        data = snapshot()
        task = data['boards'][0]['tasks'][0]
        task['agent_run'] = {'id': 4, 'status': 'running', 'started_at': 1788880953,
                             'ended_at': None, 'summary': None, 'error': None}
        task['body'] = 'Plan: use GPU0 on vv_h200 after approval.'
        note = render_project(data, data['boards'][0], 'Papers/RL/Knowledge/Hermes')['Доска.md']
        self.assertIn('В Hermes нет сообщения о прогоне', note)
        self.assertIn(task['body'], note)
        self.assertEqual(json.loads(render_project(data, data['boards'][0], 'Papers/RL')['snapshot.json'])['boards'][0],
                         data['boards'][0])

    def test_card_text_preserves_line_breaks_and_zero_priority(self):
        data = snapshot()
        task = data['boards'][0]['tasks'][0]
        task.update(priority=0, body='Line one\n\n- [ ] source checklist\n`code` & <value>')
        note = render_project(data, data['boards'][0], 'Papers/RL/Knowledge/Hermes')['Доска.md']
        class Text(HTMLParser):
            def __init__(self):
                super().__init__()
                self.parts = []
            def handle_data(self, value):
                self.parts.append(value)
        parser = Text()
        parser.feed(note)
        visible = ''.join(parser.parts)
        self.assertIn(task['body'], visible)
        self.assertIn('Приоритет: 0', visible)

    def test_source_text_stays_text_and_does_not_become_tasks_or_code(self):
        data = snapshot()
        data['boards'][0]['tasks'][0]['body'] = (
            '</div><script>alert(1)</script>\n\n```dataviewjs\nalert(2)\n```\n'
            '- [ ] injected {{operonId:: stolen}}')
        files = render_project(data, data['boards'][0], 'Papers/RL/Knowledge/Hermes')
        note = files['Доска.md']
        self.assertNotIn('<script>', note)
        self.assertNotIn('```', note)
        self.assertNotIn('- [ ]', note)
        self.assertNotIn('{{operonId', note)
        self.assertIn('&#10;', note)
        self.assertEqual(json.loads(files['snapshot.json'])['boards'][0], data['boards'][0])

    def test_transition_moves_card_to_history_and_unknown_status_remains_visible(self):
        data = snapshot()
        data['boards'][0]['tasks'][0]['status'] = 'future-status'
        files = render_project(data, data['boards'][0], 'Papers/RL/Knowledge/Hermes')
        self.assertIn('future-status', files['Доска.md'])
        data['boards'][0]['tasks'][0].update(status='done', result='New result')
        files = render_project(data, data['boards'][0], 'Papers/RL/Knowledge/Hermes')
        self.assertNotIn('t_same', files['Доска.md'])
        self.assertIn('t_same', files['История.md'])
        self.assertIn('New result', files['История.md'])
        self.assertIn('Активных задач нет', files['Доска.md'])

    def test_manual_change_in_second_project_prevents_all_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            routes = {'rl-muon': 'Papers/RL', 'dykaf-scale': 'Papers/DyKAF'}
            for folder in routes.values():
                (vault / folder).mkdir(parents=True)
            data = snapshot()
            write_project_notes(vault, data, routes)
            manual = vault / 'Papers/DyKAF/Knowledge/Hermes/Доска.md'
            manual.write_text(manual.read_text() + '\nMy annotation')
            before = {str(p):p.read_bytes() for p in vault.rglob('*') if p.is_file()}
            data['captured_at'] = '2026-09-10T07:14:00+00:00'
            with self.assertRaisesRegex(RuntimeError, 'Manual changes preserved'):
                write_project_notes(vault, data, routes)
            self.assertEqual(before, {str(p):p.read_bytes() for p in vault.rglob('*') if p.is_file()})

    def test_missing_or_conflicting_bindings_do_not_create_projects(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            (vault / 'Papers/RL').mkdir(parents=True)
            for routes in [{'rl-muon': 'Papers/RL'},
                           {'rl-muon': 'Papers/RL', 'dykaf-scale': 'Papers/missing'},
                           {'rl-muon': 'Papers/RL', 'dykaf-scale': 'Papers/RL'},
                           {'rl-muon': '..', 'dykaf-scale': 'Papers/RL'}]:
                with self.assertRaises(ValueError):
                    write_project_notes(vault, snapshot(), routes)
                self.assertEqual(list(vault.rglob('*.md')), [])

    def test_each_project_gets_its_own_board_and_full_history(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            routes = {'rl-muon': 'Papers/RL', 'dykaf-scale': 'Papers/DyKAF'}
            for folder in routes.values():
                (vault / folder).mkdir(parents=True)
            write_project_notes(vault, snapshot(), routes)
            for slug, folder in routes.items():
                root = vault / folder / 'Knowledge/Hermes'
                data = json.loads((root / 'snapshot.json').read_text())
                self.assertEqual([b['slug'] for b in data['boards']], [slug])
                self.assertEqual([t['id'] for t in data['boards'][0]['tasks']], ['t_same', 't_done'])
                current = (root / 'Доска.md').read_text()
                history = (root / 'История.md').read_text()
                self.assertIn('t_same', current)
                self.assertNotIn('t_done', current)
                self.assertIn('t_done', history)
                self.assertIn('Measurement', history)
                self.assertNotIn('operonId', current + history)
                self.assertNotIn('dataviewjs', current + history)
                self.assertNotIn('.html', current + history)


if __name__ == '__main__':
    unittest.main()
