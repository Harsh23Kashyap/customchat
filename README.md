# CustomChat

0.1.14: Selecting Prompts replaces the desktop chat preview with the full current stage editor. Prompt selection starts at the beginning of its complete text; mobile shows the editor above the stage list. Saved revise toggles match app defaults and explicit overrides. No prompt wording changed.

0.1.13: Configuration hydrates its normal controls, not a raw app-field dump. Active sources are detected by type rather than special IDs, matching presets are selected and custom looks are labeled accurately. App-file branding seeds unsaved theme values. Existing helper drafts and private key presence show in their controls; empty optional fields explicitly say not filled. Saved-state selection reflects the current model settings. No unused source is enabled automatically.

0.1.12: Nerd bundle review uses the full content width and its own static bundle preview, without an unrelated live chat preview. Review cards no longer pin and clip against the viewport top; desktop navigation has a safe inset. All settings remain in the continuous document. Imported Nerds have an explicit Edit configuration link. Configuration includes every app-file field with current values, effective branding text and saved inert code drafts or the active connector source. App-file edits are revision-checked and require restart; helper drafts never activate or run code. Model/retrieval Apply is saved to the app file for reopening. Keys remain private with saved-presence indicators.

0.1.11: Configuration scrolls continuously through every section. Prompt/code editors stay inline; navigation no longer hides neighboring sections. Nerd ZIP imports skip benign metadata, name rejected private files, and explain source-archive versus Nerd-bundle ZIPs. Empty local sources and YAML-only imports open with an empty document folder and a clear setup warning. The export button has its own Share this Nerd card.

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

### Load a shared Nerd

Open Configuration → Load and share Nerds. Drop a ZIP or app.yaml, read the readiness check, review any Python connector, then Load and run. A separate workspace opens; the current app stays intact. Keys, accounts and chat history never come with the bundle. Python runs with your local user permissions after your review. Import checks are offline, not a model/network test.

`customchat-app run app.yaml` opens the browser after the server is ready. Use `--no-browser` for servers or terminals without a desktop.

### Private workspace tools (0.1.7)

Configuration opens with one Setup and workspace page:

- **Setup** shows configuration checks without claiming live availability. Choose model/source checks, review what is sent and possible API budget use, then confirm. Failed checks show categorized, redacted diagnostics.
- **Workspace** lists imported Nerds. Open, stop or remove one after review. Removal deletes only that imported folder and its local chats. Stopped folders remain discoverable after a restart; reimport the original bundle to start a new reviewed copy.
- **Changes** keeps the last 30 model/retrieval revisions for the app owner. Compare and restore after review. Concurrent settings changes invalidate the review. Appearance, prompts and credentials are not included in this history.
- **Backup** downloads a private JSON chat archive for the owner. Restore validates the archive and adds chats instead of overwriting existing chats. It does not back up credentials, profile, uploads, feedback or model files. Chat text and evidence may contain private material: keep this archive private. It is separate from the shareable Nerd ZIP.
- **Test questions** saves up to 10 questions privately and runs them after service/cost review. Compare current and previous answers and citations. This is not an accuracy score or a correctness claim; test runs do not create chats.
- **Deploy** prepares an account/audience/cost/rollback plan only. Entered account labels, prices and permissions are not verified. No resource is created and no spending is authorized.

Imported Python connectors default to `execution: bounded`: a separate process with an environment allowlist, 20-second timeout and output limits. App write actions are disabled for imported Nerds. This is **NOT a security sandbox**. Code can still access host files and the network, and can spawn other processes; read and trust the code before allowing it. On Windows, cancellation kills the main connector process, not guaranteed child processes.

Ollama setup can cancel its own work and retry after a fresh review. OS installers or their children may still be open; close them on the host. Installed changes are not rolled back. Installer downloads restart, not resume. Model downloads show a host disk/memory review with approximate catalog sizes. The actual Ollama model location and size may differ. Retrying sends a new pull request; only Ollama decides whether partial files can be reused. No real installer or paid model call is required by the offline test suite.

0.1.7 also improves all nine prompt-generation stages and both code helpers. A short idea becomes a detailed reviewable draft with provisional assumptions, exact runtime fields/output contracts, scope examples and evidence boundaries. Generated drafts are never automatically saved; generated code is never automatically run. Unknown API endpoints remain non-operational TODOs. Static and citation-format checks do not prove truth or code safety, and the bounded process is NOT a security sandbox.

### Imported-app static review (0.1.8)

On drop, a local review shows the declared purpose, file/function counts, imports and detected Python call patterns for network, environment, files, processes and dynamic code, with file/line references. No bundle code is imported or executed, no model is called, no destination is contacted and no environment value is read. The review is not a safety verdict: unrelated functions can share these names, and aliases, dynamic calls, dependencies and runtime behavior can evade the scan. No detected pattern does not mean absent or safe. The full code and explicit consent remain before load. Bounded mode is NOT a security sandbox.

### Prompt hardening and adversarial fixtures (0.1.9)

Every model pipeline stage appends an application-owned data/instruction boundary, including when the owner has customized its prompt. Generated drafts receive the boundary from the app, not from model output. Questions, source passages, history, summaries, examples and API docs remain untrusted data. The boundary covers role spoofing, encoded/transformed text and persistent summary poisoning without blocking ordinary multilingual or security-research content by keyword. Generator/code inputs use structured JSON; JSON encoding separates structure but does not prevent semantic prompt injection.

Enabled question checks no longer silently approve an unavailable or malformed verdict, including the synchronous API. Rewrite/query/followup/summary outputs get structural checks; malformed summaries are not saved by truncation. Citation IDs remain runtime-owned. Support-check errors show that support was not verified. Static helper review adds exact imports/signatures, reflection/secret-print/env-mutation checks and limits on code executed at import time. Human review remains required before saving prompts or running code.

Tests: 13 synthetic attack families across all nine prompt constructions (117 combinations), 26 code-policy/data constructions, runtime/history/failure-path fixtures, nine AST escape samples, eight malformed-label/citation cases and four benign controls. These are deterministic construction/parser/AST checks, not measurements of live-model attack success. ChatGPT supplied a separate simulated attack review; it did not execute this backend. No finite matrix covers every possible attack.

Residual risks: models can still follow poisoned content or launder false claims; citation syntax does not prove semantic support. Optional support checks are model-dependent and off by default. Streaming can show text before final checks, so there is no confidentiality guarantee. AST checks do not isolate capabilities or enforce all endpoints; allowed Python can still access host/network resources. Bounded mode is NOT a sandbox. Prompt hardening reduces tested failure paths, not a guarantee against hallucination or jailbreaks.

### Configuration layout fixes (0.1.10)

Setup uses short, stacked status lines, with full check details behind an expandable section. Workspace tabs wrap in a consistent grid. Action links, including Open your chat, center their labels without underlines or clipped text and grow when text wraps. No provider, prompt or data behavior changes.

0.1.14: full selected prompt in the desktop preview pane; prompt switches use workspace defaults; preset navigation keeps scroll; guides remember their first display across ports; floating Save and red Reset menu; header and welcome illustration follow the palette.
