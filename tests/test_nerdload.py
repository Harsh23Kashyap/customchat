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
  with self.assertRaisesRegex(ValueError,'Private file.*.env'):self.loader.review('d.zip',self.encoded({'.env':'secret','app.yaml':'{}'}))
 def test_yaml_without_documents_loads_empty_folder(self):
  d=self.loader.review('app.yaml',base64.b64encode(b'sources: [{id: docs, type: local_files, path: docs}]').decode())
  self.assertTrue(any('No documents included' in r['message'] for r in d['readiness']['rows']))
  r=self.loader.load(d['token']);self.assertTrue((Path(r['workspace'])/'docs').is_dir())
 def test_export_empty_source_roundtrip(self):
  (self.root/'docs').mkdir();cfg=schema.validate({'sources':[{'id':'docs','type':'local_files','path':'docs'}]});cfg['_dir']=str(self.root)
  data,_=bundle(cfg);d=self.loader.review('nerd.zip',base64.b64encode(data).decode());r=self.loader.load(d['token'])
  self.assertTrue((Path(r['workspace'])/'assets/source-1').is_dir())
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
 def test_stop_list_remove(self):
  (self.root/'docs').mkdir();(self.root/'docs/guide.md').write_text('Local evidence');cfg=schema.validate({'sources':[{'id':'guide','type':'local_files','path':'docs'}]});cfg['_dir']=str(self.root)
  data,_=bundle(cfg);d=self.loader.review('nerd.zip',base64.b64encode(data).decode());self.loader.load(d['token']);row=self.loader.list()[0];self.assertTrue(row['running']);self.loader.stop(row['id']);self.assertFalse(self.loader.list()[0]['running'])
  with self.assertRaises(ValueError):self.loader.remove(row['id'],False)
  folder=self.loader.workspaces[row['id']]['folder'];self.loader.remove(row['id'],True);self.assertFalse(folder.exists());self.assertEqual(self.loader.list(),[]);self.assertTrue((self.root/'docs/guide.md').exists())
 def test_discover_stopped(self):
  f=self.root/'nerds'/'nerd-saved';f.mkdir(parents=True);(f/'app.yaml').write_text('app: {title: Saved}')
  l=NerdLoader(self.root);self.assertEqual(l.list()[0]['title'],'Saved');self.assertFalse(l.list()[0]['running']);l.remove('nerd-saved',True)
 def test_bounded_import_default(self):
  d=self.loader.review('demo.zip',self.encoded({'app.yaml':'sources: [{id: p, type: python, entry: plugin:search}]','plugin.py':'def search(q,k):return []'}));cfg=self.loader.pending[d['token']][1];self.assertEqual(cfg['sources'][0]['execution'],'bounded');self.assertFalse(cfg['actions']['writes'])

 def test_static_preview_no_execution(self):
  import yaml
  raw=yaml.safe_dump({'app':{'title':'<img src=x onerror=alert(1)>','tagline':'Bundle tagline','examples':['Example question?']},'provider':{'type':'mock'},'sources':[]})
  d=self.loader.review('demo.zip',self.encoded({'app.yaml':raw}));self.assertTrue(d['preview']['static']);self.assertEqual(d['preview']['title'],'<img src=x onerror=alert(1)>');self.assertEqual(d['preview']['examples'],['Example question?']);self.assertEqual(self.loader.list(),[])

 def test_benign_dotfiles_skipped(self):
  d=self.loader.review('demo.zip',self.encoded({'Nerd/app.yaml':'{}','Nerd/.gitignore':'data/','Nerd/.github/workflows/test.yml':'{}','Nerd/.DS_Store':'x','Nerd/__MACOSX/._doc':'x'}))
  self.assertEqual(d['preview']['files'],['app.yaml'])
 def test_secrets_in_ignored_metadata_still_rejected(self):
  for name in ['.env.local','.env.example','.ssh/id_rsa','.aws/config','.pypirc','.github/.env','__MACOSX/.env','credentials.json']:
   with self.subTest(name=name),self.assertRaisesRegex(ValueError,'Private file.*'+name.replace('.','\\.')):
    self.loader.review('d.zip',self.encoded({'app.yaml':'{}',name:'secret'}))
 def test_unknown_dotfile_named(self):
  with self.assertRaisesRegex(ValueError,'Unsupported hidden file: .private'):
   self.loader.review('d.zip',self.encoded({'app.yaml':'{}','.private':'x'}))
 def test_source_archive_explained(self):
  with self.assertRaisesRegex(ValueError,'CustomChat source ZIP, not a Nerd bundle'):
   self.loader.review('source.zip',self.encoded({'customchat/.gitignore':'x','customchat/pyproject.toml':'x','customchat/customchat/__init__.py':'x','customchat/customchat/accounts.py':'x'}))
