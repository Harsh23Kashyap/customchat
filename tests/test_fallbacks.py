import os, sys, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from customchat.connectors.http_json import HttpJson

BODY = {"/broken": b'{"results": [{"title": "A", ', "/empty": b"", "/ok": b'{"results":[{"title":"A","abstract":"text"}]}'}

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        b = BODY.get(self.path.split("?")[0], b"")
        self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = HTTPServer(("127.0.0.1", 0), H); cls.port = cls.s.server_address[1]
        threading.Thread(target=cls.s.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(cls): cls.s.shutdown()
    def src(self, path):
        return HttpJson({"id": "x", "label": "X", "url": "http://127.0.0.1:%d%s?q={query}" % (self.port, path), "results_path": "results"})
    def test_broken_json_becomes_text(self):
        r = self.src("/broken").search("q"); self.assertEqual(len(r), 1); self.assertIn("results", r[0]["text"])
    def test_empty_reply_is_no_results(self):
        self.assertEqual(self.src("/empty").search("q"), [])
    def test_valid_json_unchanged(self):
        r = self.src("/ok").search("q"); self.assertEqual(r[0]["title"], "A")
if __name__ == "__main__": unittest.main()
