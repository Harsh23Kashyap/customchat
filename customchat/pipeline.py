"""The shared mechanism behind DietChat, WirelessChat and CustomNerd-style engines.

question -> (1) resolve follow-up into a standalone question using memory
         -> (2) retrieve evidence from every selected source (cached per question)
         -> (3) rank, dedupe, number the evidence
         -> (4) generate an answer constrained to the numbered evidence
         -> (5) check citations, build a claim-to-evidence ledger
         -> (6) store the turn under a conversation and refresh its summary
"""
import re, time
from . import providers
from .connectors import make_connector

FOLLOW_UP = re.compile(r"\b(it|its|this|that|they|them|those|these|he|she|there|the same|above|previous|earlier)\b", re.I)


class Engine:
    def __init__(self, cfg, store, provider=None, connectors=None):
        self.cfg, self.store = cfg, store
        self.provider = provider or providers.make(cfg)
        base = cfg.get("_dir", ".")
        self.connectors = connectors if connectors is not None else {s["id"]: make_connector(s, base) for s in cfg["sources"]}
        self._cache = {}

    # (1) memory
    def standalone(self, question, history, summary=""):
        if not history or not FOLLOW_UP.search(question) or len(question.split()) > 14:
            return question
        recent = "\n".join("Q: %s\nA: %s" % (h["question"], h["answer"][:300]) for h in history[-2:])
        prompt = [{"role": "system", "content": "Rewrite the last question so it can be understood alone. "
                   "Return only the rewritten question."},
                  {"role": "user", "content": "%s\nConversation so far: %s\nLast question: %s" % (recent, summary, question)}]
        try:
            out = self.provider.complete(prompt).strip().splitlines()[0]
            return out if 3 < len(out) < 400 and self.cfg["provider"]["type"] != "mock" else question
        except providers.ProviderError:
            return question

    # (2)+(3) retrieval
    def retrieve(self, question, source_ids=None):
        ids = [s for s in (source_ids or list(self.connectors)) if s in self.connectors]
        key = (question.lower().strip(), tuple(sorted(ids)))
        if key in self._cache:
            return self._cache[key]
        k = self.cfg["retrieval"]["top_k"]
        found, errors, seen = [], {}, set()
        for sid in ids:
            try:
                for e in self.connectors[sid].search(question, k):
                    sig = re.sub(r"\W+", "", e["title"].lower())[:80] or e["id"]
                    if sig not in seen and e["score"] >= self.cfg["retrieval"]["min_score"]:
                        seen.add(sig); found.append(e)
            except Exception as ex:  # one failing source must not sink the answer
                errors[sid] = type(ex).__name__
        found.sort(key=lambda e: -e["score"])
        found = found[:k]
        for n, e in enumerate(found, 1):
            e["n"] = n
        self._cache[key] = (found, errors)
        return found, errors

    # (4) generation
    def prompt(self, question, evidence, style, history, summary):
        p = self.cfg["prompt"]
        ev = "\n".join("[%d] %s (%s). %s" % (e["n"], e["title"], e["year"] or "n.d.", e["text"][:1200]) for e in evidence)
        mem = ("Conversation summary: %s\n" % summary if summary else "") + "".join(
            "Earlier Q: %s\nEarlier A: %s\n" % (h["question"], h["answer"][:240]) for h in history[-self.cfg["memory"]["recent_turns"]:])
        return [{"role": "system", "content": p["system"] + " " + p["style"].get(style, p["style"]["standard"])},
                {"role": "user", "content": "%sQuestion: %s\n\nEvidence:\n%s" % (mem, question, ev)}]

    # (5) citations
    @staticmethod
    def ledger(answer, evidence):
        valid = {e["n"] for e in evidence}
        out = []
        for sent in re.split(r"(?<=[.!?])\s+(?!\[\d+\])", answer):
            cites = [int(n) for n in re.findall(r"\[(\d+)\]", sent)]
            if sent.strip():
                out.append({"claim": re.sub(r"\s*\[\d+\]", "", sent).strip(), "cites": [c for c in cites if c in valid],
                            "invalid": [c for c in cites if c not in valid], "supported": bool(cites) and all(c in valid for c in cites)})
        return out

    def ask_stream(self, owner, chat, question, sources=None, style="standard", topic=None, new_topic=False, use_cache=True):
        """Yield ('meta', {...}), ('token', str)..., ('done', result). Same behaviour as ask()."""
        q = (question or "").strip()
        if not q or len(q) > 2000:
            raise ValueError("Question must be 1-2000 characters")
        self.store.chat(owner, chat)
        if topic:
            self.store.topic(owner, topic)
        elif not new_topic:
            topic = self.store.last_topic(chat)
        if not topic:
            topic = self.store.new_topic(owner, q[:80])
        mem_on = self.cfg["memory"]["enabled"]
        history = self.store.topic_turns(owner, topic, 12) if mem_on else []
        summary = self.store.topic(owner, topic)["summary"] if mem_on else ""
        standalone = self.standalone(q, history, summary)
        evidence, errors = self.retrieve(standalone, sources) if use_cache else self._fresh(standalone, sources)
        yield "meta", {"standalone": standalone, "evidence": evidence, "source_errors": errors}
        if not evidence:
            answer = self.cfg["prompt"]["no_evidence"]
            yield "token", answer
        else:
            parts = []
            for piece in self.provider.stream(self.prompt(standalone, evidence, style, history, summary)):
                parts.append(piece)
                yield "token", piece
            answer = "".join(parts).strip()
        ledger = self.ledger(answer, evidence) if evidence else []
        tid = self.store.add_turn(chat, topic, q, standalone, answer, evidence, ledger, style)
        if mem_on:
            self._summarize(owner, topic)
        if self.store.chat(owner, chat)["title"] == "New chat":
            self.store.rename_chat(owner, chat, q[:60])
        yield "done", {"id": tid, "chat": chat, "topic": topic, "question": q, "standalone": standalone, "answer": answer,
                       "evidence": evidence, "ledger": ledger, "style": style, "source_errors": errors}

    def ask(self, owner, chat, question, sources=None, style="standard", topic=None, new_topic=False, use_cache=True):
        q = (question or "").strip()
        if not q or len(q) > 2000:
            raise ValueError("Question must be 1-2000 characters")
        self.store.chat(owner, chat)
        if topic:
            self.store.topic(owner, topic)
        elif not new_topic:
            topic = self.store.last_topic(chat)
        if not topic:
            topic = self.store.new_topic(owner, q[:80])
        mem_on = self.cfg["memory"]["enabled"]
        history = self.store.topic_turns(owner, topic, 12) if mem_on else []
        summary = self.store.topic(owner, topic)["summary"] if mem_on else ""
        standalone = self.standalone(q, history, summary)
        evidence, errors = self.retrieve(standalone, sources) if use_cache else self._fresh(standalone, sources)
        if not evidence:
            answer, ledger = self.cfg["prompt"]["no_evidence"], []
        else:
            answer = self.provider.complete(self.prompt(standalone, evidence, style, history, summary))
            ledger = self.ledger(answer, evidence)
        tid = self.store.add_turn(chat, topic, q, standalone, answer, evidence, ledger, style)
        if mem_on:
            self._summarize(owner, topic)
        if self.store.chat(owner, chat)["title"] == "New chat":
            self.store.rename_chat(owner, chat, q[:60])
        return {"id": tid, "chat": chat, "topic": topic, "question": q, "standalone": standalone, "answer": answer,
                "evidence": evidence, "ledger": ledger, "style": style, "source_errors": errors}

    def _fresh(self, q, sources):
        self._cache.clear()
        return self.retrieve(q, sources)

    # (6) rolling summary
    def _summarize(self, owner, topic):
        every = self.cfg["memory"]["summary_every"]
        turns = self.store.topic_turns(owner, topic, 50)
        if len(turns) % every:
            return
        text = " | ".join(t["standalone"] for t in turns[-every:])
        if self.cfg["provider"]["type"] == "mock":
            self.store.set_summary(topic, "Topics so far: " + text[:500])
            return
        try:
            s = self.provider.complete([{"role": "system", "content": "Summarise the conversation topics in 2 sentences."},
                                        {"role": "user", "content": text}])
            self.store.set_summary(topic, s[:600])
        except providers.ProviderError:
            pass
