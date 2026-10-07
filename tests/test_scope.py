import unittest,tempfile
from pathlib import Path
from customchat import schema
from customchat.pipeline import Engine
from customchat.store import Store
class Scope(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);p=Path(self.tmp.name);(p/'docs').mkdir()
  (p/'docs/a.md').write_text('# Apples\nApples have fiber.');(p/'docs/b.md').write_text('# Beans\nBeans have protein and fiber.')
  c=schema.validate({'sources':[{'id':'docs','type':'local_files','path':'docs','refresh_interval':0}], 'retrieval':{'top_k':1}});c['_dir']=str(p)
  self.e=Engine(c,Store(':memory:'))
 def test_filters_before_top_k_no_other_doc(self):
  one,_=self.e.retrieve('fiber',scope={'source':'docs','document':'a.md'})
  two,_=self.e.retrieve('fiber',scope={'source':'docs','document':'b.md'})
  self.assertEqual(one[0]['document'],'a.md');self.assertEqual(two[0]['document'],'b.md')
 def test_scope_excludes_uploads(self):
  self.e.store.add_upload('a','Secret','Fiber private secret facts')
  rows,_=self.e.retrieve('fiber',owner='a',scope={'source':'docs'})
  self.assertTrue(all(r['source']=='docs' for r in rows))
 def test_explicit_empty_sources_is_empty(self):
  self.assertEqual(self.e.retrieve('fiber',source_ids=[])[0],[])
 def test_invalid_scope_fails_before_events(self):
  for scope in [{'source':'bad'},{'source':'docs','document':'missing.md'},'docs']:
   with self.assertRaises(ValueError):next(self.e.ask_stream('a',None,'Fiber?',scope=scope))
 def test_done_contains_scope(self):
  scope={'source':'docs','document':'a.md'};chat=self.e.store.new_chat('a')
  done=list(self.e.ask_stream('a',chat,'What is fiber?',scope=scope))[-1][1]
  self.assertEqual(done['scope'],scope);self.assertTrue(all(r['document']=='a.md' for r in done['evidence']))

 def test_saved_scope_reload_and_sync(self):
  scope={'source':'docs','document':'a.md'};chat=self.e.store.new_chat('a')
  done=self.e.ask('a',chat,'Fiber?',scope=scope)
  self.assertEqual(self.e.store.get_state('a','scope-'+done['id']),scope)
 def test_temporary_scope_discards_old_answers(self):
  scope={'source':'docs','document':'a.md'}
  result=list(self.e.ask_stream('a',None,'Fiber?',temporary=True,temp_history=[{'question':'secret','answer':'secret'}],scope=scope))[-1][1]
  self.assertEqual(result['standalone'],'Fiber?')
 def test_selected_source_intersection_fail_closed(self):
  self.assertEqual(self.e.retrieve('fiber',source_ids=[],scope={'source':'docs'})[0],[])
