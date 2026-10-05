"""Small threaded HTTP server: static UI plus a JSON API. Standard library only."""
import uuid, hmac, json, mimetypes, os, re, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from . import schema, providers, fetch
from .pipeline import Engine
from .store import Store
from .exports import bibtex, pdf_bytes, chat_markdown
import time, collections

WEB = os.path.join(os.path.dirname(__file__), "web")


def make_handler(cfg, engine):
    store = engine.store
    token_env = cfg["auth"]["token_env"]
    hits = collections.defaultdict(list)

    def settings_view():
        p, r = cfg["provider"], cfg["retrieval"]
        return {"provider": p["type"], "model": p["model"], "base_url": p["base_url"], "temperature": p["temperature"],
                "top_k": r["top_k"], "query_rewrite": bool(r.get("query_rewrite"))}

    def can_edit(h):
        return cfg["auth"]["mode"] != "none" or h.client_address[0] in ("127.0.0.1", "::1")

    def apply_settings(v):
        import copy
        new = copy.deepcopy(cfg)
        if "provider" in v: new["provider"]["type"] = str(v["provider"])
        if "model" in v: new["provider"]["model"] = str(v["model"])[:120]
        if "base_url" in v: new["provider"]["base_url"] = str(v["base_url"])[:300]
        if "temperature" in v: new["provider"]["temperature"] = max(0.0, min(2.0, float(v["temperature"])))
        if "top_k" in v: new["retrieval"]["top_k"] = max(1, min(20, int(v["top_k"])))
        if "query_rewrite" in v: new["retrieval"]["query_rewrite"] = bool(v["query_rewrite"])
        try:
            schema.validate({k: v for k, v in new.items() if k != "_dir"})
        except schema.ConfigError as e:
            raise ValueError(str(e)) from None
        cfg["provider"], cfg["retrieval"] = new["provider"], new["retrieval"]
        engine.provider = providers.make(cfg)
        engine._cache.clear()

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
            self.send_header("X-Request-Id", uuid.uuid4().hex[:12])
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
            if n > 400_000:
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
                if qs.get("deep"):
                    return self._send(200, {"ok": True, "app": cfg["app"].get("title") or cfg["app"].get("name", ""), "provider": cfg["provider"]["type"],
                                            "sources": [x.get("id") or x.get("name") or x.get("type") for x in cfg.get("sources", [])],
                                            "db": store.ping(), "version": "0.1"})
                return self._send(200, {"ok": True})
            if path == "/api/config":
                return self._send(200, schema.public_view(cfg))
            o = self._owner()
            b = self._body() if method == "POST" else {}
            if path == "/api/settings" and method == "GET":
                return self._send(200, {"settings": settings_view(), "can_edit": can_edit(self), "providers": sorted(schema.PROVIDERS)})
            if path == "/api/settings" and method == "POST":
                if not can_edit(self):
                    return self._send(403, {"error": "Settings can only be changed from this computer or with the access token"})
                apply_settings(b.get("settings") or {})
                return self._send(200, {"settings": settings_view()})
            if path == "/api/states" and method == "GET":
                return self._send(200, {"states": store.states(o)})
            if path == "/api/states/save" and method == "POST":
                return self._send(200, {"name": store.save_state(o, b.get("name"), settings_view())})
            if path == "/api/states/load" and method == "POST":
                if not can_edit(self):
                    return self._send(403, {"error": "Settings can only be changed from this computer or with the access token"})
                apply_settings(store.get_state(o, str(b.get("name", ""))))
                return self._send(200, {"settings": settings_view()})
            if path == "/api/states/delete" and method == "POST":
                store.delete_state(o, str(b.get("name", ""))); return self._send(200, {"ok": True})
            if path == "/api/chats" and method == "GET":
                return self._send(200, store.chats(o, qs.get("q", "")))
            if path == "/api/chats" and method == "POST":
                return self._send(200, {"id": store.new_chat(o, b.get("title") or "New chat")})
            if path == "/api/turns":
                return self._send(200, store.turns(o, qs.get("chat", "")))
            if path == "/api/export-all":
                return self._send(200, json.dumps(store.export_all(o), indent=1).encode(), "application/json",
                                  {"Content-Disposition": 'attachment; filename="customchat-export.json"'})
            if path == "/api/profile":
                if method == "POST":
                    return self._send(200, {"text": store.set_profile(o, str(b.get("text", "")))})
                return self._send(200, {"text": store.get_profile(o)})
            if path == "/api/similar":
                return self._send(200, engine.similar(o, qs.get("q", "")))
            if path == "/api/rate" and method == "POST":
                return self._send(200, {"rating": store.rate(o, str(b.get("turn", "")), int(b.get("rating", 0)))})
            if path == "/api/ratings":
                return self._send(200, store.ratings(o, qs.get("chat", "")))
            if path == "/api/stats":
                return self._send(200, store.stats(o))
            if path == "/api/import" and method == "POST":
                n = store.import_chats(o, b.get("chats") or [])
                return self._send(200, {"imported": n})
            if path == "/api/export":
                ch = store.chat(o, qs.get("chat", ""))
                return self._send(200, chat_markdown(ch["title"], store.turns(o, ch["id"])).encode(), "text/markdown; charset=utf-8",
                                  {"Content-Disposition": 'attachment; filename="chat.md"'})
            if path in ("/api/ask", "/api/ask-stream", "/api/regenerate"):
                now = time.time(); hits[o] = [t for t in hits[o] if now - t < 60]
                if len(hits[o]) >= 30:
                    return self._send(429, {"error": "Too many questions, wait a moment"})
                hits[o].append(now)
            if path == "/api/ask-stream":
                if not str(b.get("question") or "").strip():
                    raise ValueError("Question must be 1-2000 characters")
                temp = bool(b.get("temporary"))
                chat = None if temp else (b.get("chat") or store.new_chat(o))
                gen = engine.ask_stream(o, chat, b.get("question"), b.get("sources"), b.get("style", "standard"),
                                        b.get("topic"), bool(b.get("new_topic")), not b.get("fresh"),
                                        temporary=temp, temp_history=b.get("history"), use_profile=bool(b.get("use_profile")))
                first = next(gen)  # validation errors surface as a normal 400 before streaming starts
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                def emit(kind, data):
                    self.wfile.write((json.dumps({"type": kind, "data": data}) + "\n").encode()); self.wfile.flush()
                emit(*first)
                try:
                    for kind, data in gen:
                        emit(kind, data)
                except providers.ProviderError as e:
                    emit("error", str(e))
                return
            if path in ("/api/ask",):
                pass
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
            if path == "/api/delete-turn":
                store.delete_turn(o, b.get("turn")); return self._send(200, {"ok": True})
            if path == "/api/restore-turn":
                store.restore_turn(o, b.get("turn")); return self._send(200, {"ok": True})
            if path == "/api/uploads" and method == "GET":
                return self._send(200, [{"id": u["id"], "name": u["name"], "chars": len(u["text"])} for u in store.uploads(o)])
            if path == "/api/uploads" and method == "POST":
                name, text = str(b.get("name", "")).strip(), str(b.get("text", ""))
                if not name or not text.strip() or len(text) > 150_000:
                    raise ValueError("Upload needs a name and text up to 150,000 characters")
                return self._send(200, {"id": store.add_upload(o, name, text)})
            if path == "/api/load-url" and method == "POST":
                name, text = fetch.load(str(b.get("url", "")).strip())
                return self._send(200, {"id": store.add_upload(o, name, text), "name": name, "chars": len(text)})
            if path == "/api/delete-upload":
                store.delete_upload(o, b.get("upload")); engine._cache.clear(); return self._send(200, {"ok": True})
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
                data = data.decode().replace("{{TITLE}}", _esc(a["title"])).replace("{{ACCENT}}", _esc(a["accent"])).replace("{{ACCENT2}}", _esc(a.get("accent2", "#d7ef72"))).replace("{{THEME}}", _esc(a["theme"])).encode()
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
