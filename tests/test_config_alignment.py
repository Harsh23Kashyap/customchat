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

 def test_navigation_does_not_hide_sections(self):
  js=(Path(__file__).parents[1]/'customchat/web/settings.js').read_text()
  follow=js.split('function pvFollow() {',1)[1].split('const m = activeSec',1)[0]
  self.assertNotIn('editing-pipeline',follow)
  self.assertNotIn('loading-nerd',follow)
  self.assertNotIn('section.hidden',follow) # editor placement may change, sections stay continuous
 def test_editors_live_in_their_sections(self):
  js=(Path(__file__).parents[1]/'customchat/web/pipeline.js').read_text()
  self.assertIn('section.append(list, pane)',js)
  self.assertIn('id:kind+"Editor"',js)
  self.assertNotIn('$(".layout").append(pane)',js)
 def test_export_has_dedicated_card(self):
  html=(Path(__file__).parents[1]/'customchat/web/settings.html').read_text()
  self.assertIn('class="export-card"',html)
  self.assertIn('Share this Nerd',html)

 def test_bundle_review_has_one_preview_and_full_content_width(self):
  css=(Path(__file__).parents[1]/'customchat/web/settings.css').read_text()
  self.assertIn('body:has(#nerdReview .import-grid) #pvbox,body:has(#nerdReview .import-grid) #pvfab{display:none!important}',css)
  self.assertIn('body:has(#nerdReview .import-grid) #col{min-width:0;width:100%;max-width:none}',css)
  self.assertIn('.import-preview{position:static;max-height:none;overflow:visible}',css)
  self.assertIn('#nerdReview{scroll-margin-top:24px}',css)
