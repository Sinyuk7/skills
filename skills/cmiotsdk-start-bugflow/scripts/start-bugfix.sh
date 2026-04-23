#!/usr/bin/env bash
# start-bugfix.sh — Stable execution entry for the cmiotsdk bugfix bootstrap.
#
# Usage: bash start-bugfix.sh <TICKET-ID>
# Example: bash start-bugfix.sh OMMUSIC-3397323
#
# This wrapper resolves the skill-local script directory, then delegates to the
# implementation script so workflow docs can keep a stable entry point.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMPL_SCRIPT="$SCRIPT_DIR/start-bugfix-impl.sh"

if [[ ! -f "$IMPL_SCRIPT" ]]; then
  printf '❌ Missing implementation script: %s\n' "$IMPL_SCRIPT" >&2
  exit 1
fi

exec bash "$IMPL_SCRIPT" "$@"
