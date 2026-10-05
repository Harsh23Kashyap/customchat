"""Look at this computer and suggest local models (for Ollama).

Logic in plain words
  1. Find how much memory a model can use (the "budget"):
       discrete NVIDIA GPU        -> its video memory (VRAM)
       Apple Silicon (unified)    -> 65% of RAM (the system and apps need the rest)
       CPU only                   -> RAM minus 4 GB, then 60% of that (the rest is for the computer itself)
  2. On CPU only, models above about 10 GB are left out: they run too slowly to chat with.
  3. A model needs its file size plus about 1.5 GB for the conversation (context) and runtime.
     It must fit in 85% of the budget. Anything bigger would swap to disk and crawl.
  4. Pick three from what fits:
       Best quality   -> the largest model that fits
       Balanced       -> the largest that needs at most 60% of the budget (leaves room for long chats)
       Fast and light -> the largest that needs at most 30% of the budget
     If two picks are the same model, the next smaller one fills the slot.
  5. Speed (rough): fully on GPU = fast; Apple Silicon = good; CPU only = slow, and it shrinks with model size.
Sizes are the approximate download size of the default 4-bit build in the Ollama library.
"""
import json, os, platform, re, shutil, subprocess, urllib.request

# (tag, display name, billions of parameters, approximate GB of the default download, note)
CATALOG = [
    ("llama3.2:1b", "Llama 3.2 1B", 1.2, 1.3, "Tiny and quick, for simple questions"),
    ("qwen3:1.7b", "Qwen3 1.7B", 1.7, 1.4, "Small, good for its size"),
    ("llama3.2:3b", "Llama 3.2 3B", 3.2, 2.0, "Small, good all-rounder"),
    ("gemma3:4b", "Gemma 3 4B", 4.3, 3.3, "Good writing, reads images"),
    ("qwen3:4b", "Qwen3 4B", 4.0, 2.6, "Strong reasoning for 4B"),
    ("qwen2.5:7b", "Qwen2.5 7B", 7.6, 4.7, "Solid for documents and code"),
    ("qwen3:8b", "Qwen3 8B", 8.2, 5.2, "Strong all-rounder"),
    ("gemma3:12b", "Gemma 3 12B", 12.2, 8.1, "High quality writing"),
    ("qwen3:14b", "Qwen3 14B", 14.8, 9.3, "Very capable"),
    ("gemma3:27b", "Gemma 3 27B", 27.4, 17.0, "Near top quality on one GPU"),
    ("qwen3:32b", "Qwen3 32B", 32.8, 20.0, "Top quality for most people"),
    ("llama3.3:70b", "Llama 3.3 70B", 70.6, 43.0, "Large, needs a big machine"),
]
OVERHEAD_GB = 1.5
FIT = 0.85


def _run(cmd, t=4):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=t).stdout.strip()
    except Exception:
        return ""


def detect():
    """Facts about this computer. Nothing leaves it."""
    sysname = platform.system()
    hw = {"os": sysname, "arch": platform.machine(), "cpu": platform.processor() or "", "cores": os.cpu_count() or 1,
          "ram_gb": 0.0, "gpu": "", "vram_gb": 0.0, "apple_silicon": False}
    try:
        if sysname == "Linux":
            for line in open("/proc/meminfo"):
                if line.startswith("MemTotal:"):
                    hw["ram_gb"] = int(line.split()[1]) / 1024 / 1024
                    break
            m = re.search(r"model name\s*:\s*(.+)", open("/proc/cpuinfo").read())
            if m: hw["cpu"] = m.group(1).strip()
        elif sysname == "Darwin":
            hw["ram_gb"] = int(_run(["sysctl", "-n", "hw.memsize"]) or 0) / 1024 ** 3
            hw["cpu"] = _run(["sysctl", "-n", "machdep.cpu.brand_string"]) or hw["cpu"]
            hw["apple_silicon"] = platform.machine() == "arm64"
        elif sysname == "Windows":
            out = _run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"], 8)
            hw["ram_gb"] = int(out or 0) / 1024 ** 3
    except (OSError, ValueError):
        pass
    if shutil.which("nvidia-smi"):
        out = _run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
        best = (0.0, "")
        for ln in out.splitlines():
            parts = [p.strip() for p in ln.split(",")]
            try:
                v = float(parts[1]) / 1024
            except (IndexError, ValueError):
                continue
            if v > best[0]: best = (v, parts[0])
        hw["vram_gb"], hw["gpu"] = round(best[0], 1), best[1]
    hw["ram_gb"] = round(hw["ram_gb"], 1)
    return hw


