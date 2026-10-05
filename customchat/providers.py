"""LLM providers. All use only the standard library.

minimax, mimo, deepseek, groq, openrouter, mistral: hosted OpenAI-style services with built-in default address and key variable.

mock               deterministic, no network (tests, demos, first run)
ollama             local model via http://localhost:11434
openai             OpenAI chat completions, key from an env var
claude             Anthropic Messages API, key from ANTHROPIC_API_KEY
gemini             Google Gemini, key from GEMINI_API_KEY
openai_compatible  any OpenAI-style server (LM Studio, vLLM, llama.cpp) via base_url
"""
import json, os, re, urllib.request, urllib.error


RETRY_CODES = {408, 409, 425, 429, 500, 502, 503, 504, 529}
HUMAN = {400: "The provider rejected the request (check the model name)", 401: "The API key was refused (check the key)",
         403: "The API key is not allowed to use this model", 404: "Model or address not found (check the model name and base URL)",
         413: "The request was too large", 429: "The provider is rate limiting requests", 529: "The provider is overloaded"}


class ProviderError(RuntimeError):
    def __init__(self, msg, code=None, retry_after=None):
        super().__init__(msg)
        if code is None:
            m = re.search(r"HTTP (\d{3})", str(msg))
            code = int(m.group(1)) if m else None
        self.code, self.retry_after = code, retry_after

    @property
    def transient(self):
        return self.code is None or self.code in RETRY_CODES


def _http_error(e):
    ra = None
    try:
        ra = float(e.headers.get("Retry-After", ""))
    except (TypeError, ValueError, AttributeError):
        pass
    msg = HUMAN.get(e.code, "The provider returned an error")
    return ProviderError("%s (HTTP %d)" % (msg, e.code), e.code, ra)


def _post(url, payload, headers, timeout, retries=3):
    """POST with exponential backoff and jitter. Retries only errors that can pass (timeouts, 429, 5xx)."""
    import random, time
    for attempt in range(retries + 1):
        try:
            return _post_once(url, payload, headers, timeout)
        except ProviderError as e:
            if attempt == retries or not e.transient:
                raise
            wait = e.retry_after if e.retry_after is not None else 0.5 * (2 ** attempt)
            time.sleep(min(wait, 8) + random.uniform(0, 0.25))


