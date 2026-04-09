#!/usr/bin/env bash
# test-start-bugfix.sh — Unit tests for start-bugfix.sh
#
# Usage: bash skills/cmiotsdk-start-bugflow/tests/test-start-bugfix.sh
#
# Creates temporary git repos, runs the script under various conditions,
# and reports pass/fail for each case. Cleans up after itself.

set -euo pipefail

# ── Test framework ───────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_UNDER_TEST="$SCRIPT_DIR/scripts/start-bugfix.sh"

PASS=0
FAIL=0
TMPDIR_BASE=""

setup_tmpdir() {
  TMPDIR_BASE="$(mktemp -d)"
}

cleanup() {
  if [[ -n "$TMPDIR_BASE" && -d "$TMPDIR_BASE" ]]; then
    rm -rf "$TMPDIR_BASE"
  fi
}
trap cleanup EXIT

pass() { PASS=$((PASS + 1)); printf '  ✅ %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  ❌ %s\n' "$1"; }

# Create a fake "cmiotsdk" repo with origin/develop
# Each call gets a unique bare repo to avoid collisions.
BARE_COUNTER=0
create_cmiotsdk_repo() {
  local repo_dir="$1"
  BARE_COUNTER=$((BARE_COUNTER + 1))
  local bare_dir="$TMPDIR_BASE/bare-cmiotsdk-${BARE_COUNTER}.git"

  # Create bare remote with 'cmiotsdk' in the path (for URL matching)
  git init --bare "$bare_dir" >/dev/null 2>&1

  # Create working repo
  git init "$repo_dir" >/dev/null 2>&1
  git -C "$repo_dir" remote add origin "$bare_dir"

  # Create initial commit on develop and push
  git -C "$repo_dir" checkout -b develop >/dev/null 2>&1
  echo "init" > "$repo_dir/README.md"
  git -C "$repo_dir" add . >/dev/null 2>&1
  git -C "$repo_dir" commit -m "initial" >/dev/null 2>&1
  git -C "$repo_dir" push -u origin develop >/dev/null 2>&1

  # Fetch so origin/develop exists
  git -C "$repo_dir" fetch origin >/dev/null 2>&1
}

# Create a repo whose remote URL does NOT contain 'cmiotsdk'
create_other_repo() {
  local repo_dir="$1"
  local bare_dir="$TMPDIR_BASE/bare-other-project.git"

  git init --bare "$bare_dir" >/dev/null 2>&1
  git init "$repo_dir" >/dev/null 2>&1
  git -C "$repo_dir" remote add origin "$bare_dir"
  git -C "$repo_dir" checkout -b main >/dev/null 2>&1
  echo "init" > "$repo_dir/README.md"
  git -C "$repo_dir" add . >/dev/null 2>&1
  git -C "$repo_dir" commit -m "initial" >/dev/null 2>&1
}

# ── Tests ────────────────────────────────────────────────────────────────────

echo ""
echo "🧪 Testing start-bugfix.sh"
echo "   Script: $SCRIPT_UNDER_TEST"
echo ""

setup_tmpdir

# ── Test 1: Happy path — create bugfix branch ────────────────────────────────

echo "─── Test 1: Happy path"

REPO1="$TMPDIR_BASE/test1-cmiotsdk"
create_cmiotsdk_repo "$REPO1"

output=$(cd "$REPO1" && bash "$SCRIPT_UNDER_TEST" "OMMUSIC-3397323" 2>&1) || true
branch=$(git -C "$REPO1" branch --show-current 2>/dev/null)

if [[ "$branch" == "bugfix/OMMUSIC-3397323" ]]; then
  pass "Branch created: $branch"
else
  fail "Expected bugfix/OMMUSIC-3397323, got: $branch"
  echo "     Output: $output"
fi

# ── Test 2: Invalid ticket ID format ─────────────────────────────────────────

echo "─── Test 2: Invalid ticket ID format"

REPO2="$TMPDIR_BASE/test2-cmiotsdk"
create_cmiotsdk_repo "$REPO2"

output=$(cd "$REPO2" && bash "$SCRIPT_UNDER_TEST" "fix-audio-bug" 2>&1) && rc=0 || rc=$?

if [[ $rc -ne 0 && "$output" == *"Invalid ticket ID format"* ]]; then
  pass "Rejected invalid ticket ID"
else
  fail "Should have rejected 'fix-audio-bug'"
  echo "     rc=$rc output: $output"
fi

# ── Test 3: No argument ──────────────────────────────────────────────────────

echo "─── Test 3: No argument"

REPO3="$TMPDIR_BASE/test3-cmiotsdk"
create_cmiotsdk_repo "$REPO3"

output=$(cd "$REPO3" && bash "$SCRIPT_UNDER_TEST" 2>&1) && rc=0 || rc=$?

