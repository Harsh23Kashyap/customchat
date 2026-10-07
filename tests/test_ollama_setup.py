import tempfile,time,unittest
from unittest.mock import patch,Mock
from customchat.ollama_setup import OllamaSetup,detect,download,OfficialRedirect
class OllamaSetupTests(unittest.TestCase):
 def data(self,state='not_detected'):
  return {'state':state,'system':'Linux','arch':'x86_64','supported':True,'disk_free_gb':10,'source':'https://ollama.com/install.sh','_binary':None}
 @patch('customchat.ollama_setup.hardware.installed',return_value=None)
 @patch('customchat.ollama_setup.shutil.which',return_value=None)
 def test_missing_is_not_connection_only(self,*m):self.assertEqual(detect()['state'],'not_detected')
 @patch('customchat.ollama_setup.hardware.installed',return_value=None)
 @patch('customchat.ollama_setup.shutil.which',return_value='/usr/bin/ollama')
 def test_stopped(self,*m):self.assertEqual(detect()['state'],'stopped')
 @patch('customchat.ollama_setup.hardware.installed',return_value=[])
 def test_running(self,*m):self.assertEqual(detect()['state'],'running')
 def test_no_download_during_prepare(self):
  with patch('customchat.ollama_setup.detect',return_value=self.data()),patch('customchat.ollama_setup.download') as dl:
   r=OllamaSetup().prepare('install');self.assertIn('ticket',r);dl.assert_not_called()
 def test_explicit_confirmation(self):
  with patch('customchat.ollama_setup.detect',return_value=self.data()):
   s=OllamaSetup();p=s.prepare('install')
   with self.assertRaises(ValueError):s.execute(p['ticket'],False)
 def test_unknown_ticket(self):
  with self.assertRaises(ValueError):OllamaSetup().execute('random',True)
 def test_expired(self):
  s=OllamaSetup();s.pending={'a':('install',time.monotonic()-601,'Linux')}
  with self.assertRaises(ValueError):s.execute('a',True)
 def test_low_disk(self):
  d=self.data();d['disk_free_gb']=1
  with patch('customchat.ollama_setup.detect',return_value=d):
   with self.assertRaises(ValueError):OllamaSetup().prepare('install')
 def test_existing_not_reinstalled(self):
  with patch('customchat.ollama_setup.detect',return_value=self.data('stopped')):
   with self.assertRaises(ValueError):OllamaSetup().prepare('install')
 def test_fixed_download(self):
  with self.assertRaises(ValueError):download('https://evil.example/a',tempfile.gettempdir())
 def test_redirect_denied(self):
  with self.assertRaises(ValueError):OfficialRedirect().redirect_request(None,None,302,'',{},'https://evil.example/a')
 def test_one_time_ticket_and_no_real_install(self):
  with patch('customchat.ollama_setup.detect',return_value=self.data()),patch('customchat.ollama_setup.threading.Thread') as th:
   s=OllamaSetup();p=s.prepare('install');r=s.execute(p['ticket'],True);self.assertEqual(s.job(r['id'])['state'],'downloading');th.return_value.start.assert_called_once()
   with self.assertRaises(ValueError):s.execute(p['ticket'],True)
 def test_linux_failure_is_not_success(self):
  with tempfile.TemporaryDirectory() as folder:
   from pathlib import Path
   f=Path(folder)/'install.sh';f.write_text('exit 1')
   s=OllamaSetup();s.jobs={'j':{'state':'downloading'}}
   with patch('customchat.ollama_setup.download',return_value=f),patch('customchat.ollama_setup.subprocess.Popen') as pop,patch('customchat.ollama_setup.hardware.installed',return_value=None):
    pop.return_value.poll.return_value=1;s._work('j','install','Linux');self.assertEqual(s.job('j')['state'],'needs_manual')
 def test_ready_requires_service(self):
  s=OllamaSetup();s.jobs={'j':{'state':'starting'}}
  with patch('customchat.ollama_setup.detect',return_value={'_binary':'/usr/bin/ollama'}),patch('customchat.ollama_setup.subprocess.Popen'),patch('customchat.ollama_setup.hardware.installed',return_value=[]):
   s._work('j','start','Linux');self.assertEqual(s.job('j')['state'],'ready')
class OllamaSetupHTTPTests(unittest.TestCase):
 def setUp(self):
  import threading
  from customchat import schema,server
  from customchat.pipeline import Engine
  from customchat.store import Store
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  cfg=schema.validate({});cfg['_dir']=self.tmp.name
  self.store=Store(':memory:');self.srv=server.LocalHTTPServer(('127.0.0.1',0),server.make_handler(cfg,Engine(cfg,self.store)))
  threading.Thread(target=self.srv.serve_forever,daemon=True).start();self.addCleanup(self.srv.server_close);self.addCleanup(self.srv.shutdown)
 def call(self,path='/api/ollama/setup',headers=None,body=None):
  import urllib.request,urllib.error,json
  req=urllib.request.Request('http://127.0.0.1:'+str(self.srv.server_port)+path,data=json.dumps(body).encode() if body is not None else None,headers=headers or {})
  try:
   with urllib.request.urlopen(req) as r:return r.status,json.load(r)
  except urllib.error.HTTPError as e:return e.code,json.load(e)
 def test_status_no_effect(self):self.assertEqual(self.call()[0],200)
 def test_foreign_origin_denied(self):self.assertEqual(self.call(headers={'Origin':'https://evil.example'})[0],404)
 def test_dns_rebinding_denied(self):self.assertEqual(self.call(headers={'Host':'evil.example'})[0],404)
 def test_form_post_denied(self):self.assertEqual(self.call('/api/ollama/setup/prepare',body={'action':'install'})[0],404)
 def test_json_prepare_no_process(self):
  with patch('customchat.ollama_setup.detect',return_value=OllamaSetupTests().data()),patch('customchat.ollama_setup.subprocess.Popen') as pop:
   status,data=self.call('/api/ollama/setup/prepare',{'Content-Type':'application/json'},{'action':'install'});self.assertEqual(status,200);self.assertIn('ticket',data);pop.assert_not_called()
