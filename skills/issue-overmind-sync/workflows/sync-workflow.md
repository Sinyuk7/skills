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

### 1. Confirm the sync target

- Resolve the case path and issue key before making changes.
- Read `status.yaml` first. Prefer syncing after `resolved_verified`, `resolved_unverified`, or `closed`.
- If the case is earlier than resolve, only continue when the user explicitly wants a partial external update.
- Confirm that Overmind MCP is actually available in the current environment before doing any planning. If it is not available, stop immediately and report that limitation.

### 2. Read the case, not just the user prompt

- Read `resolve/resolution.xml` for outcome type, summary, changed files, and delivery notes.
- Read `resolve/verification.md` for verification method, environment, and confidence.
- Read `analysis/handoff.xml` only when resolve artifacts are missing key context.
- Use explicit user instructions as highest-priority overrides. Everything else should be inferred from artifacts only when the inference is defensible.

### 3. Discover Overmind capabilities before composing the payload

- Fetch current issue details first so you know the issue type and existing values.
- Discover the editable field list for that issue type before trying to write.
- For every enum-like field you plan to update, fetch the option metadata and map labels to option ids.
- Treat close/complete actions as separate from ordinary field updates. A visible status does not mean the field is writable.
- Prefer the domain-specific Overmind MCP issue methods. Do not rely on generic MCP resource browsing if the server does not expose it.
- Build a "core field gap list" by intersecting:
  - fields visible on the current issue
  - fields editable through the API
  - fields in the core business bucket from `references/field-policy.md`
  - fields whose current value is empty or still a placeholder such as `请选择`

### 4. Build a required-first update plan

Suggested mapping order:

- Explicit user-provided values
- Directly stated values in `resolution.xml` and `verification.md`
- Safe inferences from the case
- Leave blank when the value is ambiguous

Use this priority order for writes:

- First pass: core missing fields only
- Second pass: secondary helpful fields such as description notes
- Third pass: close or complete action when the user explicitly asks for it

Common field sources:

- `解决方案`: resolution summary and concrete code/config change
- `问题原因`: root cause summary from handoff or resolution
- `问题单解决时间`: sync time or explicit resolution timestamp
- `测试方法`: inferred from verification evidence such as self-test, QA, or unavailable
- `测试环境`: inferred only when the environment is clearly stated
- `问题类型`: only when the issue can be mapped confidently to a known option

Do not invent fields like `所属迭代` when the case does not carry a trustworthy value. Mark them as skipped and explain why.

### 5. Execute in phases

Phase A: update core missing fields that are clearly writable and safely derivable.

Phase B: update secondary or rich-text summary fields such as description or solution notes when supported and useful.

Phase C: attempt close or complete only after the case details are already synced, the API path is known to work, and the user asked for a status change.

After each phase, inspect returned failures and reread the issue when needed.

### 6. Handle failures as first-class outcomes

- If a field fails, record which field failed and why.
- If status update fails but other fields can be written, continue with partial sync instead of aborting everything.
- If a tool claims success but a follow-up read disagrees, treat the write as unverified and report it honestly.
- Retrying is allowed, but do not repeat the same failing mutation without new evidence about editability or required values.

### 7. Report The Actual Execution

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
- The sync directly uses Overmind MCP instead of generating local placeholder files.
