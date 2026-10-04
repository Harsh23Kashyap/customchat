# Design

## The shared pipeline

```
question
  1. resolve   rewrite follow-ups into a standalone question using the conversation's memory
  2. retrieve  ask every selected source, dedupe, rank, number the evidence [1] [2] ...
  3. generate  prompt the model with the evidence only, in the chosen depth (quick, standard, deep)
  4. verify    split the answer into claims, check each cites a real evidence number
  5. store     save the turn under a conversation, refresh the rolling summary
```

DietChat, WirelessChat and Custom-Nerd all run this loop. They differ only in the source (PubMed, arXiv plus papers, domain APIs), the prompt, and the look. In CustomChat those differences are configuration.

## Mapping

| Concept | DietChat | WirelessChat | Custom-Nerd | CustomChat |
|---|---|---|---|---|
| Evidence | PubMed | arXiv, IEEE, uploaded papers | `user_search_apis.py` per domain | `sources:` connectors |
| Prompts | `openai_prompts.py` | wrapper prompts | `saved_states/<Domain>/` | `prompt:` |
| Model | OpenAI | OpenAI | OpenAI, Gemini, Claude, Ollama | `provider:` |
| Conversation memory | MySQL turns + summary | owner-scoped SQLite | none (single question) | `memory:` + store |
| Citations | evidence ledger | citation refs | citation rescue | numbered citations + ledger |
| Chats vs conversations | conversations table | topics | n/a | chats and topics tables |

## Components

- `schema.py`: validation and the browser-safe public view of the config.
- `connectors/`: each exposes `search(query, k)` and returns evidence dicts (`title text url authors year venue source score`).
- `providers.py`: `complete(messages)` for each model backend, standard library only.
- `pipeline.py`: the loop above.
- `store.py`: SQLite for chats, conversations (topics), turns.
- `server.py` and `web/`: a small HTTP server and a dependency-free UI.

## Adding a connector

Write a function `search(query, k)` that returns evidence dicts and reference it from `app.yaml` with `type: python`, or add a class in `customchat/connectors/`.

## Safety defaults

Keys never live in config files. The server escapes all text it renders, scopes every query to the owner, blocks path traversal, caps request size, and returns generic errors.
