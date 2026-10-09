# Changelog

## 0.1.16 - 2026-10-09

0.1.16 adds resizable settings columns and the private keys-only NewsNerd starter.

## Workspace layout
- Drag either divider to resize navigation, settings, and the preview or prompt/code editor. Widths stay in this browser. Arrow keys adjust; Home or double-click resets. Minimum widths keep each column usable.
- Hide/show chat preview reclaims the space and remembers the choice. Prompt/code editors remain available.
- Styled scrollbars match the workspace and chat. Compact/mobile layouts retain their existing flow without resize handles.

## Private custom source keys
- Sources and APIs now has private credential controls for native HTTP sources with declared header-to-environment mappings. Save/remove works without restarting or contacting the source; the field clears after saving and only presence is reported.
- Saved keys are bound to the source ID, environment label, and configured URL. Destination changes require a new saved key. Keys stay out of YAML, exports, prompts and status responses.
- Credential-bearing sources require HTTPS, reject redirects and fail before a request when a key is missing. Imported Python connector permissions are unchanged: bounded mode is NOT a security sandbox and does not receive API keys.
- HTTP article mapping handles a single author string and reports rejected or malformed responses instead of treating them as empty news.

## NewsNerd starter
Attached `newsnerd-ready-keys.zip` contains the active native NewsAPI connector, `gpt-4o-mini` provider configuration, all nine filled prompt texts, two filled inert code-helper reference drafts, wording, light/dark colors, retrieval, memory and budgets. No real keys, private saved looks, test-question history or chats are included.

1. Start CustomChat 0.1.16: `uvx --from customchat-app==0.1.16 customchat-app start`
2. Configuration > Load and share Nerds: choose the attached ZIP, review, Load and run, then Edit NewsNerd Ready configuration.
3. Model and key: save your OpenAI key. Sources and APIs > Custom source credentials: save your NewsAPI key.
4. Open the imported app's Chat and ask short keywords such as `AI regulation`.

This is configured for local development/testing, not production. NewsAPI Developer has a 24-hour delay and quota. Hosted OpenAI calls cost money when you ask questions. App question/model-call limits are not a dollar billing meter. Live news/model services were not called in verification; no correctness or live-key-validity claim is made. The preview conversation is a visual sample, not a generated news response.

Sources: https://newsapi.org/docs/authentication ; https://newsapi.org/docs/endpoints/everything ; https://newsapi.org/pricing ; https://developers.openai.com/api/docs/models/gpt-4o-mini


### 0.1.16 verification
- Source: 498 tests, 498 passed, no skips. Fresh installed wheel: 498 tests, 496 passed, 2 optional-dependency skips.
- Package checks, isolated install/demo/alias/conflict acceptance, and source/installed-wheel browser checks passed. Desktop/mobile screenshots inspected.
- Only fake service responses were used; no paid API calls.

## 0.1.15 - 2026-10-09

First release published to both GitHub and PyPI with the accepted configuration
work. 0.1.14 was published on GitHub only; its PyPI publish was cancelled, so
PyPI stayed on 0.1.13. 0.1.15 supersedes 0.1.14 everywhere.

Configuration page:

- Selected prompt and code-helper editors open in a right-side pane on desktop
  and inline on mobile, with compact helper descriptions.
- Source and additional fields save to the app file with revision checks.
  Reload shows the saved values, pending restart is labeled, and export is
  blocked until restart so a ZIP cannot contain stale settings.
- Stale concurrent edits are rejected instead of overwriting newer saves.
- Optional fields show a single "(not filled)" marker that tracks typing,
  clearing, image upload, save and reload.
- Provider fallback gets normal typed controls (enable, provider, model, base
  URL, environment variable name, temperature, timeout) with validation.
  Structured and empty values hydrate and persist; invalid blocks are rejected
  without overwriting the saved file.
- Numeric fields reject empty input instead of silently saving 0, and multiline
  text is preserved exactly.
- Articles-style JSON is rejected with a routing hint to Code helpers > Search
  connector > Match a real response instead of being imported or executed.
- Appearance Save is labeled to its scope, reset stays in the menu, and mobile
  layouts no longer clip the prompt placeholder or generation actions.

Emoji:

- 80 bundled static images (Google Noto Color Emoji, SIL OFL 1.1) render the
  supported picker and demo emoji without network fonts. Custom emoji still use
  native fonts.

Verification:

- 486 tests, 484 pass, 2 optional skips, on the source tree and on a fresh
  installed wheel.
- Independent retest of the exact change composition passed, including helper
  panes, offline emoji, blank-field markers, JSON routing, source save and
  restart-guarded export, fallback controls, and numeric/multiline boundaries.

## 0.1.14 - 2026-10-08

Configuration autofill acceptance: hydrated normal controls for the full app
schema, filled NewsNerd demo workspace, and end-to-end save/reload coverage.
Published on GitHub only.

## 0.1.13 - 2026-10-07

Hydrated normal configuration controls.
