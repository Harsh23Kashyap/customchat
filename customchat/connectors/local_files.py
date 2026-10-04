"""Search a folder of .md .txt .json .csv files with BM25. No network, no embeddings needed."""
import glob, json, math, os, re
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
        self.docs = []
        for p in sorted(glob.glob(os.path.join(root, "**", "*"), recursive=True)):
            if os.path.isfile(p) and p.lower().endswith((".md", ".txt", ".json", ".csv")):
                self._add(p, root)
        n = len(self.docs) or 1
        df = {}
        for d in self.docs:
            for t in set(d["tok"]):
                df[t] = df.get(t, 0) + 1
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        self.avg = sum(len(d["tok"]) for d in self.docs) / n

    def _add(self, path, root):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
        title = os.path.splitext(os.path.relpath(path, root))[0]
        m = re.match(r"\s*#\s+(.+)", raw)
        if m:
            title = m.group(1).strip()
        if path.endswith(".json"):
            try:
                raw = json.dumps(json.load(open(path, encoding="utf-8")), indent=1)
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
                                  "id": "%s#%d" % (os.path.relpath(path, root), n)})
                n += 1

    def search(self, query, k=6):
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
        return [Evidence(d["title"], d["text"], "", [], "", "", self.id, s, d["id"]) for s, d in scored[:k]]
