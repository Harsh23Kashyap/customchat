"""Prompt generator and code generator (the CustomNerd "AI Prompt Generator" and "AI Code Generator" ideas).

Prompt generator: you describe your domain and audience in plain words; it writes a prompt for one pipeline step in
the same shape as the built-in default for that step. With a model it asks for strict JSON and retries once on bad
output. Without a model (Demo provider, no key) it fills a template, so the button always gives something useful.

Code generator: you describe a search API or a query cleaner; it writes a small Python function. The code is only
text. It is checked here (parses, uses only allowed modules, no dangerous calls) and shown for review. CustomChat
never runs generated code by itself.
"""
import ast, json, re

from . import prompts, providers

MAX_BRIEF = 2000
KINDS = {
    "search": {
        "label": "Search connector", "filename": "user_search.py", "func": "search",
        "sig": "search(query: str, limit: int = 6) -> list",
        "contract": ("Define search(query, limit=6). Call the API described by the user with urllib.request (no other network library). "
                     "Be defensive, because real APIs differ and change: wrap every network call and all parsing in try/except; set timeout=15 on every request; "
                     "retry up to 2 more times on timeouts, HTTP 429 and 5xx with a short time.sleep back-off; send a User-Agent header; "
                     "decode bytes with errors='replace'; if the body is not valid JSON (or XML if that is what the API returns) return []; "
                     "read every field with .get() or a safe helper because fields can be missing, null, a list instead of a string, or nested differently; "
                     "skip items that have no usable text. Return a list of at most `limit` dicts, each with exactly these keys: "
                     "title (str), text (str, the passage, at most 1500 chars), url (str), year (int or None). Never raise: return [] on any error. "
                     "Read any key from os.environ by name, never write a key into the code."),
        "allowed": {"json", "re", "urllib", "urllib.request", "urllib.parse", "urllib.error", "html", "datetime", "os", "xml", "xml.etree", "xml.etree.ElementTree", "math", "time"},
    },
    "clean_query": {
        "label": "Query cleaning", "filename": "clean_query.py", "func": "clean_query",
        "sig": "clean_query(query: str) -> str",
        "contract": ("Define clean_query(query) that takes the reader's question and returns a better search string. Use only the standard "
                     "library (re, string, unicodedata). No network, no files. Always return a non-empty string; if cleaning leaves nothing, return the original query."),
        "allowed": {"re", "string", "unicodedata", "html", "json"},
    },
}
BANNED_CALLS = {"eval", "exec", "compile", "__import__", "open", "input", "breakpoint", "globals", "locals", "setattr", "delattr", "getattr"}
BANNED_ATTRS = {"system", "popen", "remove", "unlink", "rmdir", "rmtree", "rename", "chmod", "environ_set", "putenv", "kill", "fork", "spawn"}


def _extract_json(text):
    text = (text or "").strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except ValueError:
        i, j = text.find("{"), text.rfind("}")
        if 0 <= i < j:
            try:
                return json.loads(text[i:j + 1])
            except ValueError:
                return None
    return None


def _real(provider, cfg):
    return cfg.get("provider", {}).get("type") != "mock" and provider is not None


def prompt_template(stage, brief):
    """Offline fallback: the built-in default with the reader's domain added."""
    base = prompts.STAGES[stage]["default"] or "Answer using only the numbered evidence. Cite sources like [1]. Say plainly when the evidence does not cover the question."
    brief = re.sub(r"\s+", " ", brief).strip()
    if not brief:
        return base
    return "This assistant works in this area: %s\n\n%s" % (brief[:600], base)


