---
name: issue-resolve
description: Continue an issue-flow case from handoff into implementation, verification, or a final non-code disposition. Use when a case already has `handoff.xml` and the user wants to fix, verify, or close it.
---

# Issue Resolve

Thin entry skill for Stage 3 of the issue-flow system.

Shared logic lives in `../issue-flow-core/`. Use this skill as the user-facing entrypoint, then load the shared core files you need.

## Load These Core Files First

- `../issue-flow-core/workflows/resolve/resolve-workflow.md`
- `../issue-flow-core/workflows/actions/lifecycle-management.md`
- `../issue-flow-core/knowledge/issue-flow-principles.md`
- `../issue-flow-core/knowledge/artifact-contracts.md`

Load templates and scripts only when needed:

- `../issue-flow-core/templates/resolve/`
- `../issue-flow-core/scripts/check_readiness.py`

## Mission

Optionally continue from `analysis/handoff.xml` into:

- a code or config change
- a verified non-code conclusion
- an external disposition

Record the result in:

- `resolve/resolution.xml`
- `resolve/verification.md`

## Non-Negotiables

- Require an existing handoff before resolve work starts.
- Only resolve may modify the project repository.
- Do not rewrite prior collect or handoff artifacts as a substitute for resolution output.
- Record verification state explicitly for every outcome.
- Do not make external tracker sync a prerequisite for finishing resolve. External submission belongs to optional follow-up skills.

## Exit

- Move to `resolved_verified` or `resolved_unverified` when the outcome is explicit.
- Close the case only when `close_ready` passes and the next action is explicit.
- If the user wants to sync the resolved case into Overmind, hand off to the optional plugin skill `../issue-overmind-sync` after resolve artifacts are complete.
