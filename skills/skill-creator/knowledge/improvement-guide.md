# Improvement Guide

Use this note after the first evaluation pass, when you need to revise a skill instead of drafting it from scratch.

## Core principles

### 1. Generalize from feedback

Do not overfit to a handful of eval prompts. The goal is a skill that keeps working across many future requests.

When feedback is stubborn or repetitive:

- look for the deeper pattern
- try a better framing, not just a tighter rule
- favor reusable guidance over prompt-specific patches

### 2. Keep the prompt lean

Remove instructions that are not earning their keep.

Read transcripts as well as outputs. If the skill is causing wasted motion, rewrite or delete the parts responsible.

### 3. Explain the why

Modern models respond better to understandable rationale than to arbitrary rigidity.

- explain why a behavior matters
- translate terse user complaints into durable guidance
- treat repeated ALL-CAPS rules as a warning sign unless they are truly necessary

### 4. Look for repeated work

If multiple eval runs independently create the same helper code or follow the same multi-step pattern, that is a signal to bundle it.

Typical upgrade paths:

- move repeated helper code into `scripts/`
- document the preferred approach in the skill
- simplify future executions by reducing reinvention

## Iteration loop

After each revision:

1. update the skill
2. rerun evals into a new iteration directory
3. relaunch the viewer with the previous workspace attached
4. collect feedback
5. repeat if the skill is still improving

Baseline guidance:

- new skill: compare against `without_skill`
- existing skill: compare against the original snapshot or the previous iteration, whichever is the more useful baseline

## When to stop

Stop when one of these is true:

- the user is satisfied
- feedback is effectively empty
- the loop is no longer producing meaningful gains

## Optional: Blind comparison

For stricter A/B judgment, use:

- `agents/comparator.md`
- `agents/analyzer.md`

The general pattern is to compare outputs without revealing which version produced them, then analyze why the stronger version won.
