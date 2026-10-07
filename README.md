# CustomChat

Build a chat application over any evidence source from one YAML file.

CustomChat is the chat counterpart of [Custom-Nerd](https://github.com/Harsh23Kashyap/Custom-Nerd). Custom-Nerd turns a configuration into a question-answering engine for one domain. CustomChat adds the conversation layer on top: follow-up questions that remember what came before, saved chats, numbered citations, and a clean web interface. DietChat and WirelessChat are two instances of the same pattern, and both ship here as example apps.

## Deploy on Render with no configuration page

For end users who should only chat. Set `CUSTOMCHAT_CONFIG=off` and the app serves the chat only: no Configuration link, `/settings.html` and every settings, key, prompt and model endpoint return 404.

1. Fork or push this repo to GitHub.
2. In Render choose New, then Blueprint, and pick the repo. `render.yaml` sets the lock, a health check and a small disk for saved chats.
3. Configure the provider in your app YAML before deploying. The default minimal app uses offline Demo (`mock`); pasting a key alone does not switch it to AI. If you select OpenAI, paste `OPENAI_API_KEY` when Render asks. The key stays in Render's environment.
4. To use your own app file, set `APP=apps/yourapp/app.yaml`. Tune the look and sources locally first, then commit the app folder.

The lock was tested locally. A real Render deploy has not been run from here.

## One-command install and start (uv)

With uv and Git installed:

```sh
uvx --from git+https://github.com/Harsh23Kashyap/customchat.git@main customchat start
```

Creates a persistent `customchat-app` workspace in your current folder and starts offline Demo. No key, clone step or public deploy. Read the printed URL; the port can change. Ctrl+C stops it. [Install choices and validation limits](docs/INSTALL.md). No PyPI/npm package was published; do not use an unqualified registry package name yet.

## Quick start (one command)

```
python3 setup_and_run.py
```

It creates a private environment, installs what is needed, asks which AI provider you use and for its API key (typed hidden, kept only on this computer), then starts the app in your browser. Skip the key to try the offline Demo.

Windows users: run it inside WSL (Ubuntu) from the Linux home folder, not from /mnt/c. If it says the environment cannot be created, run `sudo apt install python3-venv python3-pip` first. The browser opens on the Windows side. Options: `--port 8080`, `--host 0.0.0.0`, `--no-browser`. If the port is busy it picks the next free one.

## Quick start

```bash
git clone <this repo> && cd customchat
pip install -r requirements.txt
python -m customchat run apps/minimal/app.yaml
```

Open http://127.0.0.1:8080. With no key and no model installed it runs on the built-in `mock` provider, which quotes your documents, so you can see the whole flow before choosing a model.

### Pick a model

Edit the `provider` block of your app file.

| Goal | provider block |
|---|---|
| No setup, offline demo | `type: mock` |
| Fully local | `type: ollama`, `model: llama3.2` (install [Ollama](https://ollama.com), then `ollama pull llama3.2`) |
| OpenAI | `type: openai`, `model: gpt-4o-mini`, then `export OPENAI_API_KEY=...` |
| LM Studio, vLLM, llama.cpp | `type: openai_compatible`, `base_url: http://localhost:1234/v1`, `model: ...` |

Keys are read from an environment variable you name in the file. The file never holds a key, and the loader rejects one if you try.

### Docker

```bash
docker compose up
docker compose exec ollama ollama pull llama3.2
```

## Make your own app

```bash
python -m customchat init my-chat
# edit my-chat/app.yaml, drop files into my-chat/docs
python -m customchat doctor my-chat/app.yaml    # checks model and sources
python -m customchat run my-chat/app.yaml
```

An app is one file:

```yaml
app:
  title: Policy Chat
  tagline: Ask about our HR policies.
  accent: "#0a84ff"
provider: {type: ollama, model: llama3.2}
sources:
  - {id: docs, type: local_files, label: Policies, path: docs}
  - {id: api,  type: http_json,  label: Wiki, url: "https://wiki.example.com/search?q={query}",
     results_path: results, fields: {title: title, text: snippet, url: link}}
```

Full reference: [docs/SCHEMA.md](docs/SCHEMA.md).

## What you get

- One YAML schema for the whole app: look, sources, prompts, model, memory, auth.
- Sources: local files (BM25 search, no embeddings needed), any JSON REST API, PubMed, arXiv, or your own Python function.
- Models: mock, Ollama, OpenAI, any OpenAI-compatible server.
- Context memory: each question is rewritten using earlier turns of its conversation, so "what about its cost?" still finds the right evidence. A rolling summary keeps long conversations cheap.
- Chats and conversations: a chat is a session, a conversation is a thread of thought that can continue across chats.
- Citations: answers cite numbered sources, and a claim-to-evidence check flags uncited sentences.
- Source panel with filters, BibTeX and PDF export, Shorter and Deeper regeneration.
- Pin, rename, search, delete with undo.
- Optional bearer-token login. Owner scoping in the store.
- Responsive interface with light and dark mode, keyboard shortcuts and reduced-motion support.
- `customchat init | validate | doctor | run | ask`. Tests and CI included.

## How it works

See [docs/DESIGN.md](docs/DESIGN.md) for the pipeline and how DietChat, WirelessChat and Custom-Nerd map onto it.

## Tests

```bash
python -m unittest discover -s tests
```

## Authors

Harsh Kashyap, Shela Wu. Advisor: Dennis Shasha.

## License

MIT
