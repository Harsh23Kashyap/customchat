"""Local secret store for API keys typed into the Configuration page.

Keys live in one file (secrets.json) next to the database, mode 0600, never inside the repo (data/ is ignored).
They are never returned by any API, never logged, never put in exports. Environment variables still work and
are used when no saved key exists.
"""
import json, os, threading

_lock = threading.Lock()


class SecretStore:
    def __init__(self, folder):
        self.path = os.path.join(folder, "secrets.json")
        self._d = None

    def _load(self):
        if self._d is None:
            try:
                with open(self.path) as f:
                    d = json.load(f)
                self._d = d if isinstance(d, dict) else {}
            except (OSError, ValueError):
                self._d = {}
        return self._d

    def _write(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        tmp = self.path + ".tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(self._d, f)
        os.replace(tmp, self.path)
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def get(self, name):
        with _lock:
            return self._load().get(name) or ""

    def has(self, name):
        return bool(self.get(name))

    def set(self, name, value):
        value = str(value or "").strip()
        if not value or len(value) > 4096 or any(c in value for c in "\r\n\t "):
            raise ValueError("That does not look like an API key")
        with _lock:
            self._load()[name] = value
            self._write()

    def delete(self, name):
        with _lock:
            self._load().pop(name, None)
            self._write()


STORE = None  # set by the server at start up


def saved(name):
    return STORE.get(name) if STORE else ""
