---
name: issue-overmind-sync
description: Sync a resolved issue-flow case into Overmind by updating close status, bug fields, and repair notes from case artifacts. Use when a case already has `resolve/resolution.xml`, `resolve/verification.md`, or the user asks to "同步到 overmind", "更新 BUG 状态", "回填问题原因/解决方案", or retry a failed Overmind update.
---

# Issue Overmind Sync

Plugin-style follow-up skill for issue-flow cases.

This is not a main `issue-flow-core` stage. It reads the shared case workspace, then performs an optional external-system sync to Overmind.

## When To Use

- A case is already `resolved_verified`, `resolved_unverified`, or `closed` and the user wants the result submitted to Overmind.
- The user asks to close a bug, retry a failed Overmind update, or backfill bug fields after `issue-resolve`.
- The user has an `issueKey` and wants a best-effort sync from case artifacts into Overmind without reopening the resolve stage.

## Load These Files First

- `workflows/sync-workflow.md`
- `references/chain-analysis.md`
- `references/field-policy.md`

Load the template only when writing plugin artifacts:

- `templates/overmind-sync.yaml`

## Mission

Read a resolved case and submit the handling status to Overmind without making Overmind the source of truth for the case.

## Non-Negotiables

- Treat `.issue-flow/cases/<case-id>/status.yaml` as the authoritative lifecycle source.
- Do not rewrite `resolve/resolution.xml` or `resolve/verification.md` to fit Overmind.
- Require an explicit case target or `issueKey` before writing.
- Discover editable fields before building the update payload.
- Verify every write by rereading the issue or using returned failure details. Do not trust a success message alone.

## Plugin Boundary

Own plugin artifacts under:

```text
<case-root>/integrations/overmind/
```

Recommended outputs:

- `integrations/overmind/sync.yaml`
- optional history notes under `integrations/overmind/history/`

## Exit

- `succeeded`: Overmind update landed and was verified.
- `partial`: some fields synced, others require manual follow-up or later retry.
- `failed`: no durable Overmind change was confirmed.
