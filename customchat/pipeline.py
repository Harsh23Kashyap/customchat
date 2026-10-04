"""The shared mechanism behind DietChat, WirelessChat and CustomNerd-style engines.

question -> (1) resolve follow-up into a standalone question using memory
         -> (2) retrieve evidence from every selected source (cached per question)
         -> (3) rank, dedupe, number the evidence
         -> (4) generate an answer constrained to the numbered evidence
         -> (5) check citations, build a claim-to-evidence ledger
         -> (6) store the turn under a conversation and refresh its summary
"""
import re, time, json, hashlib
from concurrent.futures import ThreadPoolExecutor
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

    def queries(self, question):
        """Search queries for the question. With a real model and retrieval.query_rewrite, the model writes up to 3
        keyword queries (the CustomNerd idea). Otherwise the question itself is used."""
        if self.cfg["retrieval"].get("query_rewrite") and self.cfg["provider"]["type"] != "mock":
            try:
                out = self.provider.complete([{"role": "system", "content": "Write up to 3 short keyword search queries for the question. One per line, no numbering."},
                                              {"role": "user", "content": question}])
                qs = [re.sub(r"^[-*\d.)\s]+", "", l).strip() for l in out.splitlines() if l.strip()][:3]
                if qs:
                    return [question] + [x for x in qs if x.lower() != question.lower()]
            except providers.ProviderError:
                pass
        return [question]

    # (2)+(3) retrieval
    def _uploads_evidence(self, owner, question):
        """Search the owner's uploaded text with the same BM25 used for local files."""
        rows = self.store.uploads(owner) if owner else []
        if not rows:
            return []
        from .connectors.local_files import LocalFiles, tokens, chunks
        lf = LocalFiles.__new__(LocalFiles)
        lf.id, lf.label, lf.docs = "uploads", "My uploads", []
        for r in rows:
            for i, c in enumerate(chunks(r["text"])):
                lf.docs.append({"title": r["name"], "text": c, "tok": tokens(r["name"] + " " + c), "id": "%s#%d" % (r["id"], i)})
        import math
        n = len(lf.docs) or 1; df = {}
        for d in lf.docs:
            for t in set(d["tok"]): df[t] = df.get(t, 0) + 1
        lf.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        lf.avg = sum(len(d["tok"]) for d in lf.docs) / n
        return lf.search(question, self.cfg["retrieval"]["top_k"])

    def retrieve(self, question, source_ids=None, owner=None):
        ids = [s for s in (source_ids or list(self.connectors)) if s in self.connectors]
        extra = self._uploads_evidence(owner, question)
        key = (question.lower().strip(), tuple(sorted(ids)), owner if extra else None, len(extra))
        if key in self._cache:
            return self._cache[key]
        k = self.cfg["retrieval"]["top_k"]
        found, errors, seen = list(extra), {}, set()
        weights = {s["id"]: float(s.get("weight", 1.0)) for s in self.cfg["sources"]}
        qs = self.queries(question)

        def run(sid):
            out = []
            for qq in qs:
                ck = hashlib.sha1(("%s|%s|%d" % (sid, qq.lower(), k)).encode()).hexdigest()
                hit = self._disk_get(ck, sid)
                if hit is None:
                    hit = self.connectors[sid].search(qq, k)
                    self._disk_put(ck, hit, sid)
                out += hit
            return sid, out

        with ThreadPoolExecutor(max_workers=max(1, min(8, len(ids)))) as ex:
            futures = [(sid, ex.submit(run, sid)) for sid in ids]
        for sid, f in futures:
            try:
                for e in f.result(timeout=60)[1]:
                    e["score"] *= weights.get(sid, 1.0)
                    sig = e["url"] or re.sub(r"\W+", "", e["title"].lower())[:80] or e["id"]
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

    # persistent evidence cache (remote sources only; local files are already fast)
    def _disk_get(self, key, sid):
        ttl = self.cfg["retrieval"].get("cache_ttl", 0)
        if not ttl or self.cfg["sources"] and next((x["type"] for x in self.cfg["sources"] if x["id"] == sid), "") == "local_files":
            return None
        r = self.store.q("SELECT payload,created FROM evidence_cache WHERE key=?", (key,), one=True)
        return json.loads(r["payload"]) if r and time.time() - r["created"] < ttl else None

    def _disk_put(self, key, hit, sid):
        ttl = self.cfg["retrieval"].get("cache_ttl", 0)
        if ttl and next((x["type"] for x in self.cfg["sources"] if x["id"] == sid), "") != "local_files":
            self.store.q("INSERT OR REPLACE INTO evidence_cache VALUES(?,?,?)", (key, json.dumps(hit), time.time()), write=True)

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
    def support(claim, cites, evidence):
        """Share of the claim's content words found in the cited evidence (0 to 1). A lexical check, not a proof."""
        words = {w for w in re.findall(r"[a-z0-9]{4,}", claim.lower())}
        if not words or not cites:
            return 0.0
        text = " ".join((e.get("title", "") + " " + e.get("text", "")).lower() for e in evidence if e.get("n") in cites)
        return round(sum(1 for w in words if w in text) / len(words), 2)

    @staticmethod
    def ledger(answer, evidence):
        valid = {e["n"] for e in evidence}
        out = []
        for sent in re.split(r"(?<=[.!?])\s+(?!\[\d+\])", answer):
            cites = [int(n) for n in re.findall(r"\[(\d+)\]", sent)]
            if sent.strip():
                claim = re.sub(r"\s*\[\d+\]", "", sent).strip()
                out.append({"claim": claim, "overlap": Engine.support(claim, [c for c in cites if c in valid], evidence), "cites": [c for c in cites if c in valid],
                            "invalid": [c for c in cites if c not in valid], "supported": bool(cites) and all(c in valid for c in cites)})
        return out

    def ask_stream(self, owner, chat, question, sources=None, style="standard", topic=None, new_topic=False, use_cache=True):
        """Yield ('meta', {...}), ('token', str)..., ('done', result). Same behaviour as ask()."""
        t0 = time.time()
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
        evidence, errors = self.retrieve(standalone, sources, owner) if use_cache else self._fresh(standalone, sources, owner)
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
        fu = self.followups(q, answer, evidence)
        yield "done", {"seconds": round(time.time() - t0, 1), "followups": fu, "id": tid, "chat": chat, "topic": topic, "question": q, "standalone": standalone, "answer": answer,
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
        evidence, errors = self.retrieve(standalone, sources, owner) if use_cache else self._fresh(standalone, sources, owner)
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

    def _fresh(self, q, sources, owner=None):
        self._cache.clear()
        return self.retrieve(q, sources, owner)

    def followups(self, question, answer, evidence):
        """Up to three short follow-up questions. Model-written when a model is configured, else from evidence titles."""
        if self.cfg["provider"]["type"] != "mock" and evidence:
            try:
                out = self.provider.complete([{"role": "system", "content": "Suggest 3 short follow-up questions a curious reader might ask next. One per line, no numbering."},
                                              {"role": "user", "content": "Question: %s\nAnswer: %s" % (question, answer[:800])}])
                qs = [re.sub(r"^[-*\d.)\s]+", "", l).strip() for l in out.splitlines() if "?" in l]
                if qs:
                    return qs[:3]
            except providers.ProviderError:
                pass
        return ["Tell me more about %s" % e["title"].rstrip(".")[:70] for e in evidence[1:4]]

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
