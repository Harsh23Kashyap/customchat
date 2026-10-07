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

## Installer entry scripts

From a clone or downloaded repository, run:

```sh
# Linux or macOS
sh install.sh
```

```powershell
# Windows PowerShell
./install.ps1
```

The scripts download uv from its official installer only if missing, then obtain Python3.12 and install CustomChat in a private environment. No sudo or Git is needed for this route. Internet is required for first setup. Default workspace: `customchat-app`; installer state: `~/.customchat/install`. Existing workspace files stay untouched. A ready environment is skipped; an incomplete or broken installer-owned environment is rebuilt. Busy ports fall forward and active healthy runs are reused. A concurrent installer exits with a clear error.

Use `--directory my-chat`, `--no-browser`, `--lock-config`, or `--prepare-only` as needed. `--offline` reuses an already prepared environment/cache; it cannot create missing downloads. The source is pinned in `scripts/install.py`, not a registry release. Installer scripts execute downloaded software: review them before running. Network, disk, permission and platform failures are reported, not a guarantee that every machine works.

Linux: eight scenarios repeated ten times passed. A separate isolated absent-uv/Python bootstrap downloaded both and passed health, Demo citations and config lock. The GitHub Actions workflow repeats the scenario matrix ten times on ubuntu, macOS and Windows; all3OS passed in https://github.com/Harsh23Kashyap/customchat/actions/runs/37570556695 (240scenario checks). The macOS startup stall was Python HTTPServer reverse DNS; the server now avoids that unused lookup, with a regression test. Its entry-script step uses preinstalled uv, so it does not prove absent-uv bootstrap on those OSes.

## Other routes

| Route | What users need | Judgment |
|---|---|---|
| uvx / uv tool | uv; internet; Git for current source command | Best balance for this Python app: isolated install, reusable CLI, no custom bootstrap |
| pipx | pipx and a compatible Python; Git for source command | Good fallback if already installed; similar isolation |
| npx wrapper | Node/npm plus Python or a bootstrap download | Adds a second runtime and npm wrapper maintenance; no benefit for this app's internals |
| curl installer | shell/curl plus maintained installer | OS entry scripts above provide this bootstrap; review downloaded code |
| Docker | Docker engine/Desktop, image/source | Useful deployment isolation, heavier for first local chat; not tested here |

For pipx users:

```sh
pipx run --spec git+https://github.com/Harsh23Kashyap/customchat.git@main customchat start
```

The pipx route follows its documented source-install syntax but was not executed here. The original uvx test used existing uv; a later isolated Linux installer test downloaded uv and managed Python. We do not have reliable measurements of what tools target users already have installed. Existing `python3 setup_and_run.py` remains the fallback for users who have Python and a clone.

## Validation and release readiness

A wheel and source distribution were built locally. In a new home/workspace and empty uv cache, the wheel installed independently of the repo and served health 200, mock provider, a Demo answer with 2 local citations, and 404 for settings in locked mode. The Git source command was also executed with a new home and empty uv cache, resolving commit eecc832bf57821692d1cceddf04f995624090d77, and passed the same health/chat/lock checks. Packaged web assets and Demo template were inspected. API-verified; browser pixels not inspected for this install path. Existing source tests plus launcher regressions pass. The original uvx test was Linux only. The later installer matrix passed on real Ubuntu/macOS/Windows runners, each with uv preinstalled; WSL, Docker and public hosting remain unverified.

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
