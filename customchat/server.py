"""Small threaded HTTP server: static UI plus a JSON API. Standard library only."""
import hmac, json, mimetypes, os, re, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from . import schema, providers
from .pipeline import Engine
from .store import Store
from .exports import bibtex, pdf_bytes

WEB = os.path.join(os.path.dirname(__file__), "web")


def make_handler(cfg, engine):
    store = engine.store
    token_env = cfg["auth"]["token_env"]

    class H(BaseHTTPRequestHandler):
        server_version = "CustomChat"

        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="application/json", extra=None):
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store" if ctype == "application/json" else "no-cache")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)

        def _owner(self):
            if cfg["auth"]["mode"] == "none":
                return "local"
            want = os.environ.get(token_env, "")
            got = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
            if not want or not hmac.compare_digest(want, got):
                raise PermissionError("Sign in required")
            return "token"

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > 200_000:
                raise ValueError("Request too large")
            return json.loads(self.rfile.read(n) or b"{}")

        def _route(self, method):
            u = urlparse(self.path)
            path, qs = u.path, {k: v[0] for k, v in parse_qs(u.query).items()}
            if path == "/favicon.ico":
                return self._send(204, b"", "image/x-icon")
            if method == "GET" and not path.startswith("/api/"):
                return self._static(path)
            if path == "/api/health":
                return self._send(200, {"ok": True})
            if path == "/api/config":
                return self._send(200, schema.public_view(cfg))
            o = self._owner()
            b = self._body() if method == "POST" else {}
            if path == "/api/chats" and method == "GET":
                return self._send(200, store.chats(o, qs.get("q", "")))
            if path == "/api/chats" and method == "POST":
                return self._send(200, {"id": store.new_chat(o, b.get("title") or "New chat")})
            if path == "/api/turns":
                return self._send(200, store.turns(o, qs.get("chat", "")))
            if path == "/api/ask":
                r = engine.ask(o, b.get("chat") or store.new_chat(o), b.get("question"), b.get("sources"),
                               b.get("style", "standard"), b.get("topic"), bool(b.get("new_topic")), not b.get("fresh"))
                return self._send(200, r)
            if path == "/api/regenerate":
                t = store.turn(o, b.get("turn", ""))
                r = engine.ask(o, t["chat"], t["question"], None, b.get("style", "standard"), t["topic"], False, False)
                return self._send(200, r)
            if path == "/api/rename":
                store.rename_chat(o, b.get("chat"), b.get("title")); return self._send(200, {"ok": True})
            if path == "/api/pin":
                store.pin(o, b.get("chat"), b.get("pinned")); return self._send(200, {"ok": True})
            if path == "/api/delete":
                store.delete_chat(o, b.get("chat")); return self._send(200, {"ok": True})
            if path == "/api/restore":
                store.restore_chat(o, b.get("chat")); return self._send(200, {"ok": True})
            if path == "/api/topics":
                return self._send(200, store.topics(o))
            if path == "/api/topic-turns":
                return self._send(200, store.topic_turns(o, qs.get("topic", "")))
            if path == "/api/rename-topic":
                store.rename_topic(o, b.get("topic"), b.get("title")); return self._send(200, {"ok": True})
            if path == "/api/bibtex":
                t = store.turn(o, qs.get("turn", ""))
                return self._send(200, bibtex(t["evidence"]).encode(), "text/plain; charset=utf-8",
                                  {"Content-Disposition": 'attachment; filename="references.bib"'})
            if path == "/api/pdf":
                t = store.turn(o, qs.get("turn", ""))
                return self._send(200, pdf_bytes(cfg["app"]["title"], t), "application/pdf",
                                  {"Content-Disposition": 'attachment; filename="answer.pdf"'})
            return self._send(404, {"error": "Not found"})

        def _static(self, path):
            name = "index.html" if path in ("/", "") else path.lstrip("/")
            full = os.path.normpath(os.path.join(WEB, name))
            if not full.startswith(WEB + os.sep) or not os.path.isfile(full):
                return self._send(404, {"error": "Not found"})
            ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
            data = open(full, "rb").read()
            if name == "index.html":
                a = cfg["app"]
                data = data.decode().replace("{{TITLE}}", _esc(a["title"])).replace("{{ACCENT}}", _esc(a["accent"])).encode()
            self._send(200, data, ctype + ("; charset=utf-8" if ctype.startswith("text") or "javascript" in ctype else ""))

        def _guard(self, method):
            try:
                self._route(method)
            except PermissionError as e:
                self._send(401 if "Sign in" in str(e) else 404, {"error": str(e)})
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                self._send(400, {"error": str(e) or "Bad request"})
            except providers.ProviderError as e:
                self._send(502, {"error": str(e)})
            except Exception:
                self._send(500, {"error": "Server error"})

        def do_GET(self): self._guard("GET")
        def do_POST(self): self._guard("POST")
    return H


def _esc(s):
    return re.sub(r"[<>\"'&]", lambda m: "&#%d;" % ord(m.group()), str(s))


def serve(path, host=None, port=None):
    cfg = schema.load(path)
    store = Store(os.path.join(cfg["_dir"], cfg["storage"]["path"]) if not os.path.isabs(cfg["storage"]["path"]) else cfg["storage"]["path"])
    engine = Engine(cfg, store)
    host, port = host or cfg["server"]["host"], port or cfg["server"]["port"]
    srv = ThreadingHTTPServer((host, port), make_handler(cfg, engine))
    print("%s running at http://%s:%d  (provider: %s)" % (cfg["app"]["title"], host, port, cfg["provider"]["type"]))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
