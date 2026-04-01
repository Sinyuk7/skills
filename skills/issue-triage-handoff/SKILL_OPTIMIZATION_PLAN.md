# SKILL OPTIMIZATION PLAN — Issue Triage Handoff v2.0

**Generated**: 2026-04-01  
**Based on**: TODOS.md P0 analysis + explore agent findings  
**Target**: Resolve critical architectural defects, reduce output 56-62%

---

## EXECUTIVE SUMMARY

**Current Problems**:
1. ❌ **No triage gate** — All cases forced into 300-line handoff pipeline (even "already clear" cases)
2. ❌ **300-line output bloat** — Triple redundancy (evidence → timeline → findings)
3. ❌ **Silent file skipping** — Images/videos ignored without inventory entry
4. ❌ **Wrong responsibility attribution** — SDK team told to "check SDK team's server"

**Optimization Impact**:
- ✅ Output: 300 lines → 114 lines (62% reduction)
- ✅ Execution: 3-5 min → 30-90s for resolved cases (70% time savings)
- ✅ Evidence: Text-only → Multimodal (images, videos)
- ✅ Attribution: Context-blind → Project-aware recommendations

---

## P0.1 — TRIAGE DECISION FORK (Priority: CRITICAL)

### Problem

**Current**: All inputs → forced through 9-step pipeline → 300-line handoff  
**Impact**: case_02 has clear root cause (timeout, error -997, stacktrace) but generates bloated output

### Solution: Pre-Workflow Decision Gate

```
User Request
    ↓
D-1: triage_decision (NEW STAGE)
    ├─ Analyze evidence quality
    ├─ Assess root cause clarity
    └─ Decision: resolved | needs_handoff | needs_more_evidence | blocked
    ↓
[FORK]
├─ resolved → triage-summary.json (50-80 lines) + STOP
├─ needs_handoff → continue to Intent Dispatch → full pipeline
├─ needs_more_evidence → evidence-gap-report.json (20-30 lines) + STOP
└─ blocked → blocker-report.json (15-20 lines) + STOP
```

### Decision Criteria

**resolved** (skip handoff):
- ✅ ≥3 confirmed_facts with stacktrace/log evidence
- ✅ Error signature explicit (error_code or exception_type)
- ✅ Timeline complete (zero gaps OR gaps documented)
- ✅ ≥1 stacktrace-backed code location
- ✅ open_questions ≤2 AND none about primary failure cause

**needs_handoff** (run full pipeline):
- ❌ <2 confirmed_facts
- ❌ Contradictions in evidence
- ❌ ≥3 bounded_inferences with conflicting assumptions
- ❌ Timeline fragmented (multiple unexplained gaps)
- ❌ Scope broad (>5 files OR >15 evidence items)

**needs_more_evidence** (request data):
- No logs in incident window
- Trace IDs provided but logs not found
- Only people_hypotheses, no log backing

### Implementation

**File**: `/workflows/triage-decision.md` (new)
**Entry point**: SKILL.md Intent Dispatch (add D-1 stage before workflow selection)
**Output templates**:
- `templates/triage-summary.json` (≤80 lines)
- `templates/evidence-gap-report.json` (≤30 lines)
- `templates/blocker-report.json` (≤20 lines)

**Schema**: Add `triage_decision` object to all outputs:
```json
{
  "triage_decision": {
    "status": "resolved|needs_handoff|needs_more_evidence|blocked",
    "confidence": "high|medium|low",
    "reasoning": "Why this decision",
    "evidence_refs": ["E001", "E003"],
    "decision_timestamp": "ISO 8601"
  }
}
```

**Verification**: case_02 routes to `resolved`, outputs triage-summary.json (≤80 lines)

---

## P0.2 — DUAL-LAYER OUTPUT (Priority: CRITICAL)

### Problem

**Current**: Single 300-line file with triple redundancy:
- evidence_inventory (67 lines): Raw log content embedded
- timeline (37 lines): Human summaries of same content
- findings (55 lines): Analytical conclusions from same data

### Solution: Reference-Based Compression

**A. Summary Document** (user-facing, ≤120 lines):
```json
{
  "schema_version": "2.0",
  "case_meta": {...},
  "context_summary": {
    "problem_statement": "...",
    "incident_window": {...}  // Keep only essential fields
  },
  "evidence_inventory": [
    {
      "evidence_id": "E001",
      "type": "log_entry",
      "source_ref": {...},  // File + line numbers ONLY
      "timestamp": "...",
      // NO content field in summary
      "tags": [...]
    }
  ],
  "findings": {
    "confirmed_facts": [...],     // Keep (ground truth)
    "bounded_inferences": [...],  // Keep (reasoned conclusions)
    "open_questions": [...]       // Keep (gaps)
  },
  "handoff_summary": {...},
  "_evidence_link": "handoff.evidence.json"  // Pointer to attachment
}
```

