# Lifecycle and State Management

This document explains the issue-flow lifecycle model and state transitions.

## Lifecycle States

### Active States

**new**:
- Case just created
- Intake started
- Evidence not yet curated

**collecting**:
- Raw materials being narrowed into curated working set
- Sources being registered
- Curation in progress

**collected**:
- Curated set sufficient for downstream work
- No longer need to reread raw directories by default
- Ready to begin handoff

**handoff_in_progress**:
- Evidence synthesis underway
- Investigation and handoff artifacts being created
- Analysis artifacts being refined

**handoff_ready**:
- handoff.xml complete and ready for external use or resolve
- Investigation traceable to evidence
- Next action recommended

**resolve_in_progress**:
- Optional resolution work underway
- Implementation or final disposition in progress
- Verification being conducted

### Terminal States

**resolved_verified**:
- Case has verified resolution or verified non-code conclusion
- Strong verification evidence
- Ready to close

**resolved_unverified**:
- Case has explicit outcome
- Verification only partial or unavailable
- Reason for partial verification documented
- Ready to close with caveats

**closed**:
- Case complete
- No further action expected
- May be reopened if user explicitly targets it

### Special States

**blocked**:
- Progress cannot continue without external input
- Missing evidence, access, or user choice
- Explicit blocker documented in activity.md
- Can transition back to working state when unblocked

## State Transition Diagram

```
new
  ↓
collecting ←----- (recollect)
  ↓         ↖
  ↓         blocked
  ↓         ↗
collected
  ↓
handoff_in_progress ←----- (refinement)
  ↓                  ↖
  ↓                  blocked
  ↓                  ↗
handoff_ready
  ↓ (optional)
  ↓
resolve_in_progress
  ↓                  ↖
  ↓                  blocked
  ↓                  ↗
resolved_verified / resolved_unverified
  ↓
closed
  ↓ (reopen)
  ↓
(back to appropriate working state)
```

## Valid Transitions

| From | To | Trigger |
|------|-----|---------|
| new | collecting | Intake started |
| collecting | collected | Curation sufficient |
| collecting | blocked | Missing critical input |
| collected | handoff_in_progress | Begin evidence synthesis |
| collected | blocked | Cannot proceed |
| handoff_in_progress | handoff_ready | All handoff artifacts complete |
| handoff_in_progress | collecting | Need more evidence (recollect) |
| handoff_in_progress | blocked | Missing critical context |
| handoff_ready | resolve_in_progress | Begin resolution work |
| handoff_ready | closed | Non-actionable, no resolution needed |
| handoff_ready | collecting | Material contradiction (recollect) |
| handoff_ready | blocked | Cannot proceed |
| resolve_in_progress | resolved_verified | Fix implemented and verified |
| resolve_in_progress | resolved_unverified | Fix implemented, verification partial |
| resolve_in_progress | blocked | Cannot proceed |
| resolved_verified | closed | No further action needed |
| resolved_unverified | closed | No further action needed |
| blocked | collecting | Blocker resolved, need more evidence |
| blocked | handoff_in_progress | Blocker resolved, continue handoff |
| blocked | resolve_in_progress | Blocker resolved, continue resolution |
| closed | collecting | Case reopened, need more evidence |
| closed | handoff_in_progress | Case reopened, refine handoff |
| closed | resolve_in_progress | Case reopened, additional resolution |

## Readiness Checkpoints

### collect_ready

Required for `collected` state:

- `sources.yaml` exists
- Curated materials exist for evidence judged relevant
- Unresolved raw-source questions are explicit
- Can continue from curated artifacts alone

Check command:
```bash
python scripts/check_readiness.py <case-path> collect_ready
```

### handoff_ready

Required for `handoff_ready` state:

- `investigation.xml` exists
- `handoff.xml` exists
- `next-step.yaml` exists
- Traceability intact across handoff artifacts
- All references resolve

Check command:
```bash
python scripts/check_readiness.py <case-path> handoff_ready
```

### resolve_ready

Required for entering resolve:

- `handoff.xml` exists
- Chosen resolution path is explicit

Check command:
```bash
python scripts/check_readiness.py <case-path> resolve_ready
```

### close_ready

Required for `closed` state:

- Resolution is recorded OR non-resolution conclusion is recorded
- Verification state is explicit
- Next action is `none` or `external`

Check command:
```bash
python scripts/check_readiness.py <case-path> close_ready
```

## Source of Truth

**status.yaml** is the single source of truth for per-case lifecycle state.

```yaml
case_id: "example-case"
lifecycle: handoff_ready
stage: handoff
updated_at: "2026-04-02T10:30:00Z"
readiness:
  collect_ready: true
  handoff_ready: true
  resolve_ready: false
  close_ready: false
notes: ""
```

**next-step.yaml** records recommended action, not authoritative case state.

## Case Selection

**Current case** is session-local only.

Across sessions, user must explicitly name the case to continue.

When new evidence arrives without explicit target:
- Ask whether to append to current session case or write to another case
- When user explicitly targets a case, obey that target without semantic warnings

## Case Discovery

v1 is filesystem-based:
- Enumerate `.issue-flow/cases/` on demand
- No project-level state files for discovery
- No active-case selection registry

## Activity Logging

All significant state transitions logged in `activity.md`:

```markdown
## 2026-04-02T10:30:00Z

**Event**: Evidence collection complete
**Lifecycle**: collecting → collected
**Trigger**: Curated evidence set is sufficient
**Details**: Registered 5 sources, curated 3 logs and 2 screenshots
```

## Reopening Policy

Closed cases may be reopened when user explicitly targets that case:

1. Move lifecycle back to stage-appropriate working state
2. Log reopen reason in `activity.md`
3. Do NOT force brand-new case

Reopen moves lifecycle to:
- `collecting` if need more evidence
- `handoff_in_progress` if refining handoff
- `resolve_in_progress` if additional resolution needed

## Blocking Conditions

Enter `blocked` state when:

- Progress depends on missing raw input
- Missing access (repository, logs, environment)
- Unanswered user choice
- Cannot determine which case should own a write
- Ambiguous write target

Blocked state requires:
- Explicit blocker documented in `activity.md`
- Clear path to unblock
- Lifecycle can resume appropriate working state when unblocked
