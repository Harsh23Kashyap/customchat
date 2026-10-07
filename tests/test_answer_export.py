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

 def test_branded_template_fonts_paper_and_metadata(self):
  b=pdf_bytes('Diet Chat',self.turn())
  self.assertIn(b'/BaseFont /Times-Roman',b)
  self.assertIn(b'/BaseFont /Helvetica-Bold',b)
  self.assertIn(b'0.973 0.957 0.914 rg 0 0 595 842 re f',b)
  self.assertIn(b'Sources at answer time',b)
  self.assertIn('## Sources at answer time',answer_markdown({'title':'Chat'},self.turn()))
 def test_wide_unbroken_text_preserved(self):
  t=self.turn();t['answer']='W'*240+' END WIDE';t['question']='W'*90
  b=pdf_bytes('Chat',t)
  self.assertIn(b'END WIDE',b)
  import re
  lines=re.findall(rb'\(([^()]*)\) Tj',b)
  self.assertTrue(any(b'W' in row for row in lines))
  self.assertLessEqual(max(len(row) for row in lines if b'WW' in row),70)
