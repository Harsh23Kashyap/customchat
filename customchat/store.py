"""SQLite storage (MySQL optional, see mysqlstore.py). Chats are sessions; conversations (topics) are threads of thought that can span chats."""
import json, os, re, sqlite3, time, uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS chats(id TEXT PRIMARY KEY, owner TEXT, title TEXT, pinned INTEGER DEFAULT 0, deleted REAL, created REAL);
CREATE TABLE IF NOT EXISTS topics(id TEXT PRIMARY KEY, owner TEXT, title TEXT, summary TEXT DEFAULT '', created REAL);
CREATE TABLE IF NOT EXISTS turns(id TEXT PRIMARY KEY, chat TEXT, topic TEXT, question TEXT, standalone TEXT, answer TEXT, evidence TEXT, ledger TEXT, style TEXT, created REAL);
CREATE TABLE IF NOT EXISTS feedback(turn TEXT PRIMARY KEY, owner TEXT, rating INTEGER, created REAL);
CREATE TABLE IF NOT EXISTS states(owner TEXT, name TEXT, payload TEXT, updated REAL, PRIMARY KEY(owner,name));
CREATE TABLE IF NOT EXISTS profile(owner TEXT PRIMARY KEY, text TEXT, updated REAL);
CREATE TABLE IF NOT EXISTS evidence_cache(key TEXT PRIMARY KEY, payload TEXT, created REAL);
CREATE TABLE IF NOT EXISTS uploads(id TEXT PRIMARY KEY, owner TEXT, name TEXT, text TEXT, created REAL);
CREATE INDEX IF NOT EXISTS turns_chat ON turns(chat, created);
CREATE INDEX IF NOT EXISTS turns_topic ON turns(topic, created);
"""


class Store:
    def __init__(self, path, url=None):
        self.path = path
        self.kind = "sqlite"
        self._my = None
        self.degraded = ""
        self._mem = None
        if path != ":memory:":
            try:
                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            except OSError as e:
                self._degrade("cannot create the data folder (%s)" % (e.strerror or e))
                return
        url = url if url is not None else os.environ.get("CUSTOMCHAT_DB_URL", "")
        if url and path != ":memory:":
            try:
                from . import mysqlstore
                self._my = mysqlstore.parse(url)
                with self.c() as c:
                    c.executescript(SCHEMA)
                self.kind = "mysql"
                print("customchat: using MySQL at " + self._my["host"])
                return
            except Exception as e:
                self._my = None
                print("customchat: MySQL not available (" + str(e)[:120] + "); using the local SQLite file instead")
        self._mem = sqlite3.connect(":memory:", check_same_thread=False) if path == ":memory:" else None
        try:
            with self.c() as c:
                c.executescript(SCHEMA)
        except sqlite3.DatabaseError as e:
            # A damaged data file must not stop the app. Keep the bad file for recovery and start fresh.
            if self._mem or not os.path.exists(path):
                if self._mem or self._unwritable(e):
                    if self._mem: raise
                    self._degrade(str(e)); return
                raise
            if self._unwritable(e):
                self._degrade(str(e)); return
            keep = path + ".corrupt-" + time.strftime("%Y%m%d-%H%M%S")
            os.replace(path, keep)
            print("customchat: data file was damaged; moved to " + keep + " and started a new one")
            with self.c() as c:
                c.executescript(SCHEMA)

    def c(self):
        if self._my:
            from . import mysqlstore
            return mysqlstore.Conn(self._my)
        if self._mem:
            self._mem.row_factory = sqlite3.Row
            return self._mem
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        return c

    @staticmethod
    def _unwritable(e):
        m = str(e).lower()
        return any(k in m for k in ("readonly", "read-only", "disk is full", "database or disk is full", "unable to open", "disk i/o", "permission"))

    def _degrade(self, why):
        """Disk full, read-only or missing folder: keep answering from memory instead of failing. History is not saved."""
        self._mem = sqlite3.connect(":memory:", check_same_thread=False)
        self._mem.executescript(SCHEMA)
        try:
            from .accounts import TABLES
            self._mem.executescript(TABLES)
        except Exception:
            pass
        self.degraded = "Chats cannot be saved right now (%s). Answers still work; history is kept only until the app restarts." % str(why)[:100]
        print("customchat: " + self.degraded)

    def q(self, sql, args=(), one=False, write=False):
        for attempt in (0, 1):
            c = self.c(); ismem = bool(self._mem)
            try:
                cur = c.execute(sql, args)
                rows = cur.fetchall()
                if write:
                    c.commit()
                return (rows[0] if rows else None) if one else [dict(r) for r in rows]
            except sqlite3.OperationalError as e:
                if attempt == 0 and not self._mem and not self._my and self.kind == "sqlite" and write and self._unwritable(e):
                    self._degrade(str(e)); continue
                raise
            finally:
                if not ismem:
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
        self.delete_state(owner, "memory-" + chat)
        self.q("UPDATE chats SET deleted=? WHERE id=?", (time.time(), chat), write=True)

    def restore_chat(self, owner, chat, window=30):
        r = self.q("SELECT deleted FROM chats WHERE id=? AND owner=?", (chat, owner), one=True)
        if not r or not r["deleted"] or time.time() - r["deleted"] > window:
            raise PermissionError("Restore expired")
        self.q("UPDATE chats SET deleted=NULL WHERE id=?", (chat,), write=True)

    # topics (conversations)
    def new_topic(self, owner, title):
        i = str(uuid.uuid4())
        self.q("INSERT INTO topics(id,owner,title,summary,created) VALUES(?,?,?,'',?)", (i, owner, title[:120], time.time()), write=True)
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

    @staticmethod
    def _history_where():
        return (" FROM turns t JOIN chats c ON c.id=t.chat WHERE c.owner=? AND c.id=? AND c.deleted IS NULL "
                "AND t.topic=? AND t.style NOT LIKE 'deleted:%' AND NOT EXISTS "
                "(SELECT 1 FROM states s WHERE s.owner=c.owner AND SUBSTR(s.name,1,6)='scope-' AND SUBSTR(s.name,7)=t.id) ")

    def history_ids(self, owner, chat, topic):
        self.chat(owner, chat); self.topic(owner, topic)
        return [r["id"] for r in self.q("SELECT t.id" + self._history_where() + "ORDER BY t.created, t.id", (owner, chat, topic))]

    def history_turns(self, owner, chat, topic, question):
        self.chat(owner, chat); self.topic(owner, topic)
        where = self._history_where(); args = (owner, chat, topic)
        # Bound text loaded from storage, but retrieve older matching turns too.
        rows = self.q("SELECT t.id,t.question,t.answer,t.created" + where + "ORDER BY t.created DESC,t.id DESC LIMIT 200", args)
        words = sorted(set(re.findall(r"[^\W_]{3,}", question.lower())))[:12]
        if words:
            match = " OR ".join("(lower(t.question) LIKE ? OR lower(t.answer) LIKE ?)" for _ in words)
            values = tuple(v for w in words for v in ("%" + w + "%", "%" + w + "%"))
            rows += self.q("SELECT t.id,t.question,t.answer,t.created" + where + "AND (" + match + ") ORDER BY t.created DESC,t.id DESC LIMIT 40", args + values)
        return sorted({r["id"]: r for r in rows}.values(), key=lambda r: (r["created"], r["id"]))

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
        self.delete_state(owner, "memory-" + t["chat"])
        self.q("UPDATE turns SET style=? WHERE id=?", ("deleted:" + t["style"], turn), write=True)

    def restore_turn(self, owner, turn):
        r = self.q("SELECT t.style FROM turns t JOIN chats c ON c.id=t.chat WHERE t.id=? AND c.owner=?", (turn, owner), one=True)
        if not r or not str(r["style"]).startswith("deleted:"):
            raise PermissionError("Turn not found")
        self.q("UPDATE turns SET style=? WHERE id=?", (r["style"][8:], turn), write=True)

    def branch(self, owner, turn, question):
        """Copy only earlier visible turns into a new chat. Never change the original."""
        question = str(question or "").strip()
        if not question or len(question) > 2000:
            raise ValueError("Question must be 1-2000 characters")
        target = self.turn(owner, turn)
        original = self.chat(owner, target["chat"])
        rows = self.turns(owner, target["chat"])
        index = next((i for i, r in enumerate(rows) if r["id"] == turn), None)
        if index is None:
            raise PermissionError("Turn not found")
        chat = str(uuid.uuid4()); topics = {}; now = time.time()
        c = self.c()
        try:
            c.execute("INSERT INTO chats(id,owner,title,created) VALUES(?,?,?,?)", (chat, owner, ("Branch: " + original["title"])[:140], now))
            for i, r in enumerate(rows[:index]):
                old = r["topic"] or "untitled"
                if old not in topics:
                    topics[old] = str(uuid.uuid4())
                    c.execute("INSERT INTO topics(id,owner,title,summary,created) VALUES(?,?,?,'',?)", (topics[old], owner, r["question"][:120], now))
                c.execute("INSERT INTO turns VALUES(?,?,?,?,?,?,?,?,?,?)", (str(uuid.uuid4()), chat, topics[old], r["question"], r["standalone"], r["answer"], json.dumps(r["evidence"]), json.dumps(r["ledger"]), r["style"], now + i * .001))
            c.execute("INSERT INTO states VALUES(?,?,?,?)", (owner, "branch-" + chat, json.dumps({"chat": original["id"], "turn": turn}), now))
            c.commit()
        except Exception:
            if hasattr(c, "rollback"): c.rollback()
            elif hasattr(c, "db"): c.db.rollback()
            raise
        finally:
            if not self._mem: c.close()
        return {"chat": chat, "question": question, "original_chat": original["id"], "copied_turns": index}

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

    def states(self, owner):
        return [r["name"] for r in self.q("SELECT name FROM states WHERE owner=? ORDER BY updated DESC", (owner,))]

    def save_state(self, owner, name, payload):
        name = (name or "").strip()[:60]
        if not name:
            raise ValueError("Give the state a name")
        self.q("INSERT OR REPLACE INTO states VALUES(?,?,?,?)", (owner, name, json.dumps(payload), time.time()), write=True)
        return name

    def get_state(self, owner, name):
        r = self.q("SELECT payload FROM states WHERE owner=? AND name=?", (owner, name), one=True)
        if not r:
            raise ValueError("No saved state with that name")
        return json.loads(r["payload"])

    def delete_state(self, owner, name):
        self.q("DELETE FROM states WHERE owner=? AND name=?", (owner, name), write=True)

    def get_profile_fields(self, owner):
        raw = self.get_profile(owner)
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and isinstance(data.get("fields"), list):
                return data["fields"]
        except (ValueError, TypeError):
            pass
        return [{"label": "Background", "value": raw}] if raw else []

    def profile_context(self, owner):
        return "\n".join(f'{f["label"]}: {f["value"]}' for f in self.get_profile_fields(owner))

    def set_profile_fields(self, owner, fields):
        if not isinstance(fields, list) or len(fields) > 20:
            raise ValueError("Use at most 20 profile fields")
        clean = []
        for f in fields:
            if not isinstance(f, dict):
                raise ValueError("Invalid profile field")
            label, value = str(f.get("label", "")).strip(), str(f.get("value", "")).strip()
            if len(label) > 60 or len(value) > 1000:
                raise ValueError("Field names: 60 characters; values: 1000 characters")
            if value:
                if not label:
                    raise ValueError("Name each filled profile field")
                clean.append({"label": label, "value": value})
        encoded = json.dumps({"fields": clean}, ensure_ascii=False) if clean else ""
        if len(encoded) > 3000:
            raise ValueError("Profile total must be 3000 characters or less")
        self.set_profile(owner, encoded)
        return clean

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
