---
name: issue-flow
description: Case-centric workflow for investigating issues across multiple sessions. Transforms raw materials into curated evidence, builds traceable handoffs, and optionally continues into resolution. Use when investigating bugs, building handoffs for other engineers, or managing issue workspaces. Supports three commands - collect (curate raw materials), handoff (synthesize investigation and build handoff), resolve (optional fix or final disposition).
---

# Issue-Flow

A case-centric workflow for investigating a single issue across multiple sessions.

The workflow is split into three progressive stages, each accessible as a command:

```text
raw sources -> curated evidence set -> structured handoff -> optional resolution
```

## Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| **collect** | Curate raw materials into case workspace | User provides logs, screenshots, archives, or issue notes |
| **handoff** | Synthesize investigation and build traceable handoff | Evidence is curated and ready for analysis |
| **resolve** | Optionally fix or record final disposition | Handoff is complete and resolution is needed |

## Intent Dispatch

Identify the user's intent, then load the corresponding command.

| User Intent | Load |
|-------------|------|
| "Investigate this issue", "Collect evidence", "Create a case" | `commands/collect.md` |
| "Build a handoff", "Analyze the evidence", "Create investigation summary" | `commands/handoff.md` |
| "Fix this", "Resolve the issue", "Verify the resolution" | `commands/resolve.md` |

If the user is moving through multiple stages in one session, start with the command that matches their immediate need, then load the next one when they are ready.

## Case Workspace Structure

Every issue gets its own case directory:

```text
<project-root>/.issue-flow/cases/<case-id>/
├── status.yaml              # Current lifecycle state
├── activity.md              # Append-only event log
├── sources.yaml             # Source registration and curation results
├── curated/                 # Curated evidence working set
│   ├── logs/
│   ├── media/
│   ├── notes/
│   ├── ocr/
│   └── excerpts/
├── analysis/                # Investigation and handoff artifacts
│   ├── investigation.xml
│   ├── handoff.xml
│   └── next-step.yaml
└── resolve/                 # Optional resolution artifacts
    ├── resolution.xml
    └── verification.md
```

## Product Principles

- **Case first**: Every issue gets its own directory
- **Curate once**: Collect narrows raw materials into working set, downstream stages work from curated evidence
- **Traceability always**: Downstream artifacts must point back to curated evidence
- **Soft readiness**: Dependencies unlock artifacts but don't force next stage
- **Human-readable**: Markdown, YAML, and XML over JSON
- **Status truth lives inside the case**: `status.yaml` is single source of truth

## Project-Level Context

Optional `ISSUE_CONTEXT.md` at project root provides:

- Common issue patterns
- Critical areas
- Architecture notes
- Investigation priorities

Commands read this file when present to incorporate project-specific context.

## Lifecycle States

Cases progress through explicit lifecycle states:

- `new` → `collecting` → `collected`
- `handoff_in_progress` → `handoff_ready`
- `resolve_in_progress` → `resolved_verified` / `resolved_unverified`
- `closed`

Special state: `blocked` (when progress depends on missing input)

## Readiness Checks

Lightweight readiness checker validates stage boundaries:

```bash
python scripts/check_readiness.py <case-path> <boundary>
```

Boundaries: `collect_ready`, `handoff_ready`, `resolve_ready`, `close_ready`

## Execution Rules

1. Use this file as a router, not as the full procedure.
2. Load the relevant command before executing detailed steps.
3. Pull in workflows, knowledge, templates, or scripts only when the command says they are needed.
4. Preserve official bundled dependencies as the source of truth unless the user explicitly asks to change them.

## Fallback

If the user's intent is ambiguous, clarify whether they want to:

1. Collect evidence and create/update a case
2. Build a handoff from existing evidence
3. Resolve an issue with an existing handoff

## Directory Guide

```text
issue-flow/
├── SKILL.md                 # This file (router)
├── commands/                # Stage-specific command instructions
│   ├── collect.md
│   ├── handoff.md
│   └── resolve.md
├── workflows/               # Detailed workflow documentation
│   ├── collect/
│   ├── handoff/
│   ├── resolve/
│   └── actions/
├── knowledge/               # Shared patterns and conventions
├── templates/               # Artifact templates
│   ├── case/
│   ├── analysis/
│   ├── resolve/
│   └── ISSUE_CONTEXT.md
└── scripts/                 # Helper scripts
    └── check_readiness.py
```

## Quick Reference

- For lifecycle and state management: `workflows/actions/lifecycle-management.md`
- For collect workflow details: `workflows/collect/collect-workflow.md`
- For handoff workflow details: `workflows/handoff/handoff-workflow.md`
- For resolve workflow details: `workflows/resolve/resolve-workflow.md`
- For core principles: `knowledge/issue-flow-principles.md`
- For artifact contracts: `knowledge/artifact-contracts.md`
- For case ID policy: `knowledge/case-id-policy.md`
