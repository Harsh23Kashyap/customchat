"""Live web results through the user's own search keys. Several providers can run together.
Each provider is fail-safe on its own: one failing or out of credits never blocks the others or the local sources."""
from concurrent.futures import ThreadPoolExecutor
from .base import Evidence
from .. import websearch


class WebSearch:
    def __init__(self, block):
        self.id, self.label, self.b = block["id"], block["label"], block
        ps = block.get("providers") or ([block["provider"]] if block.get("provider") else [])
        self.providers = [p for p in ps if p in websearch.PROVIDERS]

    def _one(self, pid, query, k):
        try:
            return pid, websearch.search(pid, query, k)
        except Exception:
            return pid, []

    def search(self, query, k=6):
        if not self.providers:
            return []
        with ThreadPoolExecutor(max_workers=len(self.providers)) as ex:
            results = list(ex.map(lambda p: self._one(p, query, k), self.providers))
        out, seen = [], set()
        for rank in range(k):  # interleave so every provider is represented
            for pid, items in results:
                if rank >= len(items):
                    continue
                i = items[rank]
                key = (i["url"] or i["title"]).split("#")[0].rstrip("/").lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(Evidence(i["title"], i["text"], i["url"], [], "", "Web (%s)" % websearch.PROVIDERS[pid]["label"], self.id, 1.0 / (len(out) + 1), i["url"] or i["title"][:60]))
        return out[:k * 2]
