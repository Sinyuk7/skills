# Evidence Protocol

This document defines how to reference and cite evidence in handoff packages.

## Core Principle

Every significant claim must be traceable to its source. If you can't point to where something came from, it's not a fact—it's speculation.

## Evidence ID System

### Format
- Use `E001`, `E002`, etc.
- Sequential within a single handoff
- Never skip numbers
- Never reuse IDs, even after deletion

### Uniqueness Scope
- IDs are unique within one handoff version
- When merging handoffs, renumber the incoming evidence to avoid collisions
- Keep a mapping if you need to trace back to original IDs

## Source Reference Structure

Every evidence item must have a `source_ref`:

```json
{
  "evidence_id": "E001",
  "source_ref": {
    "source_type": "file|url|inline",
    "path": "string",
    "line_start": 123,
    "line_end": 125
  }
}
```

### Source Types

| Type | Usage | Path Format |
|------|-------|-------------|
| `file` | Log files, code files, configs | Relative path from repo root or absolute path |
| `url` | Issue comments, chat logs, external links | Full URL |
| `inline` | User-provided text in conversation | `inline://conversation` |

### Line References
- Use 1-indexed line numbers
- `line_start` and `line_end` define inclusive range
- For single-line evidence, `line_start == line_end`
- Omit if not applicable (e.g., entire file, URL)

## Evidence Types

| Type | When to Use |
|------|-------------|
| `log_entry` | Single log line or small group |
| `stacktrace` | Exception with stack frames |
| `comment` | Issue/PR comment |
| `chat_message` | IM or discussion thread message |
| `config` | Configuration file excerpt |
| `metric` | Numeric measurement or threshold |
| `screenshot` | Visual evidence (reference path) |
| `image` | Screenshot, error dialog capture (P0.4) |
| `video` | Screen recording, reproduction video (P0.4) |
| `document` | PDF reports, documentation excerpts (P0.4) |

## Content Guidelines

### Excerpt Length
- Include enough context for the evidence to be understandable
- For log entries: typically 1-10 lines
- For stacktraces: relevant frames (may truncate middle frames)
- For comments: relevant paragraphs

### Redaction
If evidence contains sensitive data:
- Redact with `[REDACTED]` placeholder
- Note in evidence item: `"redacted": true`
- Keep enough structure to be useful

### Timestamps
- Always include if available
- Use ISO 8601 format
- Note timezone or UTC offset
- If timestamp is inferred, mark confidence as `low`

## Reference Usage

### In Findings
Every `confirmed_fact` and `bounded_inference` must have `evidence_refs`:

```json
{
  "fact": "Service A returned 500 error at 14:32:15 UTC",
  "evidence_refs": ["E003", "E004"]
}
```

### In Timeline
Timeline events should reference evidence:

```json
{
  "timestamp": "2024-01-15T14:32:15Z",
  "event": "Service A returned 500",
  "evidence_ref": "E003"
}
```

### In Code Mapping
Code locations must trace back to evidence:

```json
{
  "file": "src/handlers/user.py",
  "lines": {"start": 145, "end": 152},
  "evidence_refs": ["E003"]
}
```

## Evidence Weight Hierarchy

When evidence conflicts, weight by type and quality:

### Tier 1 — Highest Confidence
- Stacktraces with timestamps and line numbers
- Exception logs with full context (trace IDs, request IDs)

### Tier 2 — High Confidence
- **Image with OCR text + timestamp + visual_signals** (P0.4)
  - Example: Screenshot showing "Error: Connection timeout" dialog with timestamp in corner
- Structured logs with trace/request IDs
- Metric data with timestamp

### Tier 3 — Medium Confidence
- **Screenshot with visual_signals only** (P0.4)
  - Example: Error dialog visible but no text extracted
- Unstructured logs with timestamps
- Configuration files with version info

### Tier 4 — Lower Confidence
- Human comments with technical details
- Chat messages referencing specific errors
- **Video without error signals** (P0.4)
  - Requires manual interpretation, timestamps unreliable

### Tier 5 — Lowest Confidence
- Hearsay ("someone said...")
- Unverified hypotheses
- Evidence outside incident window

### Multimodal Evidence Guidelines

**Image Evidence**:
- **Best**: OCR text + visual_signals + EXIF timestamp
- **Good**: Visual_signals + filename timestamp hint
- **Weak**: Generic screenshot without error indicators

**Video Evidence**:
- **Best**: Short clip (<30s) showing error reproduction with audio narration
- **Good**: Screen recording with clear error state at specific timestamp
- **Weak**: Long video (>2min) requiring manual review

**Top-K Filtering**: In summary output, include only Top-K multimodal evidence (default K=3) ranked by:
1. Relevance (direct > context > weak)
2. Visual signals count (more signals = higher priority)
3. OCR text length (more context = higher priority)
4. File size (smaller = easier to process)

## Verification Protocol

Before finalizing evidence:

1. **Existence Check**: Does the source actually exist?
2. **Content Match**: Does the excerpt match the source?
3. **Timestamp Sanity**: Is the timestamp within incident window?
4. **Relevance Check**: Does this evidence actually support what it's referenced for?

## Anti-Patterns

### Do NOT:
- Reference evidence without adding to inventory
- Use vague source refs like "from logs" or "user mentioned"
- Cite entire large files without line numbers
- Create evidence items with empty content
- Reference evidence that contradicts the claim it supports

### Common Mistakes:
- Promoting user hypothesis to fact without additional evidence
- Citing chat message as proof of technical behavior
- Using old evidence for current state claims
- Missing evidence for code mapping confidence levels
