# CustomChat

[![Installer tests](https://github.com/Harsh23Kashyap/customchat/actions/workflows/installer.yml/badge.svg)](https://github.com/Harsh23Kashyap/customchat/actions/workflows/installer.yml)

A chat app over your documents, configured with one YAML file. Answers cite their sources. Includes offline Demo, saved chats, themes and a local configuration page.

## Start on a fresh computer

Open **Terminal** on macOS/Linux, or **PowerShell** on Windows. Copy the command for your computer. You do not need to install Python, Git, uv or uvx first.

**macOS / Linux** (needs curl, included on macOS and many Linux systems):

```sh
curl -fsSL https://raw.githubusercontent.com/Harsh23Kashyap/customchat/main/start.sh | sh
```

**Windows PowerShell**:

```powershell
& { $f = Join-Path ([IO.Path]::GetTempPath()) ([IO.Path]::GetRandomFileName() + '.ps1'); try { Invoke-WebRequest https://raw.githubusercontent.com/Harsh23Kashyap/customchat/main/start.ps1 -OutFile $f; & powershell -NoProfile -ExecutionPolicy Bypass -File $f } finally { Remove-Item $f -ErrorAction SilentlyContinue } }
```

These scripts detect uv or download it from its official installer, obtain Python 3.12 if needed, then run CustomChat with `uv tool run` (the same operation as `uvx`). No administrator access is needed. First setup needs internet and writable disk space. Review [start.sh](start.sh) or [start.ps1](start.ps1) before running downloaded software. Network restrictions or a locked-down work computer can still prevent setup; the terminal shows the error.

The app opens in your browser. If that does not happen, open the printed localhost URL. Starts with offline Demo: no API key, account, paid AI calls or cloud hosting. Press **Ctrl+C** to stop. Run the same command from the same folder to return to your chats. Your workspace is `customchat-app` in that folder, separate from the software environment. Existing app files are not overwritten.

### Already have uv?

```sh
uvx --python 3.12 --from https://github.com/Harsh23Kashyap/customchat/archive/refs/heads/main.zip customchat start
```

This archive route needs no Git. It installs from current `main`, which can change. PyPI publication of `customchat-app` is pending; do not use `uvx customchat` or `pip install customchat`, which target another project.

### Will it conflict with my other Python packages?

`uvx` runs CustomChat and its dependencies in a **separate tool environment**. It does not install packages into your system Python or another project's virtual environment. You do not need to create a venv for the commands above. The bootstrap also removes inherited `PYTHONPATH`/`PYTHONHOME` overrides for this run. Your documents and chats live outside uv's cache.

Isolation avoids shared dependency-version conflicts, not every possible computer problem. First install still needs internet; disk permissions, antivirus, proxies and platform support can affect setup. If the usual port is busy, CustomChat chooses another and prints its URL.

### Prefer pip? Use a separate venv

With **Python 3.10+** already installed, open a new empty folder and run:

```sh
# macOS / Linux
python3 -m venv .venv
.venv/bin/python -m pip install https://github.com/Harsh23Kashyap/customchat/archive/refs/heads/main.zip
.venv/bin/python -m customchat start
```

```powershell
# Windows
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install https://github.com/Harsh23Kashyap/customchat/archive/refs/heads/main.zip
.\.venv\Scripts\python.exe -m customchat start
```

These commands use the venv directly; no activation or PowerShell activation-policy change is needed. Avoid global `pip install` for this app. To check dependencies, run the venv's Python with `-m pip check`. Use a new folder or a new venv name rather than overwriting an environment you already use.

## Configure your own app

Choose an AI provider in Configuration or your app YAML. Keep keys in environment variables/private local storage, never YAML or Git.

```sh
uvx --python 3.12 --from https://github.com/Harsh23Kashyap/customchat/archive/refs/heads/main.zip customchat start --directory my-chat
```

Edit `my-chat/app.yaml` and add documents in the app folder. [Configuration reference](docs/DESIGN.md).

For a chat-only interface, append `--lock-config` or set `CUSTOMCHAT_CONFIG=off`. Configuration pages and settings/key/model endpoints then return 404. Remove the lock on restart to configure again.

## More

- [Install choices, clone installers and validation](docs/INSTALL.md)
- [Hosting and deployment](docs/DEPLOY_OPTIONS.md) (no public deployment tested here)
- [Architecture](docs/DESIGN.md)
- Tests: `python -m unittest discover -s tests`

CustomChat is the conversation counterpart of [Custom-Nerd](https://github.com/Harsh23Kashyap/Custom-Nerd). DietChat and WirelessChat are included example apps.

## Authors and license

Harsh Kashyap, Shela Wu. Advisor: Dennis Shasha. MIT license. See [LICENSE](LICENSE).
