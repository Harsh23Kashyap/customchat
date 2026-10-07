import unittest
from pathlib import Path
from customchat import schema
from customchat.pipeline import Engine
from customchat.store import Store
class Progress(unittest.TestCase):
 def test_real_stage_events_empty_sources(self):
  e=Engine(schema.validate({}),Store(':memory:'));c=e.store.new_chat('a')
  events=list(e.ask_stream('a',c,'What are the protein sources?'))
  stages=[data['stage'] for kind,data in events if kind=='progress']
  self.assertEqual(stages,['context','sources','ranking','answer','citations','history','followups'])
  self.assertEqual(events[-1][0],'done');self.assertEqual(events[-1][1]['evidence'],[])
  self.assertIn('No matching evidence',[d['label'] for k,d in events if k=='progress'][3])
 def test_validation_before_events(self):
  e=Engine(schema.validate({}),Store(':memory:'))
  with self.assertRaises(ValueError):next(e.ask_stream('a',None,''))
  with self.assertRaises(PermissionError):next(e.ask_stream('a','not-owned','Valid question?'))
 def test_status_live_region_and_scroll(self):
  w=Path(__file__).resolve().parents[1]/'customchat/web'
  self.assertIn('aria-atomic="true"',(w/'index.html').read_text());self.assertIn('Preparing your answer',(w/'app.js').read_text())
