"""The common app schema. One YAML file describes a whole chat application.

Both DietChat (PubMed evidence, accounts, saved conversations) and WirelessChat
(arXiv/IEEE evidence, source filters, pinned chats) are instances of this schema.
"""
import copy, json, os

DEFAULTS = {
    "schema_version": 1,
    "actions": {"allow": None, "writes": True},
    "budget": {"daily_questions": 0, "user_daily_questions": 0, "daily_model_calls": 0, "spend_cap_usd": None},
    "app": {
        "id": "my-chat",
        "title": "My Chat",
        "tagline": "Ask questions. Get answers with sources.",
        "accent": "#173f35",
        "accent2": "#d7ef72",
        "footer": "",
        "examples": [],
        "language": "en",
        "theme": "auto",           # auto | light | dark
    },
    "provider": {
        "type": "mock",            # mock | ollama | openai | claude | gemini | openai_compatible
        "model": "",
        "base_url": "",            # ollama default http://localhost:11434
        "api_key_env": "",         # NAME of the env var that holds the key, never the key
        "temperature": 0.2,
        "timeout": 120,
        "fallback": None,          # optional second provider block used if the first is unreachable
    },
    "sources": [],                 # list of connector blocks, see docs/SCHEMA.md
    "retrieval": {"top_k": 6, "min_score": 0.0, "query_rewrite": False, "cache_ttl": 0},
    "prompt": {
        "system": "You answer only from the numbered evidence. Cite with [n], placing each number right after the clause it supports, not at the end of the answer. "
                  "If the evidence does not cover the question, say so in one plain sentence with no citations and do not point the reader elsewhere. "
                  "Take one clear stance that matches the evidence and do not add claims the passages do not make: no years, numbers or study details that are not written in a passage, and no remarks about limits (such as small or short) unless a passage states them. "
                  "Refer to the sources as \"the sources\" or \"the studies cited\", never \"the evidence provided\" or \"the passages\". Do not call a benefit lasting or durable, and do not describe the reader's own situation, unless a passage says so. "
                  "Report each outcome as the passage measures it: fat mass is not body weight, and use \"suggested\" or \"may\" when the passage does, not \"concluded\" or \"showed\". "
                  "Do not add causal links such as \"therefore\" that no passage makes, and write \"in some settings or groups\" instead of \"for some people\" unless a passage names who. "
                  "When a passage reports a result that cuts against the main conclusion, such as another outcome where the comparison group did better, include it.",
        "style": {"quick": "Answer in 2 to 4 sentences.",
                  "standard": "Answer clearly with short paragraphs.",
                  "deep": "Answer in depth with sections, caveats and open questions."},
        "answer_note": "",
        "revise": False,
        "no_evidence": "I could not find evidence for that in the configured sources.",
    },
    "memory": {"enabled": True, "recent_turns": 4, "summary_every": 6},
    "citations": {"required": True, "ledger": True},
    "auth": {"mode": "none", "token_env": "", "signup": True},   # none | token | accounts
    "storage": {"path": "data/customchat.db"},
    "server": {"host": "127.0.0.1", "port": 8080},
}

# Hosted services that speak the OpenAI chat format: (default base_url, default key env var).
PRESET_PROVIDERS = {
    "minimax": ("https://api.minimax.io/v1", "MINIMAX_API_KEY"),
    "mimo": ("https://api.xiaomimimo.com/v1", "MIMO_API_KEY"),
    "deepseek": ("https://api.deepseek.com", "DEEPSEEK_API_KEY"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "mistral": ("https://api.mistral.ai/v1", "MISTRAL_API_KEY"),
}
NEEDS_MODEL = {"ollama", "openai", "openai_compatible", "claude", "gemini"} | set(PRESET_PROVIDERS)
PROVIDERS = {"mock", "ollama", "openai", "openai_compatible", "claude", "gemini"} | set(PRESET_PROVIDERS)
CONNECTORS = {"local_files", "http_json", "pubmed", "arxiv", "python", "web_search", "wikipedia", "crossref", "openalex"}
AUTH_MODES = {"none", "token", "accounts"}


class ConfigError(ValueError):
    pass


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _load_env(directory):
    """Load KEY=VALUE lines from a .env next to the app file. Existing environment wins."""
    f = os.path.join(directory, ".env")
    if os.path.isfile(f):
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("\"'"))


