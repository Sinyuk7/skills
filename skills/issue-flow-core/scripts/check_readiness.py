#!/usr/bin/env python3
"""
Lightweight readiness checker for issue-flow case boundaries.

Validates objective conditions for stage transitions:
- Required artifacts exist
- Required references resolve
- Lifecycle transition is compatible with status.yaml
- Terminal states have recorded outcomes and explicit verification state
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Tuple

import yaml


VALID_ACTIONS = {"resolve", "collect", "external", "none", "blocked"}
LEGACY_ACTIONS = {
    "external_handoff": "external",
    "close_as_non_actionable": "none",
}
VALID_VERIFICATION_STATUSES = {"verified", "partial", "unavailable"}
BOUNDARY_TARGETS = {
    "collect_ready": "collected",
    "handoff_ready": "handoff_ready",
    "resolve_ready": "resolve_in_progress",
    "close_ready": "closed",
}


class ReadinessChecker:
    """Validates case readiness at stage boundaries."""

    def __init__(self, case_path: str):
        self.case_path = Path(case_path).resolve()
        self.case_id = self.case_path.name
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.status = None
        self.repo_root = self._infer_repo_root()

    def check_boundary(self, boundary: str) -> Tuple[bool, List[str], List[str]]:
        """Check readiness for a specific boundary."""
        self.errors = []
        self.warnings = []
        self.status = self._load_yaml(self.case_path / "status.yaml", "status.yaml", required=True)

        self._check_boundary_lifecycle(boundary)

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
        sources_data = self._load_yaml(self.case_path / "sources.yaml", "sources.yaml", required=True)
        if not sources_data:
            return

        sources = sources_data.get("sources") or []
        issue_sources = [source for source in sources if source.get("origin") == "issue_material"]
        if not issue_sources:
            self.errors.append("sources.yaml must include at least one issue_material source")
            return

        for source in issue_sources:
            source_id = source.get("id", "<unknown>")
            collected = source.get("collected")
            if not collected:
                self.errors.append(f"Source '{source_id}' is missing a collected decision")
                continue

            if collected == "skipped":
                if not source.get("note"):
                    self.errors.append(f"Skipped source '{source_id}' must record why it was skipped")
                continue

            if not str(collected).startswith("curated/"):
                self.errors.append(
                    f"Collected source '{source_id}' must point into curated/, got: {collected}"
                )
                continue

            curated_path = self.case_path / collected
            if not curated_path.exists():
                self.errors.append(f"Missing curated material for '{source_id}': {collected}")

    def _check_handoff_ready(self):
        """Validate handoff_ready boundary."""
        investigation_root = self._parse_xml(
            self.case_path / "analysis" / "investigation.xml",
            "analysis/investigation.xml",
            expected_root="investigation",
            required_sections=["evidence_refs", "confirmed", "inferred", "open_questions", "details"],
        )
        if investigation_root is not None:
            self._check_case_id(investigation_root, "analysis/investigation.xml")
            self._check_investigation_refs(investigation_root)

        handoff_root = self._parse_xml(
            self.case_path / "analysis" / "handoff.xml",
            "analysis/handoff.xml",
            expected_root="handoff",
            required_sections=["summary", "code_context", "known"],
        )
        if handoff_root is not None:
            self._check_case_id(handoff_root, "analysis/handoff.xml")
            self._check_handoff_refs(handoff_root)

        self._load_next_step(required=True)

    def _check_resolve_ready(self):
        """Validate resolve_ready boundary."""
        handoff_root = self._parse_xml(
            self.case_path / "analysis" / "handoff.xml",
            "analysis/handoff.xml",
            expected_root="handoff",
            required_sections=["summary", "code_context", "known"],
        )
        if handoff_root is not None:
            self._check_case_id(handoff_root, "analysis/handoff.xml")

        next_step = self._load_next_step(required=True)
        if not next_step:
            return

        action = next_step.get("_normalized_action")
        if action != "resolve":
            self.errors.append(
                "analysis/next-step.yaml must set recommended_action: resolve before entering resolve"
            )

    def _check_close_ready(self):
        """Validate close_ready boundary."""
        next_step = self._load_next_step(required=True)
        if not next_step:
            return

        action = next_step.get("_normalized_action")
        verification_status = next_step.get("verification_status")

        if action not in {"none", "external"}:
            self.errors.append(
                "analysis/next-step.yaml must set recommended_action to none or external before closing"
            )

        if verification_status not in VALID_VERIFICATION_STATUSES:
            self.errors.append(
                "analysis/next-step.yaml must record verification_status as verified, partial, or unavailable before closing"
            )

        resolution_root = self._parse_xml(
            self.case_path / "resolve" / "resolution.xml",
            "resolve/resolution.xml",
            expected_root="resolution",
            required_sections=["summary", "outcome", "delivery", "verification"],
            required=False,
        )

        if resolution_root is not None:
            self._check_case_id(resolution_root, "resolve/resolution.xml")
            self._check_resolution_refs(resolution_root)
            return

        handoff_root = self._parse_xml(
            self.case_path / "analysis" / "handoff.xml",
            "analysis/handoff.xml",
            expected_root="handoff",
            required_sections=["summary", "code_context", "known"],
            required=True,
        )
        if handoff_root is not None:
            self._check_case_id(handoff_root, "analysis/handoff.xml")

    def _check_boundary_lifecycle(self, boundary: str):
        """Ensure the current lifecycle can legally reach the requested boundary."""
        if not self.status:
            return

        lifecycle = self.status.get("lifecycle")
        if not lifecycle:
            self.errors.append("status.yaml is missing lifecycle")
            return

        target_state = BOUNDARY_TARGETS.get(boundary)
        if not target_state or lifecycle == target_state:
            return

        valid, transition_errors = self.check_lifecycle_transition(lifecycle, target_state)
        if not valid:
            self.errors.extend(
                f"Lifecycle in status.yaml is not compatible with {boundary}: {message}"
                for message in transition_errors
            )

    def _load_next_step(self, required: bool) -> Optional[dict]:
        """Load and validate next-step.yaml."""
        next_step = self._load_yaml(
            self.case_path / "analysis" / "next-step.yaml",
            "analysis/next-step.yaml",
            required=required,
        )
        if not next_step:
            return None

        action = next_step.get("recommended_action")
        if not action:
            self.errors.append("analysis/next-step.yaml is missing recommended_action")
            return next_step

        normalized = LEGACY_ACTIONS.get(action, action)
        if action in LEGACY_ACTIONS:
            self.warnings.append(
                f"analysis/next-step.yaml uses legacy action '{action}'; prefer '{normalized}'"
            )

        if normalized not in VALID_ACTIONS:
            self.errors.append(
                "analysis/next-step.yaml has unsupported recommended_action: "
                f"{action} (expected one of {', '.join(sorted(VALID_ACTIONS))})"
            )
            return next_step

        next_step["_normalized_action"] = normalized
        return next_step

    def _check_investigation_refs(self, root: ET.Element):
        """Check that investigation references resolve."""
        evidence_refs = root.find("evidence_refs")
        if evidence_refs is None:
            return

        for material in evidence_refs.findall("issue_material"):
            path = material.get("path")
            if not path:
                self.errors.append("analysis/investigation.xml issue_material ref is missing path")
                continue
            if not path.startswith("curated/"):
                self.errors.append(
                    f"analysis/investigation.xml issue_material ref must point into curated/: {path}"
                )
            if not (self.case_path / path).exists():
                self.errors.append(
                    f"analysis/investigation.xml references missing curated material: {path}"
                )

        for repository_ref in evidence_refs.findall("repository_ref"):
            ref_type = repository_ref.get("type")
            path = repository_ref.get("path")
            file_path = self._resolve_repo_reference(
                path,
                f"analysis/investigation.xml repository_ref ({ref_type or 'unknown'})",
            )
            if file_path is None:
                continue

            if ref_type == "symbol":
                self._validate_symbol_reference(
                    file_path,
                    repository_ref.get("symbol"),
                    repository_ref.get("line"),
                    "analysis/investigation.xml repository_ref",
                )
            elif ref_type == "line_range":
                self._validate_line_range(
                    file_path,
                    repository_ref.get("start"),
                    repository_ref.get("end"),
                    "analysis/investigation.xml repository_ref",
                )

    def _check_handoff_refs(self, root: ET.Element):
        """Check that handoff references resolve."""
        investigation_ref = root.findtext("investigation_ref")
        if not investigation_ref:
            self.errors.append("analysis/handoff.xml is missing investigation_ref")
        elif not (self.case_path / investigation_ref).exists():
            self.errors.append(f"analysis/handoff.xml references missing file: {investigation_ref}")

        issue_context_ref = root.findtext("issue_context_ref")
        if issue_context_ref:
            issue_context_path = self._resolve_repo_reference(
                issue_context_ref,
                "analysis/handoff.xml issue_context_ref",
            )
            if issue_context_path is None:
                self.errors.append(
                    f"analysis/handoff.xml references missing project context: {issue_context_ref}"
                )

        code_context = root.find("code_context")
        if code_context is None:
            return

        for file_node in code_context.findall("./affected_files/file"):
            self._resolve_repo_reference(
                file_node.get("path"),
                "analysis/handoff.xml affected_files/file",
            )

        for symbol_node in code_context.findall("./key_symbols/symbol"):
            file_path = self._resolve_repo_reference(
                symbol_node.get("path"),
                "analysis/handoff.xml key_symbols/symbol",
            )
            if file_path is None:
                continue
            self._validate_symbol_reference(
                file_path,
                symbol_node.get("name"),
                symbol_node.get("line"),
                "analysis/handoff.xml key_symbols/symbol",
            )

        for section_node in code_context.findall("./critical_sections/section"):
            file_path = self._resolve_repo_reference(
                section_node.get("path"),
                "analysis/handoff.xml critical_sections/section",
            )
            if file_path is None:
                continue
            self._validate_line_range(
                file_path,
                section_node.get("start"),
                section_node.get("end"),
                "analysis/handoff.xml critical_sections/section",
            )

    def _check_resolution_refs(self, root: ET.Element):
        """Check that resolution references and verification state resolve."""
        outcome = root.find("outcome")
        if outcome is None or not outcome.get("type"):
            self.errors.append("resolve/resolution.xml must include outcome type")

        verification = root.find("verification")
        if verification is None:
            return

        verification_status = verification.get("status")
        if verification_status not in VALID_VERIFICATION_STATUSES:
            self.errors.append(
                "resolve/resolution.xml verification status must be verified, partial, or unavailable"
            )

        verification_ref = verification.findtext("verification_ref")
        if not verification_ref:
            self.errors.append("resolve/resolution.xml is missing verification_ref")
        elif not (self.case_path / verification_ref).exists():
            self.errors.append(f"resolve/resolution.xml references missing file: {verification_ref}")

        handoff_ref = root.findtext("handoff_ref")
        if not handoff_ref:
            self.errors.append("resolve/resolution.xml is missing handoff_ref")
        elif not (self.case_path / handoff_ref).exists():
            self.errors.append(f"resolve/resolution.xml references missing file: {handoff_ref}")

    def _parse_xml(
        self,
        path: Path,
        label: str,
        expected_root: str,
        required_sections: List[str],
        required: bool = True,
    ) -> Optional[ET.Element]:
        """Parse an XML file and validate its basic structure."""
        if not path.exists():
            if required:
                self.errors.append(f"Missing {label}")
            return None

        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            self.errors.append(f"{label} parse error: {exc}")
            return None

        if root.tag != expected_root:
            self.errors.append(f"{label} must use root <{expected_root}>, found <{root.tag}>")

        for section in required_sections:
            if root.find(section) is None:
                self.errors.append(f"{label} is missing required section: {section}")

        return root

    def _check_case_id(self, root: ET.Element, label: str):
        """Ensure the artifact case-id matches the case directory name."""
        case_id = root.get("case-id")
        if case_id and case_id != self.case_id:
            self.errors.append(
                f"{label} case-id '{case_id}' does not match case directory '{self.case_id}'"
            )

    def _load_yaml(self, path: Path, label: str, required: bool) -> Optional[dict]:
        """Load a YAML file safely."""
        if not path.exists():
            if required:
                self.errors.append(f"Missing {label}")
            return None

        try:
            with open(path, encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except yaml.YAMLError as exc:
            self.errors.append(f"{label} parse error: {exc}")
            return None

        if not isinstance(data, dict):
            self.errors.append(f"{label} must contain a YAML mapping")
            return None

        return data

    def _infer_repo_root(self) -> Optional[Path]:
        """Infer the repository root from a case path under .issue-flow/cases/."""
        for ancestor in [self.case_path, *self.case_path.parents]:
            if ancestor.name == ".issue-flow":
                return ancestor.parent
        return None

    def _resolve_repo_reference(self, ref_path: Optional[str], label: str) -> Optional[Path]:
        """Resolve a repository-relative reference and ensure it stays inside the repo root."""
        if not ref_path:
            self.errors.append(f"{label} is missing path")
            return None

        if self.repo_root is None:
            self.errors.append(
                f"{label} cannot be resolved because the case path is not inside .issue-flow/"
            )
            return None

        candidate = (self.repo_root / ref_path).resolve()
        try:
            candidate.relative_to(self.repo_root.resolve())
        except ValueError:
            self.errors.append(f"{label} points outside the repository root: {ref_path}")
            return None

        if not candidate.exists():
            self.errors.append(f"{label} references missing repository path: {ref_path}")
            return None

        return candidate

    def _validate_symbol_reference(
        self,
        file_path: Path,
        symbol_name: Optional[str],
        line_value: Optional[str],
        label: str,
    ):
        """Validate a repository symbol reference."""
        if not symbol_name:
            self.errors.append(f"{label} is missing symbol/name")
            return

        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if symbol_name not in text:
            self.errors.append(f"{label} symbol '{symbol_name}' was not found in {file_path}")
            return

        if line_value is not None:
            line_number = self._parse_line_number(line_value, label)
            if line_number is None:
                return
            total_lines = self._count_lines(file_path)
            if line_number > total_lines:
                self.errors.append(
                    f"{label} line {line_number} exceeds file length {total_lines} in {file_path}"
                )

    def _validate_line_range(
        self,
        file_path: Path,
        start_value: Optional[str],
        end_value: Optional[str],
        label: str,
    ):
        """Validate a repository line range reference."""
        start = self._parse_line_number(start_value, f"{label} start")
        end = self._parse_line_number(end_value, f"{label} end")
        if start is None or end is None:
            return

        if start > end:
            self.errors.append(f"{label} has invalid line range: {start} > {end}")
            return

        total_lines = self._count_lines(file_path)
        if end > total_lines:
            self.errors.append(
                f"{label} line range {start}-{end} exceeds file length {total_lines} in {file_path}"
            )

    def _parse_line_number(self, raw_value: Optional[str], label: str) -> Optional[int]:
        """Parse a positive integer line number."""
        if raw_value is None:
            self.errors.append(f"{label} is missing line information")
            return None

        try:
            number = int(raw_value)
        except (TypeError, ValueError):
            self.errors.append(f"{label} must be an integer, got: {raw_value}")
            return None

        if number < 1:
            self.errors.append(f"{label} must be >= 1, got: {raw_value}")
            return None

        return number

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a repository file."""
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        return max(1, len(text.splitlines()))
    
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
