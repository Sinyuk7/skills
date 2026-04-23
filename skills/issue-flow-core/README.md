# issue-flow-core

Minimal issue investigation framework.

## Overview

Issue-flow now uses a single front-door investigation stage:

1. **Investigate** → create or reuse the case, register evidence, normalize the target, and produce root cause or blocked status
2. **Resolve** → implement or document the resolution
3. **Sync** → optionally sync the resolved case to the bug tracker

## Runtime Location

At runtime, issue-flow operates inside the current git repository:

```text
<git-repo-root>/.issue-flow/cases/<case-id>/
├── case.yaml          # machine-readable state
├── investigation.md   # human-readable investigation report
└── resolution.md      # fix or disposition record
```

User-provided logs, screenshots, videos, and archives stay in their original locations.
The case workspace stores only references and structured investigation state.

## Skills

| Skill | Purpose | Entry Point |
|-------|---------|-------------|
| `issue-investigate` | Intake and investigation | `/issue-investigate` |
| `issue-resolve` | Fix, verify, or close the case | `/issue-resolve` |
| `issue-overmind-sync` | Sync resolved case to Overmind bug tracker | `/issue-overmind-sync` |

## Templates

The `templates/` directory contains reference artifacts:

- `templates/case.yaml` — case state reference
- `templates/investigation.md` — investigation report reference
- `templates/resolution.md` — resolution reference

## Design Principles

1. One public intake skill: `/issue-investigate`
2. Two long-lived investigation artifacts: `case.yaml` and `investigation.md`
3. Evidence stays in place and is referenced, not copied
4. Deterministic case-state updates belong in skill-local scripts
5. Evidence exploration should rely on generic search and chunked-read capabilities instead of vendor-specific parsers

## Case Lifecycle

```text
[User reports issue / adds evidence]
               ↓
       /issue-investigate
               ↓
   status: investigating
        ↓ yes         ↓ no / unclear
status: investigated   status: blocked
        ↓                    ↓
    /issue-resolve     [user provides more evidence or clarifies]
        ↓
   status: resolved
        ↓
/issue-overmind-sync (optional)
```

## Path Resolution

All skills should resolve the owning repository explicitly:

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel)
CASE_DIR="$PROJECT_ROOT/.issue-flow/cases/<case-id>"
```

This keeps behavior stable regardless of where the skill is invoked from.
