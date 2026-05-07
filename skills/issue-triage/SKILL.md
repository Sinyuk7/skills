---
name: issue-triage
description: Triage issue-flow cases end to end - create or reopen a case, normalize the investigation target, dispatch sub-agents to excavate evidence, and conclude with a cited disposition. Use when a user reports a new bug or issue with logs, screenshots, or traces, continues an existing case with supplementary evidence, asks for root cause analysis, requests investigation directions when evidence is insufficient, or wants a case closed as wont_fix, duplicate, already_fixed, or cannot_reproduce. Also matches Chinese requests such as 分析问题、根因分析、继续分析、补充日志、关闭问题。Do not use for pure code review, branch bootstrap, or post-triage Overmind sync.
---

# Issue Triage

Single entry point for issue-flow: intake, plan, dispatch sub-agents to excavate evidence, synthesize a disposition.

## Invocation

- **Primary argument**: an existing case ID (e.g. `OMMUSIC-3397323`) or a short issue summary for a new case.
- **Optional argument(s)**: one or more absolute paths to evidence files (logs, screenshots, archives).
- **Argument hint**: `[case-id or issue summary] [evidence paths...]`
- **Effort profile**: high — expect multi-phase investigation with sub-agent dispatch.

## When to Use

- User reports a bug or issue with evidence (logs, screenshots, traces).
- User asks for root cause analysis or 根因分析.
- User continues an existing case with new evidence or 补充日志.
- User wants to close a case as `wont_fix`, `duplicate`, `already_fixed`, or `cannot_reproduce`.
- User asks for investigation directions when evidence is insufficient.

## When NOT to Use

- Pure code review.
- Branch bootstrap or repo setup.
- Post-triage Overmind field sync (delegate to `issue-overmind-sync`).

## Capability Contract

```yaml
type: routable_skill
owns:
  - create or reuse a case
  - register or merge evidence references
  - normalize the investigation target (primary_question / primary_time_anchor / named_stakeholders)
  - load project-specific troubleshooting knowledge
  - plan excavation tasks (hypothesis + target source + why + expected_signals)
  - dispatch sub-agents to excavate evidence in parallel
  - synthesize findings into a final disposition
  - write investigation.md
  - update case.yaml
does_not_own:
  - modifying source code
  - running builds / tests to verify a fix
  - final bug-tracker sync (→ /issue-overmind-sync)
delegate_to:
  - /issue-overmind-sync (optional, when disposition.type=root_caused and user wants Overmind updated)
  - a new session (when disposition.type=direction_only, for deep-dive fixing work)
refuses_when:
  - repository ownership is ambiguous
  - the primary investigation target remains ambiguous
  - the user asks for code edits during triage
requires_evidence:
  - user context and/or referenced materials
  - existing case.yaml when continuing a case
primary_outputs:
  - case.yaml (machine-readable state; includes disposition)
  - investigation.md (human-readable report)
allowed_tools: [bash, read, write, edit, grep, glob, task]
forbidden_tools: []
eval_set: evals/evals.json
```

## Dispositions

Every terminated triage records exactly one `disposition.type`:

| type | meaning | next_step.action | typical follow-up |
|------|---------|------------------|-------------------|
| `root_caused` | root cause confirmed with cited evidence | `sync_overmind` | `/issue-overmind-sync` or open a new session to fix |
| `direction_only` | no confirmed root cause, but ranked hypotheses exist | `resume_in_new_session` | user opens a new session with `investigation.md` |
| `blocked` | evidence missing / ambiguous / mismatched | `await_evidence` | user supplies more evidence, retrigger triage |
| `wont_fix` | working as intended | `close` | `/issue-overmind-sync` optional |
| `duplicate` | duplicate of another case | `close` | `/issue-overmind-sync` optional |
| `already_fixed` | already fixed in another commit / PR | `close` | `/issue-overmind-sync` optional |
| `cannot_reproduce` | insufficient evidence to reproduce | `close` | `/issue-overmind-sync` optional |

## Parameters

When invoked with arguments, `$ARGUMENTS` contains the user-provided input. Use it to seed Phase 1 intake:

- `$1` (`case_id`): If it looks like a case ID (e.g. `OMMUSIC-3397323`), use it directly. Otherwise treat it as a new issue summary.
- `$2+` (`evidence_paths`): Register each path as an evidence source in `case.yaml`.

