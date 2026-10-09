"""Small threaded HTTP server: static UI plus a JSON API. Standard library only."""
import uuid, hmac, json, mimetypes, os, re, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import TCPServer
from urllib.parse import urlparse, parse_qs
import base64
from . import websearch, schema, providers, fetch, pdfread, secrets, hardware, theme as themes, generators, prompts as promptmod
from .pipeline import Engine
from .store import Store
from .accounts import Accounts
from .exports import bibtex, pdf_bytes, chat_markdown, answer_markdown
import time, collections

WEB = os.path.join(os.path.dirname(__file__), "web")


def make_handler(cfg, engine):
    from . import permissions
    store = engine.store
    from .actions import Actions
    actions=Actions(cfg,store)
    from .nerdload import NerdLoader
    loader = NerdLoader(cfg.get("_dir", os.getcwd()))
    engine.nerd_loader = loader
    from .ollama_setup import OllamaSetup
    ollama_setup = OllamaSetup()
    token_env = cfg["auth"]["token_env"]
    hits = collections.defaultdict(list)
    from .budget import Budget, BudgetError
    budget = Budget(cfg, os.path.dirname(os.path.abspath(store.path)) if store.path != ":memory:" else None)
    cfg["budget"] = dict(budget.value)
    engine.provider = budget.wrap(engine.provider)
    themestore = themes.ThemeStore(os.path.dirname(os.path.abspath(store.path)) if store.path != ":memory:" else "/tmp", cfg["app"])
    from . import editstate
    state_folder = os.path.dirname(os.path.abspath(store.path)) if store.path != ":memory:" else "/tmp"
    acc = Accounts(store, bool(cfg["auth"].get("signup", True))) if cfg["auth"]["mode"] == "accounts" else None

    def turn_scopes(owner, rows):
        rows=[permissions.view(cfg,owner,row) for row in rows]
        for row in rows:
            try:
                if row.get("id"):
                    saved=store.get_state(owner, "scope-" + row["id"])
                    if permissions.allowed(cfg,owner,saved["source"],saved.get("document")): row["scope"]=saved
            except ValueError: pass
        return rows

    def safe_export(owner):
        rows=store.export_all(owner)
        for chat in rows: chat['turns']=turn_scopes(owner,chat.get('turns',[]))
        return rows

    def settings_view():
        p, r = cfg["provider"], cfg["retrieval"]
        return {"provider": p["type"], "model": p["model"], "base_url": p["base_url"], "temperature": p["temperature"],
                "top_k": r["top_k"], "query_rewrite": bool(r.get("query_rewrite"))}

    def can_edit(h):
        if cfg["auth"]["mode"] == "token":
            return True
        if acc:  # the first account created is the admin
            u = acc.user_for(h._cookie())
            first = store.q("SELECT id FROM users ORDER BY created LIMIT 1", one=True)
            return bool(u and first and first["id"] == u["id"])
        return h.client_address[0] in ("127.0.0.1", "::1")

    def apply_settings(v):
        import copy
        new = copy.deepcopy(cfg)
        if "provider" in v: new["provider"]["type"] = str(v["provider"])
        if "model" in v: new["provider"]["model"] = str(v["model"])[:120]
        if "base_url" in v: new["provider"]["base_url"] = str(v["base_url"])[:300]
        if "temperature" in v: new["provider"]["temperature"] = max(0.0, min(2.0, float(v["temperature"])))
        if "top_k" in v: new["retrieval"]["top_k"] = max(1, min(20, int(v["top_k"])))
        if "query_rewrite" in v: new["retrieval"]["query_rewrite"] = bool(v["query_rewrite"])
        from .portable import _check_values,ExportError
        try:_check_values(new['provider'])
        except ExportError:raise ValueError('Do not put credentials in the model address. Use a saved private key instead') from None
        try:
            schema.validate({k: v for k, v in new.items() if not k.startswith("_")})
        except schema.ConfigError as e:
            raise ValueError(str(e)) from None
        if cfg.get("_path"):
            persisted=schema.load(cfg["_path"])
            persisted["provider"],persisted["retrieval"]=new["provider"],new["retrieval"]
            editstate.save_config(cfg,editstate.view(persisted),editstate.revision(cfg))
        cfg["provider"], cfg["retrieval"] = new["provider"], new["retrieval"]
        engine.provider = budget.wrap(providers.make(cfg))
        engine._cache.clear()

    from .management import Management, model_review
    management = Management(cfg,engine,settings_view,apply_settings,safe_export)

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

        def _cookie(self):
            for part in self.headers.get("Cookie", "").split(";"):
                k, _, v = part.strip().partition("=")
                if k == "cc_session":
                    return v
            return ""

        def _set_cookie(self, token, max_age=30 * 86400):
            return {"Set-Cookie": "cc_session=%s; Path=/; HttpOnly; SameSite=Strict; Max-Age=%d" % (token, max_age)}

        def _owner(self):
            if cfg["auth"]["mode"] == "none":
                return "local"
            if acc:
                u = acc.user_for(self._cookie())
                if not u:
                    raise PermissionError("Sign in required")
                return u["id"]
            want = os.environ.get(token_env, "")
            got = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
            if not want or not hmac.compare_digest(want, got):
                raise PermissionError("Sign in required")
            return "token"

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > 11_500_000:
                raise OverflowError("Request too large")
            d = json.loads(self.rfile.read(n) or b"{}")
            if d is None:
                return {}
            if not isinstance(d, dict):
                raise ValueError("The request must be a JSON object")
            return d

        def _route(self, method):
            u = urlparse(self.path)
            path, qs = u.path, {k: v[0] for k, v in parse_qs(u.query).items()}
            if path == "/favicon.ico":
                logo = themestore.value.get("logo", "")
                if logo:
                    try:
                        data = base64.b64decode(logo.split(",",1)[1], validate=True)
                        if data.startswith(b"\x89PNG\r\n\x1a\n"):
                            return self._send(200, data, "image/png")
                    except (ValueError, IndexError):
                        pass
                return self._send(204, b"", "image/x-icon")
            if LOCKED and (path in LOCKED_PAGES or path.startswith(LOCKED_API)):
                return self._error_page(404) if method == "GET" and not path.startswith("/api/") else self._send(404, {"error": "Not found"})
            if method == "GET" and not path.startswith("/api/"):
                return self._static(path)
            if path == "/api/guide-seen":
                self._owner()
                guide_path = os.path.join(state_folder, "guide-seen.json")
                try:
                    with open(guide_path) as f: seen = json.load(f)
                    if not isinstance(seen, dict): seen = {}
                except (OSError, ValueError): seen = {}
                if method == "POST":
                    key = self._body().get("key")
                    if key not in ("cc_tour", "cc_cfg_tour_v1"): raise ValueError("Unknown guide")
                    seen[key] = True
                    os.makedirs(state_folder, exist_ok=True)
                    with open(guide_path, "w") as f: json.dump(seen, f)
                return self._send(200, seen)
            if path == "/api/health":
                if qs.get("deep") and can_edit(self):
                    return self._send(200, {"ok": True, "app": cfg["app"].get("title") or cfg["app"].get("name", ""), "provider": cfg["provider"]["type"],
                                            "sources": [x.get("id") or x.get("name") or x.get("type") for x in cfg.get("sources", [])],
                                            "db": store.ping(), "version": "0.1", "degraded": store.degraded})
                return self._send(200, {"ok": True, "degraded": store.degraded} if store.degraded else {"ok": True})
            if path == "/api/theme" and method == "GET":
                return self._send(200, {"theme": themestore.value, "meta": themes.meta(), "can_edit": can_edit(self)})
            if path == "/api/configuration-state":
                self._owner()
                if not can_edit(self):raise PermissionError('Only the app owner can view or edit configuration')
                if method == "POST":
                    b=self._body()
                    rev=editstate.save_config(cfg,b.get('config'),str(b.get('revision','')))
                    return self._send(200,{'revision':rev,'restart_required':True,'message':'App file saved. Restart this workspace to apply all fields. No new code or network calls ran.'})
                saved_config=editstate.saved_view(cfg)
                return self._send(200,{'config':saved_config,'runtime_config':editstate.view(cfg),'restart_required':saved_config!=editstate.view(cfg),'defaults':schema.DEFAULTS,'revision':editstate.revision(cfg),'helpers':editstate.helper_state(cfg,state_folder),'connector_keys':{k:websearch.has_key(k) for k in websearch.PROVIDERS}})
            if path == "/api/codegen/draft" and method == "POST":
                self._owner()
                if not can_edit(self):raise PermissionError('Only the app owner can save helper drafts')
                b=self._body()
                return self._send(200,editstate.save_draft(state_folder,str(b.get('kind','')),b.get('brief'),b.get('code')))
            if path == "/api/config":
                view=schema.public_view(cfg)
                principal=acc.user_for(self._cookie()) if acc else None
                view['sources']=[s for s in view['sources'] if permissions.allowed(cfg,principal['id'] if principal else None,s['id'])]
                return self._send(200, view)
            if acc and path.startswith("/api/account/"):
                b = self._body() if method == "POST" else {}
                ck = self._cookie()
                if path == "/api/account/me":
                    return self._send(200, {"user": acc.user_for(ck), "signup": acc.allow_signup})
                if path == "/api/account/signup" and method == "POST":
                    acc.signup(b.get("email"), b.get("name"), b.get("password"))
                    uid, tok = acc.login(b.get("email"), b.get("password"))
                    return self._send(200, {"user": acc.user_for(tok)}, extra=self._set_cookie(tok))
                if path == "/api/account/login" and method == "POST":
                    uid, tok = acc.login(b.get("email"), b.get("password"))
                    return self._send(200, {"user": acc.user_for(tok)}, extra=self._set_cookie(tok))
                if path == "/api/account/logout" and method == "POST":
                    acc.logout(ck)
                    return self._send(200, {"ok": True}, extra=self._set_cookie("", 0))
                u = acc.user_for(ck)
                if not u:
                    raise PermissionError("Sign in required")
                if path == "/api/account/password" and method == "POST":
                    acc.change_password(u["id"], b.get("old"), b.get("new"), ck)
                    return self._send(200, {"ok": True})
                if path == "/api/account/delete" and method == "POST":
                    acc.delete_account(u["id"], b.get("password"))
                    return self._send(200, {"ok": True}, extra=self._set_cookie("", 0))
                return self._send(404, {"error": "Not found"})
            o = self._owner()
            b = self._body() if method == "POST" else {}
            if path.startswith('/api/workspace/'):
                if not can_edit(self): raise PermissionError('Only the app owner can manage this workspace')
                return self._send(200,management.handle(o,path,method,b,qs))
            if path in ('/api/nerds','/api/nerds/stop','/api/nerds/remove'):
                if not can_edit(self) or self.client_address[0] not in ('127.0.0.1','::1'): raise PermissionError('Only the local app owner can manage imported Nerds')
                if path=='/api/nerds' and method=='GET': return self._send(200,{'workspaces':loader.list()})
                if method=='POST' and path.endswith('/stop'): return self._send(200,loader.stop(str(b.get('id',''))))
                if method=='POST' and path.endswith('/remove'): return self._send(200,loader.remove(str(b.get('id','')),b.get('confirmed')))
                raise ValueError('Unknown workspace action')
            if path == "/api/actions" and method == "GET": return self._send(200,actions.catalog())
            if path == "/api/actions/prepare" and method == "POST": return self._send(200,actions.prepare(o,b.get('tool'),b.get('args')))
            if path == "/api/actions/execute" and method == "POST": return self._send(200,actions.execute(o,b.get('ticket')))
            if path == "/api/scopes" and method == "GET":
                rows = []
                for sid, conn in engine.connectors.items():
                    if not permissions.allowed(cfg,o,sid): continue
                    docs = []
                    if hasattr(conn, "docs"):
                        try: conn.refresh()
                        except OSError: pass
                        docs = sorted({d.get("document") for d in conn.docs if d.get("document") and permissions.allowed(cfg,o,sid,d.get("document"))}) if not getattr(conn, "last_error", "") else []
                    rows.append({"source": sid, "label": conn.label, "documents": docs})
                return self._send(200, rows)
            if path == "/api/suggestions" and method == "POST":
                from .suggestions import starters, recent
                result = starters(engine,o)
                return self._send(200, dict(result, recent=[] if b.get("temporary") else recent(store, o)))
            if LOCKED and path == "/api/theme" and method == "POST":
                return self._send(404, {"error": "Not found"})
            if path == "/api/theme" and method == "POST":
                if not can_edit(self):
                    return self._send(403, {"error": "The look can only be changed from this computer or by the admin"})
                return self._send(200, {"theme": themestore.reset() if b.get("reset") else themestore.save(b.get("theme"))})
            if path == "/api/budget" and method in ("GET", "POST"):
                if not can_edit(self): raise PermissionError("Only the app owner can change the budget.")
                if method == "POST":
                    budget.save(b.get("budget", {})); cfg["budget"] = dict(budget.value)
                return self._send(200, budget.view())
            if path == "/api/docs-freshness" and method in ("GET", "POST"):
                if not can_edit(self):
                    raise PermissionError("Only the app owner can check document freshness.")
                rows = []
                for conn in engine.connectors.values():
                    if hasattr(conn, "refresh") and hasattr(conn, "status"):
                        try:
                            if conn.refresh(force=method == "POST"): engine._cache.clear()
                        except OSError:
                            engine._cache.clear()
                        rows.append(conn.status())
                return self._send(200, {"sources": rows, "mode": "Checks on questions and owner refresh; no background polling"})
            if path == "/api/app-export-check" and method == "GET":
                if not can_edit(self): raise PermissionError("Only the app owner can export configuration")
                if editstate.saved_view(cfg)!=editstate.view(cfg):raise ValueError("Saved app-file changes are waiting for restart. Restart this workspace before exporting so the ZIP cannot contain stale settings.")
                from .portable import bundle
                from .readiness import check
                import io, zipfile
                data, manifest = bundle(cfg, themestore.value, engine.prompts._load())
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    files = {n:archive.read(n) for n in archive.namelist() if not n.endswith("/")}
                readiness=check(cfg,files)
                return self._send(200, {"readiness":readiness,"warnings":manifest["warnings"],"excluded":["API keys and credentials","Accounts and chat history","Personal uploads","Installed local models"],"files":list(manifest["files"])})
            if path == "/api/app-export" and method == "GET":
                if not can_edit(self):
                    raise PermissionError("Only the app owner can export configuration.")
                if editstate.saved_view(cfg)!=editstate.view(cfg):raise ValueError("Saved app-file changes are waiting for restart. Restart this workspace before exporting so the ZIP cannot contain stale settings.")
                from .portable import bundle
                data, _ = bundle(cfg, themestore.value, engine.prompts._load())
                return self._send(200, data, "application/zip", {"Content-Disposition": 'attachment; filename="customchat-app.zip"'})
            if path in ("/api/nerds/review", "/api/nerds/load") and method == "POST":
                self._owner()
                if not can_edit(self) or self.client_address[0] not in ("127.0.0.1", "::1"): raise PermissionError("Only the local app owner on this computer can load Nerds")
                if path.endswith("review"):
                    return self._send(200, loader.review(str(b.get("name", "")), str(b.get("data", ""))))
                return self._send(200, loader.load(str(b.get("token", "")), b.get("allow_code") is True))
            if path == "/api/settings" and method == "GET":
                return self._send(200, {"settings": settings_view(), "can_edit": can_edit(self), "providers": sorted(schema.PROVIDERS)})
            if path == "/api/settings" and method == "POST":
                if not can_edit(self):
                    return self._send(403, {"error": "Settings can only be changed from this computer or with the access token"})
                with management.lock:
                    if management.active:raise ValueError('Wait for the workspace test to finish before changing settings')
                    management.history.record(o,settings_view());apply_settings(b.get("settings") or {})
                return self._send(200, {"settings": settings_view()})
            if path == "/api/source-credentials":
                if not can_edit(self):
                    return self._send(403, {"error": "Source keys can only be changed from this computer or by the admin"})
                from . import source_credentials
                if method == "GET":
                    return self._send(200, {"credentials": source_credentials.status(cfg)})
                if method == "POST":
                    with management.lock:
                        if management.active:raise ValueError("Wait for the workspace test to finish before changing keys")
                        result = source_credentials.update(cfg, b)
                        engine._cache.clear()
                    return self._send(200, {"credentials": result})
                return self._send(405, {"error": "Method not allowed"})
            if path.startswith("/api/provider/"):
                if not can_edit(self):
                    return self._send(403, {"error": "Provider settings can only be changed from this computer or by the admin"})
                if path == "/api/provider/status":
                    return self._send(200, {"keys": {k: providers.has_key(k) for k in sorted(schema.PROVIDERS)}})
                kind = str(b.get("provider") or qs.get("provider") or "")
                if kind not in schema.PROVIDERS:
                    return self._send(400, {"error": "Unknown provider"})
                base = str(b.get("base_url") or "")[:300]
                if path == "/api/provider/key" and method == "POST":
                    if b.get("clear"):
                        secrets.STORE.delete(kind)
                    else:
                        secrets.STORE.set(kind, b.get("key"))
                    engine.provider = budget.wrap(providers.make(cfg)); engine._cache.clear()
                    return self._send(200, {"key": providers.has_key(kind)})
                if path == "/api/provider/models" and method == "POST":
                    try:
                        return self._send(200, {"models": providers.list_models(cfg, kind, base)})
                    except providers.ProviderError as e:
                        return self._send(200, {"models": [], "note": str(e)})
                if path == "/api/provider/test" and method == "POST":
                    ok, msg = providers.test_connection(cfg, kind, str(b.get("model") or "")[:120], base)
                    from .management import diagnosis
                    return self._send(200, {'ok':ok,'message':msg} if ok else {'ok':False,**diagnosis(msg)})
            if path == "/api/hardware":
                if not can_edit(self):
                    return self._send(403, {"error": "Only the admin can see this computer's details"})
                return self._send(200, hardware.report(str(qs.get("base_url") or "http://localhost:11434")))
            if path.startswith("/api/prompts") or path.startswith("/api/codegen") or path.startswith("/api/websearch") or path.startswith("/api/catalog"):
                if not can_edit(self):
                    return self._send(403, {"error": "Only the admin can change prompts or generate code"})
                try:
                    if path == "/api/prompts" and method == "GET":
                        return self._send(200, {"stages": engine.prompts.view(cfg["prompt"]["system"], cfg["prompt"].get("revise",False)), "real_model": cfg["provider"]["type"] != "mock"})
                    if path == "/api/prompts/save" and method == "POST":
                        engine.prompts.save(str(b.get("key") or ""), b.get("text"), b.get("on")); engine._cache.clear()
                        return self._send(200, {"stages": engine.prompts.view(cfg["prompt"]["system"], cfg["prompt"].get("revise",False))})
                    if path == "/api/prompts/reset" and method == "POST":
                        engine.prompts.reset(str(b.get("key") or "")); engine._cache.clear()
                        return self._send(200, {"stages": engine.prompts.view(cfg["prompt"]["system"], cfg["prompt"].get("revise",False))})
                    if path == "/api/prompts/test" and method == "POST":
                        if cfg["provider"]["type"] == "mock":
                            return self._send(200, {"ok": False, "error": "Demo mode has no model to run a prompt. Connect a model on the Model tab, then try again."})
                        text = str(b.get("text") or "")[:6000]; q = str(b.get("question") or "")[:1000]; ps = str(b.get("passages") or "")[:6000]
                        if not text.strip() or not q.strip():
                            return self._send(400, {"error": "Add a prompt and a sample question first"})
                        try:
                            out = engine.provider.complete([{"role": "system", "content": text}, {"role": "user", "content": q + (("\n\nPassages:\n" + ps) if ps.strip() else "")}])
                        except providers.ProviderError as e:
                            return self._send(200, {"ok": False, "error": str(e)})
                        return self._send(200, {"ok": True, "output": (out or "")[:4000]})
                    if path == "/api/prompts/generate" and method == "POST":
                        return self._send(200, generators.generate_prompt(engine.provider, cfg, str(b.get("key") or ""), b.get("brief"), str(b.get("current") or ""), cfg["prompt"]["system"]))
                    if path == "/api/websearch/source" and method == "POST":
                        on = bool(b.get("on")); raw = b.get("providers")
                        pids = [str(x) for x in (raw if isinstance(raw, list) else [b.get("provider")] if b.get("provider") else [])][:6]
                        if on:
                            pids = [x for x in dict.fromkeys(pids) if x in websearch.PROVIDERS]
                            if not pids:
                                return self._send(400, {"error": "Save a key for a provider below first, then tick it"})
                            # Selected services without keys are paused by the connector.
                        engine.set_web(on, pids)
                        try:
                            wf = os.path.join(os.path.dirname(os.path.abspath(store.path)), "websource.json")
                            with open(wf, "w") as f:
                                json.dump({"on": on, "providers": pids}, f)
                        except OSError:
                            pass
                        return self._send(200, engine.web_state())
                    if path == "/api/catalog" and method == "POST":
                        types = engine.set_catalog([str(x) for x in (b.get("types") if isinstance(b.get("types"), list) else [])][:10])
                        try:
                            with open(os.path.join(os.path.dirname(os.path.abspath(store.path)), "catalog.json"), "w") as f:
                                json.dump({"types": types}, f)
                        except OSError:
                            pass
                        return self._send(200, {"types": types})
                    if path == "/api/websearch/status":
                        return self._send(200, {"catalog": engine.catalog_state(), "catalog_keys": {"openalex": bool(secrets.saved("catalog:openalex") or os.environ.get("OPENALEX_API_KEY"))}, "source": engine.web_state(), "providers": [{"id": k, "label": v["label"], "has_key": websearch.has_key(k)} for k, v in websearch.PROVIDERS.items()]})
                    if path == "/api/catalog/key" and method == "POST":
                        if b.get("id") != "openalex":
                            return self._send(400, {"error": "Unknown library"})
                        if b.get("clear"):
                            secrets.STORE.delete("catalog:openalex")
                        else:
                            secrets.STORE.set("catalog:openalex", b.get("key"))
                        engine._cache.clear()
                        return self._send(200, {"has_key": bool(secrets.saved("catalog:openalex") or os.environ.get("OPENALEX_API_KEY"))})
                    if path == "/api/websearch/key" and method == "POST":
                        pid = str(b.get("id") or "")
                        if pid not in websearch.PROVIDERS:
                            return self._send(400, {"error": "Unknown search provider"})
                        if b.get("clear"):
                            secrets.STORE.delete("search:" + pid)
                        else:
                            secrets.STORE.set("search:" + pid, b.get("key"))
                        return self._send(200, {"has_key": websearch.has_key(pid)})
                    if path == "/api/websearch/test" and method == "POST":
                        pid = str(b.get("id") or "")
                        try:
                            items, raw = websearch.search(pid, str(b.get("query") or "test")[:300], 3, with_raw=True, key_override=b.get("key") if "key" in b else None)
                            return self._send(200, {"ok": True, "items": [{"title": i["title"], "text": i["text"][:200], "url": i["url"]} for i in items], "raw": raw})
                        except websearch.SearchError as e:
                            return self._send(200, {"ok": False, "error": str(e), "items": []})
                    if path == "/api/codegen/infer" and method == "POST":
                        pid = generators.infer_search(b.get("brief"), b.get("key"))
                        if not pid:
                            return self._send(200, {"recognized": False, "message": "Name the API or paste its docs URL. A key alone does not identify an unknown service safely."})
                        provider = websearch.PROVIDERS[pid]
                        if b.get("save_key") and b.get("key"):
                            secrets.STORE.set("search:" + pid, b.get("key"))
                        return self._send(200, {"recognized": True, "id": pid, "name": provider["label"], "endpoint": provider["url"], "has_key": websearch.has_key(pid)})
                    if path == "/api/codegen" and method == "POST":
                        if b.get("known_provider"):
                            pid = str(b["known_provider"])
                            code = generators.known_search_template(pid)
                            ok, problems = generators.review_code("search", code)
                            return self._send(200, {"code": code, "ok": ok, "problems": problems, "model_used": False, "known_provider": pid, "filename": "user_search.py"})
                        research = ""
                        if b.get("research") and engine.provider is not None:
                            pid = str(b.get("research_with") or "")
                            if pid in websearch.PROVIDERS and websearch.has_key(pid):
                                try:
                                    found = websearch.search(pid, "API documentation request parameters response format " + str(b.get("brief") or "")[:200], 4)
                                    research = "\n\n".join("%s (%s)\n%s" % (i["title"], i["url"], i["text"][:900]) for i in found)
                                except websearch.SearchError:
                                    research = ""
                        return self._send(200, dict(generators.generate_code(engine.provider, cfg, str(b.get("kind") or ""), b.get("brief"), b.get("sample"), research), researched=bool(research)))
                    if path == "/api/codegen/test" and method == "POST":
                        return self._send(200, generators.test_code(str(b.get("kind") or ""), str(b.get("code") or ""), b.get("query")))
                    if path == "/api/codegen/sample" and method == "POST":
                        return self._send(200, generators.fetch_sample(b.get("url"), b.get("query")))
                    if path == "/api/codegen/review" and method == "POST":
                        kind = str(b.get("kind") or "")
                        if kind not in generators.KINDS:
                            return self._send(400, {"error": "Unknown code type"})
                        marks = generators.review_marks(kind, str(b.get("code") or ""))
                        return self._send(200, {"ok": not marks, "problems": sorted({m for _, m in marks}), "marks": [{"line": l, "message": m} for l, m in marks]})
                except ValueError as e:
                    return self._send(400, {"error": str(e)})
            if path.startswith("/api/ollama/setup"):
                if not can_edit(self) or self.client_address[0] not in ("127.0.0.1", "::1"):
                    raise PermissionError("Only the local app owner can set up Ollama")
                # A hostile web page must not cause local software installation.
                origin = self.headers.get("Origin")
                host = self.headers.get("Host", "")
                parsed = urlparse("http://" + host)
                if parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
                    raise PermissionError("Open CustomChat through its local address for setup")
                if origin and urlparse(origin).netloc != host:
                    raise PermissionError("Local setup requires the same origin")
                if method == "POST" and "application/json" not in self.headers.get("Content-Type", ""):
                    raise PermissionError("Local setup requires a JSON request")
                if path == "/api/ollama/setup" and method == "GET": return self._send(200, ollama_setup.status())
                if path == "/api/ollama/setup/prepare" and method == "POST": return self._send(200, ollama_setup.prepare(b.get("action")))
                if path == "/api/ollama/setup/execute" and method == "POST": return self._send(200, ollama_setup.execute(str(b.get("ticket") or ""), b.get("confirmed")))
                if path == "/api/ollama/setup/cancel" and method == "POST": return self._send(200, ollama_setup.cancel(str(b.get("id", ""))))
                if path == "/api/ollama/setup/status" and method == "GET": return self._send(200, ollama_setup.job(qs.get("id", "")))
                return self._send(404, {"error": "Not found"})
            if path == '/api/ollama/pull/review' and method == 'POST':
                if not can_edit(self): raise PermissionError('Only the app owner can download models')
                plan=model_review(cfg,b)
                plan['ticket']=management.reviews.put(o,'model',plan)
                return self._send(200,plan)
            if path == '/api/ollama/pull/execute' and method == 'POST':
                if not can_edit(self): raise PermissionError('Only the app owner can download models')
                plan=management.reviews.take(o,'model',str(b.get('ticket','')),b.get('confirmed'))
                model_review(cfg,plan)
                return self._send(200,{'id':hardware.start_pull(plan['base_url'],plan['model'])})
            if path == "/api/ollama/pull/cancel" and method == "POST":
                if not can_edit(self):
                    return self._send(403, {"error": "Only the admin can cancel downloads"})
                st = hardware.cancel_pull(str(b.get("id") or ""))
                return self._send(200, st) if st else self._send(404, {"error": "Unknown download"})
            if path == "/api/ollama/pull":
                if not can_edit(self):
                    return self._send(403, {"error": "Only the admin can download models"})
                if method == "POST":
                    try:
                        return self._send(200, {"id": hardware.start_pull(str(b.get("base_url") or ""), str(b.get("model") or ""))})
                    except ValueError as e:
                        return self._send(400, {"error": str(e)})
                st = hardware.pull_status(qs.get("id", ""))
                return self._send(200, st) if st else self._send(404, {"error": "Unknown download"})
            if path == "/api/states" and method == "GET":
                names=[n for n in store.states(o) if not n.startswith(("scope-","action-","note-","history-","workspace-"))]
                matches=[n for n in names if store.get_state(o,n)==settings_view()]
                return self._send(200, {"states": names, "current": matches[0] if len(matches)==1 else ""})
            if path == "/api/states/save" and method == "POST":
                return self._send(200, {"name": store.save_state(o, b.get("name"), settings_view())})
            if path == "/api/states/load" and method == "POST":
                if not can_edit(self):
                    return self._send(403, {"error": "Settings can only be changed from this computer or with the access token"})
                with management.lock:
                    if management.active:raise ValueError('Wait for the workspace test to finish before changing settings')
                    management.history.record(o,settings_view());apply_settings(store.get_state(o, str(b.get("name", ""))))
                return self._send(200, {"settings": settings_view()})
            if path == "/api/states/delete" and method == "POST":
                store.delete_state(o, str(b.get("name", ""))); return self._send(200, {"ok": True})
            if path == "/api/chats" and method == "GET":
                return self._send(200, store.chats(o, qs.get("q", "")))
            if path == "/api/chats" and method == "POST":
                return self._send(200, {"id": store.new_chat(o, b.get("title") or "New chat")})
            if path == "/api/turns":
                return self._send(200, turn_scopes(o, store.turns(o, qs.get("chat", ""))))
            if path == "/api/export-all":
                return self._send(200, json.dumps(safe_export(o), indent=1).encode(), "application/json",
                                  {"Content-Disposition": 'attachment; filename="customchat-export.json"'})
            if path == "/api/profile":
                if method == "POST":
                    if "fields" in b:
                        fields = store.set_profile_fields(o, b["fields"])
                        return self._send(200, {"fields": fields, "text": store.profile_context(o)})
                    return self._send(200, {"text": store.set_profile(o, str(b.get("text", "")))})
                return self._send(200, {"text": store.profile_context(o), "fields": store.get_profile_fields(o)})
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
                return self._send(200, chat_markdown(ch["title"], turn_scopes(o,store.turns(o, ch["id"]))).encode(), "text/markdown; charset=utf-8",
                                  {"Content-Disposition": 'attachment; filename="chat.md"'})
            if path in ("/api/ask", "/api/ask-stream", "/api/regenerate"):
                budget.take("question", o)
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
                                        temporary=temp, temp_history=b.get("history"), use_profile=bool(b.get("use_profile")), scope=b.get("scope"))
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
                               b.get("style", "standard"), b.get("topic"), bool(b.get("new_topic")), not b.get("fresh"), scope=b.get("scope"))
                return self._send(200, r)
            if path == "/api/regenerate":
                t = permissions.view(cfg,o,store.turn(o, b.get("turn", "")))
                try: saved_scope = store.get_state(o, "scope-" + t["id"])
                except ValueError: saved_scope = None
                r = next(data for kind, data in engine.ask_stream(o, t["chat"], t["question"], None, b.get("style", "standard"), t["topic"], False, False, scope=saved_scope) if kind == "done")
                return self._send(200, r)
            if path == "/api/branch" and method == "POST":
                target=store.turn(o,str(b.get("turn") or ""))
                if any(permissions.view(cfg,o,t)['answer'] != t['answer'] for t in store.turns(o,target['chat'])):
                    raise PermissionError("This chat contains answers no longer available. Start a new chat.")
                return self._send(200, store.branch(o, str(b.get("turn") or ""), b.get("question")))
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
            if path == "/api/upload-file" and method == "POST":
                from . import fileread
                name = str(b.get("name", "document")).strip()[:120] or "document"
                text = fileread.extract(name, base64.b64decode(str(b.get("data", "")), validate=True))
                return self._send(200, {"id": store.add_upload(o, name, text), "name": name, "chars": len(text)})
            if path == "/api/upload-pdf" and method == "POST":
                name = str(b.get("name", "document.pdf")).strip()[:120] or "document.pdf"
                text = pdfread.extract(base64.b64decode(str(b.get("data", "")), validate=True))
                return self._send(200, {"id": store.add_upload(o, name, text), "name": name, "chars": len(text)})
            if path == "/api/load-url" and method == "POST":
                name, text = fetch.load(str(b.get("url", "")).strip())
                return self._send(200, {"id": store.add_upload(o, name, text), "name": name, "chars": len(text)})
            if path == "/api/delete-upload":
                store.delete_upload(o, b.get("upload")); engine._cache.clear(); return self._send(200, {"ok": True})
            if path == "/api/topics":
                return self._send(200, [dict(t,summary="") if permissions.restricted(cfg) else t for t in store.topics(o)])
            if path == "/api/topic-turns":
                return self._send(200, turn_scopes(o, store.topic_turns(o, qs.get("topic", ""))))
            if path == "/api/rename-topic":
                store.rename_topic(o, b.get("topic"), b.get("title")); return self._send(200, {"ok": True})
            if path == "/api/bibtex":
                t = permissions.view(cfg,o,store.turn(o, qs.get("turn", "")))
                return self._send(200, bibtex(t["evidence"]).encode(), "text/plain; charset=utf-8",
                                  {"Content-Disposition": 'attachment; filename="references.bib"'})
            if path == "/api/answer-markdown":
                t=permissions.view(cfg,o,store.turn(o,qs.get('turn','')))
                return self._send(200,answer_markdown(cfg['app'],t).encode(),'text/markdown; charset=utf-8',{'Content-Disposition':'attachment; filename="answer.md"'})
            if path == "/api/pdf":
                t = permissions.view(cfg,o,store.turn(o, qs.get("turn", "")))
                return self._send(200, pdf_bytes(cfg["app"]["title"], t,themestore.value.get("light",{}).get("brand",cfg["app"]["accent"]),cfg["app"].get("tagline","")), "application/pdf",
                                  {"Content-Disposition": 'attachment; filename="answer.pdf"'})
            return self._send(404, {"error": "Not found"})

        def _error_page(self, code):
            """Branded HTML error page for browsers; JSON for everything else."""
            if "text/html" not in (self.headers.get("Accept") or ""):
                return self._send(code, {"error": ERR_PAGES.get(code, ERR_PAGES[500])[0]})
            title, msg, art = ERR_PAGES.get(code, ERR_PAGES[500])
            page = open(os.path.join(WEB, "error.html"), encoding="utf-8").read()
            for k, v in (("{{CODE}}", str(code)), ("{{TITLE}}", title), ("{{MSG}}", msg), ("{{ART}}", art)):
                page = page.replace(k, v)
            self._send(code, page.encode(), "text/html; charset=utf-8")

        def _static(self, path):
            name = "index.html" if path in ("/", "") else path.lstrip("/")
            full = os.path.normpath(os.path.join(WEB, name))
            if not full.startswith(WEB + os.sep) or not os.path.isfile(full):
                return self._error_page(404)
            ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
            data = open(full, "rb").read()
            if name == "index.html":
                a = cfg["app"]
                data = data.decode().replace("{{THEME_JSON}}", json.dumps(themestore.value).replace("<", "\\u003c")).replace("{{TITLE}}", _esc(a["title"])).replace("{{ACCENT}}", _esc(a["accent"])).replace("{{ACCENT2}}", _esc(a.get("accent2", "#d7ef72"))).replace("{{THEME}}", _esc(a["theme"])).encode()
            if name == "index.html" and LOCKED:
                data = re.sub(rb'<a[^>]*href="/settings.html"[^>]*>Configuration</a>', b"", data)
            self._send(200, data, ctype + ("; charset=utf-8" if ctype.startswith("text") or "javascript" in ctype else ""))

        def _guard(self, method):
            try:
                self._route(method)
            except PermissionError as e:
                self._send(401 if "Sign in" in str(e) else 404, {"error": str(e)})
            except OverflowError:
                self._send(413, {"error": "That file is too large. The limit is 8 MB for a PDF."})
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                self._send(400, {"error": str(e) or "Bad request"})
            except (TypeError, AttributeError):
                self._send(400, {"error": "That request had the wrong shape. Check the values and try again."})
            except BudgetError as e:
                self._send(429, {"error": str(e)})
            except providers.ProviderError as e:
                self._send(502, {"error": str(e)})
            except Exception:
                self._send(500, {"error": "Server error"})

        def do_GET(self): self._guard("GET")
        def do_POST(self): self._guard("POST")
    return H


