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

## Design pass 5 (second strict review)
Darker action/chip text, user bubble contrast, one-column alignment, 8/12 rhythm, send button uses the brand color (no lime), focus rings, 44px touch targets on phone, header title ellipsis. Config: DM Sans, sentence-case buttons, segmented Chat/Configuration control, bottom room above the save bar, no em dash in the title.

## Design pass 6
Custom-styled dropdowns (keyboard and screen-reader friendly) on chat and config pages. Eight extra presets behind a Load more button. 220ms preset-switch animation. Save-bar clearance in config.

## Backend pass 1: providers and failure handling
Added MiniMax, Xiaomi MiMo, DeepSeek, Groq, OpenRouter, Mistral as one-line provider types (default address and key variable built in; MiniMax and MiMo addresses checked against their docs). Retry now uses exponential backoff with jitter, honors Retry-After, retries only timeouts, 408/425/429/5xx, and never retries 400/401/403/404. Streams retry before the first token. Plain-language error messages per HTTP code. Test file fixed: 37 tests after the old main block were never running; all 53 now run and pass.

## Backend pass 2 and config pass 7: keys, model picker, connection test, declutter
Local secret store (secrets.json, mode 0600, never returned by any API, never in exports or the repo). Per-provider API key field (masked), model picker that lists the provider's real models (Claude, Gemini, Ollama, any OpenAI-style server) with a type-a-name fallback, Test connection with plain pass/fail reasons. Live preview switches to a model card on the Model tab and shows which tab it follows. Wording, Colors, Background, Fonts, Icons, Layout regrouped with short sections and collapsed More options; color rows fixed (no overflow). Per-section Save and Reset. Emoji placeholders and defaults are blank.

## Backend pass 3 and config pass 8: provider marks, local model advisor
Provider chips: five up front (OpenAI, Claude, Gemini, DeepSeek, Ollama) and Load more for the rest, each with its own monogram and brand-ish color (original marks, not logos). New hardware.py reads RAM, CPU, NVIDIA VRAM, Apple Silicon; computes a memory budget (VRAM, 65% of RAM on Apple Silicon, or 60% of RAM minus 4 GB on CPU), requires file size plus 1.5 GB to fit in 85% of it, and picks Best quality, Balanced and Fast and light from a catalog of Ollama tags (tags checked on ollama.com). Simple and Technical views, installed detection, pull command. Tests added.

## Config pass 9: logo, progressive disclosure, font-bundled presets
Logo upload with in-browser plain-background removal and feathered edges (shrunk to 256px PNG, validated on the server as a PNG data URL, shown in the top bar and the welcome screen). Every tab shows only essentials; the rest sits under a collapsed More section. Presets show their font pairing and always set both fonts, so one click gives colors and type.

## Pass 10 (config)
- One shape language: 12px controls, 16px cards, no mixed round/rect boxes on the Model tab.
- Model tab shows a status card (provider, model, key, test result) instead of the sample chat.
- Real provider logos (10 SVGs from the MIT-licensed @lobehub/icons-static-svg package, bundled in web/logos). Not official brand-kit files; marks stay trademarks of their owners.
- Ollama cards: green/blue/red fit with a plain reason, numbers behind Details, Download button pulling through the local Ollama API with a progress bar (POST/GET /api/ollama/pull, admin only, tag validated).
- Logo control: Original / After blending / In your app tiles, updating live on every toggle and slider.
- Preview shows the hero and a doughnut chart card.
- Preview audit: every control changes the preview except those that only act in another state (gradient colour and angle only with a gradient, image link only with Image, pattern colour only with a pattern, Font "custom"). Emoji for the welcome screen needs a recheck.

## Setup script
- `python3 setup_and_run.py`: private .venv, installs requirements, optional provider and hidden key prompt (saved 0600 in the app data folder, never printed), starts the app and opens the browser. Tested from a clean copy: venv, install, server answered 200.

## Pass 11: prompts and code helpers
- Eight prompt steps (question check, standalone, searches, relevance, answer, support check, follow-ups, summary), each readable, editable, resettable and writable with the connected model. Three are optional and off by default.
- Code helpers for a search connector and query cleaning. Generated code is checked statically and never run.
- Not yet tested with a real model. Tested with a fake provider and the offline template.

## Pass 12: editor, panels, search keys
- Code box is CodeMirror 6 (vendored, MIT) with line numbers, highlighting and error markers on the flagged line.
- Prompts and Code tabs replace the chat preview with helper panels: try a prompt on a sample (needs a real model), diff against default, length estimate; live search keys with test buttons.
- Model tab right panel gains "How to get your key" guides. Links and claims come from each provider's own pages (5 Oct 2026). DeepSeek and OpenRouter have no steps because the key pages were not confirmed.
- Optional web search (Tavily, Exa, Firecrawl, Parallel) with a `web_search` source type that fails safe, and a research option for code generation. Tested against a local fake server, not the real services.

## Pass 13: ready-made sources
- Wikipedia, Crossref and OpenAlex connectors join PubMed and arXiv. No key needed; tick them in the Code panel.
- Response shapes checked live. OpenAlex search is paid per its docs and reads `OPENALEX_API_KEY` from the environment.
- Tested with mocked responses. Each source fails safe.

## Pass 14: waiting indicator
- The waiting dots now show elapsed time ("1.6s"), an idea from the Loading State on beautifului.dev (MIT, Shane Levine). No code was copied; it is our own plain-JS version.

## Pass 15 (from B2's critique of a34b03ee79)
- Answer, actions and Related now share one left edge. Related sits closer to the actions.
- One 2px focus ring.
- Code editor shows a placeholder and is short until code exists. Write, Check and Copy stay on one row.
- Config pages keep room under the sticky save bar when scrolled to the end.
- Runtime checks, no paid calls: bad code is blocked before it runs; a valid-looking loop is stopped at 20s with a plain message; web search refuses to enable without a saved key; prompt test says plainly when there is no model; a 2500-character question is rejected.

