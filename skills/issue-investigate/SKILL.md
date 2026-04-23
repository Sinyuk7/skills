---
name: issue-investigate
description: Own intake and investigation for issue-flow cases. Use when a user reports a new issue, adds evidence to an existing case, or wants root cause analysis anchored to a specific question or time.
---

# Issue Investigate

Single entry point for issue-flow intake and investigation.

## Capability Contract

Kind: routable skill

Owns:
- create or reuse a case
- register or merge evidence references
- normalize the investigation target
- analyze evidence and relevant code
- write `investigation.md`
- update `case.yaml`

Does Not Own:
- code modification
- fix implementation
- final bug-tracker sync

Requires:
- user context and/or referenced materials
- existing `case.yaml` when continuing a case

Produces:
- `case.yaml`
- `investigation.md`

Needs Capabilities:
- repository path resolution
- fuzzy search across evidence
- chunked file reads
- archive listing or extraction when safe
- media inspection when needed

Execution Surface:
- Workflow: [workflows/investigate.md](/Users/shenyeke01/Documents/Workspace/skills/skills/issue-investigate/workflows/investigate.md)
- Public execution entry:
  - [scripts/case-state](/Users/shenyeke01/Documents/Workspace/skills/skills/issue-investigate/scripts/case-state)
- Support resources:
  - [schemas/case.yaml](/Users/shenyeke01/Documents/Workspace/skills/skills/issue-investigate/schemas/case.yaml)
  - [templates/investigation.md](/Users/shenyeke01/Documents/Workspace/skills/skills/issue-investigate/templates/investigation.md)
- Internal implementation detail:
  - [scripts/case_state.py](/Users/shenyeke01/Documents/Workspace/skills/skills/issue-investigate/scripts/case_state.py)
- Evals: [evals/evals.json](/Users/shenyeke01/Documents/Workspace/skills/skills/issue-investigate/evals/evals.json)

Refuses When:
- repository ownership is ambiguous
- the primary investigation target remains ambiguous
- the user asks for code edits during investigation

Hands Off To:
- `/issue-resolve` after the case reaches `status: investigated`

## Operating Rules

- Use the skill-local wrapper `scripts/case-state` for case creation and state updates; do not hand-maintain `case.yaml`.
- Use generic search and chunked-read capabilities to explore evidence. Do not assume one vendor log format, one timestamp format, or one archive layout.
- Normalize the target before deep analysis:
  - `primary_question`
  - `primary_time_anchor`
  - `named_stakeholders`
- Write a one-line working statement near the top of `investigation.md` before presenting findings.
- Keep the main conclusion anchored to the primary target. If the evidence points at a different timestamp or question, stop and mark the case blocked instead of drifting to a different conclusion.
- Do not copy raw evidence into `.issue-flow/`.
- Do not modify source code during this skill.

## When To Ask The User

Ask instead of guessing when:

- more than one repository could own the case
- multiple candidate anchors remain unresolved
- the required evidence path is missing
- the observed failure does not match the requested anchor

## Handoff

When the investigation is complete, tell the user:

> Case `<case-id>` is investigated. Root cause: <summary>. Run `/issue-resolve` to implement or document the resolution.
