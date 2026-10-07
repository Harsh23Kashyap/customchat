# Permission-aware sources

Document restrictions require `auth.mode: accounts`. They use exact stable account IDs, not email addresses or display names. `/api/account/me` returns the signed-in account ID. The admin also needs an explicit grant; there is no admin bypass for retrieval.

```yaml
auth:
  mode: accounts
sources:
  - type: local_files
    id: handbook
    path: docs
    read_users: [u_ACCOUNT_ID]
    document_users:
      payroll.md: [u_OTHER_ACCOUNT_ID]
      retired.md: []
```

`read_users` is the collection gate. Missing means public to signed-in visitors; an empty list denies everyone. `document_users` adds exact relative document-name rules within a local collection. Both collection and document gates must pass. Missing document rule inherits the collection gate, so the example does not grant the second account access unless it also appears in `read_users`. Use empty collection readers while preparing a private collection. These are configuration rules, not OS file permissions.

## Enforcement

- Collection filters precede source calls. Local document filters precede keyword top-k, semantic fusion and reranking.
- Restricted apps isolate in-memory retrieval caches by user and policy. They bypass shared remote disk caches.
- Scope lists and public config omit forbidden collections/documents. Starter generation includes only permitted collection labels.
- Saved answers whose evidence is no longer permitted are replaced with an unavailable notice, with citations/ledger/standalone/follow-ups removed. This applies to chat/topic reads and Markdown/JSON/PDF/BibTeX export endpoints.
- Restricted apps omit prior answer history, rolling summaries and saved profiles from new answer prompts. Temporary questions still use the signed-in identity for access checks but exclude personal uploads. Branching a chat containing revoked evidence is blocked.

Restart after editing YAML. In-memory tests also cover policy changes invalidating cached answers. Revocation cannot recall content a person already saw, copied or downloaded, or erase browser tabs already open. Historical question text, chat titles and the user's own saved data remain; restriction is not a data-deletion feature. No new content or answers are written into request logs.

## Limits

Remote sources have collection-level rules only. Remote per-record permissions and external identity/group synchronization are not implemented. Shared no-auth/token modes cannot express individual readers and reject restriction rules. An app owner with filesystem/admin configuration export access can read the corpus; this does not protect data from the host operator. Local indexing loads the corpus in server memory; access gates apply to retrieval and serving, not physical partitioning. Optional semantic/rerank filtering is coded but live model quality is not benchmarked. No private user documents were used in testing.
