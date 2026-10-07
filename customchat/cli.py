"""customchat init | validate | run | doctor | ask"""
import argparse, json, os, shutil, sys, urllib.request
from . import schema, __version__

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "minimal")


def main(argv=None):
    try:
        _main(argv)
    except schema.ConfigError as e:
        sys.exit("There is a problem with the app file:\n  %s" % e)
    except KeyboardInterrupt:
        sys.exit(0)


def _main(argv=None):
    ap = argparse.ArgumentParser(prog="customchat", description="Build a chat app over any evidence source.")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init", help="scaffold a new app folder"); i.add_argument("name")
    st = sub.add_parser("start", help="create a local Demo workspace if absent, then run it")
    st.add_argument("--directory", default="customchat-app", help="persistent workspace, never the tool cache")
    st.add_argument("--port", type=int, default=8080)
    st.add_argument("--no-browser", action="store_true")
    st.add_argument("--lock-config", action="store_true")
    v = sub.add_parser("validate", help="check an app file"); v.add_argument("app")
    r = sub.add_parser("run", help="serve an app"); r.add_argument("app"); r.add_argument("--host"); r.add_argument("--port", type=int)
    df = sub.add_parser("config-diff", help="preview changed keys and effects without values"); df.add_argument("app"); df.add_argument("candidate")
    ca = sub.add_parser("config-apply", help="apply exact previewed config with private rollback backup")
    ca.add_argument("app"); ca.add_argument("candidate"); ca.add_argument("--current-sha", required=True); ca.add_argument("--candidate-sha", required=True)
    sub.add_parser("config-schema", help="print JSON Schema for editor autocomplete")
    cd = sub.add_parser("config-doctor", help="offline line/key configuration checks"); cd.add_argument("app")
    d = sub.add_parser("doctor", help="check provider and sources"); d.add_argument("app")
    ev = sub.add_parser("eval", help="run questions from a file and report citation coverage"); ev.add_argument("app"); ev.add_argument("questions", help="text file, one question per line")
    a = sub.add_parser("ask", help="ask one question from the terminal"); a.add_argument("app"); a.add_argument("question"); a.add_argument("--json", action="store_true")
    ex = sub.add_parser("export", help="export app YAML, look, prompts and local documents, without private state")
    ex.add_argument("app"); ex.add_argument("output", help="new ZIP file; never overwritten")
    if argv is None: argv = sys.argv[1:]
    if not argv: argv = ["start"]
    args = ap.parse_args(argv)
    if args.cmd == "config-diff":
        from .configchange import diff
        print(json.dumps(diff(args.app,args.candidate),indent=2)); return
    if args.cmd == "config-apply":
        from .configchange import apply
        backup=apply(args.app,args.candidate,args.current_sha,args.candidate_sha)
        print("Applied file. Rollback backup: " + backup)
        print("Restart the app to load it. Review auth/source/network changes before launch."); return
    if args.cmd == "config-schema":
        from .configdoctor import editor_schema
        print(json.dumps(editor_schema(), indent=2)); return
    if args.cmd == "config-doctor":
        from .configdoctor import report
        if not report(args.app): raise SystemExit(1)
        return
    if args.cmd == "init":
        if os.path.exists(args.name):
            sys.exit("%s already exists" % args.name)
        shutil.copytree(TEMPLATE, args.name, ignore=shutil.ignore_patterns("__pycache__", "*.db"))
        print("Created %s/. Next: customchat run %s/app.yaml" % (args.name, args.name))
    elif args.cmd == "export":
        from .portable import export_app, ExportError
        try:
            m = export_app(args.app, args.output)
        except (ExportError, OSError) as e:
            sys.exit("Export stopped: %s" % e)
        print("Exported %d app files to %s. No keys or private session state copied." % (len(m["files"]), args.output))
        print("Review included local documents before sharing.")
    elif args.cmd == "start":
        from .launcher import start
        start(args.directory, args.port, args.no_browser, args.lock_config)
    elif args.cmd == "validate":
        try:
            c = schema.load(args.app)
        except (schema.ConfigError, OSError) as e:
            sys.exit("Invalid: %s" % e)
        print("OK: %s, %d source(s), provider %s" % (c["app"]["title"], len(c["sources"]), c["provider"]["type"]))
    elif args.cmd == "run":
        from .server import serve
        serve(args.app, args.host, args.port)
    elif args.cmd == "doctor":
        doctor(args.app)
    elif args.cmd == "eval":
        from .pipeline import Engine
        from .store import Store
        c = schema.load(args.app)
        qs = [x.strip() for x in open(args.questions, encoding="utf-8") if x.strip() and not x.startswith("#")]
        e = Engine(c, Store(":memory:"))
        tot = cited = 0
        for q in qs:
            res = e.ask("eval", e.store.new_chat("eval"), q)
            led = res["ledger"]; ok = sum(1 for l in led if l["supported"])
            tot += len(led); cited += ok
            print("%-60s evidence=%d claims=%d supported=%d" % (q[:60], len(res["evidence"]), len(led), ok))
        print("coverage: %d/%d claims cited (%.0f%%)" % (cited, tot, 100.0 * cited / tot if tot else 0))
    elif args.cmd == "ask":
        from .pipeline import Engine
        from .store import Store
        c = schema.load(args.app)
        e = Engine(c, Store(":memory:"))
        res = e.ask("local", e.store.new_chat("local"), args.question)
        if args.json:
            print(json.dumps({k: res[k] for k in ("question", "standalone", "answer", "evidence", "ledger")}, indent=2)); return
        print(res["answer"])
        for ev in res["evidence"]:
            print("  [%d] %s %s" % (ev["n"], ev["title"], ev["url"]))


def doctor(path):
    c = schema.load(path)
    p = c["provider"]
    print("provider:", p["type"], p["model"])
    if p["type"] == "ollama":
        base = (p["base_url"] or os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
        try:
            tags = json.loads(urllib.request.urlopen(base + "/api/tags", timeout=5).read())
            names = [m["name"] for m in tags.get("models", [])]
            ok = any(n == p["model"] or n.startswith(p["model"] + ":") for n in names)
            print("  ollama reachable; model %s %s" % (p["model"], "installed" if ok else "NOT installed, run: ollama pull " + p["model"]))
        except Exception as e:
            print("  ollama NOT reachable at %s (%s). Install from https://ollama.com and run `ollama serve`." % (base, type(e).__name__))
    elif p["api_key_env"]:
        print("  key env %s: %s" % (p["api_key_env"], "set" if os.environ.get(p["api_key_env"]) else "NOT set"))
    from .connectors import make_connector
    for s in c["sources"]:
        try:
            conn = make_connector(s, c["_dir"])
            n = len(getattr(conn, "docs", [])) if s["type"] == "local_files" else None
            print("  source %s (%s): ready%s" % (s["id"], s["type"], "" if n is None else ", %d chunks" % n))
        except Exception as e:
            print("  source %s: FAILED %s" % (s["id"], e))


if __name__ == "__main__":
    main()
