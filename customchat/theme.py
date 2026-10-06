"""Look and feel, fully configurable. The theme is plain data (colours, fonts, background, emojis,
motion, layout). It is validated here so a bad value can never break the page, and saved next to the database."""
import json, os, re

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
COLOR_KEYS = ["brand", "accent", "bg", "surface", "ink", "muted", "line", "sidebar", "bot", "you", "danger"]

LIGHT = {"brand": "#173f35", "accent": "#d7ef72", "bg": "#f8f4e9", "surface": "#fffdf7", "ink": "#17231f", "muted": "#63736c",
         "line": "#d9e1dc", "sidebar": "#e9eee5", "bot": "#f2f3eb", "you": "#efe9d8", "danger": "#a8493c"}
DARK = {"brand": "#8fd0b4", "accent": "#d7ef72", "bg": "#0d1613", "surface": "#121d19", "ink": "#e8efe9", "muted": "#93a39b",
        "line": "#25352f", "sidebar": "#16231e", "bot": "#1a2823", "you": "#2d3a33", "danger": "#e08a7d"}

FONTS = {  # id -> (css stack, google family or None)
    "dm-sans": ('"DM Sans",system-ui,sans-serif', "DM+Sans:wght@400;500;700;800"),
    "inter": ('"Inter",system-ui,sans-serif', "Inter:wght@400;500;700"),
    "system": ('-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif', None),
    "georgia": ("Georgia,'Times New Roman',serif", None),
    "fraunces": ('"Fraunces",Georgia,serif', "Fraunces:wght@600;700"),
    "playfair": ('"Playfair Display",Georgia,serif', "Playfair+Display:wght@500;700"),
    "lora": ('"Lora",Georgia,serif', "Lora:wght@400;600"),
    "space-grotesk": ('"Space Grotesk",system-ui,sans-serif', "Space+Grotesk:wght@400;500;700"),
    "nunito": ('"Nunito",system-ui,sans-serif', "Nunito:wght@400;600;800"),
    "poppins": ('"Poppins",system-ui,sans-serif', "Poppins:wght@400;500;600"),
    "jetbrains": ('"JetBrains Mono",ui-monospace,monospace', "JetBrains+Mono:wght@400;600"),
    "mono": ("ui-monospace,SFMono-Regular,Menlo,Consolas,monospace", None),
}

ENUMS = {
    "mode": ["light", "dark", "auto"],
    "bg_style": ["soft", "solid", "gradient", "image"],
    "pattern": ["none", "dots", "grid", "lines", "diagonal", "checker", "waves", "plus"],
    "motion": ["full", "subtle", "none"],
    "entrance": ["fade", "slide", "pop", "none"],
    "bubble": ["soft", "flat", "outline"],
    "density": ["compact", "cozy", "roomy"],
    "sidebar": ["left", "right", "hidden"],
    "chat_width": ["narrow", "normal", "wide", "full"],
    "avatars": ["show", "hide"],
    "you_align": ["right", "left"],
    "shadow": ["none", "soft", "strong"],
    "composer": ["inline", "floating"],
    "toolbar": ["show", "hide"],
}

DEFAULT = {
    "mode": "auto", "light": dict(LIGHT), "dark": dict(DARK),
    "bg_style": "solid", "bg_color2": "#e6f0d0", "bg_angle": 160, "bg_image": "",
    "pattern": "none", "pattern_opacity": 12, "pattern_size": 24, "pattern_color": "",
    "font": "dm-sans", "heading_font": "fraunces", "custom_font": "", "font_size": 100, "line_height": 150,
    "radius": 100, "density": "cozy", "shadow": "soft",
    "emoji_bot": "", "emoji_you": "", "emoji_hero": "", "emoji_send": "", "emoji_attach": "", "emoji_temp": "",
    "motion": "full", "entrance": "fade", "speed": 100, "hover_lift": True,
    "sidebar": "left", "sidebar_width": 250, "chat_width": "normal", "avatars": "hide", "bubble": "flat",
    "logo": "", "txt_title": "", "txt_tagline": "", "txt_examples": "", "txt_placeholder": "", "txt_footer": "", "txt_disclaimer": "", "txt_hint": "", "txt_sidebar": "",
    "you_align": "right", "composer": "inline", "toolbar": "show", "sources_panel": True,
}

