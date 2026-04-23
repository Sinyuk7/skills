# Issue Investigate Workflow

## 1. Resolve Repository

Resolve the owning repository before creating or reading a case.

- Prefer an explicit repository path.
- Otherwise derive the repo root from a user-provided evidence or code path.
- Use the current working directory only when the conversation is already clearly inside the target repo.
- Stop and ask when more than one repository is plausible.

## 2. Initialize Case State

Resolve `case_id` from an explicit case ID, ticket ID, or stable issue slug.

Use the skill-local wrapper command `scripts/case-state init-case` to create or reopen the case. Pass:

- `PROJECT_ROOT`
- `CASE_ID`
- summary
- original user context
- evidence source list, when available

The wrapper owns skill-root path resolution and delegates to the Python implementation.
The underlying state tool owns `case.yaml` creation, timestamp updates, unknown-key preservation, and evidence-source merging.

## 3. Normalize Investigation Target

Before deep evidence work, extract:

- `primary_question`
- `primary_time_anchor`
- `named_stakeholders`
- `secondary_anchors`, only when they matter

If the target is ambiguous, stop and ask the user.

Use `scripts/case-state record-target` after the target is normalized.

## 4. Explore Evidence

Use generic system-call capabilities instead of hard-coded vendor parsers:

- fuzzy search
- chunked file reads
- archive listing or safe extraction
- image or media inspection

Rules:

- Do not assume one timestamp format or one log layout.
- Do not read entire large logs when search plus chunked reads can narrow the scope.
- Do not promote a different interesting timestamp into the main conclusion.
- If the requested anchor cannot be matched, use `scripts/case-state record-blocked`.

Read repository code only after evidence points to a concrete area to correlate.

## 5. Write Investigation Report

Use `templates/investigation.md`.

The report must contain:

- working statement
- primary target
- evidence window used
- cited findings
- code correlation when relevant
- root cause or blocked reason
- next step

## 6. Finalize Case State

Use `scripts/case-state record-root-cause` when the investigation is complete.

Use `scripts/case-state record-blocked` when evidence is missing, the anchor is ambiguous, or the observed failure does not match the requested target.
