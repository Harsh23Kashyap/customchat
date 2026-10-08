import unittest,time
from customchat.workspace import Reviews,archive,validate_archive,SettingsHistory
from customchat.store import Store
class WorkspaceTests(unittest.TestCase):
 def test_owner_bound(self):
  r=Reviews();t=r.put('a','backup',[1])
  with self.assertRaises(ValueError):r.take('b','backup',t,True)
  self.assertEqual(r.take('a','backup',t,True),[1])
  with self.assertRaises(ValueError):r.take('a','backup',t,True)
 def test_confirm_required(self):
  r=Reviews();t=r.put('a','x',{})
  with self.assertRaises(ValueError):r.take('a','x',t,False)
 def test_roundtrip(self):self.assertEqual(validate_archive(archive([{'title':'a','turns':[{'question':'q','answer':'a','evidence':[]}]}]))[0]['turns'][0]['question'],'q')
 def test_private_fields_rejected(self):
  a=archive([]);a['password']='x'
  with self.assertRaises(ValueError):validate_archive(a)
 def test_evidence_shape(self):
  with self.assertRaises(ValueError):validate_archive(archive([{'turns':[{'question':'q','answer':'a','evidence':['x']}]}]))
 def test_history_owner_and_diff(self):
  s=Store(':memory:');h=SettingsHistory(s);n=h.record('a',{'model':'old'});self.assertEqual(h.compare('a',n,{'model':'new'})[1][0]['restore'],'old');self.assertEqual(h.list('b'),[])
 def test_history_bounded(self):
  h=SettingsHistory(Store(':memory:'))
  for i in range(35):h.record('a',{'model':str(i)})
  self.assertEqual(len(h.list('a')),30)
