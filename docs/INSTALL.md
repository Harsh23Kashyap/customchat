# One-command local start

Choose uvx as the main route. It runs a Python tool in an isolated cached environment and can obtain Python if missing. CustomChat keeps your workspace outside that cache. You need uv first; the Git route also needs Git and internet. This is a prerequisite-based choice, not a claim that most people already have uv installed.

## Available now, no package registry publication

After installing uv from its official instructions, run:

```sh
uvx --from git+https://github.com/Harsh23Kashyap/customchat.git@main customchat start
```

This creates `customchat-app` in your current directory and starts offline Demo on localhost. It opens a browser where supported. Read the printed URL; 8080 may be busy. Press Ctrl+C to stop. Run the same command again to keep using the same workspace. Existing app files are never overwritten; an existing directory without app.yaml is rejected rather than changed.

```sh
# Different workspace, no browser launch, chat-only interface:
uvx --from git+https://github.com/Harsh23Kashyap/customchat.git@main customchat start --directory my-chat --no-browser --lock-config
# Keep the command installed on PATH instead:
uv tool install git+https://github.com/Harsh23Kashyap/customchat.git@main
customchat start
```

`main` is a moving source, not a release pin. For reproducibility, replace `main` with a verified commit or tag. This installs software from the repo, not from PyPI. Do not run an unqualified `uvx customchat` yet: no registry release was made here and ownership/name availability has not been verified.

The default is Demo, with local passages and no key or model call. For AI, configure your workspace's app.yaml provider or use the unlocked Configuration page. Keys stay in named environment variables/private local storage, never YAML or git. `--lock-config` hides configuration for this run; remove it on restart to configure. No public hosting, account creation or cloud spend is involved.

## Other routes

| Route | What users need | Judgment |
|---|---|---|
| uvx / uv tool | uv; internet; Git for current source command | Best balance for this Python app: isolated install, reusable CLI, no custom bootstrap |
| pipx | pipx and a compatible Python; Git for source command | Good fallback if already installed; similar isolation |
| npx wrapper | Node/npm plus Python or a bootstrap download | Adds a second runtime and npm wrapper maintenance; no benefit for this app's internals |
| curl installer | shell/curl plus maintained installer | Convenient but adds trusted remote shell execution and platform/install/update logic; not built |
| Docker | Docker engine/Desktop, image/source | Useful deployment isolation, heavier for first local chat; not tested here |

For pipx users:

```sh
pipx run --spec git+https://github.com/Harsh23Kashyap/customchat.git@main customchat start
```

The pipx route follows its documented source-install syntax but was not executed here. uv was present in the test environment; uv installation on a bare OS and automatic Python download were not exercised. We do not have reliable measurements of what tools target users already have installed. Existing `python3 setup_and_run.py` remains the fallback for users who have Python and a clone.

## Validation and release readiness

A wheel and source distribution were built locally. In a new home/workspace and empty uv cache, the wheel installed independently of the repo and served health 200, mock provider, a Demo answer with 2 local citations, and 404 for settings in locked mode. Packaged web assets and Demo template were inspected. API-verified; browser pixels not inspected for this install path. Existing source tests plus launcher regressions pass. Linux only; real Windows/macOS/WSL, Docker and public hosting remain unverified.

Packaging is prepared, not published. Before a short PyPI command: verify package-name ownership/availability, choose a release version, test the release artifact, then get approval to publish. No PyPI/npm credentials or publishing were used.

## Sources checked October 7, 2026

- uv tool isolation, Git sources, persistent installation: https://docs.astral.sh/uv/guides/tools/
- uv prerequisites/install methods: https://docs.astral.sh/uv/getting-started/installation/
- managed Python downloads: https://docs.astral.sh/uv/guides/install-python/
- pipx source/temporary execution: https://pipx.pypa.io/latest/how-to/run-scripts.html
- npx/npm cached package execution: https://docs.npmjs.com/cli/v12/commands/npm-exec/
- Docker Windows prerequisites: https://docs.docker.com/desktop/setup/install/windows-install/
- packaged runtime data: https://setuptools.pypa.io/en/latest/userguide/datafiles.html
- build backend/metadata: https://packaging.python.org/en/latest/tutorials/packaging-projects/?highlight=distributing