def load(path):
    """Load and validate an app file (YAML or JSON). Returns the merged config dict."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        raise ConfigError("Cannot read %s (%s). Check the path, or create an app with: customchat init my-app" % (path, e.strerror or e))
    try:
        if path.endswith(".json"):
            raw = json.loads(text)
        else:
            import yaml
            raw = yaml.safe_load(text) or {}
    except Exception as e:
        raise ConfigError("%s is not valid %s. %s" % (path, "JSON" if path.endswith(".json") else "YAML", str(e).replace("\n", " ")[:300]))
    if not isinstance(raw, dict):
        raise ConfigError("%s must contain a mapping at the top level (app:, provider:, sources:)." % path)
    _load_env(os.path.dirname(os.path.abspath(path)))
    cfg = validate(raw)
    cfg["_dir"] = os.path.dirname(os.path.abspath(path))
    return cfg


def validate(raw):
    if not isinstance(raw, dict):
        raise ConfigError("Config must be a mapping")
    if type(raw.get("schema_version", 1)) is not int or raw.get("schema_version", 1) != 1:
        raise ConfigError("schema_version must be 1; newer schemas are not supported by this release")
    actions=raw.get('actions',{})
    if not isinstance(actions,dict) or set(actions)-{'allow','writes'}:raise ConfigError('actions needs allow and writes options')
    from .actions import REGISTRY
    if actions.get('allow') is not None and (not isinstance(actions['allow'],list) or any(x not in REGISTRY for x in actions['allow'])):raise ConfigError('actions.allow needs registered tool IDs')
    if not isinstance(actions.get('writes',True),bool):raise ConfigError('actions.writes must be true or false')
    unknown = set(raw) - set(DEFAULTS)
    if unknown:
        raise ConfigError("Unknown top-level keys: " + ", ".join(sorted(unknown)))
    cfg = _merge(DEFAULTS, raw)
    from .budget import clean as budget_clean
    try: cfg["budget"] = budget_clean(cfg["budget"])
    except ValueError as e: raise ConfigError(str(e)) from None
    p = cfg["provider"]
    if p["type"] not in PROVIDERS:
        raise ConfigError("provider.type must be one of " + ", ".join(sorted(PROVIDERS)))
    if p["type"] in NEEDS_MODEL and not p["model"]:
        raise ConfigError("provider.model is required for provider " + p["type"])
    if p["type"] in ("openai", "openai_compatible") and not p["api_key_env"]:
        if p["type"] == "openai":
            p["api_key_env"] = "OPENAI_API_KEY"
    fb = p.get("fallback")
    if fb is not None:
        if not isinstance(fb, dict) or fb.get("type") not in PROVIDERS or "api_key" in fb:
            raise ConfigError("provider.fallback needs a valid type and no api_key")
        if fb["type"] in NEEDS_MODEL and not fb.get("model"):
            raise ConfigError("provider.fallback.model is required")
    if "api_key" in p:
        raise ConfigError("Do not put keys in the app file. Use provider.api_key_env with an env var name.")
    if not isinstance(cfg["sources"], list):
        raise ConfigError("sources must be a list")
    seen = set()
    for i, s in enumerate(cfg["sources"]):
        if not isinstance(s, dict) or s.get("type") not in CONNECTORS:
            raise ConfigError("sources[%d].type must be one of %s" % (i, ", ".join(sorted(CONNECTORS))))
        if s["type"] == "local_files":
            for key in ("semantic_model", "rerank_model"):
                value = s.get(key, "")
                if not isinstance(value, str) or (value and not os.path.isabs(value)):
                    raise ConfigError("sources[%d].%s must be an absolute local model directory" % (i, key))
            if not isinstance(s.get("ocr", False), bool):
                raise ConfigError("sources[%d].ocr must be true or false" % i)
            value = s.get("refresh_interval", 30)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 86400:
                raise ConfigError("sources[%d].refresh_interval must be 0-86400 seconds" % i)
        if "read_users" in s:
            if cfg["auth"]["mode"] != "accounts" or not isinstance(s["read_users"],list) or any(not isinstance(u,str) or not u for u in s["read_users"]):
                raise ConfigError("sources[%d].read_users needs account user IDs and accounts auth" % i)
        if "document_users" in s:
            if cfg["auth"]["mode"] != "accounts" or s["type"] != "local_files" or not isinstance(s["document_users"],dict):
                raise ConfigError("sources[%d].document_users needs local files and accounts auth" % i)
            for doc,users in s["document_users"].items():
                if not isinstance(doc,str) or not doc or not isinstance(users,list) or any(not isinstance(u,str) or not u for u in users):
                    raise ConfigError("sources[%d].document_users needs document names mapped to user ID lists" % i)
        s.setdefault("id", "%s%d" % (s["type"], i))
        s.setdefault("label", s["id"])
        if not isinstance(s.get("weight", 1.0), (int, float)) or s.get("weight", 1.0) <= 0:
            raise ConfigError("sources[%d].weight must be a positive number" % i)
        if s["id"] in seen:
            raise ConfigError("Duplicate source id " + s["id"])
        seen.add(s["id"])
    if cfg["app"]["theme"] not in ("auto", "light", "dark"):
        raise ConfigError("app.theme must be auto, light or dark")
    if cfg["auth"]["mode"] not in AUTH_MODES:
        raise ConfigError("auth.mode must be none, token or accounts")
    if cfg["retrieval"]["top_k"] < 1 or cfg["retrieval"]["top_k"] > 50:
        raise ConfigError("retrieval.top_k must be 1-50")
    return cfg


def public_view(cfg):
    """The part of the config the browser may see. Never includes env names, paths or keys."""
    return {"app": cfg["app"],
            "sources": [{"id": s["id"], "label": s["label"], "type": s["type"]} for s in cfg["sources"]],
            "styles": list(cfg["prompt"]["style"]),
            "memory": cfg["memory"]["enabled"],
            "auth": cfg["auth"]["mode"],
            "provider": {"type": cfg["provider"]["type"], "model": cfg["provider"]["model"]}}
