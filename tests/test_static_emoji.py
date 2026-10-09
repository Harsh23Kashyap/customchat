import json,re,unittest
from pathlib import Path
class StaticEmojiTests(unittest.TestCase):
 def test_picker_and_demo_assets_present(self):
  w=Path(__file__).resolve().parents[1]/'customchat/web';s=(w/'emoji.js').read_text();mapping=json.loads(s.split('staticAssets:',1)[1].split(',node:',1)[0]);self.assertEqual(len(mapping),80)
  for name in mapping.values():
   data=(w/'emoji'/(name+'.png')).read_bytes();self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n');self.assertGreater(len(data),500)
  for e in ['📰','🙂','🔎','📎','⏱️','🧑‍💻','🧑‍🚀']:self.assertIn(e,mapping)
 def test_static_not_animated_and_unknown_keeps_text(self):
  s=(Path(__file__).resolve().parents[1]/'customchat/web/emoji.js').read_text();self.assertIn('if(!f)return document.createTextNode(e)',s);self.assertIn("image.src='/emoji/'+f+'.png'",s);self.assertIn("quiet?'.png':'.webp'",s)
