# Phase 3 — Synthesize & Dispose

Main agent. Consolidate all `excavation_results`, optionally correlate a small amount of code, decide a `disposition`, write `investigation.md`, and record the terminal state.

## 3.1 Consolidate Findings
<!-- reasoning_step -->

For each task result in `excavation_results`:

- Drop entries with `status=miss` that carry no useful `gaps`.
- Merge findings that cite overlapping locators (same file + adjacent line ranges) into a single finding block.
- Rank findings by `confidence: high > medium > low`, then by relevance to `primary_question`.

Produce a `consolidated_findings` list in memory:

```yaml
consolidated_findings:
  - source: <path>
    locator: <...>
    excerpt: <...>
    interpretation: <...>
    confidence: high
    supports: "<one-sentence claim this finding supports>"
```

If the consolidated list is empty or all low-confidence, treat this as a signal that Phase 2a's hypothesis was weak. You have two choices:
- bounce back to Phase 2a with a narrower hypothesis (one extra round only), or
- proceed to 3.4 with `direction_only` or `blocked`.

## 3.2 Optional Code Correlation
<!-- reasoning_step -->

Code correlation is allowed only after evidence findings point at a concrete area. Rules:

- Correlate at most 3 code locations.
- Read with focused offset/limit; do NOT read whole modules.
- Code findings must cite `file:line_range`.
- Do not modify code, even a comment. Writing is forbidden in this skill.

If you cannot confidently correlate, skip this step. Lack of code correlation is not a blocker for producing a disposition.

## 3.3 Anchor Check
<!-- validation_step -->

Before deciding disposition, verify the conclusion is anchored to `primary_time_anchor` / `primary_question`:

- If findings point at a different timestamp than the user's anchor, DO NOT promote them into the main conclusion.
  - If they plausibly relate, record them as secondary cross-references.
  - If they contradict the requested anchor, choose `disposition.type=blocked` with `kind=anchor_mismatch`.
- If findings point at a different question than the user's, choose `disposition.type=direction_only` and list the observed signal as a ranked hypothesis — do not silently replace the question.

## 3.4 Decide Disposition
<!-- reasoning_step -->

Pick exactly one `disposition.type`:

| Condition | Disposition |
|-----------|-------------|
| High-confidence findings clearly identify a root cause anchored to the user's target | `root_caused` |
| Findings suggest plausible hypotheses but cannot confirm a single cause | `direction_only` |
| Evidence is missing, anchor is ambiguous, or anchor mismatches | `blocked` |
| Findings show the behavior is intended / expected | `wont_fix` |
| Findings identify this case as a duplicate of another | `duplicate` |
| Findings show the issue is already fixed in another commit / PR | `already_fixed` |
| Findings show evidence is insufficient AND the user has no more to provide | `cannot_reproduce` |

## 3.5 Write investigation.md
<!-- mutation_step -->

Use [templates/investigation.md](/Users/shenyeke01/Documents/Workspace/skills/skills/issue-triage/templates/investigation.md) as the skeleton.

Required sections, in order:

1. **Working Statement** — one line derived from `primary_question` + `primary_time_anchor`.
2. **Investigation Target** — primary question, time anchor, stakeholders.
3. **Troubleshooting Guide** — one line on which guide was used (or recorded `status: none`).
4. **Excavation Plan Summary** — the hypothesis and 1-line descriptions of each task. Short; the value is traceability, not repetition.
5. **Findings** — cite every `consolidated_findings` entry with `source + locator + interpretation + confidence`. Speculation must be labelled as hypothesis, not stated as fact.
6. **Code Correlation** — only when Phase 3.2 produced entries. Include `file:line_range`.
7. **Disposition** — the chosen `disposition.type`, one-paragraph rationale, and what the user should do next.

Rules:

- Every conclusion must include at least one evidence reference (file path + line range or timestamp).
- Do NOT copy raw log lines longer than the 200-char excerpts sub-agents returned.
- Do NOT duplicate `case.yaml` fields as narrative; link to the file instead.

## 3.6 Record Terminal State
<!-- mutation_step -->

Based on disposition, call exactly ONE of:

### root_caused / wont_fix / duplicate / already_fixed / cannot_reproduce

```bash
scripts/case-state close \
  --project-root "$PROJECT_ROOT" \
  --case-id "$CASE_ID" \
  --type <type> \
  --summary "<one-line summary>" \
  [--root-cause-location "foo/Bar.kt:142"]    # root_caused only
  [--evidence-refs '[...]']                    # root_caused only
  [--duplicate-of "<other-case-id>"]           # duplicate only
  [--reference "<commit SHA or PR link>"]      # already_fixed only
  --next-step "<short operator-facing note>"
```

### direction_only

```bash
scripts/case-state set-direction \
  --project-root "$PROJECT_ROOT" \
  --case-id "$CASE_ID" \
  --summary "<one-line summary>" \
  --directions '[
    {"rank":1,"hypothesis":"...","next_experiment":"..."},
    {"rank":2,"hypothesis":"...","next_experiment":"..."}
  ]' \
  --next-step "Open a new session to pursue rank-1 direction"
```

### blocked

```bash
scripts/case-state record-blocked \
  --project-root "$PROJECT_ROOT" \
  --case-id "$CASE_ID" \
  --kind missing_evidence|ambiguous_anchor|anchor_mismatch|insufficient_context \
  --detail "<what is missing and why it matters>" \
  --next-step "<what the user should provide>"
```

## 3.7 Final Handoff Message

Emit exactly one of the messages defined in `SKILL.md > Handoff Messages`, matching the chosen disposition. Do not emit multiple.

## 3.8 Exit Criteria

Triage is complete when:

- [ ] `case.yaml` has `status: investigated` or `blocked`
- [ ] `case.yaml` has a `disposition.type` field
- [ ] `investigation.md` exists and all required sections are filled
- [ ] Exactly one handoff message has been emitted to the user
