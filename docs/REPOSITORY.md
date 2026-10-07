# Repository map

- `customchat/`: packaged Python runtime, connectors, providers and web UI.
- `customchat/templates/`: bundled Demo workspace used by installed quickstart.
- `apps/`: example app YAML and sample documents (DietChat, WirelessChat, minimal).
- `schema/`: configuration schema for editors.
- `scripts/`: shared installer implementation.
- `install.sh`, `install.ps1`: OS entry scripts. Kept at root for easy download/use.
- `setup_and_run.py`: compatible older Python setup route; kept at root because docs/tests import it.
- `tests/`: unit/regression tests and installer scenario harness.
- `.github/workflows/`: repository CI.
- `deploy/`: publishing script and deployment templates. No automatic deployment from this repo.
- `docs/`: design, install, deployment and validation notes.
- `docs/ui-audit/`: screenshot context for motion review.
- Root `pyproject.toml`, requirements, Docker/Compose/Render files: packaging and hosting entry points.

Runtime entry points and hosting files stay in their expected locations. Do not move them without updating consumers and rerunning tests. Generated builds, environments and local app data are not source files and should remain ignored.
