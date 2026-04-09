
# SKILL Design Policy

> **Core Maxim — No Leaky Abstractions.**
> A SKILL must be self-contained: it defines itself by what it owns,
> not by referencing what another SKILL does internally.

---

## 1. What Is a SKILL

A SKILL is a **routable capability unit** — not merely a prompt or a workflow.
It exists so a router can decide: *should it run, when, and what bounded capability it owns*.

```text
SKILL = Routing Surface + Capability Contract + Execution Policy + Evidence Policy + Output Contract
```

---

## 2. Foundational Principles

### 2.1 Positive Boundary Definition

Define a SKILL by its **own** scope, inputs, outputs, success/failure conditions.
Never define it by enumerating another SKILL's internals it must avoid.

**Bad** — Negative / leaky boundary:
```
DO NOT create case.yaml — that is /issue-collect's job
DO NOT skip /issue-collect's own PROJECT_ROOT resolution
```

**Good** — Self-contained boundary:
```
Scope: validate repo, validate ticket, bootstrap bugfix branch.
Non-goals: evidence collection, case workspace creation, source-code analysis.
Handoff: forward original user payload unchanged to the next workflow stage.
```

### 2.2 No Knowledge Coupling

A SKILL may depend on a downstream SKILL's **interface contract** (inputs/outputs),
never on its **internal implementation** (file names, step order, resolution logic).

Violations cause: fragile docs, cascading edits, temporal coupling.

### 2.3 Separate Reasoning from Execution

| Uncertain | Deterministic |
|-----------|--------------|
| interpretation, judgment, ambiguity | retrieval, transform, validation, mutation |
| → LLM reasoning | → tool / script / code |

### 2.4 Evidence Precedes Answer

```
Retrieve → Inspect → Verify → Reason → Answer
```
Never: `Draft answer → search for supporting fragments later`.

### 2.5 Start Simple, Expand with Proof

Static structure first. One boundary at a time. Evaluate before expanding.

---

## 3. SKILL Type System

Classify every SKILL before editing it.

| Type | Routes? | Use When |
|------|---------|----------|
| **Routable Skill** | Yes | Owns a recognizable user intent with stable boundary |
| **Shared Core** | No | Reusable logic consumed by multiple skills |
| **Plugin / Tool Wrapper** | Rarely | Primary value is execution, not reasoning |
| **Stance / Mode Skill** | On explicit invoke | Changes policy/threshold of another skill |
| **Non-routable Reference** | Never | Documentation, glossary, examples only |

A routing audit MUST first remove false skills from the routable surface.

---

## 4. Router Design Rules

1. **Route by capability ownership**, not keyword lists.
2. Every routable SKILL declares: `owns`, `does_not_own`, `delegate_to`, `refuses_when`.
3. **One owner, many helpers** — assign one primary skill; let it delegate to cores/plugins.
4. Model hidden secondary intents (a request may embed multiple needs).
5. **Ship routing evals** (positive / negative / overlap / multi-intent) before declaring done.

---

## 5. Capability Contract Template

```yaml
name:
description:          # capability ownership, not aspiration
owns:                 # concrete, narrow
does_not_own:         # near-neighbor intents only
delegate_to:
requires_evidence:
primary_outputs:
allowed_tools:
forbidden_tools:
entry_workflow:
eval_set:
```

**Description rule** — describe what the SKILL *does*, not how it *feels*:
- Bad: `Carefully helps improve and optimize skills in a robust way.`
- Good: `Converts descriptive execution steps into deterministic machine instructions and tool calls.`

---

## 6. Execution Policy

### 6.1 Step Classification

For each workflow step, classify as:
`reasoning_step` · `retrieval_step` · `transform_step` · `validation_step` · `mutation_step`

Any step classifiable as retrieval/transform/validation/mutation → rewrite into tool-executable instruction.

### 6.2 Forbidden Vague Verbs

Replace: *analyze, inspect, improve, optimize, refine, clean up, understand deeply*
With: **classify, extract, compare, map, validate, patch, summarize, rank, emit**

### 6.3 Observable Outputs

Every step must produce: a file, schema object, diff, finding list, classification, evidence block, or pass/fail signal.

---

## 7. Evidence Policy

- Evidence is mandatory when: factual claims, file/code state, existence/change checks, comparisons, recommendations with consequences.
- Use small evidence units: `source → excerpt → finding → conclusion`.
- Allow explicit uncertainty: output verified facts + unresolved questions + next actions.

---

## 8. File Structure

```text
skill-name/
  SKILL.md          # purpose, routing, scope, hard constraints (compact)
  workflows/        # phase-by-phase procedures, tool calls, checkpoints
  knowledge/        # concepts, heuristics, policy, rationale
  templates/        # output formats, skeletons
  schemas/          # data contracts
  evals/            # trigger tests, regression prompts
  scripts/          # deterministic transforms, validators
```

Keep SKILL.md short. Push executable detail outward.

---

## 9. Anti-Patterns

| Anti-Pattern | Why It's Bad |
|-------------|-------------|
| Negative boundary definition | Leaky abstraction — defines self via neighbor's internals |
| Knowledge coupling | Upstream knows downstream implementation steps → fragile |
| Temporal coupling | Upstream assumes downstream's current step order |
| "Everything is a skill" | Reference material ≠ routable capability |
| One huge master skill | Hurts routing, context budget, maintainability |
| Keyword trigger soup | Overlap and false positives without ownership logic |
| Answer first, prove later | Hides uncertainty, weakens grounding |
| All instructions in SKILL.md | Context bloat, brittle execution |
| Refactor without evals | Style change, not verified improvement |
| Give every skill every tool | Harms routing clarity, increases risk |

---

## 10. Refactor Decision Tree

| Problem | Action |
|---------|--------|
| Steps are vague / too manual | Machine-instruction refactor |
| Hallucination / no proof | Evidence transformation |
| Wrong triggers / overlap | Router optimization |
| **Multiple apply** | 1→ classify routable/non  2→ stabilize boundaries  3→ extract determinism  4→ add evidence chain  5→ generate evals |

---

## 11. Acceptance Criteria

A SKILL is well-designed only when ALL are true:

- [ ] Stable capability boundary — defined positively, no abstraction leaks
- [ ] Correctly classified as routable or non-routable
- [ ] Trigger logic based on ownership, not keyword sprawl
- [ ] Deterministic work extracted into explicit tool/script steps
- [ ] Evidence requirements explicit for non-trivial claims
- [ ] Output shape stable and machine-checkable
- [ ] Tool access minimal and justified
- [ ] Ships with regression evals
- [ ] Top-level instructions compact enough to preserve context budget

---

## 12. Design Maxim

```
First decide who should own the task.
Then decide what must be proven.
Then decide what must be scripted.
Only then polish the wording.
```
