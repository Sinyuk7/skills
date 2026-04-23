# Field Discovery Policy

Use cached field contracts first. Probe live only when the write target is not covered by the cached contract or the live run proves the cache stale.

## IOT_BUG Fast Path

When issue `类型` is `IOT_BUG`, read `schemas/iot-bug-target-fields.yaml` first.

Use the cached contract directly for:

- `解决方案`
- `问题原因`
- `AI分析`
- `备注说明`
- `问题单解决时间`
- `测试方法`
- `测试环境`

Only call `EFFICIENCY_issue_get_issue_field_config` when at least one of the following is true:

- issue type is not `IOT_BUG`
- target field is not present in the cached contract
- target field is `问题类型`
- a write failed and you need live revalidation before retrying

When a cached `IOT_BUG` field write fails unexpectedly:

- revalidate that field live with `EFFICIENCY_issue_get_issue_field_config`
- do not immediately mark all cached fields stale
- classify whether the failure came from stale cache, field writability, or another write-time problem

## Live-Proven Constraints

- `EFFICIENCY_issue_get_issue_detail` omits empty fields. Missing field in detail is not proof that the field is absent or not writable.
- `EFFICIENCY_issue_get_issue_editable_fields(issueType="IOT_BUG")` currently returns only a small system-field subset and omits the custom bug fields used by this skill.
- `EFFICIENCY_issue_get_issue_field_config` is therefore the authoritative fallback for writability and option discovery.

## Write Encoding

- `TEXT` and `MULTILINE_TEXT` fields should be written as plain strings.
- `SINGLE` fields may be written using the option label when the label is unique.
- If an option label is duplicated, use the option `value` from live config or stop and ask the user to disambiguate.
- `问题单解决时间` is a `DATETIME` field for `IOT_BUG`; prefer one concrete timestamp string in Overmind display format and do not retry alternate formats.