**B. Evidence Attachment** (forensics, optional):
```json
{
  "schema_version": "2.0",
  "evidence_inventory": [
    {
      "evidence_id": "E001",
      "content": "FULL RAW LOG TEXT HERE (793 chars)",  // Now included
      ...
    }
  ],
  "timeline": [...],        // Full chronology
  "code_mapping": [...]     // Detailed source mappings
}
```

### Compression Results

| Section | Current | Summary | Evidence | Compression |
|---------|---------|---------|----------|-------------|
| evidence_inventory | 67 lines | 20 lines | 67 lines | -70% (summary) |
| timeline | 37 lines | 0 lines | 37 lines | -100% (summary) |
| context_summary | 45 lines | 20 lines | 45 lines | -55% (summary) |
| findings | 55 lines | 55 lines | — | 0% (kept) |
| **Total** | **300 lines** | **114 lines** | **186 lines** | **-62% (user-facing)** |

### Implementation

**Files**:
- `schemas/handoff.schema.json` → v2.0 (make evidence[*].content optional in summary)
- `schemas/evidence.schema.json` → new (require content field in evidence)
- `templates/handoff-summary.json` → new (≤120 lines)
- `templates/handoff-evidence.json` → new (optional attachment)
- `workflows/new-triage-handoff.md` → modify Step 8 (split output generation)

**Rules**:
- Evidence content ≤200 chars in summary (strip longer)
- All facts MUST reference evidence_id (no inline text duplication)
- Timeline moved to evidence attachment
- Top-K filtering: Include only evidence with evidence_refs (default K=8)

**Verification**: case_02 produces 114-line summary + 186-line evidence

---

## P0.3 — FULL EVIDENCE INVENTORY (Priority: HIGH)

### Problem

**Current**: collect-log-evidence.sh only processes `.log`, `.txt`, `.json` files  
**Silent Skip**: Images, videos, PDFs ignored without inventory entry  
**User Assumption**: "All files in directory are valid input"

### Solution: Mandatory Inventory Stage

**New Stage**: `D0: build_evidence_inventory` (before D-1)
```bash
#!/bin/bash
# scripts/build-evidence-inventory.sh

# Scan ALL files recursively
find "$INPUT_DIR" -type f | while read -r file; do
  case "$file" in
    *.log|*.txt|*.json)
      echo '{"path":"'$file'", "type":"text", "status":"parsed", "reason":""}' ;;
    *.png|*.jpg|*.jpeg|*.webp)
      echo '{"path":"'$file'", "type":"image", "status":"skipped", "reason":"Multimodal support not yet implemented"}' ;;
    *.mp4|*.mov)
      echo '{"path":"'$file'", "type":"video", "status":"skipped", "reason":"Multimodal support not yet implemented"}' ;;
    *)
      echo '{"path":"'$file'", "type":"unknown", "status":"skipped", "reason":"Unsupported file type"}' ;;
  esac
done
```

**Inventory Schema Extension**:
```json
{
  "file_path": "string",
  "type": "text|image|video|document|unknown",
  "size": "bytes",
  "mtime": "unix_timestamp",
  "status": "parsed | skipped | failed",  // NEW
  "reason": "why not parsed",             // NEW
  "evidence_refs": ["E001"]               // Links to extracted evidence
}
```

### Implementation

**Files**:
- `scripts/build-evidence-inventory.sh` → new (universal scanner)
- `schemas/handoff.schema.json` → add status/reason fields
- `workflows/new-triage-handoff.md` → add Step 0.5 (before Material Intake)
- `knowledge/evidence-protocol.md` → document inventory mandates

**Rules**:
- Every file in input → MUST appear in inventory
- status:skipped → MUST have reason
- No silent skips (validation: inventory size == input file count)

**Verification**: Input with logs + images → all files appear in inventory with correct status

---

## P0.4 — MULTIMODAL EVIDENCE (Priority: HIGH)

### Problem

**Current**: Schema defines `screenshot` type but no collector implements it  
**Gap**: No image/video parsing, no visual_signals field

### Solution: Multimodal Schema + Collection

