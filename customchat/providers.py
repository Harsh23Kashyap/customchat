"""LLM providers. All use only the standard library.

mock               deterministic, no network (tests, demos, first run)
ollama             local model via http://localhost:11434
openai             OpenAI chat completions, key from an env var
openai_compatible  any OpenAI-style server (LM Studio, vLLM, llama.cpp) via base_url
"""
import json, os, re, urllib.request, urllib.error


class ProviderError(RuntimeError):
    pass


def _post(url, payload, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise ProviderError("Provider returned HTTP %d" % e.code) from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ProviderError("Provider unreachable: %s" % getattr(e, "reason", e)) from None


class Mock:
    """Extractive stand-in. Quotes the first sentence of each evidence block with its citation."""
    def __init__(self, cfg): self.cfg = cfg

    def complete(self, messages):
        user = messages[-1]["content"]
        blocks = re.findall(r"\[(\d+)\]\s*(.+?)(?=\n\[\d+\]|\Z)", user, flags=re.S)
        if not blocks:
            return "No evidence was provided."
        out = []
        for n, text in blocks[:3]:
            body = re.sub(r"^.*?\([^)]*\)\.\s*", "", text.strip().replace("\n", " "), count=1)
            first = re.split(r"(?<=[.!?])\s", body)[0]
            out.append("%s [%s]" % (first[:240], n))
        return " ".join(out)


class Ollama:
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


class OpenAICompatible:
    def __init__(self, cfg):
        p = cfg["provider"]
        self.base = (p["base_url"] or "https://api.openai.com/v1").rstrip("/")
        self.model, self.t, self.temp = p["model"], p["timeout"], p["temperature"]
        self.key_env = p["api_key_env"]

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


def make(cfg):
    t = cfg["provider"]["type"]
    return {"mock": Mock, "ollama": Ollama, "openai": OpenAICompatible,
            "openai_compatible": OpenAICompatible}[t](cfg)
