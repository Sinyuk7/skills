# PRD: issue-flow

Status: Draft
Owner: Skills repo
Scope: Shared issue-flow core plus three stage entry skills

## 1. Summary

`issue-flow` is a case-centric workflow for investigating a single issue across
multiple sessions. It replaces the deprecated `issue-triage-handoff` model with
a progressive workspace model:

```text
raw sources -> curated evidence set -> structured handoff -> optional resolution
```

The system is split into three thin skill entrypoints:

- `issue-collect`
- `issue-handoff`
- `issue-resolve`

The shared logic lives in `skills/issue-flow-core/`.

## 2. Problem

The deprecated workflow centered the experience on generating a handoff package.
That caused several design problems:

- the main entrypoint became too large
- decision routing, refinement, evaluation, schemas, and script usage were mixed
- the main artifact was a JSON handoff document instead of a case workspace
- project context lived in skill-specific conventions instead of project-level
  issue conventions
- the workflow introduced heavy branching before the case workspace existed

## 3. Goals

- Make the case workspace the primary unit of work.
- Support gradual progress over multiple sessions.
- Read project-level context from `ISSUE_CONTEXT.md` as early as possible.
- Avoid re-reading large raw directories after evidence is curated.
- Use Markdown, YAML, and XML as the primary artifact formats.
- Keep entry `SKILL.md` files thin and maintainable.
- Support optional resolution without forcing every case through a fix stage.

## 4. Non-goals

- Full OpenSpec parity
- A rigid state machine with hard stage gates
- JSON-first schemas as the main authoring model
- A mandatory resolution phase for all issues
- A generic external ticketing integration layer in v1
- Sensitive-data redaction or privacy-preserving sharing layer in v1
- Automatic import of legacy `issue-triage-handoff` artifacts

Optional external sync skills may still exist in separate skill directories, but
they are plugins on top of the case workspace rather than additional core
stages.

## 5. Primary User Story

As a teammate investigating a bug or issue, I want to create a stable case
workspace inside the project so I can narrow evidence, build a traceable handoff,
and optionally continue into a fix without restarting the investigation from raw
materials.

This workflow assumes at least one non-repo issue input exists, such as logs,
screenshots, videos, archives, or user-provided issue notes.

## 6. Product Principles

- Case first: every issue gets its own directory.
- Curate once: collect narrows raw materials into a working set.
- Traceability always: downstream artifacts must point back to curated evidence.
- Soft readiness: dependencies unlock artifacts, but do not force the next stage.
- Human-readable by default: artifacts should work for both humans and LLMs.
- Shared namespace: workflow logic is shared, skill entrypoints stay small.
- Status truth lives inside the case, not in project-level indexes.
- Ambiguity should trigger a user choice, not an implicit write.
- v1 assumes a trusted local workflow and does not treat sensitive-data exposure
  as an in-scope design concern.
- The workflow operates within two roots only: user-provided issue materials and
  the current project repository.
- Repository exploration must stay evidence-driven, not open-ended.
- Mutability is stage-specific: collect may modify issue-material roots,
  handoff is read-only against source roots, and only resolve may modify the
  project repository.
- A case is a user-managed investigation container and may represent one or more
  problems without introducing split or sub-issue workflow semantics.
- Handoff artifacts should stay simple and readable; v1 does not require nested
  per-problem structures inside a case.

## 7. Proposed Information Architecture

### Project-level workspace

```text
<project-root>/
├── ISSUE_CONTEXT.md
└── .issue-flow/
    └── cases/
        └── <case-id>/
```

### Case-level workspace

```text
.issue-flow/cases/<case-id>/
├── activity.md
├── status.yaml
├── sources.yaml
├── curated/
│   ├── logs/
│   ├── media/
│   ├── notes/
│   ├── ocr/
│   └── excerpts/
├── analysis/
│   ├── investigation.xml
│   ├── handoff.xml
│   └── next-step.yaml
├── resolve/
│   ├── resolution.xml
│   └── verification.md
```

## 8. Stage Definitions

### Stage 1: issue-collect

Responsibilities:

- create or resume a case
- read `ISSUE_CONTEXT.md` if present
- register raw inputs and collected outcomes in `sources.yaml`
- copy or extract only relevant material into `curated/`
- operate only over two roots: the user-provided issue-material paths and the
  current project repository
