#!/bin/sh
# Run from a clone: sh install.sh [installer options]. No sudo, no Git required.
set -eu
UV=$(command -v uv || true)
if [ -z "$UV" ] && [ -x "$HOME/.local/bin/uv" ]; then UV="$HOME/.local/bin/uv"; fi
if [ -z "$UV" ]; then
  echo 'Installing uv from its official installer.'
  tmp=$(mktemp)
  trap 'rm -f "$tmp"' EXIT HUP INT TERM
  if command -v curl >/dev/null 2>&1; then curl -fLsS https://astral.sh/uv/install.sh -o "$tmp"
  elif command -v wget >/dev/null 2>&1; then wget -q https://astral.sh/uv/install.sh -O "$tmp"
  else echo 'Need curl or wget to download uv. No changes made.' >&2; exit 1; fi
  UV_INSTALL_DIR="$HOME/.local/bin" UV_NO_MODIFY_PATH=1 sh "$tmp"
  UV="$HOME/.local/bin/uv"
  [ -x "$UV" ] || { echo 'uv install not found; inspect installer output.' >&2; exit 1; }
else echo 'uv already installed; skipped.'; fi
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SHARED="$ROOT/scripts/install.py"
if [ ! -f "$SHARED" ]; then
  SHARED=$(mktemp)
  if command -v curl >/dev/null 2>&1; then curl -fLsS https://raw.githubusercontent.com/Harsh23Kashyap/customchat/main/scripts/install.py -o "$SHARED"
  elif command -v wget >/dev/null 2>&1; then wget -q https://raw.githubusercontent.com/Harsh23Kashyap/customchat/main/scripts/install.py -O "$SHARED"
  else echo 'Need curl or wget to download the installer.' >&2; exit 1; fi
  trap 'rm -f "$SHARED"' EXIT HUP INT TERM
fi
for arg in "$@"; do [ "$arg" != '--offline' ] || export UV_OFFLINE=1; done
"$UV" run --no-project --python 3.12 "$SHARED" --uv "$UV" "$@"
