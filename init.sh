#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required to sync skills." >&2
  echo "Install Node.js 18+ and rerun: npm run sync" >&2
  exit 127
fi

exec node "$SCRIPT_DIR/scripts/sync-skills.mjs" sync "$@"
