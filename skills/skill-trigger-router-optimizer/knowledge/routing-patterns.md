# Routing Patterns

Use this file to choose the routing mode for a skill collection.

## Modes

| Mode | Use When | Avoid When |
|------|----------|------------|
| `static` | Clear trigger words, narrow domain, low ambiguity | User language is broad or overlapping |
| `llm-assisted` | Intent is fuzzy but candidate set is small | Deterministic rules already separate the cases |
| `semantic` | Large catalog with many paraphrases | Metadata is too noisy to support similarity well |
| `hybrid` | Rules can prune first, then LLM can arbitrate | Rules do not meaningfully reduce ambiguity |
| `parallel fan-out` | Request contains separable sub-problems | Skills are mutually exclusive or order-dependent |
| `supervisor` | Multiple routed outputs must be synthesized | One skill already owns the whole request |

## Selection Heuristics

1. Prefer the cheapest reliable routing mode.
2. Fix metadata boundaries before adding smarter routing.
3. Use parallel routing only when the request naturally decomposes.
4. If a skill must always precede another, model it as `chain`, not `overlap`.
5. If no skill safely owns the request, record a `gap` instead of stretching an existing skill.

## Metadata Rewrite Rules

Good routing metadata should:

- state what the skill does
- state when it should trigger
- state what it should not be used for
- expose domain-specific trigger words
- include prerequisites when misuse is common

Weak metadata usually has one of these failures:

- too broad: steals traffic from neighboring skills
- too narrow: almost never triggers
- too abstract: cannot be mapped to user phrasing
- missing negatives: frequent false positives
- missing composition hints: chain or parallel opportunities get lost

## Escalation Rules

- Recommend `split` when one skill serves unrelated intents with different tool or model needs.
- Recommend `merge` when two skills are synonyms with only cosmetic differences.
- Recommend `abstain` when confidence is low and no safe owner exists.
- Recommend `fallback` when one skill is preferred but a second skill can safely handle degraded cases.
