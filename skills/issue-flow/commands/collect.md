# Collect Command

Curate raw user-provided issue materials into a case workspace.

## Purpose

Transform raw materials (logs, screenshots, videos, archives, notes) into a curated evidence set ready for downstream analysis.

## When to Use

- User reports a bug and provides raw materials
- User asks to investigate an issue
- User provides logs, screenshots, or other evidence
- User wants to create or update an issue case

## Prerequisites

At least one non-repository issue input must exist. The repository alone is not enough to start a case.

## Step 1: Case Identification

**Decision Point**: Create new case or append to existing?

Ask user if unclear:
- If user explicitly names target case → use that case
- If session has "current case" and user doesn't specify → **ask user**
- If no target case → create new case

**Case ID Rules**:
- Prefer bug ID or issue number when available
- Otherwise derive stable slug from issue title
- Add timestamp suffix only to avoid collisions
- Case ID remains stable after creation

**BLOCKING CONDITION**: If write target is unclear, STOP and ask user.

## Step 2: Context Loading

Check for `ISSUE_CONTEXT.md` in project root.

If present, extract:
- Common failure patterns
- Critical areas requiring attention
- Architecture notes
- Investigation priorities

Use this context to guide curation decisions.

## Step 3: Initialize Case Structure

If creating new case, set up directory structure:

```text
.issue-flow/cases/<case-id>/
├── status.yaml
├── activity.md
├── sources.yaml
└── curated/
```

Initialize from templates in `templates/case/`:
- `status.yaml` with `lifecycle: new`
- `activity.md` with case creation event
- `sources.yaml` for source registration

## Step 4: Source Registration

For each user-provided input, register in `sources.yaml`:

```yaml
sources:
  - id: "unique-id"
    origin: issue_material
    kind: path|archive|url|note|media
    location: "original-location"
    collected: "curated/path" or "skipped"
    note: "reason for collection or skip"
```

## Step 5: Material Curation

**Curation Subdirectories**:
- `curated/logs/` - log files
- `curated/media/` - screenshots, videos
- `curated/notes/` - issue descriptions, user notes
- `curated/ocr/` - extracted text from images
- `curated/excerpts/` - relevant snippets from large files

**For each source, decide**:

1. **Copy**: Relevant material → copy into appropriate `curated/` subdirectory
2. **Extract**: Archive or structured data → extract and organize
3. **Skip**: Not relevant → mark as `collected: skipped` with reason

**Mutation Recording**:

If collect modifies issue-material roots (v1 allows this):
- Log action in `activity.md`
- Record in `sources.yaml` mutations section:

```yaml
mutations:
  - timestamp: "..."
    action: extracted|renamed|created|rewritten
    target: "..."
    reason: "..."
```

## Step 6: Evidence-Driven Repository Reads

Repository reads during collect must be **evidence-driven**, not open-ended exploration.

**Allowed**:
- Search for paths mentioned in issue materials
- Look up symbols from error messages
- Find files referenced in logs

**Forbidden**:
- Unrestricted whole-repo exploration
- Browsing unrelated modules
- Open-ended architecture discovery

Record repository evidence in `sources.yaml`:

```yaml
- id: "repo-ref-1"
  origin: repository
  kind: file|symbol|line_range
  location: "src/path/to/file.ts:42"
  note: "Error originates here per stack trace"
```

**Collect does NOT modify project repository** - repository access is read-only.

## Step 7: Sufficiency Check

**Collect-Enough Rule**:

Collect is sufficient when:
- User-provided raw inputs are registered
- Relevant materials are curated into `curated/`
- Skipped materials are explicitly accounted for
- Case can continue from curated artifacts alone
- No unresolved critical gaps

**If sufficient**:
```yaml
lifecycle: collecting → collected
readiness:
  collect_ready: true
```

Log transition in `activity.md`.

**If gaps remain**:
```yaml
lifecycle: collecting → blocked
```

Document what's missing in `activity.md` and ask user.

## Step 8: Readiness Verification

Run readiness checker:

```bash
python scripts/check_readiness.py <case-path> collect_ready
```

**Pass conditions**:
- `sources.yaml` exists
- Curated materials exist for evidence judged relevant
- Unresolved raw-source questions are explicit

**If check fails**: Address blocking issues before declaring collect complete.

## Recollect Policy

Reopen raw sources only when:
- User provides new raw input
- `next-step.yaml` explicitly calls for more evidence
- Ambiguity cannot be resolved from curated materials
- User explicitly asks to revisit raw directory

When recollect happens:
- Record why in `activity.md`
- Document new sources in `sources.yaml`
- Update curated set
- May move `lifecycle` back to `collecting`

## Partial Failure Handling

If some inputs succeed but others fail:
- Record which inputs failed and why in `activity.md`
- **DO NOT** silently advance as if collect were complete
- Pause for explicit user confirmation before advancing with known gaps
- Keep `lifecycle: collecting` or move to `blocked`

## Boundaries

### Must Do

- Create or resume a case with clear identity
- Register all inputs in `sources.yaml`
- Curate relevant materials into `curated/`
- Record lifecycle transitions in `status.yaml` and `activity.md`
- Operate only over two roots: issue materials and current repository
- Ask user if write target is unclear

### Must Not Do

- Try to produce final handoff (that's handoff stage)
- Repeatedly rescan raw directories after curation complete
- Modify project repository (read-only for collect)
- Start case from repository alone without issue materials
- Default to writing into unclear target case
- Do unrestricted whole-repo exploration

## Exit Conditions

- **Success**: `lifecycle: collected`, ready for handoff stage
- **Blocked**: `lifecycle: blocked` with reason documented
- **Need More**: `lifecycle: collecting` with specific gap documented

## Next Move

Once collect is complete, load `commands/handoff.md` to begin evidence synthesis.

## Workflow Reference

For detailed collect workflow, see `workflows/collect/collect-workflow.md`.