- may modify user-provided issue-material roots directly in v1
- v1 does not restrict the kinds of direct edits `issue-collect` may make
  within user-provided issue-material roots
- may append additional user-provided issue-material roots to an existing case
  during later collect sessions when the user explicitly targets that case

Boundary:

- does not try to produce the final handoff
- does not default to repeated rescans of the raw source directories after
  curation is complete
- must decide when evidence is "collect enough" for the case to advance
- if writing target is unclear, ask whether to write into the current case or a
  different case
- ambiguous write target is a blocking condition, not a warning-only condition
- repository reads during collect should be anchored to issue evidence, not used
  as unrestricted whole-repo exploration
- collect does not modify the project repository
- creating a case requires at least one non-repo issue input; the repository
  alone is not enough to start a case

Primary outputs:

- `status.yaml`
- `sources.yaml`
- `curated/*`

### Stage 2: issue-handoff

Responsibilities:

- work from the curated case workspace
- synthesize a pure investigation record with evidence refs and expanded details
- assemble a traceable handoff with a concise summary and relevant code context
- declare the next recommended action
- read `ISSUE_CONTEXT.md` directly when present

Boundary:

- no mandatory fixing
- refinement and evaluation are actions on the same case, not separate top-level
  workflow modes
- this stage is the required producer of `handoff.xml`
- repository reads during handoff should be driven by case evidence such as
  paths, symbols, signatures, and module clues
- repository evidence should be recorded as direct repository references such as
  file paths, symbols, and line numbers, not copied into the case workspace as
  code excerpts in v1
- one case produces one `handoff.xml`; v1 does not require additional nested
  per-problem handoff structures
- handoff is read-only against both source roots

Primary outputs:

- `analysis/investigation.xml`
- `analysis/handoff.xml`
- `analysis/next-step.yaml`

### Stage 3: issue-resolve

Responsibilities:

- optionally continue from handoff into a fix or final disposition
- record implementation, verification, and closure artifacts
- support non-code conclusions when resolution is external or unnecessary
- may modify the current project repository when resolution requires code
  changes

Boundary:

- optional stage
- should not rewrite or replace prior evidence artifacts
- requires an existing `handoff.xml`; if it is missing, the workflow should stop
  and direct the user back to `issue-handoff`
- resolve does not grant permission to rewrite prior issue-material roots as a
  substitute for case artifacts

Primary outputs:

- `resolve/resolution.xml`
- `resolve/verification.md`

## 8.5 Lifecycle and Readiness Model

Each case should have an explicit lifecycle recorded in `status.yaml`.

### Lifecycle states

- `new`: case created, intake started, evidence not yet curated
- `collecting`: raw materials are being narrowed into a curated working set
- `collected`: curated set is sufficient for downstream work to begin
- `handoff_in_progress`: evidence synthesis and handoff assembly are underway
- `handoff_ready`: `handoff.xml` is ready for external use or for resolve
- `resolve_in_progress`: optional resolution work is underway
- `resolved_verified`: case has a verified resolution or a verified non-code
  conclusion
- `resolved_unverified`: case has an explicit outcome, but verification is only
  partial or unavailable in the current context
- `closed`: case is complete and no further action is expected
- `blocked`: progress cannot continue without external input or missing evidence

### Readiness checkpoints

- `collect_ready`:
  - `sources.yaml` exists
  - curated materials exist for the evidence judged relevant
  - unresolved raw-source questions are explicit
- `handoff_ready`:
  - `investigation.xml` exists
  - `handoff.xml` exists
  - `next-step.yaml` exists
  - traceability is intact across handoff artifacts
- `resolve_ready`:
  - `handoff.xml` exists
  - chosen resolution path is explicit
- `close_ready`:
  - resolution is recorded OR a non-resolution conclusion is recorded
  - verification state is explicit
  - next action is `none` or `external`

### Lightweight readiness checker

v1 should include a lightweight readiness checker for major stage boundaries.

The checker should validate only objective conditions:

- required artifacts exist for the requested boundary
- required references resolve inside the case workspace
- the requested lifecycle transition is compatible with the current
  `status.yaml`
- terminal states have an explicit recorded outcome

The checker should not:

- judge whether the writing is "good"
- score evidence quality
- enforce a heavy schema beyond minimum structural expectations
- replace human review before handoff or resolve

The checker output should stay simple:

