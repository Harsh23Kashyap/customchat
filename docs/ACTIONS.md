# Bounded actions: first registry

All registered tools are enabled by default, as requested. This release registers `list_notes` (read) and `save_note` (write), a useful local smoke path for the review/execution contract. It does not mean all conceivable tools, shell access or unrestricted network access.

```yaml
actions:
  allow: null   # all registered tools; [] disables all
  writes: true # false leaves read tools only
```

Choose Actions beside the composer, fill the declared fields, Preview action, review the exact tool/mode/arguments, then Confirm action. Every action requires that review; YAML cannot disable confirmation. Nothing runs just because a model or source document suggests it. There is no automatic model tool planner in this slice and no external ticket/email/API action yet.

Server review tickets are bound to the signed-in identity and exact validated arguments, expire after five minutes, and are single-use. Execution rechecks the current allowlist/write policy. Extra fields, arbitrary tool names and changed arguments are rejected. Consuming a ticket precedes execution so retries cannot repeat a write; if the process dies in between, the action may be lost, not automatically retried. This is an in-process execution lock and SQLite state, not a distributed multi-worker exactly-once guarantee.

Notes are in the existing user-owned state store. In accounts mode each visitor sees only their own. No-auth and shared-token modes share one identity and therefore notes: do not use those modes for private multi-user notes. Temporary chat does not make an explicitly confirmed note temporary. Account deletion removes state. Note deletion/edit UI and quota management are not in this first registry. Listing returns at most 100 notes.

The registry exposes field types and size limits; implemented notes cannot call arbitrary URLs, run code, write files outside the state store or spend money. New tools need separately implemented handlers and tests, not YAML executable snippets. Do not treat this lane as a general agent integration catalog.
