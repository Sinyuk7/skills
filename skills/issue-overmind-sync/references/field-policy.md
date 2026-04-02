# Overmind Field Policy

Keep the policy simple: discover the current bug form first, then fill only the core missing fields we can justify.

This skill is execution-oriented:

- Default behavior is to update Overmind directly through MCP.
- If MCP is unavailable, stop and report that fact.
- Do not create local sync plans or sidecar files unless the user explicitly asks for them.
- Base writable decisions on live responses from `EFFICIENCY_issue_get_issue_editable_fields`, not on assumptions from old cases.

## Assumption

Different Overmind bug types may expose different fields, defaults, and writable paths.

Do not hardcode one universal schema.

## Primary Goal

Prefer this outcome order:

1. Fill the core business fields that are still missing or still show placeholder values such as `请选择`
2. Fill secondary explanatory fields when the source is strong
3. Attempt close or status transition only after the core fields are in a good state

## How To Detect "Needs Fill"

Treat a field as needing attention when all of these are true:

- the field is visible on the current issue
- the field is editable through the available API path
- the current value is empty, null, blank, or a placeholder such as `请选择`

Do not treat already-populated fields as mandatory rewrites unless the user explicitly asks to override them.

## Core Field Bucket

For car-bug style issues like the example in `提交 BUG.md`, prioritize this bucket:

- `问题单解决时间`
- `问题类型`
- `是否是共性问题`
- `经办人`
- `测试环境`
- `测试方法`
- `问题发生阶段`
- `所属迭代`
- `解决方案`
- `问题原因`

`问题发生时间` is usually source context rather than a sync-time derived field. Read it for context, but do not overwrite it unless the user explicitly requests correction.

## Source Priority

Use this priority order for values:

1. Explicit user instruction in the current request
2. Existing case artifacts such as `resolve/resolution.xml` and `resolve/verification.md`
3. Safe inference from issue context or handoff artifacts
4. Skip the field

If a value would be a guess, skip it.

## Conservative Defaults

Safe defaults are allowed only when they are genuinely low-risk:

- `问题单解决时间`: current sync time when the case is already resolved and no better timestamp exists
- `经办人`: current assignee when the user explicitly confirms the owner or the issue already shows that owner

Everything else should prefer evidence over defaults.

## Field-Specific Notes

### `问题类型`

- Usually enum-backed
- Requires fetching the option list first
- In testing, custom bug fields like this required `issueType` when calling `EFFICIENCY_issue_get_issue_field_config`
- Fill only when there is a confident mapping, for example this case strongly suggests `进度错误`

### `是否是共性问题`

- Usually enum-backed yes/no
- Fill only with explicit user input or strong case evidence

### `测试环境`

- Prefer direct evidence from verification notes
- For this class of case, `台架` may be valid only if the case clearly states that environment

### `测试方法`

- Map from verification mode
- Typical safe mapping: developer self-check -> `开发自测`, QA verification -> `QA测试`

### `问题发生阶段`

- Usually requires product context
- Fill only when the issue context clearly indicates a stage such as `应用适配中`

### `所属迭代`

- High-risk field because it often expects an internal object id rather than plain text
- Default behavior: detect that it is missing, report it, and skip auto-fill unless a trustworthy id or mapping source is available

### `解决方案`

- Prefer the concrete patch summary from `resolve/resolution.xml`
- Do not overwrite a good existing solution unless the user asks

### `问题原因`

- Prefer the root cause summary from handoff or resolve
- Keep it short and causal, not a full debugging diary

## Recommended Execution Order

1. Call `EFFICIENCY_issue_get_issue_detail`
2. Call `EFFICIENCY_issue_get_issue_editable_fields`
3. For enum-like fields, call `EFFICIENCY_issue_get_issue_field_config`
4. Intersect with the core field bucket
5. Split into:
   - missing and fillable
   - missing but not safely derivable
   - already filled
   - visible but not editable
6. Call `EFFICIENCY_issue_update`
7. Reread the issue and report the other groups explicitly

## Expected Behavior On Your Example Bug

For a bug like `OMMUSIC-3397323`, the skill should likely:

- inspect the listed car-bug fields
- fill fields like `问题单解决时间`, `问题类型`, `测试环境`, `测试方法`, `问题发生阶段`, `解决方案`, and `问题原因` only when the values are supported
- leave `所属迭代` as skipped if there is no trustworthy id or mapping
- attempt status/close separately after the field backfill pass