## Pass 16 (from B2's critique of 5e0f98f9f0)
- Actions row has equal spacing (the More button lost its left padding by mistake). One focus ring on the composer, no halo. Disclaimer is 12px with more contrast. Related items underline on hover and have a 44px tap area on phones.
- Code editor placeholder sits further from line 1. The gap between helper cards is 20px. Diagram text is larger. Save bar is narrower and sits under the left column, so it no longer covers the key rows.
- Try it clears the old safety result first, and says "It ran for 20 seconds without finishing, so it was stopped." The web search toggle says to save a key first.
- Phone check: viewport 390 CSS px at 2x gives a 780px image. The earlier 728px file came from a layout slightly wider than the screen; the new one has no sideways overflow.

## Pass 17 (from B2's critique of a28a6583d2)
- Empty code editor has no highlight band across line 1. Try it keeps a white button on hover with a darker border (no pale fill that looks disabled).
- Save bar text is darker (contrast 7.5:1 on white). Footer disclaimer measures 6.2:1.
- Related items end with an arrow. Phone tap targets measured 44px high.

## Pass 18 (from B2's critique of ded5c7bcd0)
- Save bar slides away when there are no unsaved changes, so it never covers content. It comes back, one line, when something changes.
- Checkbox no longer gets the blue input box on focus; keyboard focus shows a 2px ring.
- Try it has a stronger outline and a visible hover state.
- Phone header: the Standard select is narrower so more of the chat title shows.

## Pass 19 (from B2's critique of 3e870eac8f)
- Phone header: Standard select is no longer cut. It keeps a 92px minimum and the chat title takes the leftover room.
- Save bar is opaque and as wide as the form column. It is a floating bar, so it can sit over content mid-page; it hides when nothing is unsaved.

## Pass 20 (from B2's critique of c2b37aee68)
- The save bar is now a docked strip at the bottom of the window with reserved space under the page. Content ends at its edge, so it never covers a field at any scroll position. Hidden when nothing is unsaved.
- App name and Welcome line show a hint ("Blank uses the app default").
- Preview chat opens scrolled to the newest message, so the last bubble is not cut.
- Preset font label shows one name when the body and heading fonts are the same.

## Pass 21 (from B2's critique of f0075158c8)
- Text fields trim stray spaces on leaving the field, so the hint shows again (App name).
- Demo: no model picker, no Refresh list, no Base URL. Base URL shows only for Ollama and Other.
- "1 model found" grammar. Temperature and Sources values are dark text, not link blue.
- Cloud model suggestions now link their sources (OpenAI and Google model pages, 5 Oct 2026); the "newest stable" wording is gone.
- Memory advice is labelled a rough estimate.

## Pass 22 (from B2's critique of a4f5ee5f7f)
- Demo: the whole model row and label are hidden, so no gap before Test connection. Status reads "Built-in demo, no model needed".
- Logo Original / After blending / In your app captions stay hidden until a picture is chosen or one is set.
- Side menu hover is an underline, not a pill, so only the section you are in is highlighted.
- Suggested model names checked on the vendors' pages on 6 Oct 2026: OpenAI lists GPT-6.1 Sol (gpt-6.1-sol) as "near-Astra performance for complex work at a lower cost"; Google lists Gemini 3.8 Flash (gemini-3.8-flash) as "our most intelligent Flash model". Descriptions now use their wording.

## Pass 23 (from B2's critique of 941c8f524c)
- Vendor blurbs follow the official wording: GPT-6.1 Sol "near-Astra performance at a lower cost, for complex coding, computer use and professional work" (developers.openai.com/api/docs/models/gpt-6.1-sol); Gemini 3.8 Flash "our most intelligent Flash model" (ai.google.dev/gemini-api/docs/models/gemini-3.8-flash).
- Dark mode: the user's message bubble had almost no contrast (dark grey text on dark grey). Fixed. Answer action buttons lost their pill borders in dark to match light.
- Disabled logo options now have a muted label.

## Pass 24 (from B2's critique of 5e99f8a02c)
- Test connection is disabled until a key exists, with "Save a key first, then test."
- The missing-key message names the variable (OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY) and tells people to paste a key under Model.
- More space under the Model heading and helper line.
- Full dark chat shot taken (sidebar, answer, composer).

## Pass 25 (first real-model run)
- A real OpenAI test run found two bugs the fake provider could not: (1) the OPENAI_API_KEY environment variable was never read for the openai provider (only a saved key worked); (2) newer OpenAI models (gpt-5, gpt-6, o-series) reject a custom temperature with HTTP 400. Both fixed.
- Real results: model list (141 models, includes gpt-6.1-sol, gpt-6-luna), Test connection "Works" on gpt-6-luna, and a full cited answer through the chat.

## Pass 26 (from B2's critique of passes 24-25)
- Related questions stack one per line, wrap, and align to the answer edge instead of running off the right side.
- Citation markers [1] [2] have a small gap.
- Three real agents run end to end on gpt-6-luna: Docs Chat (local files), Acme Support (help-center files with a support prompt), Nutrition Evidence (live PubMed). Results in the report to B2.

## Pass 27
- Copy / Helpful / More row text now starts at the same left edge as the Related questions (the first button lost its 9px inset).
- Default answer prompt asks for each [n] right after the clause it supports. Real run (gpt-6-luna) now places [1] after the first paragraph's claims and [2] after the follow-up paragraph; per-clause placement is not guaranteed by the model.
- Run logs with sources for three real apps were produced for review (no key in them).
- Sources under an answer now list only what the answer cites (real models). A refusal cites nothing, so it shows no source chips. Found by reviewing run logs: "capital of France" used to show two unrelated chips.
- Default prompt: a refusal is one plain sentence with no citations and no referral; one clear stance that matches the passages.
- Checked by hand against the full PubMed abstracts: HOMA-IR down 0.31 (PMID 35371260), 14 adults and 3 weeks (PMID 35871650), 5 weeks and 6-hour window (PMID 29754952).

## Pass 28
- Citations: ranges and lists like [2, 4] or [2-5] become [2][4]; sources used are renumbered 1, 2, 3 in order of use; a space is forced before a citation that follows punctuation. The sources list matches the numbers in the text.
- Prompt: no years, numbers or study details that are not written in a passage.
- Checked against full abstracts: 39 participants / 6 weeks 20h-fasting 4h-eating / HOMA-IR down (PMID 39193706), four studies / 355 participants / similar fasting insulin (PMID 34391831), 8-week trial of 40 older adults (5:2 fasting). All present in the passages.
- Sidebar rows: inactive rows are plain text by design; pin/edit/delete show on the active or hovered row.

