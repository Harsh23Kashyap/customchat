from pathlib import Path
import tempfile,unittest
from customchat.prompts import PromptStore
class PromptPresentation(unittest.TestCase):
 def test_revise_config_default_and_explicit_override(self):
  with tempfile.TemporaryDirectory() as d:
   p=PromptStore(d)
   for default in [False,True]:self.assertEqual(next(s for s in p.view('answer',default) if s['key']=='revise')['on'],default)
   p.save('revise',on=False);self.assertFalse(next(s for s in p.view('answer',True) if s['key']=='revise')['on'])
   p.save('revise',on=True);self.assertTrue(next(s for s in p.view('answer',False) if s['key']=='revise')['on'])
 def test_all_stage_text_survives_reload(self):
  from customchat.prompts import STAGES
  with tempfile.TemporaryDirectory() as d:
   p=PromptStore(d)
   for key in STAGES:p.save(key,text='BEGIN '+key+'\n'+'words '*400+'END '+key)
   loaded=PromptStore(d).view('fallback')
   for s in loaded:self.assertTrue(s['text'].startswith('BEGIN '+s['key']));self.assertTrue(s['text'].endswith('END '+s['key']))
 def test_menu_only_reset_and_theme_svg(self):
  w=Path(__file__).resolve().parents[1]/'customchat/web'
  s=(w/'settings.html').read_text();self.assertIn('floating-more',s);self.assertIn('aria-label="More look actions"',s)
  self.assertIn('.doc-scene .doc-spark rect{fill:var(--lime)}',(w/'style.css').read_text())
