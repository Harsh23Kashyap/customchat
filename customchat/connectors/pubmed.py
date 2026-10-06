"""PubMed through NCBI E-utilities (public, no key required; set NCBI_API_KEY for higher rate limits)."""
import json, os, time, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from .base import Evidence

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def _get(path, **params):
    if os.environ.get("NCBI_API_KEY"):
        params["api_key"] = os.environ["NCBI_API_KEY"]
    for attempt in range(3):  # NCBI allows about 3 requests a second without a key; answer 429 with a short wait
        try:
            with urllib.request.urlopen(BASE + path + "?" + urllib.parse.urlencode(params), timeout=25) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 2:
                raise
            time.sleep(1.0 + attempt)


_STOP = set("a an the and or of to for in on at by with without is are was were be been do does did can could should would will how what which who why when where than then that this these those it its my your our i you we they there their as from about into over under between versus vs better best beat beats compare compared help helps good bad vs. any some more most less not no yes".split())


def keywords(question):
    """PubMed ANDs every word, so a full question often returns nothing. Keep the content words."""
    words = [w for w in "".join(c if c.isalnum() or c in "-'" else " " for c in question).split()]
    kept = [w for w in words if w.lower() not in _STOP]
    return " ".join(kept) or question


class PubMed:
    def __init__(self, block):
        self.id, self.label, self.b = block["id"], block["label"], block

    def search(self, query, k=6):
        flt = " AND (" + self.b["filter"] + ")" if self.b.get("filter") else ""
        ids = []
        words = keywords(query).split()
        # full keyword set first, then drop the last word until something matches (keep at least 2)
        while not ids and words:
            ids = json.loads(_get("esearch.fcgi", db="pubmed", term=" ".join(words) + flt, retmax=k, sort="relevance", retmode="json"))["esearchresult"]["idlist"]
            if len(words) <= 2:
                break
            words = words[:-1]
            if not ids:
                time.sleep(0.4)
        if not ids:
            return []
        root = ET.fromstring(_get("efetch.fcgi", db="pubmed", id=",".join(ids), retmode="xml"))
        out = []
        for i, art in enumerate(root.findall(".//PubmedArticle")):
            pmid = art.findtext(".//PMID") or ""
            abstract = " ".join("".join(t.itertext()) for t in art.findall(".//AbstractText"))
            authors = [" ".join(filter(None, [a.findtext("ForeName"), a.findtext("LastName")])) for a in art.findall(".//Author")][:6]
            out.append(Evidence("".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else "",
                                abstract, "https://pubmed.ncbi.nlm.nih.gov/%s/" % pmid, authors,
                                art.findtext(".//PubDate/Year") or "", art.findtext(".//Journal/Title") or "",
                                self.id, 1.0 / (i + 1), "PMID:" + pmid))
        return out
