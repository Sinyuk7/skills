# Phase 1 — Intake & Target Normalization

Main agent, in conversation with the user. No sub-agents yet.

Goal: produce a case workspace with a normalized investigation target. If the target cannot be normalized, stop and ask — do NOT proceed to Phase 2.

## 1.1 Resolve Repository
<!-- validation_step -->

Resolve `PROJECT_ROOT` before creating or reading any case file.

- Prefer an explicit repository path from the user.
- Otherwise derive the repo root from a user-provided evidence or code path:
  ```bash
  git -C "<file-directory-or-repo-path>" rev-parse --show-toplevel
  ```
- Use plain `git rev-parse --show-toplevel` **only** when the current working directory is already known to be the target repository.
- Stop and ask if more than one repository is plausible.

Never default to the skill repository or any unrelated repo just because a git command succeeds there. Do not inline `git rev-parse --show-toplevel` again in later commands; reuse the already-resolved absolute `PROJECT_ROOT`.

## 1.2 Initialize Case State
<!-- mutation_step -->

Resolve `case_id` from an explicit case ID, ticket ID, or a stable issue slug.

Create or reopen the case via the skill-local wrapper:

```bash
scripts/case-state init-case \
  --project-root "$PROJECT_ROOT" \
  --case-id "$CASE_ID" \
  --summary "<one-line summary>" \
  --user-context "<original user-provided description>" \
  --evidence-sources '<JSON array of {kind, path, note}>'
```

The wrapper owns skill-root path resolution and delegates to `case_state.py`. The underlying tool owns `case.yaml` creation, timestamp updates, unknown-key preservation, and evidence-source merging.

If the case already exists, `init-case` reopens it and merges new evidence sources without dropping existing ones. Do not hand-maintain `case.yaml` at any point.

## 1.3 Normalize Investigation Target
<!-- reasoning_step + mutation_step -->

Before deep evidence work, extract:

- `primary_question` — the one thing the user wants answered
- `primary_time_anchor` — the dominant timestamp; if user gave a range, pick the earlier end
- `named_stakeholders` — people the user referenced
- `secondary_anchors` — only when they matter as cross-references

If the target is ambiguous (multiple plausible primary questions or anchors) stop and ask the user. Do NOT pick one silently.

Persist the normalized target:

```bash
scripts/case-state record-target \
  --project-root "$PROJECT_ROOT" \
  --case-id "$CASE_ID" \
  --primary-question "..." \
  --primary-time-anchor "..." \
  --named-stakeholders '["..."]' \
  --secondary-anchors '[]'
```

## 1.4 Exit Criteria for Phase 1

Phase 1 is done when ALL of these are true:

- [ ] `PROJECT_ROOT` is an absolute, confirmed path
- [ ] `case.yaml` exists with `status: investigating`
- [ ] `primary_question` is set
- [ ] `primary_time_anchor` is set (or explicitly marked as "none" with user consent)
- [ ] `evidence_sources` contains at least one entry or the user confirmed there is none

If any item is missing, block Phase 2 and either ask the user or `record-blocked` with the appropriate kind (`missing_evidence` / `ambiguous_anchor` / `insufficient_context`).

## Exit

Proceed to [phase-2a-plan-excavation.md](./phase-2a-plan-excavation.md).
