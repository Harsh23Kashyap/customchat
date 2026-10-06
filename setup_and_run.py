#!/usr/bin/env python3
"""One command setup and run for CustomChat.

    python3 setup_and_run.py            # first time: installs, asks for a key, starts the app
    python3 setup_and_run.py --port 8080 --app apps/minimal/app.yaml

What it does: makes a private virtual environment (.venv), installs the requirements, lets you pick an
AI provider and paste its API key (typed hidden, saved only on this computer in the app's data folder with
file mode 0600, never printed, never sent anywhere except to that provider), then starts the app and opens
the browser. Run it again any time; finished steps are skipped. Press Enter at the key prompt to skip it
(the offline Demo provider still works). Standard library only.
"""
import argparse, getpass, hashlib, os, shutil, socket, subprocess, sys, venv, webbrowser, threading, time, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(ROOT, ".venv")
PROVIDERS = [("openai", "OpenAI"), ("claude", "Claude (Anthropic)"), ("gemini", "Gemini"), ("deepseek", "DeepSeek"),
             ("groq", "Groq"), ("mistral", "Mistral"), ("openrouter", "OpenRouter"), ("minimax", "MiniMax"),
             ("mimo", "Xiaomi MiMo"), ("ollama", "Ollama (local, no key)")]


def say(m):
    print(m, flush=True)


def is_wsl():
    """True inside Windows Subsystem for Linux (1 or 2)."""
    try:
        return "microsoft" in open("/proc/version").read().lower()
    except OSError:
        return False


def port_free(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        return s.connect_ex((host, port)) != 0


def pick_port(want, tries=20):
    for p in range(want, want + tries):
        if port_free(p):
            return p
    sys.exit("Ports %d-%d are all busy. Close the other program or pass --port." % (want, want + tries - 1))


def req_hash(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def open_browser(url):
    """Open the default browser. Plain webbrowser.open does nothing useful inside WSL, so use the Windows side."""
    if is_wsl():
        for cmd in (["wslview", url], ["explorer.exe", url], ["cmd.exe", "/c", "start", "", url]):
            if shutil.which(cmd[0]):
                try:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True
                except OSError:
                    continue
        say("Open %s in your Windows browser." % url)
        return False
    return webbrowser.open(url)


def wait_ready(url, seconds=30):
    end = time.time() + seconds
    while time.time() < end:
        try:
            urllib.request.urlopen(url + "/api/health", timeout=1).read()
            return True
        except Exception:
            time.sleep(0.4)
    return False


def venv_python():
    return os.path.join(VENV, "Scripts" if os.name == "nt" else "bin", "python.exe" if os.name == "nt" else "python")


def ensure_env():
    if sys.version_info < (3, 10):
        sys.exit("CustomChat needs Python 3.10 or newer. You have %s." % sys.version.split()[0])
    if is_wsl() and ROOT.startswith("/mnt/"):
        say("Note: this folder is on the Windows drive (%s). It works but is slow. For speed, clone the repo inside the Linux home folder (~/customchat)." % ROOT)
    if not os.path.exists(venv_python()):
        say("Creating a private Python environment (.venv) ...")
        try:
            venv.EnvBuilder(with_pip=True).create(VENV)
        except Exception as e:
            shutil.rmtree(VENV, ignore_errors=True)
            hint = "On Ubuntu/Debian/WSL run: sudo apt install python3-venv python3-pip" if os.name != "nt" else "Reinstall Python from python.org with pip included."
            sys.exit("Could not create the environment (%s).\n%s\nThen run this again." % (e, hint))
    stamp = os.path.join(VENV, ".req-stamp")
    req = os.path.join(ROOT, "requirements.txt")
    want = req_hash(req)
    if not os.path.exists(stamp) or open(stamp).read() != want:
        say("Installing requirements ...")
        r = subprocess.run([venv_python(), "-m", "pip", "install", "--disable-pip-version-check", "-r", req], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        if r.returncode:
            say("\n".join(r.stdout.strip().splitlines()[-8:]))
            sys.exit("Could not install the requirements. Check your internet connection and run this again.")
        open(stamp, "w").write(want)



def ask_key(app):
    from_env = [k for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "DEEPSEEK_API_KEY") if os.environ.get(k)]
    if from_env:
        say("Found %s in your environment; it will be used. Skipping the key prompt." % ", ".join(from_env))
        return
    say("\nWhich AI provider will answer questions?")
    for i, (_, n) in enumerate(PROVIDERS, 1):
        say("  %d. %s" % (i, n))
    say("  Enter. Skip for now (offline Demo)")
    ch = input("Number: ").strip()
    if not ch.isdigit() or not 1 <= int(ch) <= len(PROVIDERS):
        say("Skipped. You can add a key later on the Configuration page, Model tab.")
        return
    kind, name = PROVIDERS[int(ch) - 1]
    if kind == "ollama":
        say("Ollama needs no key. Install it from ollama.com, then pick Ollama on the Model tab.")
        return
    key = getpass.getpass("Paste your %s API key (hidden): " % name).strip()
    if not key:
        say("No key entered. Skipped.")
        return
    sys.path.insert(0, ROOT)
    from customchat import secrets
    folder = os.path.join(os.path.dirname(os.path.abspath(app)), "data")
    try:
        secrets.SecretStore(folder).set(kind, key)
    except ValueError as e:
        say("That key was not accepted: %s" % e)
        return
    say("Saved on this computer only. Pick %s on the Model tab and press Test connection." % name)


def main():
    ap = argparse.ArgumentParser(description="Set up and run CustomChat")
    ap.add_argument("--app", default=os.path.join("apps", "minimal", "app.yaml"))
    ap.add_argument("--port", type=int, default=8095)
    ap.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 to reach it from other devices")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--no-key-prompt", action="store_true")
    a = ap.parse_args()
    app = a.app if os.path.isabs(a.app) else os.path.join(ROOT, a.app)
    if not os.path.exists(app):
        sys.exit("App file not found: %s" % app)
    ensure_env()
    if not a.no_key_prompt and sys.stdin.isatty():
        ask_key(app)
    port = pick_port(a.port)
    if port != a.port:
        say("Port %d is busy, using %d." % (a.port, port))
    url = "http://127.0.0.1:%d" % port
    if not a.no_browser:
        threading.Thread(target=lambda: wait_ready(url) and open_browser(url), daemon=True).start()
    say("\nStarting CustomChat at %s  (Ctrl+C to stop)" % url)
    env = dict(os.environ, PYTHONPATH=ROOT)
    try:
        sys.exit(subprocess.call([venv_python(), "-m", "customchat", "run", app, "--host", a.host, "--port", str(port)], cwd=ROOT, env=env))
    except KeyboardInterrupt:
        say("\nStopped.")


if __name__ == "__main__":
    main()
