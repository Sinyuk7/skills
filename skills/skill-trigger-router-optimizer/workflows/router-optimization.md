# Router Optimization Workflow

Design or refactor routing for a SKILL collection.

---

## Step 1: Load the Target Set

Accept any of these inputs:

- one `SKILL.md`
- a directory containing multiple skills
- a skill set plus known conflict cases
- a skill set plus routing test samples

Load only routing-relevant files first:

1. `SKILL.md`
2. workflow titles or entry files referenced by `SKILL.md`
3. templates or knowledge files only when they affect routing boundaries

Do not start by reading every file in full.

---

## Step 2: Inventory the Routing Surface

For each skill, extract:

- `name`
- `description`
- aliases or alternate trigger phrases if present
- explicit "Use when" cues
- explicit "Do not use" or negative triggers
- proactive-use language
- tool scope or permission constraints
- workflow entrypoints
- model or subagent constraints if present

Normalize into this structure:

```json
{
  "skill": "name",
  "primary_intents": [],
  "secondary_intents": [],
  "strong_positive_triggers": [],
  "weak_cues": [],
  "negative_triggers": [],
  "prerequisites": [],
  "mode": "exclusive|composable|parallel_candidate",
  "tool_scope": [],
  "fallback_targets": []
}
```

If metadata is missing, mark it as a routing risk instead of guessing.

---

## Step 3: Extract Intent Surface

For each skill, answer:

1. How would a user explicitly ask for this?
2. What weak cues should still trigger it?
3. What adjacent requests look similar but should not trigger it?
4. What prerequisites must be true before the skill should run?
5. Is the skill exclusive, chainable, or parallelizable?

Focus on user-language patterns, not abstract summaries.

---

## Step 4: Build Overlap and Gap Map

Construct a `skill x intent` matrix.

Classify each region as:

- `exclusive`
- `overlap`
- `gap`
- `chain`
- `parallel`

Use this decision rule:

- `exclusive`: one skill clearly owns the intent
- `overlap`: two or more skills claim the same request surface
- `gap`: no skill safely covers the request
- `chain`: one skill should run before another
- `parallel`: request should be decomposed and routed to multiple skills

Load the matrix template:

<action tool="read_file">
templates/routing-matrix.json
</action>

---

## Step 5: Choose Routing Pattern

For every ambiguous region, recommend one routing mode:

- `static`
- `llm-assisted`
- `semantic`
- `hybrid`
- `supervisor`
- `parallel fan-out`

Load the routing heuristics:

<action tool="read_file">
knowledge/routing-patterns.md
</action>

Select using these defaults:

- clear lexical triggers -> `static`
- ambiguous but narrow intent -> `llm-assisted`
- many near-synonyms across a large catalog -> `semantic`
- rules can prune candidates first -> `hybrid`
- multi-part or cross-domain requests -> `parallel fan-out`
- multi-step orchestration with synthesis -> `supervisor`

---

## Step 6: Rewrite Metadata

Only after the boundary map is stable, propose metadata rewrites.

For each affected skill, produce:

- revised `name` if current naming is too vague
- revised `description`
- strong positive triggers to keep in metadata or examples
- negative triggers to reduce false positives
- prerequisite phrases
- `use proactively` recommendation if justified
- split / merge recommendation if boundaries cannot be repaired by metadata alone

Load the rewrite template:

<action tool="read_file">
templates/rewrite-proposals.md
</action>

Rewrite for routing discrimination, not style polish.

---

## Step 7: Generate Routing Evals

Generate a minimal eval set with:

- should-trigger cases
- should-not-trigger cases
- overlap / tie-break cases
- multi-skill composition cases
- thin-context early-session cases

Load the eval schema:

<action tool="read_file">
templates/routing-evals.json
</action>

Each case should include:

- user request
- expected skill or skills
- reason
- ambiguity level
- notes for abstain, parallel, or fallback behavior

---

## Step 8: Draft Router Policy And Conflict Register

Promote the audit into explicit system behavior.

Load the policy template:

<action tool="read_file">
templates/router-policy.md
</action>

Load the conflict register template:

<action tool="read_file">
templates/conflict-register.md
</action>

The router policy should define:

- classification rules
- routing priority
- tie-break rules
- composition and chain rules
- parallel fan-out rules
- abstain and fallback rules
- rollout order for fixes

The conflict register should track:

- overlapping skills
- disputed intent regions
- chosen arbitration rule
- unresolved risks
- owner and next action if follow-up is needed

---

## Step 9: Add Observability Hooks

Recommend the minimum routing telemetry needed to improve the system.

Load the observability guide:

<action tool="read_file">
knowledge/observability-hooks.md
</action>

At minimum, specify:

- routed request or intent label
- candidate skills considered
- selected skill or skills
- routing mode used
- abstain, fallback, or parallel decision
- known false positive / false negative cases
- eval coverage gaps

Keep this lightweight unless the user asks for a production tracing spec.

---

## Step 10: Deliver Outputs

Return these artifacts:

1. `routing-audit.md`
2. `rewrite-proposals.md`
3. `routing-matrix.json`
4. `routing-evals.json`
5. `router-policy.md`
6. `conflict-register.md`

Use the audit template:

<action tool="read_file">
templates/routing-audit.md
</action>

If the user asked for a lightweight first pass, prioritize:

1. overlap / gap analysis
2. metadata rewrite proposals
3. routing eval cases
