import unittest
from customchat import theme

class LightDefault(unittest.TestCase):
 def test_missing_mode_defaults_light(self):
  self.assertEqual(theme.clean({})['mode'],'light')
  self.assertEqual(theme.clean({'mode':'invalid'})['mode'],'light')
 def test_explicit_saved_choices_preserved(self):
  for mode in ('dark','light','auto'):
   self.assertEqual(theme.clean({'mode':mode})['mode'],mode)
