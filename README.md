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

## More

[Install options](docs/INSTALL.md) · [Hosting](docs/DEPLOY_OPTIONS.md) · [Architecture](docs/DESIGN.md) · Tests: `python -m unittest discover -s tests`

Counterpart of [Custom-Nerd](https://github.com/Harsh23Kashyap/Custom-Nerd). Harsh Kashyap, Shela Wu. Advisor: Dennis Shasha. MIT license.
