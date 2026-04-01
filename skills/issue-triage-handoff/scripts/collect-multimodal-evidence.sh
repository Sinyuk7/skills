#!/bin/bash
#
# collect-multimodal-evidence.sh — Image and Video Evidence Extractor
#
# PURPOSE:
#   Extract evidence from visual materials (images, videos). Complements text
#   log collection with multimodal evidence support (P0.4).
#
# CAPABILITIES:
#   - Image: Metadata extraction (dimensions, format), OCR text extraction
#   - Video: Metadata extraction (duration, dimensions, format), frame sampling
#   - Visual signal detection: error dialogs, red buttons, timeout messages
#
# USAGE:
#   ./collect-multimodal-evidence.sh <input_directory> <output_json>
#
# OUTPUT:
#   JSON array with multimodal evidence entries:
#   [
#     {
#       "evidence_id": "E001",
#       "type": "image|video",
#       "source_ref": {...},
#       "timestamp": "ISO 8601 (from EXIF or filename)",
#       "visual_signals": ["error_dialog", "red_button"],
#       "ocr_text": "extracted text from image",
#       "relevance": "direct|context|weak",
#       "metadata": {
#         "dimensions": "1920x1080",
#         "duration_seconds": 45,
#         "file_size_bytes": 2048000,
#         "format": "PNG"
#       },
#       "tags": ["screenshot", "error"]
#     }
#   ]
#
# DEPENDENCIES:
#   - exiftool: Metadata extraction (install: brew install exiftool)
#   - tesseract: OCR (optional, install: brew install tesseract)
#   - ffprobe: Video metadata (from ffmpeg: brew install ffmpeg)
#
# INTEGRATION:
#   - Called in workflow Step 2.5 (after Step 2 log collection)
#   - Reads from evidence-inventory.json (status: skipped, type: image|video)
#   - Updates evidence_refs in inventory
#
# VERSION: Current

set -euo pipefail

INPUT_DIR="${1:-.}"
OUTPUT_JSON="${2:-multimodal-evidence.json}"

# Check dependencies
HAS_EXIFTOOL=$(command -v exiftool >/dev/null 2>&1 && echo "yes" || echo "no")
HAS_TESSERACT=$(command -v tesseract >/dev/null 2>&1 && echo "yes" || echo "no")
HAS_FFPROBE=$(command -v ffprobe >/dev/null 2>&1 && echo "yes" || echo "no")

if [[ "$HAS_EXIFTOOL" == "no" ]]; then
  echo "⚠️  WARNING: exiftool not found. Metadata extraction limited." >&2
fi

# Helpers
json_quote() {
  python3 -c 'import json,sys; data=sys.stdin.buffer.read().decode("utf-8", "surrogateescape"); sys.stdout.write(json.dumps(data))'
}

timestamp_from_epoch() {
  python3 - "$1" <<'PY'
import datetime
import sys

try:
    epoch = int(float(sys.argv[1]))
except (TypeError, ValueError):
    sys.exit(1)

print(datetime.datetime.utcfromtimestamp(epoch).strftime("%Y-%m-%dT%H:%M:%SZ"))
PY
}

