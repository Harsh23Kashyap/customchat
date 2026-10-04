# App schema

Every key is optional. Unknown top-level keys are rejected so typos fail loudly. Run `python -m customchat validate app.yaml`.

## app
| key | default | meaning |
|---|---|---|
| id, title, tagline | my-chat, My Chat, ... | names shown in the UI |
| accent | #2563eb | accent colour |
| examples | [] | starter questions on the empty screen |
| footer | "" | small text under the sidebar |

## provider
| key | meaning |
|---|---|
| type | `mock`, `ollama`, `openai`, `openai_compatible` |
| model | required except for mock |
| base_url | Ollama default `http://localhost:11434` (or `OLLAMA_BASE_URL`); OpenAI default `https://api.openai.com/v1` |
| api_key_env | NAME of the environment variable holding the key. `openai` defaults to `OPENAI_API_KEY` |
| temperature, timeout | defaults 0.2 and 120 |

## sources
A list. Each entry has `type`, optional `id` and `label`.

- `local_files`: `path` to a folder of .md .txt .json .csv files. Markdown headings become sections.
- `http_json`: `url` with `{query}` and `{k}`, `results_path` (dotted path to the result list), `fields` mapping `title text url authors year venue` to dotted paths in each result, optional `header_env: {Header-Name: ENV_VAR}`.
- `pubmed`: optional `filter` (PubMed query syntax). Set `NCBI_API_KEY` for higher rate limits.
- `arxiv`: optional `category`, for example `eess.SP`.
- `python`: `entry: module:function`. The function takes `(query, k)` and returns a list of dicts with `title`, `text` and optional `url authors year venue score`.

## retrieval
`top_k` (1 to 50, default 6), `min_score`.

## prompt
`system`, `style` (named answer depths, default quick/standard/deep), `no_evidence` (reply when nothing is found).

## memory
`enabled`, `recent_turns` (how many earlier turns go into the prompt), `summary_every` (turns between rolling-summary refreshes).

## citations
`required`, `ledger`.

## auth
`mode: none` or `token`. With `token`, set `token_env` to the name of an environment variable holding the access token.

## storage / server
`storage.path` (SQLite file, relative to the app file), `server.host`, `server.port`.
