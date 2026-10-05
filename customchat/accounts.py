"""Accounts: sign up, sign in, sign out, change password. Standard library only.
Passwords are stored as salted PBKDF2 hashes. Sessions are random tokens kept only as hashes."""
import hashlib, hmac, os, re, secrets, time

ITER = 200_000
SESSION_DAYS = 30
EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s]{2,}$")

TABLES = """
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, email TEXT UNIQUE, name TEXT, salt BLOB, hash BLOB, created REAL);
CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user TEXT, expires REAL);
CREATE TABLE IF NOT EXISTS attempts(key TEXT, ts REAL);
"""


def _hash(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, ITER)


def _th(token):
    return hashlib.sha256(token.encode()).hexdigest()


class Accounts:
    def __init__(self, store, allow_signup=True):
        self.s = store
        self.allow_signup = allow_signup
        with store.c() as c:
            c.executescript(TABLES)

    def _check_pw(self, pw):
        if not isinstance(pw, str) or not 8 <= len(pw) <= 200:
            raise ValueError("Password must be 8 to 200 characters")

    def signup(self, email, name, pw):
        if not self.allow_signup and self.s.q("SELECT 1 FROM users LIMIT 1"):
            raise PermissionError("Sign-ups are closed")
        email = str(email or "").strip().lower()
        if not EMAIL.match(email):
            raise ValueError("Enter a valid email address")
        self._check_pw(pw)
        if self.s.q("SELECT 1 FROM users WHERE email=?", (email,), one=True):
            raise ValueError("An account with that email already exists")
        uid, salt = "u_" + secrets.token_hex(8), os.urandom(16)
        self.s.q("INSERT INTO users VALUES(?,?,?,?,?,?)", (uid, email, str(name or "").strip()[:60] or email.split("@")[0], salt, _hash(pw, salt), time.time()), write=True)
        return uid

    def _throttle(self, key):
        now = time.time()
        self.s.q("DELETE FROM attempts WHERE ts<?", (now - 600,), write=True)
        if len(self.s.q("SELECT 1 FROM attempts WHERE key=?", (key,))) >= 8:
            raise PermissionError("Too many attempts, try again in a few minutes")

    def login(self, email, pw, ip=""):
        email = str(email or "").strip().lower()
        self._throttle(email)
        u = self.s.q("SELECT * FROM users WHERE email=?", (email,), one=True)
        ok = bool(u) and hmac.compare_digest(_hash(str(pw or ""), u["salt"]), u["hash"])
        if not ok:
            self.s.q("INSERT INTO attempts VALUES(?,?)", (email, time.time()), write=True)
            raise PermissionError("Wrong email or password")
        return u["id"], self._session(u["id"])

    def _session(self, uid):
        t = secrets.token_urlsafe(32)
        self.s.q("INSERT INTO sessions VALUES(?,?,?)", (_th(t), uid, time.time() + SESSION_DAYS * 86400), write=True)
        return t

    def user_for(self, token):
        if not token:
            return None
        r = self.s.q("SELECT u.id,u.email,u.name FROM sessions s JOIN users u ON u.id=s.user WHERE s.token_hash=? AND s.expires>?", (_th(token), time.time()), one=True)
        return dict(r) if r else None

    def logout(self, token):
        if token:
            self.s.q("DELETE FROM sessions WHERE token_hash=?", (_th(token),), write=True)

    def change_password(self, uid, old, new, keep_token=None):
        u = self.s.q("SELECT * FROM users WHERE id=?", (uid,), one=True)
        if not u or not hmac.compare_digest(_hash(str(old or ""), u["salt"]), u["hash"]):
            raise PermissionError("Current password is wrong")
        self._check_pw(new)
        salt = os.urandom(16)
        self.s.q("UPDATE users SET salt=?,hash=? WHERE id=?", (salt, _hash(new, salt), uid), write=True)
        # sign out every other device
        self.s.q("DELETE FROM sessions WHERE user=? AND token_hash!=?", (uid, _th(keep_token or "")), write=True)

    def delete_account(self, uid, pw):
        u = self.s.q("SELECT * FROM users WHERE id=?", (uid,), one=True)
        if not u or not hmac.compare_digest(_hash(str(pw or ""), u["salt"]), u["hash"]):
            raise PermissionError("Password is wrong")
        for t, col in (("sessions", "user"), ("chats", "owner"), ("topics", "owner"), ("feedback", "owner"), ("states", "owner"), ("profile", "owner"), ("uploads", "owner")):
            self.s.q(f"DELETE FROM {t} WHERE {col}=?", (uid,), write=True)
        self.s.q("DELETE FROM users WHERE id=?", (uid,), write=True)
