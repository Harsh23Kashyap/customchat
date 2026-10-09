import tempfile,unittest,json
from pathlib import Path
from customchat import editstate,schema
class EditStateTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.path=self.root/'app.yaml';self.path.write_text('app: {title: Saved Nerd}\n');self.cfg=schema.load(str(self.path));self.cfg['_path']=str(self.path)
 def test_full_values_preserved(self):
  d=editstate.view(self.cfg);self.assertEqual(set(d),set(schema.DEFAULTS));self.assertEqual(d['app']['title'],'Saved Nerd');self.assertNotIn('_path',d)
 def test_revision_safe_save_and_reload(self):
  d=editstate.view(self.cfg);d['provider']['temperature']=.7;editstate.save_config(self.cfg,d,editstate.revision(self.cfg));self.assertEqual(schema.load(str(self.path))['provider']['temperature'],.7)
  with self.assertRaisesRegex(ValueError,'changed'):editstate.save_config(self.cfg,d,'old')
 def test_private_values_rejected(self):
  d=editstate.view(self.cfg);d['provider']['api_key']='sk-private'
  with self.assertRaises(ValueError):editstate.save_config(self.cfg,d,editstate.revision(self.cfg))
 def test_draft_roundtrip_no_execution(self):
  text='raise RuntimeError("do not execute")';editstate.save_draft(str(self.root),'search','Current code',text);self.assertEqual(editstate.helper_state(self.cfg,str(self.root))['search']['code'],text)
 def test_active_connector_loaded_as_inert_text(self):
  self.cfg=schema.validate({'sources':[{'id':'p','type':'python','entry':'plugin:search'}]});self.cfg['_dir']=str(self.root);(self.root/'plugin.py').write_text('raise RuntimeError("never run")');self.assertIn('never run',editstate.helper_state(self.cfg,str(self.root))['search']['code'])

 def test_exports_drafts_not_saved_secrets(self):
  from customchat.portable import bundle
  from customchat.nerdload import NerdLoader
  import base64,zipfile,io
  self.cfg['storage']['path']='data/customchat.db';(self.root/'data').mkdir();(self.root/'data/secrets.json').write_text('{"openai":"test-private-key"}')
  editstate.save_draft(str(self.root/'data'),'search','Saved helper','def search(q,k):return []')
  data,_=bundle(self.cfg)
  with zipfile.ZipFile(io.BytesIO(data)) as z:
   self.assertIn('data/code-drafts.json',z.namelist());self.assertNotIn('data/secrets.json',z.namelist());self.assertNotIn(b'test-private-key',data)
  loader=NerdLoader(self.root);d=loader.review('nerd.zip',base64.b64encode(data).decode());self.assertIn('data/code-drafts.json',d['preview']['files'])
 def test_saved_view_does_not_revert_to_runtime_after_save(self):
  d=editstate.view(self.cfg);d['retrieval']['min_score']=.75;d['actions']['writes']=True;editstate.save_config(self.cfg,d,editstate.revision(self.cfg))
  current=editstate.saved_view(self.cfg);self.assertEqual(current['retrieval']['min_score'],.75);self.assertTrue(current['actions']['writes']);self.assertEqual(self.cfg['retrieval']['min_score'],0)
  current['provider']['temperature']=.8;editstate.save_config(self.cfg,current,editstate.revision(self.cfg));self.assertEqual(editstate.saved_view(self.cfg)['retrieval']['min_score'],.75)
 def test_invalid_or_symlink_saved_view_rejected(self):
  self.path.write_text('app: [');self.assertRaises(ValueError,editstate.saved_view,self.cfg);self.path.unlink();other=self.root/'other.yaml';other.write_text('{}');self.path.symlink_to(other);self.assertRaises(ValueError,editstate.saved_view,self.cfg)
