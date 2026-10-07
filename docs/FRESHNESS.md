# Local document freshness

Local source folders update without restarting the app. Before retrieval, CustomChat checks for changed, added and removed files, rebuilds the BM25 index and clears answer-evidence caches after a successful change. SHA-256 hashes identify document versions; local evidence includes the document-relative name and version hash, so saved answers retain the version they used.

```
sources:
  - id: docs
    type: local_files
    path: docs
    refresh_interval: 30
```

Checks happen when questions arrive, at most once per interval (seconds, 0-86400). Configuration > Document freshness shows the last check, counts and index revision, and **Check documents now** forces a scan. There is no idle background watch, external service polling or model call. Setting 0 scans on every question, which can be expensive for large folders. The check reads supported files to hash their content; file-time changes alone do not define freshness.

A missing/unreadable folder or symlink stops use of that source. Old passages are not used for a new answer after a failed check. Other available sources can still answer. A later question or owner check retries, and recovery swaps in a complete index. Existing saved answers remain historical snapshots; they are not silently rewritten.

The first scope is .md/.txt/.json/.csv local folders. Remote docs, PDF/OCR, notifications while idle and scheduled sync are not included. Keep private account files and personal uploads out of configured source folders. Owner/admin authorization and configuration locking apply to the freshness status endpoint.
