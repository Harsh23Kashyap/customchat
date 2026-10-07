import unittest
from unittest.mock import patch
from customchat.store import Store
class Branch(unittest.TestCase):
 def setUp(self):
  self.s=Store(':memory:');self.chat=self.s.new_chat('a','Original');self.topic=self.s.new_topic('a','Topic');self.ids=[]
  for q in ['Earlier question?','Edited question?','Future question?']:
   self.ids.append(self.s.add_turn(self.chat,self.topic,q,q,'answer',[{'n':1,'text':'private evidence'}],[],'standard'))
  self.s.set_summary(self.topic,'Summary includes future details')
 def test_preserves_original_and_excludes_future(self):
  result=self.s.branch('a',self.ids[1],'Changed question?');rows=self.s.turns('a',result['chat'])
  self.assertEqual([r['question'] for r in rows],['Earlier question?']);self.assertEqual(len(self.s.turns('a',self.chat)),3)
  self.assertNotEqual(rows[0]['id'],self.ids[0]);self.assertNotEqual(rows[0]['topic'],self.topic)
  self.assertEqual(self.s.topic('a',rows[0]['topic'])['summary'],'')
  self.assertEqual(result['question'],'Changed question?')
 def test_other_owner_rejected_no_writes(self):
  with self.assertRaises(PermissionError):self.s.branch('b',self.ids[1],'Changed question?')
  self.assertEqual(self.s.chats('b'),[])
 def test_deleted_turn_cannot_branch(self):
  self.s.delete_turn('a',self.ids[1])
  with self.assertRaises(PermissionError):self.s.branch('a',self.ids[1],'Changed question?')
 def test_deleted_chat_cannot_branch(self):
  self.s.delete_chat('a',self.chat)
  with self.assertRaises(PermissionError):self.s.branch('a',self.ids[1],'Changed question?')
 def test_first_turn_has_no_history(self):
  result=self.s.branch('a',self.ids[0],'Changed question?');self.assertEqual(self.s.turns('a',result['chat']),[])
 def test_invalid_question_no_chat_created(self):
  for q in ['', 'x'*2001]:
   with self.assertRaises(ValueError):self.s.branch('a',self.ids[0],q)
  self.assertEqual(len(self.s.chats('a')),1)
