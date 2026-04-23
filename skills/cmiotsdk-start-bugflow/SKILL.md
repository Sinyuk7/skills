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

The script `scripts/start-bugfix.sh` is authoritative for repo identity. If it reports that the current repo is not `cmiotsdk`, stop and tell the user to run the workflow from the correct repository.

## Step 2: Validate Ticket ID

Pattern: `^[A-Z]+-[0-9]+$`

- Missing → ask for the ticket ID
- Invalid → stop with the expected pattern

## Step 3: Bootstrap the branch

Run:

```bash
bash "$SKILL_DIR/scripts/start-bugfix.sh" "<TICKET-ID>"
```

The script owns all deterministic git safety checks.

## Step 4: Optional handoff to /issue-investigate

### Payload mapping

| Wrapper field | `/issue-investigate` usage |
|---------------|----------------------------|
| `ticket_id` | `case_id` |
| `summary` | `case.yaml.summary` |
| `user_context` | `case.yaml.user_context` |
| `materials` | `case.yaml.evidence_sources` |
| `code_references` | `case.yaml.evidence_sources` as `kind: code_reference` |

If `auto_enter_investigate` is `true`:

```text
Branch bugfix/<TICKET-ID> ready (from origin/develop).
Entering /issue-investigate...
```

`/issue-investigate` takes over and owns case creation, evidence registration, and investigation.

If `auto_enter_investigate` is `false`, stop after reporting the branch and tell the user to run `/issue-investigate` when ready.

## Rules

- Do not create `case.yaml`, `investigation.md`, or any raw-evidence directories in this wrapper
- Do not read, analyze, or modify source code
- Do not duplicate `/issue-investigate` case-writing logic
- Do not run on repositories other than `cmiotsdk`
- Preserve all user-provided materials for transparent forwarding

## Done When

- Repository confirmed as `cmiotsdk`
- Branch `bugfix/<TICKET-ID>` is active
- If `auto_enter_investigate=true`, the payload is handed to `/issue-investigate`
- If `auto_enter_investigate=false`, the user is told how to continue
