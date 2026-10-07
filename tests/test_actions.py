import unittest
from customchat.actions import Actions
from customchat.schema import validate,ConfigError
from customchat.store import Store
class ActionTests(unittest.TestCase):
 def setUp(self):self.s=Store(':memory:');self.cfg=validate({});self.a=Actions(self.cfg,self.s)
 def test_all_registered_default(self):self.assertEqual(len(self.a.catalog()),2)
 def test_exact_fields(self):
  for args in [{},{'title':'x','text':'y','url':'bad'}]:
   with self.assertRaises(ValueError):self.a.prepare('a','save_note',args)
 def test_owner_bound(self):
  p=self.a.prepare('a','save_note',{'title':'t','text':'x'})
  with self.assertRaises(ValueError):self.a.execute('b',p['ticket'])
 def test_one_use_and_no_prepare_effect(self):
  p=self.a.prepare('a','save_note',{'title':'t','text':'x'});self.assertFalse(any(n.startswith('note-') for n in self.s.states('a')))
  self.assertTrue(self.a.execute('a',p['ticket'])['saved'])
  with self.assertRaises(PermissionError):self.a.execute('a',p['ticket'])
 def test_revoke(self):
  p=self.a.prepare('a','list_notes',{});self.cfg['actions']['allow']=[]
  with self.assertRaises(PermissionError):self.a.execute('a',p['ticket'])
 def test_expire(self):
  p=self.a.prepare('a','list_notes',{});v=self.s.get_state('a','action-'+p['ticket']);v['expires']=0;self.s.save_state('a','action-'+p['ticket'],v)
  with self.assertRaises(PermissionError):self.a.execute('a',p['ticket'])
 def test_writes_off(self):self.cfg['actions']['writes']=False;self.assertEqual(len(self.a.catalog()),1)
 def test_unknown_no_arbitrary(self):
  with self.assertRaises(PermissionError):self.a.prepare('a','shell',{'command':'no'})
  with self.assertRaises(ConfigError):validate({'actions':{'allow':['shell']}})
