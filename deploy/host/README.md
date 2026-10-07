# One-host preparation, no Docker

This is a locally tested preparation/backup/health/code-selection path, **not a deployed public site**. It never provisions a host, changes DNS, buys a domain, installs a system service or publishes a package. Existing AWS scripts are separate and remain untested live.

## Prepare a private plan

From an installed CustomChat checkout, configure token auth, or accounts with the owner already created and signup disabled. Use a workspace-relative SQLite path. Keep code releases separate from the persistent app workspace.

```
python deploy/host/prepare.py /path/to/app.yaml /new/private-plan \
  --domain chat.your-domain.example \
  --release /opt/customchat/current \
  --workspace /var/lib/customchat/app \
  --python /opt/customchat/current/.venv/bin/python
```

Generated files: a hardened systemd unit, Caddy reverse-proxy config, private environment-variable template and plan.json. Never overwrite an existing plan. Templates contain variable names/placeholders, not key values. Enter values privately in /etc/customchat.env on the eventual host; mode 0600. Do not copy that file into GitHub or conversation channels. The generator verifies config shape and required variable names, not whether destination secrets actually work.

Before an owner-approved deployment: prepare a Linux host with a non-root customchat user, Python environment, Caddy and systemd. Install a pinned reviewed code release and dependencies before switching. Place app.yaml and sources in /var/lib/customchat/app; retain its data folder across code releases. Point /opt/customchat/current at the selected release. Confirm ownership and ReadWritePaths match the persistent workspace. Review all generated paths and limits. No startup dependency downloads: the unit uses the prebuilt environment directly.

Domain/DNS, public ports, Caddy certificate issuance and service installation require separate owner approval and live-host verification. Do not interpret successful template generation as valid TLS. No public endpoint was tested for this release.

## Backup and rollback

Stop application writes first. Keep snapshots outside the workspace and private: they include accounts, conversations and keys.

```
python deploy/host/backup.py /var/lib/customchat/app/data /private/snapshots/before-upgrade --writes-stopped
```

SQLite's backup API copies databases and verifies integrity; remaining state files use private permissions. It refuses symlinks/overwrite. Cross-file consistency depends on writes really being stopped. Encrypt backups on the host and test restore in a private copy; this script does not encrypt them or upload to a cloud service.

For a code rollback, stop the service, retain a private snapshot and select an already-prepared older release:

```
python deploy/host/rollback.py /opt/customchat/releases /opt/customchat/current release-id --apply
```

This only atomically switches the code symlink. Restart/health checks are separate. Schema-incompatible state requires a reviewed restore of its matching snapshot while stopped; never blindly overwrite live data. The script does not erase or restore database files.

After an approved local/host start:

```
python deploy/host/health.py --port 8100
```

Require database health, no degraded state, and configuration endpoints locked. Then separately verify public HTTPS/certificate, login, a real citation answer and backup restore. The public-app budget is still a partial quota slice, not verified dollar accounting (see docs/BUDGET.md).

## Verified scope

Tests cover generated plan permissions, unsafe config rejection, SQLite backup/readback, atomic local release selection and a real locked loopback server health check. systemd/Caddy service startup, certificate provisioning, a real public host, encrypted/off-host backup and production restore are pending. No deployment or registry publication occurred.
