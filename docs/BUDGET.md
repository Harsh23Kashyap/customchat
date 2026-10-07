# Budget limits (first slice)

```
budget:
  daily_questions: 500
  user_daily_questions: 50
  daily_model_calls: 2000
  spend_cap_usd: null
```

Configuration > Budget edits these limits. Saved settings persist in the app's state folder and override YAML until removed/changed. Portable app exports include the active limits, not counters. Daily counters are stored in a separate local SQLite database, survive restarts, and reset at midnight UTC. Quota checks/increments are atomic. Counter state stores hashed owner identifiers, not question/answer text. 0 means unlimited for count quotas; null means no dollar gate.

Request limits cover HTTP ask, streaming ask and regenerate, including failed attempts. Per-user quotas use the app's owner identity: account users are separate, but no-auth/token apps share their respective owner scope. The existing 30 questions/minute throttle remains. CLI ask/eval are outside HTTP quotas.

Model limits cover pipeline invocations (answer, rewrite, relevance, follow-ups, summary, etc). Failed attempts count. A provider fallback or internal transport retry can issue multiple remote requests inside one invocation, so this is **not a provider HTTP-request or token cap**. Owner-run configuration tests/generation and external web/embedding services are outside this first slice.

## Dollar caps are not a billing meter

Providers do not yet expose verified usage/pricing accounting. Any non-null spend_cap_usd blocks all non-Demo answer-pipeline model calls before calling a provider, rather than inventing a running dollar total. The UI makes this limitation explicit. It does not cap owner configuration tools or other service fees. Set provider-side billing limits before public use. This release does not promise to hold a functioning paid app below a dollar amount; usage capture, pricing, retry/fallback accounting and reservation/reconciliation remain pending.

Only an owner/admin can inspect or edit budget settings; configuration locking disables the endpoint. The local ledger is for one host/shared app folder, not a distributed cloud quota service. Do not delete its budget.db to reset enforcement. Disk errors stop budget checking rather than silently falling back to an empty counter.
