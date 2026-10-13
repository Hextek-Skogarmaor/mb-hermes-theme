#!/usr/bin/env bash
# Install the Mora Bygg theme into Hermes Desktop.
#
#   ./install.sh            build from the Mora Bygg Design folder, then install
#   ./install.sh --prebuilt install dist/plugin.js as-is (no Design folder needed)
#
# The plugin folder is staged in full, then moved into place in one step.
# Hermes Desktop watches the plugins root; a folder that appears before its
# plugin.js can be missed (no load, no error toast).
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
ROOT="$HERMES_HOME/desktop-plugins"
TARGET="$ROOT/mora-bygg-theme"

if [[ "${1:-}" != "--prebuilt" ]]; then
  python3 -I "$REPO/build.py"
fi

[[ -s "$REPO/dist/plugin.js" ]] || { echo "dist/plugin.js missing — run without --prebuilt" >&2; exit 1; }

mkdir -p "$ROOT"

if [[ -f "$TARGET/plugin.js" ]]; then
  # Already loaded: an in-place write hot-reloads it.
  cp "$REPO/dist/plugin.js" "$TARGET/plugin.js.tmp"
  mv "$TARGET/plugin.js.tmp" "$TARGET/plugin.js"
  echo "updated $TARGET/plugin.js (hot-reload)"
else
  STAGE="$(mktemp -d "${TMPDIR:-/tmp}/mora-bygg-theme.XXXXXX")"
  mkdir "$STAGE/mora-bygg-theme"
  cp "$REPO/dist/plugin.js" "$STAGE/mora-bygg-theme/plugin.js"
  rm -rf "$TARGET"
  mv "$STAGE/mora-bygg-theme" "$TARGET"
  rmdir "$STAGE"
  echo "installed $TARGET"
fi