## Pass 29
- Inline code is 0.9em and baseline aligned.
- Sidebar: chats with the same title show the time (hidden on hover or when active).
- Related questions are generated from the retrieved passages, so they can be answered.
- Code check, not only prompt: a year after "a/an/the" that no passage or source record contains is removed. Years that appear in the answers (2021, 2022) come from the PubMed record's year field (PMID 34633860 is 2021, 35371260 and 35871650 are 2022), not model memory.
- Adjacent citations are sorted and spaced: "[4] [1] [2] [3]" becomes "[1] [2] [3] [4]".
- New app option prompt.answer_note: a fixed line added to every answer that has sources. The Nutrition app sets "General research information, not medical advice." so it no longer depends on the model.

## Pass 30
- Related questions no longer show literal backticks or bold marks (plain text only).
- Related prompt now asks for new angles the answer does not already cover.
- Run logs list PMID and year for every source (29754952 = 2018, 34633860 = 2021, 35371260 = 2022, 35871650 = 2022, 39193706 = 2025, 34391831 = 2021).

## Pass 31
- Default prompt: no remarks about limits (small, short) unless a passage states them; refer to "the sources" or "the studies cited", never "the evidence provided"; include a result that cuts against the main conclusion.
- Related questions ask about the topic, not the wording of an example.
- Related hover shown (underline) in the Acme shot.
- Source chips: long titles are cut to one line with an ellipsis and the number stays on one line (they used to wrap into tall pills with "[ 2 ]" split across lines). Full title on hover.

## Pass 32
- Source chips show up to two lines of title (rounded 16px), so a counter-result title like "...but does not improve insulin sensitivity" stays readable.
- Citation spacing: one space before a marker, none between a marker and the punctuation after it.
- Prompt: no "lasting" or "durable" unless a passage says so; do not describe the reader's own situation.

## Pass 33
- New optional step "Revise against the sources" (prompt.revise: true, or the Prompts tab; off by default). One more model call rewrites the answer so every statement and descriptive word (small, short, lasting) is in the cited passages, and it must mention weight loss or a better-performing comparison group when a passage says so. On the Nutrition app the closing line now reads "lasted three and five weeks and involved specific groups" instead of "relatively small or short".
- New deterministic check, no model: every number in a sentence (digits or number words such as "fourteen") must appear in a passage that sentence cites, or in the question. Otherwise the sentence is flagged "to check". Unit test added. Found no false flags on the Docs, Acme and Nutrition runs except the question's own "45 days", which is now allowed.
- Relevance and faithfulness layers compared on Acme and Nutrition: no measurable gain, so they stay optional and off.

## Pass 34
- Phone (390px), found from a real screenshot: brand title no longer cut to "Acm..." (model badge hidden under 480px; it is still in Configuration); source chip had an empty second line; Related arrow sat far right when a question wrapped. Related rows are now 44px tall with the arrow right after the text.
- Keyboard focus ring on Related items has room around the text.

## Pass 35
- Phone: Related rows have thin dividers (no curved ends); the footer keeps "Not a substitute for professional advice" on phones; the "General research information, not medical advice." line is part of the answer.
- Bug found while checking the number check: since pass 32 put a space before each citation ("sentence. [1] Next"), the claim splitter stopped splitting, so a whole answer was one "claim" and the support check was weak. Splitter fixed, test added.
- Number check now also accepts a year from the source record (PubMed year) for the cited source.
- Code replaces "the evidence provided / the passages" with "the cited sources" (verbs fixed: "do not show").
- Rubric, 3 runs per question, 2 Nutrition questions, revise OFF vs ON: words small/short/lasting/relatively/"evidence provided": 12 vs 1; number flags 4 vs 1 (the flags were years and a mis-split claim, both fixed above). Small n, one model.

## Pass 36
- Real bug: only the first 1200 characters of each passage were sent to the model. The PubMed abstract for PMID 40749646 is 1558 characters, so the conclusion (more fat mass regain in the calorie-restriction group, IF "may be superior for weight maintenance") was cut. Answers then said "the supplied summary does not give enough follow-up results" or "the passage does not state which group regained less". Limit raised to 3000 characters. After the fix, 6 of 6 runs state the regain direction (before: 0 of 6 stated it fully).
- Revise prompt keeps the direction of every comparison and the key numbers of the main result. ON runs now carry SMD -0.21, 4-week -4.87 vs -2.82 kg, n = 50 and 46.
- Quote check: PMID 35565749 abstract ends "These findings suggest that IF may be superior to CCR for weight loss in some respects."

## Pass 37
- Base prompt: report outcomes as the passage measures them (fat mass is not body weight) and use "suggested/may" when the passage does. In 2 test runs without the revise step, 1 said "less fat-mass regain" and 1 still said "less regain", so the prompt alone is not reliable; the revise step is the stronger fix.
- Truncation mechanism shown without a model (pass37_evidence): in PMID 40749646, "fat mass" is absent from the first 1200 characters and present in the full 1558. Passages of 2130 and 2061 characters also lost their final conclusions under the old limit.
- Read in full: PMID 41458802 (2025 review: similar effectiveness and safety to calorie restriction, better adherence for some, lacks long-term studies) and PMID 34728336 (2021 review: studies in middle-aged and older adults mostly short and small). Claims citing them in the 6 runs match.

## Pass 38
- Records with no text or no title are dropped before the prompt and chips (guard in retrieval). The "None/None/None" PMID:34086376 line in an earlier log came from my own script printing a record it had not retrieved in that run; it was a real 2021 record in the run that cited it. The guard is a safeguard, not a fix for a seen defect.
- New check, no model: a sentence that says "regain" without "fat" while its cited passage says "fat mass regain" is flagged "to check" (field vague_regain). Both no-revise runs after the pass 37 prompt trip it.
- Note: the old 1200-character limit cut the endings of several passages (about 3 of 4 abstracts in one run), including conclusions such as "both IF and CRD are effective short-term weight loss strategies". This affected every answer, not only one question.

