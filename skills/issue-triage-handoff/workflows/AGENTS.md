# WORKFLOWS — EXECUTION ORCHESTRATION

**Part of**: issue-triage-handoff skill  
**Parent**: ../AGENTS.md

## OVERVIEW

Workflow orchestrators controlling deterministic/LLM phase boundaries. Three workflows map to user intents: create, refine, evaluate.

## STRUCTURE

```
workflows/
├── new-triage-handoff.md       # Create handoff from raw materials (7 steps)
├── handoff-refinement.md       # Update existing handoff (7 steps)
└── handoff-evaluation.md       # Assess handoff readiness (9 steps)
```

## WHERE TO LOOK

| Task | File | Step # |
|------|------|--------|
| Modify log collection phase | `new-triage-handoff.md` | Step 2 |
| Change evidence merge logic | `handoff-refinement.md` | Step 4 |
| Add quality scoring criteria | `handoff-evaluation.md` | Step 7 |
| Fix code mapping logic | `new-triage-handoff.md` | Step 6 |
| Change conflict handling | `handoff-refinement.md` | Step 5 |

## CONVENTIONS

### Execution Phase Boundaries

**Deterministic Steps** (scripts only):
- Material intake & recording
- Log collection with time-window filtering
- Code symbol search (stacktrace + route mapping)
- Output file generation
- Schema validation

**LLM Steps** (AI reasoning):
- Context extraction from narrative
- Evidence extraction from logs
- Timeline synthesis
- Findings classification (facts vs inferences)
- Conflict analysis

**Rule**: Never mix deterministic and LLM in same step. Batch deterministic ops before LLM.

### Workflow Selection

**Intent → Workflow Mapping** (enforced by SKILL.md):
```
"triage this issue"           → new-triage-handoff.md
"prepare handoff"             → new-triage-handoff.md
"organize debugging materials" → new-triage-handoff.md
"refine handoff with new..."  → handoff-refinement.md
"evaluate handoff quality"    → handoff-evaluation.md
```

**Ambiguous Intent**: Must clarify with user (don't auto-guess workflow).

### Evidence Integration Rules

**new-triage-handoff.md** (create):
- Evidence IDs start at E001
- Timeline built from scratch
- All findings start in appropriate tier

**handoff-refinement.md** (merge):
- Continue evidence ID sequence (existing E001-E015 → new E016+)
- Timeline: insert new events chronologically
- Conflicts: flag explicitly, keep both, document in `conflicts[]`

### Step Dependencies

**new-triage-handoff.md**:
```
Step 1 (Material Intake)
  ↓ [produces: raw_materials.json]
Step 2 (Log Collection) — DETERMINISTIC
  ↓ [produces: log_evidence.json]
Step 3 (Code Search) — DETERMINISTIC
  ↓ [produces: code_locations.json]
Step 4 (Context Extraction) — LLM
  ↓ [produces: context_summary]
Step 5 (Evidence Extraction) — LLM
  ↓ [produces: evidence_inventory]
Step 6 (Code Mapping) — LLM
  ↓ [produces: code_mapping]
Step 7 (Findings Assembly) — LLM
  ↓ [produces: findings]
Step 8 (Conflict Handling) — LLM
  ↓ [produces: conflicts]
Step 9 (Output Validation) — DETERMINISTIC
  ↓ [produces: handoff.json]
```

**handoff-refinement.md**:
```
Step 1 (Identify Materials)
  ↓
Step 2 (Evidence Integration) — append to inventory
  ↓
Step 3 (Conflict Analysis) — detect contradictions
  ↓
Step 4 (Merge) — combine findings
  ↓
Step 5 (Conflict Documentation) — explicit flags
  ↓
Step 6 (Version Update) — bump version, add revision notes
  ↓
Step 7 (Self-Check) — validate against schema
```

## ANTI-PATTERNS (WORKFLOWS)

❌ **Running LLM steps before deterministic evidence collection**  
Reason: Log collection must complete BEFORE LLM extraction. Scripts provide structured input.

❌ **Auto-resolving conflicts during merge**  
Location: handoff-refinement.md:62  
Reason: Conflicts are signal. Flag explicitly, keep both pieces of evidence.

❌ **Skipping conflict documentation**  
Location: handoff-refinement.md § Step 5  
Reason: Downstream agents need to see contradictions. Silent resolution hides critical ambiguity.

❌ **Starting evidence IDs from E001 during refinement**  
Location: handoff-refinement.md § Step 2  
Reason: Continue existing sequence to preserve traceability across versions.

❌ **Proceeding when log collection returns zero files**  
Location: new-triage-handoff.md § Step 2  
Reason: Fail-fast. Don't fabricate evidence when filtering returns empty.

## UNIQUE PATTERNS

### Evidence Promotion Flow

**handoff-refinement.md § Step 4**:
- New evidence **confirms** existing inference → promote to `confirmed_facts`
- New evidence **contradicts** → flag conflict, move affected items to `open_questions`
- New evidence **extends** → add to appropriate tier

### Conflict Resolution Strategy

**Never Auto-Resolve**:
1. Detect contradiction
2. Flag in `conflicts[]` with both evidence references
3. Mark resolution: `pending`
4. Move affected findings to `open_questions`
5. Document in revision notes

### Timeline Merge Algorithm

**handoff-refinement.md § Step 4**:
```
existing_timeline = [T1, T3, T5]
new_timeline = [T2, T4]
→ merged = [T1, T2, T3, T4, T5] (chronological insert)
```

Gap markers preserved explicitly.

## NOTES

### Workflow Prerequisites

**Before new-triage-handoff.md**:
- User must provide: raw materials (logs, chat, comments, stacktrace)
- Optional: event time for log filtering (format: `YYYY-MM-DDTHH:MM:SS`)

**Before handoff-refinement.md**:
- Existing handoff JSON (with version number)
- New evidence materials

**Before handoff-evaluation.md**:
- Completed handoff JSON

### Workflow Outputs

**new-triage-handoff.md**:
- `handoff.summary.json` (main output, ≤120 lines)
- `handoff.evidence.json` (optional, full evidence)

**handoff-refinement.md**:
- Updated handoff with version bump
- Revision notes documenting changes
- Conflicts array populated

**handoff-evaluation.md**:
- `evaluation.json` (scores, gaps, recommendations)
- Schema: `../schemas/evaluation.schema.json`

### Step Execution Times

**Deterministic steps** (fast, <10s):
- Log collection, code search, validation

**LLM steps** (slower, 30-120s):
- Context extraction, evidence synthesis, findings assembly

**Total workflow time**:
- new-triage-handoff: ~3-5 minutes
- handoff-refinement: ~2-3 minutes
- handoff-evaluation: ~1-2 minutes
