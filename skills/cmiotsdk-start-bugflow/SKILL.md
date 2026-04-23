---
name: cmiotsdk-start-bugflow
description: Start a cmiotsdk bugfix workflow. Create or reuse bugfix/<TICKET-ID> from origin/develop, then optionally hand off the same payload to /issue-investigate.
disable-model-invocation: true
argument-hint: "[TICKET-ID] [optional context, logs, screenshots]"
allowed-tools: Bash Read Grep
---

# cmiotsdk Start Bugflow

Repo-aware wrapper that bootstraps a `bugfix/<TICKET-ID>` branch in `cmiotsdk`, then optionally hands the same payload to `/issue-investigate`.

## Input

| Field | Required | Description |
|-------|----------|-------------|
| `ticket_id` | Yes | e.g. `OMMUSIC-3397323` |
| `summary` | No | One-line issue description |
| `user_context` | No | Original issue description |
| `materials` | No | Logs, screenshots, archives, notes |
| `code_references` | No | Relevant source paths |
| `auto_enter_investigate` | No | Default `true`. Set `false` to stop after branch bootstrap. |

Preserve every user-provided material for transparent forwarding.

## Step 1: Validate Repository

Validate that the current repository is `cmiotsdk`. Run the skill-local wrapper entry; if it reports that the current repo is not `cmiotsdk`, stop and tell the user to run the workflow from the correct repository.

## Step 2: Validate Ticket ID

Pattern: `^[A-Z]+-[0-9]+$`

- Missing → ask for the ticket ID
- Invalid → stop with the expected pattern

## Step 3: Bootstrap the branch

Run:

```bash
bash "$SKILL_DIR/scripts/start-bugfix.sh" "<TICKET-ID>"
```

The wrapper entry resolves the skill-local implementation and runs the deterministic git safety checks and branch creation flow.

## Step 4: Optional handoff to /issue-investigate

### Payload mapping

| Wrapper field | `/issue-investigate` usage |
|---------------|----------------------------|
| `ticket_id` | Investigation case identifier |
| `summary` | Case summary |
| `user_context` | Original issue description |
| `materials` | Evidence inputs |
| `code_references` | Code pointers forwarded with the evidence inputs |

If `auto_enter_investigate` is `true`:

```text
Branch bugfix/<TICKET-ID> ready (from origin/develop).
Load knowledge/TROUBLESHOOTING.md.
Entering /issue-investigate...
```

Before handing off, load the skill-local knowledge file `knowledge/TROUBLESHOOTING.md` so the investigation starts with cmiotsdk-specific log tags, module paths, and search hints.

Emit one minimal evidence chain before the handoff:

```text
source: knowledge/TROUBLESHOOTING.md
finding: cmiotsdk has repo-specific troubleshooting tags, module ownership hints, and log search order
conclusion: preload this guide before /issue-investigate so evidence exploration starts from the repo-specific diagnostic context
```

`/issue-investigate` takes over and owns case creation, evidence registration, and investigation.

If `auto_enter_investigate` is `false`, stop after reporting the branch and tell the user to run `/issue-investigate` when ready.

## Rules

- Scope: validate repository context, validate ticket ID, bootstrap or reuse `bugfix/<TICKET-ID>`, and optionally forward the original payload to `/issue-investigate`
- Non-goals: evidence collection, case workspace creation, and source-code analysis
- Refuse when the current repository is not `cmiotsdk`
- Preserve all user-provided materials for transparent forwarding

## Done When

- Repository confirmed as `cmiotsdk`
- Branch `bugfix/<TICKET-ID>` is active
- If `auto_enter_investigate=true`, `knowledge/TROUBLESHOOTING.md` is loaded, one minimal evidence chain is emitted, and the payload is handed to `/issue-investigate`
- If `auto_enter_investigate=false`, the user is told how to continue
