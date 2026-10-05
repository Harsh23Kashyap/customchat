# Revision log

Each round is one change plus a check (a test, or a screenshot reviewed).

## Features
| # | Change | Check |
|---|---|---|
| F1 | `.env` file next to the app file is loaded, real environment wins | unit test |
| F2 | Provider calls retry transient errors (429, 5xx, unreachable) with backoff, never retry auth errors | unit test |
| F3 | Per-owner rate limit on ask and regenerate | code review |
| F4 | Export a whole chat as Markdown (`/api/export`) | unit test |

## UI and UX
| # | Change | Check |
|---|---|---|
| U1 | Safe markdown in answers (bold, code, lists, headings), no innerHTML | screenshot |
| U2 | Copy button on each answer | screenshot |
| U3 | Export button in the title bar | screenshot |
| U4 | Mock answers cut at a word, not mid-word | screenshot |

## Batch 2
| # | Change | Check |
|---|---|---|
| F5 | `schema/chat-app.schema.json` for editor autocomplete and validation; a test keeps it in step with the loader | unit test |
| F6 | Lint pass over Custom-Nerd (`pyflakes`): no functional bugs found statically, only unused imports and variables in main.py and helper_functions.py. Runtime bug hunt needs its dependencies and is still open | static check |

## Batch 3
| # | Change | Check |
|---|---|---|
| F7 | Streaming answers: `/api/ask-stream` (NDJSON), real token streaming for Ollama and OpenAI, word streaming for mock | unit + HTTP test, browser run |
| F8 | `app.theme: auto, light, dark` | unit test |
| F9 | Mock provider ignores earlier-turn text, parses only the evidence block | browser run |
| U5 | Answers appear as they stream, thinking dots until first token | browser run |
| U6 | Skip link, labelled conversation log region (screen readers) | markup review |
| U7 | Forced light or dark theme through CSS variables | unit test |

## Batch 4 (honest tally: about 26 features and 15 UI rounds before this batch)
Features: uploads as private evidence, delete and restore turn, per-source weight, URL dedupe, follow-up suggestions, provider fallback chain, CLI ask --json, query rewrite, support score in the claim ledger, persistent evidence cache, parallel retrieval, export-all, answer timing.
UI: related chips, delete with undo, Esc closes panels, scroll-to-bottom, upload button, print stylesheet, SVG icons, pinned indicator, matched-term highlight, date groups, topic summaries, answer time chip, "to check" detail, Stop and retry, accent contrast.

## Batch 5
Features: deep health (`/api/health?deep=1`), chat import (`/api/import`), store ping. UI: keyboard shortcuts (/, n, ?). 3 features, 1 UI. Running total: about 29 features and 29 UI rounds.

## Batch 6
Features (4): answer ratings (`/api/rate`, `/api/ratings`), usage stats (`/api/stats`), `customchat eval` (citation coverage over a question file), X-Request-Id header.
UI (6): fixed the phone layout (the page was squeezed into a zero-width column below 860px), Helpful / Not helpful buttons, textarea focus ring, phone padding, scroll-to-bottom button position, "<1s" time label.
Running total: about 33 features, 35 UI.

## Batch 7
UI (7): opaque phone drawer, dim backdrop with tap to close, dark-mode phone check of the sources sheet, skip link, live-region toasts, document title follows the chat, long-word wrapping.
Running total: about 33 features, 42 UI.

## Batch 8
Features (4): temporary chat (nothing saved, bounded history), saved profile (`/api/profile`) used in prompts, similar-question lookup (`/api/similar`), per-request profile switch.
UI (7): temporary chat toggle with amber look, profile dialog, mic dictation, "Asked before" pills, previous/next question (j/k), draggable sidebar, 3-step tour.
Running total: about 37 features, 49 UI.

## Batch 9
UI (8): re-skin to the DietChat look (forest, lime and cream palette, DM Sans and Fraunces), top toolbar with theme toggle, sidebar header with + and Temporary, chat header with status dot and style select, avatar bubbles with a Sources block inside, rounded composer with lime send button, hero with serif heading, dark mode retuned. New `app.accent2` setting.
Running total: about 37 features, 57 UI.

## Batch 10
Features (4): native Claude provider, native Gemini provider (key sent as a header, never in the URL), add a web page as a source by link (public addresses only, no private or loopback hosts, size and time limits), "Context" view showing how an answer was built.
UI (2): Context dialog, link option in the add-source prompt.
Running total: about 41 features, 59 UI.

## Batch 11
Features (4): settings API (provider, model, base URL, temperature, sources per answer, query rewrite; never keys), save / load / delete named settings states, edits limited to this computer or token holders, live provider swap without restart.
UI (5): Configuration page in CustomNerd's look (pale blue page, big white card, icon tiles, gradient buttons, segmented provider switch), link from the toolbar, view-only mode, phone layout, validation messages.
Running total: about 45 features, 64 UI.

## Batch 12
Features (6): accounts mode (`auth.mode: accounts`) with sign up, sign in, sign out, change password (signs out other devices), delete account; salted PBKDF2 passwords, hashed session tokens in HttpOnly cookies, login throttling, optional closed sign-ups (`auth.signup: false`); first account is the admin who may edit settings.
UI (5): sign-in / create-account dialog in the DietChat look, inline error messages, account menu in the toolbar with avatar initial, change-password dialog, keyboard submit and focus handling.
Running total: about 51 features, 69 UI.

## Batch 13
Features (3): PDF upload (text PDFs; uses pypdf when installed, otherwise a built-in reader), clear error for scanned PDFs, 8 MB limit with the request-size guard raised only as far as needed.
UI (2): the attach dialog accepts PDF files, per-file error toasts naming the file.
Running total: about 54 features, 71 UI.

## Batch 14
Features (8): theme engine with validated settings stored in theme.json (`/api/theme`, edits limited to people who can edit settings), colors with separate light and dark values, fonts, background and patterns, shape and depth, motion, layout and wording options, emoji and icon choices, 6 presets, export and import of a look, per-group reset.
UI (14): Configuration page rebuilt with a left menu and grouped sections, an explanation under every setting, a live preview that updates as you change things, a sticky Save look bar, light and dark toggle in the chat, font and corner scaling, bubble styles, avatar choices, pattern backgrounds, animation levels.
Running total: about 62 features, 85 UI.

## Design passes 1 and 2 (no new feature count)
UI: flat warm paper background by default (no glow circles), sidebar rebuilt (title, one primary New chat button, quiet Temporary), brand once, SVG icons everywhere (no glyphs), centered hero, quieter suggestion buttons, readable 12px disclaimer, answer row cut to sources, time, Copy, Helpful, Not helpful and a More menu, Configuration page moved to one blue accent with flat buttons, no template icon squares, active section in the left menu, larger help text, room for the save bar.
Running total: about 62 features, about 100 UI (counting each fix above as a round).

## Design pass 3
UI: answer actions are quiet text buttons instead of outlined pills, dark and phone layouts checked in screenshots. Running total unchanged in features, about 105 UI.

## Design pass 4 (from strict review)
Single 720px reading column, no avatars, flat bubbles. Sources are a chip row under the answer. Stray period after citations fixed. New-conversation moved to header. Actions on one line, 13px. Suggestions 14px.
