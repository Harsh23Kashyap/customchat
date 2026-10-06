import os, sys, tempfile, unittest, types
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from customchat import mysqlstore as m
from customchat.store import Store, SCHEMA
from customchat import accounts


class FakeCur:
    def __init__(s, log): s.log = log
    def execute(s, q, a=()): s.log.append((q, a))
    def fetchall(s): return []


class FakeDB:
    def __init__(s, log): s.log = log
    def cursor(s): return FakeCur(s.log)
    def commit(s): s.log.append(("COMMIT", ()))
    def rollback(s): pass
    def close(s): pass


def fake_driver(log):
    d = types.SimpleNamespace()
    d.cursors = types.SimpleNamespace(DictCursor=object)
    d.connect = lambda **k: FakeDB(log)
    return d


class T(unittest.TestCase):
    def test_parse(self):
        c = m.parse("mysql://bob:p%40ss@db.example:3307/chat")
        self.assertEqual((c["host"], c["port"], c["user"], c["password"], c["database"]), ("db.example", 3307, "bob", "p@ss", "chat"))
        with self.assertRaises(ValueError): m.parse("postgres://x/y")
        with self.assertRaises(ValueError): m.parse("mysql://")

    def test_sql(self):
        self.assertEqual(m.sql("INSERT OR REPLACE INTO states VALUES(?,?,?,?)"), "REPLACE INTO states VALUES(%s,%s,%s,%s)")
        self.assertIn("'deleted:%%'", m.sql("SELECT 1 WHERE style NOT LIKE 'deleted:%'"))
        self.assertIn("`key`=%s", m.sql("SELECT 1 FROM attempts WHERE key=?"))
        self.assertNotIn("``", m.sql("WHERE `key`=?"))

    def test_ddl(self):
        stmts = [m.ddl(x) for x in (SCHEMA + accounts.TABLES).split(";")]
        stmts = [x for x in stmts if x]
        text = "\n".join(stmts)
        self.assertNotIn(" TEXT", text.replace("LONGTEXT", ""))
        self.assertNotIn(" REAL", text)
        self.assertNotIn("IF NOT EXISTS turns_", text)
        self.assertIn("PRIMARY KEY(owner,name)", text)
        self.assertIn("name VARCHAR(190)", text)
        self.assertIn("`key` VARCHAR(190)", text)
        self.assertNotIn("LONGTEXT DEFAULT", text)

    def test_conn_and_store(self):
        log = []
        c = m.Conn({"host": "h"}, driver=fake_driver(log))
        c.execute("SELECT * FROM chats WHERE id=?", ("a",))
        self.assertEqual(log[-1], ("SELECT * FROM chats WHERE id=%s", ("a",)))
        c.executescript(SCHEMA)
        self.assertTrue(any(q.startswith("CREATE TABLE") for q, _ in log))
        self.assertTrue(any(q.startswith("CREATE INDEX turns_chat") for q, _ in log))

    def test_fallback_when_unreachable(self):
        with tempfile.TemporaryDirectory() as d:
            s = Store(os.path.join(d, "x.db"), url="mysql://u:p@127.0.0.1:1/nope")
            self.assertEqual(s.kind, "sqlite")
            cid = s.new_chat("o", "hi")
            self.assertEqual(s.chat("o", cid)["title"], "hi")

    def test_bad_url_falls_back(self):
        with tempfile.TemporaryDirectory() as d:
            s = Store(os.path.join(d, "x.db"), url="nonsense")
            self.assertEqual(s.kind, "sqlite")

    def test_default_is_sqlite(self):
        with tempfile.TemporaryDirectory() as d:
            os.environ.pop("CUSTOMCHAT_DB_URL", None)
            self.assertEqual(Store(os.path.join(d, "x.db")).kind, "sqlite")


if __name__ == "__main__":
    unittest.main()
