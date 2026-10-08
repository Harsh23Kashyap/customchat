import unittest,tempfile,json
from pathlib import Path
from customchat import schema,theme
from customchat.pipeline import Engine
from customchat.store import Store
class Hydration(unittest.TestCase):
 def engine(self,sources):
  cfg=schema.validate({'provider':{'type':'mock'},'sources':sources,'storage':{'path':':memory:'}})
  return Engine(cfg,Store(':memory:'),connectors={})
 def test_named_catalog(self):self.assertEqual(self.engine([{'id':'papers','type':'pubmed'}]).catalog_state(),['pubmed'])
 def test_many_named_catalogs(self):self.assertEqual(self.engine([{'id':'a','type':'arxiv'},{'id':'b','type':'wikipedia'}]).catalog_state(),['arxiv','wikipedia'])
 def test_named_web(self):self.assertEqual(self.engine([{'id':'research','type':'web_search','providers':['parallel']}]).web_state(),{'on':True,'providers':['parallel']})
 def test_many_web_sources(self):self.assertEqual(self.engine([{'id':'a','type':'web_search','provider':'tavily'},{'id':'b','type':'web_search','providers':['exa','tavily']}]).web_state()['providers'],['tavily','exa'])
 def test_catalog_disable(self):
  e=self.engine([{'id':'papers','type':'pubmed'}]);e.set_catalog([]);self.assertEqual(e.catalog_state(),[])
 def test_catalog_preserves_fields(self):
  e=self.engine([{'id':'papers','type':'pubmed','email':'reader@example.invalid'}]);e.set_catalog(['pubmed']);self.assertEqual(e.cfg['sources'][0]['email'],'reader@example.invalid');self.assertEqual(e.cfg['sources'][0]['id'],'papers')
 def test_web_disable(self):
  e=self.engine([{'id':'research','type':'web_search','providers':['parallel']}]);e.set_web(False,[]);self.assertFalse(e.web_state()['on'])
 def test_app_branding(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(theme.ThemeStore(d,{'accent':'#123456','accent2':'#654321','theme':'dark'}).value['light']['brand'],'#123456')
 def test_partial_theme(self):
  with tempfile.TemporaryDirectory() as d:
   Path(d,'theme.json').write_text(json.dumps({'font_size':130,'light':{'bg':'#ffffff'}}));t=theme.ThemeStore(d,{'accent':'#123456'}).value;self.assertEqual(t['font_size'],130);self.assertEqual(t['light']['brand'],'#123456');self.assertEqual(t['light']['bg'],'#ffffff')
 def test_saved_theme_wins(self):
  with tempfile.TemporaryDirectory() as d:
   Path(d,'theme.json').write_text(json.dumps({'light':{'brand':'#abcdef'},'mode':'light'}));t=theme.ThemeStore(d,{'accent':'#123456','theme':'dark'}).value;self.assertEqual(t['light']['brand'],'#abcdef');self.assertEqual(t['mode'],'light')
 def test_custom_nested_fields(self):self.assertEqual(schema.validate({'app':{'audience':'Researchers'}})['app']['audience'],'Researchers')
 def test_raw_dump_removed(self):
  p=Path(__file__).parent.parent/'customchat/web/configstate.js';s=p.read_text();self.assertNotIn('allConfigFields',s);self.assertIn('Configured sources and custom API fields',s)
