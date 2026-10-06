import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from customchat.store import Store
from customchat.pipeline import Engine
from customchat import providers

EV = [{"n": 1, "title": "A", "text": "First passage about refunds."}, {"n": 2, "title": "B", "text": "x " * 400}]

class T(unittest.TestCase):
    def test_damaged_data_file_is_set_aside(self):
        d = tempfile.mkdtemp(); p = os.path.join(d, "customchat.db")
        open(p, "wb").write(os.urandom(200))
        s = Store(p)
        self.assertEqual(s.q("select count(*) c from sqlite_master where name='turns'", one=True)["c"], 1)
        self.assertTrue(any(".corrupt-" in f for f in os.listdir(d)))
    def test_fallback_answer_cites_passages(self):
        a = Engine.fallback_answer(EV)
        self.assertIn("could not be reached", a); self.assertIn("[1]", a); self.assertIn("[2]", a); self.assertLess(len(a), 1200)
    def test_fallback_answer_with_no_evidence(self):
        self.assertIn("could not be reached", Engine.fallback_answer([]))
    def test_bad_app_file_gives_plain_error(self):
        from customchat import schema
        d = tempfile.mkdtemp(); p = os.path.join(d, "a.yaml"); open(p, "w").write("app: [broken\n  x:")
        with self.assertRaises(schema.ConfigError) as c: schema.load(p)
        self.assertIn("not valid YAML", str(c.exception))
        with self.assertRaises(schema.ConfigError) as c: schema.load(os.path.join(d, "none.yaml"))
        self.assertIn("Cannot read", str(c.exception))
    def test_all_web_providers_failing_is_reported(self):
        from customchat.connectors.web_search import WebSearch
        from customchat import websearch
        old = websearch.search
        def boom(*a, **k): raise websearch.SearchError("no key")
        websearch.search = boom
        try:
            w = WebSearch({"id": "web", "label": "Web", "providers": ["tavily"]})
            with self.assertRaises(websearch.SearchError): w.search("q")
        finally: websearch.search = old
    def test_provider_down_fails_fast(self):
        from customchat import providers
        providers._DOWN["http://x.invalid/a"] = __import__("time").time() + 20
        with self.assertRaises(providers.ProviderError): providers._post("http://x.invalid/a", {}, {}, 5)
        providers._DOWN.clear()
if __name__ == "__main__": unittest.main()
