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

Do **not** treat the current issue detail as the complete writable-field list. Some Overmind custom fields may be absent from the detail response until they have a value.

## Step 5: Fetch Field Config

Treat these as the target fields for every resolved bug sync, in this priority order:

1. `解决方案`
2. `问题原因`
3. `备注说明` (optional)
4. `问题单解决时间`
5. `测试方法`
6. `测试环境`
7. `问题类型`

Call `EFFICIENCY_issue_get_issue_field_config` with both `name` and `issueType` for every target field you intend to write, not just enum fields.

If `EFFICIENCY_issue_get_issue_editable_fields` does not list a field, do **not** treat the absence as proof that the field is not writable. Use `EFFICIENCY_issue_get_issue_field_config` as the authoritative writability check. A field absent from `editable_fields` may still accept writes via `EFFICIENCY_issue_update`.

If a field is absent from both issue detail and field-config discovery, keep it in the plan as `unknown_writability` and report that explicitly. Do not silently drop it.

## Step 6: Prepare Draft

**Value priority:** User instruction > Artifact value > Safe inference > Skip

If the user explicitly tells you the root cause and solution, those statements outrank artifact summaries unless the case files clearly contradict them.

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

**Required behavior:**

- Always build candidate values for `解决方案` and `问题原因` when the case is resolved and the information is clear.
- Never collapse `问题原因` and `解决方案` into `备注说明` as a substitute.
- Never skip `问题原因` or `解决方案` only because they were missing from `EFFICIENCY_issue_get_issue_detail`.
- `问题原因` must include direct supporting evidence when the case relies on logs, such as timestamps, log snippets, or file/line references that let the reader locate the proof quickly. **If case artifacts contain timestamped log evidence, always include the strongest 2–3 items in the first draft — do not wait for the user to ask for more detail.**
- If direct evidence is insufficient, do not write a precise root cause as confirmed fact. Either downgrade it to a cautious statement or stop and ask the user to clarify the wording in the draft.
- `解决方案` and `问题原因` are the primary success criteria for this skill.
- `备注说明` is optional supplemental context. It must not be the only successful write when `问题原因` / `解决方案` were the main user request, and it must not affect overall success classification.
- `备注说明` should be omitted by default when it adds no extra value beyond the structured fields.

**Formatting guidance:**

- `问题原因`: root-cause conclusion first, then the strongest direct evidence in the same field; prefer 1-2 timestamped log facts or exact evidence refs
- `解决方案`: responsible layer + concrete action, without mixing in investigation-only evidence
- `备注说明`: short human-facing summary, not a replacement for the structured fields
- Use real timestamps and evidence refs from the case artifacts. Do not invent or mix evidence from a different root cause.

**Example mapping for this pattern:**

- `问题原因`: `系统原因。应用进入后台后受到 Android 后台资源限制，导致 AudioTrack 写入阻塞并最终触发 BUFFER TIMEOUT。证据：<时间戳1> 应用进入后台/onPause；<时间戳2> gap_time 持续增长；<时间戳3> BUFFER TIMEOUT；对应 <日志文件>:<行号1>,<行号2>,<行号3>。`
- `解决方案`: `App 层面自行处理。应用进入后台时启动前台服务（Foreground Service），保持音频播放不被系统限制。`
- `备注说明`: `已定位为系统限制场景，需应用侧通过前台服务保活处理，非 SDK 内部修复。`

**Never write:** `状态`, `所属迭代`

Before any Overmind write, show the user a compact confirmation draft:

```text
准备写入 Overmind 的字段草案：
- 解决方案：{draft_solution}
- 问题原因：{draft_root_cause}
- 备注说明：{draft_note or "不写"}

请确认是否按以上内容更新 Overmind。
```

- Do not call `EFFICIENCY_issue_update` before explicit user confirmation.
- If the user edits the wording, rebuild the draft and ask again.
- Keep the confirmation step short and focused on these fields only.
- If the user asks for stronger evidence in `问题原因`, revise that field first instead of proceeding to update.

## Step 7: Confirm With User

- Require explicit confirmation before any write.
- Accept concise confirmations such as `确认` / `可以更新` / `按这个写`.
- If the user does not confirm, stop after presenting the draft.

## Step 8: Execute & Verify

```
EFFICIENCY_issue_update → check failedFields → EFFICIENCY_issue_get_issue_detail
```

Execute the first write with confirmed `解决方案` and confirmed `问题原因`.

- Include `备注说明` only if the user confirmed that draft too.
- If writability is uncertain but the confirmed value is clear, prefer a real write attempt and let `failedFields` plus reread determine the outcome.
- If field fails, record it and continue with remaining fields.

After rereading, classify each target field as exactly one of:

- `filled`
- `already_set`
- `failed`
- `skipped_insufficient_evidence`
- `skipped_not_writable`
- `unknown_writability`

If only `备注说明` changed but `问题原因` and `解决方案` were not verified as `filled` or `already_set`, the run is `partial`, not `succeeded`.

## Step 9: 备注说明模板 (Optional)

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
- Explicit status for `问题原因`, `解决方案`, `备注说明`
- Reply handling result
- Manual follow-up needed

## Non-Negotiables

- Do not rewrite resolve artifacts to fit Overmind
- Do not create local artifacts (`sync.yaml`, `integrations/`)
- Do not write to Overmind before explicit user confirmation of the draft
- Do not retry `问题单解决时间` with alternate formats
- Verify every write by rereading — success message alone is not evidence
- Do not report "同步完成" or "解决完成" if only `备注说明` was updated
- Do not use `备注说明` as a fallback sink for missing `问题原因` / `解决方案`
- Do not write a high-confidence `问题原因` without direct supporting evidence
- When user-provided root cause / solution text is explicit, preserve that intent instead of replacing it with a weaker generic summary
- If MCP unavailable, stop immediately and report

## Exit States

- `awaiting_confirmation` — Draft prepared and shown to user; no write executed yet
- `succeeded` — `解决方案` and `问题原因` were verified as `filled` or `already_set`, and any remaining gaps were reported explicitly
- `partial` — Some fields synced, others need manual action
- `failed` — No confirmed change or MCP unavailable
