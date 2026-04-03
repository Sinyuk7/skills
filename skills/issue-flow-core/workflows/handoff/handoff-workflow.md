# Handoff Workflow

This workflow governs the `issue-handoff` stage.

## Purpose

Synthesize curated evidence into a pure investigation record and a traceable downstream handoff.

## Inputs

- Curated case workspace from collect stage
- `sources.yaml` with registered evidence
- `curated/*` materials
- Optional: `<repo-root>/ISSUE_CONTEXT.md` for project context
- Optional: Repository access for code context

## Outputs

- `analysis/investigation.xml` - pure investigation record with evidence refs
- `analysis/handoff.xml` - concise downstream handoff with code context
- `analysis/next-step.yaml` - recommended next action

## Workflow Steps

### 1. Prerequisites Check

Verify case is ready for handoff:

```bash
python scripts/check_readiness.py <case-path> collect_ready
```

If not ready, direct user back to `issue-collect`.

### 2. Context Loading

- Read `<repo-root>/ISSUE_CONTEXT.md` if present
- Load `sources.yaml` for evidence inventory
- Review curated materials in `curated/`

### 3. Investigation Synthesis

Create `analysis/investigation.xml` with:

**Evidence Refs**:
- Point to curated materials: `curated/logs/`, `curated/media/`, etc.
- Point to repository evidence: file paths, symbols, line numbers
- Each ref must resolve to actual artifact

**Confirmed Facts**:
- Facts verified from evidence
- Each fact includes evidence reference

**Inferred Conclusions**:
- Conclusions drawn from evidence
- Each inference includes basis references

**Open Questions**:
- Unresolved questions from investigation
- Explicit about what remains unknown

**Details**:
- Expanded analysis and narrative context
- Organized into logical sections

### 4. Repository Code Context

**Evidence-Driven Repository Reads**:
- Driven by case evidence: paths, symbols, signatures, module clues
- Record as direct repository references (file paths, symbols, line numbers)
- Use repository references rather than copying code into case workspace
- Do NOT do unrestricted whole-repo exploration

**Code Context Structure**:

```xml
<code_context>
  <affected_files>
    <file path="..." reason="..." />
  </affected_files>
  
  <key_symbols>
    <symbol path="..." name="..." line="..." />
  </key_symbols>
  
  <critical_sections>
    <section path="..." start="..." end="..." note="..." />
  </critical_sections>
</code_context>
```

### 5. Handoff Assembly

Create `analysis/handoff.xml` with:

**Summary** (2-4 paragraphs):
- Concise description of the issue
- What is definitively known
- What remains to be determined

**Code Context**:
- Affected files and reasons
- Key symbols and locations
- Critical sections to review

**Known Items**:
- Bulleted list of confirmed facts
- Must be traceable to investigation

**References**:
- Pointer to full investigation record
- Pointer to the project-level `ISSUE_CONTEXT.md` if used

### 6. Next Action Recommendation

Create `analysis/next-step.yaml`:

```yaml
recommended_action: resolve|collect|external|none|blocked
confidence: high|medium|low
verification_status: verified|partial|unavailable  # required when recommending direct close
reasoning: |
  Why this action is recommended
prerequisites:
  - Any prerequisites for the recommended action
notes: |
  Additional context
```

### 7. Traceability Verification

Verify all references resolve:
- Evidence refs in investigation.xml point to existing curated materials
- Repository refs point to actual files/symbols/lines
- Handoff references investigation
- No broken links

### 8. Readiness Verification

Run readiness checker:

```bash
python scripts/check_readiness.py <case-path> handoff_ready
```

If check fails, address blocking issues before advancing.

### 9. Lifecycle Update

Update `status.yaml`:
- `lifecycle: handoff_in_progress` → `handoff_ready`
- `readiness.handoff_ready: true`

Log transition in `activity.md`.

## Boundaries

### Architectural Constraints

**Handoff Stage Boundaries:**
- Input: Work from curated case workspace only
- Output: Synthesize investigation with evidence refs and expanded details
- Assembly: Create traceable handoff with concise summary and code context
- Recommendation: Declare next recommended action
- Context: Read project-level ISSUE_CONTEXT.md when present (never create case-local copy)
- Traceability: Ensure all artifacts link to their evidence sources
- Repository access: Read-only against both issue materials and repository
- Exploration: Evidence-driven repository reads only (no unrestricted whole-repo scanning)
- Structure: One case produces one handoff.xml (flat structure)

## Refinement and Evaluation

Refinement and evaluation are actions on the same case, not separate workflow modes.

If handoff needs improvement:
- Update artifacts in place within the case
- Preserve traceability
- Log refinement reason in `activity.md`
- Lifecycle stays `handoff_in_progress` until ready

## Post-Handoff Contradictions

If new evidence invalidates or materially contradicts `handoff_ready` case:
- Case must leave `handoff_ready`
- If contradiction resolvable from curated materials → move to `handoff_in_progress`
- If requires revisiting raw sources → move back to `collecting`
- Log reason in `activity.md`

## Exit Conditions

- **Success**: `lifecycle: handoff_ready`, `readiness.handoff_ready: true`
- **Need Recollect**: `lifecycle: collecting` with reason documented
- **Blocked**: `lifecycle: blocked` with reason in `activity.md`

## Next Stage

When handoff is ready:
- If `next-step.yaml` recommends `resolve` → proceed to `issue-resolve`
- If recommends `external` → case ready for external use
- If recommends `none` → may close directly once verification state is explicit
- If recommends `collect` → move back to evidence collection
- If `blocked` → document blocker and wait for resolution
