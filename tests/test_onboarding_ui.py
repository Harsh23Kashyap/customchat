from pathlib import Path
import unittest
class OnboardingUI(unittest.TestCase):
 def test_plain_demo_and_real_setup_paths(self):
  w=Path(__file__).resolve().parents[1]/'customchat/web';s=(w/'app.js').read_text()
  for text in ('Demo · offline','Start here','How do I add my documents?','How do I connect an AI model?','How do I change the reading view?','How do I try an action?'):self.assertIn(text,s)
  self.assertIn('if (PREVIEW || S.temp) return null',s)
 def test_tools_below_input(self):
  s=(Path(__file__).resolve().parents[1]/'customchat/web/index.html').read_text()
  self.assertGreater(s.index('id="scopeBtn"'),s.index('id="q"'))
  self.assertIn('aria-label="Question tools"',s)
 def test_preview_and_nested_logo_packaging(self):
  r=Path(__file__).resolve().parents[1];s=(r/'customchat/web/app.js').read_text()
  self.assertIn('document.body.inert = true',s)
  self.assertIn('if (PREVIEW) return;',s)
  self.assertIn('web/logos/*.svg',(r/'pyproject.toml').read_text())
 def test_theme_switch_and_preset_palette(self):
  css=(Path(__file__).resolve().parents[1]/'customchat/web/settings.css').read_text()
  self.assertNotIn('background:linear-gradient(135deg,#f3efe3 0 50%,#173f35 50% 78%,#9bb8a5 78%)!important',css)
  self.assertIn('html body .seg.mini button[aria-checked=true]',css)

 def test_designed_status_and_picker(self):
  s=(Path(__file__).resolve().parents[1]/'customchat/web/settings.js').read_text()
  for term in ('status-card','source.documents===1','Usage day:','emojiControl','dialog.showModal()','ccPreviewMotion','prefers-reduced-motion:reduce'):
   self.assertIn(term,s)
 def test_compact_fields_and_dropdown_layer(self):
  s=(Path(__file__).resolve().parents[1]/'customchat/web/settings.css').read_text()
  for term in ('.col .tile:has(.cs.open)','.rangerow>.rng','.field>.flabel','.emoji-dialog'):
   self.assertIn(term,s)
