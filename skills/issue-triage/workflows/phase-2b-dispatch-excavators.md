# Phase 2b — Dispatch Evidence Excavators

Main agent dispatches; sub-agents execute. The main agent does NOT read full raw logs here.

Goal: turn each task from `excavation_plan` into a sub-agent invocation, collect the structured `findings[]` and `gaps[]`, and hand them to Phase 3.

## 2b.1 Mandatory Sub-Agent Dispatch
<!-- retrieval_step -->

**MUST dispatch every excavation task via the `task` tool.** The main agent is forbidden from reading full raw log files or running grep/zcat over raw evidence directly in this phase. Its only allowed tools here are:

- `task` — to invoke excavators
- `./scripts/case-state` — to update case state as evidence is consolidated

Rationale: raw logs pollute the main agent's context window, which degrades the Phase 3 synthesis. Sub-agents return only structured findings + short excerpts.

## 2b.2 Invocation Pattern

For each task in `excavation_plan.tasks`:

1. Pick agent type `explore` (for search / chunked read / archive inventory / media inspect) — it is the thorough reader that does not need write access.
2. Pass the full task object plus the invariants the excavator needs.
3. Request the exact output shape defined in [agents/evidence-excavator.md](../agents/evidence-excavator.md).

Template prompt for a single sub-agent:

```text
You are an evidence excavator for case <CASE_ID>.

Case context:
- primary_question: "<...>"
- primary_time_anchor: "<...>"

Your task (do only this one task):
<paste the single task YAML from excavation_plan.tasks[i]>

Output contract (return ONLY this structure, nothing else):

task_id: <id>
status: hit | miss | partial
findings:
  - source: <path>
    locator: "<line range, byte offset, or keyword-hit identifier>"
    excerpt: "<<= 200 characters verbatim>"
    interpretation: "<one sentence>"
    confidence: high | medium | low
gaps:
  - kind: anchor_not_found | tag_absent | archive_corrupt | file_missing | ambiguous_match
    detail: "<one sentence>"
recommend_followup:
  - "<optional — a concrete next task the main agent might dispatch>"

Hard rules:
- Do NOT return raw log lines longer than 200 chars per excerpt.
- Do NOT write files.
- Do NOT invoke further sub-agents.
- If the anchor is not present in the target source, return status=miss with a `gaps` entry; do not substitute a different timestamp.
```

## 2b.3 Concurrency and Waves

- Dispatch at most 5 sub-agents concurrently.
- Wave ordering:
  1. **Wave 0 (only if present):** tasks with `kind: archive_inventory`. Wait for them to return, then extend `excavation_plan.tasks` with any new target_sources they uncovered.
  2. **Wave 1:** all remaining initial tasks, in parallel.
  3. **Wave 2 (optional):** if Phase 3 determines findings are insufficient, return here with a narrowed plan. Max 2 planning/dispatch rounds total.

## 2b.4 Collecting Results

Collect every sub-agent return value into a main-agent-side list:

```yaml
excavation_results:
  - <output of task T1>
  - <output of task T2>
  - ...
```

Do NOT persist `excavation_results` to disk. They live only for this session; their distilled content goes into `investigation.md` in Phase 3.

## 2b.5 Follow-up Tasks from Sub-Agents

If a sub-agent returned `recommend_followup`, **the main agent (not the sub-agent)** decides whether to act on it. If acted on, follow-up tasks go through Phase 2a.2 to be re-validated (hypothesis alignment, why, expected_signals) before re-dispatch. Sub-agents never invoke other sub-agents themselves.

## 2b.6 Exit Criteria

Phase 2b is done when:

- [ ] Every task in `excavation_plan.tasks` has a corresponding entry in `excavation_results`
- [ ] No sub-agent left an ambiguous status (`hit` / `miss` / `partial` are all fine; malformed outputs are not)
- [ ] The main agent has not read a single raw log line outside of sub-agent-returned excerpts

## Exit

Proceed to [phase-3-synthesize.md](./phase-3-synthesize.md).
