---
name: issue-triage-handoff
description: |
  Compress raw troubleshooting materials into a standardized handoff package.
  Use when: "triage this issue", "prepare handoff", "organize debugging materials",
  "what do we know about this bug".
---

# Issue Triage Handoff

Transform chaotic troubleshooting materials into structured handoff packages.

```
This skill does NOT: confirm root cause, generate patches, propose fixes
This skill DOES: compress noise, filter evidence, map code, produce traceable handoffs
```

## Intent Dispatch

Identify user intent, then load the corresponding workflow:

| Intent | Action |
|--------|--------|
| Create new handoff from raw materials | Load: `workflows/new-triage-handoff.md` |
| Refine existing handoff with new evidence | Load: `workflows/handoff-refinement.md` |
| Evaluate handoff readiness | Load: `workflows/handoff-evaluation.md` |

If ambiguous, ask user to clarify which mode.

## Execution Flow Pattern

```
D: Collect files/logs (deterministic)
D: Search for patterns (deterministic)
L: Extract structured info (LLM)
L: Synthesize findings (LLM)
D: Validate output (deterministic)
D: Write handoff (deterministic)
```

Minimize LLM context switches. Batch deterministic operations.

### Deterministic batching note (time-targeted)

- Use a single **event time** as the anchor: `--event "YYYY-MM-DDTHH:MM:SS"`
- Use a fixed window (default 60s): `--window-seconds 60`
- Deterministic pipeline:
  1. Select archives by **filename timestamp** within `EVENT_TIME±WINDOW_SECONDS` and expand only those
  2. Search error patterns / identifiers to get candidates
  3. Apply a second-stage **mtime window filter** to reduce noise
  4. Fail fast if no target files remain after filtering

## Quick Reference

- **Output schema**: `knowledge/handoff-schema.md`
- **Evidence rules**: `knowledge/evidence-protocol.md`
- **Core principles**: `knowledge/triage-principles.md`
- **Output template**: `templates/handoff-template.json`
- **Log collection**: `scripts/collect-log-evidence.sh`
+   - Example: `./scripts/collect-log-evidence.sh <log_dir> --event "YYYY-MM-DDTHH:MM:SS" --window-seconds 60 --identifiers "id1,id2"`
- **Code search**: `scripts/search-code-symbols.sh`
- **Schema validation**: `schemas/handoff.schema.json`

## Execution Rules

1. Load workflow before executing detailed steps
2. Pull knowledge/templates only when workflow requires them
3. Facts > Inferences > Questions (always distinguish)
4. Evidence from logs/code > human narrative

## Fallback

If user intent unclear, ask:
1. Create new handoff from raw materials?
2. Update existing handoff with new info?
3. Evaluate handoff quality and completeness?

## Directory Guide

```text
issue-triage-handoff/
├── SKILL.md
├── workflows/
│   ├── new-triage-handoff.md
│   ├── handoff-refinement.md
│   └── handoff-evaluation.md
├── knowledge/
│   ├── handoff-schema.md
│   ├── evidence-protocol.md
│   └── triage-principles.md
├── templates/
│   └── handoff-template.json
├── references/
├── scripts/
├── assets/
└── evals/
```