def generate_prompt(provider, cfg, stage, brief, current="", fallback_default=""):
    if stage not in prompts.STAGES:
        raise ValueError("Unknown step")
    brief = str(brief or "").strip()[:MAX_BRIEF]
    if not brief and not current:
        raise ValueError("Describe your area and your readers first, for example: nutrition advice for adults, plain language")
    example = prompts.STAGES[stage]["default"] or fallback_default
    if not _real(provider, cfg):
        return {"prompt": prompt_template(stage, brief), "rationale": ["Demo template. Connect a model to tailor it."], "model_used": False}
    system = ("You are an expert prompt engineer for a question answering app that cites its sources.\n"
              "Write one prompt for the pipeline step \"%s\" (%s).\n"
              "Keep the structure, tone, output format and strictness of the example prompt, but tailor it to the user's area. "
              "Do not change what the step must output, because other code reads that output.\n\n"
              "EXAMPLE PROMPT:\n%s\n\n"
              "Reply with JSON only, no commentary: {\"rationale\": [up to 3 short bullets], \"prompt\": \"the new prompt text\"}." % (
                  prompts.STAGES[stage]["label"], prompts.STAGES[stage]["help"], example))
    user = "Area and readers: %s" % brief
    if current.strip():
        user += "\n\nCurrent prompt to improve:\n%s" % current.strip()[:prompts.MAX_LEN]
    err = ""
    for attempt in range(2):
        try:
            out = provider.complete([{"role": "system", "content": system + (("\nYour last reply was not valid: %s. Reply with the JSON object only." % err) if err else "")},
                                     {"role": "user", "content": user}])
        except providers.ProviderError as e:
            raise ValueError(str(e))
        d = _extract_json(out)
        p = d.get("prompt") if isinstance(d, dict) else None
        if isinstance(p, str) and 30 <= len(p.strip()) <= prompts.MAX_LEN:
            r = d.get("rationale")
            return {"prompt": p.strip(), "rationale": [str(x)[:200] for x in r][:3] if isinstance(r, list) else [], "model_used": True}
        err = "no usable \"prompt\" text" if isinstance(d, dict) else "not JSON"
    raise ValueError("The model did not return a usable prompt. Try again, or add more detail about your area.")


# ---------------- code ----------------
def review_marks(kind, code):
    """Returns [(line, message)]. Static checks only; this does not run the code."""
    spec = KINDS[kind]
    problems = []; add = lambda ln, m: problems.append((ln or 1, m))
    if len(code) > 12000:
        return [(1, "The code is too long (limit 12000 characters).")]
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [(e.lineno or 1, "Not valid Python: %s" % e.msg)]
    has = False
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == spec["func"]:
            has = True
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name not in spec["allowed"] and a.name.split(".")[0] not in spec["allowed"]:
                    add(getattr(n, "lineno", 1), "Imports %s, which is not allowed here." % a.name)
        elif isinstance(n, ast.ImportFrom):
            m = n.module or ""
            if m not in spec["allowed"] and m.split(".")[0] not in spec["allowed"]:
                add(getattr(n, "lineno", 1), "Imports from %s, which is not allowed here." % m)
        elif isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name) and f.id in BANNED_CALLS:
                add(getattr(n, "lineno", 1), "Calls %s(), which is not allowed." % f.id)
            if isinstance(f, ast.Attribute) and f.attr in BANNED_ATTRS:
                add(getattr(n, "lineno", 1), "Calls .%s(), which is not allowed." % f.attr)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and re.search(r"sk-[A-Za-z0-9]{16,}|AIza[0-9A-Za-z_-]{20,}", n.value):
            add(getattr(n, "lineno", 1), "Looks like it contains an API key. Keys must come from environment variables.")
    if not has:
        add(1, "It must define %s." % spec["sig"])
    if kind == "search" and has:
        if not any(isinstance(n, ast.Try) for n in ast.walk(tree)):
            add(1, "It has no try/except, so one odd response could crash a question. Wrap the request and the parsing.")
        if "timeout" not in code:
            add(1, "A request has no timeout, so a slow server could hang a question.")
    return sorted(set(problems))


def review_code(kind, code):
    marks = review_marks(kind, code)
    return not marks, sorted({m for _, m in marks})


def code_template(kind, brief):
    brief = re.sub(r"\s+", " ", brief).strip()[:200]
    if kind == "clean_query":
        return ('import re\n\n\ndef clean_query(query):\n    """Tidy the question into a search string. %s"""\n'
                '    q = re.sub(r"[^\\w\\s\\-]", " ", query or "")\n    q = re.sub(r"\\s+", " ", q).strip()\n    stop = {"please", "tell", "me", "about", "what", "is", "are", "the", "a", "an", "of", "can", "you"}\n'
                '    words = [w for w in q.split() if w.lower() not in stop]\n    return " ".join(words) or (query or "").strip()\n') % brief
    return TEMPLATE % (brief or "Search connector")