**A. Schema Extensions** (schemas/handoff.schema.json v2.0):
```json
{
  "type": "image | video | document",  // NEW types
  "visual_signals": [                  // NEW field
    "error_dialog", 
    "red_button", 
    "timeout_message"
  ],
  "ocr_text": "extracted text",        // NEW field
  "relevance": "direct|context|weak",  // NEW field
  "metadata": {
    "dimensions": "1920x1080",
    "duration_seconds": 45,
    "file_size_bytes": 2048000
  }
}
```

**B. Collection Logic** (scripts/collect-multimodal-evidence.sh):
```bash
# Extract metadata + OCR from images/videos
for file in *.png *.jpg *.mp4; do
  # Use exiftool for metadata
  # Use tesseract for OCR (if image contains text)
  # Output JSON with visual_signals
done
```

**C. Evidence Weight Hierarchy** (update evidence-protocol.md):
1. Stacktraces/exceptions with timestamps (highest)
2. **Visual evidence + OCR + timestamp** (NEW, high)
3. Structured logs with trace/request IDs
4. **Screenshot with visual_signals** (NEW, medium)
5. Unstructured logs
6. Human comments/chat
7. **Unlabeled video** (NEW, low — requires interpretation)

### Implementation

**Files**:
- `scripts/collect-multimodal-evidence.sh` → new
- `schemas/handoff.schema.json` → extend evidence types
- `knowledge/evidence-protocol.md` → add multimodal weight guidance
- `workflows/new-triage-handoff.md` → add Step 2.5 (after log collection)

**Dependencies**:
- exiftool (metadata extraction)
- tesseract (OCR, optional)
- ffprobe (video metadata)

**Top-K Filtering**: Include only Top-K multimodal evidence (default K=3) in summary

**Verification**: case_02 (if video exists) → video appears in evidence with metadata

---

## P0.5 — PROJECT CONTEXT INJECTION (Priority: MEDIUM)

### Problem

**Current**: case_02 recommends "检查服务端...响应日志" when SDK team OWNS the server  
**Root Cause**: No project identity context during synthesis

### Solution: Project Context File + Synthesis Integration

**A. Context File** (`triage/project-context.md`):
```yaml
project_name: "Cloud Music IoT SDK"
team_role: "provider"  # provider | consumer | integration
ownership:
  client_code: "SDK team"
  backend_api: "SDK team"
  third_party_service: "External"
issue_scope: "Timeout on internal API"
forbidden_assumptions:
  - "Assume we don't own the backend"
  - "Recommend checking external services first"
```

**B. Synthesis Integration** (workflows/new-triage-handoff.md Step 7):
```
Step 6.5: Load Project Context (before synthesis)
    ↓
Check for: ./triage/project-context.md
If team_role == "provider":
  - Remove "investigate server" from next_steps
  - suitable_for: focus on internal agents (not RCA for external)
```

**C. Context-Aware Recommendations**:
```json
// BEFORE (wrong):
"recommended_next_steps": [
  "检查服务端 openapi.music.163.com 响应日志",
  "评估超时时间设置"
]

// AFTER (correct):
"recommended_next_steps": [
  "检查我们自己的 openapi.music.163.com API 响应日志 (SDK团队负责)",
  "评估客户端超时配置是否需要调整"
]
```

### Implementation

**Files**:
- `knowledge/project-context.md` → template (new)
- `workflows/new-triage-handoff.md` → add Step 6.5
- `workflows/handoff-evaluation.md` → add team_role checks in Step 6
- `templates/handoff-template.json` → possibly add _team_context field

**Rules**:
- provider → Don't suggest "本团队继续排查" (we're already the source)
- consumer → Focus on integration points, not internal implementation
- integration → Balance both sides

**Verification**: case_02 with project-context.md → recommendations reflect SDK team ownership

---

## IMPLEMENTATION ROADMAP

### Phase 1: Core Architecture (P0.1 + P0.2) — Week 1-2

**Priority: CRITICAL**

1. **P0.1 Triage Decision**:
   - Create `/workflows/triage-decision.md`
   - Add decision criteria matrix
   - Create triage-summary.json template
   - Modify SKILL.md Intent Dispatch (add D-1 gate)
   - Test: case_02 routes to resolved

2. **P0.2 Dual-Layer Output**:
   - Bump schema to v2.0
   - Create handoff-summary.json + handoff-evidence.json templates
   - Modify workflows Step 8 (split output generation)
   - Test: case_02 produces 114-line summary

