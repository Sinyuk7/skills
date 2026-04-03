---
name: issue-overmind-sync
description: Sync resolve artifacts to Overmind bug fields via MCP. Use after issue-resolve completes, when retrying a failed Overmind update, or when filling remaining bug fields from case artifacts. This is a post-resolve plugin only - do not use for investigation, fixing, or building handoffs.
---

# Issue Overmind Sync

Post-resolve plugin that reads `resolve/resolution.md` and `investigation.md`, then fills Overmind bug fields through MCP. For older cases, fall back to `resolve/resolution.xml` and `resolve/verification.md` if those are the only artifacts available.

## When To Use

- Case has resolve artifacts and needs Overmind fields filled
- Retry a failed Overmind update
- Write issue-thread reply to `备注说明`

## Procedure

### 1. Validate Environment

- Confirm Overmind MCP is available by calling `EFFICIENCY_issue_get_issue_detail`
- Require explicit `issueKey` before any write
- Resolve case path from current repo only — never fall back to `$HOME/.issue-flow/`

### 2. Read Artifacts

From the resolved case path:
- `resolve/resolution.md` — outcome, summary, changes, verification context
- `investigation.md` — root cause and affected code
- `resolve/resolution.xml` / `resolve/verification.md` — fallback for older cases only
- `analysis/handoff.xml` — legacy fallback only when the case predates the markdown migration

### 3. Fetch Current Issue

Call `EFFICIENCY_issue_get_issue_detail` to get:
- Current field values and placeholders (`请选择`)
- Issue type from `类型` field
- Issue URL

### 4. Fetch Field Config

For enum fields, call `EFFICIENCY_issue_get_issue_field_config` with both `name` and `issueType`.

### 5. Build Update Payload

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

### 6. Execute & Verify

```
EFFICIENCY_issue_update → check failedFields → EFFICIENCY_issue_get_issue_detail
```

If field fails, record it and continue with remaining fields.

### 7. Issue Reply (Optional)

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