def installed(base="http://localhost:11434"):
    try:
        with urllib.request.urlopen(base.rstrip("/") + "/api/tags", timeout=2) as r:
            return sorted(m["name"] for m in json.load(r).get("models", []))
    except Exception:
        return None  # Ollama is not running or not installed


def budget(hw):
    """(gb, mode, plain explanation)"""
    if hw.get("vram_gb", 0) >= 4:
        return hw["vram_gb"], "gpu", "Discrete GPU: models run in its %.0f GB of video memory." % hw["vram_gb"]
    if hw.get("apple_silicon"):
        b = hw["ram_gb"] * 0.65
        return b, "unified", "Apple Silicon shares memory with the GPU: %.0f GB of %.0f GB RAM (65%%) can hold a model." % (b, hw["ram_gb"])
    b = max(0.0, (hw.get("ram_gb", 0) - 4)) * 0.6
    return b, "cpu", "CPU only: %.0f GB RAM minus 4 GB for the system, times 0.6 = %.1f GB for a model." % (hw.get("ram_gb", 0), b)


def _speed(mode, gb, hw):
    if mode == "gpu": return "fast"
    if mode == "unified": return "good" if gb < 12 else "ok"
    cores = hw.get("cores", 4)
    tps = max(0.5, cores * 1.1 / max(gb, 0.5) * 2)  # rough tokens per second
    return "ok" if tps >= 8 else ("slow" if tps >= 3 else "very slow")


def recommend(hw, have=None):
    b, mode, why = budget(hw)
    limit = b * FIT
    fits = [m for m in CATALOG if m[3] + OVERHEAD_GB <= limit and (mode != "cpu" or m[3] <= 10)]
    fits.sort(key=lambda m: m[2])
    out = {"budget_gb": round(b, 1), "mode": mode, "budget_why": why, "limit_gb": round(limit, 1), "picks": [], "note": ""}
    if not fits:
        out["note"] = "This computer is short on memory for local models. Use a hosted provider, or try llama3.2:1b if you only need simple answers."
        small = CATALOG[0]
        fits = [small] if b >= 2 else []
        if not fits:
            return out

    def pick(frac):
        ok = [m for m in fits if (m[3] + OVERHEAD_GB) <= b * frac]
        return ok[-1] if ok else fits[0]
    chosen = []
    for label, frac, desc in (("Best quality", FIT, "The largest model that fits"), ("Balanced", 0.60, "Leaves room for long chats and other apps"), ("Fast and light", 0.30, "Replies quickly, lowest memory")):
        m = pick(frac)
        if m in [c[0] for c in chosen]:
            smaller = [x for x in fits if x[2] < min(c[0][2] for c in chosen)]
            if not smaller: continue
            m = smaller[-1]
        chosen.append((m, label, desc))
    for m, label, desc in chosen:
        need = m[3] + OVERHEAD_GB
        out["picks"].append({
            "tag": m[0], "name": m[1], "label": label, "why": desc, "note": m[4], "params_b": m[2], "download_gb": m[3],
            "needs_gb": round(need, 1), "uses_pct": round(100 * need / b) if b else 0, "speed": _speed(mode, m[3], hw),
            "installed": bool(have) and any(h == m[0] or h.split(":")[0] + ":latest" == m[0] for h in have), "pull": "ollama pull " + m[0]})
    return out


def report(base="http://localhost:11434"):
    hw = detect(); have = installed(base)
    r = recommend(hw, have)
    return {"hardware": hw, "installed": have, "recommendation": r, "ollama_running": have is not None}
