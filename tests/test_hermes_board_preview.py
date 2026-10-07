import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('preview',Path(__file__).resolve().parents[1]/'scripts/hermes_board_preview.py')
preview=importlib.util.module_from_spec(spec);spec.loader.exec_module(preview)

class PreviewTests(unittest.TestCase):
    def test_context_and_result_are_both_visible(self):
        page=preview.render({'captured_at':'snapshot','boards':[{'slug':'fixture','tasks':[{'id':'a','title':'Fixture','body':'Original protocol','result':'Measured result','status':'done'}]}]})
        self.assertIn('Original protocol',page)
        self.assertIn('Measured result',page)
        self.assertNotIn('будущего вида в Yonote',page)

    def test_untrusted_task_text_is_escaped(self):
        page=preview.render({'captured_at':'snapshot','boards':[{'slug':'fixture','tasks':[{'id':'a','title':'<script>alert(1)</script>','body':'</div><img onerror=alert(1)>','status':'running'}]}]})
        self.assertNotIn('<script>alert(1)</script>',page)
        self.assertEqual(page.count('<script>'),1)
        self.assertNotIn('<img ',page)
        self.assertIn('&lt;script&gt;',page)

    def test_all_ids_survive_including_unknown_and_history_statuses(self):
        rows=[{'id':str(i),'title':'Fixture','status':s} for i,s in enumerate(['running','blocked','ready','done','archived','future-status'])]
        page=preview.render({'captured_at':'snapshot','boards':[{'slug':'fixture','tasks':rows}]})
        for row in rows:self.assertEqual(page.count('data-task-id="'+row['id']+'"'),1)
        self.assertIn('Снимок, не живая синхронизация',page)
        self.assertIn('История · 2',page)

if __name__=='__main__':unittest.main()
