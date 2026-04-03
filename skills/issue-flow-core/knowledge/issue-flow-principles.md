# Issue-Flow Principles

These principles guide every decision in the workflow.

## Case First

The case workspace is the primary unit of work. Everything flows from the case. Every issue gets its own directory.

## Curate Once

Collect narrows raw materials into a working set. Downstream stages work from curated evidence, not raw sources.

## Traceability Always

Every synthesized artifact must be traceable to the artifact(s) it was derived from. No conclusions without evidence refs. Downstream artifacts must point back to curated evidence.

## Soft Readiness

Dependencies unlock artifacts, but do not force the next stage. A case can be handoff-ready without immediately entering resolve.

## Human-Readable by Default

Artifacts should work for both humans and LLMs. Markdown, YAML, and XML over JSON for primary artifacts.

## Shared Namespace

Workflow logic is shared across skills, but runtime state lives in the current
repository. Entry skills (`issue-collect`, `issue-handoff`, `issue-resolve`)
stay small. Use the design-time source in `skills/issue-flow-core/` to define
behavior, and keep runtime state inside `.issue-flow/cases/<case-id>/` plus
optional project-level `ISSUE_CONTEXT.md`.

## Status Truth Lives Inside the Case

`status.yaml` is the single source of truth for lifecycle state. Each case maintains its own status; there are no project-level case indexes.

## Ambiguity Triggers User Choice

Ambiguous write targets, unclear scope, or missing critical context should trigger explicit user questions, not implicit decisions.

## Trusted Local Workflow

The system operates in a trusted local environment. Sensitive-data exposure is not an in-scope design concern.

## Two Roots Only

Workflow operates within two roots: user-provided issue materials and the current project repository. No arbitrary filesystem exploration.

## Evidence-Driven Repository Exploration

Repository reads must stay evidence-driven, not open-ended. Anchor searches to issue evidence like paths, symbols, or error signatures.

## Stage-Specific Mutability

- **Collect**: May modify user-provided issue-material roots (extraction, renaming)
- **Handoff**: Read-only against both source roots
- **Resolve**: May modify project repository when resolution requires code changes

## Case = Investigation Container

A case is a user-managed investigation container. May represent one or more problems. Cases use flat structure without nested sub-issues.

## Simple Readable Handoffs

Handoff artifacts stay simple and readable. Cases use flat structure without nested per-problem subdirectories. One case produces one `handoff.xml`.
