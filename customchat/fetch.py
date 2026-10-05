"""Safe URL loader: http(s) only, public addresses only, no redirects, size and time limits."""
import ipaddress, socket, urllib.request, urllib.error
from html.parser import HTMLParser
from urllib.parse import urlparse

MAX_BYTES = 600_000


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.out, self.skip, self.title, self._t = [], 0, "", False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"): self.skip += 1
        if tag == "title": self._t = True
        if tag in ("p", "br", "li", "h1", "h2", "h3", "div", "tr"): self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.skip: self.skip -= 1
        if tag == "title": self._t = False

    def handle_data(self, d):
        if self._t: self.title += d
        elif not self.skip: self.out.append(d)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def check_public(url):
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise ValueError("Only http and https links are supported")
    try:
        infos = socket.getaddrinfo(u.hostname, u.port or (443 if u.scheme == "https" else 80))
    except OSError:
        raise ValueError("Could not resolve that address") from None
    for i in infos:
        ip = ipaddress.ip_address(i[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError("That address is not a public website")
    return u


def load(url, opener=None):
    """Return (name, text) for a public page. Follows up to 3 redirects, re-checking each hop."""
    for _ in range(4):
        check_public(url)
        op = opener or urllib.request.build_opener(_NoRedirect)
        try:
            r = op.open(urllib.request.Request(url, headers={"User-Agent": "CustomChat/1.0"}), timeout=15)
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
                from urllib.parse import urljoin
                url = urljoin(url, e.headers["Location"]); continue
            raise ValueError("The site returned HTTP %d" % e.code) from None
        except (urllib.error.URLError, OSError) as e:
            raise ValueError("Could not fetch that page") from None
        raw = r.read(MAX_BYTES + 1)[:MAX_BYTES]
        ctype = r.headers.get("Content-Type", "")
        text = raw.decode(r.headers.get_content_charset() or "utf-8", "replace")
        name = urlparse(url).netloc
        if "html" in ctype or text.lstrip().lower().startswith(("<!doctype", "<html")):
            p = _Text(); p.feed(text)
            text = "".join(p.out)
            name = (p.title.strip() or name)[:80]
        elif not ctype.startswith("text/") and "json" not in ctype:
            raise ValueError("Only text and web pages can be loaded")
        text = "\n".join(l.strip() for l in text.splitlines() if l.strip())[:150_000]
        if not text:
            raise ValueError("No readable text on that page")
        return name, text
    raise ValueError("Too many redirects")
