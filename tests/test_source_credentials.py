import io,json,os,tempfile,unittest,zipfile
from unittest.mock import patch
from customchat import schema,secrets,source_credentials
from customchat.connectors.http_json import HttpJson
from customchat.portable import bundle
class Reply:
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self):return json.dumps({'articles':[{'title':'Fixture only','description':'Not real news','url':'https://example.test/story','author':'Fixture author','publishedAt':'2026-10-09T00:00:00Z','source':{'name':'Fixture publisher'}}]}).encode()
class SourceKeys(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=secrets.STORE;secrets.STORE=secrets.SecretStore(self.tmp.name)
  self.src={'id':'newsapi','label':'NewsAPI','type':'http_json','url':'https://newsapi.org/v2/everything?q={query}&pageSize={k}','header_env':{'X-Api-Key':'NEWSAPI_KEY'},'results_path':'articles','fields':{'title':'title','text':'description','url':'url','authors':'author','year':'publishedAt','venue':'source.name'}}
  self.cfg=schema.validate({'provider':{'type':'mock'},'sources':[self.src]})
 def tearDown(self):secrets.STORE=self.old;self.tmp.cleanup()
 def test_missing_key_fails_before_network(self):
  with patch.dict(os.environ,{},clear=True),patch('urllib.request.urlopen') as call:
   with self.assertRaises(ValueError):HttpJson(self.src).search('AI regulation')
   call.assert_not_called()
 def test_private_key_header_and_mapping(self):
  source_credentials.update(self.cfg,{'source':'newsapi','env':'NEWSAPI_KEY','key':'FAKE_FIXTURE_ONLY'})
  with patch.dict(os.environ,{},clear=True),patch('urllib.request.OpenerDirector.open',return_value=Reply()) as call:
   rows=HttpJson(self.src).search('AI regulation',6);req=call.call_args[0][0]
   self.assertEqual(req.get_header('X-api-key'),'FAKE_FIXTURE_ONLY');self.assertNotIn('FAKE_FIXTURE_ONLY',req.full_url);self.assertEqual(rows[0]['authors'],['Fixture author']);self.assertEqual(rows[0]['venue'],'Fixture publisher')
 def test_presence_no_echo_remove_and_export_exclusion(self):
  source_credentials.update(self.cfg,{'source':'newsapi','env':'NEWSAPI_KEY','key':'FAKE_FIXTURE_ONLY'})
  status=source_credentials.status(self.cfg);self.assertTrue(status[0]['has_key']);self.assertNotIn('FAKE_FIXTURE_ONLY',json.dumps(status))
  self.cfg['_dir']=self.tmp.name;data,_=bundle(self.cfg)
  with zipfile.ZipFile(io.BytesIO(data)) as z:
   self.assertNotIn('FAKE_FIXTURE_ONLY',str([z.read(n) for n in z.namelist()]))
  source_credentials.update(self.cfg,{'source':'newsapi','env':'NEWSAPI_KEY','clear':True});self.assertFalse(source_credentials.status(self.cfg)[0]['has_key'])
 def test_undeclared_and_python_keys_rejected(self):
  with self.assertRaises(ValueError):source_credentials.update(self.cfg,{'source':'other','env':'NEWSAPI_KEY','key':'FAKE'})
  self.cfg['sources']=[{'id':'p','type':'python','label':'p','entry':'plugin:search','header_env':{'X-Api-Key':'NEWSAPI_KEY'}}]
  self.assertEqual(source_credentials.status(self.cfg),[])
 def test_saved_key_bound_to_destination(self):
  source_credentials.update(self.cfg,{'source':'newsapi','env':'NEWSAPI_KEY','key':'FAKE_FIXTURE_ONLY'})
  self.cfg['sources'][0]['url']='https://other.invalid/search?q={query}'
  with patch.dict(os.environ,{},clear=True):self.assertFalse(source_credentials.status(self.cfg)[0]['has_key'])
 def test_plain_http_credentials_rejected(self):
  self.cfg['sources'][0]['url']='http://example.test/search'
  with self.assertRaises(ValueError):source_credentials.status(self.cfg)
 def test_no_credential_redirect(self):
  from customchat.connectors.http_json import _NoCredentialRedirect
  with self.assertRaises(ValueError):_NoCredentialRedirect().redirect_request(None,None,302,'Found',{},'https://other.invalid')
 def test_error_payload_not_empty_success(self):
  source_credentials.update(self.cfg,{'source':'newsapi','env':'NEWSAPI_KEY','key':'FAKE_FIXTURE_ONLY'})
  with patch('urllib.request.OpenerDirector.open',return_value=Reply()),patch.object(Reply,'read',return_value=b'{"status":"error","message":"not exposed"}'):
   with self.assertRaises(ValueError):HttpJson(self.src).search('AI')
 def test_bad_mapping_rejected(self):
  source_credentials.update(self.cfg,{'source':'newsapi','env':'NEWSAPI_KEY','key':'FAKE_FIXTURE_ONLY'})
  with patch('urllib.request.OpenerDirector.open',return_value=Reply()),patch.object(Reply,'read',return_value=b'{"articles":{"wrong":"object"}}'):
   with self.assertRaises(ValueError):HttpJson(self.src).search('AI')
 def test_private_file_mode(self):
  source_credentials.update(self.cfg,{'source':'newsapi','env':'NEWSAPI_KEY','key':'FAKE_FIXTURE_ONLY'});self.assertEqual(os.stat(secrets.STORE.path).st_mode&0o777,0o600)
