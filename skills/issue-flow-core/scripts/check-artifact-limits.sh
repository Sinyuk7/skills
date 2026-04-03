#!/bin/bash
# Enforce maximum artifact counts per stage

if [ "$#" -ne 1 ]; then
  echo "Usage: check-artifact-limits.sh <case-dir>"
  exit 2
fi

case_dir="$1"

if [ ! -d "$case_dir" ]; then
  echo "❌ Case directory not found: $case_dir"
  exit 1
fi

errors=0

if [ -d "$case_dir/analysis" ]; then
  analysis_count=$(find "$case_dir/analysis" -maxdepth 1 -type f \( -name "*.xml" -o -name "*.yaml" -o -name "*.md" \) | wc -l | tr -d ' ')
  if [ "$analysis_count" -gt 2 ]; then
    echo "❌ Analysis stage has $analysis_count artifacts (max 2 allowed: investigation.xml, handoff.xml)"
    errors=$((errors + 1))
  fi
fi

if [ -d "$case_dir/resolve" ]; then
  resolve_count=$(find "$case_dir/resolve" -maxdepth 1 -type f | wc -l | tr -d ' ')
  if [ "$resolve_count" -gt 2 ]; then
    echo "❌ Resolve stage has $resolve_count artifacts (max 2 allowed: resolution.xml, verification.md)"
    errors=$((errors + 1))
  fi
fi

if [ "$errors" -gt 0 ]; then
  echo ""
  echo "Artifact count limits exceeded. Remove extra artifacts or run migration."
  exit 1
else
  echo "✓ Artifact count limits respected for $case_dir"
  exit 0
fi
