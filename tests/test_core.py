import json, os, tempfile, threading, unittest, urllib.request
from http.server import ThreadingHTTPServer
from customchat import schema
from customchat.pipeline import Engine
from customchat.store import Store
from customchat.server import make_handler
from customchat.exports import bibtex, pdf_bytes
from customchat.connectors.local_files import LocalFiles

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "apps", "minimal", "app.yaml")


def engine():
    cfg = schema.load(APP)
    return Engine(cfg, Store(":memory:")), cfg


class Schema(unittest.TestCase):
    def test_defaults_and_validation(self):
        c = schema.validate({})
        self.assertEqual(c["provider"]["type"], "mock")
        for bad in ({"nope": 1}, {"provider": {"type": "x"}}, {"provider": {"type": "ollama"}},
                    {"provider": {"api_key": "sk-1"}}, {"sources": [{"type": "zzz"}]},
                    {"sources": [{"type": "local_files", "id": "a"}, {"type": "local_files", "id": "a"}]},
                    {"retrieval": {"top_k": 0}}, {"auth": {"mode": "x"}}):
            with self.assertRaises(schema.ConfigError, msg=str(bad)):
                schema.validate(bad)

    def test_public_view_hides_internals(self):
        c = schema.validate({"provider": {"type": "openai", "model": "m", "api_key_env": "SECRET_ENV"}})
        self.assertNotIn("SECRET_ENV", json.dumps(schema.public_view(c)))

    def test_example_apps_validate(self):
        for a in ("minimal", "dietchat", "wirelesschat"):
            schema.load(os.path.join(ROOT, "apps", a, "app.yaml"))


class Retrieval(unittest.TestCase):
    def test_bm25_prefers_matching_section(self):
        c = schema.load(APP)
        lf = LocalFiles(c["sources"][0], c["_dir"])
        r = lf.search("conversation memory follow-up", 3)
        self.assertEqual(r[0]["title"], "Conversation memory")
        self.assertEqual(lf.search("zzzz qqqq", 3), [])


class Pipeline(unittest.TestCase):
    def test_answer_cites_and_stores(self):
        e, _ = engine()
        chat = e.store.new_chat("local")
        r = e.ask("local", chat, "What is CustomChat?")
        self.assertIn("[1]", r["answer"])
        self.assertTrue(all(l["supported"] for l in r["ledger"]))
        self.assertEqual(len(e.store.turns("local", chat)), 1)
        self.assertEqual(e.store.chat("local", chat)["title"], "What is CustomChat?")

    def test_no_evidence_message(self):
        e, cfg = engine()
        r = e.ask("local", e.store.new_chat("local"), "xyzzy plugh")
        self.assertEqual(r["answer"], cfg["prompt"]["no_evidence"])

    def test_ledger_flags_invalid_citation(self):
        led = Engine.ledger("A claim [9]. Another [1].", [{"n": 1}])
        self.assertFalse(led[0]["supported"]); self.assertEqual(led[0]["invalid"], [9]); self.assertTrue(led[1]["supported"])

    def test_followup_is_resolved_with_history(self):
        class P:
            def __init__(s): s.calls = []
            def complete(s, m):
                s.calls.append(m); return "How does conversation memory work in CustomChat?" if "Rewrite" in m[0]["content"] else "ok [1]"
        e, cfg = engine()
        cfg["provider"]["type"] = "ollama"
        e.provider = P()
        chat = e.store.new_chat("local")
        e.ask("local", chat, "What is conversation memory?")
        r = e.ask("local", chat, "How does it work?")
        self.assertIn("conversation memory", r["standalone"].lower())

    def test_topics_span_chats_and_new_topic(self):
        e, _ = engine()
        c1 = e.store.new_chat("local")
        a = e.ask("local", c1, "What is CustomChat?")
        b = e.ask("local", c1, "What is conversation memory?")
        self.assertEqual(a["topic"], b["topic"])
        c = e.ask("local", c1, "What is CustomChat?", new_topic=True)
        self.assertNotEqual(c["topic"], a["topic"])
        c2 = e.store.new_chat("local")
        d = e.ask("local", c2, "memory again", topic=a["topic"])
        self.assertEqual(len(e.store.topic_turns("local", a["topic"])), 3)

    def test_owner_isolation(self):
        e, _ = engine()
        chat = e.store.new_chat("alice")
        with self.assertRaises(PermissionError):
            e.store.turns("bob", chat)
        with self.assertRaises(PermissionError):
            e.ask("bob", chat, "hi")

    def test_failing_source_does_not_sink_answer(self):
        e, _ = engine()
        class Boom:
            def search(self, q, k): raise OSError("down")
        e.connectors["bad"] = Boom()
        r = e.ask("local", e.store.new_chat("local"), "What is CustomChat?")
        self.assertTrue(r["evidence"])
        e._cache.clear()
        self.assertEqual(e.retrieve("What is CustomChat?", ["bad"])[1], {"bad": "OSError"})

    def test_chat_lifecycle(self):
        s = Store(":memory:")
        c = s.new_chat("o", "A"); s.pin("o", c, True); s.rename_chat("o", c, "B")
        self.assertEqual(s.chats("o")[0]["title"], "B")
        s.delete_chat("o", c); self.assertEqual(s.chats("o"), [])
        s.restore_chat("o", c); self.assertEqual(len(s.chats("o")), 1)


