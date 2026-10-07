from pathlib import Path
import unittest

WEB = Path(__file__).parents[1] / 'customchat/web'


class WebReachabilityTests(unittest.TestCase):
    def test_pipeline_is_loaded_and_registered(self):
        self.assertIn('src="/pipeline.js"', (WEB / 'settings.html').read_text())
        js = (WEB / 'settings.js').read_text()
        self.assertIn('["prompts","Prompts"]', js)
        self.assertIn('["code","Code helpers"]', js)
        css = (WEB / 'settings.css').read_text()
        self.assertIn('body.simple #sec-code{display:block!important}', css)

    def test_collapsing_does_not_reopen_for_selected_provider(self):
        js = (WEB / 'settings.js').read_text()
        self.assertNotIn('if (rest.includes(cur.provider)) chipsMore = true', js)
        self.assertIn('let chipsMore = false', js)

    def test_default_icon_and_team_are_packaged(self):
        config = (WEB.parents[1] / 'pyproject.toml').read_text()
        for item in ['web/icons/*.svg', 'web/team/*.jpg']:
            self.assertIn(item, config)
        self.assertTrue((WEB / 'icons/customchat.svg').is_file())
        for name in ['harsh', 'dennis']:
            self.assertTrue((WEB / ('team/' + name + '.jpg')).is_file())
