#!/bin/bash
# scripts/collect-log-evidence.sh
# Purpose: Collect relevant log files based on error patterns, identifiers, and a time-targeted window.
#
# Usage:
#   ./collect-log-evidence.sh <log_dir> --event "YYYY-MM-DDTHH:MM:SS" [--window-seconds 300] [--identifiers "id1,id2"]
#   ./collect-log-evidence.sh <log_dir> --cleanup  # Remove extraction workspace
#
# Notes:
# - Targeted archive expansion: only archives whose *filename timestamp* falls within EVENT_TIME±WINDOW_SECONDS are expanded.
# - After matching (error patterns / identifiers), a second-stage mtime window filter is applied to reduce noise.
# - Fail fast if no target files remain after filtering.
#
# Dependencies:
# - required: python3
# - optional (for extraction): unzip, tar, gzip
# - optional (for better JSON match extraction when using rg): jq

set -euo pipefail

LOG_DIR="${1:-.}"
IDENTIFIERS=""
START_TIME=""
END_TIME=""
OUTPUT_FORMAT="json"
CLEANUP_ONLY=false

# Time targeting controls
# - We only expand archives whose filename timestamp falls within [event_time - window, event_time + window]
# - Default window is 300 seconds (5 minutes)
EVENT_TIME=""
WINDOW_SECONDS="300"

# Workspace for targeted extraction
WORK_DIR="${WORK_DIR:-.triage_work}"
UNPACK_DIR="$WORK_DIR/unpacked"

# Parse arguments
shift || true
while [[ $# -gt 0 ]]; do
  case $1 in
    --identifiers)
      IDENTIFIERS="$2"
      shift 2
      ;;
    --start)
      echo "WARNING: --start is deprecated and ignored. Use --event + --window-seconds instead." >&2
      START_TIME="$2"
      shift 2
      ;;
    --end)
      echo "WARNING: --end is deprecated and ignored. Use --event + --window-seconds instead." >&2
      END_TIME="$2"
      shift 2
      ;;
    --format)
      OUTPUT_FORMAT="$2"
      shift 2
      ;;
    --event)
      EVENT_TIME="$2"
      shift 2
      ;;
    --window-seconds)
      WINDOW_SECONDS="$2"
      shift 2
      ;;
    --cleanup)
      CLEANUP_ONLY=true
      shift
      ;;
    *)
      shift
      ;;
  esac
done

if [[ "$CLEANUP_ONLY" == "true" ]]; then
  if [[ -d "$WORK_DIR" ]]; then
    rm -rf "$WORK_DIR"
    echo "Cleaned up extraction workspace: $WORK_DIR" >&2
    exit 0
  else
    echo "No extraction workspace found at: $WORK_DIR" >&2
    exit 0
  fi
fi

# Error patterns to search
ERROR_PATTERNS="error|exception|failed|timeout|panic|fatal|critical"

