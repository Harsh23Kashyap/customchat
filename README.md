# CustomChat

[![Installer tests](https://github.com/Harsh23Kashyap/customchat/actions/workflows/installer.yml/badge.svg)](https://github.com/Harsh23Kashyap/customchat/actions/workflows/installer.yml)

A chat app over your documents, configured with one YAML file. Follow-ups keep context; answers link to numbered sources. Includes offline Demo, saved chats, themes and a local configuration page.

## ⚡ Start with uv

With [uv](https://docs.astral.sh/uv/getting-started/installation/), Git and internet:

```sh
uvx --from git+https://github.com/Harsh23Kashyap/customchat.git@main customchat start
```

Creates `customchat-app` in your current folder and starts offline Demo. Open the printed URL; a busy port changes it. Ctrl+C stops the app. Rerun to keep your workspace. No PyPI/npm package has been published: use this source command, not `uvx customchat`.

## 📦 Install without uv or Python

Download or clone this repo, open a terminal in its folder, then:

```sh
# Linux / macOS
sh install.sh
```

```powershell
# Windows PowerShell
./install.ps1
```

Downloads uv, Python and dependencies when missing. Keeps its private environment in `~/.customchat/install`, preserves your app files and skips ready setup. First setup needs internet. Review scripts before running downloaded software. [Installer options, tested scope and limits](docs/INSTALL.md).

## 🛠 Manual setup

With Python3.10+ and this repository:

```sh
python -m venv .venv
# Linux / macOS
. .venv/bin/activate
# Windows instead: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m customchat run apps/minimal/app.yaml
```

Demo uses local passages, no API key and no paid model calls. Choose an AI provider in Configuration or your app YAML. Keep keys in environment variables/private local storage, never YAML or Git.

## 🌱 Your own app

```sh
customchat init my-chat
customchat doctor my-chat/app.yaml
customchat run my-chat/app.yaml
```

When using the manual route, prefix these commands with `python -m` instead of the `customchat` executable. Edit `app.yaml` and add documents in the app folder. [Configuration reference](docs/DESIGN.md).

For a chat-only interface, use `customchat start --lock-config` or set `CUSTOMCHAT_CONFIG=off`. Configuration pages and settings/key/model endpoints then return 404. Remove the lock on restart to configure again.

## 📚 More

- [Install choices and validation](docs/INSTALL.md)
- [Hosting and deployment](docs/DEPLOY_OPTIONS.md) (no public deployment tested here)
- [Architecture](docs/DESIGN.md)
- Tests: `python -m unittest discover -s tests`

CustomChat is the conversation counterpart of [Custom-Nerd](https://github.com/Harsh23Kashyap/Custom-Nerd). DietChat and WirelessChat are included example apps.

## Authors and license

Harsh Kashyap, Shela Wu. Advisor: Dennis Shasha. MIT license. See [LICENSE](LICENSE).
