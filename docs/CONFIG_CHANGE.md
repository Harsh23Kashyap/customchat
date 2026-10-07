# Config diff and rollback

Legacy app files without `schema_version` are version 1. New files can say `schema_version: 1`. This release rejects unknown/future versions instead of silently interpreting them. There is no version-2 migration yet and no automatic upgrade.

Preview a candidate without loading `.env`, models, source connectors or private state:

```sh
customchat config-diff app.yaml candidate.yaml
```

The output lists changed keys and their behavior category, plus SHA-256 hashes of both exact files. It compares merged defaults, so adding an unchanged default is not a behavior change. It deliberately does not print old/new values, credentials or prompt text. Review the candidate privately to understand the exact values; the categories do not judge whether a change is safe. Source list changes are reported as one corpus/access change.

Apply only the two exact files reviewed, using the hashes from that preview:

```sh
customchat config-apply app.yaml candidate.yaml --current-sha CURRENT_HASH --candidate-sha CANDIDATE_HASH
```

Both files must pass config-doctor. A stale hash or symlink stops replacement. A new owner-readable backup is written before replacement, preserving the old bytes, comments and formatting. Candidate bytes replace the config through a same-directory temporary file, with private permissions. No `.env`, database, theme or session files are copied. Restart to load the new config; this does not hot-reload a running server.

## Rollback

The apply command prints the backup path. Use that backup as the next candidate:

```sh
customchat config-diff app.yaml app.yaml.backup-TIMESTAMP
customchat config-apply app.yaml app.yaml.backup-TIMESTAMP --current-sha CURRENT_HASH --candidate-sha BACKUP_HASH
```

Rollback itself keeps another backup. No backups are deleted automatically. Store them privately; although diagnostics hide values, the backup contains your full original file. Backup paths are not published or uploaded.

This protects configuration-file replacement, not database migration, external side effects or concurrent writers. There is a last hash check before replacement but no distributed file lock; stop other writers while applying. Backups are not a production restore or a promise that old provider APIs still work.
