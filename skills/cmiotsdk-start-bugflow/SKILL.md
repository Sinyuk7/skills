---
name: cmiotsdk-start-bugflow
description: Start a cmiotsdk bugfix workflow. Create or reuse a bugfix branch from origin/develop. If auto_enter_investigate=true (default), hand off the original payload to /issue-triage; otherwise stop after branch bootstrap.
disable-model-invocation: true
argument-hint: "[TICKET-ID] [optional context, logs, screenshots]"
---

# cmiotsdk Start Bugflow

Repo-aware wrapper that bootstraps a `bugfix/<TICKET-ID>` branch in `cmiotsdk`, then hands the same payload to `/issue-triage` only when `auto_enter_investigate=true`.

## Input

| Field | Required | Description |
|-------|----------|-------------|
| `ticket_id` | Yes | e.g. `OMMUSIC-3397323` |
| `summary` | No | One-line issue description |
| `user_context` | No | Original issue description |
| `materials` | No | Logs, screenshots, archives, notes |
| `code_references` | No | Relevant source paths |
| `auto_enter_investigate` | No | Default `true`. When `true`, hand off to `/issue-triage` after branch bootstrap. When `false`, stop after branch bootstrap. |

Forward every user-provided material to `/issue-triage` without modification, and tell the user which materials were forwarded.

## Step 1: Validate Repository

Validate that the current repository is `cmiotsdk`. Run the skill-local wrapper entry; if it reports that the current repo is not `cmiotsdk`, stop and tell the user to run the workflow from the correct repository.

If repository validation still fails after the user confirms they are in the intended repo, tell them to verify that `origin` points to the `cmiotsdk` remote and re-run the workflow. Do not fall through to `/issue-triage` when repository validation fails.

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

If the script exits non-zero, stop immediately. Report the script error to the user, suggest checking repository state or git remote configuration as indicated by the error, and do not hand off to `/issue-triage`.

## Step 4: Conditional handoff to /issue-triage

### Payload mapping

| Wrapper field | `/issue-triage` usage |
|---------------|-----------------------|
| `ticket_id` | Triage case identifier |
| `summary` | Case summary |
| `user_context` | Original issue description |
| `materials` | Evidence inputs |
| `code_references` | Code pointers forwarded with the evidence inputs |

If `auto_enter_investigate` is `true`:

```text
Branch bugfix/<TICKET-ID> ready (from origin/develop).
Load knowledge/TROUBLESHOOTING.md.
Entering /issue-triage...
```

Before handing off, load the skill-local knowledge file `knowledge/TROUBLESHOOTING.md` so `/issue-triage`'s Phase 2a planning starts with cmiotsdk-specific log tags, module paths, and search hints.

Emit one minimal evidence chain before the handoff:

```text
source: knowledge/TROUBLESHOOTING.md
finding: cmiotsdk has repo-specific troubleshooting tags, module ownership hints, and log search order
conclusion: preload this guide before /issue-triage so Phase 2a excavation planning starts from the repo-specific diagnostic context
```

`/issue-triage` takes over and owns case creation, evidence excavation (via sub-agents), and disposition.

If `auto_enter_investigate` is `false`, stop after reporting the branch and tell the user to run `/issue-triage` when ready.

## Rules

- Scope: validate repository context, validate ticket ID, bootstrap or reuse `bugfix/<TICKET-ID>`, and forward the original payload to `/issue-triage` only when `auto_enter_investigate=true`
- Non-goals: evidence collection, case workspace creation, and source-code analysis
- Refuse when the current repository is not `cmiotsdk`
- Forward all user-provided materials without modification and report the forwarded items to the user
- Stop on any wrapper-script failure and do not continue into `/issue-triage`

## Done When

- Repository confirmed as `cmiotsdk`
- Branch `bugfix/<TICKET-ID>` is active
- If `auto_enter_investigate=true`, `knowledge/TROUBLESHOOTING.md` is loaded, one minimal evidence chain is emitted, and the payload is handed to `/issue-triage`
- If `auto_enter_investigate=false`, the user is told how to continue