- `pass`: boundary conditions are satisfied
- `fail`: one or more blocking conditions are missing
- a short list of blocking reasons with concrete artifact paths or missing
  references

The checker is a guardrail, not a second workflow. It exists to catch obvious
state mistakes early and keep stage transitions honest.

### Enter and exit rules

- Enter `collected` only when the curated evidence set is sufficient for
  downstream reasoning.
- Enter `handoff_ready` only when the case can be handed to another human,
  another agent, or a later session without re-reading raw directories.
- Enter `resolved_verified` only when the outcome is explicit and verification is
  strong enough for confidence.
- Enter `resolved_unverified` only when the outcome is explicit but verification
  remains partial, blocked, or impossible in the current environment.
- Enter `blocked` whenever progress depends on missing raw input, missing access,
  or an unanswered user choice.
- Enter `blocked` whenever the workflow cannot determine which case should own a
  write.
- a case in `closed` may be reopened only when the user explicitly targets that
  case for continued work
- reopening should move the case back to the stage-appropriate working state
  rather than forcing a brand-new case
- the reopen reason should be recorded in `activity.md`

### Source of truth

- `status.yaml` is the single source of truth for per-case lifecycle state.
- `next-step.yaml` records recommended action, not authoritative case state.
- v1 does not maintain project-level state files for discovery or active-case
  selection.
- case selection should be explicit: continue the current case in session, or
  name the target case directly.
- "current case" is session-local only; across sessions the user must explicitly
  name the case to continue
- when new evidence arrives without an explicit target case, the workflow should
  ask whether to append to the current session case or write to another case
- case discovery in v1 is filesystem-based on demand by enumerating
  `.issue-flow/cases/`, not by maintaining a separate registry
- when the user explicitly targets a case, the workflow should obey that target
  without adding semantic warnings about whether the new material "matches"

## 8.6 Evidence Sufficiency and Recollect Policy

`issue-flow` treats curation as a boundary, not just a convenience.

### Collect-enough rule

Collect is considered sufficient when:

- the user-provided raw inputs have been registered
- relevant materials have been curated into the case workspace
- skipped or unresolved raw materials are explicitly accounted for
- the case can continue from curated artifacts alone

### Default rule after collect

- once a case reaches `collected`, downstream stages should work from the case
  workspace, not from the original raw directories

### Recollect policy

Reopening raw sources is allowed only when one of these is true:

- the user provides new raw input
- `next-step.yaml` explicitly calls for additional evidence collection
- an ambiguity or contradiction cannot be resolved from curated materials alone
- the user explicitly asks to revisit the raw directory

### Recollect recording

When recollect happens, the case should record:

- why recollect was necessary
- what new raw source was consulted
- what changed in the curated set
- whether the case state moved back from `collected` to `collecting`

### Source-mutation recording

Because v1 allows `issue-collect` to modify user-provided issue-material roots:

- any material change to those roots should be recorded in `activity.md`
- `sources.yaml` should make it clear which items were discovered as-is versus
  created, extracted, renamed, or rewritten during collect
- this recording should stay simple and human-readable; it does not require a
  nested mutation model

### Post-handoff contradiction rule

- if new evidence invalidates or materially contradicts a `handoff_ready` case,
  the case must leave `handoff_ready`
- if the contradiction can be resolved from curated materials alone, move back
  to `handoff_in_progress`
- if resolving the contradiction requires revisiting raw sources, move back to
  `collecting`

### Partial-collect failure handling

If some raw inputs are successfully processed but others fail:

- the case must record which inputs failed and why
- the workflow must not silently treat the curated set as complete
- the system should pause for explicit user confirmation before advancing with
  known evidence gaps
- until that confirmation happens, the case should remain `collecting` or move
  to `blocked`, rather than advancing as if collect were complete

## 8.7 Canonical Walkthrough

This workflow should include one canonical example case that demonstrates the
golden path end to end.

### Example narrative

1. User reports a bug and provides a log directory, two screenshots, and a short
   problem statement.
2. `issue-collect` creates `.issue-flow/cases/<case-id>/`, writes
   `sources.yaml`.
3. Relevant logs, OCR output, and excerpts are copied into `curated/`.
4. `status.yaml` advances from `new` to `collecting`, then to `collected` once
   the curated evidence set is sufficient.
5. `activity.md` records each significant step: collect start, collect complete,
   recollect trigger, handoff start, handoff ready, resolve start, resolved, and
   closed.
