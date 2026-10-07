#!/bin/sh
# Bootstrap uv, then run CustomChat in uvx's isolated tool environment.
set -eu
UV=$(command -v uv || true)
if [ -z "$UV" ] && [ -x "$HOME/.local/bin/uv" ]; then UV="$HOME/.local/bin/uv"; fi
if [ -z "$UV" ]; then
  echo 'Installing uv from its official installer (no sudo).'
  tmp=$(mktemp)
  trap 'rm -f "$tmp"' EXIT HUP INT TERM
  if command -v curl >/dev/null 2>&1; then curl -fLsS https://astral.sh/uv/install.sh -o "$tmp"
  elif command -v wget >/dev/null 2>&1; then wget -q https://astral.sh/uv/install.sh -O "$tmp"
  else echo 'Need curl or wget and internet to download uv.' >&2; exit 1; fi
  UV_INSTALL_DIR="$HOME/.local/bin" UV_NO_MODIFY_PATH=1 sh "$tmp"
  UV="$HOME/.local/bin/uv"
  [ -x "$UV" ] || { echo 'uv install failed; inspect the message above.' >&2; exit 1; }
fi
# uv tool run is uvx. Archive source works without Git until the PyPI release.
SOURCE=${CUSTOMCHAT_INSTALL_SOURCE:-https://github.com/Harsh23Kashyap/customchat/archive/refs/heads/main.zip}
unset PYTHONPATH PYTHONHOME
exec "$UV" tool run --python 3.12 --from "$SOURCE" customchat start "$@"
