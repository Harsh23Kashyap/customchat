import tempfile, unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from customchat.budget import Budget, BudgetError, clean
from customchat.providers import Mock
from customchat import schema

class BudgetTests(unittest.TestCase):
    def test_global_user_quotas(self):
        b=Budget({'budget':{'daily_questions':3,'user_daily_questions':1}})
        b.take('question','a')
        with self.assertRaises(BudgetError):b.take('question','a')
        b.take('question','b');b.take('question','c')
        with self.assertRaises(BudgetError):b.take('question','d')
        self.assertEqual(b.view()['used']['question'],3)
    def test_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            b=Budget({},folder);b.save({'daily_questions':1});b.take('question','a')
            again=Budget({},folder)
            with self.assertRaises(BudgetError):again.take('question','b')
    def test_day_reset(self):
        b=Budget({'budget':{'daily_questions':1}});b.take('question','a')
        with patch.object(b,'day',return_value='2099-01-01'):b.take('question','a')
    def test_atomic_concurrency(self):
        b=Budget({'budget':{'daily_questions':5}})
        def call(i):
            try:b.take('question',str(i));return True
            except BudgetError:return False
        with ThreadPoolExecutor(max_workers=8) as e:out=list(e.map(call,range(30)))
        self.assertEqual(sum(out),5)
    def test_cross_instance(self):
        with tempfile.TemporaryDirectory() as folder:
            a=Budget({'budget':{'daily_questions':1}},folder);b=Budget({'budget':{'daily_questions':1}},folder)
            a.take('question','a')
            with self.assertRaises(BudgetError):b.take('question','b')
    def test_model_limit(self):
        b=Budget({'budget':{'daily_model_calls':1}});p=b.wrap(Mock({}))
        p.complete([{'content':'hi'}])
        with self.assertRaises(BudgetError):list(p.stream([{'content':'hi'}]))
    def test_dollar_cap_fail_closed(self):
        class Remote:
            def complete(self,_):raise AssertionError('must not call')
        b=Budget({'budget':{'spend_cap_usd':10}})
        with self.assertRaises(BudgetError):b.wrap(Remote()).complete([])
        self.assertFalse(b.view()['used'])
    def test_bad_values(self):
        for raw in ({'daily_questions':True},{'daily_questions':-1},{'daily_model_calls':.5},{'other':1},{'spend_cap_usd':-1},{'spend_cap_usd':float('nan')}):
            with self.assertRaises(ValueError):clean(raw)
    def test_schema(self):
        self.assertEqual(schema.validate({})['budget']['daily_questions'],0)
        with self.assertRaises(schema.ConfigError):schema.validate({'budget':{'daily_questions':'many'}})
class BudgetPermissions(unittest.TestCase):
    def test_endpoint_auth_and_lock(self):
        import threading, urllib.request, urllib.error
        from customchat import server
        from customchat.pipeline import Engine
        from customchat.store import Store
        cfg=schema.validate({'auth':{'mode':'token','token_env':'BUDGET_TEST_TOKEN'},'storage':{'path':':memory:'}})
        engine=Engine(cfg,Store(':memory:'));srv=server.LocalHTTPServer(('127.0.0.1',0),server.make_handler(cfg,engine))
        th=threading.Thread(target=srv.serve_forever,daemon=True);th.start();url='http://127.0.0.1:%d/api/budget'%srv.server_port
        try:
            with patch.dict('os.environ',{'BUDGET_TEST_TOKEN':'test-only'}):
                with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(url)
                self.assertEqual(e.exception.code,401)
                req=urllib.request.Request(url,headers={'Authorization':'Bearer test-only'})
                with urllib.request.urlopen(req) as r:self.assertEqual(r.status,200)
                with patch.object(server,'LOCKED',True):
                    with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(req)
                    self.assertEqual(e.exception.code,404)
        finally:srv.shutdown();srv.server_close();th.join()
if __name__=='__main__':unittest.main()
