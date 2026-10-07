# CustomChat 0.1.5

- Prompts and Code helpers are now loaded and visible in the Configuration sidebar, including Simple mode.
- Connector helpers can recognize Tavily, Exa, Firecrawl and Parallel from a description (Tavily also from its key prefix), save a key privately and generate a matching standalone template without a model. Unknown services need a name or docs URL. Live tests use the built-in connector after a cost/host confirmation; edited code is never given the saved key.
- Generated Python is checked with both AST parsing and compilation. Invalid code shows line-specific errors and cannot run through Try it.
- Selected document-playground landing SVG loop is built in, with mobile layout and reduced-motion support.
- Selected linked-answers icon is bundled as the default favicon and About brand. Custom app logos still override defaults.
- Chat, About and Configuration use the same header/navigation position.
- Model provider list defaults compact. Show fewer now works without losing the selected provider.
- Local-model cards no longer play entrance transforms inside their scrolling area; Details titles remain visible.
- Subtle motion no longer accelerates looping animations to 0.12 seconds. Temporary scene animations no longer affect ordinary answer bubbles.
- Search/reference services expose inline private key setup, saved/missing state and key-free labels. Missing keys pause only the affected service. OpenAlex keys can be saved in the app instead of needing an environment variable.
- About team uses bundled photos, Harsh's LinkedIn and Dennis Shasha's NYU faculty link.
- `python3 start_local.py` creates a private environment, installs this public release and starts the app. No Homebrew system-Python override, sudo or app reset needed.

No deployment or paid model calls were made during verification. Browser layout tests run on Linux Chrome at desktop/mobile sizes. Darwin arm64/24GB model layout was tested with controlled hardware data, not on the owner's Mac. New workspaces start in offline Demo; existing workspaces keep their configuration.
