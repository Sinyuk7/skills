---
name: issue-investigate
description: Analyze collected evidence to find root cause. Use when evidence is collected and ready for analysis.
---

# Investigate

Read evidence, find patterns, identify root cause.

## Input

- `evidence/` — Collected logs, media, notes
- `collect.md` — Collection summary
- Repository code (read-only)

## Output

**investigation.md** containing:

1. **Summary** — 2-3 sentence issue description
2. **Evidence Analysis** — Key excerpts from logs/media with line numbers
3. **Root Cause** — What's broken and why
4. **Affected Code** — Files, functions, line numbers
5. **Proposed Fix** — What needs to change
6. **Next** — "Ready for resolution" or "Blocked: <reason>"

## Rules

- Quote evidence with source: "From `logs/app.log` lines 234-236:"
- Identify code locations: `src/auth/Service.java:42`
- Root cause MUST be grounded in evidence—no guessing
- If evidence insufficient, update `case.yaml`:
  ```yaml
  status: collected
  next_step:
    action: blocked
    note: "Need stack trace from staging"
  ```

## Done When

- Root cause identified with evidence
- Affected code located
- Fix direction clear
- `case.yaml` updated: `status: investigated`
