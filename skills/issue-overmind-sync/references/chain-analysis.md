# Chain Analysis From `提交 BUG.md`

This note extracts the reusable workflow pattern from the manual Overmind submission conversation.

## Observed interaction chain

1. The user asked to update the Overmind bug status for `OMMUSIC-3397323`.
2. The agent fetched current issue details first and learned the issue type was `IOT_BUG`.
3. The agent tried a direct close action early and reported success.
4. The user reported that the close did not actually stick.
5. A later retry exposed `failedFields: ["状态"]`, showing the first success signal was not enough.
6. The agent then queried editable fields and learned that the visible status field was not writable through the same path.
7. The agent fell back to updating description and solution-style fields that were writable.
8. The user asked for a broader set of business fields such as `问题类型`, `问题单解决时间`, `测试环境`, and `问题原因`.
9. The agent fetched field metadata and option lists one field at a time, then mapped human labels to option ids.
10. The agent updated the fields that had known mappings and left `所属迭代` unresolved because no safe value was available.

## Design implications

- Separate field updates from close actions. They fail differently and need different fallback paths.
- Always verify writes after the API reports success. A success banner alone is not evidence.
- Discover editability before mutating. A field may be visible in issue details but still not writable.
- Enum fields require label-to-id lookup, not raw label writes.
- Partial success is normal and should be modeled explicitly.
- User-specified values outrank inferred defaults.
- Missing values such as `所属迭代` should become follow-up items, not guessed writes.

## Recommended plugin shape

- Keep this skill outside `issue-flow-core` so Overmind stays optional.
- Read from the shared case workspace, but write plugin-owned records under `integrations/overmind/`.
- Allow the skill to run after `issue-resolve`, after a manual fix, or as a retry pass after a failed external sync.

## Candidate field derivations

| Overmind field | Preferred source |
|---|---|
| `解决方案` | `resolve/resolution.xml` summary plus concrete change notes |
| `问题原因` | handoff or resolution root cause summary |
| `问题单解决时间` | explicit resolution timestamp, otherwise sync time |
| `测试方法` | `resolve/verification.md` |
| `测试环境` | `resolve/verification.md` when clearly stated |
| `问题类型` | explicit user choice, otherwise cautious inference |
| `状态/关闭` | dedicated action or verified writable field path only |

## What not to do

- Do not change case lifecycle just because Overmind closed or failed to close.
- Do not rewrite resolve artifacts to make the external payload look cleaner.
- Do not keep retrying the same close mutation when the system already proved the field path is invalid.
