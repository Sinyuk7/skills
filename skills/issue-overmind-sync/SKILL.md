---
name: issue-overmind-sync
description: Use Overmind MCP to directly inspect and update an Overmind bug from issue-flow case artifacts. Use when a case already has `resolve/resolution.xml`, `resolve/verification.md`, or the user asks to "同步到 overmind", "回填问题原因/解决方案", or retry a failed Overmind update.
---

# Issue Overmind Sync

Plugin-style follow-up skill for issue-flow cases.

This is not a main `issue-flow-core` stage. It reads the shared case workspace, then directly operates on Overmind through MCP.

## When To Use

- A case is already `resolved_verified`, `resolved_unverified`, or `closed` and the user wants the result submitted to Overmind.
- The user asks to retry a failed Overmind update or backfill bug fields after `issue-resolve`.
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
- Resolve the case only from the current project workspace unless the user explicitly gives an absolute case path.
- Never default to `$HOME/.issue-flow/...` or infer a case path from `issueKey` alone.
- Before doing any planning, confirm the Overmind MCP tools are actually callable in the current environment.
- Use the real Overmind tools, not generic placeholders:
  - `EFFICIENCY_issue_get_issue_detail`
  - `EFFICIENCY_issue_get_issue_field_config`
  - `EFFICIENCY_issue_update`
- For enum-like fields, fetch field config first. In practice, `EFFICIENCY_issue_get_issue_field_config` needs `issueType` for bug custom fields like `问题类型`; calling it with only `name` may fail.
- Verify every write by rereading the issue or using returned `failedFields`. Do not trust a success message alone.
- Never attempt to update `状态` or `所属迭代` through MCP. If the user asks to close the bug, report that `状态` is manual-only in the UI and stop there.
- If no direct comment or reply tool exists, skip the external reply when there is no writable landing field.
- Only write external reply content when the current issue type already exposes a writable `备注说明` field.
- If Overmind MCP is unavailable in the current environment, say so plainly and stop immediately.
- Do not create `sync.yaml`, `integrations/overmind/`, or any other local placeholder artifacts.

## Issue Reply

When the sync is meant to reply inside the issue thread, produce a concise reply only if there is a writable landing field.

Template:

```text
【原因】
{surface_cause}

【处理方式】
{surface_fix}
```

Fill rules:

- Prefer one short paragraph per block.
- Keep the wording like a thread reply on the issue itself; do not include internal code paths, stack traces, or implementation details.
- If there is no writable landing field, skip the external reply entirely.
- Only write the reply into `备注说明` when that field is available to the current issue type.

## Exit

- `succeeded`: Overmind update landed and was verified by follow-up read.
- `partial`: some fields synced, others require manual follow-up or later retry.
- `failed`: no durable Overmind change was confirmed, or Overmind MCP was unavailable.
