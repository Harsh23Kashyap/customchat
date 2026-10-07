import unittest,tempfile
from pathlib import Path
from customchat import schema,permissions
from customchat.pipeline import Engine
from customchat.store import Store
class Permissions(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);p=Path(self.tmp.name);(p/'docs').mkdir()
  (p/'docs/public.md').write_text('# Public\nFiber public facts.');(p/'docs/private.md').write_text('# Secret\nFiber secret facts.')
  self.cfg=schema.validate({'auth':{'mode':'accounts'},'sources':[{'id':'docs','type':'local_files','path':'docs','document_users':{'private.md':['alice']}}],'retrieval':{'top_k':1}});self.cfg['_dir']=str(p)
  self.e=Engine(self.cfg,Store(':memory:'))
 def test_before_topk_and_cache(self):
  a,_=self.e.retrieve('secret fiber',owner='alice');b,_=self.e.retrieve('secret fiber',owner='bob')
  self.assertEqual(a[0]['document'],'private.md');self.assertEqual(b[0]['document'],'public.md')
 def test_direct_scope_denial(self):
  with self.assertRaises(ValueError):next(self.e.ask_stream('bob',None,'fiber',temporary=True,scope={'source':'docs','document':'private.md'}))
 def test_collection_denial(self):
  self.cfg['sources'][0]['read_users']=['alice'];self.assertEqual(self.e.retrieve('fiber',owner='bob')[0],[])
 def test_policy_revocation_cache(self):
  self.e.retrieve('secret fiber',owner='alice');self.cfg['sources'][0]['document_users']['private.md']=[]
  a,_=self.e.retrieve('secret fiber',owner='alice');self.assertEqual(a[0]['document'],'public.md')
 def test_empty_deny(self):
  self.cfg['sources'][0]['read_users']=[];self.assertEqual(self.e.retrieve('fiber',owner='alice')[0],[])
 def test_saved_answer_redacted(self):
  c=self.e.store.new_chat('alice');r=self.e.ask('alice',c,'secret fiber');self.cfg['sources'][0]['document_users']['private.md']=[]
  v=permissions.view(self.cfg,'alice',r);self.assertEqual(v['evidence'],[]);self.assertNotIn('secret facts',v['answer'])
 def test_temp_permissions_no_uploads(self):
  self.e.store.add_upload('alice','upload','Fiber super secret upload')
  r=list(self.e.ask_stream('alice',None,'secret fiber',temporary=True))[-1][1]
  self.assertEqual(r['evidence'][0]['document'],'private.md');self.assertTrue(all(x['source']!='uploads' for x in r['evidence']))
 def test_accounts_required(self):
  with self.assertRaises(schema.ConfigError):schema.validate({'sources':[{'type':'local_files','read_users':['alice']}]})
 def test_remote_document_rule_rejected(self):
  with self.assertRaises(schema.ConfigError):schema.validate({'auth':{'mode':'accounts'},'sources':[{'type':'pubmed','document_users':{}}]})
 def test_source_listing(self):
  self.cfg['sources'][0]['read_users']=['alice'];self.assertFalse(permissions.allowed(self.cfg,None,'docs'))
 def test_http_accounts_and_revocation(self):
  import threading,json,urllib.request,http.cookiejar
  from http.server import ThreadingHTTPServer
  from customchat.server import make_handler
  from customchat.accounts import Accounts
  acc=Accounts(self.e.store);alice=acc.signup('alice@test.invalid','Alice','test-password');bob=acc.signup('bob@test.invalid','Bob','test-password')
  self.cfg['sources'][0]['document_users']={'private.md':[alice]}
  srv=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.cfg,self.e));threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:
   clients=[]
   for email in ['alice@test.invalid','bob@test.invalid']:
    client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));clients.append(client)
    client.open(urllib.request.Request('http://127.0.0.1:%s/api/account/login'%srv.server_port,data=json.dumps({'email':email,'password':'test-password'}).encode(),headers={'Content-Type':'application/json'})).read()
   def call(client,path,body=None):
    data=None if body is None else json.dumps(body).encode()
    return json.loads(client.open(urllib.request.Request('http://127.0.0.1:%s'%srv.server_port+path,data=data,headers={'Content-Type':'application/json'})).read())
   a,b=clients
   self.assertIn('private.md',call(a,'/api/scopes')[0]['documents']);self.assertNotIn('private.md',call(b,'/api/scopes')[0]['documents'])
   result=call(a,'/api/ask',{'question':'secret fiber'});self.assertEqual(result['evidence'][0]['document'],'private.md')
   resultb=call(b,'/api/ask',{'question':'secret fiber'});self.assertEqual(resultb['evidence'][0]['document'],'public.md')
   self.cfg['sources'][0]['document_users']['private.md']=[]
   turns=call(a,'/api/turns?chat='+result['chat']);self.assertEqual(turns[0]['evidence'],[])
   exported=call(a,'/api/export-all');self.assertNotIn('secret facts',str(exported))
  finally:srv.shutdown();srv.server_close()
