#!/usr/bin/env python3
"""
Lightweight readiness checker for issue-flow case boundaries.

Validates objective conditions for stage transitions:
- Required artifacts exist
- Required references resolve
- Lifecycle transition is compatible
- Terminal states have recorded outcomes
"""

import sys
import os
import yaml
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple


class ReadinessChecker:
    """Validates case readiness at stage boundaries."""
    
    def __init__(self, case_path: str):
        self.case_path = Path(case_path)
        self.case_id = self.case_path.name
        self.errors = []
        self.warnings = []
        
    def check_boundary(self, boundary: str) -> Tuple[bool, List[str], List[str]]:
        """
        Check readiness for a specific boundary.
        
        Args:
            boundary: collect_ready, handoff_ready, resolve_ready, close_ready
            
        Returns:
            (passed, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        if boundary == "collect_ready":
            self._check_collect_ready()
        elif boundary == "handoff_ready":
            self._check_handoff_ready()
        elif boundary == "resolve_ready":
            self._check_resolve_ready()
        elif boundary == "close_ready":
            self._check_close_ready()
        else:
            self.errors.append(f"Unknown boundary: {boundary}")
            
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _check_collect_ready(self):
        """Validate collect_ready boundary."""
        # sources.yaml must exist
        if not (self.case_path / "sources.yaml").exists():
            self.errors.append("Missing sources.yaml")
            return
            
        # Curated materials must exist for collected sources
        with open(self.case_path / "sources.yaml") as f:
            sources = yaml.safe_load(f)
            
        for source in sources.get("sources", []):
            if source.get("origin") == "issue_material":
                collected = source.get("collected")
                if collected and collected != "skipped":
                    curated_path = self.case_path / collected
                    if not curated_path.exists():
                        self.errors.append(f"Missing curated material: {collected}")
    
    def _check_handoff_ready(self):
        """Validate handoff_ready boundary."""
        # investigation.xml must exist
        if not (self.case_path / "analysis" / "investigation.xml").exists():
            self.errors.append("Missing analysis/investigation.xml")
            
        # handoff.xml must exist
        if not (self.case_path / "analysis" / "handoff.xml").exists():
            self.errors.append("Missing analysis/handoff.xml")
            
        # next-step.yaml must exist
        if not (self.case_path / "analysis" / "next-step.yaml").exists():
            self.errors.append("Missing analysis/next-step.yaml")
            
        # Validate investigation.xml references
        inv_path = self.case_path / "analysis" / "investigation.xml"
        if inv_path.exists():
            self._check_investigation_refs(inv_path)
            
        # Validate handoff.xml structure
        handoff_path = self.case_path / "analysis" / "handoff.xml"
        if handoff_path.exists():
            self._check_handoff_structure(handoff_path)
    
    def _check_resolve_ready(self):
        """Validate resolve_ready boundary."""
        # handoff.xml must exist
        if not (self.case_path / "analysis" / "handoff.xml").exists():
            self.errors.append("Missing analysis/handoff.xml - cannot enter resolve without handoff")
            
        # next-step.yaml should recommend resolution
        next_step_path = self.case_path / "analysis" / "next-step.yaml"
        if next_step_path.exists():
            with open(next_step_path) as f:
                next_step = yaml.safe_load(f)
            if next_step.get("recommended_action") != "resolve":
                self.warnings.append("next-step.yaml does not recommend 'resolve' action")
    
    def _check_close_ready(self):
        """Validate close_ready boundary."""
        status_path = self.case_path / "status.yaml"
        if not status_path.exists():
            self.errors.append("Missing status.yaml")
            return
            
        with open(status_path) as f:
            status = yaml.safe_load(f)
            
        lifecycle = status.get("lifecycle")
        
        # Must have resolution OR explicit non-resolution conclusion
        has_resolution = (self.case_path / "resolve" / "resolution.xml").exists()
        
        # Check if handoff exists with non-actionable conclusion
        handoff_exists = (self.case_path / "analysis" / "handoff.xml").exists()
        next_step_path = self.case_path / "analysis" / "next-step.yaml"
        
        if next_step_path.exists():
            with open(next_step_path) as f:
                next_step = yaml.safe_load(f)
            action = next_step.get("recommended_action")
            
            if action == "close_as_non_actionable" or action == "external_handoff":
                # Non-resolution conclusion is acceptable
                pass
            elif not has_resolution:
                self.errors.append("Case cannot close without resolution.xml or explicit non-resolution conclusion")
        else:
            if not has_resolution:
                self.errors.append("Case cannot close without resolution.xml or next-step.yaml with explicit conclusion")
    
    def _check_investigation_refs(self, inv_path: Path):
        """Check that investigation.xml references resolve to curated materials."""
        try:
            tree = ET.parse(inv_path)
            root = tree.getroot()
            
            for material in root.findall(".//evidence_refs/issue_material"):
                path = material.get("path")
                if path:
                    full_path = self.case_path / path
                    if not full_path.exists():
                        self.errors.append(f"investigation.xml references missing curated material: {path}")
        except ET.ParseError as e:
            self.errors.append(f"investigation.xml parse error: {e}")
    
    def _check_handoff_structure(self, handoff_path: Path):
        """Check that handoff.xml has required sections."""
        try:
            tree = ET.parse(handoff_path)
            root = tree.getroot()
            
            required_sections = ["summary", "code_context", "known"]
            for section in required_sections:
                if root.find(section) is None:
                    self.errors.append(f"handoff.xml missing required section: {section}")
        except ET.ParseError as e:
            self.errors.append(f"handoff.xml parse error: {e}")
    
    def check_lifecycle_transition(self, from_state: str, to_state: str) -> Tuple[bool, List[str]]:
        """Check if a lifecycle transition is valid."""
        errors = []
        
        valid_transitions = {
            "new": ["collecting"],
            "collecting": ["collected", "blocked"],
            "collected": ["handoff_in_progress", "blocked"],
            "handoff_in_progress": ["handoff_ready", "collecting", "blocked"],
            "handoff_ready": ["resolve_in_progress", "closed", "collecting", "blocked"],
            "resolve_in_progress": ["resolved_verified", "resolved_unverified", "blocked"],
            "resolved_verified": ["closed"],
            "resolved_unverified": ["closed"],
            "blocked": ["collecting", "handoff_in_progress", "resolve_in_progress"],
            "closed": ["collecting", "handoff_in_progress", "resolve_in_progress"],  # Reopen allowed
        }
        
        if from_state not in valid_transitions:
            errors.append(f"Unknown lifecycle state: {from_state}")
            return False, errors
            
        if to_state not in valid_transitions.get(from_state, []):
            errors.append(f"Invalid lifecycle transition: {from_state} -> {to_state}")
            return False, errors
            
        return True, []


def main():
    if len(sys.argv) < 3:
        print("Usage: check_readiness.py <case_path> <boundary>")
        print("Boundaries: collect_ready, handoff_ready, resolve_ready, close_ready")
        sys.exit(1)
        
    case_path = sys.argv[1]
    boundary = sys.argv[2]
    
    if not os.path.isdir(case_path):
        print(f"Error: Case path does not exist: {case_path}")
        sys.exit(1)
        
    checker = ReadinessChecker(case_path)
    passed, errors, warnings = checker.check_boundary(boundary)
    
    print(f"Readiness Check: {boundary}")
    print(f"Case: {checker.case_id}")
    print()
    
    if passed:
        print("✓ PASS")
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  - {warning}")
        sys.exit(0)
    else:
        print("✗ FAIL")
        print("\nBlocking Issues:")
        for error in errors:
            print(f"  - {error}")
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  - {warning}")
        sys.exit(1)


if __name__ == "__main__":
    main()
