#!/bin/bash
# scripts/search-code-symbols.sh
# Purpose: Search for code symbols based on stacktraces, function names, class names, and routes
# Usage: ./search-code-symbols.sh <repo_dir> --symbols "func1,Class2" [--stacktrace "file.py:123,other.py:456"]

set -euo pipefail

REPO_DIR="${1:-.}"
SYMBOLS=""
STACKTRACE=""
ROUTES=""

# Parse arguments
shift || true
while [[ $# -gt 0 ]]; do
  case $1 in
    --symbols)
      SYMBOLS="$2"
      shift 2
      ;;
    --stacktrace)
      STACKTRACE="$2"
      shift 2
      ;;
    --routes)
      ROUTES="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

# Common code file extensions
CODE_EXTENSIONS="ts|tsx|js|jsx|py|java|go|rb|rs|cpp|c|h|cs|php|swift|kt"

echo "{"
echo '  "search_params": {'
echo "    \"repo_dir\": \"$REPO_DIR\","
echo "    \"symbols\": \"$SYMBOLS\","
echo "    \"stacktrace\": \"$STACKTRACE\","
echo "    \"routes\": \"$ROUTES\""
echo "  },"

# Step 1: Parse stacktrace and find exact locations
echo '  "stacktrace_matches": ['
if [[ -n "$STACKTRACE" ]]; then
  IFS=',' read -ra FRAMES <<< "$STACKTRACE"
  for frame in "${FRAMES[@]}"; do
    # Parse file:line format
    file=$(echo "$frame" | cut -d: -f1)
    line=$(echo "$frame" | cut -d: -f2)
    
    # Find the file in repo
    found_file=$(find "$REPO_DIR" -type f -name "$(basename "$file")" 2>/dev/null | head -1)
    
    if [[ -n "$found_file" ]]; then
      echo "    {"
      echo "      \"frame\": \"$frame\","
      echo "      \"resolved_path\": \"$found_file\","
      echo "      \"line\": $line,"
      echo "      \"match_type\": \"stacktrace\","
      echo "      \"confidence\": \"high\""
      echo "    },"
    fi
  done | sed '$ s/,$//'
fi
echo "  ],"

# Step 2: Search for symbol definitions
echo '  "symbol_matches": ['
if [[ -n "$SYMBOLS" ]]; then
  IFS=',' read -ra SYMBOL_ARRAY <<< "$SYMBOLS"
  for symbol in "${SYMBOL_ARRAY[@]}"; do
    # Trim whitespace
    symbol=$(echo "$symbol" | xargs)
    
    # Search for function/class definitions
    if command -v rg &> /dev/null; then
      # Python: def func, class Class
      # JavaScript/TypeScript: function func, class Class, const func =
      # Java/Go: func func, type Class
      rg -n --json \
        "(def $symbol|class $symbol|function $symbol|const $symbol|func $symbol|type $symbol|public.*$symbol|private.*$symbol)" \
        --type-add "code:*.{ts,tsx,js,jsx,py,java,go,rb,rs,cpp,c,h,cs,php,swift,kt}" \
        --type code \
        "$REPO_DIR" 2>/dev/null | \
        head -20 | \
        jq -c 'select(.type == "match") | {
          symbol: "'"$symbol"'",
          path: .data.path.text,
          line: .data.line_number,
          content: .data.lines.text,
          match_type: "symbol_search",
          confidence: "medium"
        }' 2>/dev/null || true
    else
      grep -r -n -E "(def $symbol|class $symbol|function $symbol|const $symbol)" \
        --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
        --include="*.py" --include="*.java" --include="*.go" \
        "$REPO_DIR" 2>/dev/null | \
        head -20 | \
        while IFS=: read -r file line content; do
          echo "    {\"symbol\": \"$symbol\", \"path\": \"$file\", \"line\": $line, \"match_type\": \"symbol_search\", \"confidence\": \"medium\"},"
        done || true
    fi
  done | sed '$ s/,$//'
fi
echo "  ],"

# Step 3: Search for route/endpoint handlers
echo '  "route_matches": ['
if [[ -n "$ROUTES" ]]; then
  IFS=',' read -ra ROUTE_ARRAY <<< "$ROUTES"
  for route in "${ROUTE_ARRAY[@]}"; do
    # Escape special characters for regex
    route_escaped=$(echo "$route" | sed 's/[[\.*^$()+?{|]/\\&/g')
    
    if command -v rg &> /dev/null; then
      # Common route patterns
      # Express: app.get('/path', router.post('/path'
      # NestJS: @Get('/path'), @Post('/path')
      # Flask: @app.route('/path'), @route('/path')
      # FastAPI: @router.get('/path')
      rg -n --json \
        "(@(Get|Post|Put|Delete|Patch)|app\.(get|post|put|delete)|router\.(get|post|put|delete)|@.*route).*['\"]$route_escaped['\"]" \
        --type-add "code:*.{ts,tsx,js,jsx,py,java,go,rb}" \
        --type code \
        "$REPO_DIR" 2>/dev/null | \
        head -10 | \
        jq -c 'select(.type == "match") | {
          route: "'"$route"'",
          path: .data.path.text,
          line: .data.line_number,
          content: .data.lines.text,
          match_type: "route_mapping",
          confidence: "medium"
        }' 2>/dev/null || true
    else
      grep -r -n -E "(Get|Post|Put|Delete|route).*['\"]$route_escaped['\"]" \
        --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.py" \
        "$REPO_DIR" 2>/dev/null | \
        head -10 | \
        while IFS=: read -r file line content; do
          echo "    {\"route\": \"$route\", \"path\": \"$file\", \"line\": $line, \"match_type\": \"route_mapping\", \"confidence\": \"medium\"},"
        done || true
    fi
  done | sed '$ s/,$//'
fi
echo "  ],"

# Step 4: Generate summary of all matches
echo '  "summary": {'
echo '    "total_stacktrace_matches": '$(echo "$STACKTRACE" | tr ',' '\n' | grep -c . || echo 0)','
echo '    "total_symbol_matches": '$(echo "$SYMBOLS" | tr ',' '\n' | grep -c . || echo 0)','
echo '    "total_route_matches": '$(echo "$ROUTES" | tr ',' '\n' | grep -c . || echo 0)
echo "  }"

echo "}"