# --- Step 0: targeted archive expansion ---
# Only run when EVENT_TIME is provided.
# We select archives by parsing timestamps from filenames and checking whether they fall within
# [EVENT_TIME - WINDOW_SECONDS, EVENT_TIME + WINDOW_SECONDS].
if [[ -n "$EVENT_TIME" ]]; then
  mkdir -p "$UNPACK_DIR"

  # Find candidate archives
  ARCHIVES=()
  while IFS= read -r -d '' archive; do
    ARCHIVES+=("$archive")
  done < <(find "$LOG_DIR" -type f \( -name "*.zip" -o -name "*.tar" -o -name "*.tgz" -o -name "*.tar.gz" -o -name "*.gz" \) -print0 2>/dev/null)

  if [[ ${#ARCHIVES[@]} -gt 0 ]]; then
    # Use python to decide which archives match the event time window based on filename timestamps.
    # Output: one archive path per line.
    MATCHED_ARCHIVES=()
    while IFS= read -r archive; do
      [[ -n "$archive" ]] && MATCHED_ARCHIVES+=("$archive")
    done < <(EVENT_TIME="$EVENT_TIME" WINDOW_SECONDS="$WINDOW_SECONDS" python3 - <<'PY'
import os, re, sys
from datetime import datetime, timedelta

event = os.environ.get('EVENT_TIME','').strip()
window_s = int(os.environ.get('WINDOW_SECONDS','300') or '300')

# Accept ISO-like: 2026-02-03T16:00:00 or 2026-02-03 16:00:00
# Also accept minute precision.
def parse_iso(s: str) -> datetime:
    s = s.strip().replace(' ', 'T')
    fmts = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"]
    for f in fmts:
        try:
            return datetime.strptime(s, f)
        except ValueError:
            pass
    raise ValueError(f"Unsupported time format: {s}")

event_dt = parse_iso(event)
start_dt = event_dt - timedelta(seconds=window_s)
end_dt = event_dt + timedelta(seconds=window_s)

# Heuristic timestamp extraction from filename.
# We intentionally support multiple readable patterns; if a filename has a readable time, we try to parse it.
# Supported examples:
#   log-2026-0203-1620.zip            -> 2026-02-03 16:20
#   app_20260203_1620.tar.gz          -> 2026-02-03 16:20
#   svc-2026-02-03-16-20-30.tgz       -> 2026-02-03 16:20:30
#   2026-02-03T16-20-30_error.zip     -> 2026-02-03 16:20:30
patterns = [
    # 2026-02-03-16-20-30 or 2026_02_03_16_20_30
    (re.compile(r"(?P<Y>20\d{2})[-_](?P<M>\d{2})[-_](?P<D>\d{2})[-_T](?P<h>\d{2})[-_](?P<m>\d{2})[-_](?P<s>\d{2})"), True),
    # 2026-02-03-16-20 (no seconds)
    (re.compile(r"(?P<Y>20\d{2})[-_](?P<M>\d{2})[-_](?P<D>\d{2})[-_T](?P<h>\d{2})[-_](?P<m>\d{2})"), False),
    # log-2026-0203-1620 (YYYY-MMDD-HHMM)
    (re.compile(r"(?P<Y>20\d{2})[-_](?P<M>\d{2})(?P<D>\d{2})[-_](?P<h>\d{2})(?P<m>\d{2})"), False),
    # 20260203_1620 or 20260203-1620
    (re.compile(r"(?P<Y>20\d{2})(?P<M>\d{2})(?P<D>\d{2})[-_](?P<h>\d{2})(?P<m>\d{2})"), False),
]

def extract_dt(name: str):
    for p, has_s in patterns:
        m = p.search(name)
        if not m:
            continue
        try:
            s = int(m.group('s')) if has_s else 0
            return datetime(
                int(m.group('Y')),
                int(m.group('M')),
                int(m.group('D')),
                int(m.group('h')),
                int(m.group('m')),
                s,
            )
        except Exception:
            return None
    return None

matched = []
for line in sys.stdin:
    path = line.strip()
    if not path:
        continue
    dt = extract_dt(os.path.basename(path))
    if not dt:
        continue
    if start_dt <= dt <= end_dt:
        matched.append((dt, path))

# Sort by closeness to event time (most relevant first)
matched.sort(key=lambda x: abs((x[0] - event_dt).total_seconds()))
for _, p in matched:
    print(p)
PY
    <<<"$(printf '%s\n' "${ARCHIVES[@]}")")

    if [[ ${#MATCHED_ARCHIVES[@]} -eq 0 ]]; then
      echo "WARNING: No archives matched EVENT_TIME±WINDOW_SECONDS based on filename timestamps." >&2
      echo "WARNING: Falling back to all archives under $LOG_DIR so relevant evidence is not missed." >&2
      MATCHED_ARCHIVES=("${ARCHIVES[@]}")
    fi

    # Extract matched archives into UNPACK_DIR (per-archive subdir)
    for a in "${MATCHED_ARCHIVES[@]}"; do
      base=$(basename "$a")
      out="$UNPACK_DIR/$base"
      mkdir -p "$out"

      if [[ "$a" == *.zip ]]; then
        command -v unzip >/dev/null 2>&1 || { echo "ERROR: unzip not found (needed for $a)" >&2; exit 3; }
        unzip -o -q "$a" -d "$out" || true
      elif [[ "$a" == *.tar.gz || "$a" == *.tgz || "$a" == *.tar ]]; then
        command -v tar >/dev/null 2>&1 || { echo "ERROR: tar not found (needed for $a)" >&2; exit 3; }
        tar -xf "$a" -C "$out" || true
      elif [[ "$a" == *.gz ]]; then
        command -v gzip >/dev/null 2>&1 || { echo "ERROR: gzip not found (needed for $a)" >&2; exit 3; }
        fname=$(basename "$a" .gz)
        gzip -cd "$a" > "$out/$fname" || true
      fi
    done

    LOG_DIRS_TO_SEARCH=("$LOG_DIR" "$UNPACK_DIR")
  else
    LOG_DIRS_TO_SEARCH=("$LOG_DIR")
  fi
else
  LOG_DIRS_TO_SEARCH=("$LOG_DIR")
fi

(
  set +o pipefail

  echo "{"

  # Step 1: Survey directory structure
  echo '  "directory_survey": ['
  # Survey both original and unpacked dirs
  for d in "${LOG_DIRS_TO_SEARCH[@]}"; do
    find "$d" -type f \( -name "*.log" -o -name "*.txt" -o -name "*.json" \) 2>/dev/null | \
      head -100 | \
      while IFS= read -r file; do
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
        mtime=$(stat -f%m "$file" 2>/dev/null || stat -c%Y "$file" 2>/dev/null || echo "0")
        echo "    {\"path\": \"$file\", \"size\": $size, \"mtime\": $mtime},"
      done
  done | sed '$ s/,$//'
  echo "  ],"
)

# Step 2: Search for error patterns
(
  set +o pipefail

  echo '  "error_matches": ['
  if command -v rg &> /dev/null; then
    for d in "${LOG_DIRS_TO_SEARCH[@]}"; do
      rg -i -n --json "$ERROR_PATTERNS" "$d" 2>/dev/null | \
        head -200 | \
        jq -c 'select(.type == "match") | {path: .data.path.text, line: .data.line_number, content: .data.lines.text}' 2>/dev/null || true
    done | sed 's/$/,/' | sed '$ s/,$//'
  else
    mkdir -p "$WORK_DIR"
    : > "$WORK_DIR/error_matches.json"
    for d in "${LOG_DIRS_TO_SEARCH[@]}"; do
      grep -r -i -n -E "$ERROR_PATTERNS" "$d" 2>/dev/null | \
        head -200 | \
        while IFS=: read -r file line content; do
          content_escaped=$(printf '%s' "$content" | head -c 500 | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g; s/\r/\\r/g; s/\n/\\n/g')
          printf '    {"path": "%s", "line": %s, "content": "%s"}\n' "$file" "$line" "$content_escaped"
        done
    done >> "$WORK_DIR/error_matches.json"
    cat "$WORK_DIR/error_matches.json" | sed 's/$/,/' | sed '$ s/,$//'
  fi
  echo "  ],"
)

# Step 3: Search for identifiers
(
  set +o pipefail

  echo '  "identifier_matches": ['
  if [[ -n "$IDENTIFIERS" ]]; then
    mkdir -p "$WORK_DIR"
    : > "$WORK_DIR/identifier_matches.json"
    IFS=',' read -ra ID_ARRAY <<< "$IDENTIFIERS"
    for id in "${ID_ARRAY[@]}"; do
      if command -v rg &> /dev/null; then
        for d in "${LOG_DIRS_TO_SEARCH[@]}"; do
          rg -n --json "$id" "$d" 2>/dev/null | \
            head -50 | \
            jq -c 'select(.type == "match") | {identifier: "'"$id"'", path: .data.path.text, line: .data.line_number}' 2>/dev/null || true
        done >> "$WORK_DIR/identifier_matches.json"
      else
        for d in "${LOG_DIRS_TO_SEARCH[@]}"; do
          grep -r -n "$id" "$d" 2>/dev/null | \
            head -50 | \
            while IFS=: read -r file line content; do
              printf '    {"identifier": "%s", "path": "%s", "line": %s}\n' "$id" "$file" "$line"
            done || true
        done >> "$WORK_DIR/identifier_matches.json"
      fi
    done
    # Emit valid JSON with proper comma handling
    cat "$WORK_DIR/identifier_matches.json" | sed 's/$/,/' | sed '$ s/,$//'
  fi
  echo "  ],"
)

# Step 4: Generate selected files list
echo '  "selected_files": ['
selected_count=0
mkdir -p "$WORK_DIR"
: > "$WORK_DIR/selected_files.json"
{
  # Files with errors
  if command -v rg &> /dev/null; then
    for d in "${LOG_DIRS_TO_SEARCH[@]}"; do
      rg -i -l "$ERROR_PATTERNS" "$d" 2>/dev/null || true
    done
  else
    for d in "${LOG_DIRS_TO_SEARCH[@]}"; do
      grep -r -i -l -E "$ERROR_PATTERNS" "$d" 2>/dev/null || true
    done
  fi

  # Files with identifiers
  if [[ -n "$IDENTIFIERS" ]]; then
    IFS=',' read -ra ID_ARRAY <<< "$IDENTIFIERS"
    for id in "${ID_ARRAY[@]}"; do
      for d in "${LOG_DIRS_TO_SEARCH[@]}"; do
        if command -v rg &> /dev/null; then
          rg -l "$id" "$d" 2>/dev/null || true
        else
          grep -r -l "$id" "$d" 2>/dev/null || true
        fi
      done
    done
  fi
} | sort -u >"$WORK_DIR/selected_candidates.txt"

while IFS= read -r file; do
  [[ -z "$file" ]] && continue

  # Optional: second-stage time window filter by file mtime around EVENT_TIME
  if [[ -n "$EVENT_TIME" ]]; then
    if ! CANDIDATE_FILE="$file" EVENT_TIME="$EVENT_TIME" WINDOW_SECONDS="$WINDOW_SECONDS" python3 - <<'PY' >/dev/null 2>&1; then
import os, sys
from datetime import datetime, timedelta

path = os.environ.get('CANDIDATE_FILE', '')
event = os.environ.get('EVENT_TIME', '').strip()
window_s = int(os.environ.get('WINDOW_SECONDS', '300') or '300')

def parse_iso(s: str) -> datetime:
    s = s.strip().replace(' ', 'T')
    fmts = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"]
    for f in fmts:
        try:
            return datetime.strptime(s, f)
        except ValueError:
            pass
    raise ValueError

event_dt = parse_iso(event)
start_dt = event_dt - timedelta(seconds=window_s)
end_dt = event_dt + timedelta(seconds=window_s)

try:
    st = os.stat(path)
except FileNotFoundError:
    sys.exit(1)

mtime = datetime.fromtimestamp(st.st_mtime)
if start_dt <= mtime <= end_dt:
    sys.exit(0)
else:
    sys.exit(2)
PY
      continue
    fi
  fi

  selected_count=$((selected_count+1))
  echo "    {\"path\": \"$file\", \"reason\": \"contains error pattern or identifier\"}," >> "$WORK_DIR/selected_files.json"
done <"$WORK_DIR/selected_candidates.txt"

cat "$WORK_DIR/selected_files.json" | sed '$ s/,$//'
echo "  ],"

# Fail fast if nothing selected (after second-stage filter)
if [[ $selected_count -eq 0 ]]; then
  echo "ERROR: No target files selected after applying match + mtime window filters." >&2
  echo "Hint: check --event/--window-seconds, identifiers, and whether logs exist in the selected time window." >&2
  exit 4
fi

# Step 5: Excluded files (large files, binary, irrelevant extensions)
echo '  "excluded_files": ['
find "$LOG_DIR" -type f \( -size +100M -o -name "*.gz" -o -name "*.zip" -o -name "*.tar" \) 2>/dev/null | \
  while IFS= read -r file; do
    echo "    {\"path\": \"$file\", \"reason\": \"large or compressed file (may be expanded if time window matches)\"},"
  done | sed '$ s/,$//'
echo "  ]"

echo "}"
