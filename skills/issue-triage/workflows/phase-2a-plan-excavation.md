# Phase 2a — Plan Excavation Tasks

Main agent. This is the bridge between "what the user wants" and "what sub-agents should go dig".

Goal: produce an `excavation_plan` with a hypothesis and 1–N concrete, sub-agent-executable excavation tasks. Do NOT dispatch sub-agents in this phase.

## 2a.1 Ensure Troubleshooting Knowledge Is In Context
<!-- retrieval_step -->

Project-specific troubleshooting knowledge dramatically improves task planning (symptom → TAG mapping, module call-chain, known failure modes). Resolve it in this order:

### Check 1 — Already preloaded by an upstream skill

If the conversation was handed off from a repo-aware bootstrap skill (for example `/cmiotsdk-start-bugflow` preloads its `knowledge/TROUBLESHOOTING.md` before handing off), the guide is expected to already be in context.

Indicators:
- an earlier message contains a TAG table, module ownership map, or a section heading matching `TROUBLESHOOTING`
- an upstream evidence chain explicitly referenced `knowledge/TROUBLESHOOTING.md`

If present, record it and skip to 2a.2:

```bash
scripts/case-state record-guide \
  --project-root "$PROJECT_ROOT" \
  --case-id "$CASE_ID" \
  --status preloaded_from_upstream \
  --source "<upstream skill name, e.g. cmiotsdk-start-bugflow>"
```

### Check 2 — Fallback to repo-local convention

If not preloaded, look for a guide at the conventional path:

```
$PROJECT_ROOT/.issue-flow/TROUBLESHOOTING.md
```

If it exists, read it into context now, then record:

```bash
scripts/case-state record-guide \
  --project-root "$PROJECT_ROOT" \
  --case-id "$CASE_ID" \
  --status loaded_from_repo \
  --source "$PROJECT_ROOT/.issue-flow/TROUBLESHOOTING.md"
```

### Check 3 — No guide available

Proceed with generic heuristics. Record the gap so it shows up in `investigation.md`:

```bash
scripts/case-state record-guide \
  --project-root "$PROJECT_ROOT" \
  --case-id "$CASE_ID" \
  --status none \
  --note "No project-specific guide; planning relies on generic log patterns."
```

Do NOT fabricate a guide. Do NOT assume TAGs or module boundaries not supported by either a loaded guide or explicit user input.

## 2a.2 Derive Hypothesis and Tasks
<!-- reasoning_step -->

Using `primary_question`, `primary_time_anchor`, `evidence_sources`, and the troubleshooting guide (if any), produce an `excavation_plan`.

Shape (see [schemas/excavation-plan.yaml](/Users/shenyeke01/Documents/Workspace/skills/skills/issue-triage/schemas/excavation-plan.yaml) for the full contract):

```yaml
excavation_plan:
  hypothesis: "<one-sentence working hypothesis the tasks are designed to confirm or falsify>"
  tasks:
    - id: T1
      kind: tag_search | time_anchor_slice | keyword_search | archive_inventory | media_inspect | code_correlate
      target_source: "<absolute path to a single evidence source OR a repo-relative code path>"
      query:
        tags: ["LocalPlayback"]            # for tag_search
        keywords: ["playInner", "error"]   # optional refinement
        time_window:                        # required for tag_search / time_anchor_slice
          anchor: "<primary_time_anchor>"
          radius_seconds: 30
      why: "<why this task matters for the hypothesis — ideally cite the troubleshooting guide>"
      expected_signals:
        - "<concrete signal shape, e.g. 'playInner() called but mState stuck on STATE_PREPARING'>"
```

Rules for task generation:

1. **One task = one evidence source + one excavation kind.** Do not bundle "search log A then search log B" into one task.
2. **Every task must have `why` and at least one `expected_signal`.** If you cannot state why, you are guessing — drop the task or ask the user.
3. **Rule out cheap alternatives first.** If the guide says "check auth before deep-diving playback chain", add a low-cost `tag_search` on auth TAGs as an early task.
4. **Include archive inventory when any evidence source is an archive** (`.tar.gz`, `.zip`, `.rar`, unknown compressed format). Archive inventory tasks should run before tasks that depend on contents.
5. **Do not plan `code_correlate` tasks in the initial batch.** Code correlation happens in Phase 3, only after evidence findings point at a concrete code area. The one exception: the user explicitly named a code path and it is small (<500 lines), in which case a single `code_correlate` task is permitted.
6. **Cap the initial batch at 5 tasks.** More than 5 means the hypothesis is too broad — narrow it first.

## 2a.3 Dispatch Policy

- Tasks dispatch in Phase 2b via the `task` tool, one sub-agent per task, running in parallel.
- Tasks with `kind: archive_inventory` dispatch first (a separate wave) because their output may add new `target_source` values for follow-up tasks.
- If the first wave of findings is insufficient, Phase 3 may bounce back to Phase 2a to plan a second wave — but no more than 2 planning rounds total.

## 2a.4 Exit Criteria

Phase 2a is done when:

- [ ] `troubleshooting_guide.status` is recorded in `case.yaml`
- [ ] `excavation_plan` exists with a non-empty `hypothesis` and 1–5 tasks
- [ ] Every task has `kind`, `target_source`, `why`, `expected_signals`

The `excavation_plan` lives in the main agent's working memory for this session. It is not persisted to disk unless the user asks for it. The reasoning behind it will be summarized into `investigation.md` in Phase 3.

## Exit

Proceed to [phase-2b-dispatch-excavators.md](./phase-2b-dispatch-excavators.md).
