# issue-flow-core

Minimal issue investigation framework.

## Overview

Issue-flow is a 3-stage workflow for structured bug investigation:

1. **Collect** → Register evidence references
2. **Investigate** → Find root cause
3. **Resolve** → Fix and verify

## Runtime Location

At runtime, issue-flow operates inside the **current git repository**:

```
<git-repo-root>/.issue-flow/cases/<case-id>/
├── case.yaml          # State (single source of truth)
├── collect.md         # Stage 1 output: what was registered
├── investigation.md   # Stage 2 output: root cause analysis
└── resolution.md      # Stage 3 output: fix + verification
```

User-provided logs, screenshots, videos, and archives stay in their original locations. The case workspace stores references to those paths in `case.yaml` instead of copying raw evidence into the repository.

## Skills (Self-Contained)

Each skill is **fully self-contained** with embedded templates and step-by-step instructions:

| Skill | Purpose | Entry Point |
|-------|---------|-------------|
| `issue-collect` | Register user-provided materials | `/issue-collect` |
| `issue-investigate` | Analyze referenced evidence and find root cause | `/issue-investigate` |
| `issue-resolve` | Implement fix, verify, document | `/issue-resolve` |
| `issue-overmind-sync` | Sync resolved case to Overmind bug tracker | `/issue-overmind-sync` |

Skills do NOT depend on loading files from this directory at runtime.

## Templates (Reference Only)

The `templates/` directory contains **reference templates** for documentation purposes. Skills have their own embedded versions and do not load from here.

- `templates/case.yaml` — State structure reference
- `templates/collect.md` — Collection documentation reference
- `templates/investigation.md` — Investigation findings reference
- `templates/resolution.md` — Resolution documentation reference

## Design Principles

1. **Self-contained skills**: Each skill embeds all instructions and examples
2. **Explicit path resolution**: Skills use `git rev-parse --show-toplevel` to find project root
3. **Minimal artifacts**: 4 files per case (1 state + 3 stage outputs)
4. **Evidence stays in place**: Logs, screenshots, videos, and archives are referenced, not copied
5. **Single state file**: `case.yaml` is the only state file
6. **Progressive workflow**: Each stage adds exactly one file

## Case Lifecycle

```
[User reports issue]
        ↓
   /issue-collect
        ↓
   status: collected ←──────────┐
        ↓                       │
  /issue-investigate            │
        ↓                       │
   [evidence sufficient?]       │
        ↓ yes           no ↓    │
   status: investigated    next_step.action: blocked
        ↓                       │
   /issue-resolve          [user provides more evidence]
        ↓                       │
   status: resolved ────────────┘
        ↓
   /issue-overmind-sync (optional)
```

## Path Resolution

All skills resolve paths the same way:

```bash
# Get project root
PROJECT_ROOT=$(git rev-parse --show-toplevel)

# Case workspace
CASE_DIR="$PROJECT_ROOT/.issue-flow/cases/<case-id>"
```

Evidence references recorded in `case.yaml` should point to the original source paths so later stages can inspect the materials in place.

This ensures consistent behavior regardless of where the skill is invoked from.
