"""SQLite storage. Chats are sessions; conversations (topics) are threads of thought that can span chats."""
import json, os, sqlite3, time, uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS chats(id TEXT PRIMARY KEY, owner TEXT, title TEXT, pinned INTEGER DEFAULT 0, deleted REAL, created REAL);
CREATE TABLE IF NOT EXISTS topics(id TEXT PRIMARY KEY, owner TEXT, title TEXT, summary TEXT DEFAULT '', created REAL);
CREATE TABLE IF NOT EXISTS turns(id TEXT PRIMARY KEY, chat TEXT, topic TEXT, question TEXT, standalone TEXT, answer TEXT, evidence TEXT, ledger TEXT, style TEXT, created REAL);
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
        return [self._turn(r) for r in self.q("SELECT * FROM turns WHERE chat=? ORDER BY created", (chat,))]

    def topic_turns(self, owner, topic, limit=200):
        self.topic(owner, topic)
        return [self._turn(r) for r in self.q("SELECT * FROM turns WHERE topic=? ORDER BY created DESC LIMIT ?", (topic, limit))][::-1]

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
