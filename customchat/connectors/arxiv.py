"""arXiv Atom API (public). block.category narrows the search, e.g. eess.SP for signal processing."""
import urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from .base import Evidence

NS = {"a": "http://www.w3.org/2005/Atom"}


class Arxiv:
    def __init__(self, block):
        self.id, self.label, self.b = block["id"], block["label"], block

    def search(self, query, k=6):
        q = "all:" + urllib.parse.quote(query)
        if self.b.get("category"):
            q += "+AND+cat:" + urllib.parse.quote(self.b["category"])
        url = "http://export.arxiv.org/api/query?search_query=%s&max_results=%d&sortBy=relevance" % (q, k)
        with urllib.request.urlopen(url, timeout=25) as r:
            root = ET.fromstring(r.read())
        out = []
        for i, e in enumerate(root.findall("a:entry", NS)):
            link = e.findtext("a:id", "", NS)
            out.append(Evidence(" ".join((e.findtext("a:title", "", NS) or "").split()),
                                " ".join((e.findtext("a:summary", "", NS) or "").split()), link,
                                [a.findtext("a:name", "", NS) for a in e.findall("a:author", NS)][:6],
                                (e.findtext("a:published", "", NS) or "")[:4], "arXiv", self.id, 1.0 / (i + 1),
                                "arXiv:" + link.rsplit("/", 1)[-1]))
        return out
