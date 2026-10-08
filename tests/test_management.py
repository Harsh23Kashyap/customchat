import tempfile,unittest,time
from pathlib import Path
from unittest.mock import Mock,patch
from customchat import schema
from customchat.store import Store
from customchat.pipeline import Engine
from customchat.management import Management,diagnosis,deploy_plan,model_review
class ManagementTests(unittest.TestCase):
 def setUp(self):
  self.cfg=schema.validate({'app':{'title':'test'},'provider':{'type':'mock'},'sources':[]});self.store=Store(':memory:');self.engine=Engine(self.cfg,self.store);self.current={'model':'old'}
  self.m=Management(self.cfg,self.engine,lambda:dict(self.current),lambda x:self.current.update(x),self.store.export_all)
 def test_status_offline(self):
  with patch.object(self.engine.provider,'complete') as p:self.m.status('a');p.assert_not_called()
 def test_live_requires_choice(self):
  with self.assertRaises(ValueError):self.m.prepare_live('a',{})
 def test_live_requires_confirmation(self):
  r=self.m.prepare_live('a',{'model':True})
  with self.assertRaises(ValueError):self.m.start('a','preflight',{'ticket':r['ticket']})
 def wait(self,jid):
  for _ in range(100):
   r=self.m.job('a',jid)
   if r['state']!='running':return r
   time.sleep(.01)
  self.fail('Job stuck')
 def test_live_job_private(self):
  r=self.m.prepare_live('a',{'model':True});jid=self.m.start('a','preflight',{'ticket':r['ticket'],'confirmed':True})['id'];self.assertEqual(self.wait(jid)['state'],'done')
  with self.assertRaises(ValueError):self.m.job('b',jid)
 def test_changed_settings_rejected(self):
  r=self.m.prepare_live('a',{'model':True});self.current['model']='new'
  with self.assertRaises(ValueError):self.m.start('a','preflight',{'ticket':r['ticket'],'confirmed':True})
 def test_restore_revision_guard(self):
  n=self.m.history.record('a',{'model':'saved'});r=self.m.handle('a','/api/workspace/history/review','POST',{'name':n},{})
  self.current['model']='later'
  with self.assertRaises(ValueError):self.m.handle('a','/api/workspace/history/restore','POST',{'ticket':r['ticket'],'confirmed':True},{})
 def test_archive_additive(self):
  cid=self.store.new_chat('a','existing');self.store.add_turn(cid,None,'q','q','a',[],[],'standard')
  r=self.m.handle('a','/api/workspace/archive/review','POST',{'archive':self.m.handle('a','/api/workspace/archive','GET',{}, {})},{})
  self.m.handle('a','/api/workspace/archive/restore','POST',{'ticket':r['ticket'],'confirmed':True},{})
  self.assertEqual(len(self.store.chats('a')),2);self.assertEqual(len(self.store.chats('b')),0)
 def test_smoke_no_chat_and_comparison(self):
  self.m.handle('a','/api/workspace/questions','POST',{'questions':['Explain this']},{})
  for i in range(2):
   r=self.m.prepare_live('a',{'sources':[]},'smoke');j=self.m.start('a','smoke',{'ticket':r['ticket'],'confirmed':True})['id'];result=self.wait(j)
  self.assertEqual(result['state'],'done');self.assertEqual(self.store.chats('a'),[]);self.assertIsNotNone(result['results'][0]['previous_answer'])
 def test_diagnostics_no_raw_exception(self):
  r=diagnosis('401 https://host/?key=secret password hello');self.assertEqual(r['category'],'authentication');self.assertNotIn('secret',r['message'])
 def test_deploy_plan_no_mutation(self):
  plan={k:'test' for k in ('target','account','region','audience','cost_limit','rollback')};plan['audience']='private';r=deploy_plan(self.cfg,plan);self.assertTrue(r['plan_only']);self.assertEqual(r['checks'][0]['state'],'unverified')
 def test_question_limit(self):
  with self.assertRaises(ValueError):self.m.handle('a','/api/workspace/questions','POST',{'questions':['q']*11},{})
 def test_model_local_only(self):
  with self.assertRaises(ValueError):model_review(self.cfg,{'model':'llama3.2:1b','base_url':'https://remote.invalid'})
 def test_model_estimate(self):
  with patch('customchat.hardware.detect',return_value={'ram_gb':16,'vram_gb':0}),patch('customchat.management.shutil.disk_usage',return_value=Mock(free=20*1024**3)):
   r=model_review(self.cfg,{'model':'llama3.2:1b'});self.assertEqual(r['download_gb_estimate'],1.3);self.assertEqual(r['free_disk_gb'],20)
 def test_source_change_invalidates_review(self):
  r=self.m.prepare_live('a',{'model':True});self.cfg['sources'].append({'id':'new','type':'pubmed'})
  with self.assertRaises(ValueError):self.m.start('a','preflight',{'ticket':r['ticket'],'confirmed':True})
 def test_live_failure_redacted(self):
  with patch.object(self.engine.provider,'complete',side_effect=RuntimeError('401 private-token')):
   r=self.m.prepare_live('a',{'model':True});j=self.m.start('a','preflight',{'ticket':r['ticket'],'confirmed':True})['id'];result=self.wait(j);self.assertNotIn('private-token',str(result));self.assertEqual(result['results'][0]['category'],'authentication')
 def test_preflight_respects_readers(self):
  self.cfg['sources']=[{'id':'x','type':'pubmed','label':'x','read_users':['b']}];self.engine.connectors['x']=Mock()
  with self.assertRaises(ValueError):self.m.prepare_live('a',{'sources':['x']})
  self.assertEqual(self.m.handle('a','/api/workspace/sources','GET',{}, {})['sources'],[])
 def test_smoke_multiple_call_notice(self):
  self.m.handle('a','/api/workspace/questions','POST',{'questions':['q']},{})
  self.assertIn('Multiple',self.m.prepare_live('a',{},'smoke')['model_calls'])
 def test_live_never_uses_persistent_cache(self):
  self.cfg['retrieval']['cache_ttl']=3600
  # The copied runner disables persistent caching, not the user's normal config.
  r=self.m.prepare_live('a',{'model':True});j=self.m.start('a','preflight',{'ticket':r['ticket'],'confirmed':True})['id'];self.wait(j);self.assertEqual(self.cfg['retrieval']['cache_ttl'],3600)
