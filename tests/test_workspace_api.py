import unittest,threading,json,urllib.request,urllib.error,http.cookiejar,tempfile
from customchat import schema
from customchat.pipeline import Engine
from customchat.store import Store
from customchat.server import make_handler
from customchat.accounts import Accounts
from http.server import ThreadingHTTPServer
class WorkspaceAPITests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.cfg=schema.validate({'auth':{'mode':'accounts'},'sources':[]});self.cfg['_dir']=self.tmp.name;self.store=Store(':memory:');self.engine=Engine(self.cfg,self.store);acc=Accounts(self.store);acc.signup('admin@test.invalid','Admin','test-password');acc.signup('other@test.invalid','Other','test-password');self.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.cfg,self.engine));threading.Thread(target=self.server.serve_forever,daemon=True).start();self.clients=[]
  for email in ('admin@test.invalid','other@test.invalid'):
   c=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));self.clients.append(c);self.call(c,'/api/account/login',{'email':email,'password':'test-password'})
 def tearDown(self):self.server.shutdown();self.server.server_close();self.engine.nerd_loader.close();self.tmp.cleanup()
 def call(self,c,path,data=None):return json.loads(c.open(urllib.request.Request('http://127.0.0.1:'+str(self.server.server_port)+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})).read())
 def test_owner_only(self):
  self.assertIn('rows',self.call(self.clients[0],'/api/workspace/status'))
  with self.assertRaises(urllib.error.HTTPError) as e:self.call(self.clients[1],'/api/workspace/status')
  self.assertEqual(e.exception.code,404)
 def test_settings_history_and_reserved_hidden(self):
  c=self.clients[0];self.call(c,'/api/settings',{'settings':{'top_k':3}});names=self.call(c,'/api/workspace/history')['revisions'];self.assertEqual(len(names),1);self.assertEqual(self.call(c,'/api/states')['states'],[])
  r=self.call(c,'/api/workspace/history/review',{'name':names[0]});self.assertTrue(r['diff']);self.call(c,'/api/workspace/history/restore',{'ticket':r['ticket'],'confirmed':True});self.assertNotEqual(self.call(c,'/api/settings')['settings']['top_k'],3)
 def test_model_review_blocks_remote(self):
  with self.assertRaises(urllib.error.HTTPError):self.call(self.clients[0],'/api/ollama/pull/review',{'model':'qwen3:1.7b','base_url':'https://remote.invalid'})
 def test_archive_invalid_no_chat(self):
  with self.assertRaises(urllib.error.HTTPError):self.call(self.clients[0],'/api/workspace/archive/review',{'archive':{'format':'other'}})
  self.assertEqual(self.call(self.clients[0],'/api/chats'),[])
 def test_no_live_without_review(self):
  with self.assertRaises(urllib.error.HTTPError):self.call(self.clients[0],'/api/workspace/preflight/run',{'confirmed':True,'ticket':'unknown'})
 def test_credential_url_rejected(self):
  with self.assertRaises(urllib.error.HTTPError):self.call(self.clients[0],'/api/settings',{'settings':{'base_url':'https://host/?key=secret'}})

 def test_source_credentials_admin_only_and_not_echoed(self):
  from customchat import secrets
  old=secrets.STORE;secrets.STORE=secrets.SecretStore(self.tmp.name)
  self.cfg['sources']=[{'id':'newsapi','type':'http_json','label':'NewsAPI','url':'https://newsapi.org/v2/everything?q={query}','header_env':{'X-Api-Key':'NEWSAPI_KEY'}}]
  try:
   self.assertIn('credentials',self.call(self.clients[0],'/api/source-credentials'))
   for data in [None,{'source':'newsapi','env':'NEWSAPI_KEY','key':'FAKE_FIXTURE_ONLY'}]:
    with self.assertRaises(urllib.error.HTTPError):self.call(self.clients[1],'/api/source-credentials',data)
   result=self.call(self.clients[0],'/api/source-credentials',{'source':'newsapi','env':'NEWSAPI_KEY','key':'FAKE_FIXTURE_ONLY'})
   self.assertTrue(result['credentials'][0]['has_key']);self.assertNotIn('FAKE_FIXTURE_ONLY',json.dumps(result))
   self.call(self.clients[0],'/api/source-credentials',{'source':'newsapi','env':'NEWSAPI_KEY','clear':True})
  finally:secrets.STORE=old
 def test_source_credentials_locked(self):
  from unittest.mock import patch
  with patch('customchat.server.LOCKED',True):
   with self.assertRaises(urllib.error.HTTPError) as error:self.call(self.clients[0],'/api/source-credentials')
   self.assertEqual(error.exception.code,404)
