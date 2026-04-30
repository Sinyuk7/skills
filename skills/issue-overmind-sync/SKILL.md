---
name: issue-overmind-sync
description: Sync triage artifacts to Overmind bug fields via MCP. Use after /issue-triage terminates with a concrete disposition (root_caused, wont_fix, duplicate, already_fixed, or cannot_reproduce), when retrying a failed Overmind update, or when filling remaining bug fields from case artifacts. This is a post-triage plugin only — do not use for investigation, fixing, or building handoffs.
---

# Issue Overmind Sync

Post-triage plugin that syncs case artifacts to Overmind bug tracking system via MCP.

## Capability Contract

```yaml
type: plugin
owns: Map triaged case artifacts to Overmind bug fields; draft and confirm field values with user; execute Overmind MCP writes; verify write success by rereading
does_not_own: Evidence collection, root cause investigation, code modification, case lifecycle management
delegate_to: none (terminal skill in the issue-flow pipeline)
refuses_when: Overmind MCP is unavailable; no explicit issueKey from user; neither a triaged case nor explicit user-provided primary field text is available
requires_evidence: Either (a) case.yaml with status=investigated (disposition.type in {root_caused, wont_fix, duplicate, already_fixed, cannot_reproduce}) + investigation.md, or (b) explicit user-provided `问题原因` and `解决方案` text for update-only mode
primary_outputs:
  - Overmind fields updated (解决方案, 问题原因, and optionally AI分析 / 备注说明)
  - Per-field status report (filled, already_set, failed, skipped)
allowed_tools: [bash (git rev-parse only), read, EFFICIENCY_issue_* MCP tools]
forbidden_tools: [edit, write (no local artifact creation)]
eval_set: evals/evals.json
```

## When To Use

- Case has `status: investigated` with a non-blocked `disposition.type` and needs Overmind fields filled
- Retry a failed Overmind update
- Write a supplemental AI-facing or human-facing note to `AI分析` and/or `备注说明`
- Resubmit or correct final field wording when the user already provides explicit `问题原因` and `解决方案`

Do NOT use when:
- `status: investigating` or `status: blocked` — triage is not done yet
- `disposition.type: direction_only` — no confirmed root cause to sync yet; user should open a new session to deepen investigation first

## Step 1: Choose Evidence Mode
<!-- validation_step -->

Choose exactly one evidence mode before doing anything else:

- `case_backed`: use project-local triaged case artifacts as the source of truth
- `direct_text`: use explicit user-provided primary field text as the source of truth for an update-only run

Enter `case_backed` mode when the user provides a case path / case id, or asks to sync the triaged case output.

Enter `direct_text` mode only when all of the following are true:

- the user provides explicit `issueKey`
- the user provides explicit `问题原因` text
- the user provides explicit `解决方案` text
- the task is retrying, correcting, or resubmitting final wording rather than asking this skill to investigate from scratch

If neither mode can be entered safely, stop and ask the user for either:

- the triaged case location
- or the exact `问题原因` and `解决方案` wording to use

If the selected mode is `direct_text`, skip case workspace resolution and move to MCP validation.

If the selected mode is `case_backed`, resolve `PROJECT_ROOT` before doing anything else.

- Prefer an explicit repository path from the user
- Otherwise derive the repo root from a user-provided code path or evidence path:
  ```bash
  git -C "<file-directory-or-repo-path>" rev-parse --show-toplevel
  ```
- Use plain `git rev-parse --show-toplevel` only when the current working directory is already known to be the target repository
- If the target repository is ambiguous, stop and ask the user instead of guessing

Never default to the skill repository or any unrelated repo just because the command succeeds there.
Do not inline `git rev-parse --show-toplevel` again in later commands; reuse the already-resolved absolute `PROJECT_ROOT`.

Then find the case:

```
PROJECT_ROOT/.issue-flow/cases/<case-id>/
```

