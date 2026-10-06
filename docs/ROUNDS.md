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