6. `issue-handoff` creates `analysis/investigation.xml`,
   `analysis/handoff.xml`, and `analysis/next-step.yaml`.
7. `analysis/handoff.xml` carries the concise downstream summary, while
   `analysis/next-step.yaml` records whether the case should be resolved,
   sent back to collect, closed with no further action, or handed off
   externally.
8. If the case needs a fix, `issue-resolve` consumes `handoff.xml`, records the
   outcome in `resolve/resolution.xml`, and records verification in
   `resolve/verification.md`.
9. If the case already has a complete answer at handoff time, it can move
   directly to `closed` without entering `resolve_in_progress`.

## 9. Artifact System

### Markdown

Use for overview and narrative artifacts:

- `activity.md`
- `verification.md`

### YAML

Use for status, indexes, manifests, and compact structured maps:

- `status.yaml`
- `sources.yaml`
- `next-step.yaml`

### XML

Use for hierarchical evidence-chain artifacts:

- `investigation.xml`
- `handoff.xml`
- `resolution.xml`

## 9.5 Minimal Artifact Contracts

Each artifact family should obey a minimum shared contract.

### Identity and references

- every case has one stable `case_id`
- every derived artifact includes or implies that `case_id`
- evidence references for user-provided issue inputs must point to curated
  materials, not vague raw-source descriptions
- repository evidence references should point directly to explicit repository
  locations such as file paths, symbols, and line numbers
- IDs should be readable, stable within the case, and safe to export
- `sources.yaml` should distinguish whether each source came from
  user-provided issue materials or from the current project repository, and how
  that source was carried into the case

### Provenance

- every synthesized artifact must be traceable to the artifact(s) it was derived
  from
- any artifact created after collect should prefer curated paths over raw paths
- repository-derived conclusions should prefer direct repository references over
  copied code excerpts in v1
- user assertions and machine-derived evidence should remain distinguishable

### Update strategy

- `status.yaml` is updated in place as the current state record
- `activity.md` is append-only and records why significant state transitions or
  workflow re-entries happened
- `sources.yaml` may be extended, but should not silently discard prior
  accounted items
- working artifacts such as `investigation.xml`, `handoff.xml`, `next-step.yaml`,
  and `resolution.xml` are updated in place to represent the current best state
- the case workspace is the live working surface; it does not maintain an
  internal revision chain for these artifacts in v1
- handoff and resolve artifacts inside the case workspace are the canonical
  outputs of the case, not temporary drafts waiting for extra packaging
- result artifacts should avoid references that only make sense inside a live
  interactive session
- result artifacts should preserve enough provenance to be useful to another
  human or a later session without extra packaging
- `resolution.xml` should include delivery metadata such as commit, branch, or
  PR references when resolve produces code changes
- `verification.md` should remain separate so detailed verification steps do not
  bloat `resolution.xml`

### File split heuristic

- merge by default when two files only weakly differ and mostly repeat the same
  story
- keep files separate when they have clearly different jobs or clearly
  different growth patterns
- prefer 2-3 files in a directory when that keeps each file readable and fast to
  update
- do not add a fourth helper file unless the existing split cannot keep files
  readable

### Case root file rule

- keep `status.yaml` separate from `activity.md`
- `status.yaml` is the compact current-state file
- `activity.md` is the append-only historical log
- do not collapse them into one file in v1, because current state and growing
  history have different shapes and should not bloat each other

### Analysis directory rule

- v1 `analysis/` should stay within 2-3 working files
- the canonical v1 split is three files:
  `investigation.xml`, `handoff.xml`, and `next-step.yaml`
- `investigation.xml` is the pure investigation record: evidence refs,
  findings, and expanded analysis details
- `handoff.xml` is the downstream-facing result: a concise summary plus the
  relevant code context and conclusions
- `next-step.yaml` is the small action file for what should happen next
- do not create a fourth analysis-layer helper file in v1

### Analysis file size rule

- prefer splitting work across 2-3 analysis files before letting one file grow
  too large
- 100-200 lines is a useful heuristic for a comfortable working file, not a
  hard product rule
- if one analysis file grows well past that heuristic, first move material into
  the existing 2-3 file split before inventing more files
- when a file grows too large, compress and reference instead of inlining more
  raw material
