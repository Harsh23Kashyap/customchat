# Changelog

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