**Never** fall back to `$HOME/.issue-flow/` — only use project-local cases.
**Never** silently switch to another repository if the expected case directory is missing from `PROJECT_ROOT`.

## Step 2: Validate MCP Availability
<!-- validation_step -->

Confirm Overmind MCP is available:

```
EFFICIENCY_issue_get_issue_detail(issueKey: "<user-provided-key>")
```

- **REQUIRE** explicit `issueKey` from user before any write
- If MCP unavailable, **STOP** and report to user

## Step 3: Read Evidence Inputs
<!-- retrieval_step -->

If mode is `case_backed`, from the case workspace read:

| File | Purpose |
|------|---------|
| `case.yaml` | Verify `status: investigated` and read `disposition` |
| `investigation.md` | Root cause summary, cited findings, and (when `disposition.type=already_fixed`) the fix reference |

From `case.yaml.disposition`, extract:

- `type` — must be one of `root_caused`, `wont_fix`, `duplicate`, `already_fixed`, `cannot_reproduce`. If it is `blocked` or `direction_only`, stop — there is nothing final to sync yet.
- `summary`
- type-specific fields:
  - `root_caused` → `root_cause_location`, `evidence_refs`
  - `already_fixed` → `reference` (commit SHA or PR link)
  - `duplicate` → `duplicate_of`

**Legacy fallback** (only for pre-triage-era cases that still have these files):
- `resolution.md`
- `resolve/resolution.md`
- `resolve/resolution.xml`
- `resolve/verification.md`
- `analysis/handoff.xml`

These legacy files are optional. In the current triage model, no `resolution.md` is produced — the information comes from `case.yaml.disposition` + `investigation.md`.

If mode is `direct_text`:

- Treat the user-provided `问题原因` and `解决方案` wording as the source of truth for those primary fields
- Treat user-provided `AI分析` / `备注说明` as optional supplemental inputs
- Do not invent additional evidence, logs, or code references that the user did not provide
- Do not strengthen the user's wording into a higher-confidence root-cause claim than they explicitly gave you

## Step 4: Fetch Current Issue
<!-- retrieval_step -->

Call `EFFICIENCY_issue_get_issue_detail` to get:
- Current field values and placeholders (`请选择`)
- Issue type from `类型` field
- Issue URL

Do **not** treat the current issue detail as the complete writable-field list. Some Overmind custom fields may be absent from the detail response until they have a value.

## Step 5: Retrieve Field Config
<!-- retrieval_step -->

Treat these as the target fields for every resolved bug sync, in this priority order:

1. `解决方案`
2. `问题原因`
3. `AI分析` (optional, preferred supplemental field)
4. `备注说明` (optional fallback)
5. `问题单解决时间`
6. `测试方法`
7. `测试环境`
8. `问题类型`

Read the skill-local field contract first:

- `schemas/iot-bug-target-fields.yaml`
- `knowledge/field-discovery-policy.md`

If the current issue `类型` is `IOT_BUG`, use the cached contract directly for:

- `解决方案`
- `问题原因`
- `AI分析`
- `备注说明`
- `问题单解决时间`
- `测试方法`
- `测试环境`

Only call `EFFICIENCY_issue_get_issue_field_config` with both `name` and `issueType` when:

- issue type is not `IOT_BUG`
- the target field is missing from the cached contract
- the target field is `问题类型`
- a write failed and you need live revalidation before retrying

If `EFFICIENCY_issue_get_issue_editable_fields` does not list a field, do **not** treat the absence as proof that the field is not writable. Use `EFFICIENCY_issue_get_issue_field_config` as the authoritative writability check. A field absent from `editable_fields` may still accept writes via `EFFICIENCY_issue_update`.

If a field is absent from both issue detail and field-config discovery, keep it in the plan as `unknown_writability` and report that explicitly. Do not silently drop it.

## Step 6: Map and Draft Field Values
<!-- transform_step + reasoning_step -->

**Value priority:** User instruction > Artifact value > Safe inference > Skip

