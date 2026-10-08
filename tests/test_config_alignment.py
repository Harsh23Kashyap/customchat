import unittest
from pathlib import Path
class ConfigAlignment(unittest.TestCase):
 def test_setup_rows_have_dedicated_layout(self):
  js=(Path(__file__).parents[1]/'customchat/web/workspace.js').read_text()
  self.assertIn("workspace-row workspace-status-row",js)
 def test_label_columns_and_mobile_stack(self):
  css=(Path(__file__).parents[1]/'customchat/web/settings.css').read_text()
  self.assertIn('grid-template-columns:minmax(0,1fr)',css)
  self.assertIn('@media(max-width:760px){.workspace-status-row{grid-template-columns:minmax(0,1fr)',css)
 def test_action_links_not_inline_underlined(self):
  css=(Path(__file__).parents[1]/'customchat/web/settings.css').read_text()
  self.assertIn('a.go{display:inline-flex;align-items:center;justify-content:center;text-align:center;text-decoration:none',css)
  self.assertIn('.keyrow>a.go{height:auto;min-height:44px',css)

 def test_setup_details_are_disclosed_on_demand(self):
  js=(Path(__file__).parents[1]/'customchat/web/workspace.js').read_text()
  self.assertIn("Check details and limits",js)
  self.assertIn("Local checks only. Live services have not been tested.",js)
