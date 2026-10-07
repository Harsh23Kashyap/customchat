import unittest
from customchat.theme import clean
class BrandTests(unittest.TestCase):
    def test_watermark_default_and_save(self):
        self.assertFalse(clean({})['logo_watermark'])
        self.assertTrue(clean({'logo_watermark':True})['logo_watermark'])
    def test_svg_is_not_accepted_as_logo(self):
        self.assertEqual(clean({'logo':'data:image/svg+xml,<svg onload=alert(1)>'})['logo'],'')
