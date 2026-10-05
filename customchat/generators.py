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
        "contract": ("Define search(query, limit=6). Call the API described by the user with urllib.request (no other network library) "
                     "and return a list of dicts. Each dict has: title (str), text (str, the passage), url (str), year (int or None). "
                     "Return [] on any error. Keep a timeout of 15 seconds on every request. Read any key from os.environ by name, never write a key into the code."),
        "allowed": {"json", "re", "urllib", "urllib.request", "urllib.parse", "html", "datetime", "os", "xml", "xml.etree", "xml.etree.ElementTree", "math", "time"},
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
        return {"prompt": prompt_template(stage, brief), "rationale": ["No AI model is connected, so this is the built-in prompt with your area added. Connect a model on the Model tab for a fully tailored prompt."], "model_used": False}
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
def review_code(kind, code):
    """Returns (ok, problems[]). Static checks only; this does not run the code."""
    spec = KINDS[kind]
    problems = []
    if len(code) > 12000:
        return False, ["The code is too long (limit 12000 characters)."]
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, ["Not valid Python: line %s, %s" % (e.lineno, e.msg)]
    has = False
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == spec["func"]:
            has = True
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name not in spec["allowed"] and a.name.split(".")[0] not in spec["allowed"]:
                    problems.append("Imports %s, which is not allowed here." % a.name)
        elif isinstance(n, ast.ImportFrom):
            m = n.module or ""
            if m not in spec["allowed"] and m.split(".")[0] not in spec["allowed"]:
                problems.append("Imports from %s, which is not allowed here." % m)
        elif isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name) and f.id in BANNED_CALLS:
                problems.append("Calls %s(), which is not allowed." % f.id)
            if isinstance(f, ast.Attribute) and f.attr in BANNED_ATTRS:
                problems.append("Calls .%s(), which is not allowed." % f.attr)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and re.search(r"sk-[A-Za-z0-9]{16,}|AIza[0-9A-Za-z_-]{20,}", n.value):
            problems.append("Looks like it contains an API key. Keys must come from environment variables.")
    if not has:
        problems.append("It must define %s." % spec["sig"])
    return not problems, sorted(set(problems))


def code_template(kind, brief):
    brief = re.sub(r"\s+", " ", brief).strip()[:200]
    if kind == "clean_query":
        return ('import re\n\n\ndef clean_query(query):\n    """Tidy the question into a search string. %s"""\n'
                '    q = re.sub(r"[^\\w\\s\\-]", " ", query or "")\n    q = re.sub(r"\\s+", " ", q).strip()\n    stop = {"please", "tell", "me", "about", "what", "is", "are", "the", "a", "an", "of", "can", "you"}\n'
                '    words = [w for w in q.split() if w.lower() not in stop]\n    return " ".join(words) or (query or "").strip()\n') % brief
    return ('import json, os, urllib.parse, urllib.request\n\nAPI_URL = "https://example.org/search"  # TODO: the API address from your description\n'
            'API_KEY = os.environ.get("MY_SEARCH_API_KEY", "")  # optional; set it in your environment, never in this file\n\n\n'
            'def search(query, limit=6):\n    """%s"""\n    try:\n        url = API_URL + "?" + urllib.parse.urlencode({"q": query, "limit": limit})\n'
            '        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + API_KEY} if API_KEY else {})\n'
            '        with urllib.request.urlopen(req, timeout=15) as r:\n            data = json.loads(r.read().decode("utf-8", "replace"))\n'
            '    except Exception:\n        return []\n    out = []\n    for it in (data.get("results") or [])[:limit]:\n'
            '        out.append({"title": str(it.get("title", ""))[:200], "text": str(it.get("text", ""))[:1500], "url": str(it.get("url", "")), "year": it.get("year")})\n    return out\n') % (brief or "Search connector")


def generate_code(provider, cfg, kind, brief):
    if kind not in KINDS:
        raise ValueError("Unknown code type")
    spec = KINDS[kind]
    brief = str(brief or "").strip()[:MAX_BRIEF]
    if not brief:
        raise ValueError("Describe what it should do first, for example the API address and what its results look like.")
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
                                     {"role": "user", "content": brief}])
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