_DOC = '<path d="M42 24h46l20 20v82H42z"/><path d="M88 24v22h20"/><path d="M54 62h40M54 76h40M54 90h26" opacity=".55"/>'
ERR_PAGES = {
    404: ("Page not found", "That page does not exist. It may have moved, or the link has a typo.", _DOC + '<circle cx="96" cy="100" r="18" fill="var(--bg)"/><path d="m109 113 16 16"/>'),
    413: ("That file is too big", "The upload is larger than the limit. PDFs can be up to 8 MB and pasted text up to 150,000 characters.", _DOC + '<path d="M75 138v-30m-12 12 12-12 12 12" stroke-width="4"/>'),
    500: ("Something went wrong", "The server hit an unexpected problem. Nothing was lost. Try again in a moment.", _DOC + '<path d="M75 58v26M75 98v2" stroke-width="5"/>'),
}


# Config lock: CUSTOMCHAT_CONFIG=off serves the chat only. No settings page, no config or key endpoints.
LOCKED = os.environ.get("CUSTOMCHAT_CONFIG", "").strip().lower() in ("off", "0", "false", "locked", "disabled")
LOCKED_PAGES = {"/settings.html", "/settings.js", "/settings.css", "/panels.js", "/pipeline.js", "/codeeditor.js", "/codeeditor.LICENSE.txt", "/workspace.js", "/splitters.js", "/sourcekeys.js"}
LOCKED_API = ("/api/source-credentials","/api/budget", "/api/docs-freshness", "/api/app-export", "/api/app-export-check", "/api/settings", "/api/provider", "/api/hardware", "/api/prompts", "/api/codegen", "/api/websearch", "/api/catalog", "/api/ollama", "/api/states", "/api/nerds", "/api/workspace")


