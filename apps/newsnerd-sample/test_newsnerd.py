import json,os,unittest
from unittest.mock import patch
from pathlib import Path
import news_connector as n
class Reply:
    def __enter__(self):return self
    def __exit__(self,*a):pass
    def read(self,*a):return json.dumps({'articles':[{'title':'Fixture only','description':'Synthetic test snippet, not news.','url':'https://example.test/article','publishedAt':'2026-10-01T10:00:00Z','source':{'name':'Fixture publisher'}}]}).encode()
class Tests(unittest.TestCase):
    def test_gnews(self):
        with patch.dict(os.environ,{'GNEWS_API_KEY':'FAKE_UNIT_TEST_ONLY'}),patch('urllib.request.urlopen',return_value=Reply()) as req:
            a=n.gnews('What has been reported about AI regulation?',6)
            r=req.call_args[0][0];self.assertNotIn('FAKE_UNIT',r.full_url);self.assertIn('AI+regulation',r.full_url);self.assertEqual(r.get_header('X-api-key'),'FAKE_UNIT_TEST_ONLY');self.assertIn('Published: 2026',a[0]['text']);self.assertIn('Fixture publisher',a[0]['text'])
    def test_newsapi(self):
        with patch.dict(os.environ,{'NEWSAPI_KEY':'FAKE_UNIT_TEST_ONLY'}),patch('urllib.request.urlopen',return_value=Reply()) as req:
            self.assertEqual(len(n.newsapi('renewable energy',50)),1);self.assertIn('pageSize=10',req.call_args[0][0].full_url)
    def test_missing_key_no_network(self):
        with patch.dict(os.environ,{},clear=True),patch('urllib.request.urlopen') as req:
            with self.assertRaises(ValueError):n.gnews('AI',6)
            req.assert_not_called()
    def test_empty_query_no_network(self):
        with patch.dict(os.environ,{'GNEWS_API_KEY':'FAKE_UNIT_TEST_ONLY'}),patch('urllib.request.urlopen') as req:
            self.assertEqual(n.gnews('what is the news?',6),[]);req.assert_not_called()
    def test_all_config_fields(self):
        import yaml
        from customchat.schema import DEFAULTS,validate
        def check(raw,base):
            for key,value in base.items():
                self.assertIn(key,raw)
                if isinstance(value,dict):check(raw[key],value)
        for f in Path(__file__).parent.glob('app*.yaml'):
            raw=yaml.safe_load(f.read_text());validate(raw);check(raw,DEFAULTS)
if __name__=='__main__':unittest.main()
