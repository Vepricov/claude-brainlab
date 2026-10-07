import copy
import importlib.util
from pathlib import Path
import unittest


path = Path(__file__).resolve().parents[1] / 'skills/lab-knowledge/scripts/yonote_task_gate.py'
spec = importlib.util.spec_from_file_location('yonote_task_gate', path)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
OWNER, OTHER, PROJECT, BOARD, TASK = [f'00000000-0000-4000-8000-{n:012d}' for n in range(1, 6)]


class TaskGateTests(unittest.TestCase):
    def setUp(self):
        self.binding = {'project_id': PROJECT, 'board_id': BOARD}
        self.row = {'id': TASK, 'title': 'Check result', 'assignee_ids': [OWNER],
                    'status': 'Бэклог', 'revision': 'source-revision'}
        self.snapshot = {**self.binding, 'binding_verified': True, 'has_more': False,
                         'next_offset': None, 'items': [self.row]}

    def select(self, executions=None):
        return gate.select_tasks(self.snapshot, self.binding, OWNER, executions)

    def test_owner_ready_and_input_unchanged(self):
        original = copy.deepcopy(self.snapshot)
        result = self.select()
        self.assertEqual(result['candidates'][0]['action'], 'start')
        self.assertEqual(result['candidates'][0]['id'], TASK)
        self.assertFalse(result['mutations'])
        self.assertEqual(self.snapshot, original)

    def test_other_unassigned_and_multiple_assignees_are_excluded(self):
        for ids in ([OTHER], [], [OWNER, OTHER]):
            with self.subTest(ids=ids):
                self.row['assignee_ids'] = ids
                self.assertEqual(self.select()['candidates'], [])

    def test_owner_name_does_not_replace_stable_identity(self):
        del self.row['assignee_ids']
        self.row['assignee'] = 'Owner'
        self.assertEqual(self.select()['pending'][0]['reason'], 'assignee_identity_unavailable')

    def test_resumes_only_linked_execution(self):
        self.row['status'] = 'В работе'
        self.assertEqual(self.select()['candidates'], [])
        key = '/'.join((PROJECT, BOARD, TASK))
        result = self.select({key: 't_existing'})
        self.assertEqual(result['candidates'][0]['hermes_task_id'], 't_existing')
        self.assertEqual(result['candidates'][0]['action'], 'resume')

    def test_cannot_enqueue_linked_task_twice(self):
        key = '/'.join((PROJECT, BOARD, TASK))
        self.assertEqual(self.select({key: 't_existing'})['candidates'], [])

    def test_reassignment_prevents_resume(self):
        self.row.update(status='В работе', assignee_ids=[OTHER])
        key = '/'.join((PROJECT, BOARD, TASK))
        self.assertEqual(self.select({key: 't_existing'})['candidates'], [])

    def test_finished_and_unknown_states_are_not_started(self):
        for status in ['Готово', 'На проверке', None]:
            self.row['status'] = status
            self.assertEqual(self.select()['candidates'], [])

    def test_wrong_project_or_board_is_blocked(self):
        for field in self.binding:
            original = self.snapshot[field]
            self.snapshot[field] = OTHER
            with self.assertRaises(ValueError): self.select()
            self.snapshot[field] = original

    def test_unverified_binding_and_partial_pagination_are_blocked(self):
        for field, value in [('binding_verified', False), ('has_more', True), ('next_offset', 100)]:
            original = self.snapshot[field]
            self.snapshot[field] = value
            with self.assertRaises(ValueError): self.select()
            self.snapshot[field] = original

    def test_duplicate_rows_are_blocked(self):
        self.snapshot['items'].append(copy.deepcopy(self.row))
        with self.assertRaises(ValueError): self.select()


if __name__ == '__main__':
    unittest.main()
