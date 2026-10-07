import unittest
from pathlib import Path
W=Path(__file__).resolve().parents[1]/'customchat/web'
class Reading(unittest.TestCase):
 def test_bounds_and_local_prefs(self):
  s=(W/'reading.js').read_text();self.assertIn('[600,720,900]',s);self.assertIn('[15,17,19,21]',s);self.assertIn('localStorage.setItem',s);self.assertNotIn('fetch(',s)
 def test_keep_scroll_when_reading_earlier(self):
  s=(W/'app.js').read_text();self.assertIn('keep ? priorScroll',s);self.assertIn('if (follow) th.scrollTop',s)
 def test_accessible_dialog_and_focus(self):
  s=(W/'reading.js').read_text();self.assertIn('dialog.showModal()',s);self.assertIn('button.focus()',s)
