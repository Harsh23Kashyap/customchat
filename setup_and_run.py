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
import argparse, getpass, os, subprocess, sys, venv, webbrowser, threading, time

ROOT = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(ROOT, ".venv")
PROVIDERS = [("openai", "OpenAI"), ("claude", "Claude (Anthropic)"), ("gemini", "Gemini"), ("deepseek", "DeepSeek"),
             ("groq", "Groq"), ("mistral", "Mistral"), ("openrouter", "OpenRouter"), ("minimax", "MiniMax"),
             ("mimo", "Xiaomi MiMo"), ("ollama", "Ollama (local, no key)")]


def say(m):
    print(m, flush=True)


def venv_python():
    return os.path.join(VENV, "Scripts" if os.name == "nt" else "bin", "python.exe" if os.name == "nt" else "python")


def ensure_env():
    if sys.version_info < (3, 9):
        sys.exit("CustomChat needs Python 3.9 or newer. You have %s." % sys.version.split()[0])
    if not os.path.exists(venv_python()):
        say("Creating a private Python environment (.venv) ...")
        venv.EnvBuilder(with_pip=True).create(VENV)
    stamp = os.path.join(VENV, ".req-stamp")
    req = os.path.join(ROOT, "requirements.txt")
    want = str(os.path.getmtime(req))
    if not os.path.exists(stamp) or open(stamp).read() != want:
        say("Installing requirements ...")
        r = subprocess.run([venv_python(), "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "-r", req])
        if r.returncode:
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
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--no-key-prompt", action="store_true")
    a = ap.parse_args()
    app = a.app if os.path.isabs(a.app) else os.path.join(ROOT, a.app)
    if not os.path.exists(app):
        sys.exit("App file not found: %s" % app)
    ensure_env()
    if not a.no_key_prompt and sys.stdin.isatty():
        ask_key(app)
    url = "http://127.0.0.1:%d" % a.port
    if not a.no_browser:
        threading.Thread(target=lambda: (time.sleep(2.5), webbrowser.open(url)), daemon=True).start()
    say("\nStarting CustomChat at %s  (Ctrl+C to stop)" % url)
    env = dict(os.environ, PYTHONPATH=ROOT)
    try:
        sys.exit(subprocess.call([venv_python(), "-m", "customchat", "run", app, "--port", str(a.port)], cwd=ROOT, env=env))
    except KeyboardInterrupt:
        say("\nStopped.")


if __name__ == "__main__":
    main()
