"""Search a folder of .md .txt .json .csv files with BM25. No network, no embeddings needed."""
import glob, hashlib, json, math, os, re, threading, time
from .base import Evidence

TOKEN = re.compile(r"[a-z0-9]{2,}")
STOP = set("the of and to in is are for on with that this as by an be or it at from was were which can".split())


def tokens(s):
    return [t for t in TOKEN.findall(s.lower()) if t not in STOP]


def chunks(text, size=900):
    paras, cur, out = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()], "", []
    for p in paras:
        if cur and len(cur) + len(p) > size:
            out.append(cur); cur = p
        else:
            cur = (cur + "\n\n" + p).strip()
    if cur:
        out.append(cur)
    return out


class LocalFiles:
    def __init__(self, block, base_dir="."):
        self.id, self.label = block["id"], block["label"]
        root = block.get("path", "docs")
        root = root if os.path.isabs(root) else os.path.join(base_dir, root)
        self.root = os.path.abspath(root)
        self.refresh_interval = float(block.get("refresh_interval", 30))
        self._lock = threading.RLock()
        self._snapshot = None
        self.checked_at = self.indexed_at = 0
        self.last_error = ""
        self.revision = ""
        self.docs = []; self.idf = {}; self.avg = 0
        try: self.refresh(force=True)
        except OSError: pass  # Keep the app available; failed folders are excluded until recovery.

    def _scan(self):
        if os.path.realpath(self.root) != self.root:
            raise OSError("Local document folder must not use symlinks")
        if not os.path.isdir(self.root):
            raise OSError("Local document folder is missing or unavailable")
        rows = []
        for p in sorted(glob.glob(os.path.join(self.root, "**", "*"), recursive=True)):
            if not p.lower().endswith((".md", ".txt", ".json", ".csv")): continue
            if os.path.islink(p) or os.path.realpath(p) != os.path.abspath(p):
                raise OSError("Local documents must not use symlinks")
            if os.path.isfile(p):
                with open(p, "rb") as f: data = f.read()
                rows.append((os.path.relpath(p, self.root), data, hashlib.sha256(data).hexdigest()))
        return rows

    def refresh(self, force=False):
        """Swap a complete content-hashed index only after a successful scan."""
        with self._lock:
            if not force and not self.last_error and time.time() - self.checked_at < self.refresh_interval:
                return False
            self.checked_at = time.time()
            try:
                rows = self._scan()
                signature = tuple((name, digest) for name, _, digest in rows)
                if signature == self._snapshot:
                    self.last_error = ""
                    return False
                nxt = LocalFiles.__new__(LocalFiles)
                nxt.docs = []
                for name, data, digest in rows:
                    nxt._add(os.path.join(self.root, name), self.root, data, digest)
                n = len(nxt.docs) or 1
                df = {}
                for d in nxt.docs:
                    for t in set(d["tok"]): df[t] = df.get(t, 0) + 1
                idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
                avg = sum(len(d["tok"]) for d in nxt.docs) / n
                self.docs, self.idf, self.avg = nxt.docs, idf, avg
                self._snapshot = signature
                self.revision = hashlib.sha256(json.dumps(signature).encode()).hexdigest()
                self.indexed_at = time.time(); self.last_error = ""
                return True
            except OSError:
                self.last_error = "Local folder check failed. No old passages will be used until it recovers."
                raise

    def status(self):
        with self._lock:
            return {"id": self.id, "label": self.label, "documents": len(self._snapshot or ()),
                    "chunks": len(self.docs), "revision": self.revision,
                    "checked_at": self.checked_at, "indexed_at": self.indexed_at,
                    "refresh_interval": self.refresh_interval, "error": self.last_error}

    def _add(self, path, root, data=None, digest=""):
        if data is None:
            with open(path, "rb") as f: data = f.read()
        raw = data.decode("utf-8", errors="replace")
        digest = digest or hashlib.sha256(data).hexdigest()
        title = os.path.splitext(os.path.relpath(path, root))[0]
        m = re.match(r"\s*#\s+(.+)", raw)
        if m:
            title = m.group(1).strip()
        if path.endswith(".json"):
            try:
                raw = json.dumps(json.loads(raw), indent=1)
            except ValueError:
                pass
        sections = re.split(r"(?m)^(?=#{1,3}\s)", raw) if raw.lstrip().startswith("#") or "\n#" in raw else [raw]
        n = 0
        for sec in sections:
            if not sec.strip():
                continue
            h = re.match(r"\s*#{1,3}\s+(.+)", sec)
            sec_title = h.group(1).strip() if h else title
            body = re.sub(r"^\s*#{1,3}\s+.*\n?", "", sec, count=1) if h else sec
            for c in chunks(body):
                self.docs.append({"title": sec_title, "text": c, "tok": tokens(sec_title + " " + c),
                                  "id": "%s#%d" % (os.path.relpath(path, root), n), "document": os.path.relpath(path, root), "version": digest})
                n += 1

    def search(self, query, k=6):
        if hasattr(self, "_lock"):
            with self._lock:
                self.refresh()
                return self._search(query, k)
        return self._search(query, k)

    def _search(self, query, k):
        q = tokens(query)
        scored = []
        for d in self.docs:
            tf = {}
            for t in d["tok"]:
                tf[t] = tf.get(t, 0) + 1
            s = 0.0
            for t in q:
                if t in tf:
                    s += self.idf.get(t, 0) * tf[t] * 2.2 / (tf[t] + 1.2 * (0.25 + 0.75 * len(d["tok"]) / (self.avg or 1)))
            if s > 0:
                scored.append((s, d))
        scored.sort(key=lambda x: -x[0])
        return [{**Evidence(d["title"], d["text"], "", [], "", "", self.id, s, d["id"]),
                 **({"document": d["document"], "version": d["version"]} if "version" in d else {})} for s, d in scored[:k]]
