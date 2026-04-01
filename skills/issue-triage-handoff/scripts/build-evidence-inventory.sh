#!/bin/bash
#
# build-evidence-inventory.sh — Universal Evidence File Scanner
#
# PURPOSE:
#   Mandatory inventory stage for triage workflow. Scans ALL files in input
#   directory and records each file with status (parsed|skipped|failed) and reason.
#   Prevents silent file skipping and ensures comprehensive evidence collection.
#
# USAGE:
#   ./build-evidence-inventory.sh <input_directory> <output_json>
#
# OUTPUT:
#   JSON array with inventory entries:
#   [
#     {
#       "file_path": "string",
#       "type": "text|image|video|document|unknown",
#       "size_bytes": number,
#       "mtime": unix_timestamp,
#       "status": "parsed|skipped|failed",
#       "reason": "why not parsed (empty if parsed)",
#       "evidence_refs": []
#     }
#   ]
#
# INTEGRATION:
#   - Called in workflow Step 0.5 (before Material Intake)
#   - Feeds into collect-log-evidence.sh and collect-multimodal-evidence.sh
#   - Validates: inventory_size == input_file_count
#
# VERSION: Current

set -euo pipefail

INPUT_DIR="${1:-.}"
OUTPUT_JSON="${2:-evidence-inventory.json}"

# Helpers
json_quote() {
  python3 -c 'import json,sys; data=sys.stdin.buffer.read().decode("utf-8", "surrogateescape"); sys.stdout.write(json.dumps(data))'
}

canonical_path() {
  python3 - "$1" <<'PY'
import os
import sys

print(os.path.realpath(os.path.abspath(sys.argv[1])))
PY
}

# Validation
if [[ ! -d "$INPUT_DIR" ]]; then
  echo "ERROR: Input directory does not exist: $INPUT_DIR" >&2
  exit 1
fi

INPUT_ABS=$(canonical_path "$INPUT_DIR")
OUTPUT_ABS=$(canonical_path "$OUTPUT_JSON")
TMP_JSON=$(mktemp "${TMPDIR:-/tmp}/evidence-inventory.XXXXXX.json")
trap 'rm -f "$TMP_JSON"' EXIT

mkdir -p "$(dirname "$OUTPUT_ABS")"

# Initialize JSON array in a temp file outside the scanned tree.
echo "[" > "$TMP_JSON"

# File counter
FILE_COUNT=0

# Scan all files recursively
while IFS= read -r -d '' file; do
  # Skip the output file itself if it already exists inside the tree.
  if [[ "$file" == "$OUTPUT_ABS" ]]; then
    continue
  fi

  # Extract file metadata
  SIZE_BYTES=$(stat -f%z "$file" 2>/dev/null || echo "0")
  MTIME=$(stat -f%m "$file" 2>/dev/null || echo "0")
  
  # Determine file type and status
  TYPE="unknown"
  STATUS="skipped"
  REASON=""
  
  # Get file extension (lowercase)
  EXT="${file##*.}"
  EXT=$(printf '%s' "$EXT" | tr '[:upper:]' '[:lower:]')
  
  case "$EXT" in
    # Text evidence (parseable)
    log|txt|json|jsonl|csv|md|yaml|yml)
      TYPE="text"
      STATUS="parsed"
      REASON=""
      ;;
    
    # Image evidence (requires multimodal support)
    png|jpg|jpeg|gif|webp|bmp|svg)
      TYPE="image"
      STATUS="skipped"
      REASON="Multimodal processing required"
      ;;
    
    # Video evidence (requires multimodal support)
    mp4|mov|avi|webm|mkv)
      TYPE="video"
      STATUS="skipped"
      REASON="Multimodal processing required"
      ;;
    
    # Document evidence (requires parser)
    pdf|doc|docx)
      TYPE="document"
      STATUS="skipped"
      REASON="Document parser not implemented"
      ;;
    
    # Binary/compressed (skip)
    zip|tar|gz|bz2|xz|rar|7z)
      TYPE="archive"
      STATUS="skipped"
      REASON="Archive extraction not supported"
      ;;
    
    # Unknown type
    *)
      TYPE="unknown"
      STATUS="skipped"
      REASON="Unsupported file type: .$EXT"
      ;;
  esac
  
  # Add comma separator (except for first entry)
  if [[ $FILE_COUNT -gt 0 ]]; then
    echo "," >> "$TMP_JSON"
  fi
  
  # Write JSON entry
  cat >> "$TMP_JSON" <<EOF
  {
    "file_path": $(printf '%s' "$file" | json_quote),
    "type": $(printf '%s' "$TYPE" | json_quote),
    "size_bytes": $SIZE_BYTES,
    "mtime": $MTIME,
    "status": $(printf '%s' "$STATUS" | json_quote),
    "reason": $(printf '%s' "$REASON" | json_quote),
    "evidence_refs": []
  }
EOF
  
  FILE_COUNT=$((FILE_COUNT + 1))
  
done < <(find "$INPUT_ABS" -type f -print0)

# Close JSON array
echo "" >> "$TMP_JSON"
echo "]" >> "$TMP_JSON"

# Summary statistics
PARSED_COUNT=$(grep -c '"status": "parsed"' "$TMP_JSON" || true)
SKIPPED_COUNT=$(grep -c '"status": "skipped"' "$TMP_JSON" || true)

mv "$TMP_JSON" "$OUTPUT_ABS"
trap - EXIT

echo "✅ Evidence inventory complete:" >&2
echo "   Total files: $FILE_COUNT" >&2
echo "   Parsed: $PARSED_COUNT" >&2
echo "   Skipped: $SKIPPED_COUNT" >&2
echo "   Output: $OUTPUT_ABS" >&2

# Validation: No silent skips
if [[ $FILE_COUNT -eq 0 ]]; then
  echo "⚠️  WARNING: No files found in $INPUT_DIR" >&2
  exit 1
fi

exit 0
