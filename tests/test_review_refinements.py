"""Bounded visual refinements, with browser pixel checks alongside this contract."""
from pathlib import Path
import unittest
class ReviewRefinements(unittest.TestCase):
 def test_motion_and_accessible_status(self):
  web=Path(__file__).resolve().parents[1]/'customchat/web'
  css=(web/'style.css').read_text(); app=(web/'app.js').read_text(); settings=(web/'settings.js').read_text()
  self.assertIn('prefers-reduced-motion:no-preference',css)
  self.assertIn('html[data-motion] *::after{transition:none!important;transition-duration:0s!important',css)
  self.assertIn('html.preview:not([data-motion=none])',css)
  self.assertIn('["calm","none"].includes(t.motion)',settings)
  self.assertIn('["calm","none"].includes(theme.motion)',settings)
  self.assertIn('if(trigger?.classList.contains("cite"))',app)
  self.assertIn('result ? "Reply ready"',app)
 def test_original_palette_and_scoped_modal(self):
  css=(Path(__file__).resolve().parents[1]/'customchat/web/style.css').read_text().split('/* Reviewed hierarchy')[1]
  self.assertNotIn('#d97706',css)
  self.assertIn('#readingDialog{width:390px}',css)
  self.assertIn('background:var(--soft)',css)
  self.assertIn('html.preview .thread:has(.hero){display:block}',css)