if [[ $rc -ne 0 && "$output" == *"Usage:"* ]]; then
  pass "Showed usage on missing argument"
else
  fail "Should have shown usage"
  echo "     rc=$rc output: $output"
fi

# ── Test 4: Wrong repository ─────────────────────────────────────────────────

echo "─── Test 4: Wrong repository"

REPO4="$TMPDIR_BASE/test4-other"
create_other_repo "$REPO4"

output=$(cd "$REPO4" && bash "$SCRIPT_UNDER_TEST" "OMMUSIC-1234" 2>&1) && rc=0 || rc=$?

if [[ $rc -ne 0 && "$output" == *"cmiotsdk only"* ]]; then
  pass "Rejected non-cmiotsdk repo"
else
  fail "Should have rejected non-cmiotsdk repo"
  echo "     rc=$rc output: $output"
fi

# ── Test 5: Dirty working tree ───────────────────────────────────────────────

echo "─── Test 5: Dirty working tree"

REPO5="$TMPDIR_BASE/test5-cmiotsdk"
create_cmiotsdk_repo "$REPO5"

# Make dirty
echo "dirty" >> "$REPO5/README.md"

output=$(cd "$REPO5" && bash "$SCRIPT_UNDER_TEST" "OMMUSIC-5555" 2>&1) && rc=0 || rc=$?

if [[ $rc -ne 0 && "$output" == *"uncommitted changes"* ]]; then
  pass "Aborted on dirty tree"
else
  fail "Should have aborted on dirty tree"
  echo "     rc=$rc output: $output"
fi

# ── Test 6: Detached HEAD ────────────────────────────────────────────────────

echo "─── Test 6: Detached HEAD"

REPO6="$TMPDIR_BASE/test6-cmiotsdk"
create_cmiotsdk_repo "$REPO6"
git -C "$REPO6" checkout --detach HEAD >/dev/null 2>&1

output=$(cd "$REPO6" && bash "$SCRIPT_UNDER_TEST" "OMMUSIC-6666" 2>&1) && rc=0 || rc=$?

if [[ $rc -ne 0 && "$output" == *"detached HEAD"* ]]; then
  pass "Aborted on detached HEAD"
else
  fail "Should have aborted on detached HEAD"
  echo "     rc=$rc output: $output"
fi

# ── Test 7: Different bugfix branch conflict ─────────────────────────────────

echo "─── Test 7: Different bugfix branch conflict"

REPO7="$TMPDIR_BASE/test7-cmiotsdk"
create_cmiotsdk_repo "$REPO7"

# Create and switch to a different bugfix branch
git -C "$REPO7" checkout -b "bugfix/OMMUSIC-1111111" >/dev/null 2>&1

output=$(cd "$REPO7" && bash "$SCRIPT_UNDER_TEST" "OMMUSIC-7777" 2>&1) && rc=0 || rc=$?

if [[ $rc -ne 0 && "$output" == *"bugfix/OMMUSIC-1111111"* ]]; then
  pass "Aborted due to conflicting bugfix branch"
else
  fail "Should have aborted due to different bugfix branch"
  echo "     rc=$rc output: $output"
fi

# ── Test 8: Branch already exists (non-destructive reuse) ────────────────────

echo "─── Test 8: Branch already exists"

REPO8="$TMPDIR_BASE/test8-cmiotsdk"
create_cmiotsdk_repo "$REPO8"

# Pre-create the branch, then switch away
git -C "$REPO8" checkout -b "bugfix/OMMUSIC-8888" >/dev/null 2>&1
git -C "$REPO8" checkout develop >/dev/null 2>&1

output=$(cd "$REPO8" && bash "$SCRIPT_UNDER_TEST" "OMMUSIC-8888" 2>&1) || true
branch=$(git -C "$REPO8" branch --show-current 2>/dev/null)

if [[ "$branch" == "bugfix/OMMUSIC-8888" && "$output" == *"already exists"* ]]; then
  pass "Switched to existing branch non-destructively"
else
  fail "Should have switched to existing branch"
  echo "     branch=$branch output: $output"
fi

# ── Test 9: Not in a git repo ────────────────────────────────────────────────

echo "─── Test 9: Not in a git repo"

REPO9="$TMPDIR_BASE/test9-nongit"
mkdir -p "$REPO9"

output=$(cd "$REPO9" && bash "$SCRIPT_UNDER_TEST" "OMMUSIC-9999" 2>&1) && rc=0 || rc=$?

if [[ $rc -ne 0 && "$output" == *"Not inside a git repository"* ]]; then
  pass "Aborted outside git repo"
else
  fail "Should have aborted outside git repo"
  echo "     rc=$rc output: $output"
fi

# ── Summary ──────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════"
printf "  Results: %d passed, %d failed\n" "$PASS" "$FAIL"
echo "═══════════════════════════════════════"
echo ""

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
