#!/usr/bin/env bash
# One-push publish to an EXISTING EC2 box. It never creates AWS resources.
# Usage:  deploy/publish.sh            show the plan only (default, changes nothing)
#         deploy/publish.sh --yes      do it
# Settings come from deploy/publish.env (copy deploy/publish.env.example). No secrets are kept in this repo.
set -euo pipefail
cd "$(dirname "$0")/.."
ENV_FILE="${PUBLISH_ENV:-deploy/publish.env}"
[ -f "$ENV_FILE" ] || { echo "Missing $ENV_FILE. Copy deploy/publish.env.example to it and fill it in."; exit 1; }
# shellcheck disable=SC1090
. "$ENV_FILE"
: "${EC2_HOST:?set EC2_HOST}" "${EC2_USER:=ubuntu}" "${SSH_KEY:?set SSH_KEY}" "${APP_DIR:=/opt/customchat}"
S3_BACKUP="${S3_BACKUP:-}"
APP_DATA_DIR="${APP_DATA_DIR:-$APP_DIR/apps/dietchat/data}"
SSH="ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new $EC2_USER@$EC2_HOST"
echo "Plan:"
echo "  1. Check tests pass here"
echo "  2. Copy this folder to $EC2_USER@$EC2_HOST:$APP_DIR (not data/, .venv, .git, publish.env)"
echo "  3. On the box: restart the customchat service (it installs anything missing on start)"
echo "  4. Wait for /api/health"
[ -n "$S3_BACKUP" ] && echo "  Before copying: back up $APP_DATA_DIR to $S3_BACKUP (local files only, not MySQL)"
if [ "${1:-}" != "--yes" ]; then echo; echo "Dry run only. Add --yes to run."; exit 0; fi
python3 -m unittest discover -s tests >/dev/null
if [ -n "$S3_BACKUP" ]; then
  $SSH "test -d '$APP_DATA_DIR' && aws s3 sync '$APP_DATA_DIR' '$S3_BACKUP'/\$(date +%Y%m%d-%H%M%S)/ --only-show-errors"
fi
rsync -az --delete -e "ssh -i $SSH_KEY" --exclude data --exclude .venv --exclude .git --exclude 'deploy/publish.env' ./ "$EC2_USER@$EC2_HOST:$APP_DIR/"
$SSH "cd $APP_DIR && sudo systemctl restart customchat"
for i in $(seq 1 20); do
  if $SSH "curl -fs http://127.0.0.1:8100/api/health" >/dev/null 2>&1; then echo "Healthy."; exit 0; fi
  sleep 3
done
echo "App did not report healthy. Check: sudo journalctl -u customchat -n 50"; exit 1
