#!/usr/bin/env python3
"""
Validate that all handoff known items trace back to confirmed investigation facts.
BLOCKING: handoff-ready transition fails if validation fails.

Usage:
    python validate-traceability.py <case-dir>

Exit codes:
    0 - Validation passed
    1 - Validation failed
"""

import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path


def validate_case_traceability(case_dir):
    """Validate fact traceability from handoff to investigation."""
    investigation_path = Path(case_dir) / "analysis" / "investigation.xml"
    handoff_path = Path(case_dir) / "analysis" / "handoff.xml"
    
    errors = []
    warnings = []
    
    # Check if files exist
    if not investigation_path.exists():
        errors.append(f"Investigation file not found: {investigation_path}")
        return errors, warnings
    
    if not handoff_path.exists():
        errors.append(f"Handoff file not found: {handoff_path}")
        return errors, warnings
    
    try:
        # Parse investigation facts
        investigation = ET.parse(investigation_path)
        fact_ids = {fact.get('id') for fact in investigation.findall('.//confirmed/fact[@id]')}
        valid_ids = fact_ids
        
        # Parse handoff known items
        handoff = ET.parse(handoff_path)
        known_items = handoff.findall('.//known/item')
        
        if not known_items:
            warnings.append("Handoff has no <known> items (empty handoff)")
        
        for item in known_items:
            fact_ref = item.get('fact_ref')
            item_text = (item.text or "")[:50]
            
            if not fact_ref:
                errors.append(f"Known item missing fact_ref attribute: '{item_text}...'")
            elif fact_ref not in valid_ids:
                errors.append(
                    f"Known item references non-confirmed fact ID: {fact_ref} "
                    f"(item text: '{item_text}...')"
                )
        
        # Check that investigation has IDs
        facts_without_id = [f for f in investigation.findall('.//confirmed/fact') if f.get('id') is None]
        if facts_without_id:
            errors.append(
                f"Found {len(facts_without_id)} facts in investigation.xml without id attribute "
                "(all facts must have id='F-001', id='F-002', etc.)"
            )
        
        inferences_without_id = [i for i in investigation.findall('.//inferred/inference') if i.get('id') is None]
        if inferences_without_id:
            errors.append(
                f"Found {len(inferences_without_id)} inferences in investigation.xml without id attribute "
                "(all inferences must have id='I-001', id='I-002', etc.)"
            )
        
    except ET.ParseError as e:
        errors.append(f"XML parse error: {e}")
    except Exception as e:
        errors.append(f"Unexpected error: {e}")
    
    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print("Usage: validate-traceability.py <case-dir>")
        sys.exit(2)
    
    case_dir = sys.argv[1]
    
    if not os.path.isdir(case_dir):
        print(f"❌ Case directory not found: {case_dir}")
        sys.exit(1)
    
    print(f"Validating traceability for: {case_dir}")
    errors, warnings = validate_case_traceability(case_dir)
    
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if errors:
        print(f"\n❌ Traceability validation FAILED for {case_dir}")
        print(f"\nFound {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print(f"\n✓ Traceability validation PASSED for {case_dir}")
        sys.exit(0)


if __name__ == "__main__":
    main()
