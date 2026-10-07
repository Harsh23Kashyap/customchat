# App schema

Every key is optional. Unknown top-level keys are rejected so typos fail loudly. Run `python -m customchat validate app.yaml`.

## app
| key | default | meaning |
|---|---|---|
| id, title, tagline | my-chat, My Chat, ... | names shown in the UI |
| accent | #173f35 | brand colour (buttons, active rows, user bubbles) |
| accent2 | #d7ef72 | highlight colour (send button) |
| examples | [] | starter questions on the empty screen |
| footer | "" | small text under the sidebar |

## provider
| key | meaning |
|---|---|
| type | `mock`, `ollama`, `openai`, `claude`, `gemini`, `openai_compatible` |
| model | required except for mock |
| base_url | Ollama default `http://localhost:11434` (or `OLLAMA_BASE_URL`); OpenAI default `https://api.openai.com/v1` |
| api_key_env | NAME of the environment variable holding the key. `openai` defaults to `OPENAI_API_KEY` |
| temperature, timeout | defaults 0.2 and 120 |

## sources
A list. Each entry has `type`, optional `id` and `label`.

- `local_files`: `path` to a folder of .md .txt .json .csv files. Markdown headings become sections. `refresh_interval` is seconds between on-question checks (default 30, 0 checks every question, max 86400). Content hashes detect changes even when file size/time stay the same.
- `http_json`: `url` with `{query}` and `{k}`, `results_path` (dotted path to the result list), `fields` mapping `title text url authors year venue` to dotted paths in each result, optional `header_env: {Header-Name: ENV_VAR}`.
- `pubmed`: optional `filter` (PubMed query syntax). Set `NCBI_API_KEY` for higher rate limits.
- `arxiv`: optional `category`, for example `eess.SP`.
- `python`: `entry: module:function`. The function takes `(query, k)` and returns a list of dicts with `title`, `text` and optional `url authors year venue score`.

## retrieval
`top_k` (1 to 50, default 6), `min_score`.

## prompt
`system`, `style` (named answer depths, default quick/standard/deep), `no_evidence` (reply when nothing is found), `answer_note` (a fixed line added after every answer that has sources, e.g. a disclaimer).

## memory
`enabled`, `recent_turns` (recent turns prioritised in context), `summary_every` (turns between chat-local summary refreshes), `context_chars` (character allowance; see Conversation context below).

## citations
`required`, `ledger`.

## auth
`mode: none` or `token`. With `token`, set `token_env` to the name of an environment variable holding the access token.

## storage / server
`storage.path` (SQLite file, relative to the app file), `server.host`, `server.port`.

### Conversation context

`memory.enabled` controls saved and temporary conversation context. Context stays within the current owner, chat and conversation; switching conversations does not import another chat's answers. Scoped-document answers are excluded from later general context.

- `recent_turns` (1-20, default 4): prioritise the newest turns before older matching turns.
- `summary_every` (1-50, default 6): refresh a chat-local summary every N visible, unscoped turns. Deleting a source turn invalidates its summary.
- `context_chars` (8000-2000000, default 60000): character allowance for answer context, with space reserved for the question, instructions and current evidence. Set a lower allowance for small local models. This is not an exact token count or automatic model-window discovery. Evidence alone can exceed a very small allowance.

Recent history and older keyword matches are selected from storage; the entire thread is not sent to the model. Complete answers are kept when they fit. An oversized latest answer uses a marked head/tail excerpt. Summaries are lossy context, not evidence or unlimited recall. Demo mode does not perform model-based follow-up rewriting.
