#!/bin/bash
# scripts/collect-log-evidence.sh
# Purpose: Collect relevant log files based on error patterns, identifiers, and time window
# Usage: ./collect-log-evidence.sh <log_dir> [--identifiers "id1,id2"] [--start "2024-01-15T10:00:00"] [--end "2024-01-15T12:00:00"]

set -euo pipefail

LOG_DIR="${1:-.}"
IDENTIFIERS=""
START_TIME=""
END_TIME=""
OUTPUT_FORMAT="json"

# Parse arguments
shift || true
while [[ $# -gt 0 ]]; do
  case $1 in
    --identifiers)
      IDENTIFIERS="$2"
      shift 2
      ;;
    --start)
      START_TIME="$2"
      shift 2
      ;;
    --end)
      END_TIME="$2"
      shift 2
      ;;
    --format)
      OUTPUT_FORMAT="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

# Error patterns to search
ERROR_PATTERNS="error|exception|failed|timeout|panic|fatal|critical"

# Output JSON structure
echo "{"
echo '  "search_params": {'
echo "    \"log_dir\": \"$LOG_DIR\","
echo "    \"identifiers\": \"$IDENTIFIERS\","
echo "    \"start_time\": \"$START_TIME\","
echo "    \"end_time\": \"$END_TIME\""
echo "  },"

# Step 1: Survey directory structure
echo '  "directory_survey": ['
find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.txt" -o -name "*.json" \) 2>/dev/null | \
  head -100 | \
  while IFS= read -r file; do
    size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
    mtime=$(stat -f%m "$file" 2>/dev/null || stat -c%Y "$file" 2>/dev/null || echo "0")
    echo "    {\"path\": \"$file\", \"size\": $size, \"mtime\": $mtime},"
  done | sed '$ s/,$//'
echo "  ],"

# Step 2: Search for error patterns
echo '  "error_matches": ['
if command -v rg &> /dev/null; then
  rg -i -n --json "$ERROR_PATTERNS" "$LOG_DIR" 2>/dev/null | \
    head -200 | \
    jq -c 'select(.type == "match") | {path: .data.path.text, line: .data.line_number, content: .data.lines.text}' 2>/dev/null | \
    sed 's/$/,/' | sed '$ s/,$//' || true
else
  grep -r -i -n -E "$ERROR_PATTERNS" "$LOG_DIR" 2>/dev/null | \
    head -200 | \
    while IFS=: read -r file line content; do
      echo "    {\"path\": \"$file\", \"line\": $line, \"content\": \"$(echo "$content" | sed 's/"/\\"/g' | head -c 500)\"},"
    done | sed '$ s/,$//' || true
fi
echo "  ],"

# Step 3: Search for identifiers
echo '  "identifier_matches": ['
if [[ -n "$IDENTIFIERS" ]]; then
  IFS=',' read -ra ID_ARRAY <<< "$IDENTIFIERS"
  for id in "${ID_ARRAY[@]}"; do
    if command -v rg &> /dev/null; then
      rg -n --json "$id" "$LOG_DIR" 2>/dev/null | \
        head -50 | \
        jq -c 'select(.type == "match") | {identifier: "'"$id"'", path: .data.path.text, line: .data.line_number}' 2>/dev/null || true
    else
      grep -r -n "$id" "$LOG_DIR" 2>/dev/null | \
        head -50 | \
        while IFS=: read -r file line content; do
          echo "    {\"identifier\": \"$id\", \"path\": \"$file\", \"line\": $line},"
        done || true
    fi
  done | sed '$ s/,$//'
fi
echo "  ],"

# Step 4: Generate selected files list
echo '  "selected_files": ['
{
  # Files with errors
  if command -v rg &> /dev/null; then
    rg -i -l "$ERROR_PATTERNS" "$LOG_DIR" 2>/dev/null
  else
    grep -r -i -l -E "$ERROR_PATTERNS" "$LOG_DIR" 2>/dev/null
  fi
  
  # Files with identifiers
  if [[ -n "$IDENTIFIERS" ]]; then
    IFS=',' read -ra ID_ARRAY <<< "$IDENTIFIERS"
    for id in "${ID_ARRAY[@]}"; do
      if command -v rg &> /dev/null; then
        rg -l "$id" "$LOG_DIR" 2>/dev/null
      else
        grep -r -l "$id" "$LOG_DIR" 2>/dev/null
      fi
    done
  fi
} | sort -u | while IFS= read -r file; do
  echo "    {\"path\": \"$file\", \"reason\": \"contains error pattern or identifier\"},"
done | sed '$ s/,$//'
echo "  ],"

# Step 5: Excluded files (large files, binary, irrelevant extensions)
echo '  "excluded_files": ['
find "$LOG_DIR" -type f \( -size +100M -o -name "*.gz" -o -name "*.zip" -o -name "*.tar" \) 2>/dev/null | \
  while IFS= read -r file; do
    echo "    {\"path\": \"$file\", \"reason\": \"large or compressed file\"},"
  done | sed '$ s/,$//'
echo "  ]"

echo "}"