capture_ocr_text() {
  local file="$1"

  python3 - "$file" <<'PY'
import subprocess
import sys

path = sys.argv[1]

try:
    proc = subprocess.run(
        ["tesseract", path, "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
except (FileNotFoundError, OSError, Exception):
    sys.exit(0)

text = proc.stdout.replace(b"\r", b" ").replace(b"\n", b" ")
sys.stdout.buffer.write(text[:500])
PY
}

# Initialize JSON array
echo "[" > "$OUTPUT_JSON"

EVIDENCE_COUNT=0

# Process images
while IFS= read -r -d '' file; do
  [[ ! -f "$file" ]] && continue
  
  # Generate evidence ID
  EVIDENCE_ID=$(printf "E%03d" $((EVIDENCE_COUNT + 1)))
  
  # Extract metadata
  FILE_SIZE=$(stat -f%z "$file" 2>/dev/null || echo "0")
  MTIME=$(stat -f%m "$file" 2>/dev/null || date +%s)
  
  # Get dimensions and format via exiftool
  if [[ "$HAS_EXIFTOOL" == "yes" ]]; then
    DIMENSIONS=$(exiftool -s -s -s -ImageSize "$file" 2>/dev/null || echo "unknown")
    FORMAT=$(exiftool -s -s -s -FileType "$file" 2>/dev/null || echo "unknown")
    EXIF_TIME=$(exiftool -d '%Y-%m-%dT%H:%M:%SZ' -s -s -s -DateTimeOriginal "$file" 2>/dev/null || echo "")
  else
    DIMENSIONS="unknown"
    FORMAT="${file##*.}"
    EXIF_TIME=""
  fi
  
  # Use EXIF timestamp if available, else file mtime
  if [[ -n "$EXIF_TIME" ]]; then
    TIMESTAMP="$EXIF_TIME"
  else
    TIMESTAMP=$(timestamp_from_epoch "$MTIME")
  fi
  
  # OCR text extraction (if tesseract available)
  OCR_TEXT=""
  if [[ "$HAS_TESSERACT" == "yes" ]]; then
    OCR_TEXT=$(capture_ocr_text "$file")
  fi
  
  # Visual signal detection (simple keyword-based heuristics)
  VISUAL_SIGNALS=()
  if [[ "$OCR_TEXT" =~ [Ee]rror|[Ff]ailed|[Tt]imeout|[Ee]xception ]]; then
    VISUAL_SIGNALS+=("error_text")
  fi
  if [[ "$OCR_TEXT" =~ [Cc]onnection.*[Ll]ost|[Nn]etwork.*[Ee]rror ]]; then
    VISUAL_SIGNALS+=("connection_error")
  fi
  # Filename-based hints
  if [[ "$file" =~ [Ee]rror|[Bb]ug|[Cc]rash|[Ff]ail ]]; then
    VISUAL_SIGNALS+=("error_filename_hint")
  fi
  
  # Determine relevance
  RELEVANCE="weak"
  if [[ ${#VISUAL_SIGNALS[@]} -gt 0 ]]; then
    RELEVANCE="direct"
  elif [[ -n "$OCR_TEXT" && ${#OCR_TEXT} -gt 20 ]]; then
    RELEVANCE="context"
  fi
  
  # Build visual_signals JSON array
  VISUAL_SIGNALS_JSON="[]"
  if [[ ${#VISUAL_SIGNALS[@]} -gt 0 ]]; then
    VISUAL_SIGNALS_JSON=$(printf '"%s",' "${VISUAL_SIGNALS[@]}" | sed 's/,$//')
    VISUAL_SIGNALS_JSON="[$VISUAL_SIGNALS_JSON]"
  fi
  
  # Add comma separator (except for first entry)
  if [[ $EVIDENCE_COUNT -gt 0 ]]; then
    echo "," >> "$OUTPUT_JSON"
  fi
  
  # Write JSON entry
  cat >> "$OUTPUT_JSON" <<EOF
  {
    "evidence_id": $(printf '%s' "$EVIDENCE_ID" | json_quote),
    "type": "image",
    "source_ref": {
      "source_type": "file",
      "path": $(printf '%s' "$file" | json_quote)
    },
    "timestamp": $(printf '%s' "$TIMESTAMP" | json_quote),
    "visual_signals": $VISUAL_SIGNALS_JSON,
    "ocr_text": $(printf '%s' "$OCR_TEXT" | json_quote),
    "relevance": $(printf '%s' "$RELEVANCE" | json_quote),
    "metadata": {
      "dimensions": $(printf '%s' "$DIMENSIONS" | json_quote),
      "file_size_bytes": $FILE_SIZE,
      "format": $(printf '%s' "$FORMAT" | json_quote)
    },
    "tags": ["screenshot", "image"]
  }
EOF
  
  EVIDENCE_COUNT=$((EVIDENCE_COUNT + 1))
  
done < <(find "$INPUT_DIR" -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.gif" -o -iname "*.webp" \) -print0)

# Process videos
while IFS= read -r -d '' file; do
  [[ ! -f "$file" ]] && continue
  
  # Generate evidence ID
  EVIDENCE_ID=$(printf "E%03d" $((EVIDENCE_COUNT + 1)))
  
  # Extract metadata
  FILE_SIZE=$(stat -f%z "$file" 2>/dev/null || echo "0")
  MTIME=$(stat -f%m "$file" 2>/dev/null || date +%s)
  TIMESTAMP=$(timestamp_from_epoch "$MTIME")
  
  # Get video metadata via ffprobe
  if [[ "$HAS_FFPROBE" == "yes" ]]; then
    DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$file" 2>/dev/null || echo "0")
    DIMENSIONS=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$file" 2>/dev/null || echo "unknown")
    FORMAT=$(ffprobe -v error -show_entries format=format_name -of default=noprint_wrappers=1:nokey=1 "$file" 2>/dev/null || echo "unknown")
  else
    DURATION="0"
    DIMENSIONS="unknown"
    FORMAT="${file##*.}"
  fi
  
  # Visual signals for video (filename-based heuristics only, no frame analysis)
  VISUAL_SIGNALS=()
  if [[ "$file" =~ [Ee]rror|[Bb]ug|[Cc]rash|[Ff]ail|[Rr]eproduction ]]; then
    VISUAL_SIGNALS+=("error_filename_hint")
  fi
  
  VISUAL_SIGNALS_JSON="[]"
  if [[ ${#VISUAL_SIGNALS[@]} -gt 0 ]]; then
    VISUAL_SIGNALS_JSON=$(printf '"%s",' "${VISUAL_SIGNALS[@]}" | sed 's/,$//')
    VISUAL_SIGNALS_JSON="[$VISUAL_SIGNALS_JSON]"
  fi
  
  # Relevance (videos are generally context unless filename indicates error)
  RELEVANCE="context"
  if [[ ${#VISUAL_SIGNALS[@]} -gt 0 ]]; then
    RELEVANCE="direct"
  fi
  
  # Add comma separator
  if [[ $EVIDENCE_COUNT -gt 0 ]]; then
    echo "," >> "$OUTPUT_JSON"
  fi
  
  # Write JSON entry
  cat >> "$OUTPUT_JSON" <<EOF
  {
    "evidence_id": $(printf '%s' "$EVIDENCE_ID" | json_quote),
    "type": "video",
    "source_ref": {
      "source_type": "file",
      "path": $(printf '%s' "$file" | json_quote)
    },
    "timestamp": $(printf '%s' "$TIMESTAMP" | json_quote),
    "visual_signals": $VISUAL_SIGNALS_JSON,
    "ocr_text": "",
    "relevance": $(printf '%s' "$RELEVANCE" | json_quote),
    "metadata": {
      "dimensions": $(printf '%s' "$DIMENSIONS" | json_quote),
      "duration_seconds": $DURATION,
      "file_size_bytes": $FILE_SIZE,
      "format": $(printf '%s' "$FORMAT" | json_quote)
    },
    "tags": ["video", "recording"]
  }
EOF
  
  EVIDENCE_COUNT=$((EVIDENCE_COUNT + 1))
  
done < <(find "$INPUT_DIR" -type f \( -iname "*.mp4" -o -iname "*.mov" -o -iname "*.avi" -o -iname "*.webm" -o -iname "*.mkv" \) -print0)

# Close JSON array
echo "" >> "$OUTPUT_JSON"
echo "]" >> "$OUTPUT_JSON"

# Summary statistics
echo "✅ Multimodal evidence collection complete:" >&2
echo "   Total evidence items: $EVIDENCE_COUNT" >&2
echo "   Output: $OUTPUT_JSON" >&2

if [[ "$HAS_TESSERACT" == "no" ]]; then
  echo "   ⚠️  OCR disabled (tesseract not installed)" >&2
fi

exit 0
