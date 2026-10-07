# CustomChat

[![Installer tests](https://github.com/Harsh23Kashyap/customchat/actions/workflows/installer.yml/badge.svg)](https://github.com/Harsh23Kashyap/customchat/actions/workflows/installer.yml)

A chat app over your documents, set up with one YAML file. Answers cite their sources. Starts in offline Demo mode: no key, account or paid calls.

## Start

No Python, Git or uv needed. Open Terminal (macOS/Linux) or PowerShell (Windows) and run:

```sh
curl -fsSL https://raw.githubusercontent.com/Harsh23Kashyap/customchat/main/start.sh | sh
```

```powershell
& { $f = Join-Path ([IO.Path]::GetTempPath()) ([IO.Path]::GetRandomFileName() + '.ps1'); try { Invoke-WebRequest https://raw.githubusercontent.com/Harsh23Kashyap/customchat/main/start.ps1 -OutFile $f; & powershell -NoProfile -ExecutionPolicy Bypass -File $f } finally { Remove-Item $f -ErrorAction SilentlyContinue } }
```

The app opens in your browser (or open the printed localhost URL). Ctrl+C stops it. Run the same command in the same folder to come back to your chats. Review [start.sh](start.sh) or [start.ps1](start.ps1) before running downloaded scripts.

**Have uv?** `uvx customchat-app start`

**Prefer pip?** In an empty folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install customchat-app
.venv/bin/python -m customchat start
```

On Windows use `py -3 -m venv .venv` and `.\.venv\Scripts\python.exe`. The package is `customchat-app`; `customchat` on PyPI is a different project. Both install paths use an isolated environment, so nothing touches your system Python.

## macOS with Homebrew Python

From this repository folder, one command installs 0.1.5 in a private environment and opens the app:

```sh
python3 start_local.py
```

This handles Homebrew's `externally-managed-environment` error without sudo, global pip, activation, or `--break-system-packages`. Requires Python 3.10+ and internet for installation. It reuses `.customchat-venv`; it never deletes or resets your app, chats or keys. Ctrl+C stops the app. Run the same command from the same folder to resume.

To reopen a different existing workspace, pass its folder (the one containing `app.yaml`):

```sh
python3 start_local.py --directory /path/to/my-chat
```

Starts offline Demo for a new workspace. Existing workspaces keep their settings. Add `--no-browser` or `--port 8081` if needed. This installs the published package, not uncommitted source changes in your clone.

## Make it yours

```sh
uvx customchat-app start --directory my-chat
```

Edit `my-chat/app.yaml`, add documents, and open Configuration to pick a model, look and sources. Keep keys in environment variables or the private local store, never in YAML or Git. Add `--lock-config` for a chat-only app. See the [configuration reference](docs/DESIGN.md).

## Features

- Upload files or add web links. Reads PDF, text/code, DOCX, XLSX, PPTX, ODT and, with Tesseract, images.
- Quick, Standard and Deep answer modes.
- Saved chats with bounded history, a temporary chat mode and an optional profile.
- Themes, light/dark, logo, animated emojis and a live preview.
- Budget limits, document freshness checks and a portable app export.

Demo is the default. Choose and test a live provider in Configuration to use paid or local models.

## Prompts and code helpers

Open Configuration, then **Prompts** or **Code helpers** in the sidebar. Both are visible in Simple and Advanced. Prompts can be edited or generated for review. Code helpers generate Python, check compilation and safety, and only run when you press Try it. In offline Demo, generation returns a starter template, not model-written code.

## More

[Install options](docs/INSTALL.md) · [Hosting](docs/DEPLOY_OPTIONS.md) · [Architecture](docs/DESIGN.md) · Tests: `python -m unittest discover -s tests`

Counterpart of [Custom-Nerd](https://github.com/Harsh23Kashyap/Custom-Nerd). Harsh Kashyap, Shela Wu. Advisor: Dennis Shasha. MIT license.