class Exports(unittest.TestCase):
    def test_bibtex_and_pdf(self):
        ev = [{"title": "T {x}", "authors": ["Ada Lovelace"], "year": "1843", "venue": "J", "url": "u"}]
        self.assertIn("@article{Lovelace18431", bibtex(ev)); self.assertNotIn("{x}", bibtex(ev))
        p = pdf_bytes("App", {"question": "q (1)", "answer": "a [1]", "evidence": ev})
        self.assertTrue(p.startswith(b"%PDF-1.4") and p.rstrip().endswith(b"%%EOF"))


class Http(unittest.TestCase):
    def setUp(self):
        self.e, self.cfg = engine()
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.cfg, self.e))
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = "http://127.0.0.1:%d" % self.srv.server_port

    def tearDown(self): self.srv.shutdown()

    def call(self, path, body=None, headers=None):
        req = urllib.request.Request(self.base + path, data=None if body is None else json.dumps(body).encode(), headers=headers or {})
        try:
            with urllib.request.urlopen(req) as r: return r.status, r.read()
        except urllib.error.HTTPError as ex: return ex.code, ex.read()

    def test_flow(self):
        self.assertEqual(self.call("/api/health")[0], 200)
        code, body = self.call("/")
        self.assertIn(b"Docs Chat", body)
        code, body = self.call("/api/ask", {"question": "What is CustomChat?"})
        r = json.loads(body); self.assertEqual(code, 200); self.assertIn("[1]", r["answer"])
        self.assertEqual(len(json.loads(self.call("/api/turns?chat=" + r["chat"])[1])), 1)
        self.assertEqual(self.call("/api/bibtex?turn=" + r["id"])[0], 200)
        self.assertEqual(self.call("/api/pdf?turn=" + r["id"])[1][:4], b"%PDF")
        self.assertEqual(self.call("/api/ask", {"question": ""})[0], 400)
        self.assertEqual(self.call("/api/turns?chat=nope")[0], 404)

    def test_static_traversal_blocked(self):
        self.assertEqual(self.call("/..%2f..%2fsetup.py")[0], 404)
        self.assertEqual(self.call("/../README.md")[0], 404)

    def test_token_auth(self):
        self.cfg["auth"] = {"mode": "token", "token_env": "CC_TEST_TOKEN"}
        srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.cfg, self.e))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        os.environ["CC_TEST_TOKEN"] = "s3cret"
        base = "http://127.0.0.1:%d" % srv.server_port
        def get(h):
            try: return urllib.request.urlopen(urllib.request.Request(base + "/api/chats", headers=h)).status
            except urllib.error.HTTPError as ex: return ex.code
        self.assertEqual(get({}), 401); self.assertEqual(get({"Authorization": "Bearer wrong"}), 401)
        self.assertEqual(get({"Authorization": "Bearer s3cret"}), 200); srv.shutdown()


if __name__ == "__main__":
    unittest.main()


