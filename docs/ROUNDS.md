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