RANGES = {"bg_angle": (0, 360), "pattern_opacity": (0, 60), "pattern_size": (8, 80), "font_size": (80, 140), "line_height": (120, 200),
          "radius": (0, 160), "speed": (40, 250), "sidebar_width": (200, 460)}
BOOLS = ["hover_lift", "sources_panel"]
COLORLIKE = ["bg_color2", "pattern_color"]


def _emoji(v):
    v = str(v or "").strip()
    return v[:8] if not re.search(r"[<>&\"']", v) else ""


def clean(raw):
    """Merge `raw` over the defaults; anything invalid falls back to the default value."""
    raw = raw if isinstance(raw, dict) else {}
    t = json.loads(json.dumps(DEFAULT))
    for mode, base in (("light", LIGHT), ("dark", DARK)):
        got = raw.get(mode) if isinstance(raw.get(mode), dict) else {}
        for k in COLOR_KEYS:
            v = got.get(k)
            t[mode][k] = v.lower() if isinstance(v, str) and HEX.match(v) else base[k]
    for k, opts in ENUMS.items():
        if raw.get(k) in opts:
            t[k] = raw[k]
    for k, (lo, hi) in RANGES.items():
        try:
            t[k] = max(lo, min(hi, int(float(raw.get(k, t[k])))))
        except (TypeError, ValueError):
            pass
    for k in BOOLS:
        if k in raw:
            t[k] = bool(raw[k])
    for k in COLORLIKE:
        v = raw.get(k)
        if k == "pattern_color" and v == "":
            t[k] = ""
        elif isinstance(v, str) and HEX.match(v):
            t[k] = v.lower()
    for k in ("font", "heading_font"):
        if raw.get(k) in FONTS or raw.get(k) == "custom":
            t[k] = raw[k]
    cf = str(raw.get("custom_font") or "").strip()
    t["custom_font"] = cf if re.fullmatch(r"[A-Za-z0-9 \-]{2,40}", cf) else ""
    img = str(raw.get("bg_image") or "").strip()
    t["bg_image"] = img if re.match(r"^https://[^\s\"'()<>]{4,300}$", img) else ""
    lg = str(raw.get("logo") or "")
    t["logo"] = lg if re.fullmatch(r"data:image/png;base64,[A-Za-z0-9+/=]{20,300000}", lg) else ""
    for k in ("emoji_bot", "emoji_you", "emoji_hero", "emoji_send", "emoji_attach", "emoji_temp"):
        t[k] = _emoji(raw.get(k))
    limits = {"txt_title": 60, "txt_tagline": 160, "txt_examples": 600, "txt_placeholder": 80, "txt_footer": 200, "txt_disclaimer": 120, "txt_hint": 120, "txt_sidebar": 40}
    for k, n in limits.items():
        v = str(raw.get(k) or "").replace("\r", "").strip()[:n]
        t[k] = v if k == "txt_examples" else v.replace("\n", " ")
    return t


class ThemeStore:
    def __init__(self, folder):
        self.path = os.path.join(folder, "theme.json")
        self.value = DEFAULT_CLEAN()
        try:
            with open(self.path, encoding="utf-8") as f:
                self.value = clean(json.load(f))
        except (OSError, ValueError):
            pass

    def save(self, raw):
        self.value = clean(raw)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.value, f, indent=1)
        return self.value

    def reset(self):
        return self.save({})


def DEFAULT_CLEAN():
    return clean({})


def meta():
    """Option lists for the Configuration page."""
    return {"fonts": {k: v[0] for k, v in FONTS.items()}, "enums": ENUMS, "ranges": RANGES, "default": DEFAULT_CLEAN()}