If the user explicitly tells you the root cause and solution, those statements outrank artifact summaries unless the case files clearly contradict them.

**Field mapping:**

| Field | Source |
|-------|--------|
| `解决方案` | For `root_caused`: responsible layer + concrete action derived from investigation.md's disposition + root_cause_location. For `already_fixed`: describe the reference fix (commit/PR). For `wont_fix`/`duplicate`/`cannot_reproduce`: state the disposition and rationale. |
| `问题原因` | investigation.md root cause + cited evidence; `case.yaml.disposition.summary` and `disposition.evidence_refs` when applicable |
| `AI分析` | Human-facing AI summary of cause + action, only as supplemental context |
| `问题单解决时间` | `case.yaml.closed` timestamp (or sync timestamp) in Overmind display format when clearly known |
| `测试方法` | Verification context from investigation.md if present → `开发自测` / `QA测试`; leave unset when triage alone cannot support a testing statement |
| `测试环境` | Verification context from investigation.md when clearly stated |
| `问题类型` | Only with confident mapping |
| `备注说明` | Supplemental note only when `AI分析` is unavailable or extra context is still needed |

**Required behavior:**

- Always build candidate values for `解决方案` and `问题原因` when the case has a concrete disposition and the information is clear.
- Never collapse `问题原因` and `解决方案` into `备注说明` as a substitute.
- Never skip `问题原因` or `解决方案` only because they were missing from `EFFICIENCY_issue_get_issue_detail`.
- `问题原因` must include direct supporting evidence when the case relies on logs, such as timestamps, log snippets, or file/line references that let the reader locate the proof quickly. **If case artifacts contain timestamped log evidence, always include the strongest 2–3 items in the first draft — do not wait for the user to ask for more detail.**
- If direct evidence is insufficient, do not write a precise root cause as confirmed fact. Either downgrade it to a cautious statement or stop and ask the user to clarify the wording in the draft.
- In `direct_text` mode, do not infer missing primary fields from memory. Use the user-provided wording, lightly normalize it if needed, and ask for clarification instead of filling gaps yourself.
- `解决方案` and `问题原因` are the primary success criteria for this skill.
- `AI分析` and `备注说明` are optional supplemental fields. Prefer `AI分析` when choosing only one of them.
- It is valid to write `AI分析`, to write `备注说明`, to write both, or to write neither.
- `备注说明` is optional supplemental context. It must not be the only successful write when `问题原因` / `解决方案` were the main user request, and it must not affect overall success classification.
- `备注说明` should be omitted by default when it adds no extra value beyond the structured fields.
- `AI分析` should be omitted by default when it adds no value beyond the structured fields, but when a supplemental field is useful it is the preferred landing field.
- For `IOT_BUG`, do not spend extra round-trips probing the stable target-field contract on every run. Use the cached contract first and fall back to live discovery only when needed.
- `问题类型` is the expensive field. It has a large option set and duplicate labels, so only probe and write it when you already have a confident mapping.

**Formatting guidance:**

- `问题原因`: root-cause conclusion first, then the strongest direct evidence in the same field; prefer 1-2 timestamped log facts or exact evidence refs
- `解决方案`: responsible layer + concrete action, without mixing in investigation-only evidence
- `AI分析`: short human-facing summary that explains what happened and what should be done, without replacing the structured root-cause/solution fields
- `备注说明`: short human-facing summary, not a replacement for the structured fields
- Use real timestamps and evidence refs from the case artifacts. Do not invent or mix evidence from a different root cause.

**Example mapping for this pattern:**

