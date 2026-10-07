# 0.1.6

- Prompts and Code helpers use a stage list and full right-pane editor. Visual settings keep their live preview. Phone editors appear below the list.
- `run` opens the browser after health readiness; `--no-browser` is available.
- Chat model badge refreshes when configuration/state changes in another tab or the chat regains focus.
- Configuration identifies the loaded Nerd, model and active YAML sources. Answer prompt uses its app YAML, not a generic override.
- Smaller source-key Save button; Get a key link removed; Remove key stays available.
- Model memory details are a budget/reserve/fit graph, with zero-budget handling. Card lists remain scrollable without clipped first cards.
- Local owner can drag/drop a Nerd ZIP or YAML, review fields/prerequisites/code, and run it in a separate workspace. No implicit code execution during review, no keys/chats import. Network and model readiness are not claimed from offline checks.
- Export preflight names omitted keys/accounts/chats/models and missing prerequisites. Local Python connector is included for explicit review.

Security notes: local-only importer, traversal/hidden/private file and size checks, unknown auth rejected, write actions disabled in imported apps, secrets removed from child process environment. Imported Python is not a sandbox; review it carefully. Hosting/deploy remains a separate design, not an automatic cloud launch.

## Opt-in Ollama setup

Configuration can detect and start a local Ollama service, or download and open the fixed official installer after a separate review and explicit confirmation. Only the local owner may use setup. Windows/macOS require completing OS installer prompts on the host; Linux falls back to official terminal steps if local permissions prevent non-interactive setup. CustomChat does not collect a sudo password, create a cloud account, or download a model during installation. Readiness is reported only when the local service responds. Unit and UI flows were tested with mocked installation, not a real cross-platform installer matrix.
