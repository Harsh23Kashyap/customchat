# NewsNerd local starter

All supported configuration fields are explicitly filled. Only secret key values are blank. This is a sample inside CustomChat, not a separate backend or a reset of your existing workspace.

## Start on existing CustomChat

From the CustomChat repository root: `python -m customchat run apps/newsnerd-sample/app.yaml`.
Uses the existing CustomChat installation, no extra launcher or app. Open http://127.0.0.1:8081. Offline Demo returns setup-guide excerpts, not live news. Ask "What is NewsNerd?".

## Live GNews with a local model

1. Copy `.env.example` to `.env` in this folder. Fill `GNEWS_API_KEY` locally. Keep `NEWSAPI_KEY` blank unless you use the alternative. Never send `.env` to anyone, include it in a ZIP, commit it or paste it into a prompt.
2. Install Ollama from https://ollama.com and start it. In a separate Terminal run `ollama pull qwen2.5:3b`. This downloads a model and uses disk/bandwidth, but no hosted generation API. If Ollama is not already running, use `ollama serve`.
3. Run `python -m customchat run apps/newsnerd-sample/app-gnews.yaml` (Windows: `py -3 -m customchat run apps/newsnerd-sample/app-gnews.yaml`). API requests begin when a news query is asked; without a key the adapter fails before any network request.
4. Ask short keywords, such as `AI regulation`, `renewable energy`, or `India economy`. The adapter removes common question filler and special punctuation; it does not send the whole natural-language sentence as strict GNews AND syntax.

GNews Free: 100 requests/day, at most ten articles/request, twelve-hour delay and thirty-day history. This sample asks for up to six English-language articles, sorted newest first. Free is for non-commercial development/testing, not public production. Do not deploy this sample on a public domain with the free key.

Local Ollama summaries are real model output but can be wrong. An article claim is not independently verified just because it has a citation. Responses use snippets, with publisher and publication time embedded in the evidence. Read original links. Delayed results are not breaking news.

## NewsAPI alternative

Fill `NEWSAPI_KEY` in `.env`, then `python -m customchat run apps/newsnerd-sample/app-newsapi.yaml`. The same local model is used. NewsAPI Developer permits local development/testing only, has 100 requests/day, articles delayed twenty-four hours, and search up to a month old. Do not combine both sources by default: it would multiply requests and require two keys.

## Files and state

- `app.yaml`: offline Demo, local setup-guide source.
- `app-gnews.yaml`: GNews API + local Ollama.
- `app-newsapi.yaml`: NewsAPI alternative + local Ollama.
- `news_connector.py`: complete reviewed adapter source. Keys go in the X-Api-Key header, never URLs.
- `.env.example`: key slots, blank by design. Copy locally to `.env`.
- `docs/`: offline guide, not a real article corpus.
- `CONFIG-FIELDS.md`: every config field, value and reason.
- `PROMPTS.md`: every prompt stage and editing path.
- `test_newsnerd.py`: fixture-only connector/config tests, never calls a real API.
- `data/customchat.db`: created on first run; local saved chats. All three modes share it, so keep the same folder. Prompts and settings may persist beside it. Restart after changing YAML or `.env`.

## Troubleshooting

- Port 8081 busy: stop the earlier app or change `server.port` in the selected YAML; then open the new printed URL. The run command opens the configured URL automatically; use --no-browser to disable that.
- Missing key: fill the matching local `.env` variable and restart. A shell env value takes priority over `.env`.
- No results: use shorter keywords; free plans omit very recent articles. Unknown publisher/date are labelled rather than invented.
- HTTP 401/403: key or plan access problem. HTTP 429: daily/rate limit; stop and wait for the provider reset. There is no automatic retry loop.
- Source error may appear as `ValueError` in this release's source-error summary. The direct adapter test below provides a clearer message without exposing the key.
- Ollama unavailable/model missing: start it and pull the configured model. No paid hosted model fallback is configured.
- Demo answers look like excerpts: expected. Demo is not a news summarizer. Use live config plus local model for summaries.
- Python pip externally managed: use your existing private CustomChat environment. Do not use sudo, global pip or `--break-system-packages`.
- All fields filled does not mean every field is active: `UNUSED_DEMO_KEY` and `UNUSED_LOCAL_KEY` are explicit inactive env-name labels; mock ignores model/address and Ollama needs no key. `fallback: null` intentionally means disabled.

## Verification you can run

From this folder after installation:

```sh
python -m unittest test_newsnerd.py
python -m customchat validate app.yaml
python -m customchat validate app-gnews.yaml
python -m customchat validate app-newsapi.yaml
```

Windows use the Python interpreter from your existing CustomChat environment. Tests use a fake response and fake key, never real credentials or API calls. Do not run live doctor/probes repeatedly: they can consume quota. No live paid/API key test was performed in preparing this bundle.

Budget: app question limit 80/day is a coarse guard, not provider-wide quota enforcement. Other apps, prompt tests or direct adapter use can consume your key outside that guard. Cache is thirty minutes on repeated matching retrieval queries, not a guarantee of zero API calls. Dollar cap is `null` because this release lacks a billing meter; a numeric cap blocks all non-Demo model calls including local Ollama. The selected provider is local-only, not a paid fallback.

## Current sources (checked October 8, 2026)

- https://docs.gnews.io/authentication
- https://docs.gnews.io/endpoints/search-endpoint
- https://docs.gnews.io/error-handling
- https://gnews.io/pricing
- https://newsapi.org/docs/authentication
- https://newsapi.org/docs/endpoints/everything
- https://newsapi.org/pricing

Provider terms can change. Verify the current plan before using a public/staging/production server. This bundle creates no account, subscription, deployment, or AWS resource.
