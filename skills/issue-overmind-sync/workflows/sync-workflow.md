# Overmind Sync Workflow

Use this workflow to directly update an Overmind bug through MCP as a plugin-style post-resolve action.

## Purpose

Translate case artifacts into direct Overmind MCP operations while keeping the case workspace as the local source of truth.

## Inputs

- A case workspace under `.issue-flow/cases/<case-id>/`
- An explicit `issueKey` or a case whose id already matches the Overmind issue
- Preferably `resolve/resolution.xml` and `resolve/verification.md`
- Optional user-specified field overrides such as assignee, test method, or issue type

## Outputs

- A concise user-facing execution summary with updated fields, skipped fields, failed fields, and any manual follow-up

## Procedure

### 1. Confirm MCP Works First

- Resolve the case path and issue key before making changes.
- Read `status.yaml` first. Prefer syncing after `resolved_verified`, `resolved_unverified`, or `closed`.
- If the case is earlier than resolve, only continue when the user explicitly wants a partial external update.
- Confirm that Overmind MCP is actually available in the current environment before doing any planning.
- Prefer verifying by actually calling a real read tool such as `EFFICIENCY_issue_get_issue_detail` instead of only looking for server metadata.
- If the tools are unavailable or unauthorized, stop immediately and report that limitation.

### 2. Read The Case

- Read `resolve/resolution.xml` for outcome type, summary, changed files, and delivery notes.
- Read `resolve/verification.md` for verification method, environment, and confidence.
- Read `analysis/handoff.xml` only when resolve artifacts are missing key context.
- Use explicit user instructions as highest-priority overrides. Everything else should be inferred from artifacts only when the inference is defensible.

### 3. Read The Current Issue In Overmind

- Call `EFFICIENCY_issue_get_issue_detail` first.
- Extract at least:
  - current readable field values
  - issue URL
  - issue type from the readable `类型` field
- Treat close/complete actions as separate from ordinary field updates. A visible `状态` field does not mean the update path will succeed.

### 4. Discover What Can Actually Be Edited

- Call `EFFICIENCY_issue_get_issue_editable_fields`.
- Use the actual response as the source of truth. Do not assume every bug field will appear there.
- Build a "core field gap list" by intersecting:
  - fields visible on the current issue
  - fields editable through the API
  - fields in the core business bucket from `references/field-policy.md`
  - fields whose current value is empty or still a placeholder such as `请选择`
- If a field is not returned by `EFFICIENCY_issue_get_issue_editable_fields`, do not claim it is writable.

### 5. Fetch Field Config For Enum-Like Fields

- For fields such as `问题类型`, `是否是共性问题`, `测试环境`, `测试方法`, `问题发生阶段`, call `EFFICIENCY_issue_get_issue_field_config` before updating.
- Pass both `name` and `issueType` when the field belongs to bug custom fields. This was verified in testing: calling with only `name` can fail.
- Use `fuzzyOptionName` to narrow large option lists when helpful.
- Prefer label writes when labels are unique. Fall back to option values only when labels are duplicated.

### 6. Build The Update Payload

Suggested value priority:

- Explicit user-provided values
- Directly stated values in `resolution.xml` and `verification.md`
- Safe inferences from the case
- Leave blank when the value is ambiguous

Write in this order:

- First pass: core missing fields only
- Second pass: secondary helpful fields such as `描述`
- Third pass: `状态` or close-only fields when the user explicitly asks for it

Common field sources:

- `解决方案`: resolution summary and concrete code/config change
- `问题原因`: root cause summary from handoff or resolution
- `问题单解决时间`: sync time or explicit resolution timestamp
- `测试方法`: inferred from verification evidence such as self-test, QA, or unavailable
- `测试环境`: inferred only when the environment is clearly stated
- `问题类型`: only when the issue can be mapped confidently to a known option

Do not invent fields like `所属迭代` when the case does not carry a trustworthy value. Mark them as skipped and explain why.

### 7. Execute The Update

- Call `EFFICIENCY_issue_update` with the chosen field map.
- A same-value update is acceptable as a safe smoke test when you need to verify the write path without changing business meaning.
- If `failedFields` is non-empty, treat the run as partial or failed based on what actually landed.

### 8. Verify

- Reread the issue with `EFFICIENCY_issue_get_issue_detail` after updates.
- Confirm the field values actually changed as expected.
- If `状态` update fails while ordinary fields succeed, report that explicitly instead of rolling back the good field updates.

### 9. Handle Failures As First-Class Outcomes

- If a field fails, record which field failed and why.
- If status update fails but other fields can be written, continue with partial sync instead of aborting everything.
- If a tool claims success but a follow-up read disagrees, treat the write as unverified and report it honestly.
- Retrying is allowed, but do not repeat the same failing mutation without new evidence about editability or required values.

### 10. Report The Actual Execution

Default behavior: do not write local plugin artifacts.

Report the execution summary directly to the user:

- target issue id and URL
- source case lifecycle at sync time
- core fields grouped into `filled`, `skipped`, `already_set`, and `not_editable`
- fields requested, applied, skipped, and failed
- close attempt result
- manual follow-up needed

Do not mirror Overmind status back into `status.yaml`. The local case lifecycle remains authoritative.

## Success Criteria

- Overmind changes are based on case artifacts, not ad hoc freehand edits.
- Partial success is explicit.
- Field discovery happens before enum updates.
- The workflow uses the real tools `EFFICIENCY_issue_get_issue_detail`, `EFFICIENCY_issue_get_issue_editable_fields`, `EFFICIENCY_issue_get_issue_field_config`, and `EFFICIENCY_issue_update`.
- The sync directly uses Overmind MCP instead of generating local placeholder files.
