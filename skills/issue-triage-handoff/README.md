# Issue Triage Handoff

Compress troubleshooting materials (logs, screenshots, chat) into structured handoff packages.

## Quick Start

Entry point: `SKILL.md` → dispatches to workflows in `workflows/`

## Optional: Project Context

**When**: Your team owns multiple components (e.g., client SDK + backend server)

**Why**: Prevents wrong recommendations like "check external server" when you ARE the server team

**How**:
```bash
# 1. Copy template to your project
cp knowledge/project-context.md ./triage/project-context.md

# 2. Edit ./triage/project-context.md
team_role: "provider"          # provider|consumer|integration|platform
ownership:
  our_code:
    - "Client SDK"
    - "backend API server"     # Key: clarify what you own
forbidden_assumptions:
  - "Assume backend is external"

# 3. Run triage — auto-loads context in Step 6.5
```

**Example**: `/Users/you/project/triage/project-context.md`

## Key Features

- Triage decision gate (avoid full pipeline for simple cases)
- Dual-layer output: summary (≤120 lines) + optional evidence attachment
- Multimodal: images (OCR, visual signals), videos
- Evidence inventory: all files accounted, no silent skips

## Docs

- `AGENTS.md` — full documentation, conventions, anti-patterns
- `knowledge/triage-principles.md` — 15 core principles
- `knowledge/project-context.md` — template with examples

**Dependencies**: bash 3.2+, python3 | Optional: exiftool, tesseract, ffprobe
