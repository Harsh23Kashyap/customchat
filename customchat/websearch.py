"""Optional live web search through the user's own key (Tavily, Exa, Firecrawl, Parallel).

Request and response shapes were read from each provider's official API reference on 5 Oct 2026.
Keys come from the local secret store (never returned by any API) or from an environment variable.
"""
import json, os, urllib.request, urllib.error
from . import secrets

PROVIDERS = {
    "tavily": {"label": "Tavily", "env": "TAVILY_API_KEY", "url": "https://api.tavily.com/search", "auth": "bearer"},
    "exa": {"label": "Exa", "env": "EXA_API_KEY", "url": "https://api.exa.ai/search", "auth": "x-api-key"},
    "firecrawl": {"label": "Firecrawl", "env": "FIRECRAWL_API_KEY", "url": "https://api.firecrawl.dev/v2/search", "auth": "bearer"},
    "parallel": {"label": "Parallel", "env": "PARALLEL_API_KEY", "url": "https://api.parallel.ai/v1/search", "auth": "x-api-key"},
}


class SearchError(Exception):
    pass


def _name(pid):
    return "search:" + pid


def key_for(pid):
    k = secrets.STORE.get(_name(pid)) if secrets.STORE else ""
    return k or os.environ.get(PROVIDERS[pid]["env"], "")


def has_key(pid):
    return bool(key_for(pid))


def _body(pid, query, limit):
    if pid == "tavily":
        return {"query": query, "max_results": limit}
    if pid == "exa":
        return {"query": query, "numResults": limit, "contents": {"highlights": True}}
    if pid == "firecrawl":
        return {"query": query, "limit": limit}
    return {"objective": query, "search_queries": [query]}


def _s(v):
    if isinstance(v, list):
        v = " ".join(_s(x) for x in v)
    return v.strip() if isinstance(v, str) else ""


def normalize(pid, data, limit):
    """Raw response -> [{title, text, url}]. Tolerant of missing or odd fields."""
    if not isinstance(data, dict):
        return []
    if pid == "firecrawl":
        d = data.get("data")
        items = d.get("web") if isinstance(d, dict) else d
    else:
        items = data.get("results")
    out = []
    for it in (items if isinstance(items, list) else []):
        if not isinstance(it, dict):
            continue
        if pid == "tavily":
            text = _s(it.get("content"))
        elif pid == "exa":
            text = _s(it.get("highlights")) or _s(it.get("text")) or _s(it.get("summary"))
        elif pid == "firecrawl":
            text = _s(it.get("description")) or _s(it.get("markdown"))
        else:
            text = _s(it.get("excerpts"))
        title = _s(it.get("title"))
        if not (text or title):
            continue
        out.append({"title": title[:200], "text": (text or title)[:1500], "url": _s(it.get("url"))})
        if len(out) >= limit:
            break
    return out


def search(pid, query, limit=5, with_raw=False):
    if pid not in PROVIDERS:
        raise SearchError("Unknown search provider")
    key = key_for(pid)
    if not key:
        raise SearchError("No key saved for %s" % PROVIDERS[pid]["label"])
    p = PROVIDERS[pid]
    h = {"Content-Type": "application/json", "User-Agent": "customchat/1.0"}
    h["Authorization" if p["auth"] == "bearer" else "x-api-key"] = ("Bearer " + key) if p["auth"] == "bearer" else key
    req = urllib.request.Request(p["url"], json.dumps(_body(pid, str(query)[:400], int(limit))).encode(), h, method="POST")
    last = ""
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = r.read(1500000).decode("utf-8", "replace")
            break
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise SearchError("%s did not accept the key (HTTP %d)." % (p["label"], e.code))
            if e.code == 402:
                raise SearchError("%s says the account is out of credits (HTTP 402)." % p["label"])
            last = "HTTP %d" % e.code
            if e.code not in (429, 500, 502, 503, 504):
                raise SearchError("%s returned %s." % (p["label"], last))
        except Exception as e:
            last = type(e).__name__
    else:
        raise SearchError("%s could not be reached (%s)." % (p["label"], last))
    try:
        data = json.loads(raw)
    except ValueError:
        raise SearchError("%s sent something that is not JSON." % p["label"])
    items = normalize(pid, data, int(limit))
    return (items, raw[:1800]) if with_raw else items
