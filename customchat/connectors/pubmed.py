"""PubMed through NCBI E-utilities (public, no key required; set NCBI_API_KEY for higher rate limits)."""
import json, os, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from .base import Evidence

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def _get(path, **params):
    if os.environ.get("NCBI_API_KEY"):
        params["api_key"] = os.environ["NCBI_API_KEY"]
    with urllib.request.urlopen(BASE + path + "?" + urllib.parse.urlencode(params), timeout=25) as r:
        return r.read()


class PubMed:
    def __init__(self, block):
        self.id, self.label, self.b = block["id"], block["label"], block

    def search(self, query, k=6):
        q = query + (" AND (" + self.b["filter"] + ")" if self.b.get("filter") else "")
        ids = json.loads(_get("esearch.fcgi", db="pubmed", term=q, retmax=k, sort="relevance", retmode="json"))["esearchresult"]["idlist"]
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
