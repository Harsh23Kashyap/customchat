import importlib, os, sys


def Evidence(title="", text="", url="", authors=None, year="", venue="", source="", score=0.0, id=""):
    return {"id": id or title[:60], "title": title, "text": text, "url": url, "authors": authors or [],
            "year": str(year or ""), "venue": venue, "source": source, "score": float(score)}


def make_connector(block, base_dir="."):
    t = block["type"]
    if t == "local_files":
        from .local_files import LocalFiles
        return LocalFiles(block, base_dir)
    if t == "http_json":
        from .http_json import HttpJson
        return HttpJson(block)
    if t == "pubmed":
        from .pubmed import PubMed
        return PubMed(block)
    if t == "arxiv":
        from .arxiv import Arxiv
        return Arxiv(block)
    if t in ("wikipedia", "crossref", "openalex"):
        from . import open_sources
        return {"wikipedia": open_sources.Wikipedia, "crossref": open_sources.Crossref, "openalex": open_sources.OpenAlex}[t](block)
    if t == "web_search":
        from .web_search import WebSearch
        return WebSearch(block)
    if t == "python":
        if block.get('execution') == 'bounded':
            from .bounded import BoundedPlugin
            return BoundedPlugin(block, base_dir)
        # plugin: module:function, function(query, k) -> list of Evidence dicts
        mod, _, fn = block["entry"].partition(":")
        if base_dir not in sys.path:
            sys.path.insert(0, os.path.abspath(base_dir))
        f = getattr(importlib.import_module(mod), fn)

        class Plugin:
            def __init__(self): self.id = block["id"]; self.label = block["label"]
            def search(self, q, k):
                out = []
                for e in f(q, k):
                    e = {**Evidence(), **e}
                    e["source"] = self.id
                    out.append(e)
                return out
        return Plugin()
    raise ValueError("Unknown connector " + t)
