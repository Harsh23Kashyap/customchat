import unittest
from unittest.mock import patch
from customchat import bundle_review as b,schema
class BundleReviewTests(unittest.TestCase):
 def review(self,code):return b.review(schema.validate({}),{'plugin.py':code.encode(),'app.yaml':b'{}'})
 def test_patterns_and_lines(self):
  r=self.review('import os, urllib.request, subprocess\ndef search(q,k):\n key=os.environ.get("KEY")\n urllib.request.urlopen(q)\n open(q)\n subprocess.run(q)\n eval(q)')
  self.assertEqual(r['python_files'],1);self.assertEqual(r['functions'],1);self.assertIn('os',r['imports'])
  for category in ('network','environment','files','process','dynamic'):self.assertGreater(r['counts'][category],0)
  self.assertTrue(all(f['path']=='plugin.py' and f['line']>0 for f in r['findings']))
 def test_no_execution_or_secret_access(self):
  with patch('urllib.request.urlopen',side_effect=AssertionError('network')),patch('os.getenv',side_effect=AssertionError('env')):
   r=self.review('raise Exception("do not execute")\nimport os\nx=os.getenv("SECRET")')
  self.assertEqual(r['counts']['environment'],1);self.assertNotIn('SECRET',str(r));self.assertTrue(r['static'])
 def test_empty_not_safe(self):
  r=self.review('def search(q,k):return []');self.assertFalse(r['counts']);self.assertIn('does not mean absent or safe',r['limits'])
 def test_unparsed_and_caps(self):
  self.assertEqual(self.review('def broken(')['counts']['unparsed'],1)
  r=self.review('\n'.join('open("x")' for _ in range(100)));self.assertEqual(r['counts']['files'],100);self.assertEqual(len(r['findings']),80);self.assertTrue(r['truncated'])
 def test_only_names_not_literals(self):
  r=self.review('text="open getenv urlopen run"');self.assertFalse(r['findings'])
 def test_static_limit_aliases(self):
  r=self.review('from os import system as alias\nalias("x")');self.assertFalse(r['counts']);self.assertIn('Aliases',r['limits']);self.assertIn('os',r['imports'])
