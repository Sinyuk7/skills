# Handoff Schema

This document defines the structure of a handoff package.

## Overview

A handoff package is a JSON document with stable structure that downstream agents can consume without re-reading raw materials.

## Schema

```json
{
  "schema_version": "1.0",
  
  "case_meta": {
    "title": "string - Brief problem description",
    "handoff_id": "string - Unique identifier",
    "created_at": "ISO 8601 timestamp",
    "last_modified": "ISO 8601 timestamp",
    "version": "integer - Increment on each refinement",
    "sources": [
      {
        "type": "issue|comment|chat|log|repo|trace|config",
        "identifier": "string - URL, path, or ID",
        "added_at": "ISO 8601 timestamp"
      }
    ],
    "revision_notes": ["string - What changed in each version"]
  },

  "context_summary": {
    "problem_statement": "string - What is broken, in one paragraph",
    "expected_behavior": "string - What should happen",
    "actual_behavior": "string - What actually happens",
    "environment": {
      "os": "string",
      "version": "string",
      "branch": "string",
      "commit": "string",
      "additional": {}
    },
    "key_identifiers": {
      "trace_ids": ["string"],
      "request_ids": ["string"],
      "user_ids": ["string"],
      "session_ids": ["string"],
      "additional": {}
    },
    "incident_window": {
      "first_observed": "ISO 8601 timestamp or null",
      "last_observed": "ISO 8601 timestamp or null",
      "timezone": "string - IANA timezone or UTC offset"
    },
    "actions_attempted": [
      {
        "action": "string - What was tried",
        "result": "string - What happened",
        "source_ref": "string - evidence_id"
      }
    ],
    "people_hypotheses": [
      {
        "hypothesis": "string - Human's guess",
        "source": "string - Who said it",
        "source_ref": "string - evidence_id"
      }
    ]
  },

  "evidence_inventory": [
    {
      "evidence_id": "string - Unique within this handoff (e.g., E001)",
      "type": "log_entry|stacktrace|comment|chat_message|config|metric|screenshot",
      "source_ref": {
        "source_type": "file|url|inline",
        "path": "string - File path or URL",
        "line_start": "integer or null",
        "line_end": "integer or null"
      },
      "timestamp": "ISO 8601 timestamp or null",
      "content": "string - The actual evidence content or excerpt",
      "tags": ["error", "warning", "info", "key_identifier", "stacktrace"]
    }
  ],

  "key_signals": [
    {
      "signal_type": "error|exception|timeout|connection_failure|resource_exhaustion|permission_denied|data_inconsistency",
      "signature": "string - Deduplication key (e.g., exception type + message prefix)",
      "first_occurrence": "evidence_id",
      "occurrence_count": "integer",
      "evidence_refs": ["evidence_id"]
    }
  ],

  "timeline": [
    {
      "timestamp": "ISO 8601 timestamp",
      "event": "string - What happened",
      "source": "log|comment|inferred",
      "evidence_ref": "string - evidence_id or null if inferred",
      "confidence": "high|medium|low"
    }
  ],

  "code_mapping": [
    {
      "file": "string - Path relative to repo root",
      "lines": {
        "start": "integer",
        "end": "integer"
      },
      "symbols": ["string - Function/class names"],
      "match_type": "stacktrace|symbol_search|route_mapping|keyword",
      "confidence": "high|medium|low",
      "evidence_refs": ["evidence_id"],
      "notes": "string - Why this location matters"
    }
  ],

  "findings": {
    "confirmed_facts": [
      {
        "fact": "string - Statement of verified truth",
        "evidence_refs": ["evidence_id"]
      }
    ],
    "bounded_inferences": [
      {
        "inference": "string - Conclusion with assumptions",
        "assumptions": ["string - What must be true for this to hold"],
        "evidence_refs": ["evidence_id"],
        "confidence": "high|medium|low"
      }
    ],
    "open_questions": [
      {
        "question": "string - What we don't know",
        "why_unknown": "string - What evidence is missing",
        "suggested_action": "string - How to resolve"
      }
    ]
  },

  "conflicts": [
    {
      "description": "string - What's conflicting",
      "original": "string - First evidence",
      "original_ref": "evidence_id",
      "contradicting": "string - Contradicting evidence",
      "contradicting_ref": "evidence_id",
      "resolution": "pending|resolved",
      "resolution_notes": "string or null"
    }
  ],

  "selected_files": [
    {
      "path": "string",
      "reason": "string - Why this file was selected for analysis"
    }
  ],

  "excluded_files": [
    {
      "path": "string or pattern",
      "reason": "string - Why this file was excluded"
    }
  ],

  "handoff_summary": {
    "scope": "string - What this handoff covers",
    "confidence": "high|medium|low - Overall confidence in findings",
    "gaps": ["string - Known gaps in the analysis"],
    "recommended_next_steps": ["string - Suggested actions for downstream"],
    "suitable_for": ["rca_agent", "patch_agent", "human_review"]
  }
}
```

## Field Guidelines

### Required vs Optional

**Required** (handoff is invalid without these):
- `schema_version`
- `case_meta.title`
- `case_meta.created_at`
- `case_meta.sources` (at least one)
- `context_summary.problem_statement`
- `evidence_inventory` (at least one item)
- `findings.confirmed_facts` (may be empty array)
- `findings.bounded_inferences` (may be empty array)
- `findings.open_questions` (should have at least one)
- `handoff_summary.scope`

**Optional**:
- `timeline` (omit if insufficient data)
- `code_mapping` (omit if no code evidence)
- `conflicts` (only if contradictions exist)
- `key_signals` (only if patterns identified)

### Evidence ID Convention

Use format: `E001`, `E002`, etc.
- Sequential within handoff
- Never reuse IDs across versions
- When merging, renumber to maintain uniqueness

### Confidence Levels

| Level | Meaning |
|-------|---------|
| high | Direct evidence (stacktrace, explicit log message) |
| medium | Strong correlation (timestamp match, symbol match) |
| low | Weak signal (keyword match, heuristic) |

### Match Types for Code Mapping

| Type | Confidence Default |
|------|-------------------|
| stacktrace | high |
| symbol_search | medium |
| route_mapping | medium |
| keyword | low |

## Extensibility

Add custom fields under `additional` objects or at the top level with underscore prefix: `_custom_field`.

Core schema fields should not be modified without version bump.
