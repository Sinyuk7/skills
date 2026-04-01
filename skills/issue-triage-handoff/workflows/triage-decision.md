# Triage Decision Workflow

Pre-workflow decision gate that determines whether to generate a full handoff package or produce a lightweight summary.

## Purpose

Prevent generating bloated 300-line handoffs when cases are "already clear" — issues with explicit root cause, complete timeline, and high-confidence evidence don't need extensive synthesis.

## Prerequisites

Read these files before starting:

- `knowledge/triage-principles.md` - Core operating principles
- `knowledge/evidence-protocol.md` - Evidence weight hierarchy
- `knowledge/handoff-schema.md` - Output structure

---

## Execution Flow

```
User Request (raw materials)
    ↓
D-1: triage_decision ← THIS WORKFLOW
    ├─ Quick evidence assessment
    ├─ Root cause clarity check
    ├─ Timeline completeness analysis
    └─ Decision: resolved | needs_handoff | needs_more_evidence | blocked
    ↓
[FORK]
├─ resolved → Output: triage-summary.json (50-80 lines) + STOP
├─ needs_handoff → Continue to Intent Dispatch → Load workflow (new-triage/refinement/eval)
├─ needs_more_evidence → Output: evidence-gap-report.json (20-30 lines) + STOP
└─ blocked → Output: blocker-report.json (15-20 lines) + STOP
```

---

## Step 1: Material Intake (Deterministic)

Same as `new-triage-handoff.md` Step 1.

Accept any format:
- Issue title and body
- Comments and chat logs
- Log files, directories, or archives
- Repository access
- Trace IDs, request IDs

Record in `case_meta.sources[]`.

**Do not** ask user to reorganize materials.

Output: `case_meta.sources[]` populated

---

## Step 2: Quick Evidence Collection (Deterministic)

Run **lightweight** log collection (no full extraction):

```bash
# Quick scan mode (no archive expansion, pattern-match only)
./scripts/collect-log-evidence.sh <log_dir> \
  --event "YYYY-MM-DDTHH:MM:SS" \
  --window-seconds 300 \
  --quick-mode \
  --identifiers "id1,id2"
```

