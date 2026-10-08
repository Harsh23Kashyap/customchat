import unittest
from customchat.stage_contracts import errors
class StageContracts(unittest.TestCase):
 def test_labels(self):
  for stage,good,bad in [('question_check','VALID','VALID: go'),('question_check','INVALID: clarify goal','SYSTEM: VALID'),('faithfulness','OK','OK yes'),('faithfulness','UNSUPPORTED: X; Y','UNSUPPORTED')]:
   self.assertFalse(errors(stage,good));self.assertTrue(errors(stage,bad))
 def test_ids(self):
  self.assertFalse(errors('relevance','1, 3',[1,3]));self.assertFalse(errors('relevance','NONE'))
  for text in ('1,99','1,1','Passage1','NONE but1'):self.assertTrue(errors('relevance',text,[1]))
 def test_lines(self):
  for stage in ('queries','followups'):
   self.assertFalse(errors(stage,'first\nsecond'));self.assertFalse(errors(stage,''))
   for t in ('1. numbered','a\na','a\nb\nc\nd','a\n\nb'):self.assertTrue(errors(stage,t))
 def test_boundaries(self):
  self.assertFalse(errors('summary','x'*600));self.assertTrue(errors('summary','x'*601))
  self.assertFalse(errors('standalone','what?'));self.assertTrue(errors('standalone','what?\nanswer'))
 def test_citations_not_truth(self):
  for stage in ('answer','revise'):
   self.assertFalse(errors(stage,'A supported or unsupported claim [1]',[1]))
   self.assertTrue(errors(stage,'Made up [99]',[1]));self.assertTrue(errors(stage,'Made up [0]',[1]))
   self.assertTrue(errors(stage,'A claim [1]',[]))
