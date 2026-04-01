# KNOWLEDGE — CORE PRINCIPLES & PROTOCOLS

**Part of**: issue-triage-handoff skill  
**Parent**: ../AGENTS.md

## OVERVIEW

Foundational knowledge base: operating principles, evidence protocols, schema specifications. Referenced by all workflows as execution prerequisites.

## STRUCTURE

```
knowledge/
├── triage-principles.md        # 10 core operating principles
├── evidence-protocol.md        # Evidence referencing & ID rules
└── handoff-schema.md           # Output structure specification
```

## WHERE TO LOOK

| Task | File | Section |
|------|------|---------|
| Modify evidence classification rules | `evidence-protocol.md` | Evidence Types |
| Change finding tier criteria | `triage-principles.md` | Principle 3 |
| Add required output field | `handoff-schema.md` | Required Fields |
| Fix evidence ID sequencing | `evidence-protocol.md` | ID Sequencing |
| Change conflict handling rules | `triage-principles.md` | Principle 9 |

## CONVENTIONS

### Three-Tier Findings Model

**From triage-principles.md § Principle 3**:

| Tier | Evidence Requirement | Promotion Criteria |
|------|---------------------|-------------------|
| `confirmed_facts` | Direct evidence (logs/stacktraces with timestamps) | No interpretation needed |
| `bounded_inferences` | Evidence supports but doesn't prove | Assumptions stated explicitly |
| `open_questions` | Insufficient evidence | State what's missing |

**Demotion Rule**: When uncertain between tiers, always demote to lower tier.

### Evidence ID Protocol

**From evidence-protocol.md**:
- Format: `E001`, `E002`, ... (3-digit zero-padded)
- Sequential within handoff version
- Never skip numbers
- Never reuse IDs (even after deletion)
- On merge: continue sequence (E001-E015 → new starts at E016)

### Source Reference Structure

**Required Fields**:
```json
{
  "evidence_id": "E001",
  "source_ref": {
    "source_type": "file|url|inline",  // REQUIRED
    "path": "string",                   // REQUIRED for file/url
    "line_start": 1,                    // optional
    "line_end": 3                       // optional
  }
}
```

**Rule**: Every `evidence_refs` array element must exist in `evidence_inventory`.

### Evidence Weight Hierarchy

**From evidence-protocol.md** (for conflict resolution):
1. **Stacktraces/exceptions** with timestamps (highest weight)
2. **Structured logs** with trace/request IDs
3. **Unstructured logs** with timestamps
4. **Human comments/chat** messages
5. **Hearsay** (lowest weight)

When evidence conflicts, higher-weight evidence takes precedence in conflict documentation.

## ANTI-PATTERNS (KNOWLEDGE BASE)

❌ **Promoting human narrative to confirmed facts**  
Location: triage-principles.md:20-31  
Reason: Human claims go in `people_hypotheses`. Only logs/stacktraces become `confirmed_facts`.

❌ **Creating evidence without `source_ref`**  
Location: evidence-protocol.md:139  
Reason: All evidence must be traceable. Broken references make output unusable.

❌ **Reusing evidence IDs after deletion**  
Location: evidence-protocol.md:15  
Reason: IDs track provenance across refinements. Reuse creates ambiguity.

❌ **Empty `open_questions` when gaps exist**  
Location: handoff-schema.md:194  
Reason: Gaps must be explicit. Empty array misrepresents completeness.

❌ **Vague evidence references**  
Location: evidence-protocol.md:139-150  
Examples: "from logs", "user mentioned", "somewhere in code"  
Reason: References must be followable in <30 seconds.

## UNIQUE PATTERNS

### Evidence Provenance Chain

**From evidence-protocol.md**:
```
E001: app.log:1423-1425 (stacktrace)
  ↓ [backs]
F001: "NullPointerException at UserService.java:145" (confirmed_fact)
  ↓ [supports]
I001: "Likely timeout caused crash" (bounded_inference)
  ↓ [identifies gap]
Q001: "Why didn't retry mechanism trigger?" (open_question)
```

Every claim traces back to evidence ID.

### Conflict Documentation Format

**From triage-principles.md § Principle 9**:
```json
{
  "conflicts": [
    {
      "description": "Error timestamp mismatch",
      "original": "Error at 14:03:00",
      "original_ref": "E003",
      "contradicting": "Error at 14:05:00",
      "contradicting_ref": "E008",
      "resolution": "pending",
      "resolution_notes": null
    }
  ]
}
```

Both pieces of evidence preserved. Resolution documented explicitly.

### Scope Boundaries

**From triage-principles.md § Principle 10**:

**IN SCOPE** (what this skill does):
- Compress noise → signal
- Filter evidence
- Map code locations
- Build timeline
- Classify findings

**OUT OF SCOPE** (what downstream agents do):
- Confirm root cause
- Generate patches
- Recommend fixes
- Assign blame
- Make deployment decisions

## NOTES

### Schema Version Management

**From handoff-schema.md**:
- Current: `schema_version: "1.0"`
- Core field changes → version bump required
- Downstream tools parse version for compatibility
- Optional field additions → no version bump needed

### Cost-Aware Compression

**From triage-principles.md § Principle 5**:

**Cheap operations** (do here):
- Summarization
- Pattern matching
- Keyword extraction
- Schema filling

**Expensive operations** (leave downstream):
- Causal reasoning
- Code comprehension
- Fix generation
- Architectural analysis

### Evidence Content Limits

**From handoff-schema.md**:
- Evidence content: ≤200 chars
- Longer content → use `source_ref` with line numbers
- Full text goes in original files, not evidence inventory

### Required vs Optional Fields

**Always Required** (handoff invalid without):
- `schema_version`, `case_meta.title`, `case_meta.created_at`, `case_meta.sources`
- `context_summary.problem_statement`
- `evidence_inventory` (≥1 item)
- `findings.*` (all three arrays, may be empty)
- `handoff_summary.scope`

**Optional** (omit if insufficient data):
- `timeline`, `code_mapping`, `conflicts`, `key_signals`
