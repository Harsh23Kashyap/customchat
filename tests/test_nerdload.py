import base64,io,tempfile,unittest,zipfile
from pathlib import Path
from customchat.nerdload import NerdLoader
from customchat import schema
from customchat.portable import bundle
class NerdLoadTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.loader=NerdLoader(self.root);self.addCleanup(self.loader.close)
 def encoded(self,files):
  out=io.BytesIO()
  with zipfile.ZipFile(out,'w') as z:
   for n,d in files.items():z.writestr(n,d)
  return base64.b64encode(out.getvalue()).decode()
 def test_review_does_not_run_python(self):
  cfg='sources: [{id: plugin, type: python, entry: example:search}]'
  d=self.loader.review('demo.zip',self.encoded({'app.yaml':cfg,'example.py':'raise RuntimeError("must not execute")'}));self.assertEqual(len(d['code']),1)
  with self.assertRaisesRegex(ValueError,'Review Python'):self.loader.load(d['token'])
 def test_path_traversal(self):
  with self.assertRaisesRegex(ValueError,'Unsafe path'):self.loader.review('d.zip',self.encoded({'../bad.txt':'x','app.yaml':'{}'}))
 def test_env_rejected(self):
  with self.assertRaisesRegex(ValueError,'Hidden'):self.loader.review('d.zip',self.encoded({'.env':'secret','app.yaml':'{}'}))
 def test_missing_source(self):
  with self.assertRaisesRegex(ValueError,'Missing local'):self.loader.review('app.yaml',base64.b64encode(b'sources: [{id: docs, type: local_files, path: docs}]').decode())
 def test_inline_secret_rejected(self):
  raw=b'sources: [{id: x, type: http_json, url: "https://a.example/?token=secret"}]'
  with self.assertRaises(ValueError):self.loader.review('app.yaml',base64.b64encode(raw).decode())
 def test_local_roundtrip_start(self):
  (self.root/'docs').mkdir();(self.root/'docs/guide.md').write_text('Local evidence');cfg=schema.validate({'app':{'title':'Loaded Nerd'},'sources':[{'id':'guide','type':'local_files','path':'docs'}]});cfg['_dir']=str(self.root)
  data,_=bundle(cfg);d=self.loader.review('nerd.zip',base64.b64encode(data).decode());r=self.loader.load(d['token']);self.assertTrue(r['url'].startswith('http://127.0.0.1:'));self.assertEqual(r['title'],'Loaded Nerd')
 def test_missing_python(self):
  with self.assertRaisesRegex(ValueError,'missing'):self.loader.review('app.yaml',base64.b64encode(b'sources: [{id: x, type: python, entry: absent:search}]').decode())
 def test_auth_not_silently_replaced(self):
  with self.assertRaisesRegex(ValueError,'auth.mode'):self.loader.review('app.yaml',base64.b64encode(b'auth: {mode: accounts}').decode())