TEMPLATE = '''import json, os, time, urllib.error, urllib.parse, urllib.request

API_URL = "https://example.org/search"  # TODO: the API address from your description
API_KEY = os.environ.get("MY_SEARCH_API_KEY", "")  # optional; set it in your environment, never in this file


def _get(url, tries=3):
    """GET with a timeout and a few retries. Returns the body text, or None."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "customchat/1.0", **({"Authorization": "Bearer " + API_KEY} if API_KEY else {})})
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.read(2000000).decode("utf-8", "replace")
        except Exception as e:
            code = e.code if isinstance(e, urllib.error.HTTPError) else 0
            if i + 1 < tries and (code in (429, 500, 502, 503, 504) or not code):
                time.sleep(1.5 * (i + 1))
                continue
            return None


def _text(v):
    if isinstance(v, list):
        v = " ".join(_text(x) for x in v)
    return v.strip() if isinstance(v, str) else ""


def search(query, limit=6):
    """%s"""
    try:
        body = _get(API_URL + "?" + urllib.parse.urlencode({"q": query, "limit": limit}))
        data = json.loads(body) if body else {}
        items = data.get("results") if isinstance(data, dict) else data
        out = []
        for it in (items if isinstance(items, list) else []):
            if not isinstance(it, dict):
                continue
            text = _text(it.get("text") or it.get("abstract") or it.get("snippet"))
            title = _text(it.get("title"))
            if not (text or title):
                continue
            year = it.get("year")
            out.append({"title": title[:200], "text": (text or title)[:1500], "url": _text(it.get("url")),
                        "year": year if isinstance(year, int) else None})
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []
'''


def generate_code(provider, cfg, kind, brief, sample="", research=""):
    if kind not in KINDS:
        raise ValueError("Unknown code type")
    spec = KINDS[kind]
    brief = str(brief or "").strip()[:MAX_BRIEF]
    if not brief:
        raise ValueError("Describe what it should do first, for example the API address and what its results look like.")
    sample = str(sample or "")[:6000]
    research = str(research or "")[:5000]
    if not _real(provider, cfg):
        code = code_template(kind, brief); ok, probs = review_code(kind, code)
        return {"code": code, "ok": ok, "problems": probs, "filename": spec["filename"], "model_used": False,
                "note": "No AI model is connected, so this is a starter template. Connect a model on the Model tab to generate code from your description."}
    system = ("You write small, safe Python functions for a question answering app.\n%s\n"
              "Reply with one ```python code block and nothing else. Plain code, short comments, no placeholders left for the user to guess except API addresses you were not given." % spec["contract"])
    err = ""
    for attempt in range(3):
        try:
            out = provider.complete([{"role": "system", "content": system + (("\nFix these problems from your last attempt: %s" % err) if err else "")},
                                     {"role": "user", "content": brief + (("\n\nNotes found on the web about this API (may be incomplete; trust the user description first):\n" + research) if research else "") + (("\n\nHere is a real raw response from the API. Write the parsing for exactly this shape, and stay tolerant of missing fields:\n" + sample) if sample else "")}])
        except providers.ProviderError as e:
            raise ValueError(str(e))
        m = re.search(r"```(?:python)?\s*(.*?)```", out or "", flags=re.S)
        code = (m.group(1) if m else out or "").strip() + "\n"
        ok, probs = review_code(kind, code)
        if ok:
            return {"code": code, "ok": True, "problems": [], "filename": spec["filename"], "model_used": True, "note": ""}
        err = "; ".join(probs)
    return {"code": code, "ok": False, "problems": probs, "filename": spec["filename"], "model_used": True,
            "note": "The model's code did not pass the safety review after 3 tries. Review the notes, edit it, or add detail to your description."}


RUNNER = r"""
import sys, json, resource
resource.setrlimit(resource.RLIMIT_AS, (768 * 2**20, 768 * 2**20)); resource.setrlimit(resource.RLIMIT_CPU, (20, 20)); resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
spec = json.loads(sys.stdin.read())
ns = {"__name__": "helper"}
exec(compile(spec["code"], "helper.py", "exec"), ns)
r = ns[spec["func"]](*spec["args"])
print("\n@@RESULT@@" + json.dumps(r, default=str)[:200000])
"""