**Verification**: case_02 output drops from 300 → 80-114 lines

---

### Phase 2: Evidence Completeness (P0.3 + P0.4) — Week 3-4

**Priority: HIGH**

3. **P0.3 Full Inventory**:
   - Create `scripts/build-evidence-inventory.sh`
   - Add status/reason fields to schema
   - Modify workflows (add Step 0.5)
   - Test: All input files appear in inventory

4. **P0.4 Multimodal Support**:
   - Extend schema for image/video types
   - Create `scripts/collect-multimodal-evidence.sh`
   - Add visual_signals/ocr_text fields
   - Update evidence-protocol.md (weight hierarchy)
   - Test: Images/videos processed and appear in handoff

**Verification**: Mixed input (logs + images) → all evidence types handled

---

### Phase 3: Context Intelligence (P0.5) — Week 5

**Priority: MEDIUM**

5. **P0.5 Project Context**:
   - Create `knowledge/project-context.md` template
   - Modify workflows Step 6.5 (load context)
   - Add context-aware recommendation logic
   - Test: case_02 with context → correct attribution

**Verification**: Recommendations reflect project ownership

---

## SUCCESS METRICS

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| **Output Size** | 300 lines | 114 lines | ≤120 lines ✓ |
| **Execution Time** (resolved) | 3-5 min | 30-90s | <2 min ✓ |
| **Silent Skips** | Unknown (unbounded) | 0 | 0 ✓ |
| **Attribution Errors** | 1/1 (100%) | 0/1 (0%) | <10% ✓ |
| **Evidence Types** | 1 (text) | 3 (text+image+video) | ≥3 ✓ |

---

## RISK ANALYSIS

### High Risk

❗ **P0.1 Triage Decision False Negatives**: Case routed to "resolved" but actually needs handoff  
**Mitigation**: Conservative criteria (when in doubt, route to needs_handoff), confidence scoring

❗ **P0.2 Schema v2.0 Breaking Change**: Downstream tools expect v1.0  
**Mitigation**: Version negotiation (tools check schema_version), backward compatibility layer

### Medium Risk

⚠️ **P0.4 OCR Accuracy**: False positives from image text extraction  
**Mitigation**: Mark OCR evidence as "low confidence", require manual verification

⚠️ **P0.5 Context File Staleness**: project-context.md outdated  
**Mitigation**: Timestamp validation, warn if >90 days old

### Low Risk

ℹ️ **P0.3 Inventory Size**: Large directories (10k+ files) slow inventory  
**Mitigation**: Parallel scanning, caching, incremental inventory

---

## FILES TO CREATE

**New Files**:
1. `/workflows/triage-decision.md`
2. `/templates/triage-summary.json`
3. `/templates/evidence-gap-report.json`
4. `/templates/blocker-report.json`
5. `/templates/handoff-summary.json` (v2.0)
6. `/templates/handoff-evidence.json` (v2.0)
7. `/schemas/evidence.schema.json` (v2.0)
8. `/scripts/build-evidence-inventory.sh`
9. `/scripts/collect-multimodal-evidence.sh`
10. `/knowledge/project-context.md` (template)

**Files to Modify**:
1. `/SKILL.md` — Add D-1 triage_decision stage before Intent Dispatch
2. `/schemas/handoff.schema.json` → v2.0 (status/reason fields, optional content)
3. `/workflows/new-triage-handoff.md` — Add Step 0.5 (inventory), Step 6.5 (context), modify Step 8 (split output)
4. `/workflows/handoff-evaluation.md` — Add team_role checks in Step 6
5. `/knowledge/evidence-protocol.md` — Add multimodal weight hierarchy
6. `/knowledge/triage-principles.md` — Add triage-decision principles
7. `/AGENTS.md` — Update with v2.0 changes

---

## NEXT ACTIONS

**Immediate** (this session):
1. Review this optimization plan with user
2. Confirm priority order: P0.1 → P0.2 → P0.3 → P0.4 → P0.5
3. Get approval for schema v2.0 breaking change

**Week 1**:
1. Design triage_decision criteria matrix (detailed rules)
2. Create triage-decision.md workflow
3. Implement D-1 gate in SKILL.md
4. Test case_02 routing

**Week 2**:
1. Design handoff-summary.json schema
2. Implement dual-layer output generation
3. Test compression (300 → 114 lines)
4. Validate no information loss

---

**Ready for implementation. All P0 issues analyzed, solutions designed, roadmap defined.**
