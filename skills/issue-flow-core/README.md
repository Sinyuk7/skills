# issue-flow-core

Minimal issue investigation framework.

## Architecture

This directory contains **templates only**. At runtime, issue-flow operates inside the current repository:

```
<repo>/.issue-flow/cases/<case-id>/
├── case.yaml          # State
├── evidence/          # Raw materials
│   ├── logs/
│   ├── media/
│   └── notes/
├── collect.md         # What was collected
├── investigation.md   # Root cause analysis
└── resolution.md      # Fix + verification (if resolved)
```

## Stages

1. **Collect** (`issue-collect`) — Curate user-provided materials into evidence/
2. **Investigate** (`issue-investigate`) — Analyze evidence, find root cause
3. **Resolve** (`issue-resolve`) — Fix, verify, document

## Templates

- `templates/case.yaml` — State structure
- `templates/collect.md` — Collection documentation
- `templates/investigation.md` — Investigation findings
- `templates/resolution.md` — Resolution + verification

## Design Principles

- **Minimal artifacts**: 4 files per case (1 state + 3 stage outputs)
- **No ceremony**: Skills are self-contained, no mandatory file loads
- **Markdown native**: No XML, no validation scripts
- **State in one place**: `case.yaml` is the only state file
- **Progressive**: Each stage adds one file

## User-Facing Skills

- `../issue-collect` — Stage 1
- `../issue-investigate` — Stage 2 
- `../issue-resolve` — Stage 3
