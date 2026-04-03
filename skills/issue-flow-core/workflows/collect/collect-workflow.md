# Collect Workflow

This workflow governs the `issue-collect` stage.

## Purpose

Transform raw user-provided issue materials into a curated evidence workspace.

## Inputs

- User-provided issue materials (logs, screenshots, videos, archives, notes)
- Optional: existing case to append to
- Optional: ISSUE_CONTEXT.md for project-level conventions

## Runtime Model

Before collect work begins:

- Resolve the current git repository root
- Use `<repo-root>/.issue-flow/cases/` as the runtime workspace root
- Use `<repo-root>/ISSUE_CONTEXT.md` as the optional project-level context file
- Read workflow docs, templates, and scripts from the installed skills tree
- Do not create or depend on a separate repo-local `.issue-flow-core/` directory
- Stop with a clear error only when required case artifacts or project context assumptions are missing

## Outputs

- `status.yaml` with lifecycle state
- `sources.yaml` registering all inputs and curation results
- `curated/*` with relevant extracted materials
- `activity.md` with collect events logged

## Workflow Steps

### 1. Case Identification

**Decision Point**: Create new case or append to existing?

- If user explicitly names a target case → use that case
- If session has a "current case" and user doesn't specify → ask user
- If no target case → create new case

**Case ID Rules**:
- Prefer bug ID or issue number when available
- Otherwise derive stable slug from issue title
- Add timestamp suffix only when needed to avoid collisions

**Blocking Condition**: If write target is unclear, STOP and ask user

### 2. Context Loading

Load `ISSUE_CONTEXT.md` if present in project root.

Extract relevant:
- Common failure patterns
- Critical areas
- Architecture notes
- Investigation priorities

`ISSUE_CONTEXT.md` remains a project-level source file. Do not copy it into the
case directory or create case-local variants.

### 3. Source Registration

For each user-provided input, record in `sources.yaml`:

```yaml
- id: "unique-id"
  origin: issue_material
  kind: path|archive|url|note|media
  location: "original-location"
  collected: "curated/path" or "skipped"
  note: "reason for collection or skip"
```

### 4. Material Curation

**Evidence-Driven Repository Reads**:
- Repository reads must be anchored to issue evidence
- Look for paths, symbols, or error signatures mentioned in issue materials
- Do NOT do open-ended whole-repo exploration
- Record repository evidence as direct references in `sources.yaml`

**Curation Actions**:

For each source, decide:

1. **Copy**: Relevant material copied into `curated/` subdirectory
   - `curated/logs/` for log files
   - `curated/media/` for screenshots, videos
   - `curated/notes/` for issue descriptions, user notes
   - `curated/ocr/` for extracted text from images
   - `curated/excerpts/` for relevant snippets from large files

2. **Extract**: Archive or structured data extracted and organized

3. **Skip**: Not relevant, mark as `collected: skipped` with reason

**Mutation Recording**:
- If collect modifies issue-material roots, log in `activity.md`
- Record action type in `sources.yaml` mutations section

### 5. Sufficiency Check

**Collect-Enough Rule**:

Collect is sufficient when:
- User-provided raw inputs are registered
- Relevant materials are curated
- Skipped materials are explicitly accounted for
- Case can continue from curated artifacts alone

If collect is sufficient:
- Update `status.yaml` lifecycle: `collecting` → `collected`
- Set `readiness.collect_ready: true`
- Log in `activity.md`

If gaps remain:
- Update `status.yaml` lifecycle: `collecting` → `blocked`
- Document what's missing in `activity.md`
- Ask user for missing information

### 6. Readiness Verification

Run readiness checker:

```bash
python scripts/check_readiness.py <case-path> collect_ready
```

If check fails, address blocking issues before advancing.

## Boundaries

### Must Do

- Create or resume a case
- Register all inputs in `sources.yaml`
- Curate relevant materials into `curated/`
- Record lifecycle transitions in `status.yaml` and `activity.md`
- Operate only over two roots: issue materials and current repository

### Architectural Constraints

**Collect Stage Boundaries:**
- Scope: Evidence curation only (handoff synthesis happens in handoff stage)
- Context: Project-level `ISSUE_CONTEXT.md` remains at repo root (never copied to case)
- Repository: Read-only (code modifications happen in resolve stage)
- Input requirement: At least one issue material required (cannot start from repository alone)
- Write target: Case ID must be determined before beginning curation
- Scan policy: Do not repeatedly rescan raw directories after curation complete

## Recollect Policy

Reopen raw sources only when:
- User provides new raw input
- Downstream artifact explicitly calls for more evidence
- Ambiguity cannot be resolved from curated materials
- User explicitly asks to revisit raw directory

When recollect happens:
- Record why in `activity.md`
- Document new sources in `sources.yaml`
- Update curated set
- May move lifecycle back to `collecting` if needed

## Partial Failure Handling

If some inputs succeed but others fail:
- Record which inputs failed and why in `activity.md`
- Do NOT silently advance as if collect were complete
- Pause for explicit user confirmation before advancing with known gaps
- Keep lifecycle as `collecting` or move to `blocked`

## Exit Conditions

- **Success**: `lifecycle: collected`, `readiness.collect_ready: true`
- **Blocked**: `lifecycle: blocked` with reason in `activity.md`
- **Need More**: `lifecycle: collecting` with specific gap documented

## Next Stage

When collect is ready, proceed to `issue-handoff` stage.