def check_shape(kind, result):
    """Problems in what a helper returned. [] means it matches the expected shape."""
    probs = []
    if kind == "clean_query":
        if not isinstance(result, str) or not result.strip():
            probs.append("It must return a non-empty string.")
        return probs
    if not isinstance(result, list):
        return ["It must return a list."]
    for i, it in enumerate(result[:50]):
        if not isinstance(it, dict):
            probs.append("Item %d is not a dict." % (i + 1)); continue
        for k, t in (("title", str), ("text", str), ("url", str)):
            if not isinstance(it.get(k), t):
                probs.append("Item %d: '%s' must be text." % (i + 1, k))
        if it.get("year") is not None and not isinstance(it.get("year"), int):
            probs.append("Item %d: 'year' must be a whole number or None." % (i + 1))
        if not (it.get("text") or "").strip():
            probs.append("Item %d has empty text." % (i + 1))
    return sorted(set(probs))[:8]


def test_code(kind, code, query):
    """Runs reviewed code once in a separate, limited process. Only called after an explicit click."""
    import subprocess, sys, tempfile, json as _j, time as _t
    if kind not in KINDS:
        raise ValueError("Unknown code type")
    query = str(query or "").strip()[:300]
    if not query:
        raise ValueError("Type a sample question to try it with.")
    ok, probs = review_code(kind, code)
    if not ok:
        return {"ran": False, "ok": False, "problems": probs, "error": "Fix the safety problems first.", "items": [], "seconds": 0}
    spec = KINDS[kind]
    args = [query, 5] if kind == "search" else [query]
    t0 = _t.time(); err = ""; result = None; ran = True
    with tempfile.TemporaryDirectory() as d:
        try:
            p = subprocess.run([sys.executable, "-I", "-c", RUNNER], input=_j.dumps({"code": code, "func": spec["func"], "args": args}), capture_output=True,
                               text=True, timeout=60, cwd=d, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"})
            out = p.stdout or ""
            if "@@RESULT@@" in out:
                try:
                    result = _j.loads(out.split("@@RESULT@@", 1)[1])
                except ValueError:
                    err = "It returned something that is not plain data."
            else:
                err = (p.stderr or "It stopped without a result.").strip().splitlines()[-1][:300] if (p.stderr or "").strip() else ("It ran for 20 seconds without finishing, so it was stopped." if _t.time() - t0 >= 18 else "It stopped without a result.")
        except subprocess.TimeoutExpired:
            err = "It took longer than 60 seconds and was stopped."
    shape = check_shape(kind, result) if result is not None else []
    items = result if isinstance(result, list) else []
    empty = kind == "search" and result == [] and not err
    return {"ran": ran, "ok": result is not None and not shape and not empty and not err, "error": err, "problems": shape,
            "empty": empty, "items": [{k: (str(v)[:240] if v is not None else None) for k, v in it.items()} for it in items[:5] if isinstance(it, dict)],
            "result": result if isinstance(result, str) else None, "count": len(items), "seconds": round(_t.time() - t0, 1)}


def fetch_sample(url, query):
    """One real request so the user can see the raw response. https only, public hosts only."""
    import socket, ipaddress, urllib.request, urllib.parse
    u = urllib.parse.urlparse(str(url or "").strip())
    if u.scheme != "https" or not u.hostname:
        raise ValueError("Use a full https:// address.")
    try:
        for fam, _, _, _, sa in socket.getaddrinfo(u.hostname, u.port or 443, proto=socket.IPPROTO_TCP):
            ip = ipaddress.ip_address(sa[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                raise ValueError("That address points to a private network, so it is not fetched.")
    except socket.gaierror:
        raise ValueError("That host name could not be found.")
    full = str(url).replace("{query}", urllib.parse.quote(str(query or "test")))
    req = urllib.request.Request(full, headers={"User-Agent": "customchat/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            body = r.read(8000).decode("utf-8", "replace"); return {"status": r.status, "type": r.headers.get("Content-Type", ""), "body": body[:6000]}
    except Exception as e:
        raise ValueError("The request failed: %s" % (getattr(e, "reason", None) or getattr(e, "code", None) or type(e).__name__))
