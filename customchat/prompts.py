"""Editable prompts for each step of the answer pipeline, saved next to the database (prompts.json).

CustomNerd lets you edit the prompt of every stage. CustomChat does the same for the stages it has. Each stage has a
built-in default, an on/off switch where the stage is optional, and a prompt you can change. Empty text means the
default. Nothing here ever holds a key.
"""
import json, os, threading

_lock = threading.Lock()
MAX_LEN = 6000

# key -> label, plain help, default prompt, optional (has an on/off switch), default on
STAGES = {
    "question_check": {
        "label": "Question check", "optional": True, "on": False,
        "help": "Decides whether a question is in scope before spending time searching. Off by default.",
        "default": ("You decide whether a question is something this assistant should answer from its sources.\n"
                    "Reply with one line. Start with VALID if the question is on topic and clear enough to search, "
                    "or INVALID followed by a colon and a short, friendly reason the reader can act on.\n"
                    "Greetings and thanks are VALID. Do not answer the question."),
    },
    "standalone": {
        "label": "Follow-up rewrite", "optional": False, "on": True,
        "help": "Turns a short follow-up like \"and for kids?\" into a question that makes sense alone.",
        "default": "Rewrite the last question so it can be understood alone. Return only the rewritten question.",
    },
    "queries": {
        "label": "Search queries", "optional": False, "on": True,
        "help": "Writes the short keyword searches sent to your sources.",
        "default": "Write up to 3 short keyword search queries for the question. One per line, no numbering.",
    },
    "relevance": {
        "label": "Relevance filter", "optional": True, "on": False,
        "help": "Asks the model which retrieved passages actually help, and drops the rest. Off by default.",
        "default": ("You check retrieved passages against a question. Each passage has a number in square brackets.\n"
                    "Reply with only the numbers of the passages that help answer the question, separated by commas. "
                    "Reply NONE if no passage helps. Be strict: a passage that only shares a word with the question does not help."),
    },
    "answer": {
        "label": "Answer", "optional": False, "on": True,
        "help": "The main instruction for writing the answer. The answer style (short, standard, detailed) is added after it.",
        "default": "",  # empty means the app file's prompt.system
    },
    "faithfulness": {
        "label": "Support check", "optional": True, "on": False,
        "help": "After the answer, checks that each claim is backed by the passages and adds a gentle note if not. Off by default.",
        "default": ("You verify an answer against its evidence. Each evidence passage has a number in square brackets.\n"
                    "If every claim in the answer is supported by the evidence, reply with exactly OK.\n"
                    "Otherwise reply with UNSUPPORTED followed by a colon and a short list of the claims that the evidence does not support. "
                    "Do not rewrite the answer."),
    },
    "revise": {
        "label": "Revise against the sources", "optional": True, "on": False,
        "help": "After the answer, rewrites it once so every statement, including words like small, short or lasting, is backed by the numbered passages. Adds one more model call. Off by default.",
        "default": ("You edit an answer so it stays inside its numbered evidence passages.\n"
                    "Rules: keep every [n] citation in place and keep the same length and structure. Delete or rewrite any statement, number, year or descriptive word "
                    "(small, short, lasting, strong) that the cited passage does not state. If a cited passage says the participants lost weight or that a comparison group did better on an outcome, "
                    "the answer must say so. Keep the direction of every comparison finding (which group did better or regained less) and keep the key numbers the passages give for the main result (effect sizes, group sizes, durations); never reduce a directional finding to a bare report that something happened. Call the sources 'the sources', never 'the evidence provided'. Reply with only the edited answer."),
    },
    "followups": {
        "label": "Follow-up suggestions", "optional": False, "on": True,
        "help": "Suggests what a curious reader might ask next.",
        "default": "Suggest 3 short follow-up questions a curious reader might ask next. One per line, no numbering.",
    },
    "summary": {
        "label": "Conversation summary", "optional": False, "on": True,
        "help": "Keeps a short running summary so later questions build on earlier ones.",
        "default": "Summarise the conversation topics in 2 sentences.",
    },
}


class PromptStore:
    def __init__(self, folder):
        self.path = os.path.join(folder, "prompts.json") if folder else ""
        self._d = None

    def _load(self):
        if self._d is None:
            self._d = {"text": {}, "on": {}}
            try:
                with open(self.path) as f:
                    d = json.load(f)
                if isinstance(d, dict):
                    self._d["text"] = {k: v for k, v in (d.get("text") or {}).items() if k in STAGES and isinstance(v, str)}
                    self._d["on"] = {k: bool(v) for k, v in (d.get("on") or {}).items() if k in STAGES}
            except (OSError, ValueError):
                pass
        return self._d

    def _write(self):
        if not self.path:
            return
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self._d, f)
        os.replace(tmp, self.path)

    def text(self, key, fallback=""):
        """The prompt in use: the saved one, else the built-in default, else the fallback (the app file's prompt)."""
        with _lock:
            t = (self._load()["text"].get(key) or "").strip()
        return t or STAGES[key]["default"] or fallback

    def enabled(self, key):
        with _lock:
            return self._load()["on"].get(key, STAGES[key]["on"])

    def view(self, fallback_answer=""):
        with _lock:
            d = self._load()
            return [{"key": k, "label": s["label"], "help": s["help"], "optional": s["optional"],
                     "on": d["on"].get(k, s["on"]), "text": d["text"].get(k, ""),
                     "default": s["default"] or fallback_answer, "custom": bool((d["text"].get(k) or "").strip())}
                    for k, s in STAGES.items()]

    def save(self, key, text=None, on=None):
        if key not in STAGES:
            raise ValueError("Unknown step")
        with _lock:
            d = self._load()
            if text is not None:
                text = str(text).strip()
                if len(text) > MAX_LEN:
                    raise ValueError("That prompt is too long (limit %d characters)" % MAX_LEN)
                if text:
                    d["text"][key] = text
                else:
                    d["text"].pop(key, None)
            if on is not None and STAGES[key]["optional"]:
                d["on"][key] = bool(on)
            self._write()

    def reset(self, key):
        with _lock:
            d = self._load(); d["text"].pop(key, None); d["on"].pop(key, None); self._write()
