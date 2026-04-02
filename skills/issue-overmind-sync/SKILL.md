---
name: issue-overmind-sync
description: Thin post-resolve plugin. Use after `issue-resolve` to turn `resolve/resolution.xml` and `resolve/verification.md` into Overmind field updates or an issue-thread reply through MCP.
---

# Issue Overmind Sync

Thin post-resolve plugin for issue-flow cases.

This is not a main `issue-flow-core` stage. It reads resolve artifacts, then fills the remaining Overmind gaps through MCP.

## When To Use

- A case already has resolve artifacts and the user wants the remaining Overmind fields filled.
- The user asks to retry a failed Overmind update after `issue-resolve`.
- The user wants an issue-thread reply written to `备注说明` when that field is available.

## Load These Files First

- `workflows/sync-workflow.md`
- `references/chain-analysis.md`
- `references/field-policy.md`

## Mission

Read the resolve artifacts and fill the remaining Overmind bug fields through MCP.

## Non-Negotiables

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
