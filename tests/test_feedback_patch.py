from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
class FeedbackPatch(unittest.TestCase):
 def test_settings_groups_with_helper_loader(self):
  html=(R/'customchat/web/settings.html').read_text();js=(R/'customchat/web/settings.js').read_text()
  self.assertIn('src="/pipeline.js"',html);self.assertNotIn('src="/codeeditor.js"',html)
  for x in ('Start and share','Answers and sources','Appearance','Usage and maintenance','Sources and APIs'):self.assertIn(x,js)
 def test_real_assets_and_package(self):
  files=list((R/'customchat/web/emoji').glob('*.webp'));self.assertEqual(len(files),17)
  for p in files:
   self.assertIn(b"ANIM",p.read_bytes());self.assertGreater(p.read_bytes().count(b"ANMF"),1)
   self.assertTrue(p.with_suffix('.png').exists())
  self.assertIn('web/emoji/*',(R/'pyproject.toml').read_text())
 def test_preview_and_logo_regressions(self):
  s=(R/'customchat/web/settings.js').read_text()
  for x in ('readAsDataURL','ccPreviewMotion','testLog.unshift','detail:message','Suggested local models'):self.assertIn(x,s)
  self.assertNotIn('motion-sample',s)
 def test_disclosures_are_not_height_clipped(self):
  s=(R/'customchat/web/settings.css').read_text()
  self.assertIn('details::details-content{block-size:auto!important',s)
  self.assertIn('#pv{pointer-events:none}',s)
