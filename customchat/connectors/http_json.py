"""Generic REST connector: GET a URL template, map JSON fields to evidence. Covers most search APIs."""
import json, urllib.parse, urllib.request
from .base import Evidence
from .. import source_credentials


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


class _NoCredentialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Credential-bearing HTTP sources do not follow redirects; review the configured address')


class HttpJson:
    """block: url (with {query} and {k}), results_path, fields {title,text,url,authors,year,venue},
    optional header_env: {Header-Name: ENV_VAR} so keys never live in the file."""
    def __init__(self, block):
        self.id, self.label, self.b = block["id"], block["label"], block

    def search(self, query, k=6):
        url = self.b["url"].replace("{query}", urllib.parse.quote(query)).replace("{k}", str(k))
        headers = {"User-Agent": "customchat/0.1"}
        if self.b.get("header_env"):source_credentials.declared({"sources":[self.b]})
        for h, env in (self.b.get("header_env") or {}).items():
            key = source_credentials.value(self.id, env, self.b["url"])
            if not key: raise ValueError('Missing private HTTP source key: ' + env)
            headers[h] = key
        request = urllib.request.Request(url, headers=headers)
        opener = urllib.request.build_opener(_NoCredentialRedirect()).open if self.b.get('header_env') else urllib.request.urlopen
        with opener(request, timeout=self.b.get("timeout", 20)) as r:
            raw = r.read().decode("utf-8", "replace")
        try:
            data = json.loads(raw)
        except ValueError:
            # Broken or non-JSON reply: keep it as one text passage so the model can still read it.
            return [Evidence(self.b.get("name", "Source reply"), raw[:4000], url, [], "", "", self.id, 1.0)] if raw.strip() else []
        if isinstance(data, dict) and (data.get('status') == 'error' or data.get('errors')):
            raise ValueError('HTTP source rejected the query; check its key, quota and plan')
        items = dig(data, self.b.get("results_path", "")) or []
        if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
            raise ValueError('HTTP source result mapping must select a list of objects')
        f = self.b.get("fields", {})
        out = []
        for i, item in enumerate(items):
            a = dig(item, f.get("authors", "authors")) or []
            if isinstance(a, list):
                a = [x.get("name", "") if isinstance(x, dict) else str(x) for x in a]
            elif a: a = [str(a)]
            else: a = []
            out.append(Evidence(str(dig(item, f.get("title", "title")) or ""), str(dig(item, f.get("text", "abstract")) or ""),
                                str(dig(item, f.get("url", "url")) or ""), a, dig(item, f.get("year", "year")) or "",
                                str(dig(item, f.get("venue", "venue")) or ""), self.id, 1.0 / (i + 1)))
        return out[:k]
