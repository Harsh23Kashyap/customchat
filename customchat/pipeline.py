"""The shared mechanism behind DietChat, WirelessChat and CustomNerd-style engines.

question -> (1) resolve follow-up into a standalone question using memory
         -> (2) retrieve evidence from every selected source (cached per question)
         -> (3) rank, dedupe, number the evidence
         -> (4) generate an answer constrained to the numbered evidence
         -> (5) check citations, build a claim-to-evidence ledger
         -> (6) store the turn under a conversation and refresh its summary
"""
import collections, math, re, time, json, hashlib
from concurrent.futures import ThreadPoolExecutor
from . import providers, prompts as promptmod
from .connectors import make_connector

FOLLOW_UP = re.compile(r"\b(it|its|this|that|they|them|those|these|he|she|there|the same|above|previous|earlier)\b", re.I)


class Engine:
    def __init__(self, cfg, store, provider=None, connectors=None):
        self.cfg, self.store = cfg, store
        self.provider = provider or providers.make(cfg)
        base = cfg.get("_dir", ".")
        self.connectors = connectors if connectors is not None else {s["id"]: make_connector(s, base) for s in cfg["sources"]}
        self._cache = {}
        self.prompts = promptmod.PromptStore("")

    # optional live web source, switched on from the Configuration page
    WEB_ID = "web"

    def web_state(self):
        b = next((x for x in self.cfg["sources"] if x["id"] == self.WEB_ID), None)
        return {"on": bool(b), "providers": list((b or {}).get("providers", []))}

    def set_web(self, on, providers=()):
        providers = [providers] if isinstance(providers, str) else list(providers or [])
        self.cfg["sources"] = [x for x in self.cfg["sources"] if x["id"] != self.WEB_ID]
        self.connectors.pop(self.WEB_ID, None)
        if on and providers:
            blk = {"id": self.WEB_ID, "type": "web_search", "label": "Live web", "providers": providers, "weight": 0.8}
            self.cfg["sources"].append(blk)
            self.connectors[self.WEB_ID] = make_connector(blk, self.cfg.get("_dir", "."))
        self._cache.clear()

    CATALOG = {"pubmed": "PubMed", "arxiv": "arXiv", "wikipedia": "Wikipedia", "crossref": "Crossref", "openalex": "OpenAlex"}

    def catalog_state(self):
        return [x["type"] for x in self.cfg["sources"] if x["id"].startswith("cat-")]

    def set_catalog(self, types):
        types = [t for t in dict.fromkeys(types or []) if t in self.CATALOG]
        for x in [x for x in self.cfg["sources"] if x["id"].startswith("cat-")]:
            self.connectors.pop(x["id"], None)
        self.cfg["sources"] = [x for x in self.cfg["sources"] if not x["id"].startswith("cat-")]
        for t in types:
            blk = {"id": "cat-" + t, "type": t, "label": self.CATALOG[t], "weight": 0.9}
            self.cfg["sources"].append(blk)
            self.connectors[blk["id"]] = make_connector(blk, self.cfg.get("_dir", "."))
        self._cache.clear()
        return types

    # (1) memory
    def standalone(self, question, history, summary=""):
        if not history or not FOLLOW_UP.search(question) or len(question.split()) > 14:
            return question
        recent = "\n".join("Q: %s\nA: %s" % (h["question"], h["answer"][:300]) for h in history[-2:])
        prompt = [{"role": "system", "content": self.prompts.text("standalone")},
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
                out = self.provider.complete([{"role": "system", "content": self.prompts.text("queries")},
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
                    if not Engine.usable(e):
                        continue  # a record with no text or no title cannot be cited
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
    def prompt(self, question, evidence, style, history, summary, profile=""):
        p = self.cfg["prompt"]
        ev = "\n".join("[%d] %s (%s). %s" % (e["n"], e["title"], e["year"] or "n.d.", e["text"][:3000]) for e in evidence)
        mem = ("About the reader (self-reported background, not evidence): %s\n" % profile[:1500] if profile else "") + ("Conversation summary: %s\n" % summary if summary else "") + "".join(
            "Earlier Q: %s\nEarlier A: %s\n" % (h["question"], h["answer"][:240]) for h in history[-self.cfg["memory"]["recent_turns"]:])
        return [{"role": "system", "content": self.prompts.text("answer", p["system"]) + " " + p["style"].get(style, p["style"]["standard"])},
                {"role": "user", "content": "%sQuestion: %s\n\nEvidence:\n%s" % (mem, question, ev)}]

    @staticmethod
    def usable(e):
        return bool((e.get("text") or "").strip() and (e.get("title") or "").strip())

    def correct(self, answer, evidence, ledger, asked=""):
        """When a sentence is flagged as vague about regain, rewrite once with the passages and the flagged sentences, then keep the rewrite only if the flag is gone."""
        flagged = [l["claim"] for l in ledger if l.get("vague_regain") or l.get("animal_unmarked") or l.get("unhedged_lead") or l.get("uncited")]
        if not flagged or self.cfg["provider"]["type"] == "mock":
            return answer
        ev = "\n".join("[%d] %s. %s" % (e["n"], e["title"], e["text"][:3000]) for e in evidence)
        try:
            out = self.provider.complete([{"role": "system", "content": self.prompts.text("revise")},
                                          {"role": "user", "content": "These sentences are too vague: %s\nSay exactly what the passage measured (for example fat mass regain, and which group had more). If a sentence rests on an animal study, say plainly that it was in rats or mice. Every sentence that states a finding needs its own [n] after it. If the opening says Yes or Probably and the effect came with weight loss, open with Possibly or say the effect may partly come from the weight loss.\n\nAnswer:\n%s\n\nEvidence:\n%s" % (" | ".join(flagged)[:800], answer, ev)}]).strip()
        except providers.ProviderError:
            return answer
        if len(out) < 0.4 * len(answer) or not re.search(r"\[\d+\]", out):
            return answer
        new, ev2 = self.tidy(out, evidence)
        led2 = self.ledger(new, ev2, asked)
        n_flags = lambda led: sum(1 for l in led if l.get("vague_regain") or l.get("animal_unmarked") or l.get("unhedged_lead") or l.get("uncited"))
        if n_flags(led2) >= n_flags(ledger) or any(l.get("bad_numbers") for l in led2):
            return answer  # the rewrite must have fewer flags than the original and add no number the cited passages lack
        return out

    def _fix(self, answer, evidence, ledger, asked):
        fixed = self.correct(answer, evidence, ledger, asked)
        if fixed == answer:
            return self._drop_uncited_numbers(answer, evidence, ledger, asked)
        self.corrections = (getattr(self, "corrections", []) + [{"before": answer, "after": fixed}])[-20:]
        new, ev2 = self.tidy(fixed, evidence)
        return self._drop_uncited_numbers(new, ev2, self.ledger(new, ev2, asked), asked)

    def _drop_uncited_numbers(self, answer, evidence, ledger, asked):
        """A sentence that carries a number but no [n] cannot be checked, so it is removed from the answer (kept in self.dropped)."""
        bad = [l["claim"] for l in ledger if re.search(r"\d", l["claim"]) and not l.get("cites") and len(l["claim"].split()) >= 4 and not l["claim"].lower().startswith(("i could not", "i couldn"))]
        out = answer
        for c in bad:
            if c in out:
                out = out.replace(c, "", 1)
        if out == answer:
            return answer, evidence, ledger
        self.dropped = (getattr(self, "dropped", []) + bad)[-50:]
        out = re.sub(r"[ \t]{2,}", " ", out)
        out = re.sub(r"\n{3,}", "\n\n", out).strip()
        new, ev2 = self.tidy(out, evidence)
        return new, ev2, self.ledger(new, ev2, asked)

    @staticmethod
    def tidy(answer, evidence):
        """Space before a citation that follows punctuation, keep only cited sources and number them 1, 2, 3 in order of use."""
        def expand(m):
            nums = []
            for part in re.split(r"\s*,\s*", m.group(1)):
                r = re.match(r"^(\d+)\s*[-\u2013]\s*(\d+)$", part)
                nums += list(range(int(r.group(1)), int(r.group(2)) + 1)) if r and int(r.group(2)) - int(r.group(1)) < 10 else ([int(part)] if part.isdigit() else [])
            return "".join("[%d]" % n for n in nums) if nums else m.group(0)
        answer = re.sub(r"\[(\d+(?:\s*[,\-\u2013]\s*\d+)+)\]", expand, answer)
        answer = re.sub(r"(?<=[.!?:;,])(?=\[\d+\])", " ", answer)
        answer = re.sub(r"\s*((?:\[\d+\]\s*)+)\*\*", lambda m: "** " + m.group(1).strip(), answer)  # citations go outside bold
        order = []
        for m in re.findall(r"\[(\d+)\]", answer):
            m = int(m)
            if m not in order and any(e["n"] == m for e in evidence):
                order.append(m)
        mp = {o: i + 1 for i, o in enumerate(order)}
        answer = re.sub(r"\[(\d+)\]", lambda m: "[%d]" % mp[int(m.group(1))] if int(m.group(1)) in mp else m.group(0), answer)
        answer = re.sub(r"(\[\d+\])(?=\[\d+\])", r"\1 ", answer)
        def group(m):
            ns = sorted({int(x) for x in re.findall(r"\d+", m.group(0))})
            return " ".join("[%d]" % n for n in ns)
        answer = re.sub(r"\[\d+\](?:\s*\[\d+\])+", group, answer)
        # years that no passage mentions are the model's memory, not the evidence: drop "a 2022 review" down to "a review"
        known = " ".join(e.get("title", "") + " " + e.get("text", "") + " " + str(e.get("year") or "") for e in evidence)
        answer = re.sub(r"\b((?:a|an|the|this|that)\s+)((?:19|20)\d\d)\s+(?=[A-Za-z])", lambda m: m.group(0) if m.group(2) in known else m.group(1), answer, flags=re.I)
        answer = re.sub(r"[ \t]+(?=\[\d+\])", " ", answer)
        answer = re.sub(r"(\[\d+\])[ \t]+(?=[.,;:!?)])", r"\1", answer)
        answer = re.sub(r"\b(the|these|this)\s+(?:provided\s+|available\s+)?(?:evidence|passages)(?:\s+(?:provided|here|supplied))?\b", lambda m: "the cited sources" if m.group(1).lower() == "the" else "these sources", answer, flags=re.I)
        verbs = {"does": "do", "is": "are", "was": "were", "has": "have", "shows": "show", "suggests": "suggest", "supports": "support", "indicates": "indicate", "doesn't": "don't", "isn't": "aren't", "provides": "provide"}
        answer = re.sub(r"\b(the cited sources|these sources) (%s)\b" % "|".join(verbs), lambda m: m.group(1) + " " + verbs[m.group(2).lower()], answer, flags=re.I)
        out = []
        for o in order:
            e = dict(next(x for x in evidence if x["n"] == o)); e["n"] = mp[o]; out.append(e)
        return answer, out

    # (5) citations
    @staticmethod
    def support(claim, cites, evidence):
        """Share of the claim's content words found in the cited evidence (0 to 1). A lexical check, not a proof."""
        words = {w for w in re.findall(r"[a-z0-9]{4,}", claim.lower())}
        if not words or not cites:
            return 0.0
        text = " ".join((e.get("title", "") + " " + e.get("text", "")).lower() for e in evidence if e.get("n") in cites)
        return round(sum(1 for w in words if w in text) / len(words), 2)

    _WORDS = {w: str(i) for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
    _WORDS.update({"thirty": "30", "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70", "eighty": "80", "ninety": "90", "hundred": "100"})

    @staticmethod
    def numbers(text):
        t = text.lower()
        found = set(re.findall(r"\d+(?:\.\d+)?", t.replace(",", "")))
        found |= {Engine._WORDS[w] for w in re.findall(r"[a-z]+", t) if w in Engine._WORDS}
        return found

    @staticmethod
    def bad_numbers(claim, cites, evidence, asked=""):
        """Numbers written in the claim that none of the cited passages contain (digits or number words). A deterministic check."""
        text = " ".join((e.get("title", "") + " " + e.get("text", "") + " " + str(e.get("year") or "")) for e in evidence if e.get("n") in cites)
        have = Engine.numbers(text) | Engine.numbers(asked)
        return sorted(n for n in Engine.numbers(claim) if n not in have)

    @staticmethod
    def ledger(answer, evidence, asked=""):
        valid = {e["n"] for e in evidence}
        out = []
        for sent in re.split(r"(?<=[.!?])\s+(?!\[\d+\])|(?<=[.!?]\*\*)\s+(?!\[\d+\])|(?<=\])\s+(?=[A-Z0-9*])", answer):
            cites = [int(n) for n in re.findall(r"\[(\d+)\]", sent)]
            if sent.strip():
                claim = re.sub(r"\s*\[\d+\]", "", sent).strip()
                good = [c for c in cites if c in valid]
                bad = Engine.bad_numbers(claim, good, evidence, asked) if good else []
                blob = " ".join(e.get("text", "").lower() for e in evidence if e.get("n") in good)
                vague = "regain" in claim.lower() and "fat" not in claim.lower() and "fat mass regain" in blob
                animal = bool(good) and re.search(r"\b(rats?|mice|mouse|murine|rodents?|mouse|monkeys?|zebrafish)\b", blob) is not None and re.search(r"\b(rats?|mice|mouse|murine|rodents?|animals?|preclinical|monkeys?|zebrafish)\b", claim.lower()) is None
                weak = [c for c in good if len(good) > 1 and Engine.support(claim, [c], evidence) < 0.34]
                uncited = not cites and len(re.findall(r"[A-Za-z]{3,}", claim)) >= 6 and not claim.lower().startswith(("i could not", "i couldn", "the source does not", "the sources do not", "the source doesn", "the sources don", "the documents do not", "the passages do not"))
                out.append({"uncited": uncited, "weak_cites": weak, "claim": claim, "overlap": Engine.support(claim, good, evidence), "cites": good, "bad_numbers": bad,
                            "invalid": [c for c in cites if c not in valid], "supported": bool(cites) and all(c in valid for c in cites) and not bad and not vague and not animal, "vague_regain": vague, "animal_unmarked": animal})
        if out:
            lead = re.sub(r"[*_\s]", "", out[0]["claim"].lower())
            allev = " ".join((e.get("title", "") + " " + e.get("text", "")).lower() for e in evidence)
            # a confident lead ("Yes", "Probably") on an effect reported with weight loss needs the weight caveat somewhere
            out[0]["unhedged_lead"] = bool(re.match(r"(yes|probably)\b", lead)) and "weight" in allev and not any("weight" in l["claim"].lower() for l in out[1:])
            if out[0]["unhedged_lead"]:
                out[0]["supported"] = False
        return out

    # optional steps, each off by default and only used with a real model
    def _llm_on(self, key):
        return self.prompts.enabled(key) and self.cfg["provider"]["type"] != "mock"

    def check_question(self, question):
        """Empty string when the question is fine; otherwise a short reason to show instead of an answer."""
        if not self._llm_on("question_check"):
            return ""
        try:
            out = self.provider.complete([{"role": "system", "content": self.prompts.text("question_check")}, {"role": "user", "content": question}]).strip()
        except providers.ProviderError:
            return ""
        if out.upper().startswith("INVALID"):
            why = out.split(":", 1)[1].strip() if ":" in out else ""
            return why[:300] or "That question is outside what this assistant can answer."
        return ""

    def filter_relevant(self, question, evidence):
        if not evidence or not self._llm_on("relevance"):
            return evidence
        listing = "\n".join("[%d] %s. %s" % (e["n"], e["title"], e["text"][:400]) for e in evidence)
        try:
            out = self.provider.complete([{"role": "system", "content": self.prompts.text("relevance")}, {"role": "user", "content": "Question: %s\n\nPassages:\n%s" % (question, listing)}]).strip()
        except providers.ProviderError:
            return evidence
        if out.upper().startswith("NONE"):
            return []
        keep = {int(x) for x in re.findall(r"\d+", out)}
        kept = [e for e in evidence if e["n"] in keep]
        return kept or evidence

    def revise(self, answer, evidence):
        if not evidence or not answer or not (self._llm_on("revise") or (self.cfg["prompt"].get("revise") and self.cfg["provider"]["type"] != "mock")):
            return answer
        ev = "\n".join("[%d] %s. %s" % (e["n"], e["title"], e["text"][:3000]) for e in evidence)
        try:
            out = self.provider.complete([{"role": "system", "content": self.prompts.text("revise")}, {"role": "user", "content": "Answer:\n%s\n\nEvidence:\n%s" % (answer, ev)}]).strip()
        except providers.ProviderError:
            return answer
        if len(out) < 0.4 * len(answer) or (re.search(r"\[\d+\]", answer) and not re.search(r"\[\d+\]", out)):
            return answer
        return out

    def check_support(self, answer, evidence):
        if not evidence or not answer or not self._llm_on("faithfulness"):
            return ""
        ev = "\n".join("[%d] %s" % (e["n"], e["text"][:600]) for e in evidence)
        try:
            out = self.provider.complete([{"role": "system", "content": self.prompts.text("faithfulness")}, {"role": "user", "content": "Answer:\n%s\n\nEvidence:\n%s" % (answer, ev)}]).strip()
        except providers.ProviderError:
            return ""
        if out.upper().startswith("UNSUPPORTED"):
            what = out.split(":", 1)[1].strip() if ":" in out else ""
            return "Note: the sources may not fully support this: %s" % what[:300] if what else "Note: some statements here may not be fully supported by the sources."
        return ""

    @staticmethod
    def fallback_answer(evidence, why=""):
        """No model reachable: answer with the best passages from the sources instead of an error."""
        lines = ["The AI model could not be reached, so here are the most relevant passages from your sources."]
        for e in (evidence or [])[:3]:
            t = " ".join(str(e.get("text") or "").split())
            if len(t) > 320:
                t = t[:320].rsplit(" ", 1)[0] + "..."
            lines.append("- " + t + " [" + str(e.get("n")) + "]")
        return "\n\n".join([lines[0], "\n".join(lines[1:])]) if len(lines) > 1 else lines[0]

    def ask_stream(self, owner, chat, question, sources=None, style="standard", topic=None, new_topic=False, use_cache=True, temporary=False, temp_history=None, use_profile=False):
        """Yield ('meta', {...}), ('token', str)..., ('done', result). Same behaviour as ask()."""
        t0 = time.time()
        q = str(question or "").strip()
        if not q or len(q) > 2000:
            raise ValueError("Question must be 1-2000 characters")
        mem_on = self.cfg["memory"]["enabled"]
        profile = ""
        if temporary:
            # nothing is read from or written to the saved history, uploads or profile
            chat = topic = None
            history = [{"question": str(h.get("question", ""))[:500], "answer": str(h.get("answer", ""))[:600]}
                       for h in (temp_history or [])[-6:] if isinstance(h, dict)] if mem_on else []
            summary = ""
            standalone = self.standalone(q, history, summary)
            blocked = self.check_question(standalone)
            evidence, errors = ([], []) if blocked else self.retrieve(standalone, sources, None)
        else:
            self.store.chat(owner, chat)
            if topic:
                self.store.topic(owner, topic)
            elif not new_topic:
                topic = self.store.last_topic(chat)
            if not topic:
                topic = self.store.new_topic(owner, q[:80])
            history = self.store.topic_turns(owner, topic, 12) if mem_on else []
            summary = self.store.topic(owner, topic)["summary"] if mem_on else ""
            profile = self.store.get_profile(owner) if use_profile else ""
            standalone = self.standalone(q, history, summary)
            blocked = self.check_question(standalone)
            evidence, errors = ([], []) if blocked else (self.retrieve(standalone, sources, owner) if use_cache else self._fresh(standalone, sources, owner))
        evidence = self.filter_relevant(standalone, evidence)
        yield "meta", {"standalone": standalone, "evidence": evidence, "source_errors": errors}
        if not evidence:
            answer = blocked or self.cfg["prompt"]["no_evidence"]
            yield "token", answer
        else:
            parts = []
            degraded = False
            try:
                for piece in self.provider.stream(self.prompt(standalone, evidence, style, history, summary, profile)):
                    parts.append(piece)
                    yield "token", piece
            except providers.ProviderError:
                degraded = True
                if parts:
                    tail = "\n\n(The answer was cut short because the model stopped responding.)"
                    parts.append(tail); yield "token", tail
                else:
                    fb = self.fallback_answer(evidence); parts.append(fb); yield "token", fb
            answer = "".join(parts).strip()
            if not degraded:
                answer = self.revise(answer, evidence)
                note = self.check_support(answer, evidence)
                if note:
                    answer += "\n\n" + note
                    yield "token", "\n\n" + note
        ledger = self.ledger(answer, evidence, standalone) if evidence else []
        if evidence and self.cfg["provider"]["type"] != "mock" and not locals().get("degraded"):
            # show only the sources the answer cites; a refusal cites nothing, so it shows none
            answer, evidence = self.tidy(answer, evidence)
            ledger = self.ledger(answer, evidence, standalone)
            answer, evidence, ledger = self._fix(answer, evidence, ledger, standalone)
            note = (self.cfg["prompt"].get("answer_note") or "").strip()
            if evidence and note and note not in answer:
                answer += "\n\n" + note
        if temporary:
            tid = None
        else:
            tid = self.store.add_turn(chat, topic, q, standalone, answer, evidence, ledger, style)
            if mem_on:
                self._summarize(owner, topic)
            if self.store.chat(owner, chat)["title"] == "New chat":
                self.store.rename_chat(owner, chat, q[:60])
        fu = self.followups(q, answer, evidence)
        yield "done", {"seconds": round(time.time() - t0, 1), "followups": fu, "id": tid, "chat": chat, "topic": topic, "question": q, "standalone": standalone, "answer": answer,
                       "evidence": evidence, "ledger": ledger, "style": style, "source_errors": errors, "temporary": temporary}

    def ask(self, owner, chat, question, sources=None, style="standard", topic=None, new_topic=False, use_cache=True):
        q = str(question or "").strip()
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
            degraded = False
            try:
                answer = self.provider.complete(self.prompt(standalone, evidence, style, history, summary))
            except providers.ProviderError:
                degraded = True
                answer = self.fallback_answer(evidence)
            if not degraded:
                answer = self.revise(answer, evidence)
            ledger = self.ledger(answer, evidence, standalone)
            if self.cfg["provider"]["type"] != "mock" and not degraded:
                answer, evidence = self.tidy(answer, evidence)
                ledger = self.ledger(answer, evidence, standalone)
                answer, evidence, ledger = self._fix(answer, evidence, ledger, standalone)
                note = (self.cfg["prompt"].get("answer_note") or "").strip()
                if evidence and note and note not in answer:
                    answer += "\n\n" + note
        tid = self.store.add_turn(chat, topic, q, standalone, answer, evidence, ledger, style)
        if mem_on:
            self._summarize(owner, topic)
        if self.store.chat(owner, chat)["title"] == "New chat":
            self.store.rename_chat(owner, chat, q[:60])
        return {"id": tid, "chat": chat, "topic": topic, "question": q, "standalone": standalone, "answer": answer,
                "evidence": evidence, "ledger": ledger, "style": style, "source_errors": errors}

    def similar(self, owner, question, limit=3, threshold=0.3):
        """Earlier questions of this reader that look like `question` (idf-weighted token overlap)."""
        rows = self.store.recent_questions(owner, 400)
        stop = {"how", "does", "what", "the", "and", "for", "are", "can", "you", "please", "tell", "about", "explain", "with", "this", "that", "why", "who", "when", "where", "which", "work", "works"}
        tok = lambda s: {t for t in re.findall(r"[a-z0-9]{3,}", s.lower()) if t not in stop}
        qt = tok(question)
        if not qt or not rows:
            return []
        df = collections.Counter(t for r in rows for t in tok(r["question"]))
        n = len(rows)
        w = lambda t: math.log(1 + n / (1 + df.get(t, 0)))
        out, seen = [], set()
        for r in rows:
            rt = tok(r["question"])
            if not rt or r["question"].strip().lower() == question.strip().lower() or r["question"] in seen:
                continue
            inter = sum(w(t) for t in qt & rt); union = sum(w(t) for t in qt | rt)
            score = inter / union if union else 0
            if score >= threshold:
                seen.add(r["question"]); out.append({"turn": r["id"], "chat": r["chat"], "question": r["question"], "score": round(score, 2)})
        return sorted(out, key=lambda x: -x["score"])[:limit]

    def _fresh(self, q, sources, owner=None):
        self._cache.clear()
        return self.retrieve(q, sources, owner)

    def followups(self, question, answer, evidence):
        """Up to three short follow-up questions. Model-written when a model is configured, else from evidence titles."""
        if self.cfg["provider"]["type"] != "mock" and evidence:
            try:
                out = self.provider.complete([{"role": "system", "content": self.prompts.text("followups")},
                                              {"role": "user", "content": "Question: %s\nAnswer: %s\n\nSuggest only NEW questions that these passages can answer and that the answer above does not already cover. Ask about the topic itself, never about the wording of an example:\n%s" % (question, answer[:800], "\n".join("- %s. %s" % (e["title"][:80], e["text"][:200]) for e in evidence[:4]))}])
                qs = [re.sub(r"^[-*\d.)\s]+", "", l.replace("`", "").replace("**", "")).strip() for l in out.splitlines() if "?" in l]
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
            s = self.provider.complete([{"role": "system", "content": self.prompts.text("summary")},
                                        {"role": "user", "content": text}])
            self.store.set_summary(topic, s[:600])
        except providers.ProviderError:
            pass