## Pass 39
- A sentence flagged as vague about regain is now corrected: one rewrite using the revise prompt plus the flagged sentence, kept only if the flag is gone (else the original stays). Real before/after from a run without the revise step: "participants in both groups regained some weight" became "both groups regained weight, but the CRD group regained more fat mass; the study reported that IF may better prevent weight regain".
- Base prompt: no causal "therefore" the passages do not make; "in some settings or groups" instead of "for some people" unless a passage names who.
- Tests added for the empty-record guard (Engine.usable) and for the regain check.

## Pass 40
- `correct()` keeps a rewrite only if it has no vague_regain flag and no new number or year not in the cited passage; otherwise the original stays.
- Tests: test_rewrite_kept_only_if_flag_is_gone, test_rewrite_rejected_if_it_adds_a_number.
- Counts (8 runs, one question, one model): 5 flagged before correction, 0 flagged after.

## Pass 41
- Touch screens: row actions (pin, rename, delete) always visible, buttons 36px (were 22px), rows 48px, no duplicate pin icon on pinned rows, time label hidden.
- Desktop hover shot checked: actions show on the hovered row and the active row.

## Pass 42
- Pinned rows show a filled pin; the pin button has "Pin/Unpin <title>" labels and aria-pressed. Rename and Delete have labels too.
- Rows have a title attribute (full title on hover). Delete toast now reads "Chat deleted. Undo".
- Phone drawer has a close button; backdrop tap closes it (both tested by script).
- Touch targets measured by DOM box: row actions 44x44, rows 60 tall, close 44x44.
- Refund ranking log: 8 phrasings, refunds.md#0 top-1 in 8 of 8 (refund_rank2.txt, scores). Only one passage returned per question, so there is no top-3 to log.

## Pass 43
- PubMed search: full questions returned 0 papers because PubMed ANDs every word ("does", "beat"). Now question words are dropped, and if nothing matches the last word is dropped (down to 2 words). After the change the type 2 diabetes question returns 4 papers (before: 0).
- 34086376 read in full: it is a rat study. New ledger flag `animal_unmarked`: a sentence citing a passage about rats/mice that never says so is flagged, and the existing rewrite step is asked to say it. Tests: 2 (flagged, marked passes). In 6 live weight-loss runs the rat paper was no longer retrieved (keyword search changed the result set), so the live effect is untested.
- Tests: PubMedQuery (2), AnimalFlag (2). Phone checks: pin/unpin state, rename vs delete taps, undo toast.

## Pass 44
- Phone drawer: New chat now closes it (it stayed open over the new chat). Tapping Undo no longer closes the drawer, so the restored row is visible. The delete toast lasts 6 seconds (code, setTimeout 6000; not timed in a browser).
- Test with the real 34086376 passage text and a fake model reply: the unmarked sentence is flagged, the rewrite request says "rats or mice", a rewrite that still hides the animal is rejected.
- Nutrition prompt (dietchat example config, not deployed): the opening sentence must match the evidence; "Yes" or "Probably" only if every cited source agrees, otherwise "Possibly" or "Mixed"; effects reported with weight loss say they may partly come from it. Insulin question, 5 runs each: before 2 Probably, 1 Yes, 2 "may"; after 3 Possibly, 1 Mixed, 1 Probably.
- Cited claims for PMIDs 40533200, 32060194, 39458528, 39732588 checked against the passage text.
- Known limit: a bare follow-up with no topic words ("And what about a monthly plan?") ranks the wrong document first when asked in a fresh chat. In a chat after a refund question it ranks refunds first. Not rewritten.

## Pass 45
- Ledger: `weak_cites` lists, for a sentence with 2 or more cites, each cited passage that shares under 34 percent of the claim's content words (logged, not blocking; a coarse word check). `unhedged_lead`: a lead of Yes or Probably on evidence that mentions weight, with no other sentence mentioning weight, is flagged and goes through the same keep-only-if-clean rewrite. 4 tests.
- Sentence splitter now splits after a bold lead ("...**" then a space).
- Undo script on 4 uniquely titled chats, one pinned, a middle one deleted: same position, pinned state and API list (ids, titles, pinned) after undo; a second tap on the toast found it gone.
- Insulin question, 5 runs: all 5 leads hedged (Possibly x4, Mixed x1). 35871650 was never retrieved. The code guard was not exercised live (the model hedged every time); it is covered by unit tests only.

## Pass 46
- Nutrition prompt: name the population and the intervention as the passage does (for example obese adults, fasting-based strategies) and do not widen a finding. 39458528 defines FBS as "fasting-based strategies" and covers obese adults; earlier answers wrote "fasting showed no superior long-term outcomes".
- test_pdf: the "EOF marker not found" line is a pypdf warning about the hand-made PDF in the test; it is now silenced in the test.
- Undo checked by exact text on the phone: deleting the pinned chat, and deleting the open chat, then undo, restored the row, pin state and the first user message and the first and last 80 characters of the answer.
- Live animal run with the real model: 34086376 forced to rank first in retrieval. It was cited in 1 of 8 runs; in that run the sentence said "The animal study in rats ...". The guard did not fire live.

## Pass 47
- Undo of an open chat now reopens it (before: it stayed on "New chat" with nothing selected). Undo of a chat that is not open leaves the open chat selected; that is intended, so undoing a delete never moves the reader away from what they are reading.
- Tested on a 4-turn chat (8 messages): same chat id after undo, same title and pinned state, 0 of 8 messages differ.
- test_pdf now asserts the exact extracted text, so silencing the pypdf warning hides nothing.
- Weight-loss and long-term question after the population rule, 3 runs: the long-term sentence named "obese adults" and "fasting-based strategies" in 3 of 3.