- raw logs, screenshots, OCR output, and long excerpts should stay under
  `curated/`, not be duplicated into analysis files
- repository evidence should stay as path/symbol/line references, not copied
  source blocks
- if a case becomes too broad to keep the 2-3 analysis files readable, shorten
  the writing before introducing more analysis files

## 9.6 Lightweight XML Conventions

v1 should use lightweight XML conventions across hierarchical artifacts.

The goal is consistency without turning XML authoring into a schema exercise.

### Shared rules

- each XML artifact uses one stable root node for its artifact type
- the root should include or imply the case identity
- the document should keep a small number of stable first-level sections
- section bodies may contain free-form prose, simple lists, and evidence
  references
- section order should be conventional, but not treated as a hard contract
- downstream automation may rely on root type and first-level section names, but
  should not require a fully rigid schema

### Root nodes

- `investigation.xml` uses `investigation`
- `handoff.xml` uses `handoff`
- `resolution.xml` uses `resolution`

### Minimum first-level sections by artifact

- `investigation.xml`:
  - `evidence_refs`
  - `confirmed`
  - `inferred`
  - `open_questions`
  - `details`
- `handoff.xml`:
  - `summary`
  - `code_context`
  - `known`
- `resolution.xml`:
  - `summary`
  - `outcome`
  - `delivery`
  - `verification`

### Non-goals

- no strict XSD-style schema in v1
- no deep mandatory nesting
- no requirement that every fact be normalized into tiny machine-only fields
- no attempt to eliminate natural writing style inside sections

## 10. Artifact Readiness Graph

Dependencies show when an artifact can be generated. They do not require the
workflow to advance immediately.

- `sources.yaml` depends on user-provided raw paths, materials, and collect
  results
- `investigation.xml` depends on curated materials and `sources.yaml`
- `handoff.xml` depends on investigation and may reference
  `ISSUE_CONTEXT.md` when present
- `next-step.yaml` depends on `handoff.xml`
- `resolution.xml` depends on resolve stage outcomes
- `verification.md` depends on resolution and verification activity

## 10.5 Direct Result Artifact Rule

`issue-flow` does not introduce a second layer of result packaging in v1.

### Canonical result files

- `analysis/handoff.xml` is the primary handoff result for cases that stop at
  handoff
- `analysis/next-step.yaml` is the small companion action file for handoff
  cases
- `resolve/resolution.xml` and `resolve/verification.md` are the canonical
  resolution results for cases that enter resolve

### Shareability rule

- if a case is ready to be handed to another human, another agent, or a later
  session, the case's canonical result files should already be usable as-is
- broken references are a readiness failure, not a warning-only condition
- result files should be explicit about what is known, what is inferred, and
  what remains open
- v1 does not add a separate sharing or redaction layer on top of the case

## 11. Case Identity Rules

- Prefer bug ID or issue number when available.
- Otherwise derive a stable slug from the issue title.
- Add a timestamp suffix only when needed to avoid collisions.
- The case ID should remain stable after creation.
- case cleanup is filesystem-based in v1: deleting a case directory removes that
  case from the workflow.
- a case may represent one or more problems; v1 does not model sub-issues or
  automatic case splitting

## 12. Migration Strategy

Phase 1:

- add new `issue-flow-core` shared namespace
- add three thin entry skills
- keep `issue-triage-handoff` as deprecated reference only

Phase 2:

- replace JSON-first artifact generation with Markdown, YAML, and XML templates
- move old refinement and evaluation behavior into case actions

## 13. Initial Deliverables

- shared namespace directory skeleton
- thin `SKILL.md` files for the three entry skills
- workflow stub docs
- knowledge stub docs
- artifact templates
- script contract placeholders
- lightweight readiness-check contract

## 14. File-Structure Status

The v1 file structure is considered converged for now:

- collect uses `sources.yaml`
- case root keeps `status.yaml` and `activity.md` separate
- `analysis/` uses `investigation.xml`, `handoff.xml`, and `next-step.yaml`
- `resolve/` uses `resolution.xml` and `verification.md`

## 15. Success Criteria

- A new case can be initialized without touching deprecated workflow assets.
- Each stage can resume from an existing case directory.
- The default happy path never requires JSON as the primary authored output.
- The entry `SKILL.md` files stay short and role-specific.
- The project-level workspace uses `.issue-flow/` instead of a skill-specific
  directory name.
