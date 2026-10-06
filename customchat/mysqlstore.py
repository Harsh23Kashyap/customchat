"""Optional MySQL/MariaDB backend for Store. SQLite stays the default and the fallback.
Turned on by the CUSTOMCHAT_DB_URL environment variable, for example mysql://user:pass@host:3306/dbname.
The URL is read from the environment only, so a password never sits in a file in the repo.
Needs the PyMySQL package (pip install -r requirements-mysql.txt). If anything is missing or
unreachable, Store falls back to SQLite and says so."""
import os, re
from urllib.parse import urlparse, unquote

LONG = {"answer", "evidence", "ledger", "text", "payload", "summary", "standalone", "question"}


def parse(url):
    u = urlparse(url)
    if u.scheme not in ("mysql", "mariadb") or not u.hostname:
        raise ValueError("CUSTOMCHAT_DB_URL must look like mysql://user:password@host:3306/dbname")
    return dict(host=u.hostname, port=u.port or 3306, user=unquote(u.username or ""), password=unquote(u.password or ""),
                database=(u.path or "/").lstrip("/") or "customchat")


def sql(s):
    """Translate the SQLite statements the app uses into MySQL."""
    s = s.replace("%", "%%").replace("?", "%s")
    s = re.sub(r"(?i)^\s*INSERT OR REPLACE", "REPLACE", s)
    s = re.sub(r"(?<![`\w])key(?![`\w])", "`key`", s)
    return s


def ddl(stmt):
    stmt = stmt.strip()
    if not stmt:
        return None
    stmt = re.sub(r"(?i)^CREATE INDEX IF NOT EXISTS", "CREATE INDEX", stmt)
    stmt = re.sub(r"(?i)\bREAL\b", "DOUBLE", stmt)
    stmt = re.sub(r"(?i)\bBLOB\b", "LONGBLOB", stmt)
    def col(m):
        n = m.group(1)
        return n + (" LONGTEXT" if n.lower() in LONG else " VARCHAR(190)")
    stmt = re.sub(r"(?i)\b(\w+) TEXT\b", col, stmt)
    stmt = re.sub(r"(?i)(LONGTEXT) DEFAULT ''", r"\1", stmt)
    stmt = re.sub(r"(?<![`\w])key(?![`\w])", "`key`", stmt)
    return stmt


class Conn:
    """Looks enough like a sqlite3 connection for Store and Accounts."""
    def __init__(self, cfg, driver=None):
        if driver is None:
            import pymysql
            driver = pymysql
        self.db = driver.connect(charset="utf8mb4", autocommit=False, connect_timeout=8,
                                 cursorclass=driver.cursors.DictCursor, **cfg)

    def execute(self, q, args=()):
        cur = self.db.cursor()
        cur.execute(sql(q), tuple(args))
        return cur

    def executescript(self, script):
        for part in script.split(";"):
            d = ddl(part)
            if not d:
                continue
            try:
                self.execute(d)
            except Exception as e:
                if "1061" in str(e) or "Duplicate key name" in str(e):
                    continue
                raise
        self.db.commit()

    def commit(self):
        self.db.commit()

    def close(self):
        try:
            self.db.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        if a[0] is None:
            self.db.commit()
        else:
            self.db.rollback()
        return False
