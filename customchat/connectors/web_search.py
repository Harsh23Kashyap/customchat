"""Live web results through the user's own search key. Fails safe: any error returns no results."""
from .base import Evidence
from .. import websearch


class WebSearch:
    def __init__(self, block):
        self.id, self.label, self.b = block["id"], block["label"], block
        self.provider = block.get("provider", "tavily")

    def search(self, query, k=6):
        try:
            items = websearch.search(self.provider, query, k)
        except websearch.SearchError:
            return []
        return [Evidence(i["title"], i["text"], i["url"], [], "", "Web (%s)" % websearch.PROVIDERS[self.provider]["label"], self.id, 1.0 / (n + 1), i["url"] or i["title"][:60]) for n, i in enumerate(items)]