class Extras(unittest.TestCase):
    def test_env_file_loaded_and_existing_wins(self):
        d = tempfile.mkdtemp()
        open(os.path.join(d, ".env"), "w").write("CC_A=1\nCC_B='two'\n# c\n")
        open(os.path.join(d, "app.yaml"), "w").write("app: {title: T}\n")
        os.environ["CC_A"] = "keep"
        schema.load(os.path.join(d, "app.yaml"))
        self.assertEqual(os.environ["CC_A"], "keep"); self.assertEqual(os.environ["CC_B"], "two")

    def test_chat_markdown(self):
        from customchat.exports import chat_markdown
        md = chat_markdown("T", [{"question": "q", "answer": "a [1]", "evidence": [{"title": "X", "url": "u"}]}])
        self.assertIn("**Q:** q", md); self.assertIn("1. X <u>", md)

    def test_provider_retry_on_transient(self):
        from customchat import providers
        calls = []
        def fake(url, payload, headers, timeout):
            calls.append(1)
            if len(calls) < 3: raise providers.ProviderError("Provider returned HTTP 503")
            return {"ok": 1}
        orig = providers._post_once; providers._post_once = fake
        try:
            self.assertEqual(providers._post("u", {}, {}, 1), {"ok": 1}); self.assertEqual(len(calls), 3)
            calls.clear()
            def bad(*a): calls.append(1); raise providers.ProviderError("Provider returned HTTP 401")
            providers._post_once = bad
            with self.assertRaises(providers.ProviderError): providers._post("u", {}, {}, 1)
            self.assertEqual(len(calls), 1)
        finally: providers._post_once = orig


class JsonSchemaFile(unittest.TestCase):
    def test_json_schema_matches_defaults(self):
        js = json.load(open(os.path.join(ROOT, "schema", "chat-app.schema.json")))
        self.assertEqual(set(js["properties"]), set(schema.DEFAULTS))
        for k, v in schema.DEFAULTS.items():
            if isinstance(v, dict) and "properties" in js["properties"][k]:
                self.assertLessEqual(set(v), set(js["properties"][k]["properties"]) , k)


class Streaming(unittest.TestCase):
    def test_ask_stream_matches_ask(self):
        e, _ = engine()
        chat = e.store.new_chat("local")
        events = list(e.ask_stream("local", chat, "What is CustomChat?"))
        kinds = [k for k, _ in events]
        self.assertEqual(kinds[0], "meta"); self.assertEqual(kinds[-1], "done"); self.assertIn("token", kinds)
        done = events[-1][1]
        self.assertEqual("".join(d for k, d in events if k == "token").strip(), done["answer"])
        self.assertEqual(len(e.store.turns("local", chat)), 1)

    def test_http_stream_and_validation(self):
        e, cfg = engine()
        srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cfg, e))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = "http://127.0.0.1:%d" % srv.server_port
        def post(b):
            return urllib.request.urlopen(urllib.request.Request(base + "/api/ask-stream", data=json.dumps(b).encode()))
        lines = [json.loads(l) for l in post({"question": "What is CustomChat?"}).read().decode().splitlines()]
        self.assertEqual(lines[0]["type"], "meta"); self.assertEqual(lines[-1]["type"], "done")
        with self.assertRaises(urllib.error.HTTPError) as c: post({"question": ""})
        self.assertEqual(c.exception.code, 400); srv.shutdown()


class Theme(unittest.TestCase):
    def test_theme_validation_and_render(self):
        with self.assertRaises(schema.ConfigError): schema.validate({"app": {"theme": "neon"}})
        e, cfg = engine(); cfg["app"]["theme"] = "dark"
        srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cfg, e))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        html = urllib.request.urlopen("http://127.0.0.1:%d/" % srv.server_port).read().decode()
        self.assertIn('data-theme="dark"', html); srv.shutdown()


