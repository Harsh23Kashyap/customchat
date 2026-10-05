"""Free, key-free search sources: Wikipedia, Crossref and OpenAlex.

Shapes were checked against live responses on 5 Oct 2026. Each connector is tolerant of missing fields and
raises on network errors, which the pipeline reports as a source error without blocking other sources.
Crossref asks polite users to send a contact address; set `mailto` on the source block to do that.
OpenAlex works without a key for light use; set `api_key` through the OPENALEX_API_KEY environment variable for more.
"""
import json, os, re, urllib.parse, urllib.request
from .base import Evidence

UA = "customchat/1.0 (+https://github.com/Harsh23Kashyap/customchat)"


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read(3000000).decode("utf-8", "replace"))


def _clean(t):
    return " ".join(re.sub(r"<[^>]+>", " ", str(t or "")).split())


class Wikipedia:
    def __init__(self, block):
        self.id, self.label, self.b = block["id"], block["label"], block
        self.lang = re.sub(r"[^a-z\-]", "", str(block.get("lang", "en")).lower()) or "en"

    def search(self, query, k=6):
        q = urllib.parse.urlencode({"action": "query", "generator": "search", "gsrsearch": query, "gsrlimit": k, "prop": "extracts",
                                    "exintro": 1, "explaintext": 1, "exlimit": "max", "format": "json", "formatversion": 2, "redirects": 1})
        data = _get("https://%s.wikipedia.org/w/api.php?%s" % (self.lang, q))
        pages = (data.get("query") or {}).get("pages") or []
        pages = sorted((p for p in pages if isinstance(p, dict)), key=lambda p: p.get("index", 99))
        out = []
        for n, p in enumerate(pages):
            text = _clean(p.get("extract"))
            title = _clean(p.get("title"))
            if not (text and title):
                continue
            url = "https://%s.wikipedia.org/wiki/%s" % (self.lang, urllib.parse.quote(title.replace(" ", "_")))
            out.append(Evidence(title, text[:1500], url, [], "", "Wikipedia", self.id, 1.0 / (n + 1), "wiki:" + str(p.get("pageid", title))))
        return out


class Crossref:
    def __init__(self, block):
        self.id, self.label, self.b = block["id"], block["label"], block

    def search(self, query, k=6):
        args = {"query": query, "rows": k, "select": "DOI,title,abstract,URL,issued,container-title,author"}
        if self.b.get("mailto"):
            args["mailto"] = str(self.b["mailto"])[:200]
        data = _get("https://api.crossref.org/works?" + urllib.parse.urlencode(args))
        items = (data.get("message") or {}).get("items") or []
        out = []
        for n, it in enumerate(items):
            if not isinstance(it, dict):
                continue
            title = _clean((it.get("title") or [""])[0] if isinstance(it.get("title"), list) else it.get("title"))
            text = _clean(it.get("abstract"))
            if not title:
                continue
            year = ""
            try:
                year = str(it["issued"]["date-parts"][0][0] or "")
            except (KeyError, IndexError, TypeError):
                pass
            venue = _clean((it.get("container-title") or [""])[0] if isinstance(it.get("container-title"), list) else "")
            authors = [" ".join(x for x in (a.get("given"), a.get("family")) if x) for a in (it.get("author") or []) if isinstance(a, dict)][:6]
            out.append(Evidence(title, (text or title)[:1500], it.get("URL") or "", authors, year, venue or "Crossref", self.id, 1.0 / (n + 1), "doi:" + str(it.get("DOI", title[:40]))))
        return out


def _abstract(inv):
    if not isinstance(inv, dict):
        return ""
    words = {}
    for w, pos in inv.items():
        for p in pos if isinstance(pos, list) else []:
            if isinstance(p, int):
                words[p] = w
    return " ".join(words[i] for i in sorted(words))


class OpenAlex:
    def __init__(self, block):
        self.id, self.label, self.b = block["id"], block["label"], block

    def search(self, query, k=6):
        args = {"search": query, "per-page": k, "select": "id,title,publication_year,abstract_inverted_index,doi,authorships,primary_location"}
        key = os.environ.get("OPENALEX_API_KEY", "")
        if key:
            args["api_key"] = key
        data = _get("https://api.openalex.org/works?" + urllib.parse.urlencode(args))
        out = []
        for n, it in enumerate(data.get("results") or []):
            if not isinstance(it, dict) or not it.get("title"):
                continue
            title = _clean(it["title"])
            text = _abstract(it.get("abstract_inverted_index"))
            authors = [((a.get("author") or {}).get("display_name") or "") for a in (it.get("authorships") or []) if isinstance(a, dict)][:6]
            src = (((it.get("primary_location") or {}).get("source")) or {}).get("display_name") or "OpenAlex"
            out.append(Evidence(title, (text or title)[:1500], it.get("doi") or it.get("id") or "", [a for a in authors if a], it.get("publication_year") or "", src, self.id, 1.0 / (n + 1), "openalex:" + str(it.get("id", title[:40]))))
        return out
