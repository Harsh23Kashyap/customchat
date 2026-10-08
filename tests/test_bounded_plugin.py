import tempfile,unittest,os
from pathlib import Path
from customchat.connectors.bounded import BoundedPlugin
class BoundedTests(unittest.TestCase):
 def test_result_and_env(self):
  with tempfile.TemporaryDirectory() as d:
   Path(d,'plug.py').write_text('import os\ndef search(q,k):\n return [{"title":q,"text":str(os.getenv("TEST_PRIVATE_KEY"))}]\n')
   os.environ['TEST_PRIVATE_KEY']='must-not-leak'
   try:r=BoundedPlugin({'id':'x','label':'x','entry':'plug:search'},d).search('hello',2);self.assertEqual(r[0]['text'],'None');self.assertEqual(r[0]['source'],'x')
   finally:os.environ.pop('TEST_PRIVATE_KEY')
 def test_failure_redacted(self):
  with tempfile.TemporaryDirectory() as d:
   Path(d,'plug.py').write_text('raise RuntimeError("secret-value")')
   with self.assertRaisesRegex(ValueError,'Connector failed') as e:BoundedPlugin({'id':'x','label':'x','entry':'plug:search'},d).search('q',2)
   self.assertNotIn('secret-value',str(e.exception))
 def test_wrong_result(self):
  with tempfile.TemporaryDirectory() as d:
   Path(d,'plug.py').write_text('def search(q,k):return ["bad"]')
   with self.assertRaises(ValueError):BoundedPlugin({'id':'x','label':'x','entry':'plug:search'},d).search('q',2)
 def test_environment_allowlist(self):
  with tempfile.TemporaryDirectory() as d:
   Path(d,'plug.py').write_text('import os\ndef search(q,k):\n return [{"text":str(os.getenv("PRIVATE_SESSION_VALUE"))}]')
   os.environ['PRIVATE_SESSION_VALUE']='no'
   try:self.assertEqual(BoundedPlugin({'id':'x','label':'x','entry':'plug:search'},d).search('q',2)[0]['text'],'None')
   finally:os.environ.pop('PRIVATE_SESSION_VALUE')
 def test_result_limit(self):
  with tempfile.TemporaryDirectory() as d:
   Path(d,'plug.py').write_text('def search(q,k):return [{"text":"x"*3000000}]')
   with self.assertRaises(ValueError):BoundedPlugin({'id':'x','label':'x','entry':'plug:search'},d).search('q',1)
 def test_timeout_kills(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   Path(d,'plug.py').write_text('import time\ndef search(q,k):time.sleep(20);return []')
   with patch('time.monotonic',side_effect=[0,21]):
    with self.assertRaisesRegex(ValueError,'time/output'):BoundedPlugin({'id':'x','label':'x','entry':'plug:search'},d).search('q',1)
