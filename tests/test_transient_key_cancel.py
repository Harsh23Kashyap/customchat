import io,json,time,unittest
from unittest.mock import patch,MagicMock
from customchat import websearch,hardware
class TransientKeyAndCancellation(unittest.TestCase):
 def test_transient_key_is_used_without_secret_store_read_or_write(self):
  store=MagicMock();response=io.BytesIO(json.dumps({'results':[{'title':'Result','text':'Body','url':'https://example.org'}]}).encode())
  with patch.object(websearch.secrets,'STORE',store),patch.object(websearch.urllib.request,'urlopen',return_value=response) as request:
   items,raw=websearch.search('exa','test',with_raw=True,key_override='temporary-test-placeholder')
  self.assertEqual(request.call_args.args[0].get_header('X-api-key'),'temporary-test-placeholder')
  store.get.assert_not_called();store.set.assert_not_called();store.delete.assert_not_called();self.assertNotIn('temporary-test-placeholder',raw);self.assertEqual(len(items),1)
 def test_blank_typed_key_does_not_fall_back(self):
  with patch.object(websearch,'key_for',return_value='saved') as saved:
   with self.assertRaises(websearch.SearchError):websearch.search('exa','q',key_override='')
  saved.assert_not_called()
 def pull(self,payload):
  response=io.BytesIO(payload)
  with patch.object(hardware.urllib.request,'urlopen',return_value=response):
   pid=hardware.start_pull('http://localhost:11434','test:8b')
   for _ in range(100):
    if hardware.pull_status(pid)['done']:break
    time.sleep(.01)
  return pid,hardware.pull_status(pid)
 def test_success_cannot_be_cancelled_after_done(self):
  pid,st=self.pull(b'{"status":"success"}\n');self.assertTrue(st['done']);self.assertEqual(st['pct'],100);self.assertFalse(hardware.cancel_pull(pid)['cancelled']);self.assertNotIn(pid,hardware._PULL_HANDLES)
 def test_truncated_stream_is_not_installed(self):
  pid,st=self.pull(b'{"status":"pulling","total":100,"completed":12}\n');self.assertTrue(st['error']);self.assertLess(st['pct'],100)
 def test_unknown_cancel(self):self.assertIsNone(hardware.cancel_pull('missing-test-id'))
