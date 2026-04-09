#!/usr/bin/env bash
# start-bugfix.sh — Create a bugfix branch from origin/develop for cmiotsdk.
#
# Usage: bash start-bugfix.sh <TICKET-ID>
# Example: bash start-bugfix.sh OMMUSIC-3397323
#
# Creates and switches to: bugfix/<TICKET-ID>
#
# Safety guarantees:
#   - Never reset --hard
#   - Never auto-stash
#   - Never modify existing branch history
#   - Aborts on dirty tree, wrong repo, detached HEAD, conflicting bugfix branch

set -euo pipefail

# ── Helpers ───────────────────────────────────────────────────────────────────

die()  { printf '❌ %s\n' "$*" >&2; exit 1; }
info() { printf '   %s\n' "$*"; }

# ── Argument validation ──────────────────────────────────────────────────────

TICKET_ID="${1:-}"

if [[ -z "$TICKET_ID" ]]; then
  die "Usage: start-bugfix.sh <TICKET-ID>  (e.g. OMMUSIC-3397323)"
fi

# Validate ticket ID format: UPPERCASE-DIGITS (e.g. OMMUSIC-3397323, BUG-123)
if [[ ! "$TICKET_ID" =~ ^[A-Z]+-[0-9]+$ ]]; then
  die "Invalid ticket ID format: '$TICKET_ID'. Expected pattern: PROJ-12345"
fi

# ── Repository validation ───────────────────────────────────────────────────

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" \
  || die "Not inside a git repository. Please cd into cmiotsdk first."

# Primary check: remote URL must contain 'cmiotsdk'
REMOTE_URL="$(git -C "$REPO_ROOT" remote get-url origin 2>/dev/null)" \
  || die "No 'origin' remote configured. Cannot verify repository identity."

if [[ "$REMOTE_URL" != *cmiotsdk* ]]; then
  die "This script is for cmiotsdk only.
   Current repo remote: $REMOTE_URL
   Use /issue-collect directly for other repos."
fi

BRANCH_NAME="bugfix/${TICKET_ID}"

# ── Pre-flight checks ───────────────────────────────────────────────────────

# Check for detached HEAD
if ! git -C "$REPO_ROOT" symbolic-ref -q HEAD >/dev/null 2>&1; then
  die "Repository is in detached HEAD state.
   Please checkout a branch first:
   git checkout develop"
fi

# Check if currently on a DIFFERENT bugfix branch (conflict guard)
CURRENT_BRANCH="$(git -C "$REPO_ROOT" branch --show-current 2>/dev/null || echo "")"

if [[ "$CURRENT_BRANCH" == bugfix/* && "$CURRENT_BRANCH" != "$BRANCH_NAME" ]]; then
  die "You are currently on branch '$CURRENT_BRANCH'.
   Please finish or switch off that branch before starting a new bugfix.
   git checkout develop    # to leave current bugfix"
fi

# Check if the target branch already exists locally
if git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
  echo "⚠️  Branch '${BRANCH_NAME}' already exists locally."
  echo "   Switching to it..."
  git -C "$REPO_ROOT" checkout "${BRANCH_NAME}"
  echo ""
  echo "✅ Now on existing branch: ${BRANCH_NAME}"
  git -C "$REPO_ROOT" log --oneline -3
  exit 0
fi

# Check for uncommitted changes (staged or unstaged)
if ! git -C "$REPO_ROOT" diff --quiet HEAD -- 2>/dev/null \
   || ! git -C "$REPO_ROOT" diff --cached --quiet HEAD -- 2>/dev/null; then
  die "You have uncommitted changes. Please commit or stash them first.
   git stash        # to stash changes
   git stash pop    # to restore later"
fi

# ── Main flow ────────────────────────────────────────────────────────────────

echo "🔄 Fetching origin..."
git -C "$REPO_ROOT" fetch origin \
  || die "Failed to fetch origin. Check your network connection."

# Verify origin/develop exists
git -C "$REPO_ROOT" rev-parse --verify origin/develop >/dev/null 2>&1 \
  || die "Remote branch 'origin/develop' not found. Is the remote configured correctly?"

echo "🌿 Creating branch '${BRANCH_NAME}' from origin/develop..."

# Create and switch to the new branch based on origin/develop
git -C "$REPO_ROOT" checkout -b "${BRANCH_NAME}" origin/develop \
  || die "Failed to create branch '${BRANCH_NAME}'."

echo ""
echo "✅ Bugfix branch ready."
echo ""
info "Repository: cmiotsdk"
info "Branch:     ${BRANCH_NAME}"
info "Base:       origin/develop ($(git -C "$REPO_ROOT" rev-parse --short origin/develop))"
