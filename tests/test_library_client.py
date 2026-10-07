"""Verify that publishing a note preserves other contributors and requires read-back."""
import copy
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'skills/paper-ingest/scripts/sync_to_lab.py'
spec = importlib.util.spec_from_file_location('library_client', PATH)
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)

class LibraryClientTest(unittest.TestCase):
    def setUp(self):
        self.paper = {'id':'paper-id','title':'A paper','arxiv_id':'fixture','obsidian_path':'Literature/Topic/Paper'}
        self.chunks = [{'section':'Review','content':'Detailed old reading'},
                       {'section':'Original abstract','content':'Original source passage'}]
        self.incoming = {**{k:v for k,v in self.paper.items() if k!='id'},
                         'sections':[{'section':'Review','content':'Updated reading'}]}
        self.calls=[]

    def rpc(self, name, args):
        self.calls.append((name,copy.deepcopy(args)))
        if name=='get_paper':
            return {'paper':copy.deepcopy(self.paper),'chunks':copy.deepcopy(self.chunks)}
        if name=='upsert_paper':
            self.assertNotIn('sections',args)
            self.paper.update(args)
            if "themes" in args:self.paper["theme_slugs"]=args["themes"]
        if name=='add_paper_section':
            self.chunks=[x for x in self.chunks if x['section']!=args['section']]+[dict(args)]
        return {}

    def test_update_preserves_original_and_concurrent_extra_sections(self):
        def rpc(name,args):
            if name=='add_paper_section':
                self.chunks.append({'section':'Another contributor','content':'Arrived after the read'})
            return self.rpc(name,args)
        with patch.object(client,'_ask',side_effect=rpc):
            client.sync_paper(self.incoming)
        self.assertEqual({x['section'] for x in self.chunks},
                         {'Review','Original abstract','Another contributor'})
        self.assertEqual(self.calls[-1][0],'get_paper')

    def test_other_note_cannot_replace_matching_section_name(self):
        self.incoming['obsidian_path']='Literature/Other/Paper'
        with patch.object(client,'_ask',side_effect=self.rpc):
            with self.assertRaisesRegex(RuntimeError,'другому разбору'):
                client.sync_paper(self.incoming)
        self.assertTrue(all(name=='get_paper' for name,_ in self.calls))

    def test_silent_noop_is_not_reported_as_success(self):
        with patch.object(client,'_ask',side_effect=lambda name,args:
                          self.rpc(name,args) if name=='get_paper' else {}):
            with self.assertRaisesRegex(RuntimeError,'Read-back differs'):
                client.sync_paper(self.incoming)

    def test_read_failure_cannot_be_treated_as_new_paper(self):
        with patch.object(client,'_ask',side_effect=RuntimeError('unreachable')) as rpc:
            with self.assertRaisesRegex(RuntimeError,'unreachable'):
                client.sync_paper(self.incoming)
            self.assertEqual(rpc.call_count,1)

    def test_themes_and_tags_from_other_contributors_survive(self):
        self.paper.update(theme_slugs=['other-theme'],tags=['curated'])
        self.incoming.update(tags=['from-note'],summary_ru='Updated summary')
        with patch.object(client,'_ask',side_effect=self.rpc):client.sync_paper(self.incoming)
        self.assertEqual(self.paper['theme_slugs'],['other-theme'])
        self.assertEqual(self.paper['tags'],['curated','from-note'])

    def test_summary_write_must_be_verified_too(self):
        self.incoming['summary_ru']='New summary'
        def rpc(name,args):
            answer=self.rpc(name,args)
            if name=='upsert_paper':self.paper['summary_ru']='Old summary'
            return answer
        with patch.object(client,'_ask',side_effect=rpc):
            with self.assertRaisesRegex(RuntimeError,'Read-back differs'):client.sync_paper(self.incoming)

    def test_empty_metadata_does_not_erase_existing_authors(self):
        self.paper['authors']=['Original author']
        self.incoming['authors']=[]
        with patch.object(client,'_ask',side_effect=self.rpc):client.sync_paper(self.incoming)
        self.assertEqual(self.paper['authors'],['Original author'])

if __name__=='__main__':unittest.main()
