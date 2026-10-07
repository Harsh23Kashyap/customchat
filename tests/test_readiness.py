import unittest
from customchat import schema
from customchat.readiness import check
class ReadinessTests(unittest.TestCase):
 def test_partial_uses_defaults(self):
  raw={'app':{'title':'Partial'}};r=check(schema.validate(raw),provided=raw);self.assertTrue(r['can_load']);self.assertTrue(any(x['kind']=='default' for x in r['rows']))
 def test_ollama_explicitly_unchecked(self):
  r=check(schema.validate({'provider':{'type':'ollama','model':'qwen2.5:3b'}}));self.assertTrue(any('Not checked' in x['message'] for x in r['rows']))
 def test_python_key_names(self):
  cfg=schema.validate({'sources':[{'id':'news','type':'python','entry':'news:search'}]});r=check(cfg,{'news.py':b'import os\nKEY=os.getenv("GNEWS_API_KEY")'});self.assertIn('GNEWS_API_KEY',r['required_env'])
 def test_bad_python_blocks(self):
  cfg=schema.validate({'sources':[{'id':'news','type':'python','entry':'news:search'}]});r=check(cfg,{'news.py':b'def broken('});self.assertFalse(r['can_load'])
