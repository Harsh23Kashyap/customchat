"""Generic REST connector: GET a URL template, map JSON fields to evidence. Covers most search APIs."""
import json, os, urllib.parse, urllib.request
from .base import Evidence


def dig(obj, path):
    for part in [p for p in (path or "").split(".") if p]:
        if isinstance(obj, list):
            try: obj = obj[int(part)]
            except (ValueError, IndexError): return None
        elif isinstance(obj, dict):
            obj = obj.get(part)
        else:
            return None
    return obj


class HttpJson:
    """block: url (with {query} and {k}), results_path, fields {title,text,url,authors,year,venue},
    optional header_env: {Header-Name: ENV_VAR} so keys never live in the file."""
    def __init__(self, block):
        self.id, self.label, self.b = block["id"], block["label"], block

    def search(self, query, k=6):
        url = self.b["url"].replace("{query}", urllib.parse.quote(query)).replace("{k}", str(k))
        headers = {"User-Agent": "customchat/0.1"}
        for h, env in (self.b.get("header_env") or {}).items():
            if os.environ.get(env):
                headers[h] = os.environ[env]
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=self.b.get("timeout", 20)) as r:
            data = json.loads(r.read().decode())
        f = self.b.get("fields", {})
        out = []
        for i, item in enumerate(dig(data, self.b.get("results_path", "")) or []):
            a = dig(item, f.get("authors", "authors")) or []
            if isinstance(a, list):
                a = [x.get("name", "") if isinstance(x, dict) else str(x) for x in a]
            out.append(Evidence(str(dig(item, f.get("title", "title")) or ""), str(dig(item, f.get("text", "abstract")) or ""),
                                str(dig(item, f.get("url", "url")) or ""), a, dig(item, f.get("year", "year")) or "",
                                str(dig(item, f.get("venue", "venue")) or ""), self.id, 1.0 / (i + 1)))
        return out[:k]