class Round10(unittest.TestCase):
    def test_uploads_become_evidence_and_are_private(self):
        e, _ = engine()
        e.store.add_upload("local", "notes", "Zebrafish regeneration needs fgf signalling in the fin blastema.")
        chat = e.store.new_chat("local")
        r = e.ask("local", chat, "zebrafish fin regeneration")
        self.assertEqual(r["evidence"][0]["title"], "notes")
        e2 = e.ask("someone-else", e.store.new_chat("someone-else"), "zebrafish fin regeneration")
        self.assertNotIn("notes", [x["title"] for x in e2["evidence"]])

    def test_delete_and_restore_turn(self):
        e, _ = engine()
        chat = e.store.new_chat("local")
        r = e.ask("local", chat, "What is CustomChat?")
        e.store.delete_turn("local", r["id"]); self.assertEqual(e.store.turns("local", chat), [])
        e.store.restore_turn("local", r["id"]); self.assertEqual(len(e.store.turns("local", chat)), 1)

    def test_weight_validated_and_applied(self):
        with self.assertRaises(schema.ConfigError): schema.validate({"sources": [{"type": "local_files", "weight": 0}]})
        e, cfg = engine()
        a = e.retrieve("What is CustomChat?")[0][0]["score"]
        e.cfg["sources"][0]["weight"] = 3.0; e._cache.clear()
        self.assertAlmostEqual(e.retrieve("What is CustomChat?")[0][0]["score"], a * 3, places=6)

    def test_followups_present(self):
        e, _ = engine()
        done = [d for k, d in e.ask_stream("local", e.store.new_chat("local"), "What is CustomChat?") if k == "done"][0]
        self.assertTrue(done["followups"])

    def test_url_dedupe(self):
        e, _ = engine()
        class Dup:
            def search(self, q, k): return [{"id": "1", "title": "A", "text": "t", "url": "http://x", "authors": [], "year": "", "venue": "", "source": "d", "score": 1.0},
                                             {"id": "2", "title": "B different title", "text": "t", "url": "http://x", "authors": [], "year": "", "venue": "", "source": "d", "score": 0.9}]
        e.connectors = {"d": Dup()}
        self.assertEqual(len(e.retrieve("anything")[0]), 1)


class Round16(unittest.TestCase):
    def test_support_score_and_ledger_overlap(self):
        ev = [{"n": 1, "title": "Memory", "text": "Every question is rewritten into a standalone question"}]
        led = Engine.ledger("Every question is rewritten into a standalone question [1]. Bananas are yellow [1].", ev)
        self.assertGreater(led[0]["overlap"], 0.8); self.assertLess(led[1]["overlap"], 0.4)

    def test_fallback_provider_used_when_primary_fails(self):
        from customchat import providers
        class Bad:
            def complete(self, m): raise providers.ProviderError("down")
            def stream(self, m): raise providers.ProviderError("down"); yield
        class Good:
            def complete(self, m): return "ok"
            def stream(self, m): yield "ok"
        w = providers.WithFallback(Bad(), Good())
        self.assertEqual(w.complete([]), "ok"); self.assertEqual(list(w.stream([])), ["ok"])
        with self.assertRaises(schema.ConfigError): schema.validate({"provider": {"type": "mock", "fallback": {"type": "bogus"}}})
        c = schema.validate({"provider": {"type": "ollama", "model": "m", "fallback": {"type": "mock"}}})
        self.assertIsInstance(providers.make(c), providers.WithFallback)

    def test_parallel_retrieval_survives_slow_and_failing_sources(self):
        import time as _t
        e, _ = engine()
        class Slow:
            def search(self, q, k): _t.sleep(0.2); return [{"id": "s", "title": "Slow", "text": "t", "url": "u1", "authors": [], "year": "", "venue": "", "source": "slow", "score": 0.5}]
        class Boom:
            def search(self, q, k): raise RuntimeError("x")
        e.connectors = {"slow": Slow(), "boom": Boom()}
        found, errors = e.retrieve("anything")
        self.assertEqual([f["title"] for f in found], ["Slow"]); self.assertEqual(errors, {"boom": "RuntimeError"})

    def test_query_rewrite_with_model(self):
        class P:
            def complete(s, m): return "1. alpha beta\n2. gamma"
        e, cfg = engine(); cfg["provider"]["type"] = "ollama"; cfg["retrieval"]["query_rewrite"] = True; e.provider = P()
        self.assertEqual(e.queries("what is it"), ["what is it", "alpha beta", "gamma"])
        cfg["retrieval"]["query_rewrite"] = False; self.assertEqual(e.queries("q"), ["q"])

    def test_persistent_cache_skips_second_remote_call(self):
        e, cfg = engine(); cfg["retrieval"]["cache_ttl"] = 60
        cfg["sources"] = [{"id": "remote", "type": "arxiv", "label": "r"}]
        calls = []
        class R:
            def search(self, q, k): calls.append(q); return [{"id": "r", "title": "R", "text": "t", "url": "u", "authors": [], "year": "", "venue": "", "source": "remote", "score": 1.0}]
        e.connectors = {"remote": R()}
        e.retrieve("same question"); e._cache.clear(); e.retrieve("same question")
        self.assertEqual(len(calls), 1)

    def test_export_all(self):
        e, _ = engine(); chat = e.store.new_chat("local"); e.ask("local", chat, "What is CustomChat?")
        out = e.store.export_all("local"); self.assertEqual(len(out), 1); self.assertEqual(len(out[0]["turns"]), 1)

    def test_cli_ask_json(self):
        import subprocess, sys
        r = subprocess.run([sys.executable, "-m", "customchat", "ask", APP, "What is CustomChat?", "--json"], cwd=ROOT, capture_output=True, text=True)
        self.assertIn("evidence", json.loads(r.stdout))