## Pass 48
- Toast sits 16 px above the composer on phone and desktop (measured: toast bottom 647, composer top 663 on phone; 615 and 631 on desktop; overlap false). It follows the composer height through a CSS variable.
- Citations that the model puts inside the closing bold ("**lead. [1]**") are moved outside it. New ledger flag `uncited` for sentences of 6 or more words with no citation (refusals excepted).
- PubMed: the relaxed search made several requests at once and NCBI answered 429 (HTTPError, no evidence). Added a 0.4 s pause between relaxed tries and a short wait and retry on 429.
- Live animal run with a question that retrieves 34086376 naturally (it names the study's topic): cited in 5 of 5 runs, and every lead says "in male rats". The guard was not needed live. Four more natural questions about fitness and fasting did not retrieve it at all.
- Undo log now hashes every message text (8 of 8 identical, phone and desktop).

## Pass 49
- Rewrite is kept when it has fewer flags than the original (before: only when it had none). Live finding: in an animal-study run, 3 sentences did not name rats and the all-or-nothing rule kept them.
- The uncited flag now also goes through the rewrite ("every sentence that states a finding needs its own [n]"). Live check, 3 runs of the long-term question: leads cited in 3 of 3 (before the change: lead uncited in 2 of 3 saved ledgers); uncited sentences left: 0, 6 and 0 (of 8, 15 and 10).
- NCBI 429: unit test forces two 429 answers then success (3 calls) and checks that a third 429 raises.
- Clause check of "compared fasting and calorie-restricted approaches alongside exercise" against 40749646: supported; "does not establish a general long-term advantage" understates the passage, which says the IF approach "may be superior for weight maintenance" at 6 and 12 months.

## Pass 50
- A sentence that carries a number but no [n] is now dropped from the answer after the rewrite (kept in `dropped`). 3 live runs of the weight question: uncited sentences with numbers 0, 0, 0; uncited sentences 0 of 7, 0 of 9, 0 of 7.
- Toast is centred on the chat panel, not the window. Measured centre x vs panel centre x: 675 vs 675 at 1100 px wide, 845 vs 845 at 1440 px wide (offset 0; before the change the window centre was 550 at 1100 px, 125 px left of the panel).
- Bug: "New chat" left the last open row shaded, because the list was not redrawn. It redraws now. Check: with New chat open and the mouse on a row the row is plain+hover; after the mouse moves away it is plain.
- Nutrition prompt: carry the authors' lean next to "does not establish a long-term advantage"; put a number only in a sentence with its own [n].
- NCBI 429: test with 5 straight 429s: 3 calls in all (cap), waits of 1 s then 2 s, then HTTPError.

## Pass 52
- Bug (found by the reviewer in a screenshot): after deleting a chat the sidebar showed two TODAY groups and duplicate rows. Cause: pass 50 made New chat redraw the list, and delete also redraws it; the two requests both appended. Now only the newest request draws. DOM count on desktop, 2 chats: start 1 header / 2 rows; after delete before the fix 2 headers / 2 rows (one chat was left, shown twice); after the fix 1 header / 1 row; after undo 1 header / 2 rows; New chat with the mouse away 1 header / 2 rows, none selected.
- Status dot: 6 px more room before the title.
- Phone 390 px, long title: title box ends at x=179, select starts at 181, title is cut with an ellipsis.

## Pass 53
- Code panel: after "Try it" on a search connector, a "Compare raw and normalized" box shows what the code returned as the chat receives it (JSON), and the raw response from the box above when one is filled. Browser check with a small test function: it opened and showed the normalized item (year 2021 became the text "2021"). The raw side was not exercised.
- Phone: drawer rows 60 px -> 52 px (touch buttons stay 44 px); title-to-select gap 2 px -> 8 px (box edges).
- Not reproduced: a grey first suggestion chip. Computed background of both chips is transparent, neither focused nor hovered, on desktop and phone.

## Pass 54
- Compare box: long JSON lines wrap instead of being cut (no horizontal scroll at 1100 px: scrollWidth <= clientWidth in both blocks); box edge at x=583, text blocks end at 552. Code editor lines wrap (pre-wrap). "Raw" and "Normalized" labels darker and bold. Shot with the raw box filled and full page height.

## Pass 55
- Code editor now wraps long lines with the editor's own line wrapping (the CSS-only wrap in pass 54 did not show in pixels). Check with a 260-character comment line: that line is 105 px tall (several rows), the other long lines 35 and 53 px, no horizontal scroll.

## Pass 56
- Code editor: wrapped rows have a 20 px hanging indent. Measured on the 260-character line: first row starts at x=170, continuation rows at x=190. Narrow check at 480 px wide: no horizontal scroll, the long line wraps to 175 px tall.

## Pass 57
- Hanging indent now follows each line's own indent: wrapped rows start 20 px right of where that line's code starts (leading spaces counted, a tab = 4). Measured at 1100 px: line with 8 leading spaces: code starts ~227, continuation 247; line with 4 spaces: ~197 and 217. The earlier fixed offset (pass 56) was replaced.
- A first attempt did not show because CodeMirror reset the style after each update; the styles are re-applied when that happens.

## Pass 58
- Editor gutter drift fixed: the per-line indent set by script after the editor measured the lines left line numbers off their rows. Replaced with a fixed style rule that the editor measures with. Gutter offsets at 480 px, line number top minus line top (px): before 0 0 0 0 0 -17 -17 -17 -35; after 0 for all 9 lines. Cost: the continuation indent is a fixed 20 px from the editor edge, not the line's own indent (per-line indent needs editor internals).
- URL break: wrapping prefers break-word, so a long line no longer splits inside "https://" when an earlier break exists.
- Settings: under 1000 px wide the live preview stacks above the form (before: form 368 px wide at 900 px; now 772 px).
- Keyboard: Tab inside the code editor inserted spaces, so "Try it" could not be reached (40 Tab presses, never reached). Now Esc then Tab leaves the editor; from the description box, "Try it" is reached in 6 presses at 900 and 1100 px. A hint line says so.

## Pass 59
- Regression from pass 58 fixed: the break-word override stopped the editor from wrapping, so long lines were cut at the right edge. Removed. Checks now include clipping: at 480 px and 1100 px the editor has no horizontal scroll, content right edge equals the scroller right edge, and 0 lines extend past it. Gutter offsets are 0 for all lines at both widths (line 8 is 140 px tall at 480 px, 88 px at 1100 px).
- Settings at 900 px: the blank space under the stacked preview was a 90 px bottom margin meant for the side layout; it is 12 px now (gap from the preview to its caption was 100 px).
- Editor: a long line starting with spaces had a blank first row (8 spaces on a row alone, then the text). Wrapping may now break anywhere, so the text starts on the first row. Measured rows at 480 px: before ["        ", "urllib...", ...], after ["        urllib.request.urlopen(\"htt", "ps://example...", ...]. The cost is a break inside "https" at narrow width. No clipping (0 lines past the edge) at 480 and 1100 px; gutter offsets 0.
- Settings intro says "live preview", not "preview on the right" (it can sit above the form now).
- Footer: the separator dot moved from the first text to the second, so it disappears with it (820 px wide: no trailing dot).

## Pass 61
- Settings menu showed two active items after a click and a scroll (the Prompts and Code helpers links were added later and were not part of the scroll tracking). Now one active item at a time: after click on Code helpers 1 active; after scrolling to Shape and spacing 1 active (before: 2).
- Answers with no evidence now keep a Copy button next to More (before: only More).
- The "uncited" flag skips honest no-evidence sentences such as "The sources do not explain ...". Test added (77 tests OK).
- Docs app on a real corpus (README, DESIGN, SCHEMA, 8.4 KB), 6 questions, real model: 6 of 6 answered from the files with citations; 5 of 6 had every sentence supported (the API-key answer had 2 of 3), none uncited. One 8099 port clash showed a stale server first; re-run on its own port.
- Nutrition prompt: no em dashes.
- The two similar rows in the nutrition sidebar were two chats (different ids), made by my test asking the same question at two widths; not a duplicate row.

## Pass 62 (design review round 1, 8 items)
- Settings page recoloured from blue to the deep green of the chat (buttons, toggle, top nav, focus rings, links, "More" link, summary links, editor text) and the blue-tinted greys replaced with green-greys. Check: a script that scans every visible element's colours for blue found 42 elements before and 0 after, on the settings page at 1440 px.
- Sidebar: the active chat is now a light green fill with dark green bold text; New chat keeps the dark green fill (measured: New chat rgb(23,63,53), active row about rgb(230,232,226)).
- Answer actions: 12 px between Copy, Helpful, Not helpful and More (measured 12 and 12).
- Settings intro: 600 px wide. Code helper buttons: 8 px gap, 12 px radius. Success banner lighter, with a soft border.
- Preview card: layered soft shadow. Donut to legend gap 24 px.
- Docs at 390 px: the style select is 96 px wide (title box 100 px); user bubble cream lightened from #e6deca to #efe9d8 (theme default; apps that set their own colour keep it).
- Not done on purpose: green left borders on cards (owner rule); the code editor wrap at 480 px (kept, see pass 59).

## Pass 63 (Gemini round 2, 78/100): 8 items
Gemini text used as design input only. Skipped the left-border advice (house rule: no accent bars).
- Settings h1 in the serif heading font (Fraunces now loaded on settings.html).
- Settings layout max-width 1180px, centred, so the nav sits next to the cards (nav left 210, 1600px viewport).
- Reference card numbers bold deep green (#173f35, 700), same as inline citations.
- Answer actions separated by a faint middle dot, no pill chrome. Touch targets 44px high (Copy 44x44, More 51x44 at 390).
- Null answer ("no evidence") styled muted and italic (class none, set when evidence is empty).
- Dashed borders replaced by solid light (#cfd9d1); blue-ish ctx chipmore recoloured to deep green.
- Save/Load state cards equal height (243 and 243) and equal padding.
- Chat header Configuration link weight 500.
Open: nothing new. Checks are DOM and computed-style numbers (p64.cjs), not pixels.

## Pass 64 (Gemini round 3, 88/100, plus B2 pixels on pass 64)
Gemini text used as design input only. No resting pills (house rule); hover and press tint instead.
- Save/Load state: inputs 100% width, 44px high, placeholder fits; Save, Load, Delete all 40px high on one baseline (top 833); cards equal width 242 and equal height 213 at 1600.
- Settings grid: nav 170px, gap 22px, cards 566px wide, container 1180px (nav to cards gap 22).
- Sidebar active row: 14px right padding, 4px icon gap, title max-width leaves room for icons.
- Composer: textarea 38px high, line-height 20px, centre 714 equals icon centre 714.
- Answer actions: hover tint (8% green) and press tint on buttons, 8px radius, no resting background.
Open: Gemini's ask for resting pill containers was declined on purpose.

## Pass 65 (Gemini round 4 96/100, ChatGPT round 1 79/100)
Reviewer text used as design input only. Skipped: left borders, resting heavy pills.
- Copy: never a resting background (hover and press tint only, forced with !important); the grey in the earlier shot was a captured hover.
- Related arrows are an SVG mask icon, not text. Settings lead uses text-wrap balance. Delete button has a lighter border.
- Live preview header tightened (gaps, 88px select, 13px title) so "Refund questions" is not cut.
- Empty evidence answers now show "No evidence found", the answer line and 3 tips.
- Mobile header: Configuration button and style select hidden under 760px, 44px icon targets, title takes the space (182px at 390).
- User bubble max 88% (86% on mobile) with 16px thread padding; reading column 780px on desktop.
- Sidebar: action icons only on hover or focus, not on the selected row at rest.
- Citation cards smaller radius and padding, lighter border. Footer note 12px. Inactive tab darker.
- Settings: "state" wording changed to "look" everywhere (Save look, Load a saved look); "Updates as you edit" tag on the preview; nav rows tighter.
Not done: full spacing scale and type scale audit; superscript citation numbers in prose.

## Pass 66 (settings at 390)
My late grid override (170px / 1fr / 400px) sat after the responsive rules in settings.css, so at 390 the cards column collapsed to 0px and the page was 580px wide. Responsive rules re-added at the end of the file: single column under 1000px, nav hidden under 1180px, card and toolbar full width, tighter card padding under 560px, code-helper buttons wrap. Measured at 390: document width 390, no section wider than its box (n=12 sections). Section captures are now full panels (19KB to 78KB each), plus a full-page capture.

## Pass 67 (Gemini fresh full-set review, 42/100)
Reviewer text used as design input only. Not done on purpose: white cards, dashed dropzone, resting pills, left borders.
- Mobile config: floating Preview button opens the live preview as a bottom sheet (62vh); closed by default under 1000px. Measured at 390: doc width 390, FAB 48px high, sheet 374x523.
- Logo picker: native file button restyled (outline, 44px, 12px radius, no "No file chosen" text).
- Intro max-width 60ch; form fields max 640px; focus-visible ring (2px deep green); checkbox top aligned; colour swatch border; slider track 4px with thumb shadow; select chevron 12px from edge and 32px right padding; disabled opacity .5; mono font in code boxes; export/import/reset borders; preview panel shadow.
- Chat: 24px gap before a user turn after an answer; bullets 1.6 line height; 16px action gaps; dark disclaimer #a9b7b0; user bubble padding 12px 16px; tab shadow; safe-area bottom padding; header icon gap 12px.
- Mobile settings: 20px side padding (card 16px), inputs, selects and buttons 44px, section and save buttons 48px.
Not done: font previews inside options, radius slider cap, stepper scroll, provider icon audit, icon stroke audit, user bubble colour change (kept #efe9d8, matches theme.py).

## Pass 68 (ChatGPT full-set 63/100, Gemini FAB sheet bug, Harsh: Simple/Advanced)
Reviewer text used as design input only. Skipped: left borders, resting pills.
- Capture fixed: the "answer with sources" shot now uses the Nutrition app and shows source cards (4, 2, 3, 3 cited sources in light/dark desktop/390); before it showed no-evidence.
- Model tab and intro say one thing: keys stay on the computer running CustomChat, from an environment variable or a private local file (secrets.json, mode 0600), never shown again.
- Preview sheet at 390 had overlapping cards because `#pvmodel{min-height:48px}` overrode the panel height; removed. Sheet children no longer shrink (iframe 433px). Checked 3 sections: Model (status cards), Colors, Layout: 0 overlaps.
- Settings page background now cream #f5f1e8 (was pale blue).
- Irrelevant fields hidden: gradient colour and angle only with Gradient, image link only with Image, pattern controls only with a pattern.
- 390: sticky horizontal jump menu (12 chips, 44px), composer 48px, send and icons 44px, suggestion chips 36px.
- Dark muted text #a3b3ab. No-evidence tips padding 16px.
- Simple / Advanced switch on the config page, saved in the browser, Simple by default. Simple hides Prompts, Code helpers, pattern controls, line spacing, animation speed, sidebar width, image link and Ollama/guide boxes (10 sections, 10 menu items). Advanced shows all (12 and 12).
Pages that exist: chat (/) and configuration (/settings.html). There is no About or Contact page.
Not done: one sticky save bar instead of per-section Save and Reset, preview rebuilt from the production chat component, wider desktop sidebar.

## Pass 69 (apply remaining reviewer items)
- Sliders show their range ("0% to 160%") under the value; slider hit area 44px at 390.
- Delete look: muted red text and a confirm dialog. Export look wording shortened; Apply replaces "Apply model settings".
- Provider choice is a 2-column grid of 44px buttons.
- Remove-background checkbox starts unchecked and disabled until a logo exists. Copy: "Choose a picture", "Stays on this computer", "Fonts" tab name, motion and corner roundness help, editor hint "Press Esc, then Tab, to move past the editor."
- 390: smaller title (26px), lead 14px, export/import full width.
Still open from the reviews: one sticky save bar, preview from the real chat component, wider desktop sidebar, row chevrons on prompt rows, collapse generated code until written, background-style swatch picker, font previews inside the font selects, layout previews, micro-animations pass.

## Pass 70 (UI round 1: Gemini 58, ChatGPT 72)
- Form fields: border deep green at 22% opacity, 12px radius, cream fill (no dark borders). Buttons pills, inputs 12px, cards 16px.
- Mobile config: bottom padding 180px and card margin 96px so the Preview button no longer covers Reset or the last fields.
- Sliders: 6px track, 22px deep-green thumb with cream ring. Colour inputs: round 40px swatches.
- Settings title 28px. Simple/Advanced switch smaller with a light green fill.
- Chat: no-evidence block left-aligned, answer 15px/1.55, source cards 13px, action row 12.5px, empty state lower with 32px gap before suggestions, dark composer 1px light border, disclaimer safe-area padding.
Still open: custom select popovers, toggle switches on prompt rows, row chevrons, preview from real chat component.

## Pass 71: UI round 2 fixes (part 1)
Chat column 700px centred with composer to match. Quieter sidebar, top bar controls without pills, composer radius 18 and 1px border, 38px send, source rows without borders, 32px action targets (44px on phones), tighter phone composer and disclaimer, 32/28px empty heading, dark palette with readable secondary text, equal-height key input and save button, segmented control thumb shadow. Not done yet: custom select popovers, toggles on prompt rows, sticky save bar, real-chat preview.

## Pass 72: UI round 3 fixes (part 2)
Preview is a full-width bottom bar under 1000px (no overlap measured with visible controls). Sources are plain rows with a hover tint, example questions are text rows with an arrow, composer border softened, dark palette split into canvas #07130F, surface #0B1C16, elevated #10261E, 20px side padding and 14.5px answer text on phones. Audit: no coloured left borders, no dark borders and no resting backgrounds on action links found in the DOM at 390 chat, 390 settings, 1440 settings (composer border was dark green, now softened).

## Pass 73: UI round 4 fixes
Settings: every select is now a custom listbox (bottom sheet on phones), checkboxes are switches, file input has a styled button, no textarea resize handles, section menu is text with an underline for the active item. Chat: source numbers are round badges, dots between actions removed (16px gap), phone sources are a one-line horizontal row, phone header has blur and a faint divider, phone hint line hidden (the one-line safety note stays). Not done: single sticky save bar, real-chat preview, desktop 3-column layout, font/colour specimens, copy cut, dark code editor page.

## Pass 74
Settings desktop widens to 1360px with a 440px live preview (the preview already is the real chat page in an iframe, /?preview=1). Help text is plain muted text, not a boxed card. Hex codes show only in Advanced mode. Not done: single sticky save bar, font/colour specimens, copy cut, dark code editor page, SVG chevrons.

## Pass 75: UI round 5 fixes
Phone settings: section menu is a plain scrolling row (no sticky overlay), intro paragraph hidden, Simple/Advanced 36px, provider chips scroll with snap, prompt steps are a vertical numbered list, inputs and buttons side by side are all 40px, colour swatches 24px with a light border, logo picker uses a styled label button (native input hidden). Chat: composer border and shadow quieter (green only on focus), safe-area padding, 15.5px answers on desktop, 12px above the action row. Not done: auto-save or a single save bar replacing per-section Save, unified preset icons, kebab menu for code helper actions, SVG chevrons.

## Pass 76: UI round 7 fixes
Audit of computed styles and ::before/::after on chat (1440, 390, no-evidence 390) and settings found 0 coloured left borders, 0 inset left shadows and 0 accent bars; only the preset swatch diagonal gradients matched. Changes: composer has a blur and fade, desktop form column capped at 720px, 20px side padding on phones, 44px switch rows, section headings in the serif at 19px, 32px between sections, field borders 20% green with a 2px focus ring, secondary buttons are text with hover tint, font menus preview each font, no-evidence text in a deliberate secondary tone. Not done: single save bar, SVG chevrons, dark code editor page.

## Pass 77: UI round 8 fixes
One save bar for the look: the per-panel Save and Reset blocks are gone from the look panels (each panel keeps its small reset in the header, the sticky bar saves everything). Measured at 390 after a change: save bar sits directly above the Preview bar with no overlap. Also: 12px radius on inputs and buttons, 24px thumb and 360px max width on sliders, panel subtitles darker, left-aligned composer text, 16px under the disclaimer, 32px above user messages, balanced text wrapping, source text 12px. Not done: SVG chevrons, dark code editor page, unified preset icons, kebab for code-helper buttons, auto-save.

## Pass 78 (round 10)
Serif 22px panel headings, prompt statuses right aligned, preset padding 16px, one segmented style, 4px slider, Preview bar blur + safe-area padding, larger empty state (34px/16px), no-evidence text no italics, stronger sidebar and answer type. Left-border audit: 0 found.

## Pass 79 (round 11)
Mobile provider chips become a 2-column grid, tab menu fades at the edge, stage rows 48px, monospace padded code boxes, SVG select chevrons, source chips tinted, dark muted text lifted, sidebar active row stronger.

## Pass 80 (round 12)
SVG chevrons replace arrow characters, citation chips lose resting fill (hover only), Simple/Advanced is a 240px segmented control, white slider thumb with accent ring, numbered vertical step list, spacing above RELATED, no-evidence list rhythm, dark subtext lifted.

## Pass 81 (round 13)
Mobile Preview button moved into the header row (no fixed bottom bar, no overlay), save bar only when dirty, 20px mobile margins, 40px buttons, Export/Import as quiet text, Temperature/Sources side by side on desktop, dark composer border.

## Pass 82 (round 14)
Custom range sliders with filled track, code helpers as collapsed accordions, quieter presets, chat line height 1.6, composer safe area and send-button padding, sources wrap to two lines, 44px rows.

## Pass 83 (round 15)
Auto-save (1.5 s after the last change), merged Saved looks section with quiet Export/Import/Reset, 4 presets shown by default, 520px desktop preview, live typography/layout/motion previews, Prompts grouped in three stages, calmer provider selector, dark code editor.

## Pass 84 (round 16)
Mobile toolbar reserves room for the Preview button, section tabs wrap instead of clipping, 13.5px helper text, 64px emoji fields, lighter dark send button, 780px desktop chat column, softer composer shadow, more safe-area padding.

## Pass 85 (round 17)
Provider selector is a 3-column grid on desktop (was clipping at 398px, scrollWidth 443), composer placeholder no longer wraps (padding-right 56px to 12px), sources stack on phones, disabled controls readable, tighter radii, dark RELATED contrast.

## Pass 86 (round 18)
Settings sections lose their card boxes and use hairline dividers, presets are a full-width list on phones, inputs 44px with 8px radius, lighter composer, no icon chips in headings.

## Pass 87 (round 19)
Dark no-evidence text lightened, citation markers get a 4px tint, 32px under user rows, mobile heading 26px and full-width Simple/Advanced, equal-size preset tiles, switch rows label-left, Light/Dark control iOS style.

## Pass 88 (round 20)
Mobile section tabs scroll in one row with edge fade (44px chips), filled borderless inputs with green focus ring, 19px section headings, quiet Reset group, smaller slider thumb, sticky desktop preview, custom no-evidence bullets, larger phone secondary text.

## Pass 89 (round 21)
Motion preview dot removed, solid circular send button, RELATED in sentence case, fixed-width source numbers, 15.5px phone answers, 14px source titles, stronger unselected Light/Dark text, dark secondary text lifted.

## Pass 90 (round 22)
Code-helper rows compacted, Load more as quiet text, 44px aligned key row, 20px phone padding, answer line height 1.65, hanging-indent source rows, centred send arrow, no-evidence bullet spacing. Left-border audit: 0 found (light and dark).

## Pass 91 (round 23)
Two-column groups and row buttons stack at 390, Preview button 44px with safe-area top, more space above group headers, dark footer text lifted, empty-state suggestions get a hairline border and 44px height.

## Pass 92 (micro-animations)
Transform/opacity-only micro-animations: staggered suggestion entrance with chevron nudge, send button hover/press, composer focus ring, citation and source hover lift, sidebar item shift, settings tiles fade-up, preset lift, button press, slider thumb grow, accordion content fade, saved-tick, custom select open. Disabled by Motion = none and prefers-reduced-motion.

## Pass 93 (R23 leftovers + Harsh note)
Chat column centred in the main area (was left-anchored at 1440, leaving a gap on the right), empty state capped at 640px, slider value readouts aligned and no-wrap, provider buttons share one baseline, desktop preview 560px, settings content flush-left, 20px phone padding.

## Pass 94 (UX pass 2, round 1)
Copy button confirms in place (tick, "Copied" for 1.6 s, plus the toast), send button dims when the box is empty, slider inputs get accessible names, focus-visible ring on all controls. Audit at 1280: 0 unnamed controls in chat, 2 on settings (fixed).
