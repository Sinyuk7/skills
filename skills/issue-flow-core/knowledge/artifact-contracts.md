# Artifact Contracts

## Minimal Artifact Set

Issue-flow keeps a fixed, minimal artifact set. Anything else is out of contract.

### Core Principles
1. **One artifact per concept** — Do not duplicate information across files
2. **Traceability is mandatory** — All downstream facts MUST reference upstream IDs
3. **No unsupported artifacts** — If an artifact does not support a decision or verification step, do not add it

---

## Case Management

| Artifact | Format | Purpose | Owner |
|----------|--------|---------|-------|
| `case/status.yaml` | YAML | Lifecycle state + readiness flags | All stages (read/write) |
| `case/sources.yaml` | YAML | Source registration + mutation log | Collect (write), Handoff/Resolve (read) |
| `case/activity.md` | Markdown | Append-only event log | All stages (append) |

**Constraint**: `status.yaml` is the single source of truth for lifecycle state. No project-level case indexes allowed.

---

## Collect Stage

**Inputs**: User-provided issue materials (external paths)

**Outputs**:
- `curated/*` directories — evidence workspace for logs, media, notes, excerpts, ocr
- `case/sources.yaml`
- `case/status.yaml`
- `case/activity.md`

**Rule**: no synthesis artifacts at this stage.

---

## Handoff Stage

**Inputs**: `curated/*`, `sources.yaml`, `ISSUE_CONTEXT.md`

**Outputs**:
- `analysis/investigation.xml` — evidence refs, excerpts, confirmed facts, inferences, open questions, details
- `analysis/handoff.xml` — summary, code context, known items, next_step, references

**Traceability Constraint**: Every `<known>` item in `handoff.xml` MUST have `fact_ref="F-XXX"` pointing to a confirmed fact in `investigation.xml`. If a fact is backed by a log, it MUST also point to a matching `source_excerpt` from the same log file.

---

## Resolve Stage

**Inputs**: `analysis/handoff.xml`, `analysis/investigation.xml`, `ISSUE_CONTEXT.md`

**Outputs**:
- `resolve/resolution.xml` — outcome, delivery metadata, verification summary
- `resolve/verification.md` — verification plan, results, evidence

**Rule**: `resolution.xml` and `verification.md` are separate on purpose; keep metadata in XML and evidence in Markdown.

---

## Artifact Count

**Total artifacts per complete case**: 8
- 3 case management: `status.yaml`, `sources.yaml`, `activity.md`
- 1 evidence workspace: `curated/*`
- 2 handoff: `investigation.xml`, `handoff.xml`
- 2 resolve: `resolution.xml`, `verification.md`
- 1 shared project context: `ISSUE_CONTEXT.md`

---

## Validation & Enforcement

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

**Failure Mode**: Any validation failure BLOCKS the relevant lifecycle transition.

---

## Anti-Patterns (FORBIDDEN)

❌ **Creating intermediate summary files** between stages  
❌ **Duplicating evidence excerpts** outside investigation.xml  
❌ **Restating facts without traceability** (missing fact_ref attributes)  
❌ **Project-level case indexes** (violates "Status Truth Lives Inside the Case")  
❌ **Nested case subdirectories** (violates flat structure principle)  
❌ **Multiple investigation files** per case (only ONE fact-of-record allowed)