class Round17(unittest.TestCase):
    def test_import_roundtrip_and_ping(self):
        import tempfile, os
        from customchat.store import Store
        d = tempfile.mkdtemp()
        s = Store(os.path.join(d, "t.db"))
        self.assertTrue(s.ping())
        n = s.import_chats("o", [{"title": "X", "turns": [{"question": "q", "answer": "a"}]}, "bad"])
        self.assertEqual(n, 1)
        out = s.export_all("o")
        self.assertEqual(out[0]["turns"][0]["answer"], "a")


class Round18(unittest.TestCase):
    def test_feedback_and_stats(self):
        import tempfile, os
        from customchat.store import Store
        s = Store(os.path.join(tempfile.mkdtemp(), "t.db"))
        cid = s.new_chat("o", "x")
        tid = s.add_turn(cid, None, "q", "q", "a", [], [], "standard")
        self.assertEqual(s.rate("o", tid, 1), 1)
        self.assertEqual(s.ratings("o", cid), {tid: 1})
        self.assertEqual(s.stats("o")["helpful"], 1)
        s.rate("o", tid, 0)
        self.assertEqual(s.ratings("o", cid), {})

    def test_eval_command(self):
        import tempfile, os, subprocess, sys
        d = tempfile.mkdtemp(); q = os.path.join(d, "q.txt")
        open(q, "w").write("# c\nwhat is this\n")
        out = subprocess.run([sys.executable, "-m", "customchat", "eval", "apps/minimal/app.yaml", q], capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("coverage:", out.stdout)


class Round19(unittest.TestCase):
    def _engine(self):
        import tempfile, os
        from customchat import schema
        from customchat.pipeline import Engine
        from customchat.store import Store
        c = schema.load("apps/minimal/app.yaml")
        return Engine(c, Store(os.path.join(tempfile.mkdtemp(), "t.db")))

    def test_temporary_chat_saves_nothing(self):
        e = self._engine()
        out = list(e.ask_stream("o", None, "What is CustomChat?", temporary=True))
        done = out[-1][1]
        self.assertTrue(done["temporary"]); self.assertIsNone(done["id"])
        self.assertEqual(e.store.export_all("o"), [])
        self.assertEqual(e.store.stats("o")["turns"], 0)

    def test_temporary_uses_bounded_client_history(self):
        e = self._engine()
        h = [{"question": "q%d" % i, "answer": "a"} for i in range(20)]
        out = list(e.ask_stream("o", None, "What about its cost?", temporary=True, temp_history=h))
        self.assertTrue(out[-1][1]["answer"])

    def test_profile_roundtrip_and_prompt(self):
        e = self._engine()
        e.store.set_profile("o", "Vegetarian, 30s")
        self.assertEqual(e.store.get_profile("o"), "Vegetarian, 30s")
        msgs = e.prompt("q", [{"n": 1, "title": "t", "year": None, "text": "x"}], "standard", [], "", "Vegetarian, 30s")
        self.assertIn("Vegetarian", msgs[1]["content"])
        e.store.set_profile("o", "")
        self.assertEqual(e.store.get_profile("o"), "")

    def test_similar_questions(self):
        e = self._engine()
        c = e.store.new_chat("o", "x")
        e.store.add_turn(c, None, "How does conversation memory work", "q", "a", [], [], "standard")
        e.store.add_turn(c, None, "Totally unrelated pizza topic", "q", "a", [], [], "standard")
        r = e.similar("o", "explain conversation memory")
        self.assertEqual(len(r), 1); self.assertIn("memory", r[0]["question"])
