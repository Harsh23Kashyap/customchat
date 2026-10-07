import unittest
from customchat.exports import pdf_bytes,answer_markdown
class Export(unittest.TestCase):
 def turn(self):return {'question':'Fiber?','answer':('Fiber answer [1].\n'*200)+'FINAL END','evidence':[{'n':1,'title':'A source','url':'https://example.invalid/source','document':'file.md','page':2,'version':'abc123'}],'owner':'secret-owner','chat':'secret-chat','profile':'private'}
 def test_markdown_snapshot_private(self):
  m=answer_markdown({'title':'Diet Chat'},self.turn());self.assertIn('abc123',m);self.assertIn('page 2',m);self.assertIn('FINAL END',m)
  for private in ['secret-owner','secret-chat','private']:self.assertNotIn(private,m)
 def test_multi_page_no_cut(self):
  b=pdf_bytes('Diet Chat',self.turn());self.assertIn(b'FINAL END',b);self.assertIn(b'abc123',b);self.assertGreater(b.count(b'/Type /Page '),1)
 def test_unicode_no_silent_loss(self):
  t=self.turn();t['answer']='नमस्ते'
  with self.assertRaises(ValueError):pdf_bytes('Chat',t)
  self.assertIn('नमस्ते',answer_markdown({'title':'Chat'},t))
 def test_accent_not_pdf_injection(self):self.assertIn(b'0.090 0.247 0.208',pdf_bytes('Chat',self.turn(),'bad-pdf'))