def _esc(s):
    return re.sub(r"[<>\"'&]", lambda m: "&#%d;" % ord(m.group()), str(s))


class LocalHTTPServer(ThreadingHTTPServer):
    def server_bind(self):
        # HTTPServer's reverse-DNS lookup is unused here and can stall on macOS.
        TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


def serve(path, host=None, port=None):
    cfg = schema.load(path)
    cfg["_path"] = os.path.abspath(path)
    store = Store(os.path.join(cfg["_dir"], cfg["storage"]["path"]) if not os.path.isabs(cfg["storage"]["path"]) else cfg["storage"]["path"])
    secrets.STORE = secrets.SecretStore(os.path.dirname(os.path.abspath(store.path)) if store.path != ":memory:" else "/tmp")
    engine = Engine(cfg, store)
    try:
        wf = os.path.join(os.path.dirname(os.path.abspath(store.path)), "websource.json")
        if store.path != ":memory:" and os.path.exists(wf):
            ws = json.load(open(wf))
            pl = [x for x in (ws.get("providers") or [ws.get("provider")]) if x in websearch.PROVIDERS]
            engine.set_web(bool(ws.get("on")), pl)
    except (OSError, ValueError):
        pass
    try:
        cf = os.path.join(os.path.dirname(os.path.abspath(store.path)), "catalog.json")
        if store.path != ":memory:" and os.path.exists(cf):
            engine.set_catalog(json.load(open(cf)).get("types"))
    except (OSError, ValueError, AttributeError):
        pass
    engine.prompts = promptmod.PromptStore(os.path.dirname(os.path.abspath(store.path)) if store.path != ":memory:" else "")
    host, port = host or cfg["server"]["host"], port or cfg["server"]["port"]
    srv = LocalHTTPServer((host, port), make_handler(cfg, engine))
    print("%s running at http://%s:%d  (provider: %s)" % (cfg["app"]["title"], host, port, cfg["provider"]["type"]))
    import signal, threading
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        engine.nerd_loader.close()
        srv.server_close()
