import unittest
from unittest.mock import Mock
from customchat import schema
from customchat.pipeline import Engine
from customchat.store import Store
from customchat.suggestions import starters,recent,clean
from customchat.providers import ProviderError
class Suggestions(unittest.TestCase):
    def engine(self):
        cfg=schema.validate({'app':{'title':'Diet Chat','examples':['What are the protein sources?']}})
        return Engine(cfg,Store(':memory:'))
    def test_demo_never_calls_model(self):
        e=self.engine();e.provider=Mock();self.assertEqual(starters(e)['origin'],'configured');e.provider.complete.assert_not_called()
    def test_generation_cached_and_prompt_change_invalidates(self):
        e=self.engine();e.cfg['provider'].update(type='openai',model='cheap-test');e.provider=Mock()
        e.provider.complete.return_value='1. What are the protein sources?\n2. How much fiber is in beans?'
        a=starters(e);self.assertEqual(a,starters(e));self.assertEqual(e.provider.complete.call_count,1)
        e.cfg['prompt']['system']='New scope';starters(e);self.assertEqual(e.provider.complete.call_count,2)
    def test_failure_cached_not_retried_every_load(self):
        e=self.engine();e.cfg['provider'].update(type='openai',model='cheap-test');e.provider=Mock()
        e.provider.complete.side_effect=ProviderError('budget reached')
        self.assertEqual(starters(e)['origin'],'fallback');starters(e);self.assertEqual(e.provider.complete.call_count,1)
    def test_recent_private_deleted_and_deduped(self):
        e=self.engine();s=e.store
        for owner,q in [('alice','How much fiber is in beans?'),('bob','What is my private history?'),('alice','How much fiber is in beans?')]:
            c=s.new_chat(owner);t=s.add_turn(c,None,q,q,'',[],[],'standard')
        self.assertEqual(recent(s,'alice'),['How much fiber is in beans?'])
        s.delete_turn('alice',t);s.delete_chat('alice',s.chats('alice')[1]['id'])
        self.assertEqual(recent(s,'alice'),[])
    def test_filter_bounded_safe_distinct(self):
        self.assertEqual(clean(['<script>evil?</script>','x?','What are the protein sources?','What are the protein sources?']),['What are the protein sources?'])
    def test_http_temporary_hides_recent(self):
        import threading,json,urllib.request
        from customchat.server import LocalHTTPServer,make_handler
        e=self.engine();c=e.store.new_chat('local');e.store.add_turn(c,None,'How much fiber is in beans?','','',[],[],'standard')
        srv=LocalHTTPServer(('127.0.0.1',0),make_handler(e.cfg,e));threading.Thread(target=srv.serve_forever,daemon=True).start()
        try:
            def call(temp):
                req=urllib.request.Request('http://127.0.0.1:'+str(srv.server_port)+'/api/suggestions',data=json.dumps({'temporary':temp}).encode(),headers={'Content-Type':'application/json'})
                return json.load(urllib.request.urlopen(req))
            self.assertEqual(call(True)['recent'],[])
            self.assertTrue(call(False)['questions'])
        finally:srv.shutdown();srv.server_close()
