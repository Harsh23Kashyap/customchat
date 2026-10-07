import io, unittest, zipfile
from customchat import theme, fileread
from customchat.pipeline import Engine
from customchat.store import Store

class FeedbackComplete(unittest.TestCase):
 def test_profile_fields_and_owner_isolation(self):
  s=Store(':memory:');s.set_profile('a','Old background');self.assertEqual(s.get_profile_fields('a')[0]['value'],'Old background')
  s.set_profile_fields('a',[{'label':'Goal','value':'Learn'},{'label':'Role','value':'Student'}]);self.assertIn('Role: Student',s.profile_context('a'));self.assertEqual(s.get_profile_fields('b'),[])
  with self.assertRaises(ValueError):s.set_profile_fields('a',[{'label':'','value':'Filled'}])
  with self.assertRaises(ValueError):s.set_profile_fields('a',[{'label':'Role','value':'x'*1001}])
  s.set_profile_fields('a',[]);self.assertEqual(s.profile_context('a'),'')
 def test_whole_history_answers_and_relevance(self):
  rows=[{'question':'Q'+str(i),'answer':'Full answer '+str(i)+' END'} for i in range(20)]
  self.assertEqual(Engine.pack_history(rows,'Q1'),rows)
  big=[{'question':'remote unique topic' if i==0 else 'other','answer':'z'*9000+' END'} for i in range(20)]
  packed=Engine.pack_history(big,'remote unique topic');self.assertLessEqual(sum(len(r['question'])+len(r['answer']) for r in packed),60000);self.assertTrue(all(r['answer'].endswith(' END') for r in packed));self.assertIn(big[0],packed)
 def test_saved_history_chat_topic_isolation(self):
  from customchat import schema
  e=Engine(schema.validate({}),Store(':memory:'));a=e.store.new_chat('o','a');b=e.store.new_chat('o','b');topic=e.store.new_topic('o','one');other=e.store.new_topic('o','two')
  e.store.add_turn(a,topic,'Earlier question','q','Complete answer END',[],[],'standard')
  e.store.add_turn(a,other,'Different topic','q','Private other topic',[],[],'standard')
  e.store.add_turn(b,topic,'Different chat','q','Private other chat',[],[],'standard')
  history=e.conversation_history('o',a,topic,'follow-up');self.assertEqual(len(history),1)
  prompt=e.prompt('follow-up',[],'standard',history,'')[1]['content'];self.assertIn('Complete answer END',prompt);self.assertNotIn('Private other',prompt)
  with self.assertRaises(PermissionError):e.conversation_history('different-owner',a,topic,'q')
 def test_whole_answer_prompt_after_old_clip_boundary(self):
  from customchat import schema
  e=Engine(schema.validate({}),Store(':memory:'));answer='a'*500+' RELEVANT END'
  prompt=e.prompt('q',[],'standard',[{'question':'before','answer':answer}],'')[1]['content'];self.assertIn('RELEVANT END',prompt)
 def test_animated_emoji_validation(self):
  t=theme.clean({'emoji_bot':'🚀','emoji_bot_motion':'bounce'});self.assertEqual(t['emoji_bot_motion'],'bounce');self.assertEqual(theme.clean({'emoji_bot_motion':'javascript'})['emoji_bot_motion'],'none')
 def test_file_types_and_binary_rejection(self):
  self.assertIn('hello',fileread.extract('notes.md',b'hello'))
  for name,data in [('program.exe',b'binary'),('bad.txt',b'\x00data'),('broken.docx',b'not zip')]:
   with self.assertRaises(ValueError):fileread.extract(name,data)
 def test_word_and_sheet_values(self):
  def archive(items):
   b=io.BytesIO()
   with zipfile.ZipFile(b,'w') as z:
    for k,v in items.items():z.writestr(k,v)
   return b.getvalue()
  self.assertIn('Readable',fileread.extract('file.docx',archive({'word/document.xml':'<root><p>Readable paragraph</p></root>'})))
  data=archive({'xl/sharedStrings.xml':'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>Name</t></si></sst>','xl/worksheets/sheet1.xml':'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c r="A1" t="s"><v>0</v></c><c r="B1"><v>42</v></c></row></sheetData></worksheet>'})
  self.assertEqual(fileread.extract('sheet.xlsx',data),'A1: Name | B1: 42')
