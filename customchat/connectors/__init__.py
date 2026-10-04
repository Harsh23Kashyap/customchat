"""Connectors turn a source block from the app file into evidence.

Every connector exposes search(query, k) -> list of Evidence dicts:
  {id, title, text, url, authors, year, venue, source, score}
"""
from .base import Evidence, make_connector  # noqa: F401
