import tempfile,unittest,json
from pathlib import Path
from customchat.configdoctor import inspect,editor_schema
class ConfigDoctor(unittest.TestCase):
 def check(self,text):
  with tempfile.TemporaryDirectory() as p:
   f=Path(p)/'app.yaml';f.write_text(text);return inspect(f)
 def test_good(self):self.assertFalse(self.check('provider: {type: mock}\n')[0])
 def test_line_typo(self):
  i,_=self.check('app:\n  title: Test\nprovider:\n  temperture: 0.2\n');self.assertEqual(i[0]['line'],4);self.assertIn('temperature',i[0]['suggestion'])
 def test_bad_shape(self):self.assertTrue(self.check('provider: no\n')[0])
 def test_bool_number(self):self.assertTrue(self.check('retrieval: {top_k: true}')[0])
 def test_duplicate(self):self.assertIn('Duplicate',self.check('app: {}\napp: {}')[0][0]['message'])
 def test_syntax_hides_secret(self):
  i,_=self.check('provider: [secret-value');self.assertNotIn('secret-value',str(i))
 def test_secret_key(self):
  i,_=self.check('provider: {api_key: secret-value}');self.assertNotIn('secret-value',str(i));self.assertTrue(i)
 def test_missing_model(self):self.assertEqual(self.check('provider: {type: ollama}')[0][0]['key'],'provider.model')
 def test_custom_style(self):self.assertFalse(self.check('prompt: {style: {tiny: Short}}')[0])
 def test_schema_serializable(self):self.assertIn('properties',json.loads(json.dumps(editor_schema())))
 def test_fallback_shape(self):self.assertTrue(self.check('provider: {fallback: broken}')[0])
 def test_no_env_loaded(self):
  import os
  with tempfile.TemporaryDirectory() as p:
   f=Path(p)/'app.yaml';f.write_text('{}');(Path(p)/'.env').write_text('DOCTOR_NO_READ=secret')
   inspect(f);self.assertNotIn('DOCTOR_NO_READ',os.environ)
 def test_all_apps(self):
  for f in Path('apps').glob('*/app.yaml'):self.assertFalse(inspect(f)[0],str(f))
