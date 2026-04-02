# Chain Analysis From `提交 BUG.md`

This note extracts the reusable workflow pattern from the manual Overmind submission conversation.

## Observed interaction chain

1. The user asked to update the Overmind bug status for `OMMUSIC-3397323`.
2. The agent fetched current issue details first and learned the issue type was `IOT_BUG`.
3. The agent tried a direct close action early and reported success.
4. The user reported that the close did not actually stick.
5. A later retry exposed `failedFields: ["状态"]`, showing the first success signal was not enough.
6. The agent continued with ordinary field updates instead of treating status as the only signal.
7. The user asked for a broader set of business fields such as `问题类型`, `问题单解决时间`, `测试环境`, and `问题原因`.
8. The agent fetched field metadata and option lists one field at a time, then mapped human labels to option ids.
9. The agent updated the fields that had known mappings and treated `所属迭代` as read-only context.

## Tested MCP Chain

This skill must be grounded in the real Overmind MCP tool chain:

1. `EFFICIENCY_issue_get_issue_detail`
2. `EFFICIENCY_issue_get_issue_field_config`
3. `EFFICIENCY_issue_update`

Tested behaviors:

- `EFFICIENCY_issue_get_issue_detail` works with `issueKey`.
- `EFFICIENCY_issue_update` works for direct field writes and returns `failedFields`.
- A same-value update such as `{\"测试方法\":\"开发自测\"}` is a safe smoke test for the write path.
- `EFFICIENCY_issue_get_issue_field_config` for custom bug fields like `问题类型` works when `issueType` is provided.
- Calling `EFFICIENCY_issue_get_issue_field_config` with only `name` can fail for those same fields.
- A bad local-path fallback can break the skill before any MCP call happens. In testing, falling back to `/Users/<user>/.issue-flow/...` was wrong when the actual case lived under the current repository.
- If the case workspace is missing, the skill must stop instead of continuing with Overmind-only updates.

## Design implications

- Separate field updates from close actions. They fail differently and need different fallback paths.
- Always verify writes after the API reports success. A success banner alone is not evidence.
- Enum fields require label-to-id lookup, not raw label writes.
- Partial success is normal and should be modeled explicitly.
- User-specified values outrank inferred defaults.
- Missing values such as `所属迭代` should remain read-only context, not guessed writes.

## Recommended plugin shape

- Keep this skill outside `issue-flow-core` so Overmind stays optional.
- Read from the shared case workspace, then directly call Overmind MCP.
- Allow the skill to run after `issue-resolve`, after a manual fix, or as a retry pass after a failed external sync.
- Do not generate local `sync.yaml` files or `integrations/` directories unless the user explicitly asks for an audit artifact.

## Candidate field derivations

| Overmind field | Preferred source |
|---|---|
| `解决方案` | `resolve/resolution.xml` summary plus concrete change notes |
| `问题原因` | handoff or resolution root cause summary |
| `问题单解决时间` | explicit resolution timestamp, otherwise sync time |
| `测试方法` | `resolve/verification.md` |
| `测试环境` | `resolve/verification.md` when clearly stated |
| `问题类型` | explicit user choice, otherwise cautious inference |
| `备注说明` | external reply text when writable |
| `所属迭代` | read-only context only |

## What not to do

- Do not change case lifecycle just because Overmind closed or failed to close.
- Do not rewrite resolve artifacts to make the external payload look cleaner.
- Do not keep retrying the same close mutation when the system already proved the field path is invalid.
- Do not claim "同步完成" if you never actually called Overmind MCP.
- Do not fall back to creating local config files when direct MCP execution is unavailable.
- Do not search for case files under `$HOME/.issue-flow` unless the user explicitly gave that path.
- Do not keep going when the case workspace is missing.
