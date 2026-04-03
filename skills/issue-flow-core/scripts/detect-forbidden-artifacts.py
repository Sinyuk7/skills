#!/usr/bin/env python3
"""
Detect artifacts that should not exist in case directories.

Usage:
    python detect-forbidden-artifacts.py <case-dir>

Exit codes:
    0 - No invalid artifacts found
    1 - Invalid artifacts detected
"""

import os
import sys
from pathlib import Path


FORBIDDEN_ARTIFACTS = [
    "analysis/findings.xml",
    "analysis/evidence-pack.xml",
    "analysis/code-map.yaml",
    "analysis/next-step.yaml",
    "resolve/commits.yaml"
]


def check_case(case_dir):
    violations = []
    
    for forbidden in FORBIDDEN_ARTIFACTS:
        path = Path(case_dir) / forbidden
        if path.exists():
            violations.append(forbidden)
    
    return violations


def main():
    if len(sys.argv) != 2:
        print("Usage: detect-forbidden-artifacts.py <case-dir>")
        sys.exit(2)
    
    case_dir = sys.argv[1]
    
    if not os.path.isdir(case_dir):
        print(f"❌ Case directory not found: {case_dir}")
        sys.exit(1)
    
    violations = check_case(case_dir)
    
    if violations:
        print(f"⚠️  Found {len(violations)} invalid artifact(s) in {case_dir}:")
        for v in violations:
            print(f"  - {v}")
        print("\nThese artifacts should not exist in the minimal structure.")
        print("Remove them manually or check artifact-contracts.md for guidance.")
        sys.exit(1)
    else:
        print(f"✓ No forbidden artifacts in {case_dir}")
        sys.exit(0)


if __name__ == "__main__":
    main()