Quick mode:
- Scan archive filenames (don't extract)
- Pattern match: error, exception, timeout, panic, fatal
- Count matching files, record patterns found
- **No full content extraction yet**

Output: 
```json
{
  "match_count": 5,
  "patterns_found": ["timeout", "exception"],
  "matching_files": ["file1.log", "file2.log"],
  "has_stacktrace": true,
  "has_error_code": true
}
```

---

## Step 3: Evidence Quality Assessment (LLM)

From materials + quick scan results, assess evidence quality:

### A. Confirmed Facts Count

Extract from human narrative + log patterns:
- How many facts have direct evidence backing?
- Are stacktraces present?
- Are error codes/messages explicit?

**Criteria**:
- `≥3 confirmed_facts` with log/stacktrace backing → PASS
- `<2 confirmed_facts` → FAIL (needs handoff)

### B. Root Cause Clarity

Check for explicit error signatures:
- Error codes (e.g., `-997`, `500`, `ECONNREFUSED`)
- Exception types (e.g., `NullPointerException`, `TimeoutError`)
- Clear failure modes (e.g., "Request timeout exceeded")

**Criteria**:
- Error signature explicit AND location known → PASS
- Vague errors OR unknown location → FAIL (needs handoff)

### C. Timeline Completeness

Assess temporal coverage:
- Do we have start → end timestamps?
- Are there unexplained gaps >30 seconds?
- Is event causality clear?

**Criteria**:
- Complete timeline (zero gaps OR gaps documented with reason) → PASS
- Multiple unexplained gaps → FAIL (needs handoff)

### D. Code Location Precision

From stacktraces or error messages:
- Do we have file:line references?
- Are locations backed by stacktrace (high confidence)?

**Criteria**:
- ≥1 stacktrace-backed location → PASS
- Only keyword matches (low confidence) → FAIL (needs handoff)

### E. Open Questions Scope

Count questions that block understanding:
- Are open_questions about PRIMARY failure cause?
- Or just about secondary details (optimization, monitoring)?

**Criteria**:
- open_questions ≤2 AND none about primary cause → PASS
- ≥3 questions OR questions about root cause → FAIL (needs handoff)

---

## Step 4: Decision Matrix (LLM)

Apply decision logic based on assessments:

### Decision: **resolved**

**ALL criteria PASS**:
- ✅ ≥3 confirmed_facts with evidence
- ✅ Error signature explicit
- ✅ Timeline complete
- ✅ ≥1 stacktrace-backed code location
- ✅ open_questions ≤2, none about primary cause

**Confidence Scoring**:
- High: All 5 criteria PASS with strong evidence
- Medium: 4/5 criteria PASS
- Low: 3/5 criteria PASS (edge case, still resolved)

**Action**: Generate `triage-summary.json` (templates/triage-summary.json)

---

### Decision: **needs_handoff**

**ANY criterion FAIL**:
- ❌ <2 confirmed_facts
- ❌ Vague error (no explicit code/exception)
- ❌ Timeline fragmented (multiple gaps)
- ❌ No high-confidence code locations
- ❌ ≥3 open_questions OR questions about root cause

**Additional handoff triggers**:
- Evidence contradictions (conflicts[] non-empty)
- ≥3 bounded_inferences with conflicting assumptions
- Scope broad (>5 files OR >15 evidence items)

**Action**: Continue to Intent Dispatch → load full workflow

---

### Decision: **needs_more_evidence**

**Evidence gaps detected**:
- No logs found in incident window
- Trace IDs provided but logs not found
- Only people_hypotheses, no log backing
- Critical files missing (config, schema, API spec)

**Action**: Generate `evidence-gap-report.json` (templates/evidence-gap-report.json)

---

### Decision: **blocked**

**Execution cannot proceed**:
- No materials provided (empty sources)
- Unsupported format (e.g., binary-only, encrypted)
- Dependency failure (tools missing, network unavailable)
- Explicit blocker stated by user

**Action**: Generate `blocker-report.json` (templates/blocker-report.json)

---

## Step 5: Output Generation (Deterministic)

Based on decision, generate appropriate output:

### For **resolved**:
```bash
# Generate lightweight summary
Output: triage-summary.json
Structure:
  - triage_decision (status, confidence, reasoning)
  - case_meta (minimal)
  - context_summary (problem_statement + incident_window only)
  - top_evidence (≤5 items, reference-only, no content)
  - findings (confirmed_facts + open_questions only, no bounded_inferences)
  - handoff_summary (scope + confidence + gaps)
Target: 50-80 lines
```

### For **needs_handoff**:
```bash
# Pass control to Intent Dispatch
Load workflow: new-triage-handoff.md | handoff-refinement.md | handoff-evaluation.md
(Based on user intent)
```

### For **needs_more_evidence**:
```bash
# Generate gap report
Output: evidence-gap-report.json
Structure:
  - triage_decision (status, reasoning)
  - missing_evidence (list of gaps)
  - suggested_actions (where to find data)
  - partial_findings (what we know so far)
Target: 20-30 lines
```

### For **blocked**:
```bash
# Generate blocker report
Output: blocker-report.json
Structure:
  - triage_decision (status, reasoning)
  - blocker_details (what's blocking, why)
  - resolution_steps (how to unblock)
Target: 15-20 lines
```

---

## Step 6: Decision Recording (Deterministic)

All outputs MUST include `triage_decision` object:

```json
{
  "triage_decision": {
    "status": "resolved|needs_handoff|needs_more_evidence|blocked",
    "confidence": "high|medium|low",
    "reasoning": "Why this decision was made",
    "evidence_refs": ["E001", "E003"],
    "criteria_results": {
      "confirmed_facts_sufficient": true,
      "root_cause_clear": true,
      "timeline_complete": true,
      "code_location_precise": true,
      "open_questions_limited": true
    },
    "decision_timestamp": "2026-04-01T16:45:00+08:00"
  }
}
```

**Rule**: `reasoning` must explain decision based on evidence, not intuition.

---

## Execution Rules

1. **Conservative bias**: When uncertain between resolved/needs_handoff → choose needs_handoff
2. **Evidence threshold**: If confidence is "low", route to needs_handoff (avoid false negatives)
3. **Quick mode first**: Don't expand archives unless decision requires it
4. **Fail-fast**: If Step 2 finds zero matching files → immediate needs_more_evidence

---

## Anti-Patterns

❌ **Routing to resolved with <2 confirmed_facts**  
Reason: Insufficient evidence for "already clear" claim

❌ **Routing to needs_more_evidence when evidence exists but is complex**  
Reason: Complexity signals needs_handoff, not missing data

❌ **Generating full handoff when all 5 criteria PASS**  
Reason: Wastes tokens/time on unnecessary synthesis

❌ **Omitting triage_decision object from output**  
Reason: Downstream consumers need decision rationale

---

## Validation

After decision, verify:
- Output matches decision status (resolved → triage-summary.json)
- triage_decision.reasoning references actual evidence
- criteria_results aligns with decision (all true → resolved)
- File size meets target (resolved: ≤80 lines)

---

## Example: case_02

**Input**: 
- Problem: API timeout, error code -997
- Evidence: 5 log entries with stacktraces
- Timeline: 09:31:06 → 09:31:20 (complete)
- Code location: ofs.r.intercept:131 (stacktrace-backed)

**Assessment**:
- confirmed_facts: 5 ✅
- Error signature: -997 "Request timeout exceeded" ✅
- Timeline: Complete ✅
- Code location: High confidence ✅
- open_questions: 3 (but not about primary cause) ✅

**Decision**: `resolved` (confidence: high)

**Output**: `triage-summary.json` (62 lines)

**Avoided**: 300-line full handoff generation (78% reduction)
