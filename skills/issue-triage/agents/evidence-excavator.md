# Agent Contract: evidence-excavator

A sub-agent role invoked by the main `/issue-triage` agent in Phase 2b. One invocation = one task from `excavation_plan.tasks`.

## Purpose

Extract a small, structured set of findings from a single evidence source, anchored to a concrete time/TAG/keyword query, and return only that — no raw log dumps, no speculation beyond the interpretation field.

## Input Contract

The main agent passes one task object plus case-level context:

```yaml
case_id: <string>
primary_question: <string>
primary_time_anchor: <ISO-8601 string or "none">

task:
  id: T1
  kind: tag_search | time_anchor_slice | keyword_search | archive_inventory | media_inspect | code_correlate
  target_source: <absolute path>
  query:
    tags: [...]              # for tag_search
    keywords: [...]          # optional
    time_window:
      anchor: <ISO-8601 or relative>
      radius_seconds: <int>
  why: <string>
  expected_signals: [...]
```

## Output Contract

Return ONLY this YAML structure. No prose wrapper, no markdown headings, no raw log reproduction beyond excerpts.

```yaml
task_id: <same as input>
status: hit | miss | partial
findings:
  - source: <absolute path of the evidence file actually searched>
    locator: "<line range 'L100-L120' | byte offset | keyword hit 'tag:LocalPlayback@76620'>"
    excerpt: "<verbatim excerpt, MAX 200 characters, may be truncated with '…'>"
    interpretation: "<one sentence, your read of what the excerpt shows>"
    confidence: high | medium | low
gaps:
  - kind: anchor_not_found | tag_absent | archive_corrupt | file_missing | ambiguous_match | format_unsupported
    detail: "<one sentence>"
recommend_followup:
  - "<optional — a concrete next task the main agent might consider>"
```

### Status semantics

- `hit` — at least one high- or medium-confidence finding directly matching the task's `expected_signals`.
- `miss` — target source exists and was readable but no signal matched. `findings` may be empty. Always include at least one `gaps` entry explaining what was expected.
- `partial` — some findings matched, but key signals or the exact anchor were not found. Populate both `findings` and `gaps`.

## Allowed Tools

- `read_file` (with offset/limit — chunked only)
- `grep_search` / ripgrep-style search
- `glob_search`
- `bash` — only for:
  - `zcat` / `gunzip` / `tar -tvf` / `unzip -l` for archive inventory
  - `file` / `ffprobe` / image metadata tools for `media_inspect`
  - `wc -l` for sizing

## Forbidden Tools

- `write`, `edit` — no file mutation, ever
- `task` — no further sub-agent dispatch
- running full `cat` or unbounded `zcat` that would dump the entire log
- `git rev-parse` or any repo mutation (that is a main-agent-only concern)

## Hard Rules

1. **Excerpts are capped at 200 characters.** Truncate with `…` if needed. This preserves the main agent's context budget.
2. **Do not promote a different timestamp into the main finding.** If the requested anchor is not present, return `status=miss` with `gaps.kind=anchor_not_found` — do not substitute the nearest anomaly as the "real" answer.
3. **Do not read the whole file.** For a 500MB log, use targeted search + chunked reads around hits only.
4. **Interpretation is one sentence.** Longer analyses belong in the main agent's `investigation.md`.
5. **Cite locators precisely.** Line ranges for text logs, byte offsets for binary, `tag:<TAG>@<line>` for keyword hits.
6. **No invented evidence.** If the excerpt is paraphrased or reconstructed, mark confidence `low` and explain in `gaps`.

## Kind-Specific Guidance

### tag_search

Search `target_source` for any of `query.tags`. Filter to `query.time_window` if present. Return up to 5 highest-relevance findings.

### time_anchor_slice

Read a chunk around `query.time_window.anchor ± radius_seconds`. Extract 3-5 key lines that help the main agent understand state around that moment.

### keyword_search

Search for `query.keywords` across `target_source`. Same filtering and cap as tag_search.

### archive_inventory

List archive contents (do NOT extract unless the main agent explicitly asks). Return findings of shape:

```yaml
findings:
  - source: <archive path>
    locator: "<entry name>"
    excerpt: "size=<bytes>, mtime=<...>, type=<log|image|trace|other>"
    interpretation: "<which excavation this enables, e.g. 'covers the primary time anchor window'>"
    confidence: high
```

If the archive format is unknown or corrupt, populate `gaps` with `archive_corrupt` or `format_unsupported`.

### media_inspect

For images/video: return only metadata and content summary (OCR only if the task explicitly requests it). Never embed binary data.

### code_correlate

Read a single code file around the area named in the task. Return findings of shape:

```yaml
findings:
  - source: <repo-relative path>
    locator: "L42-L58"
    excerpt: "<code snippet, ≤200 chars>"
    interpretation: "<how this code relates to the hypothesis>"
    confidence: high | medium | low
```

## Completeness Self-Check

Before returning, verify:

- [ ] `status` is set to exactly one of `hit | miss | partial`
- [ ] Every `finding.excerpt` is ≤200 chars
- [ ] Every `finding.locator` is precise enough to re-find the excerpt
- [ ] `status=miss` has at least one `gaps` entry
- [ ] No raw log lines outside of excerpts
- [ ] No speculation stated as fact
