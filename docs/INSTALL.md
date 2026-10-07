# One-command local start

Choose uvx as the main route. It runs a Python tool in an isolated cached environment and can obtain Python if missing. CustomChat keeps your workspace outside that cache. You need uv first; the Git route also needs Git and internet. This is a prerequisite-based choice, not a claim that most people already have uv installed.

## Published package and one-command start

CustomChat 0.1.0 is published at https://pypi.org/project/customchat-app/ . With uv already installed:

```sh
uvx customchat-app start
# Pin a release:
uvx customchat-app@0.1.0 start
# Choose a workspace and hide configuration:
uvx customchat-app start --directory my-chat --no-browser --lock-config
```

For a fresh computer, use the README's OS-specific one-command bootstrap. It downloads uv and managed Python if absent, then runs the pinned package with `uv tool run`, the same operation as uvx. Git is not needed. The app starts offline Demo, opens or prints its local URL and preserves your workspace outside the tool environment. Ctrl+C stops it. API keys are only needed if you choose a live AI provider.

Do not use `uvx customchat` or `pip install customchat`: that distribution belongs to another project.

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

Version 0.1.0 passed build and six artifact/bootstrap acceptance jobs on Ubuntu/macOS/Windows with Python 3.10/3.12: https://github.com/Harsh23Kashyap/customchat/actions/runs/37623429389 . The published package was then installed and run in a fresh Linux home/cache with no uv/Python/Git available, passing health 200 and cited Demo. Publication completed after account verification and token-free trusted-publisher setup.

## Sources checked October 7, 2026

- uv tool isolation, Git sources, persistent installation: https://docs.astral.sh/uv/guides/tools/
- uv prerequisites/install methods: https://docs.astral.sh/uv/getting-started/installation/
- managed Python downloads: https://docs.astral.sh/uv/guides/install-python/
- pipx source/temporary execution: https://pipx.pypa.io/latest/how-to/run-scripts.html
- npx/npm cached package execution: https://docs.npmjs.com/cli/v12/commands/npm-exec/
- Docker Windows prerequisites: https://docs.docker.com/desktop/setup/install/windows-install/
- packaged runtime data: https://setuptools.pypa.io/en/latest/userguide/datafiles.html
- build backend/metadata: https://packaging.python.org/en/latest/tutorials/packaging-projects/?highlight=distributing

## Fresh-computer bootstrap (October 7 update)

The README now uses `start.sh` / `start.ps1`: they detect or install uv, obtain managed Python 3.12, and invoke `uv tool run` (uvx) in an isolated tool environment. The archive source does not require Git. This differs from the older `install.sh` route above, which uses an installer-owned venv. Both keep user workspaces outside the software environment.

`tests/start_bootstrap.py` runs the new bootstrap in a disposable home and empty cache, with uv, uvx, Python and Git absent from PATH, then checks health 200 and a Demo answer with citations. Linux passed with the wheel, real remote archive and published PyPI package. The wheel bootstrap also passed on macOS/Windows in the six-job release workflow. The remote PyPI bootstrap was executed locally on Linux only. The pip venv artifact test also passed dependency checks, offline Demo and isolation from a deliberately broken host yaml package.