- `问题原因`: `系统原因。应用进入后台后受到 Android 后台资源限制，导致 AudioTrack 写入阻塞并最终触发 BUFFER TIMEOUT。证据：<时间戳1> 应用进入后台/onPause；<时间戳2> gap_time 持续增长；<时间戳3> BUFFER TIMEOUT；对应 <日志文件>:<行号1>,<行号2>,<行号3>。`
- `解决方案`: `App 层面自行处理。应用进入后台时启动前台服务（Foreground Service），保持音频播放不被系统限制。`
- `AI分析`: `已定位为系统限制场景。应用退到后台后被 Android 后台策略限制，最终触发播放超时；建议由 App 在后台播放场景启动前台服务保活，非 SDK 内部修复项。`
- `备注说明`: `已定位为系统限制场景，需应用侧通过前台服务保活处理，非 SDK 内部修复。`

**Never write:** `状态`, `所属迭代`

Before any Overmind write, show the user the compact confirmation draft from:

- `templates/confirmation-draft.txt`

- Do not call `EFFICIENCY_issue_update` before explicit user confirmation.
- If the user edits the wording, rebuild the draft and ask again.
- Keep the confirmation step short and focused on these fields only.
- If the user asks for stronger evidence in `问题原因`, revise that field first instead of proceeding to update.

## Step 7: Confirm With User
<!-- validation_step -->

- Require explicit confirmation before any write.
- Accept concise confirmations such as `确认` / `可以更新` / `按这个写`.
- If the user does not confirm, stop after presenting the draft.

## Step 8: Execute & Verify
<!-- mutation_step + validation_step -->

```
EFFICIENCY_issue_update → check failedFields → EFFICIENCY_issue_get_issue_detail
```

Execute the first write with confirmed `解决方案` and confirmed `问题原因`.

- Include `AI分析` only if the user confirmed that draft too.
- Include `备注说明` only if the user confirmed that draft too.
- If writability is uncertain but the confirmed value is clear, prefer a real write attempt and let `failedFields` plus reread determine the outcome.
- If field fails, record it and continue with remaining fields.
- If the run used cached field contract data and a cached field fails unexpectedly, perform one live `EFFICIENCY_issue_get_issue_field_config` revalidation for that field before deciding whether manual follow-up is required.

After rereading, classify each target field as exactly one of:

- `filled`
- `already_set`
- `failed`
- `skipped_insufficient_evidence`
- `skipped_not_writable`
- `unknown_writability`

If only `AI分析` and/or `备注说明` changed but `问题原因` and `解决方案` were not verified as `filled` or `already_set`, the run is `partial`, not `succeeded`.

## Step 9: AI分析 / 备注说明模板 (Optional)

Prefer writing to `AI分析` when a supplemental field is useful and writable.
Use `备注说明` as a fallback or as extra context only when it adds value.

`AI分析`:

```text
{surface_cause_and_action — one short paragraph, human-facing, no code paths}
```

`备注说明`:

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
- Explicit status for `问题原因`, `解决方案`, `AI分析`, `备注说明`
- Reply handling result
- Manual follow-up needed

## Non-Negotiables

- Do not rewrite resolve artifacts to fit Overmind
- Do not create local artifacts (`sync.yaml`, `integrations/`)
- Do not write to Overmind before explicit user confirmation of the draft
- Do not retry `问题单解决时间` with alternate formats
- Verify every write by rereading — success message alone is not evidence
- Do not report "同步完成" or "解决完成" if only `AI分析` / `备注说明` was updated
- Do not use `AI分析` or `备注说明` as a fallback sink for missing `问题原因` / `解决方案`
- Do not write a high-confidence `问题原因` without direct supporting evidence
- When user-provided root cause / solution text is explicit, preserve that intent instead of replacing it with a weaker generic summary
- If MCP unavailable, stop immediately and report
- Do not re-probe every stable `IOT_BUG` target field on every run; use the cached contract first
- If cached contract write fails unexpectedly, revalidate that field live before declaring the cache stale or the field not writable

## Exit States

- `awaiting_confirmation` — Draft prepared and shown to user; no write executed yet
- `succeeded` — `解决方案` and `问题原因` were verified as `filled` or `already_set`, and any remaining gaps were reported explicitly
- `partial` — Some fields synced, others need manual action
- `failed` — No confirmed change or MCP unavailable
