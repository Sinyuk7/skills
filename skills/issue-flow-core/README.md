# issue-flow-core

Minimal issue triage framework.

## Overview

Issue-flow is a single-stage triage pipeline followed by an optional sync plugin:

1. **Triage** → intake, dispatch sub-agents for evidence excavation, synthesize a disposition (root cause, ranked directions, blocked, or a close-out type)
2. **Sync** (optional) → reflect the disposition on the bug tracker

There is no separate "resolve" stage. Code fixes happen in a fresh session after triage completes, so the fix gets a clean context instead of inheriting the triage transcript.

## Runtime Location

At runtime, issue-flow operates inside the current git repository:

```text
<git-repo-root>/.issue-flow/
├── TROUBLESHOOTING.md          # (optional) repo-local troubleshooting guide
└── cases/<case-id>/
    ├── case.yaml               # machine-readable state (status, disposition, etc.)
    └── investigation.md        # human-readable triage report
```

User-provided logs, screenshots, videos, and archives stay in their original locations. The case workspace stores only references and structured state.

## Skills

| Skill | Purpose | Entry Point |
|-------|---------|-------------|
| `issue-triage` | Intake + sub-agent evidence excavation + disposition | `/issue-triage` |
| `issue-overmind-sync` | Sync disposition to Overmind bug tracker | `/issue-overmind-sync` |

## Artifacts per triage run

Every `/issue-triage` invocation produces:

| Artifact | Persisted | Role |
|----------|-----------|------|
| `case.yaml` | yes | machine-readable state, including `disposition` |
| `investigation.md` | yes | human-readable report with cited findings |
| sub-agent `findings[] + gaps[]` | no (in-memory only) | structured excavation results that feed Phase 3 synthesis |

Deliberately NOT produced:
- `resolution.md` — removed with the old `issue-resolve` skill
- `disposition.md` — disposition is a field on `case.yaml`, not a separate file
- copies of raw logs — evidence stays at its original path

## Design Principles

1. One public triage entry point: `/issue-triage`
2. Two long-lived artifacts per case: `case.yaml` and `investigation.md`
3. Evidence stays in place and is referenced, not copied
4. Deterministic case-state updates belong in skill-local scripts (`scripts/case-state`)
5. Evidence excavation runs in **sub-agents**, not the main agent, to protect the main agent's context window
6. Main agent stays in the reasoning seat: plan excavation → synthesize findings → decide disposition

## Case Lifecycle

```text
[User reports issue / adds evidence]
               ↓
         /issue-triage
               ↓
 Phase 1: intake + target normalization
               ↓
 Phase 2a: plan excavation tasks (with optional TROUBLESHOOTING.md)
               ↓
 Phase 2b: dispatch sub-agents (parallel)
               ↓
 Phase 3: synthesize + decide disposition
               ↓
 ┌────────────────┬────────────────┬────────────────┐
 ↓                ↓                ↓                ↓
root_caused /    direction_only   blocked          duplicate /
already_fixed /       ↓              ↓              wont_fix /
cannot_reproduce   [new session    [user supplies   ...
       ↓          for deep dive]   more evidence]
/issue-overmind-
sync (optional)
```

`case.yaml.status` has exactly three values: `investigating`, `blocked`, `investigated`. The terminal reason (root_caused / direction_only / blocked / wont_fix / duplicate / already_fixed / cannot_reproduce) is stored in `case.yaml.disposition.type`.

## Repo-Specific Troubleshooting Guide (Optional)

Projects can supply a troubleshooting guide to bias Phase 2a task planning (symptom → TAG mapping, module call-chain, known failure modes). `/issue-triage` resolves it in this order:

1. **Already preloaded in context** by an upstream bootstrap skill. Example: `cmiotsdk-start-bugflow` reads its own `knowledge/TROUBLESHOOTING.md` before handing off.
2. **`<PROJECT_ROOT>/.issue-flow/TROUBLESHOOTING.md`** — the convention for repos that don't have a companion bootstrap skill.
3. **None** — Phase 2a proceeds with generic log patterns and records the gap in `case.yaml`.

Recommended shape: a symptom → TAG table, a module ownership map, key log landmarks, and a few known failure modes.

## Path Resolution

All skills resolve the owning repository explicitly:

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel)
CASE_DIR="$PROJECT_ROOT/.issue-flow/cases/<case-id>"
```

This keeps behavior stable regardless of where the skill is invoked from.

## Templates

The `templates/` directory contains reference artifacts:

- `templates/case.yaml` — case state reference (includes `disposition` examples)
- `templates/investigation.md` — investigation report reference
