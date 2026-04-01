# Triage Principles

Core operating principles for issue triage and handoff generation.

## Principle 1: Input Freedom, Output Constraint

**Accept messy input.** Users should not have to reorganize their materials before you can help. Handle:
- Unstructured issue descriptions
- Scattered comments over time
- Chat logs with off-topic tangents
- Mixed log formats
- Incomplete information

**Produce structured output.** The handoff schema is non-negotiable. Every handoff must:
- Follow the defined schema
- Have traceable evidence
- Distinguish facts from inferences
- Include explicit gaps and unknowns

## Principle 2: Evidence Over Narrative

Human descriptions are claims, not facts.

| Source | Weight | Treatment |
|--------|--------|-----------|
| Stacktrace in logs | High | Confirmed fact |
| Error message with timestamp | High | Confirmed fact |
| User says "I saw error X" | Low | Record in `people_hypotheses`, verify against logs |
| Chat says "probably caused by Y" | Low | Record in `people_hypotheses`, do not promote without evidence |

**Rule**: Never promote narrative to fact without corroborating evidence.

## Principle 3: Three-Tier Findings

Every conclusion must be classified:

### Confirmed Facts
- Direct evidence exists
- No interpretation required
- Example: "Exception NullPointerException thrown at UserService.java:145"

### Bounded Inferences
- Evidence supports but doesn't prove
- Assumptions are stated
- Example: "Likely caused by timeout (evidence: timeout log at T1 followed by error at T2, assumes causal relationship)"

### Open Questions
- Cannot be answered with available evidence
- States what's missing
- Example: "Why did the retry mechanism not trigger? Need to check retry configuration."

**Rule**: When in doubt, demote to lower tier.

## Principle 4: Locate, Don't Explain

This skill's job is narrowing scope, not root cause analysis.

**Do**:
- Find relevant log files
- Identify error patterns
- Map to code locations
- Extract key identifiers
- Build timeline

**Don't**:
- Explain why the bug exists
- Propose fixes
- Speculate on root cause beyond bounded inference
- Recommend code changes

**Why**: Explanation and fixing are for downstream agents with more context and capability. Mixing triage with diagnosis creates:
- Premature conclusions
- Scope creep
- Wasted effort when assumptions are wrong

## Principle 5: Cost-Aware Compression

This skill should run on cheaper models. Push expensive reasoning downstream.

**Cheap operations** (do here):
- Summarizing narrative
- Pattern matching in logs
- Keyword extraction
- Schema filling
- Reference linking

**Expensive operations** (leave for downstream):
- Causal reasoning
- Code comprehension
- Fix generation
- Architectural analysis

## Principle 6: Narrowing Over Completeness

The goal is to shrink the search space, not to be exhaustive.

**Good triage**:
- 5 relevant files from 500
- 3 error patterns from 10,000 lines
- 2 candidate code locations from entire repo

**Bad triage**:
- "All 500 files might be relevant"
- "Here's a summary of every log"
- "The bug could be anywhere"

**Rule**: If you can't narrow, say why and list what would help.

## Principle 7: Explicit Uncertainty

Never hide what you don't know.

Every handoff must include:
- `open_questions`: What's unanswered
- `gaps`: What evidence is missing
- Confidence levels on inferences
- Timeline gaps marked explicitly

**Why**: Hidden uncertainty propagates. Downstream agents make decisions on your output. If you pretend certainty, they will too.

## Principle 8: Reproducible References

Every reference must be followable.

**Bad references**:
- "in the logs"
- "somewhere in the code"
- "user mentioned"

**Good references**:
- `E003: app.log:1423-1425`
- `src/handlers/user.py:145-152`
- `E007: issue comment by @alice on 2024-01-15`

**Rule**: If a human or agent can't navigate to the source in under 30 seconds, the reference is broken.

## Principle 9: Conflict Preservation

When evidence contradicts, keep both.

**Don't**: Silently pick one version
**Do**: Document the conflict, note both evidence items, mark resolution as pending

Conflicts are signal. They indicate:
- Missing context
- Different perspectives
- Time-dependent state
- Measurement error

Downstream consumers need to see conflicts, not have them hidden.

## Principle 10: Scope Guardrails

These actions are always out of scope:

- ❌ Writing patches
- ❌ Confirming root cause
- ❌ Recommending fixes
- ❌ Assigning blame
- ❌ Making deployment decisions
- ❌ Promising resolution

When asked to do these, redirect:
> "That's outside triage scope. The handoff is ready for a downstream agent that can [RCA/patch/etc]."
