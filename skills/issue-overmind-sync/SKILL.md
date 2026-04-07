---
name: issue-overmind-sync
description: Sync resolve artifacts to Overmind bug fields via MCP. Use after issue-resolve completes, when retrying a failed Overmind update, or when filling remaining bug fields from case artifacts. This is a post-resolve plugin only - do not use for investigation, fixing, or building handoffs.
---

# Issue Overmind Sync

Post-resolve plugin that syncs case artifacts to Overmind bug tracking system via MCP.

## When To Use

- Case has `status: resolved` and needs Overmind fields filled
- Retry a failed Overmind update
- Write issue-thread reply to `备注说明`

## Step 1: Locate Case Workspace

Execute to get project root:

```bash
git rev-parse --show-toplevel
```

Then find the case:

```
PROJECT_ROOT/.issue-flow/cases/<case-id>/
```

**Never** fall back to `$HOME/.issue-flow/` — only use project-local cases.

## Step 2: Validate Environment

Confirm Overmind MCP is available:

```
EFFICIENCY_issue_get_issue_detail(issueKey: "<user-provided-key>")
```

- **REQUIRE** explicit `issueKey` from user before any write
- If MCP unavailable, **STOP** and report to user

## Step 3: Read Case Artifacts

From the case workspace, read:

| File | Purpose |
|------|---------|
| `case.yaml` | Verify `status: resolved` |
| `resolution.md` | Fix details, verification context |
| `investigation.md` | Root cause and affected code |

**Legacy fallback** (only for older cases):
- `resolve/resolution.md`
- `resolve/resolution.xml`
- `resolve/verification.md`
- `analysis/handoff.xml`

## Step 4: Fetch Current Issue

Call `EFFICIENCY_issue_get_issue_detail` to get:
- Current field values and placeholders (`请选择`)
- Issue type from `类型` field
- Issue URL

## Step 5: Fetch Field Config

For enum fields, call `EFFICIENCY_issue_get_issue_field_config` with both `name` and `issueType`.

## Step 6: Build Update Payload

**Value priority:** User instruction > Artifact value > Safe inference > Skip

**Field mapping:**

| Field | Source |
|-------|--------|
| `解决方案` | resolution.md fix applied + fix details |
| `问题原因` | investigation.md root cause |
| `问题单解决时间` | Resolution date or sync date (`YYYY-MM-DD` only) |
| `测试方法` | resolution.md verification context → `开发自测` / `QA测试` |
| `测试环境` | resolution.md verification context when clearly stated |
| `问题类型` | Only with confident mapping |
| `备注说明` | Issue reply (if field is writable) |

**Never write:** `状态`, `所属迭代`

## Step 7: Execute & Verify

```
EFFICIENCY_issue_update → check failedFields → EFFICIENCY_issue_get_issue_detail
```

If field fails, record it and continue with remaining fields.

## Step 8: Issue Reply (Optional)

Only write to `备注说明` if the field is writable:

```text
【AI分析】
{surface_cause — one short paragraph, no code paths}

【AI自动回复】
{surface_fix — one short paragraph, no implementation details}
```

## Output

Report directly to user:
- Target issue ID and URL
- Fields: filled, skipped, already_set, failed
- Reply handling result
- Manual follow-up needed

## Non-Negotiables

- Do not rewrite resolve artifacts to fit Overmind
- Do not create local artifacts (`sync.yaml`, `integrations/`)
- Do not retry `问题单解决时间` with alternate formats
- Verify every write by rereading — success message alone is not evidence
- If MCP unavailable, stop immediately and report

## Exit States

- `succeeded` — Update verified by follow-up read
- `partial` — Some fields synced, others need manual action
- `failed` — No confirmed change or MCP unavailable