def _post_once(url, payload, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise _http_error(e) from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ProviderError("Provider unreachable: %s" % getattr(e, "reason", e)) from None
    except ValueError:
        raise ProviderError("The provider sent a reply that could not be read", 502) from None


def _stream_lines(url, payload, headers, timeout, retries=2):
    """Yield lines. Retries only before the first line arrives; once text flows, errors surface."""
    import random, time
    for attempt in range(retries + 1):
        got = False
        try:
            for line in _stream_once(url, payload, headers, timeout):
                got = True
                yield line
            return
        except ProviderError as e:
            if got or attempt == retries or not e.transient:
                raise
            time.sleep(min(e.retry_after if e.retry_after is not None else 0.5 * (2 ** attempt), 8) + random.uniform(0, 0.25))


def _stream_once(url, payload, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            for raw in r:
                line = raw.decode("utf-8", "replace").strip()
                if line:
                    yield line
    except urllib.error.HTTPError as e:
        raise _http_error(e) from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ProviderError("Provider unreachable: %s" % getattr(e, "reason", e)) from None
    except ValueError:
        raise ProviderError("The provider sent a reply that could not be read", 502) from None


class Streams:
    """Default streaming: yield the finished answer word by word."""
    def stream(self, messages):
        for w in re.findall(r"\S+\s*", self.complete(messages)):
            yield w


class Mock(Streams):
    """Extractive stand-in. Quotes the first sentence of each evidence block with its citation."""
    def __init__(self, cfg): self.cfg = cfg

    def complete(self, messages):
        user = messages[-1]["content"].split("Evidence:\n", 1)[-1]
        blocks = re.findall(r"\[(\d+)\]\s*(.+?)(?=\n\[\d+\]|\Z)", user, flags=re.S)
        if not blocks:
            return "No evidence was provided."
        out = []
        for n, text in blocks[:3]:
            body = re.sub(r"^.*?\([^)]*\)\.\s*", "", text.strip().replace("\n", " "), count=1)
            first = re.split(r"(?<=[.!?])\s", body)[0]
            out.append("%s [%s]" % (first if len(first) <= 240 else first[:240].rsplit(" ", 1)[0] + "...", n))
        return " ".join(out)


class Ollama(Streams):
    def stream(self, messages):
        base = (self.base)
        for line in _stream_lines(base + "/api/chat", {"model": self.model, "messages": messages, "stream": True,
                                  "options": {"temperature": self.temp}}, {}, self.t):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("message", {}).get("content"):
                yield d["message"]["content"]

    def __init__(self, cfg):
        p = cfg["provider"]
        self.base = (p["base_url"] or os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
        self.model, self.t, self.temp = p["model"], p["timeout"], p["temperature"]

    def complete(self, messages):
        r = _post(self.base + "/api/chat", {"model": self.model, "messages": messages, "stream": False,
                                            "options": {"temperature": self.temp}}, {}, self.t)
        try:
            return r["message"]["content"].strip()
        except (KeyError, TypeError):
            raise ProviderError("Unexpected Ollama response") from None


class OpenAICompatible(Streams):
    def stream(self, messages):
        headers = {}
        if self.key_env:
            key = os.environ.get(self.key_env, "")
            if not key:
                raise ProviderError("Set the %s environment variable" % self.key_env)
            headers["Authorization"] = "Bearer " + key
        for line in _stream_lines(self.base + "/chat/completions", {"model": self.model, "messages": messages,
                                  "temperature": self.temp, "stream": True}, headers, self.t):
            if not line.startswith("data:") or line.endswith("[DONE]"):
                continue
            try:
                piece = json.loads(line[5:])["choices"][0]["delta"].get("content")
            except (ValueError, KeyError, IndexError):
                continue
            if piece:
                yield piece

    def __init__(self, cfg):
        from .schema import PRESET_PROVIDERS
        p = cfg["provider"]
        dbase, denv = PRESET_PROVIDERS.get(p["type"], ("https://api.openai.com/v1", ""))
        self.base = (p["base_url"] or dbase).rstrip("/")
        self.model, self.t, self.temp = p["model"], p["timeout"], p["temperature"]
        self.key_env = p["api_key_env"] or denv

    def complete(self, messages):
        headers = {}
        if self.key_env:
            key = os.environ.get(self.key_env, "")
            if not key:
                raise ProviderError("Set the %s environment variable" % self.key_env)
            headers["Authorization"] = "Bearer " + key
        r = _post(self.base + "/chat/completions", {"model": self.model, "messages": messages,
                                                    "temperature": self.temp}, headers, self.t)
        try:
            return r["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError):
            raise ProviderError("Unexpected provider response") from None


def _key(env):
    key = os.environ.get(env, "")
    if not key:
        raise ProviderError("Set the %s environment variable" % env)
    return key


class Claude(Streams):
    """Anthropic Messages API. Key from an env var (default ANTHROPIC_API_KEY)."""
    def __init__(self, cfg):
        p = cfg["provider"]
        self.base = (p["base_url"] or "https://api.anthropic.com").rstrip("/")
        self.model, self.t, self.temp, self.key_env = p["model"], p["timeout"], p["temperature"], p["api_key_env"] or "ANTHROPIC_API_KEY"

    def complete(self, messages):
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        turns = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in ("user", "assistant")]
        r = _post(self.base + "/v1/messages", {"model": self.model, "max_tokens": 1500, "temperature": self.temp,
                  "system": system, "messages": turns}, {"x-api-key": _key(self.key_env), "anthropic-version": "2023-06-01"}, self.t)
        try:
            return "".join(b.get("text", "") for b in r["content"] if b.get("type") == "text").strip()
        except (KeyError, TypeError):
            raise ProviderError("Unexpected provider response") from None


class Gemini(Streams):
    """Google Gemini generateContent. Key from an env var (default GEMINI_API_KEY), sent as a header."""
    def __init__(self, cfg):
        p = cfg["provider"]
        self.base = (p["base_url"] or "https://generativelanguage.googleapis.com").rstrip("/")
        self.model, self.t, self.temp, self.key_env = p["model"], p["timeout"], p["temperature"], p["api_key_env"] or "GEMINI_API_KEY"

    def complete(self, messages):
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]} for m in messages if m["role"] in ("user", "assistant")]
        body = {"contents": contents, "generationConfig": {"temperature": self.temp}}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        r = _post("%s/v1beta/models/%s:generateContent" % (self.base, self.model), body, {"x-goog-api-key": _key(self.key_env)}, self.t)
        try:
            return "".join(x.get("text", "") for x in r["candidates"][0]["content"]["parts"]).strip()
        except (KeyError, IndexError, TypeError):
            raise ProviderError("Unexpected provider response") from None


class WithFallback:
    """Try the primary provider; on ProviderError use the fallback (before any text was produced)."""
    def __init__(self, primary, secondary):
        self.primary, self.secondary = primary, secondary

    def complete(self, messages):
        try:
            return self.primary.complete(messages)
        except ProviderError:
            return self.secondary.complete(messages)

    def stream(self, messages):
        started = False
        try:
            for piece in self.primary.stream(messages):
                started = True
                yield piece
        except ProviderError:
            if started:
                raise
            yield from self.secondary.stream(messages)


def _one(cfg, block):
    c = {**cfg, "provider": {**cfg["provider"], **block, "fallback": None}}
    from .schema import PRESET_PROVIDERS
    kinds = {"mock": Mock, "ollama": Ollama, "openai": OpenAICompatible, "openai_compatible": OpenAICompatible, "claude": Claude, "gemini": Gemini}
    kinds.update({k: OpenAICompatible for k in PRESET_PROVIDERS})
    return kinds[c["provider"]["type"]](c)


def make(cfg):
    primary = _one(cfg, {})
    fb = cfg["provider"].get("fallback")
    return WithFallback(primary, _one(cfg, fb)) if fb else primary
