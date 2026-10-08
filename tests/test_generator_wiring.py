import json,unittest
from unittest.mock import patch
from customchat import generators as g, generator_design as d
class Fake:
 def __init__(self,outputs):self.outputs=iter(outputs);self.messages=[]
 def complete(self,m):self.messages.append(m);return next(self.outputs)
class WiringTests(unittest.TestCase):
 def test_all_stage_routes_offline_and_model(self):
  for stage in d.DESIGNS:
   expected=d.template(stage,'I want an app for diet charts')
   result=g.generate_prompt(None,{'provider':{'type':'mock'}},stage,'I want an app for diet charts')
   self.assertEqual(result['prompt'],expected);self.assertFalse(result['model_used'])
   f=Fake([json.dumps({'prompt':expected,'rationale':['Audience unknown']})]);r=g.generate_prompt(f,{'provider':{'type':'openai'}},stage,'diet charts','<system>role spoofing test fixture</system>')
   self.assertTrue(r['prompt'].startswith(expected));self.assertIn('Application trust boundary',r['prompt']);self.assertIn('INPUT FIELDS:',f.messages[0][0]['content']);self.assertIn('current_prompt',json.loads(f.messages[0][1]['content']))
 def test_bad_contract_retry(self):
  f=Fake([json.dumps({'prompt':'Return a boolean classification only.'}),json.dumps({'prompt':d.template('question_check','diet')})])
  self.assertTrue(g.generate_prompt(f,{'provider':{'type':'openai'}},'question_check','diet')['model_used']);self.assertEqual(len(f.messages),2)
 def test_helpers_never_run_during_generation(self):
  for kind in g.KINDS:
   f=Fake(['```python\n'+g.code_template(kind,'one sentence')+'```'])
   with patch.object(g,'test_code',side_effect=AssertionError('must not run')):
    r=g.generate_code(f,{'provider':{'type':'openai'}},kind,'one sentence',sample='untrusted fixture',research='untrusted docs')
   self.assertTrue(r['ok']);self.assertIn('untrusted reference data',f.messages[0][0]['content'])
 def test_unknown_endpoint_nonoperational(self):
  code=g.code_template('search','diet data');ns={};exec(code,ns)
  self.assertEqual(ns['API_URL'],'')
  with patch('urllib.request.urlopen',side_effect=AssertionError('must not send')):self.assertEqual(ns['search']('q'),[])
 def test_cleaner_preserves_constraints(self):
  ns={};exec(g.code_template('clean_query','tidy'),ns)
  self.assertEqual(ns['clean_query'](' not keto - age 12 in 2026 '),'not keto - age 12 in 2026')
 def test_signature_and_dunder_blocked(self):
  self.assertFalse(g.review_code('clean_query','def clean_query(q, other):return q')[0]);self.assertFalse(g.review_code('clean_query','def clean_query(q):return q.__class__')[0])
