"""SQLite storage. Chats are sessions; conversations (topics) are threads of thought that can span chats."""
import json, os, sqlite3, time, uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS chats(id TEXT PRIMARY KEY, owner TEXT, title TEXT, pinned INTEGER DEFAULT 0, deleted REAL, created REAL);
CREATE TABLE IF NOT EXISTS topics(id TEXT PRIMARY KEY, owner TEXT, title TEXT, summary TEXT DEFAULT '', created REAL);
CREATE TABLE IF NOT EXISTS turns(id TEXT PRIMARY KEY, chat TEXT, topic TEXT, question TEXT, standalone TEXT, answer TEXT, evidence TEXT, ledger TEXT, style TEXT, created REAL);
CREATE TABLE IF NOT EXISTS feedback(turn TEXT PRIMARY KEY, owner TEXT, rating INTEGER, created REAL);
CREATE TABLE IF NOT EXISTS profile(owner TEXT PRIMARY KEY, text TEXT, updated REAL);
CREATE TABLE IF NOT EXISTS evidence_cache(key TEXT PRIMARY KEY, payload TEXT, created REAL);
CREATE TABLE IF NOT EXISTS uploads(id TEXT PRIMARY KEY, owner TEXT, name TEXT, text TEXT, created REAL);
CREATE INDEX IF NOT EXISTS turns_chat ON turns(chat, created);
CREATE INDEX IF NOT EXISTS turns_topic ON turns(topic, created);
"""


class Store:
    def __init__(self, path):
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.path = path
        self._mem = sqlite3.connect(":memory:", check_same_thread=False) if path == ":memory:" else None
        with self.c() as c:
            c.executescript(SCHEMA)

    def c(self):
        if self._mem:
            self._mem.row_factory = sqlite3.Row
            return self._mem
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        return c

    def q(self, sql, args=(), one=False, write=False):
        c = self.c()
        try:
            cur = c.execute(sql, args)
            rows = cur.fetchall()
            if write:
                c.commit()
            return (rows[0] if rows else None) if one else [dict(r) for r in rows]
        finally:
            if not self._mem:
                c.close()

    # chats
    def new_chat(self, owner, title="New chat"):
        i = str(uuid.uuid4())
        self.q("INSERT INTO chats(id,owner,title,created) VALUES(?,?,?,?)", (i, owner, title[:140], time.time()), write=True)
        return i

    def chats(self, owner, search=""):
        like = "%" + search.lower() + "%"
        return self.q("SELECT id,title,pinned,created FROM chats WHERE owner=? AND deleted IS NULL AND lower(title) LIKE ? "
                      "ORDER BY pinned DESC, created DESC", (owner, like))

    def chat(self, owner, chat):
        r = self.q("SELECT * FROM chats WHERE id=? AND owner=? AND deleted IS NULL", (chat, owner), one=True)
        if not r:
            raise PermissionError("Chat not found")
        return dict(r)

    def rename_chat(self, owner, chat, title):
        self.chat(owner, chat)
        title = str(title).strip()
        if not title or len(title) > 140:
            raise ValueError("Title must be 1-140 characters")
        self.q("UPDATE chats SET title=? WHERE id=?", (title, chat), write=True)

    def pin(self, owner, chat, pinned):
        self.chat(owner, chat)
        self.q("UPDATE chats SET pinned=? WHERE id=?", (1 if pinned else 0, chat), write=True)

    def delete_chat(self, owner, chat):
        self.chat(owner, chat)
        self.q("UPDATE chats SET deleted=? WHERE id=?", (time.time(), chat), write=True)

    def restore_chat(self, owner, chat, window=30):
        r = self.q("SELECT deleted FROM chats WHERE id=? AND owner=?", (chat, owner), one=True)
        if not r or not r["deleted"] or time.time() - r["deleted"] > window:
            raise PermissionError("Restore expired")
        self.q("UPDATE chats SET deleted=NULL WHERE id=?", (chat,), write=True)

    # topics (conversations)
    def new_topic(self, owner, title):
        i = str(uuid.uuid4())
        self.q("INSERT INTO topics(id,owner,title,created) VALUES(?,?,?,?)", (i, owner, title[:120], time.time()), write=True)
        return i

    def topic(self, owner, topic):
        r = self.q("SELECT * FROM topics WHERE id=? AND owner=?", (topic, owner), one=True)
        if not r:
            raise PermissionError("Conversation not found")
        return dict(r)

    def topics(self, owner):
        return self.q("SELECT t.id,t.title,t.summary,t.created,(SELECT COUNT(*) FROM turns u WHERE u.topic=t.id) AS turns "
                      "FROM topics t WHERE t.owner=? ORDER BY t.created DESC", (owner,))

    def rename_topic(self, owner, topic, title):
        self.topic(owner, topic)
        self.q("UPDATE topics SET title=? WHERE id=?", (str(title).strip()[:120], topic), write=True)

    def set_summary(self, topic, summary):
        self.q("UPDATE topics SET summary=? WHERE id=?", (summary, topic), write=True)

    def last_topic(self, chat):
        r = self.q("SELECT topic FROM turns WHERE chat=? ORDER BY created DESC LIMIT 1", (chat,), one=True)
        return r["topic"] if r else None

    # turns
    def add_turn(self, chat, topic, question, standalone, answer, evidence, ledger, style):
        i = str(uuid.uuid4())
        self.q("INSERT INTO turns VALUES(?,?,?,?,?,?,?,?,?,?)", (i, chat, topic, question, standalone, answer,
               json.dumps(evidence), json.dumps(ledger), style, time.time()), write=True)
        return i

    def turns(self, owner, chat):
        self.chat(owner, chat)
        return [self._turn(r) for r in self.q("SELECT * FROM turns WHERE chat=? AND style NOT LIKE 'deleted:%' ORDER BY created", (chat,))]

    def topic_turns(self, owner, topic, limit=200):
        self.topic(owner, topic)
        return [self._turn(r) for r in self.q("SELECT * FROM turns WHERE topic=? AND style NOT LIKE 'deleted:%' ORDER BY created DESC LIMIT ?", (topic, limit))][::-1]

    def turn(self, owner, turn):
        r = self.q("SELECT t.* FROM turns t JOIN chats c ON c.id=t.chat WHERE t.id=? AND c.owner=?", (turn, owner), one=True)
        if not r:
            raise PermissionError("Turn not found")
        return self._turn(dict(r))

    @staticmethod
    def _turn(r):
        r = dict(r)
        r["evidence"] = json.loads(r["evidence"] or "[]")
        r["ledger"] = json.loads(r["ledger"] or "[]")
        return r

    # turns: delete / restore
    def delete_turn(self, owner, turn):
        t = self.turn(owner, turn)
        self.q("UPDATE turns SET style=? WHERE id=?", ("deleted:" + t["style"], turn), write=True)

    def restore_turn(self, owner, turn):
        r = self.q("SELECT t.style FROM turns t JOIN chats c ON c.id=t.chat WHERE t.id=? AND c.owner=?", (turn, owner), one=True)
        if not r or not str(r["style"]).startswith("deleted:"):
            raise PermissionError("Turn not found")
        self.q("UPDATE turns SET style=? WHERE id=?", (r["style"][8:], turn), write=True)

    # uploads (private text the owner adds in the UI)
    def add_upload(self, owner, name, text):
        i = str(uuid.uuid4())
        self.q("INSERT INTO uploads VALUES(?,?,?,?,?)", (i, owner, name[:120], text, time.time()), write=True)
        return i

    def uploads(self, owner):
        return self.q("SELECT id,name,text FROM uploads WHERE owner=? ORDER BY created", (owner,))

    def delete_upload(self, owner, upload):
        self.q("DELETE FROM uploads WHERE id=? AND owner=?", (upload, owner), write=True)

    def rate(self, owner, turn, rating):
        rating = 1 if rating > 0 else -1 if rating < 0 else 0
        if rating == 0:
            self.q("DELETE FROM feedback WHERE turn=? AND owner=?", (turn, owner), write=True)
        else:
            self.q("INSERT OR REPLACE INTO feedback VALUES(?,?,?,?)", (turn, owner, rating, time.time()), write=True)
        return rating

    def ratings(self, owner, chat):
        return {r["turn"]: r["rating"] for r in self.q(
            "SELECT f.turn, f.rating FROM feedback f JOIN turns t ON t.id=f.turn WHERE f.owner=? AND t.chat=?", (owner, chat))}

    def stats(self, owner):
        one = lambda sql: (self.q(sql, (owner,), one=True) or {"n": 0})["n"]
        return {"chats": one("SELECT COUNT(*) n FROM chats WHERE owner=? AND deleted IS NULL"),
                "turns": one("SELECT COUNT(*) n FROM turns t JOIN chats c ON c.id=t.chat WHERE c.owner=? AND t.style NOT LIKE 'deleted:%'"),
                "uploads": one("SELECT COUNT(*) n FROM uploads WHERE owner=?"),
                "helpful": one("SELECT COUNT(*) n FROM feedback WHERE owner=? AND rating>0"),
                "not_helpful": one("SELECT COUNT(*) n FROM feedback WHERE owner=? AND rating<0")}

    def get_profile(self, owner):
        r = self.q("SELECT text FROM profile WHERE owner=?", (owner,), one=True)
        return r["text"] if r else ""

    def set_profile(self, owner, text):
        text = (text or "").strip()[:3000]
        if text:
            self.q("INSERT OR REPLACE INTO profile VALUES(?,?,?)", (owner, text, time.time()), write=True)
        else:
            self.q("DELETE FROM profile WHERE owner=?", (owner,), write=True)
        return text

    def recent_questions(self, owner, limit=400):
        return self.q("SELECT t.id, t.chat, t.question FROM turns t JOIN chats c ON c.id=t.chat WHERE c.owner=? AND c.deleted IS NULL AND t.style NOT LIKE 'deleted:%' ORDER BY t.created DESC LIMIT ?", (owner, limit))

    def ping(self):
        try:
            return bool(self.q("SELECT 1 AS x"))
        except Exception:
            return False

    def import_chats(self, owner, chats):
        n = 0
        for c in chats[:200]:
            if not isinstance(c, dict):
                continue
            cid = self.new_chat(owner, str(c.get("title") or "Imported")[:120])
            for t in (c.get("turns") or [])[:500]:
                if isinstance(t, dict) and t.get("question") and t.get("answer"):
                    self.add_turn(cid, None, str(t["question"])[:2000], str(t["question"])[:2000], str(t["answer"]), t.get("evidence") or [], [], "standard")
            n += 1
        return n

    def export_all(self, owner):
        out = []
        for c in self.q("SELECT id,title,pinned,created FROM chats WHERE owner=? AND deleted IS NULL ORDER BY created", (owner,)):
            c["turns"] = [{k: t[k] for k in ("question", "answer", "evidence", "created")} for t in self.turns(owner, c["id"])]
            out.append(c)
        return out
