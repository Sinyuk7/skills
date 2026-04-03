# Artifact Contracts

## Minimal Artifact Set

Issue-flow enforces a strict minimal artifact architecture to eliminate redundancy and maintain single-source-of-truth.

### Core Principles
1. **One artifact per concept** — No duplication of information across files
2. **Traceability is mandatory** — All downstream facts MUST reference upstream IDs
3. **Merging over splitting** — Prefer consolidated artifacts over multiple small files
4. **No optional artifacts** — Every artifact serves a decision-making purpose

---

## Case Management (ALL STAGES)

| Artifact | Format | Purpose | Owner |
|----------|--------|---------|-------|
| `case/status.yaml` | YAML | Lifecycle state + readiness flags | All stages (read/write) |
| `case/sources.yaml` | YAML | Source registration + mutation log | Collect (write), Handoff/Resolve (read) |
| `case/activity.md` | Markdown | Append-only event log | All stages (append) |

**Constraint**: `status.yaml` is the SINGLE source of truth for lifecycle state. No project-level case indexes allowed.

---

## Collect Stage

**Inputs**: User-provided issue materials (external paths)

**Outputs**:
- `curated/*` directories — Organized evidence workspace (logs/, media/, notes/, excerpts/, ocr/)
- `case/sources.yaml` — Source registration with collection status
- `case/status.yaml` — Lifecycle: `new` → `collecting` → `collected`
- `case/activity.md` — Case creation and collection events

**Artifacts NOT allowed**: None (no synthesis at this stage)

---

## Handoff Stage

**Inputs**: `curated/*`, `sources.yaml`, `ISSUE_CONTEXT.md`

**Outputs**:
- **`analysis/investigation.xml`** — FACT OF RECORD
  - Evidence refs (issue materials + repository)
  - Evidence excerpts with IDs
  - Confirmed facts with IDs (F-001, F-002, ...)
  - Inferred conclusions with IDs (I-001, I-002, ...)
  - Open questions with IDs (Q-001, Q-002, ...)
  - Detailed narrative sections

- **`analysis/handoff.xml`** — DOWNSTREAM DELIVERY
  - Concise 2-4 paragraph summary
  - Code context (affected files, key symbols with evidence refs, critical sections)
  - Known items (MUST reference investigation fact IDs via `fact_ref` attribute)
  - Next step recommendation
  - References: investigation.xml, ISSUE_CONTEXT.md

**Traceability Constraint**: Every `<known>` item in handoff.xml MUST have `fact_ref="F-XXX"` pointing to investigation.xml fact ID. Validation enforced via `validate-traceability.py`.

---

## Resolve Stage

**Inputs**: `analysis/handoff.xml`, `analysis/investigation.xml`, `ISSUE_CONTEXT.md`

**Outputs**:
- **`resolve/resolution.xml`** — IMPLEMENTATION OUTCOME
  - Summary
  - Outcome type (code_fix, config_change, non_code_conclusion, external)
  - Enhanced delivery section with commits
  - Verification status + summary
  - References: handoff.xml

- **`resolve/verification.md`** — VERIFICATION EVIDENCE
  - Detailed verification plan
  - Test results (automated + manual)
  - Before/after evidence
  - Verification status

**Intentional Split**: resolution.xml (structured metadata) + verification.md (detailed evidence) is NOT redundant — different purposes and audiences.

---

## Artifact Dependency Graph

```
sources.yaml → curated/* → investigation.xml → handoff.xml → resolution.xml
                                                    ↓              ↓
                                              (next_step)    verification.md
```

**Total Artifacts Per Complete Case**: 8
- 3 case management (status, sources, activity)
- 1 evidence workspace (curated/)
- 2 handoff (investigation, handoff)
- 2 resolve (resolution, verification)
- 1 project context (ISSUE_CONTEXT.md, shared)

---

## Validation & Enforcement

### Pre-Flight Checks (Every Skill Invocation)
```bash
scripts/detect-forbidden-artifacts.py <case-dir>
```

### Handoff-Ready Gate (Blocking)
```bash
scripts/validate-traceability.py <case-dir>
```

### XML Schema Validation (Blocking)
```bash
xmllint --schema schemas/investigation.xsd analysis/investigation.xml
xmllint --schema schemas/handoff.xsd analysis/handoff.xml
xmllint --schema schemas/resolution.xsd resolve/resolution.xml
```

### Artifact Count Limits
```bash
scripts/check-artifact-limits.sh <case-dir>
```

**Failure Mode**: Any validation failure BLOCKS lifecycle transition (collect_ready, handoff_ready, resolve_ready).

---



## Anti-Patterns (FORBIDDEN)

❌ **Creating intermediate summary files** between stages  
❌ **Duplicating evidence excerpts** outside investigation.xml  
❌ **Restating facts without traceability** (missing fact_ref attributes)  
❌ **Project-level case indexes** (violates "Status Truth Lives Inside the Case")  
❌ **Nested case subdirectories** (violates flat structure principle)  
❌ **Multiple investigation files** per case (only ONE fact-of-record allowed)

---

## Design Rationale

**Why so strict?**
- Prevents artifact drift (summaries diverging from source facts)
- Enforces traceability (every claim has provenance)
- Reduces cognitive load (fewer files to track)
- Optimizes for long-term clarity over completeness
- Makes cases resumable (clear fact-of-record ownership)

**Why include next_step in handoff?**
- Next-step recommendation is part of handoff delivery
- Consolidates "what to do next" decision with investigation output
- Reduces file count without losing information

**Why include commits in resolution?**
- Commits are delivery metadata, not standalone artifacts
- Resolution already tracks delivery outcomes
- Consolidates all "what shipped" info in one place

**Why keep verification.md separate?**
- Detailed verification evidence is distinct from structured outcome metadata
- Different audiences (engineers vs stakeholders)
- Markdown format better for test output, screenshots, logs
- XML for structured data, Markdown for narrative evidence

---

## Questions & Escalation

If you encounter a case where the minimal structure seems insufficient:
1. Document the limitation with a specific example
2. Propose the MINIMUM additional artifact needed
3. Justify why existing artifacts cannot absorb the information
4. Escalate to architecture review before creating new artifact types

**Default bias**: Prefer verbosity loss over artifact proliferation.
