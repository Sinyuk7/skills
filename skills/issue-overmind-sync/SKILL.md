---
name: issue-overmind-sync
description: Use Overmind MCP to directly inspect and update an Overmind bug from issue-flow case artifacts. Use when a case already has `resolve/resolution.xml`, `resolve/verification.md`, or the user asks to "同步到 overmind", "更新 BUG 状态", "回填问题原因/解决方案", or retry a failed Overmind update.
---

# Issue Overmind Sync

Plugin-style follow-up skill for issue-flow cases.

This is not a main `issue-flow-core` stage. It reads the shared case workspace, then directly operates on Overmind through MCP.

## When To Use

- A case is already `resolved_verified`, `resolved_unverified`, or `closed` and the user wants the result submitted to Overmind.
- The user asks to close a bug, retry a failed Overmind update, or backfill bug fields after `issue-resolve`.
- The user has an `issueKey` and wants a best-effort sync from case artifacts into Overmind without reopening the resolve stage.

## Load These Files First

- `workflows/sync-workflow.md`
- `references/chain-analysis.md`
- `references/field-policy.md`

## Mission

Read a resolved case and directly update the target issue in Overmind through MCP.

## Non-Negotiables

- Treat `.issue-flow/cases/<case-id>/status.yaml` as the authoritative lifecycle source.
- Do not rewrite `resolve/resolution.xml` or `resolve/verification.md` to fit Overmind.
- Require an explicit case target or `issueKey` before writing to Overmind.
- Discover editable fields before building the update payload.
- Verify every write by rereading the issue or using returned `failedFields`. Do not trust a success message alone.
- If Overmind MCP is unavailable in the current environment, say so plainly and stop immediately.
- Do not create `sync.yaml`, `integrations/overmind/`, or any other local placeholder artifacts unless the user explicitly asks for a local audit record.

## Exit

- `succeeded`: Overmind update landed and was verified by follow-up read.
- `partial`: some fields synced, others require manual follow-up or later retry.
- `failed`: no durable Overmind change was confirmed, or Overmind MCP was unavailable.
