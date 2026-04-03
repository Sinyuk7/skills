# Observability Hooks

Use this note to keep routing improvements testable after the first rewrite.

## Goals

- explain why a skill was selected
- catch false positives and false negatives
- measure whether metadata changes improved routing quality
- expose overlap zones that still need arbitration

## Minimum Trace Fields

Capture these fields whenever practical:

- request text or normalized intent label
- candidate skills considered
- selected skill or skills
- routing mode: `static|llm-assisted|semantic|hybrid|supervisor|parallel fan-out`
- confidence or arbitration note if available
- abstain, fallback, or tie-break outcome
- final success or failure label after execution

## Core Metrics

Track at least:

- trigger precision by skill
- trigger recall by skill
- false positive count
- false negative count
- overlap resolution rate
- abstain rate
- parallel routing usage

## Eval Guidance

When routing quality is unstable:

1. add thin-context cases first
2. add near-neighbor conflict cases second
3. add multi-skill composition cases third
4. rewrite metadata before changing routing logic

## Escalation Guidance

- If one skill keeps stealing traffic, tighten negative triggers before adding smarter arbitration.
- If multiple skills remain plausible after rewrite, add an explicit tie-break rule.
- If no single owner emerges, record a `gap` or `parallel` policy instead of forcing exclusivity.
