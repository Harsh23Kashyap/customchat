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

    def test_followups_are_new_short_and_answerable(self):
        ev = [{"title": "Refund policy", "text": "Refunds within 30 days of purchase"}, {"title": "Store credit", "text": "Store credit after 30 days"}]
        cands = ["What is the refund policy?", "How long do I have to get a refund?", "How long do I have to get a refund today?",
                 "Who won the world cup final?", "Tell me", "Can I get store credit after 30 days?"]
        out = Engine.pick_followups(cands, "What is the refund policy?", ["Is there store credit?"], ev)
        self.assertEqual(out, ["How long do I have to get a refund?", "Can I get store credit after 30 days?"])
    def test_followups_fallback_varies_and_skips_covered_titles(self):
        eng = Engine.__new__(Engine); eng.cfg = {"provider": {"type": "mock"}}
        ev = [{"title": "Refund policy", "text": "x"}, {"title": "Store credit", "text": "y"}, {"title": "Shipping times", "text": "z"}]
        out = eng.followups("What is the refund policy?", "Refunds within 30 days.", ev)
        self.assertEqual(len(out), 2); self.assertTrue(all("Refund policy" not in o for o in out)); self.assertNotEqual(out[0].split(" ")[0:3], out[1].split(" ")[0:3])
    def test_model_stream_faults_become_plain_errors(self):
        import threading, http.server, socket, json as _j
        from customchat import providers
        class H(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            def log_message(self, *a): pass
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", 0)))
                m = self.path
                def body(code, ct, b):
                    self.send_response(code); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
                if m.startswith("/cut"):
                    self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Transfer-Encoding", "chunked"); self.end_headers()
                    for w in ("Hello ", "world "):
                        d = ("data: " + _j.dumps({"choices": [{"delta": {"content": w}}]}) + "\n\n").encode()
                        self.wfile.write(b"%x\r\n" % len(d) + d + b"\r\n"); self.wfile.flush()
                    self.connection.shutdown(socket.SHUT_RDWR); return
                if m.startswith("/e429"): return body(429, "application/json", b'{"error":{"message":"Rate limit"}}')
                if m.startswith("/html500"): return body(500, "text/html", b"<html>Bad gateway</html>")
                if m.startswith("/empty"): return body(200, "application/json", b"")
                if m.startswith("/gem"): return body(400, "application/json", b'{"error":{"code":400,"message":"API key not valid","status":"INVALID_ARGUMENT"}}')
                if m.startswith("/ssee"):
                    self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Connection", "close"); self.end_headers()
                    self.wfile.write(b'data: {"choices":[{"delta":{"content":"Hi "}}]}\n\ndata: {"error":{"message":"overloaded"}}\n\n'); self.wfile.flush(); return
                body(200, "application/json", b'{"choices":[{"message":{"content":"ok"}}]}')
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        os.environ["CC_TEST_KEY"] = "sk-x"
        def mk(path): return providers.OpenAICompatible({"provider": {"type": "openai_compatible", "base_url": "http://127.0.0.1:%d%s" % (port, path), "model": "m", "timeout": 5, "temperature": 0.2, "api_key_env": "CC_TEST_KEY"}})
        try:
            for path, text in (("/cut", "ended early"), ("/ssee", "overloaded"), ("/empty", "empty reply"), ("/e429", "rate limiting"), ("/html500", "HTTP 500"), ("/gem", "rejected")):
                got = []
                with self.assertRaises(providers.ProviderError) as c:
                    for piece in mk(path).stream([{"role": "user", "content": "x"}]): got.append(piece)
                self.assertIn(text, str(c.exception), path)
                if path in ("/cut", "/ssee"): self.assertTrue(got, "text before the cut is kept")
            with self.assertRaises(providers.ProviderError) as c: mk("/cut").complete([{"role": "user", "content": "x"}])
            self.assertIn("dropped", str(c.exception))
            self.assertEqual(mk("/fine").complete([{"role": "user", "content": "x"}]), "ok")
        finally:
            srv.shutdown(); providers._DOWN.clear()

    def test_read_only_data_folder_keeps_working(self):
        if os.geteuid() == 0: self.skipTest("root ignores file permissions")
        import stat
        d = tempfile.mkdtemp()
        try:
            s = Store(os.path.join(d, "x.db"))
            cid = s.new_chat("o", "first")  # saved normally
            self.assertEqual(s.degraded, "")
            os.chmod(os.path.join(d, "x.db"), 0o444); os.chmod(d, 0o555)
            s2 = Store(os.path.join(d, "x.db"))
            new = s2.new_chat("o", "second")  # write fails -> memory, no exception
            self.assertTrue(s2.degraded)
            self.assertEqual(s2.chat("o", new)["title"], "second")
            # a folder that cannot be created at all
            s3 = Store(os.path.join(d, "sub", "y.db"))
            self.assertTrue(s3.degraded)
            self.assertTrue(s3.new_chat("o", "third"))
        finally:
            os.chmod(d, 0o755)
            for f in os.listdir(d): os.chmod(os.path.join(d, f), 0o644)

if __name__ == "__main__": unittest.main()