If the user provides multi-word arguments, they must be quoted: `/issue-triage "playback fails after focus change" /tmp/player.log /tmp/ui.png`.

If no arguments are provided, ask the user for the issue summary and evidence paths before proceeding to Phase 1.

## Pipeline

`/issue-triage` is a strict 3-phase pipeline. Follow them in order.

| Phase | File | Kind | Agent |
|-------|------|------|-------|
| 1. Intake | [workflows/phase-1-intake.md](./workflows/phase-1-intake.md) | reasoning + mutation | main |
| 2a. Plan Excavation | [workflows/phase-2a-plan-excavation.md](./workflows/phase-2a-plan-excavation.md) | reasoning | main |
| 2b. Dispatch Excavators | [workflows/phase-2b-dispatch-excavators.md](./workflows/phase-2b-dispatch-excavators.md) | retrieval | **sub-agents (parallel)** |
| 3. Synthesize & Dispose | [workflows/phase-3-synthesize.md](./workflows/phase-3-synthesize.md) | reasoning + mutation | main |

## Execution Surface

- Workflows: see table above
- Sub-agent contract: [agents/evidence-excavator.md](./agents/evidence-excavator.md)
- Public execution entry:
  - [scripts/case-state](./scripts/case-state)
  - [scripts/validate-evals](./scripts/validate-evals) — local sanity check for `evals/*.json`
- Schemas:
  - [schemas/case.yaml](./schemas/case.yaml)
  - [schemas/excavation-plan.yaml](./schemas/excavation-plan.yaml)
- Templates:
  - [templates/investigation.md](./templates/investigation.md)
- Internal implementation detail:
  - [scripts/case_state.py](./scripts/case_state.py)
  - [scripts/validate_evals.py](./scripts/validate_evals.py)
- Evals: [evals/evals.json](./evals/evals.json), [evals/routing-evals.json](./evals/routing-evals.json)

## Operating Rules

- **Context lifecycle:** This skill's content persists for the entire session. If the context window compacts (each skill is capped at ~5,000 tokens after compaction), re-run `/issue-triage` to restore the full workflow. The `case.yaml` and `investigation.md` on disk preserve all state across compactions.
- **Extended thinking:** This skill involves multi-phase reasoning, hypothesis generation, and evidence synthesis. Use `ultrathink` when evaluating competing hypotheses or deciding dispositions on ambiguous evidence.
- Use the skill-local wrapper `./scripts/case-state` for all `case.yaml` mutations. Resolve the wrapper from the skill directory; never assume the target repo cwd contains a matching `scripts/` entry. Never hand-edit `case.yaml`.
- **Evidence excavation MUST go through sub-agents (task tool)** in Phase 2b. The main agent never reads full raw logs itself in this skill. Its job is to plan tasks (Phase 2a) and synthesize returned findings (Phase 3).
- Normalize the target before planning excavation:
  - `primary_question`
  - `primary_time_anchor`
  - `named_stakeholders`
- Write a one-line working statement near the top of `investigation.md` before presenting findings.
- Keep the main conclusion anchored to the primary target. If evidence points at a different timestamp or a different question, do not drift the conclusion — either close with `disposition.type=direction_only` and list both hypotheses, or `record-blocked` with `anchor_mismatch`.
- Do not copy raw evidence into `.issue-flow/`. Evidence paths are referenced only.
- Do not modify source code during this skill. Reading code for correlation is allowed; writing is not.

## When To Ask The User

Ask instead of guessing when:

- more than one repository could own the case
- multiple candidate anchors remain unresolved
- the required evidence path is missing
- the observed failure does not match the requested anchor

## Handoff Messages

When triage concludes, tell the user one of:

- `root_caused` →
  > Case `<case-id>` triaged. Root cause: `<summary>` at `<location>`. Run `/issue-overmind-sync` to update Overmind, or open a new session to implement the fix using `investigation.md`.
- `direction_only` →
  > Case `<case-id>` triaged with investigation directions (no confirmed root cause). Ranked hypotheses are in `investigation.md`. Open a new session to pursue the top direction.
- `blocked` →
  > Case `<case-id>` blocked: `<reason>`. Please supply `<missing evidence>` and re-run `/issue-triage`.
- `wont_fix` / `duplicate` / `already_fixed` / `cannot_reproduce` →
  > Case `<case-id>` closed as `<type>`. `<summary>`. Optionally run `/issue-overmind-sync` to reflect this in Overmind.
