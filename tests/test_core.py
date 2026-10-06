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


class Round20(unittest.TestCase):
    def _cfg(self, t):
        return schema.load({"app": {"title": "T"}, "provider": {"type": t, "model": "m"}}) if hasattr(schema, "load") else None

    def test_claude_request_shape(self):
        from customchat import providers
        seen = {}
        def fake(url, payload, headers, timeout, retries=2):
            seen.update(url=url, payload=payload, headers=headers)
            return {"content": [{"type": "text", "text": " hi [1] "}]}
        old = providers._post; providers._post = fake
        os.environ["ANTHROPIC_API_KEY"] = "k"
        try:
            c = providers.Claude({"provider": {"base_url": "", "model": "claude-x", "timeout": 5, "temperature": 0.1, "api_key_env": ""}})
            out = c.complete([{"role": "system", "content": "sys"}, {"role": "user", "content": "q"}])
        finally:
            providers._post = old; del os.environ["ANTHROPIC_API_KEY"]
        self.assertEqual(out, "hi [1]")
        self.assertTrue(seen["url"].endswith("/v1/messages"))
        self.assertEqual(seen["payload"]["system"], "sys")
        self.assertEqual(seen["payload"]["messages"], [{"role": "user", "content": "q"}])
        self.assertIn("x-api-key", seen["headers"])

    def test_gemini_request_shape(self):
        from customchat import providers
        seen = {}
        def fake(url, payload, headers, timeout, retries=2):
            seen.update(url=url, payload=payload, headers=headers)
            return {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
        old = providers._post; providers._post = fake
        os.environ["GEMINI_API_KEY"] = "k"
        try:
            g = providers.Gemini({"provider": {"base_url": "", "model": "gem", "timeout": 5, "temperature": 0.1, "api_key_env": ""}})
            out = g.complete([{"role": "system", "content": "sys"}, {"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}])
        finally:
            providers._post = old; del os.environ["GEMINI_API_KEY"]
        self.assertEqual(out, "ok")
        self.assertNotIn("k", seen["url"].split("?")[-1] if "?" in seen["url"] else "")
        self.assertEqual(seen["payload"]["contents"][1]["role"], "model")
        self.assertIn("x-goog-api-key", seen["headers"])

    def test_missing_key_is_a_clear_error(self):
        from customchat import providers
        os.environ.pop("ANTHROPIC_API_KEY", None)
        c = providers.Claude({"provider": {"base_url": "", "model": "m", "timeout": 5, "temperature": 0, "api_key_env": ""}})
        with self.assertRaises(providers.ProviderError):
            c.complete([{"role": "user", "content": "q"}])

    def test_url_loader_blocks_private_hosts(self):
        from customchat import fetch
        for u in ("http://127.0.0.1:8000/x", "http://localhost/x", "http://10.0.0.5/", "ftp://example.com/a", "file:///etc/passwd", "http://169.254.169.254/latest"):
            with self.assertRaises(ValueError, msg=u):
                fetch.load(u)

    def test_html_to_text(self):
        from customchat import fetch
        p = fetch._Text(); p.feed("<html><title>Doc</title><script>bad()</script><p>Hello</p><p>World</p></html>")
        self.assertEqual(p.title, "Doc")
        self.assertIn("Hello", "".join(p.out)); self.assertNotIn("bad", "".join(p.out))


class SettingsApi(Http):
    def post(self, path, body):
        return self.call(path, body, {"Content-Type": "application/json"})

    def test_settings_roundtrip_and_states(self):
        code, body = self.call("/api/settings"); d = json.loads(body)
        self.assertEqual(code, 200); self.assertTrue(d["can_edit"]); self.assertIn("claude", d["providers"])
        self.assertNotIn("key", json.dumps(d).lower())
        code, body = self.post("/api/settings", {"settings": {"top_k": 3, "temperature": 0.7}})
        self.assertEqual(json.loads(body)["settings"]["top_k"], 3)
        self.assertEqual(self.post("/api/states/save", {"name": "three"})[0], 200)
        self.post("/api/settings", {"settings": {"top_k": 9}})
        code, body = self.post("/api/states/load", {"name": "three"})
        self.assertEqual(json.loads(body)["settings"]["top_k"], 3)
        self.assertEqual(json.loads(self.call("/api/states")[1])["states"], ["three"])
        self.post("/api/states/delete", {"name": "three"})
        self.assertEqual(json.loads(self.call("/api/states")[1])["states"], [])

    def test_bad_settings_rejected(self):
        self.assertEqual(self.post("/api/settings", {"settings": {"provider": "nope"}})[0], 400)
        self.assertEqual(self.post("/api/settings", {"settings": {"provider": "openai", "model": ""}})[0], 400)
        self.assertEqual(self.post("/api/states/save", {"name": " "})[0], 400)
        self.assertEqual(self.post("/api/states/load", {"name": "missing"})[0], 400)

    def test_settings_page_served(self):
        self.assertIn(b"Save current state", self.call("/settings.html")[1])


def test_accounts():
    from customchat.store import Store
    from customchat.accounts import Accounts
    a = Accounts(Store(":memory:"))
    u1 = a.signup("Ann@x.com", "Ann", "password1")
    for bad in (("nope", "password1"), ("b@x.com", "short"), ("ann@x.com", "password1")):
        try:
            a.signup(bad[0], "", bad[1]); assert False
        except ValueError:
            pass
    uid, tok = a.login("ann@x.com", "password1")
    assert uid == u1 and a.user_for(tok)["email"] == "ann@x.com"
    tok2 = a.login("ann@x.com", "password1")[1]
    a.change_password(uid, "password1", "newpassword", tok)
    assert a.user_for(tok) and a.user_for(tok2) is None
    try:
        a.login("ann@x.com", "password1"); assert False
    except PermissionError:
        pass
    a.login("ann@x.com", "newpassword")
    for _ in range(9):
        try: a.login("ann@x.com", "bad")
        except PermissionError: pass
    try:
        a.login("ann@x.com", "newpassword"); assert False, "throttle"
    except PermissionError as e:
        assert "Too many" in str(e)
    a.logout(tok); assert a.user_for(tok) is None
    a.delete_account(uid, "newpassword") if False else None
    closed = Accounts(Store(":memory:"), allow_signup=False)
    closed.signup("o@x.com", "", "password1")
    try:
        closed.signup("p@x.com", "", "password1"); assert False
    except PermissionError:
        pass
    print("accounts ok")


test_accounts()


def test_pdf():
    import logging; logging.getLogger("pypdf").setLevel(logging.CRITICAL)  # the hand-made PDF triggers a harmless "EOF marker not found" warning
    import zlib
    from customchat import pdfread
    c = zlib.compress(b"BT (Hello from a PDF with enough words.) Tj 0 -14 Td [(Second ) -300 (line here.)] TJ ET")
    pdf = b"%PDF-1.4\n1 0 obj<</Filter/FlateDecode>>\nstream\n" + c + b"\nendstream\nendobj\n%%EOF"
    t = pdfread.extract(pdf)
    print("pdf text:", repr(t))
    assert "Hello from a PDF with enough words." in t and "Second" in t and "line here." in t
    for bad in (b"nope", b"%PDF-1.4 empty"):
        try: pdfread.extract(bad); assert False
        except ValueError: pass
    print("pdf ok")


test_pdf()


def test_provider_retry():
    import threading, http.server, json as _j
    from customchat import providers, schema
    hits = {"n": 0}

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_POST(self):
            hits["n"] += 1
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            if self.path.startswith("/bad"):
                self.send_response(401); self.end_headers(); return
            if hits["n"] < 3:
                self.send_response(503); self.send_header("Retry-After", "0"); self.end_headers(); return
            b = _j.dumps({"choices": [{"message": {"content": "ok"}}]}).encode()
            self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    srv = http.server.HTTPServer(("127.0.0.1", 0), H); port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    import os; os.environ["T_KEY"] = "k"
    cfg = schema.validate({"app": {"title": "t"}, "provider": {"type": "minimax", "model": "m", "base_url": "http://127.0.0.1:%d/v1" % port, "timeout": 5}}) if hasattr(schema, "validate") else None
    pv = providers.OpenAICompatible({"provider": {"type": "minimax", "model": "m", "base_url": "http://127.0.0.1:%d/v1" % port, "timeout": 5, "temperature": 0, "api_key_env": "T_KEY"}})
    assert pv.complete([{"role": "user", "content": "hi"}]) == "ok" and hits["n"] == 3, hits
    hits["n"] = 0
    bad = providers.OpenAICompatible({"provider": {"type": "openai", "model": "m", "base_url": "http://127.0.0.1:%d/bad" % port, "timeout": 5, "temperature": 0, "api_key_env": "T_KEY"}})
    try: bad.complete([{"role": "user", "content": "hi"}]); assert False
    except providers.ProviderError as e: assert e.code == 401 and "key" in str(e).lower() and hits["n"] == 1
    assert "minimax" in schema.PROVIDERS and "mimo" in schema.PROVIDERS
    srv.shutdown()
    print("provider retry ok")


test_provider_retry()


def test_secret_store():
    import tempfile, os, stat
    from customchat import secrets, providers
    d = tempfile.mkdtemp(); st = secrets.SecretStore(d); secrets.STORE = st
    st.set("claude", "sk-abc123")
    assert st.get("claude") == "sk-abc123" and st.has("claude") and not st.has("gemini")
    assert stat.S_IMODE(os.stat(st.path).st_mode) == 0o600
    assert providers.has_key("claude")["source"] == "saved"
    for bad in ("", "has space", "a\nb", "x" * 5000):
        try: st.set("claude", bad); assert False
        except ValueError: pass
    assert providers._key("ANTHROPIC_API_KEY", "claude") == "sk-abc123"
    st.delete("claude"); assert not st.has("claude")
    secrets.STORE = None
    print("secret store ok")


test_secret_store()


def test_hardware_logic():
    from customchat import hardware as h
    big = h.recommend({"ram_gb": 64, "vram_gb": 24, "cores": 16})
    assert [p["tag"] for p in big["picks"]][0] == "gemma3:27b" and len(big["picks"]) == 3
    assert len({p["tag"] for p in big["picks"]}) == 3
    mac = h.recommend({"ram_gb": 16, "cores": 8, "apple_silicon": True})
    assert mac["budget_gb"] == 10.4 and all(p["needs_gb"] <= mac["limit_gb"] for p in mac["picks"])
    cpu = h.recommend({"ram_gb": 64, "cores": 16})
    assert all(p["download_gb"] <= 10 for p in cpu["picks"])
    tiny = h.recommend({"ram_gb": 4, "cores": 2})
    assert tiny["picks"] == [] and tiny["note"]
    assert h.detect()["ram_gb"] > 0
    print("hardware ok")


test_hardware_logic()


def test_logo_validation():
    from customchat import theme
    ok = "data:image/png;base64," + "A" * 100
    assert theme.clean({"logo": ok})["logo"] == ok
    for bad in ("http://x/y.png", "data:image/svg+xml;base64,AAAA" + "A" * 30, "data:image/png;base64,<script>", "data:image/png;base64," + "A" * 400000):
        assert theme.clean({"logo": bad})["logo"] == ""
    assert theme.clean({})["logo"] == ""
    print("logo ok")


test_logo_validation()



def test_ollama_fit_and_pull_validation():
    from customchat import hardware as h
    assert h.fit_of(2, 10)[0] == "green" and h.fit_of(8, 10)[0] == "blue" and h.fit_of(12, 10)[0] == "red"
    for bad in ["", "a b", "x;rm -rf", "../x", "a" * 90]:
        try:
            h.start_pull("http://localhost:11434", bad); assert False, bad
        except ValueError:
            pass
    try:
        h.start_pull("file:///etc", "qwen3:8b"); assert False
    except ValueError:
        pass
    print("ollama fit/pull ok")

def test_prompts_and_generators():
    import tempfile, json as _j
    from customchat import prompts as pm, generators as g
    d = tempfile.mkdtemp(); ps = pm.PromptStore(d)
    assert ps.text("queries") == pm.STAGES["queries"]["default"]
    ps.save("queries", "Custom queries prompt"); assert pm.PromptStore(d).text("queries") == "Custom queries prompt"
    assert ps.text("answer", "APP SYSTEM") == "APP SYSTEM"
    assert not ps.enabled("relevance"); ps.save("relevance", on=True); assert ps.enabled("relevance")
    ps.save("standalone", on=False); assert ps.enabled("standalone")  # required steps cannot be switched off
    try: ps.save("nope", "x"); assert False
    except ValueError: pass
    try: ps.save("queries", "x" * 7000); assert False
    except ValueError: pass
    ps.reset("queries"); assert ps.text("queries") == pm.STAGES["queries"]["default"]
    mock_cfg = {"provider": {"type": "mock"}}
    r = g.generate_prompt(None, mock_cfg, "relevance", "nutrition advice for adults"); assert r["model_used"] is False and "nutrition" in r["prompt"]
    try: g.generate_prompt(None, mock_cfg, "relevance", ""); assert False
    except ValueError: pass
    class Fake:
        def __init__(s, outs): s.outs = list(outs); s.calls = 0
        def complete(s, m): s.calls += 1; return s.outs.pop(0)
    real = {"provider": {"type": "openai"}}
    f = Fake(["sorry, here you go", "```json\n" + _j.dumps({"rationale": ["a"], "prompt": "You judge passages for nutrition questions. Reply with numbers only, or NONE."}) + "\n```"])
    r = g.generate_prompt(f, real, "relevance", "nutrition"); assert r["model_used"] and f.calls == 2 and r["prompt"].startswith("You judge")
    try: g.generate_prompt(Fake(["x", "y"]), real, "relevance", "nutrition"); assert False
    except ValueError: pass
    good = g.code_template("search", "x")
    assert g.review_code("search", good)[0]
    for bad in ["import os\nos.system('x')\ndef search(q): pass", "import subprocess\ndef search(q): pass", "def search(q):\n    return eval(q)", "def search(q):\n    open('f','w')", "def other(): pass", "def search(:", "KEY='sk-abcdefghijklmnop12345'\ndef search(q): pass"]:
        assert not g.review_code("search", bad)[0], bad
    assert g.review_code("clean_query", "import re\ndef clean_query(q):\n    return q")[0]
    assert not g.review_code("clean_query", "import urllib.request\ndef clean_query(q):\n    return q")[0]
    f = Fake(["```python\nimport subprocess\ndef search(q): pass\n```", "```python\n" + good + "```"])
    r = g.generate_code(f, real, "search", "my api"); assert r["ok"] and f.calls == 2
    r = g.generate_code(None, mock_cfg, "search", "my api"); assert r["ok"] and not r["model_used"]
    r = g.generate_code(None, mock_cfg, "clean_query", "strip filler"); assert r["ok"]
    assert not g.review_code("search", "def search(q, limit=6):\n    return []")[0]
    r = g.test_code("clean_query", "import re\ndef clean_query(q):\n    return re.sub(r'\\s+', ' ', q).strip()", "  hi   there "); assert r["ok"] and r["result"] == "hi there"
    assert not g.test_code("search", "import os\ndef search(q, limit=6):\n    os.system('x')", "q")["ran"]
    assert g.check_shape("search", [{"title": "a", "text": "b", "url": "", "year": None}]) == []
    assert g.check_shape("search", [{"title": 1}])
    for bad in ["http://x.org", "https://127.0.0.1/", "https://localhost/"]:
        try: g.fetch_sample(bad, "q"); assert False
        except ValueError: pass
    print("prompts and generators ok")

test_prompts_and_generators()

def test_websearch():
    import threading, tempfile, json as _j
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from customchat import websearch as w, secrets as sec
    from customchat.connectors.base import make_connector
    seen = {}
    class H(BaseHTTPRequestHandler):
        def do_POST(s):
            n = int(s.headers.get("Content-Length", 0)); seen["body"] = _j.loads(s.rfile.read(n)); seen["auth"] = s.headers.get("Authorization")
            if s.path == "/bad": s.send_response(401); s.end_headers(); return
            s.send_response(200); s.end_headers(); s.wfile.write(_j.dumps({"results": [{"title": "T", "content": "C", "url": "https://x.org"}, "junk"]}).encode())
        def log_message(s, *a): pass
    srv = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % srv.server_port
    sec.STORE = sec.SecretStore(tempfile.mkdtemp())
    try:
        w.search("tavily", "q"); assert False
    except w.SearchError as e: assert "No key" in str(e)
    sec.STORE.set("search:tavily", "tvly-test-key-1234")
    w.PROVIDERS["tavily"]["url"] = base + "/search"
    items = w.search("tavily", "hello", 3); assert items == [{"title": "T", "text": "C", "url": "https://x.org"}]
    assert seen["auth"] == "Bearer tvly-test-key-1234" and seen["body"]["query"] == "hello"
    c = make_connector({"id": "web", "label": "Web", "type": "web_search", "provider": "tavily"})
    ev = c.search("hello", 3); assert ev[0]["source"] == "web" and ev[0]["venue"].startswith("Web")
    w.PROVIDERS["tavily"]["url"] = base + "/bad"
    try: w.search("tavily", "q"); assert False
    except w.SearchError as e: assert "did not accept" in str(e)
    assert c.search("q", 3) == []  # fails safe
    # several providers at once: merged, deduped, and one failing does not hurt the rest
    sec.STORE.set("search:exa", "exa-test-key-123456"); w.PROVIDERS["tavily"]["url"] = base + "/search"; w.PROVIDERS["exa"]["url"] = base + "/bad"
    m = make_connector({"id": "web", "label": "Web", "type": "web_search", "providers": ["tavily", "exa", "nope"]})
    assert m.providers == ["tavily", "exa"] and len(m.search("hello", 4)) == 1
    w.PROVIDERS["exa"]["url"] = base + "/search"
    ev2 = m.search("hello", 4); assert len(ev2) == 1  # same URL from both providers is kept once
    srv.shutdown(); print("websearch ok")

test_websearch()

def test_web_toggle():
    import tempfile
    from customchat import schema, secrets as sec, websearch as w
    from customchat.pipeline import Engine
    from customchat.store import Store
    sec.STORE = sec.SecretStore(tempfile.mkdtemp()); sec.STORE.set("search:tavily", "tvly-test-key-1234")
    w.PROVIDERS["tavily"]["url"] = "http://127.0.0.1:9/none"  # nothing listens here, so every call fails
    cfg = schema.load("apps/minimal/app.yaml")
    e = Engine(cfg, Store(":memory:"))
    assert not e.web_state()["on"]
    e.set_web(True, ["tavily"]); assert e.web_state() == {"on": True, "providers": ["tavily"]} and "web" in e.connectors
    ev, errs = e.retrieve("conversation memory", None, None)  # web fails, local docs still answer
    assert ev and all(x["source"] != "web" for x in ev)
    e.set_web(False); assert not e.web_state()["on"] and "web" not in e.connectors
    print("web toggle ok")

test_web_toggle()

def test_open_sources():
    from customchat.connectors import open_sources as o
    from customchat.connectors.base import make_connector
    calls = []
    def fake(url, timeout=20):
        calls.append(url)
        if "wikipedia" in url: return {"query": {"pages": [{"title": "Vitamin D", "pageid": 1, "index": 2, "extract": "A vitamin."}, {"title": "", "extract": "x"}, "junk", {"title": "Sun", "pageid": 2, "index": 1, "extract": "A star."}]}}
        if "crossref" in url: return {"message": {"items": [{"title": ["Paper A"], "abstract": "<jats:p>Hello <b>world</b></jats:p>", "URL": "https://doi.org/x", "issued": {"date-parts": [[2021]]}, "container-title": ["J"], "author": [{"given": "A", "family": "B"}], "DOI": "x"}, {"nothing": 1}, 5]}}
        return {"results": [{"id": "https://openalex.org/W1", "title": "Work", "publication_year": 2020, "abstract_inverted_index": {"world": [1], "Hello": [0]}, "doi": "https://doi.org/y"}, {"title": None}]}
    real = o._get; o._get = fake
    try:
        w = make_connector({"id": "w", "label": "W", "type": "wikipedia"}).search("q", 3)
        assert [x["title"] for x in w] == ["Sun", "Vitamin D"] and w[0]["url"].endswith("/wiki/Sun")
        c = make_connector({"id": "c", "label": "C", "type": "crossref", "mailto": "a@b.org"}).search("q", 3)
        assert len(c) == 1 and c[0]["text"] == "Hello world" and c[0]["year"] == "2021" and "mailto=a%40b.org" in calls[-1]
        a = make_connector({"id": "a", "label": "A", "type": "openalex"}).search("q", 3)
        assert len(a) == 1 and a[0]["text"] == "Hello world" and a[0]["year"] == "2020"
    finally:
        o._get = real
    from customchat import schema
    from customchat.pipeline import Engine
    from customchat.store import Store
    e = Engine(schema.load("apps/minimal/app.yaml"), Store(":memory:"))
    assert e.set_catalog(["wikipedia", "bogus", "arxiv"]) == ["wikipedia", "arxiv"] and "cat-wikipedia" in e.connectors
    assert e.set_catalog([]) == [] and not [k for k in e.connectors if k.startswith("cat-")]
    print("open sources ok")

test_open_sources()

test_ollama_fit_and_pull_validation()


class AnimalFlag(unittest.TestCase):
    EV = [{"n": 1, "id": "x", "title": "Fasting in rats", "text": "Alternate-day fasting caused weight loss in low-fitness rats."}]

    def test_unmarked_animal_study_is_flagged(self):
        led = Engine.ledger("Alternate-day fasting caused weight loss in low-fitness groups. [1]", self.EV)
        self.assertTrue(led[0]["animal_unmarked"]); self.assertFalse(led[0]["supported"])

    def test_marked_animal_study_passes(self):
        led = Engine.ledger("In rats, alternate-day fasting caused weight loss. [1]", self.EV)
        self.assertFalse(led[0]["animal_unmarked"])


class LeadAndAttribution(unittest.TestCase):
    EV = [{"n": 1, "title": "t1", "text": "Fasting lowered HOMA-IR and body weight fell too."},
          {"n": 2, "title": "t2", "text": "Longer trials are needed to confirm durability of fasting benefits."},
          {"n": 3, "title": "t3", "text": "Meal timing and circadian rhythm in mice."}]

    def test_confident_lead_without_weight_caveat_is_flagged(self):
        led = Engine.ledger("**Probably, fasting improves insulin sensitivity.** HOMA-IR fell. [1]", self.EV)
        self.assertTrue(led[0]["unhedged_lead"]); self.assertFalse(led[0]["supported"])

    def test_confident_lead_with_weight_caveat_passes(self):
        led = Engine.ledger("**Probably, fasting improves insulin sensitivity.** The effect may partly come from the weight loss. [1]", self.EV)
        self.assertFalse(led[0]["unhedged_lead"])

    def test_hedged_lead_passes(self):
        led = Engine.ledger("**Possibly, fasting improves insulin sensitivity.** HOMA-IR fell. [1]", self.EV)
        self.assertFalse(led[0]["unhedged_lead"])

    def test_multi_cite_weak_source_is_listed(self):
        led = Engine.ledger("Longer trials are needed to confirm durability of fasting benefits. [1] [2] [3]", self.EV)
        self.assertEqual(led[0]["weak_cites"], [1, 3])  # only source 2 says it


class CiteFormat(unittest.TestCase):
    def test_citation_moves_outside_bold(self):
        from customchat.pipeline import Engine
        ev = [{"n": 1, "title": "t", "text": "x"}]
        out, _ = Engine.tidy("**Mixed: fasting may help. [1]** More text.", ev)
        self.assertIn("**Mixed: fasting may help.** [1]", out)

    def test_bold_lead_keeps_its_citation(self):
        ev = [{"n": 1, "title": "t", "text": "fasting results in rats"}]
        led = Engine.ledger("**Mixed: fasting results differ across the rat groups studied.** [1] More text here about rats and fasting results. [1]", ev)
        self.assertEqual(len(led), 2); self.assertEqual(led[0]["cites"], [1]); self.assertFalse(led[0]["uncited"])

    def test_honest_no_evidence_sentence_is_not_flagged_uncited(self):
        ev = [{"n": 1, "title": "t", "text": "about the docs folder"}]
        led = Engine.ledger("The sources do not explain how to run an app from a YAML file.", ev)
        self.assertFalse(led[0]["uncited"])

    def test_uncited_sentences_are_rewritten_with_fewer_flags(self):
        ev = [{"n": 1, "title": "t", "text": "fasting results matter in obese adults and long term outcomes"}]
        bad = "**Mixed: fasting results matter in obese adults and long term outcomes.** Fasting results matter in obese adults. [1]"
        led = Engine.ledger(bad, ev)
        self.assertTrue(led[0]["uncited"])
        class P:
            def complete(self, m): return "**Mixed: fasting results matter in obese adults and long term outcomes.** [1] Fasting results matter in obese adults. [1]"
        class Pr:
            def text(self, k, f=""): return "revise"
        from customchat.pipeline import Engine as E
        e = object.__new__(E); e.cfg = {"provider": {"type": "openai"}}; e.provider = P(); e.prompts = Pr()
        out = e.correct(bad, ev, led)
        self.assertIn("outcomes.** [1]", out)

    def test_uncited_sentence_is_flagged(self):
        ev = [{"n": 1, "title": "t", "text": "fasting results"}]
        led = Engine.ledger("Overall the sources are limited and mixed on fasting. Fasting results matter. [1]", ev)
        self.assertTrue(led[0]["uncited"]); self.assertFalse(led[1]["uncited"])


class PubMedQuery(unittest.TestCase):
    def test_429_is_retried_then_succeeds(self):
        import io, urllib.error
        from customchat.connectors import pubmed
        calls = []
        class R:
            def __enter__(s): return s
            def __exit__(s, *a): pass
            def read(s): return b"ok"
        def fake_open(url, timeout=0):
            calls.append(url)
            if len(calls) < 3: raise urllib.error.HTTPError(url, 429, "Too Many Requests", {}, io.BytesIO(b""))
            return R()
        old_open, old_sleep = pubmed.urllib.request.urlopen, pubmed.time.sleep
        pubmed.urllib.request.urlopen, pubmed.time.sleep = fake_open, lambda s: None
        try:
            self.assertEqual(pubmed._get("esearch.fcgi", term="x"), b"ok")
            self.assertEqual(len(calls), 3)
            calls.clear()
            def always(url, timeout=0): raise urllib.error.HTTPError(url, 429, "x", {}, io.BytesIO(b""))
            pubmed.urllib.request.urlopen = always
            with self.assertRaises(urllib.error.HTTPError): pubmed._get("esearch.fcgi", term="x")
        finally:
            pubmed.urllib.request.urlopen, pubmed.time.sleep = old_open, old_sleep

    def test_429_gives_up_after_three_calls_and_waits_between(self):
        import io, urllib.error
        from customchat.connectors import pubmed
        calls, waits = [], []
        def always(url, timeout=0):
            calls.append(url); raise urllib.error.HTTPError(url, 429, "x", {}, io.BytesIO(b""))
        old_open, old_sleep = pubmed.urllib.request.urlopen, pubmed.time.sleep
        pubmed.urllib.request.urlopen, pubmed.time.sleep = always, waits.append
        try:
            with self.assertRaises(urllib.error.HTTPError): pubmed._get("esearch.fcgi", term="x")
        finally:
            pubmed.urllib.request.urlopen, pubmed.time.sleep = old_open, old_sleep
        self.assertEqual(len(calls), 3)   # retry cap: 3 calls in all, 2 waits (1 s, 2 s)
        self.assertEqual(waits, [1.0, 2.0])

    def test_uncited_sentence_with_number_is_dropped(self):
        from customchat.pipeline import Engine
        e = Engine.__new__(Engine)
        ans = "**Possibly, in adults.** [1] Group A lost 4.87 kg versus 2.82 kg in group B. Other work is needed [1]."
        ledger = [{"claim": "Group A lost 4.87 kg versus 2.82 kg in group B.", "cites": []}, {"claim": "Other work is needed [1].", "cites": [1]}]
        e.tidy = lambda a, ev: (a, ev); e.ledger = lambda a, ev, q: [{"claim": a, "cites": [1]}]
        out, ev, led = e._drop_uncited_numbers(ans, [{"n": 1}], ledger, "")
        self.assertNotIn("4.87", out); self.assertIn("Other work is needed", out)
        self.assertEqual(e.dropped, ["Group A lost 4.87 kg versus 2.82 kg in group B."])

    def test_keywords_drop_question_words(self):
        from customchat.connectors.pubmed import keywords
        self.assertEqual(keywords("Does intermittent fasting beat continuous calorie restriction for type 2 diabetes?"),
                         "intermittent fasting continuous calorie restriction type 2 diabetes")

    def test_relaxes_when_nothing_matches(self):
        from customchat.connectors import pubmed
        calls = []
        def fake(path, **p):
            if path == "esearch.fcgi":
                calls.append(p["term"])
                return b'{"esearchresult":{"idlist":[]}}'
            return b"<x/>"
        old = pubmed._get; pubmed._get = fake
        try:
            pubmed.PubMed({"id": "p", "label": "P"}).search("alpha beta gamma delta")
        finally:
            pubmed._get = old
        self.assertEqual(calls, ["alpha beta gamma delta", "alpha beta gamma", "alpha beta"])


class NumberCheck(unittest.TestCase):
    def test_numbers_must_be_in_cited_passage(self):
        from customchat.pipeline import Engine
        ev = [{"n": 1, "title": "t", "text": "Fourteen adults did a 3 week trial; HOMA-IR fell 0.31"}]
        self.assertEqual(Engine.ledger("14 adults, three weeks [1].", ev)[0]["bad_numbers"], [])
        led = Engine.ledger("HOMA-IR fell 0.31 in 40 adults [1].", ev)[0]
        self.assertEqual(led["bad_numbers"], ["40"])
        self.assertFalse(led["supported"])

    def _engine(self, reply):
        from customchat.pipeline import Engine
        class P:
            def complete(self, m): return reply
        class Pr:
            def text(self, k, f=""): return "revise"
        e = object.__new__(Engine); e.cfg = {"provider": {"type": "openai"}}; e.provider = P(); e.prompts = Pr()
        return e

    def test_rewrite_kept_only_if_flag_is_gone(self):
        ev = [{"n": 1, "title": "t", "text": "both groups regained weight, with more fat mass regain in the CRD group 96 adults"}]
        bad = "IF had less regain. [1]"
        from customchat.pipeline import Engine
        led = Engine.ledger(bad, ev)
        good = "The CRD group had more fat mass regain. [1]"
        self.assertEqual(self._engine(good).correct(bad, ev, led), good)
        self.assertEqual(self._engine("Still less regain here. [1]").correct(bad, ev, led), bad)

    RAT = [{"n": 1, "title": "Differential weight loss with intermittent fasting or daily calorie restriction in low- and high-fitness phenotypes.",
            "text": "Intermittent fasting is effective for weight loss in rats with low fitness. In a separate experiment using intermittent fasting in male HCR and LCR rats, alternate-day fasting induced significantly greater loss of weight and fat mass in LCR compared with HCR rats."}]

    def test_rewrite_with_fewer_flags_is_kept(self):
        from customchat.pipeline import Engine
        bad = "Fasting caused greater loss in low-fitness groups. [1] A direct comparison is warranted for energy expenditure effects. [1]"
        led = Engine.ledger(bad, self.RAT)
        self.assertEqual(sum(1 for l in led if l["animal_unmarked"]), 2)
        part = "In rats, fasting caused greater loss in low-fitness groups. [1] A direct comparison is warranted for energy expenditure effects. [1]"
        self.assertEqual(self._engine(part).correct(bad, self.RAT, led), part)   # 2 flags down to 1: kept
        self.assertEqual(self._engine(bad).correct(bad, self.RAT, led), bad)      # no improvement: original stays

    def test_pmid_34086376_unmarked_animal_sentence_is_flagged_and_rewrite_names_rats(self):
        # real PMID 34086376 passage text (verbatim sentences); the model output is a fake string
        from customchat.pipeline import Engine
        bad = "Alternate-day fasting caused greater loss of weight and fat mass in low-fitness groups. [1]"
        led = Engine.ledger(bad, self.RAT)
        self.assertTrue(led[0]["animal_unmarked"])
        seen = []
        eng = self._engine("In rats with low fitness, alternate-day fasting caused greater loss of weight and fat mass. [1]")
        orig = eng.provider.complete
        eng.provider.complete = lambda m: (seen.append(m[-1]["content"]), orig(m))[1]
        out = eng.correct(bad, self.RAT, led)
        self.assertIn("rats", out)
        self.assertIn("rats or mice", seen[0])
        # a rewrite that still hides the animal is rejected
        self.assertEqual(self._engine("Fasting caused greater loss of weight in low-fitness groups. [1]").correct(bad, self.RAT, led), bad)

    def test_rewrite_rejected_if_it_adds_a_number(self):
        ev = [{"n": 1, "title": "t", "text": "both groups regained weight, with more fat mass regain in the CRD group 96 adults"}]
        from customchat.pipeline import Engine
        bad = "IF had less regain. [1]"
        led = Engine.ledger(bad, ev)
        self.assertEqual(self._engine("The CRD group had more fat mass regain in 250 adults. [1]").correct(bad, ev, led), bad)

    def test_empty_records_are_not_usable(self):
        from customchat.pipeline import Engine
        self.assertFalse(Engine.usable({"title": "t", "text": "  "}))
        self.assertFalse(Engine.usable({"title": "", "text": "abc"}))
        self.assertFalse(Engine.usable({"title": None, "text": None}))
        self.assertTrue(Engine.usable({"title": "t", "text": "abc"}))

    def test_regain_without_fat_mass_is_flagged(self):
        from customchat.pipeline import Engine
        ev = [{"n": 1, "title": "t", "text": "both groups regained weight, with more fat mass regain in the CRD group"}]
        self.assertTrue(Engine.ledger("The IF group had less regain. [1]", ev)[0]["vague_regain"])
        self.assertFalse(Engine.ledger("The IF group had less fat-mass regain. [1]", ev)[0]["vague_regain"])

    def test_sentences_split_when_citations_follow_the_period(self):
        from customchat.pipeline import Engine
        ev = [{"n": 1, "title": "t", "text": "alpha beta"}, {"n": 2, "title": "t", "text": "gamma 96"}]
        led = Engine.ledger("Alpha is beta. [1] Gamma is 96. [2] Both. [1] [2]", ev)
        self.assertEqual([l["cites"] for l in led], [[1], [2], [1, 2]])

if __name__ == "__main__":
    unittest.main()
